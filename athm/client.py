"""ATH Móvil API Client implementation."""

import json
import time
from typing import Any

import httpx
from pydantic import ValidationError as PydanticValidationError

from athm.constants import BASE_URL, DEFAULT_HEADERS, ENDPOINTS, MAX_RETRIES, REQUEST_TIMEOUT
from athm.exceptions import (
    AuthenticationError,
    NetworkError,
    TimeoutError,
    TransactionError,
    ValidationError,
    create_exception_from_response,
)
from athm.models import (
    CancelPaymentRequest,
    FindPaymentRequest,
    PaymentItem,
    PaymentRequest,
    PaymentResponse,
    RefundRequest,
    RefundResponse,
    SuccessResponse,
    TransactionResponse,
    TransactionStatus,
    UpdatePhoneRequest,
)
from athm.types import Self, Timeout


class ATHMovilClient:
    """Client for interacting with ATH Móvil Payment API.

    This client provides synchronous methods for all ATH Móvil API operations.

    Attributes:
        public_token: Your ATH Business public token
        private_token: Your ATH Business private token (optional, required for refunds)
        base_url: API base URL (defaults to production)
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        verify_ssl: Whether to verify SSL certificates
    """

    def __init__(
        self,
        public_token: str,
        private_token: str | None = None,
        base_url: str = BASE_URL,
        timeout: Timeout = REQUEST_TIMEOUT,
        max_retries: int = MAX_RETRIES,
        verify_ssl: bool = True,
    ) -> None:
        """Initialize the ATH Móvil client.

        Args:
            public_token: Your ATH Business public token
            private_token: Your ATH Business private token (optional)
            base_url: API base URL
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            verify_ssl: Whether to verify SSL certificates

        Raises:
            ValidationError: If public_token is empty
        """
        if not public_token or not public_token.strip():
            raise ValidationError("public_token is required and cannot be empty")

        self.public_token = public_token
        self.private_token = private_token
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.verify_ssl = verify_ssl

        self._sync_client: httpx.Client | None = None
        self._auth_tokens: dict[str, str] = {}

    def __enter__(self) -> Self:
        """Enter context manager and initialize HTTP client."""
        self._sync_client = httpx.Client(
            base_url=self.base_url,
            headers=DEFAULT_HEADERS,
            timeout=self.timeout,
            verify=self.verify_ssl,
        )
        return self

    def __exit__(self, *args: Any) -> None:
        """Exit context manager and cleanup HTTP client."""
        if self._sync_client:
            self._sync_client.close()
            self._sync_client = None

    @property
    def sync_client(self) -> httpx.Client:
        """Get or lazily initialize the synchronous HTTP client."""
        if self._sync_client is None:
            self._sync_client = httpx.Client(
                base_url=self.base_url,
                headers=DEFAULT_HEADERS,
                timeout=self.timeout,
                verify=self.verify_ssl,
            )
        return self._sync_client

    def _prepare_headers(self, auth_token: str | None = None) -> dict[str, str]:
        """Prepare request headers.

        Args:
            auth_token: Optional JWT auth token

        Returns:
            Headers dictionary
        """
        headers = DEFAULT_HEADERS.copy()
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        return headers

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        """Handle API response and raise appropriate exceptions.

        Args:
            response: HTTP response

        Returns:
            Parsed JSON response

        Raises:
            ATHMovilError: On API errors
        """
        try:
            data: dict[str, Any] = response.json()
        except json.JSONDecodeError as e:
            raise NetworkError(
                f"Invalid JSON response: {e}",
                status_code=response.status_code,
            ) from e

        if response.status_code >= 400 or data.get("status") == "error":
            raise create_exception_from_response(data, response.status_code)

        return data

    def _make_request(
        self,
        method: str,
        endpoint: str,
        json_data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        retries: int = 0,
    ) -> dict[str, Any]:
        """Make synchronous HTTP request with retry logic.

        Args:
            method: HTTP method
            endpoint: API endpoint
            json_data: Request body
            headers: Request headers
            retries: Current retry count

        Returns:
            Response data

        Raises:
            ATHMovilError: On API errors
        """
        headers = headers or self._prepare_headers()

        try:
            response = self.sync_client.request(
                method=method,
                url=endpoint,
                json=json_data,
                headers=headers,
            )
            return self._handle_response(response)

        except (httpx.TimeoutException, httpx.NetworkError) as e:
            if retries < self.max_retries:
                backoff = 2**retries
                time.sleep(backoff)
                return self._make_request(method, endpoint, json_data, headers, retries + 1)

            error_class = TimeoutError if isinstance(e, httpx.TimeoutException) else NetworkError
            raise error_class(f"{type(e).__name__}: {e}") from e

        except httpx.HTTPError as e:
            raise NetworkError(f"HTTP error: {e}") from e

    def create_payment(
        self,
        total: str,
        phone_number: str,
        items: list[PaymentItem],
        **kwargs: Any,
    ) -> PaymentResponse:
        """Create a payment ticket.

        Args:
            total: Total amount (1.00 to 1500.00)
            phone_number: Customer phone number (10 digits)
            items: List of payment items
            **kwargs: Additional payment fields (tax, subtotal, metadata1, metadata2, timeout)

        Returns:
            PaymentResponse with ecommerce_id and auth_token

        Raises:
            ValidationError: On invalid input
            ATHMovilError: On API errors
        """
        try:
            request_data = PaymentRequest(
                public_token=self.public_token,
                total=total,
                phone_number=phone_number,
                items=items,
                **kwargs,
            )
        except PydanticValidationError as e:
            raise ValidationError(str(e)) from e

        response = self._make_request(
            "POST",
            ENDPOINTS["payment"],
            json_data=request_data.model_dump(by_alias=True, exclude_none=True),
        )

        payment_response = PaymentResponse(**response)
        self._auth_tokens[payment_response.data.ecommerce_id] = payment_response.data.auth_token

        return payment_response

    def find_payment(self, ecommerce_id: str) -> TransactionResponse:
        """Check payment status.

        Args:
            ecommerce_id: The payment ID to check

        Returns:
            TransactionResponse with current status

        Raises:
            ATHMovilError: On API errors
        """
        request_data = FindPaymentRequest(
            ecommerce_id=ecommerce_id,
            public_token=self.public_token,
        )

        response = self._make_request(
            "POST",
            ENDPOINTS["find_payment"],
            json_data=request_data.model_dump(by_alias=True),
        )

        return TransactionResponse(**response)

    def authorize_payment(
        self,
        ecommerce_id: str,
        auth_token: str | None = None,
    ) -> TransactionResponse:
        """Authorize and complete a confirmed payment.

        Args:
            ecommerce_id: The payment ID to authorize
            auth_token: JWT token from create_payment (if not stored internally)

        Returns:
            TransactionResponse with completed transaction details

        Raises:
            AuthenticationError: If no auth token available
            ATHMovilError: On API errors
        """
        token = auth_token or self._auth_tokens.get(ecommerce_id)
        if not token:
            raise AuthenticationError(
                "No auth token available. Create payment first or provide auth_token."
            )

        headers = self._prepare_headers(auth_token=token)

        response = self._make_request(
            "POST",
            ENDPOINTS["authorization"],
            json_data={},
            headers=headers,
        )

        return TransactionResponse(**response)

    def update_phone_number(
        self,
        ecommerce_id: str,
        phone_number: str,
        auth_token: str | None = None,
    ) -> SuccessResponse:
        """Update the phone number for a payment notification.

        Args:
            ecommerce_id: The payment ID
            phone_number: New phone number (10 digits)
            auth_token: JWT token (if not stored internally)

        Returns:
            SuccessResponse

        Raises:
            AuthenticationError: If no auth token available
            ValidationError: On invalid phone number
            ATHMovilError: On API errors
        """
        token = auth_token or self._auth_tokens.get(ecommerce_id)
        if not token:
            raise AuthenticationError("No auth token available")

        try:
            request_data = UpdatePhoneRequest(
                ecommerce_id=ecommerce_id,
                phone_number=phone_number,
            )
        except PydanticValidationError as e:
            raise ValidationError(str(e)) from e

        headers = self._prepare_headers(auth_token=token)

        response = self._make_request(
            "PUT",
            ENDPOINTS["update_phone"],
            json_data=request_data.model_dump(by_alias=True),
            headers=headers,
        )

        return SuccessResponse(**response)

    def cancel_payment(self, ecommerce_id: str) -> SuccessResponse:
        """Cancel an open payment.

        Args:
            ecommerce_id: The payment ID to cancel

        Returns:
            SuccessResponse

        Raises:
            ATHMovilError: On API errors
        """
        request_data = CancelPaymentRequest(
            ecommerce_id=ecommerce_id,
            public_token=self.public_token,
        )

        response = self._make_request(
            "POST",
            ENDPOINTS["cancel"],
            json_data=request_data.model_dump(by_alias=True),
        )

        self._auth_tokens.pop(ecommerce_id, None)

        return SuccessResponse(**response)

    def refund_payment(
        self,
        reference_number: str,
        amount: str,
        message: str | None = None,
    ) -> RefundResponse:
        """Process a refund for a completed transaction.

        Args:
            reference_number: Original transaction reference
            amount: Amount to refund
            message: Optional refund message (max 50 chars)

        Returns:
            RefundResponse with refund details

        Raises:
            AuthenticationError: If private_token not configured
            ValidationError: On invalid input
            ATHMovilError: On API errors
        """
        if not self.private_token:
            raise AuthenticationError("Private token required for refunds")

        try:
            request_data = RefundRequest(
                public_token=self.public_token,
                private_token=self.private_token,
                reference_number=reference_number,
                amount=amount,
                message=message,
            )
        except PydanticValidationError as e:
            raise ValidationError(str(e)) from e

        response = self._make_request(
            "POST",
            ENDPOINTS["refund"],
            json_data=request_data.model_dump(by_alias=True, exclude_none=True),
        )

        return RefundResponse(**response)

    def wait_for_confirmation(
        self,
        ecommerce_id: str,
        timeout: int = 300,
        polling_interval: float = 2.0,
    ) -> bool:
        """Wait for customer to confirm payment.

        Polls payment status until customer confirms or timeout is reached.

        Args:
            ecommerce_id: The payment ID from create_payment()
            timeout: Maximum seconds to wait (default: 300)
            polling_interval: Seconds between status checks (default: 2.0)

        Returns:
            True if payment was confirmed

        Raises:
            TimeoutError: If timeout exceeded without confirmation
            TransactionError: If payment was cancelled

        Example:
            >>> payment = client.create_payment(...)
            >>> client.wait_for_confirmation(payment.data.ecommerce_id)
            >>> result = client.authorize_payment(payment.data.ecommerce_id)
        """
        elapsed = 0.0
        while elapsed < timeout:
            status = self.find_payment(ecommerce_id)

            if status.data and status.data.ecommerce_status == TransactionStatus.CONFIRM:
                return True
            elif status.data and status.data.ecommerce_status == TransactionStatus.CANCEL:
                raise TransactionError(
                    "Payment was cancelled",
                    error_code="PAYMENT_CANCELLED",
                )

            time.sleep(polling_interval)
            elapsed += polling_interval

        raise TimeoutError(
            f"Payment not confirmed within {timeout} seconds",
            error_code="POLLING_TIMEOUT",
        )

    def close(self) -> None:
        """Close HTTP client and cleanup resources.

        This method should be called when you're done using the client,
        or use the client as a context manager to ensure automatic cleanup.

        Example:
            >>> client = ATHMovilClient(public_token="token")
            >>> try:
            ...     client.create_payment(...)
            ... finally:
            ...     client.close()

            Or use as context manager:
            >>> with ATHMovilClient(public_token="token") as client:
            ...     client.create_payment(...)
        """
        if self._sync_client:
            self._sync_client.close()
            self._sync_client = None

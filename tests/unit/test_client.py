"""Unit tests for ATH Móvil Client."""

from typing import Any

import httpx
import pytest
from pytest_httpx import HTTPXMock

from athm.client import ATHMovilClient
from athm.constants import ENDPOINTS
from athm.exceptions import (
    ATHMovilError,
    AuthenticationError,
    NetworkError,
    TimeoutError,
    TransactionError,
    ValidationError,
)
from athm.models import PaymentResponse, TransactionResponse, TransactionStatus
from tests.conftest import SAMPLE_ECOMMERCE_ID, create_mock_transaction


class TestClientInitialization:
    def test_init_with_public_token(self, public_token: str):
        client = ATHMovilClient(public_token=public_token)
        assert client.public_token == public_token
        assert client.private_token is None
        assert client.base_url == "https://payments.athmovil.com"

    def test_init_with_both_tokens(self, public_token: str, private_token: str):
        client = ATHMovilClient(
            public_token=public_token,
            private_token=private_token,
        )
        assert client.public_token == public_token
        assert client.private_token == private_token

    def test_init_without_public_token(self):
        with pytest.raises(ValidationError, match="public_token is required"):
            ATHMovilClient(public_token="")

    def test_init_with_whitespace_token(self):
        with pytest.raises(ValidationError, match="cannot be empty"):
            ATHMovilClient(public_token="   ")

    def test_custom_configuration(self, public_token: str):
        client = ATHMovilClient(
            public_token=public_token,
            base_url="https://custom.api.com",
            timeout=10.0,
            max_retries=5,
            verify_ssl=False,
        )
        assert client.base_url == "https://custom.api.com"
        assert client.timeout == 10.0
        assert client.max_retries == 5
        assert client.verify_ssl is False

    def test_context_manager(self, public_token: str):
        with ATHMovilClient(public_token=public_token) as client:
            assert client._sync_client is not None
        # After exiting context, client should be closed
        assert client._sync_client is None


class TestPaymentOperations:
    def test_create_payment_success(
        self,
        client: ATHMovilClient,
        httpx_mock: HTTPXMock,
        mock_payment_response: dict[str, Any],
    ):
        httpx_mock.add_response(
            method="POST",
            url=f"https://payments.athmovil.com{ENDPOINTS['payment']}",
            json=mock_payment_response,
            status_code=200,
        )

        response = client.create_payment(
            total="5.00",
            phone_number="7875551234",
            metadata1="Test",
            metadata2="Test",
            items=[
                {
                    "name": "Test",
                    "description": "Test",
                    "quantity": "1",
                    "price": "5.00",
                }
            ],
        )

        assert isinstance(response, PaymentResponse)
        assert response.data.ecommerce_id == SAMPLE_ECOMMERCE_ID
        assert response.data.auth_token
        # Check that auth token is stored internally
        assert client._auth_tokens.get(SAMPLE_ECOMMERCE_ID)

    def test_create_payment_validation_error(self, client: ATHMovilClient):
        with pytest.raises(ValidationError):
            client.create_payment(
                total="0.50",  # Below minimum
                phone_number="123",  # Invalid phone
                items=[{"name": "Test", "description": "Test", "quantity": "1", "price": "0.50"}],
            )

    def test_create_payment_api_error(
        self,
        client: ATHMovilClient,
        httpx_mock: HTTPXMock,
        mock_error_response: dict[str, Any],
    ):
        httpx_mock.add_response(
            method="POST",
            url=f"https://payments.athmovil.com{ENDPOINTS['payment']}",
            json=mock_error_response,
            status_code=400,
        )

        with pytest.raises(ValidationError):
            client.create_payment(
                total="5.00",
                phone_number="7875551234",
                metadata1="Test",
                metadata2="Test",
                items=[{"name": "Test", "description": "Test", "quantity": "1", "price": "5.00"}],
            )


class TestFindPaymentOperations:
    def test_find_payment_success(
        self,
        client: ATHMovilClient,
        httpx_mock: HTTPXMock,
        ecommerce_id: str,
        mock_transaction_response: dict[str, Any],
    ):
        httpx_mock.add_response(
            method="POST",
            url=f"https://payments.athmovil.com{ENDPOINTS['find_payment']}",
            json=mock_transaction_response,
            status_code=200,
        )

        response = client.find_payment(ecommerce_id)

        assert isinstance(response, TransactionResponse)
        assert response.data
        assert response.data.ecommerce_status == TransactionStatus.CONFIRM

    def test_find_payment_not_found(
        self,
        client: ATHMovilClient,
        httpx_mock: HTTPXMock,
        ecommerce_id: str,
    ):
        error_response = {
            "status": "error",
            "message": "EcommerceId does not exist",
            "errorcode": "BTRA_0031",
            "data": None,
        }

        httpx_mock.add_response(
            method="POST",
            url=f"https://payments.athmovil.com{ENDPOINTS['find_payment']}",
            json=error_response,
            status_code=404,
        )

        with pytest.raises(ATHMovilError) as exc_info:
            client.find_payment(ecommerce_id)
        assert exc_info.value.error_code == "BTRA_0031"


class TestWaitForConfirmation:
    def test_wait_for_confirmation_success(
        self,
        client: ATHMovilClient,
        httpx_mock: HTTPXMock,
        ecommerce_id: str,
    ):
        # First poll: OPEN status
        open_response = create_mock_transaction(TransactionStatus.OPEN)
        httpx_mock.add_response(
            method="POST",
            url=f"https://payments.athmovil.com{ENDPOINTS['find_payment']}",
            json=open_response,
            status_code=200,
        )

        # Second poll: CONFIRM status
        confirm_response = create_mock_transaction(TransactionStatus.CONFIRM)
        httpx_mock.add_response(
            method="POST",
            url=f"https://payments.athmovil.com{ENDPOINTS['find_payment']}",
            json=confirm_response,
            status_code=200,
        )

        result = client.wait_for_confirmation(ecommerce_id, polling_interval=0.1)
        assert result is True

    def test_wait_for_confirmation_immediate(
        self,
        client: ATHMovilClient,
        httpx_mock: HTTPXMock,
        ecommerce_id: str,
    ):
        # Already confirmed
        confirm_response = create_mock_transaction(TransactionStatus.CONFIRM)
        httpx_mock.add_response(
            method="POST",
            url=f"https://payments.athmovil.com{ENDPOINTS['find_payment']}",
            json=confirm_response,
            status_code=200,
        )

        result = client.wait_for_confirmation(ecommerce_id)
        assert result is True

    def test_wait_for_confirmation_timeout(
        self,
        client: ATHMovilClient,
        httpx_mock: HTTPXMock,
        ecommerce_id: str,
    ):
        # Always return OPEN status
        # timeout=1s, interval=0.1s = 11 polls (0.0, 0.1, 0.2, ..., 1.0)
        open_response = create_mock_transaction(TransactionStatus.OPEN)
        for _ in range(11):
            httpx_mock.add_response(
                method="POST",
                url=f"https://payments.athmovil.com{ENDPOINTS['find_payment']}",
                json=open_response,
                status_code=200,
            )

        with pytest.raises(TimeoutError, match="Payment not confirmed within"):
            client.wait_for_confirmation(ecommerce_id, timeout=1, polling_interval=0.1)

    def test_wait_for_confirmation_cancelled(
        self,
        client: ATHMovilClient,
        httpx_mock: HTTPXMock,
        ecommerce_id: str,
    ):
        # Payment was cancelled
        cancel_response = create_mock_transaction(TransactionStatus.CANCEL)
        httpx_mock.add_response(
            method="POST",
            url=f"https://payments.athmovil.com{ENDPOINTS['find_payment']}",
            json=cancel_response,
            status_code=200,
        )

        with pytest.raises(TransactionError, match="Payment was cancelled"):
            client.wait_for_confirmation(ecommerce_id)


class TestAuthorizationOperations:
    def test_authorize_payment_success(
        self,
        client: ATHMovilClient,
        httpx_mock: HTTPXMock,
        ecommerce_id: str,
        auth_token: str,
    ):
        # Set up internal auth token
        client._auth_tokens[ecommerce_id] = auth_token

        completed_response = create_mock_transaction(TransactionStatus.COMPLETED)
        httpx_mock.add_response(
            method="POST",
            url=f"https://payments.athmovil.com{ENDPOINTS['authorization']}",
            json=completed_response,
            status_code=200,
        )

        response = client.authorize_payment(ecommerce_id)

        assert isinstance(response, TransactionResponse)
        assert response.data
        assert response.data.ecommerce_status == TransactionStatus.COMPLETED

    def test_authorize_payment_no_token(
        self,
        client: ATHMovilClient,
        ecommerce_id: str,
    ):
        with pytest.raises(AuthenticationError, match="No auth token available"):
            client.authorize_payment(ecommerce_id)

    def test_authorize_payment_with_provided_token(
        self,
        client: ATHMovilClient,
        httpx_mock: HTTPXMock,
        ecommerce_id: str,
        auth_token: str,
    ):
        completed_response = create_mock_transaction(TransactionStatus.COMPLETED)
        httpx_mock.add_response(
            method="POST",
            url=f"https://payments.athmovil.com{ENDPOINTS['authorization']}",
            json=completed_response,
            status_code=200,
        )

        response = client.authorize_payment(ecommerce_id, auth_token=auth_token)

        assert response.data
        assert response.data.ecommerce_status == TransactionStatus.COMPLETED


class TestCancelOperations:
    def test_cancel_payment_success(
        self,
        client: ATHMovilClient,
        httpx_mock: HTTPXMock,
        ecommerce_id: str,
        mock_success_response: dict[str, Any],
    ):
        # Store an auth token to verify it gets removed
        client._auth_tokens[ecommerce_id] = "test_token"

        httpx_mock.add_response(
            method="POST",
            url=f"https://payments.athmovil.com{ENDPOINTS['cancel']}",
            json=mock_success_response,
            status_code=200,
        )

        response = client.cancel_payment(ecommerce_id)

        assert response.status == "success"
        # Verify auth token was removed
        assert ecommerce_id not in client._auth_tokens


class TestRefundOperations:
    def test_refund_payment_success(
        self,
        client: ATHMovilClient,
        httpx_mock: HTTPXMock,
        reference_number: str,
        mock_refund_response: dict[str, Any],
    ):
        httpx_mock.add_response(
            method="POST",
            url=f"https://payments.athmovil.com{ENDPOINTS['refund']}",
            json=mock_refund_response,
            status_code=200,
        )

        response = client.refund_payment(
            reference_number=reference_number,
            amount="50.00",
            message="Product return",
        )

        assert response.status == "success"
        assert response.data.refund.refunded_amount == 50.00

    def test_refund_without_private_token(
        self,
        public_token: str,
        reference_number: str,
    ):
        client = ATHMovilClient(public_token=public_token)

        with pytest.raises(AuthenticationError, match="Private token required for refunds"):
            client.refund_payment(reference_number, "50.00")

    def test_refund_invalid_amount(
        self,
        client: ATHMovilClient,
        reference_number: str,
    ):
        with pytest.raises(ValidationError):
            client.refund_payment(reference_number, "-10.00")


class TestUpdatePhoneOperations:
    def test_update_phone_success(
        self,
        client: ATHMovilClient,
        httpx_mock: HTTPXMock,
        ecommerce_id: str,
        auth_token: str,
        mock_success_response: dict[str, Any],
    ):
        client._auth_tokens[ecommerce_id] = auth_token

        httpx_mock.add_response(
            method="PUT",
            url=f"https://payments.athmovil.com{ENDPOINTS['update_phone']}",
            json=mock_success_response,
            status_code=200,
        )

        response = client.update_phone_number(ecommerce_id, "7875559999")

        assert response.status == "success"

    def test_update_phone_invalid_number(
        self,
        client: ATHMovilClient,
        ecommerce_id: str,
        auth_token: str,
    ):
        client._auth_tokens[ecommerce_id] = auth_token

        with pytest.raises(ValidationError):
            client.update_phone_number(ecommerce_id, "123")

    def test_update_phone_no_auth_token(
        self,
        client: ATHMovilClient,
        ecommerce_id: str,
    ):
        # Don't set auth token - should raise AuthenticationError
        with pytest.raises(AuthenticationError, match="No auth token available"):
            client.update_phone_number(ecommerce_id, "7875559999")


class TestErrorHandling:
    def test_network_error_with_retry(
        self,
        client: ATHMovilClient,
        httpx_mock: HTTPXMock,
        ecommerce_id: str,
        mock_transaction_response: dict[str, Any],
    ):
        client.max_retries = 2

        # First attempt: network error
        httpx_mock.add_exception(httpx.NetworkError("Connection failed"))
        # Second attempt: success
        httpx_mock.add_response(
            method="POST",
            url=f"https://payments.athmovil.com{ENDPOINTS['find_payment']}",
            json=mock_transaction_response,
        )

        response = client.find_payment(ecommerce_id)
        assert response.data

    def test_timeout_error_max_retries(
        self,
        client: ATHMovilClient,
        httpx_mock: HTTPXMock,
        ecommerce_id: str,
    ):
        client.max_retries = 1

        # All attempts fail with timeout - initial + 1 retry = 2 attempts
        for _ in range(2):
            httpx_mock.add_exception(httpx.TimeoutException("Request timed out"))

        with pytest.raises(TimeoutError):
            client.find_payment(ecommerce_id)

    def test_invalid_json_response(
        self,
        client: ATHMovilClient,
        httpx_mock: HTTPXMock,
        ecommerce_id: str,
    ):
        httpx_mock.add_response(
            method="POST",
            url=f"https://payments.athmovil.com{ENDPOINTS['find_payment']}",
            text="Not valid JSON",
            status_code=200,
        )

        with pytest.raises(NetworkError, match="Invalid JSON response"):
            client.find_payment(ecommerce_id)


class TestClientCleanup:
    def test_close_sync_client(self, public_token: str):
        client = ATHMovilClient(public_token=public_token)
        # Force client creation
        _ = client.sync_client
        assert client._sync_client is not None

        client.close()
        assert client._sync_client is None


class TestAdditionalCoverage:
    def test_network_error_retry_exhausted(
        self,
        client: ATHMovilClient,
        httpx_mock: HTTPXMock,
        ecommerce_id: str,
    ):
        client.max_retries = 1

        # Add 2 network errors (initial + 1 retry)
        for _ in range(2):
            httpx_mock.add_exception(httpx.NetworkError("Network error"))

        with pytest.raises(NetworkError, match="Network error"):
            client.find_payment(ecommerce_id)

    def test_http_error(
        self,
        client: ATHMovilClient,
        httpx_mock: HTTPXMock,
        ecommerce_id: str,
    ):
        httpx_mock.add_exception(httpx.HTTPError("HTTP error"))

        with pytest.raises(NetworkError, match="HTTP error"):
            client.find_payment(ecommerce_id)

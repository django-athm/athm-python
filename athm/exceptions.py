"""Custom exceptions for ATH Móvil API errors."""

from typing import Any

from athm.constants import (
    AUTHENTICATION_ERROR_CODES,
    BUSINESS_ERROR_CODES,
    ERROR_MESSAGES,
    INTERNAL_ERROR_CODES,
    NETWORK_ERROR_CODES,
    TRANSACTION_ERROR_CODES,
    VALIDATION_ERROR_CODES,
)


class ATHMovilError(Exception):
    """Base exception for all ATH Móvil API errors."""

    def __init__(
        self,
        message: str,
        error_code: str | None = None,
        status_code: int | None = None,
        response_data: dict[str, Any] | None = None,
    ) -> None:
        """Initialize ATH Móvil error.

        Args:
            message: Error message
            error_code: ATH Móvil API error code
            status_code: HTTP status code
            response_data: Full API response data
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.response_data = response_data

        if error_code and error_code in ERROR_MESSAGES:
            self.message = f"{ERROR_MESSAGES[error_code]} (Code: {error_code})"

    def __str__(self) -> str:
        """Return formatted error message with code and HTTP status."""
        parts = [self.message]
        if self.error_code:
            parts.append(f"Error Code: {self.error_code}")
        if self.status_code:
            parts.append(f"HTTP Status: {self.status_code}")
        return " | ".join(parts)

    def __repr__(self) -> str:
        """Return detailed representation of the error."""
        return (
            f"{self.__class__.__name__}(message={self.message!r}, "
            f"error_code={self.error_code!r}, status_code={self.status_code!r})"
        )


class AuthenticationError(ATHMovilError):
    """Raised when authentication with ATH Móvil API fails."""

    pass


class ValidationError(ATHMovilError):
    """Raised when request validation fails."""

    pass


class InvalidRequestError(ATHMovilError):
    """Raised when API request is malformed or contains invalid business logic."""

    pass


class TransactionError(ATHMovilError):
    """Raised when a transaction operation fails."""

    pass


class PaymentError(TransactionError):
    """Raised when a payment transaction fails."""

    pass


class RefundError(TransactionError):
    """Raised when a refund transaction fails."""

    pass


class TimeoutError(ATHMovilError):
    """Raised when an API request times out."""

    pass


class RateLimitError(ATHMovilError):
    """Raised when API rate limit is exceeded."""

    pass


class NetworkError(ATHMovilError):
    """Raised when a network-related error occurs during API communication."""

    pass


class InternalServerError(ATHMovilError):
    """Raised when ATH Móvil API experiences an internal server error."""

    pass


def create_exception_from_response(
    response_data: dict[str, Any], status_code: int
) -> ATHMovilError:
    """Create appropriate exception from API response.

    Args:
        response_data: Response data from API
        status_code: HTTP status code

    Returns:
        Appropriate exception instance
    """
    message = response_data.get("message", "Unknown error")
    error_code = response_data.get("errorcode")

    if error_code:
        if error_code in AUTHENTICATION_ERROR_CODES:
            return AuthenticationError(
                message=message,
                error_code=error_code,
                status_code=status_code,
                response_data=response_data,
            )

        if error_code in VALIDATION_ERROR_CODES:
            return ValidationError(
                message=message,
                error_code=error_code,
                status_code=status_code,
                response_data=response_data,
            )

        if error_code in TRANSACTION_ERROR_CODES:
            return TransactionError(
                message=message,
                error_code=error_code,
                status_code=status_code,
                response_data=response_data,
            )

        if error_code in BUSINESS_ERROR_CODES:
            return InvalidRequestError(
                message=message,
                error_code=error_code,
                status_code=status_code,
                response_data=response_data,
            )

        if error_code in NETWORK_ERROR_CODES:
            return NetworkError(
                message=message,
                error_code=error_code,
                status_code=status_code,
                response_data=response_data,
            )

        if error_code in INTERNAL_ERROR_CODES:
            return InternalServerError(
                message=message,
                error_code=error_code,
                status_code=status_code,
                response_data=response_data,
            )
    if status_code == 401:
        return AuthenticationError(
            message=message,
            error_code=error_code,
            status_code=status_code,
            response_data=response_data,
        )
    if status_code == 400:
        return InvalidRequestError(
            message=message,
            error_code=error_code,
            status_code=status_code,
            response_data=response_data,
        )
    if status_code == 429:
        return RateLimitError(
            message=message,
            error_code=error_code,
            status_code=status_code,
            response_data=response_data,
        )
    if status_code >= 500:
        return InternalServerError(
            message=message,
            error_code=error_code,
            status_code=status_code,
            response_data=response_data,
        )

    return ATHMovilError(
        message=message,
        error_code=error_code,
        status_code=status_code,
        response_data=response_data,
    )

"""Custom exceptions for ATH Móvil API errors."""

from typing import Any

from athm.constants import ErrorCode


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


class AuthenticationError(ATHMovilError):
    """Raised when authentication with ATH Móvil API fails."""

    pass


class ValidationError(ATHMovilError):
    """Raised when request validation fails."""

    pass


class TransactionError(ATHMovilError):
    """Raised when a transaction operation fails."""

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

    kwargs = {
        "message": message,
        "error_code": error_code,
        "status_code": status_code,
        "response_data": response_data,
    }

    # Check error code first (more specific than status code)
    if error_code:
        # Authentication errors
        auth_codes = (
            ErrorCode.TOKEN_INVALID_HEADER.value,
            ErrorCode.TOKEN_EXPIRED.value,
            ErrorCode.BTRA_0401.value,
            ErrorCode.BTRA_0402.value,
            ErrorCode.BTRA_0403.value,
            ErrorCode.BTRA_0017.value,
        )
        if error_code in auth_codes:
            return AuthenticationError(**kwargs)

        # Validation errors
        validation_codes = (
            ErrorCode.BTRA_0001.value,
            ErrorCode.BTRA_0004.value,
            ErrorCode.BTRA_0006.value,
            ErrorCode.BTRA_0013.value,
            ErrorCode.BTRA_0038.value,
            ErrorCode.BTRA_0040.value,
            ErrorCode.BTRA_0003.value,
            ErrorCode.BTRA_0009.value,
            ErrorCode.BTRA_0010.value,
        )
        if error_code in validation_codes:
            return ValidationError(**kwargs)

        # Transaction errors
        transaction_codes = (
            ErrorCode.BTRA_0007.value,
            ErrorCode.BTRA_0031.value,
            ErrorCode.BTRA_0032.value,
            ErrorCode.BTRA_0037.value,
            ErrorCode.BTRA_0039.value,
        )
        if error_code in transaction_codes:
            return TransactionError(**kwargs)

        # Network errors
        if error_code == ErrorCode.BTRA_9998.value:
            return NetworkError(**kwargs)

        # Internal server errors
        if error_code == ErrorCode.BTRA_9999.value:
            return InternalServerError(**kwargs)

    # Fall back to status code
    if status_code == 401:
        return AuthenticationError(**kwargs)
    if status_code == 400:
        return ValidationError(**kwargs)
    if status_code == 429:
        return RateLimitError(**kwargs)
    if status_code >= 500:
        return InternalServerError(**kwargs)

    # Default to base exception
    return ATHMovilError(**kwargs)

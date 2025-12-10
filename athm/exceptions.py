"""Custom exceptions for ATH Móvil API errors."""

from dataclasses import dataclass
from dataclasses import field as dataclass_field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pydantic import ValidationError as PydanticValidationError

from athm.constants import (
    AUTH_ERROR_CODES,
    TRANSACTION_ERROR_CODES,
    VALIDATION_ERROR_CODES,
    ErrorCode,
)


@dataclass
class FieldError:
    """Single field validation error."""

    field: str
    message: str
    value: Any = dataclass_field(default=None)


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

    def __init__(
        self,
        message: str,
        errors: list[FieldError] | None = None,
        error_code: str | None = None,
        status_code: int | None = None,
        response_data: dict[str, Any] | None = None,
    ) -> None:
        """Initialize validation error.

        Args:
            message: Error message
            errors: List of field-level validation errors
            error_code: ATH Móvil API error code
            status_code: HTTP status code
            response_data: Full API response data
        """
        super().__init__(message, error_code, status_code, response_data)
        self.errors = errors or []

    @classmethod
    def from_pydantic(
        cls, exc: "PydanticValidationError", context: str = "request"
    ) -> "ValidationError":
        """Transform Pydantic ValidationError into clean domain error.

        Args:
            exc: Pydantic validation error
            context: Description of what was being validated (e.g., "payment request")

        Returns:
            ValidationError with clean, user-friendly messages
        """
        field_errors: list[FieldError] = []
        for error in exc.errors():
            loc = error.get("loc", ())
            field_name = ".".join(str(x) for x in loc) if loc else "unknown"
            msg_value = error.get("msg", "Invalid value")
            msg = str(msg_value) if msg_value else "Invalid value"
            # Clean up Pydantic message artifacts
            msg = msg.replace("Value error, ", "")
            field_errors.append(
                FieldError(
                    field=field_name,
                    message=msg,
                    value=error.get("input"),
                )
            )

        # Build clean summary message
        summary = f"Invalid {context}"
        if field_errors:
            details = "; ".join(f"{e.field}: {e.message}" for e in field_errors)
            summary = f"{summary}: {details}"

        return cls(message=summary, errors=field_errors)


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
    """Create appropriate exception from API response."""
    message_value = response_data.get("message")
    message: str = message_value if isinstance(message_value, str) else "Unknown error"
    error_code_value = response_data.get("errorcode")
    error_code: str | None = error_code_value if isinstance(error_code_value, str) else None

    if error_code:
        if error_code in AUTH_ERROR_CODES:
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
        if error_code == ErrorCode.BTRA_9998.value:
            return NetworkError(
                message=message,
                error_code=error_code,
                status_code=status_code,
                response_data=response_data,
            )
        if error_code == ErrorCode.BTRA_9999.value:
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
        return ValidationError(
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

"""Unit tests for exception handling."""

from athm.constants import ErrorCode
from athm.exceptions import (
    ATHMovilError,
    AuthenticationError,
    InternalServerError,
    NetworkError,
    RateLimitError,
    TimeoutError,
    TransactionError,
    ValidationError,
    create_exception_from_response,
)


class TestATHMovilError:
    def test_basic_error_creation(self):
        error = ATHMovilError("Test error message")
        assert str(error) == "Test error message"
        assert error.message == "Test error message"
        assert error.error_code is None
        assert error.status_code is None

    def test_error_with_all_fields(self):
        error = ATHMovilError(
            message="Test error",
            error_code="TEST_001",
            status_code=400,
            response_data={"field": "value"},
        )
        assert error.message == "Test error"
        assert error.error_code == "TEST_001"
        assert error.status_code == 400
        assert error.response_data == {"field": "value"}
        assert str(error) == "Test error"

    def test_error_with_error_code(self):
        error = ATHMovilError(
            message="Original message",
            error_code=ErrorCode.BTRA_0001,
        )
        assert error.message == "Original message"
        assert error.error_code == ErrorCode.BTRA_0001

    def test_error_representation(self):
        error = ATHMovilError(
            message="Test",
            error_code="CODE",
            status_code=400,
        )
        repr_str = repr(error)
        assert "ATHMovilError" in repr_str
        assert "Test" in repr_str


class TestSpecificExceptions:
    def test_authentication_error(self):
        error = AuthenticationError("Auth failed", error_code="AUTH_001")
        assert isinstance(error, ATHMovilError)
        assert error.message == "Auth failed"

    def test_validation_error(self):
        error = ValidationError("Invalid data")
        assert isinstance(error, ATHMovilError)
        assert error.message == "Invalid data"

    def test_transaction_error(self):
        error = TransactionError("Transaction failed")
        assert isinstance(error, ATHMovilError)

    def test_network_error(self):
        error = NetworkError("Connection failed")
        assert isinstance(error, ATHMovilError)

    def test_timeout_error(self):
        error = TimeoutError("Request timed out")
        assert isinstance(error, ATHMovilError)

    def test_rate_limit_error(self):
        error = RateLimitError("Rate limit exceeded")
        assert isinstance(error, ATHMovilError)

    def test_internal_server_error(self):
        error = InternalServerError("Server error")
        assert isinstance(error, ATHMovilError)


class TestCreateExceptionFromResponse:
    def test_authentication_error_codes(self):
        auth_codes = [
            ErrorCode.TOKEN_INVALID_HEADER,
            ErrorCode.TOKEN_EXPIRED,
            ErrorCode.BTRA_0401,
            ErrorCode.BTRA_0402,
            ErrorCode.BTRA_0403,
            ErrorCode.BTRA_0017,
        ]

        for code in auth_codes:
            response = {
                "status": "error",
                "message": "Auth failed",
                "errorcode": code,
            }
            error = create_exception_from_response(response, 401)
            assert isinstance(error, AuthenticationError)
            assert error.error_code == code

    def test_validation_error_codes(self):
        validation_codes = [
            ErrorCode.BTRA_0001,  # Amount below minimum
            ErrorCode.BTRA_0004,  # Amount over limits
            ErrorCode.BTRA_0006,  # Invalid format
            ErrorCode.BTRA_0013,  # Amount is zero
            ErrorCode.BTRA_0038,  # Metadata exceeds 40 chars
            ErrorCode.BTRA_0040,  # Message exceeds 50 chars
        ]

        for code in validation_codes:
            response = {
                "status": "error",
                "message": "Validation failed",
                "errorcode": code,
            }
            error = create_exception_from_response(response, 400)
            assert isinstance(error, ValidationError)
            assert error.error_code == code

    def test_transaction_error_codes(self):
        transaction_codes = [
            ErrorCode.BTRA_0007,  # TransactionId does not exist
            ErrorCode.BTRA_0031,  # EcommerceId does not exist
            ErrorCode.BTRA_0032,  # Status not confirmed
            ErrorCode.BTRA_0037,  # Cannot confirm cancelled
            ErrorCode.BTRA_0039,  # Transaction timeout
        ]

        for code in transaction_codes:
            response = {
                "status": "error",
                "message": "Transaction error",
                "errorcode": code,
            }
            error = create_exception_from_response(response, 400)
            assert isinstance(error, TransactionError)
            assert error.error_code == code

    def test_business_error_codes_map_to_validation(self):
        business_codes = [
            ErrorCode.BTRA_0003,  # Same card
            ErrorCode.BTRA_0009,  # Business not active
            ErrorCode.BTRA_0010,  # Business not active
        ]

        for code in business_codes:
            response = {
                "status": "error",
                "message": "Business error",
                "errorcode": code,
            }
            error = create_exception_from_response(response, 400)
            assert isinstance(error, ValidationError)
            assert error.error_code == code

    def test_network_error_code(self):
        response = {
            "status": "error",
            "message": "Communication error",
            "errorcode": ErrorCode.BTRA_9998,
        }
        error = create_exception_from_response(response, 500)
        assert isinstance(error, NetworkError)
        assert error.error_code == ErrorCode.BTRA_9998

    def test_internal_server_error_code(self):
        response = {
            "status": "error",
            "message": "Internal error",
            "errorcode": ErrorCode.BTRA_9999,
        }
        error = create_exception_from_response(response, 500)
        assert isinstance(error, InternalServerError)
        assert error.error_code == ErrorCode.BTRA_9999

    def test_status_code_mapping_401(self):
        response = {
            "status": "error",
            "message": "Unauthorized",
        }
        error = create_exception_from_response(response, 401)
        assert isinstance(error, AuthenticationError)
        assert error.status_code == 401

    def test_status_code_mapping_400(self):
        response = {
            "status": "error",
            "message": "Bad request",
        }
        error = create_exception_from_response(response, 400)
        assert isinstance(error, ValidationError)
        assert error.status_code == 400

    def test_status_code_mapping_429(self):
        response = {
            "status": "error",
            "message": "Too many requests",
        }
        error = create_exception_from_response(response, 429)
        assert isinstance(error, RateLimitError)
        assert error.status_code == 429

    def test_status_code_mapping_500(self):
        response = {
            "status": "error",
            "message": "Server error",
        }

        for status_code in [500, 502, 503, 504]:
            error = create_exception_from_response(response, status_code)
            assert isinstance(error, InternalServerError)
            assert error.status_code == status_code

    def test_unknown_error_code(self):
        response = {
            "status": "error",
            "message": "Unknown error",
            "errorcode": "UNKNOWN_CODE",
        }
        error = create_exception_from_response(response, 400)
        assert type(error) is ValidationError  # Falls back to status code mapping
        assert error.error_code == "UNKNOWN_CODE"

    def test_no_error_code_default(self):
        response = {
            "status": "error",
            "message": "Generic error",
        }
        error = create_exception_from_response(response, 418)  # Unknown status
        assert type(error) is ATHMovilError  # Base class
        assert error.error_code is None
        assert error.status_code == 418

    def test_error_message_from_api(self):
        response = {
            "status": "error",
            "message": "Original message from API",
            "errorcode": ErrorCode.BTRA_0001,
        }
        error = create_exception_from_response(response, 400)
        # Should use message from API response, not a lookup dict
        assert error.message == "Original message from API"

    def test_response_data_preserved(self):
        response = {
            "status": "error",
            "message": "Error occurred",
            "errorcode": "TEST_001",
            "data": {"extra": "info"},
            "additional_field": "value",
        }
        error = create_exception_from_response(response, 400)
        assert error.response_data == response
        assert error.response_data["additional_field"] == "value"

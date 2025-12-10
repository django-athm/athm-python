"""Unit tests for exception handling."""

from pydantic import BaseModel, field_validator

from athm.constants import ErrorCode
from athm.exceptions import (
    ATHMovilError,
    AuthenticationError,
    FieldError,
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


class TestFieldError:
    def test_field_error_creation(self):
        error = FieldError(field="total", message="Must be at least $1.00")
        assert error.field == "total"
        assert error.message == "Must be at least $1.00"
        assert error.value is None

    def test_field_error_with_value(self):
        error = FieldError(field="amount", message="Invalid value", value="0.50")
        assert error.field == "amount"
        assert error.message == "Invalid value"
        assert error.value == "0.50"


class TestValidationErrorFromPydantic:
    """Tests for ValidationError.from_pydantic() classmethod."""

    def test_from_pydantic_single_error(self):
        class TestModel(BaseModel):
            amount: float

            @field_validator("amount")
            @classmethod
            def validate_amount(cls, v: float) -> float:
                if v < 1.0:
                    raise ValueError("Amount must be at least $1.00")
                return v

        try:
            TestModel(amount=0.50)
        except Exception as pydantic_exc:
            error = ValidationError.from_pydantic(pydantic_exc, context="payment")
            assert "Invalid payment" in error.message
            assert "amount: Amount must be at least $1.00" in error.message
            assert len(error.errors) == 1
            assert error.errors[0].field == "amount"
            assert error.errors[0].message == "Amount must be at least $1.00"
            assert error.errors[0].value == 0.50

    def test_from_pydantic_multiple_errors(self):
        class TestModel(BaseModel):
            name: str
            age: int

        try:
            TestModel(name=123, age="not a number")  # type: ignore[arg-type]
        except Exception as pydantic_exc:
            error = ValidationError.from_pydantic(pydantic_exc, context="user data")
            assert "Invalid user data" in error.message
            assert len(error.errors) == 2

    def test_from_pydantic_no_pydantic_leakage(self):
        class TestModel(BaseModel):
            value: int

        try:
            TestModel(value="not a number")  # type: ignore[arg-type]
        except Exception as pydantic_exc:
            error = ValidationError.from_pydantic(pydantic_exc, context="test")
            # Should not contain pydantic references
            assert "pydantic" not in error.message.lower()
            assert "errors.pydantic.dev" not in error.message

    def test_from_pydantic_cleans_value_error_prefix(self):
        class TestModel(BaseModel):
            field: str

            @field_validator("field")
            @classmethod
            def validate_field(cls, v: str) -> str:
                raise ValueError("Custom error message")

        try:
            TestModel(field="test")
        except Exception as pydantic_exc:
            error = ValidationError.from_pydantic(pydantic_exc, context="test")
            # Should not have "Value error, " prefix
            assert "Value error, " not in error.errors[0].message
            assert error.errors[0].message == "Custom error message"

    def test_from_pydantic_nested_field_location(self):
        class Inner(BaseModel):
            value: int

        class Outer(BaseModel):
            inner: Inner

        try:
            Outer(inner={"value": "not a number"})  # type: ignore[arg-type]
        except Exception as pydantic_exc:
            error = ValidationError.from_pydantic(pydantic_exc, context="nested")
            assert len(error.errors) == 1
            # Field should include full path
            assert error.errors[0].field == "inner.value"

    def test_validation_error_with_errors_attribute(self):
        error = ValidationError(
            message="Test error",
            errors=[
                FieldError(field="a", message="Error A"),
                FieldError(field="b", message="Error B"),
            ],
        )
        assert len(error.errors) == 2
        assert error.errors[0].field == "a"
        assert error.errors[1].field == "b"

    def test_validation_error_default_empty_errors(self):
        error = ValidationError(message="Simple error")
        assert error.errors == []


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

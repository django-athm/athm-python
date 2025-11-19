"""Constants and error codes for ATH Móvil API."""

from enum import Enum


class ErrorCode(str, Enum):
    """ATH Móvil API error codes."""

    TOKEN_INVALID_HEADER = "token.invalid.header"
    TOKEN_EXPIRED = "token.expired"
    BTRA_0401 = "BTRA_0401"
    BTRA_0402 = "BTRA_0402"
    BTRA_0403 = "BTRA_0403"
    BTRA_0017 = "BTRA_0017"
    BTRA_0001 = "BTRA_0001"
    BTRA_0003 = "BTRA_0003"
    BTRA_0004 = "BTRA_0004"
    BTRA_0006 = "BTRA_0006"
    BTRA_0007 = "BTRA_0007"
    BTRA_0009 = "BTRA_0009"
    BTRA_0010 = "BTRA_0010"
    BTRA_0013 = "BTRA_0013"
    BTRA_0031 = "BTRA_0031"
    BTRA_0032 = "BTRA_0032"
    BTRA_0037 = "BTRA_0037"
    BTRA_0038 = "BTRA_0038"
    BTRA_0039 = "BTRA_0039"
    BTRA_0040 = "BTRA_0040"
    BTRA_9998 = "BTRA_9998"
    BTRA_9999 = "BTRA_9999"


AUTHENTICATION_ERROR_CODES: set[str] = {
    ErrorCode.TOKEN_INVALID_HEADER,
    ErrorCode.TOKEN_EXPIRED,
    ErrorCode.BTRA_0401,
    ErrorCode.BTRA_0402,
    ErrorCode.BTRA_0403,
    ErrorCode.BTRA_0017,
}

VALIDATION_ERROR_CODES: set[str] = {
    ErrorCode.BTRA_0001,
    ErrorCode.BTRA_0004,
    ErrorCode.BTRA_0006,
    ErrorCode.BTRA_0013,
    ErrorCode.BTRA_0038,
    ErrorCode.BTRA_0040,
}

TRANSACTION_ERROR_CODES: set[str] = {
    ErrorCode.BTRA_0007,
    ErrorCode.BTRA_0031,
    ErrorCode.BTRA_0032,
    ErrorCode.BTRA_0037,
    ErrorCode.BTRA_0039,
}

BUSINESS_ERROR_CODES: set[str] = {
    ErrorCode.BTRA_0003,
    ErrorCode.BTRA_0009,
    ErrorCode.BTRA_0010,
}

NETWORK_ERROR_CODES: set[str] = {ErrorCode.BTRA_9998}

INTERNAL_ERROR_CODES: set[str] = {ErrorCode.BTRA_9999}

ERROR_MESSAGES: dict[str, str] = {
    ErrorCode.TOKEN_INVALID_HEADER: "No authorization header provided",
    ErrorCode.TOKEN_EXPIRED: "Authorization token has expired",
    ErrorCode.BTRA_0401: "Authorization token issue",
    ErrorCode.BTRA_0402: "Authorization token issue",
    ErrorCode.BTRA_0403: "Authorization token issue",
    ErrorCode.BTRA_0017: "Invalid authorization token",
    ErrorCode.BTRA_0001: "Amount is below minimum ($1.00)",
    ErrorCode.BTRA_0003: "Customer card cannot be the same as business card",
    ErrorCode.BTRA_0004: "Amount exceeds maximum limit ($1,500.00)",
    ErrorCode.BTRA_0006: "Invalid format or required body missing",
    ErrorCode.BTRA_0007: "Transaction ID does not exist",
    ErrorCode.BTRA_0009: "Business is not active",
    ErrorCode.BTRA_0010: "Business is not active",
    ErrorCode.BTRA_0013: "Amount cannot be zero",
    ErrorCode.BTRA_0031: "Ecommerce ID does not exist",
    ErrorCode.BTRA_0032: "E-commerce transaction status is not confirmed",
    ErrorCode.BTRA_0037: "Cannot confirm cancelled or failed transaction",
    ErrorCode.BTRA_0038: "Metadata exceeds 40 characters",
    ErrorCode.BTRA_0039: "Transaction timeout has expired",
    ErrorCode.BTRA_0040: "Message exceeds 50 characters",
    ErrorCode.BTRA_9998: "Communication error with ATH Móvil services",
    ErrorCode.BTRA_9999: "Internal server error",
}


BASE_URL = "https://payments.athmovil.com"
API_VERSION = "v1"

ENDPOINTS = {
    "payment": "/api/business-transaction/ecommerce/payment",
    "find_payment": "/api/business-transaction/ecommerce/business/findPayment",
    "authorization": "/api/business-transaction/ecommerce/authorization",
    "update_phone": "/api/business-transaction/ecommerce/business/updatePhoneNumber",
    "refund": "/api/business-transaction/ecommerce/refund",
    "cancel": "/api/business-transaction/ecommerce/business/cancel",
}

MIN_AMOUNT = 1.00
MAX_AMOUNT = 1500.00
MIN_TIMEOUT = 120
MAX_TIMEOUT = 600
DEFAULT_TIMEOUT = 600
MAX_METADATA_LENGTH = 40
MAX_MESSAGE_LENGTH = 50

REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY = 1

DEFAULT_HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
}

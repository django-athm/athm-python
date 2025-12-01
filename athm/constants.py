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


BASE_URL = "https://payments.athmovil.com"
API_VERSION = "v1"

# Webhook subscription uses a different base URL
# Ref: https://github.com/evertec/athmovil-webhooks?tab=readme-ov-file#using-a-web-service
WEBHOOK_BASE_URL = "https://www.athmovil.com"
WEBHOOK_SUBSCRIBE_ENDPOINT = "/transactions/webhook/post"

ENDPOINTS = {
    "payment": "/api/business-transaction/ecommerce/payment",
    "find_payment": "/api/business-transaction/ecommerce/business/findPayment",
    "authorization": "/api/business-transaction/ecommerce/authorization",
    "update_phone": "/api/business-transaction/ecommerce/business/updatePhoneNumber",
    "refund": "/api/business-transaction/ecommerce/refund",
    "cancel": "/api/business-transaction/ecommerce/business/cancel",
}

# Business rules from ATH Móvil API
MIN_AMOUNT = 1.00
MAX_AMOUNT = 1500.00
MIN_TIMEOUT = 120
DEFAULT_TIMEOUT = 600
MAX_METADATA_LENGTH = 40
MAX_MESSAGE_LENGTH = 50

# HTTP client configuration
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3

DEFAULT_HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
}

# Error code categories for exception mapping
AUTH_ERROR_CODES = frozenset(
    {
        ErrorCode.TOKEN_INVALID_HEADER.value,
        ErrorCode.TOKEN_EXPIRED.value,
        ErrorCode.BTRA_0401.value,
        ErrorCode.BTRA_0402.value,
        ErrorCode.BTRA_0403.value,
        ErrorCode.BTRA_0017.value,
    }
)

VALIDATION_ERROR_CODES = frozenset(
    {
        ErrorCode.BTRA_0001.value,
        ErrorCode.BTRA_0004.value,
        ErrorCode.BTRA_0006.value,
        ErrorCode.BTRA_0013.value,
        ErrorCode.BTRA_0038.value,
        ErrorCode.BTRA_0040.value,
        ErrorCode.BTRA_0003.value,
        ErrorCode.BTRA_0009.value,
        ErrorCode.BTRA_0010.value,
    }
)

TRANSACTION_ERROR_CODES = frozenset(
    {
        ErrorCode.BTRA_0007.value,
        ErrorCode.BTRA_0031.value,
        ErrorCode.BTRA_0032.value,
        ErrorCode.BTRA_0037.value,
        ErrorCode.BTRA_0039.value,
    }
)

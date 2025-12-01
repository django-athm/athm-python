"""ATH Móvil Unofficial Library.

A modern Python library for integrating with the ATH Móvil payment API.
"""

from athm.client import ATHMovilClient
from athm.exceptions import (
    ATHMovilError,
    AuthenticationError,
    InternalServerError,
    NetworkError,
    RateLimitError,
    TimeoutError,
    TransactionError,
    ValidationError,
)
from athm.models import (
    PaymentItem,
    PaymentRequest,
    PaymentResponse,
    RefundRequest,
    RefundResponse,
    TransactionData,
    TransactionResponse,
    TransactionStatus,
)
from athm.webhooks import (
    WebhookEventType,
    WebhookItem,
    WebhookPayload,
    WebhookStatus,
    WebhookSubscriptionRequest,
    parse_webhook,
)

__version__ = "0.3.0"
__author__ = "Raúl Negrón-Otero"
__email__ = "raul.esteban.negron@gmail.com"

__all__ = [
    "ATHMovilClient",
    "ATHMovilError",
    "AuthenticationError",
    "InternalServerError",
    "NetworkError",
    "PaymentItem",
    "PaymentRequest",
    "PaymentResponse",
    "RateLimitError",
    "RefundRequest",
    "RefundResponse",
    "TimeoutError",
    "TransactionData",
    "TransactionError",
    "TransactionResponse",
    "TransactionStatus",
    "ValidationError",
    "WebhookEventType",
    "WebhookItem",
    "WebhookPayload",
    "WebhookStatus",
    "WebhookSubscriptionRequest",
    "parse_webhook",
]

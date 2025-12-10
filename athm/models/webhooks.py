"""Pydantic models for ATH Movil webhook payloads.

Ref: https://github.com/evertec/athmovil-webhooks
"""

from datetime import datetime
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Any

from pydantic import Field, field_validator, model_validator

from athm.models.base import ATHMovilBaseModel


class WebhookEventType(str, Enum):
    """Webhook event types from ATH Movil.

    Ref: https://github.com/evertec/athmovil-webhooks#transaction-types

    Attributes:
        SIMULATED: Test/simulated payment event
        PAYMENT: Standard payment received
        DONATION: Donation received
        REFUND: Refund sent to customer
        ECOMMERCE: eCommerce transaction (completed, cancelled, or expired)
    """

    SIMULATED = "simulated"
    PAYMENT = "payment"
    DONATION = "donation"
    REFUND = "refund"
    ECOMMERCE = "ecommerce"


class WebhookStatus(str, Enum):
    """Webhook payload status values.

    Ref: https://github.com/evertec/athmovil-webhooks#event-types
    """

    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class WebhookItem(ATHMovilBaseModel):
    """Item in webhook payload.

    Ref: https://github.com/evertec/athmovil-webhooks#webhook-payload-structure
    """

    name: str
    description: str
    price: Decimal
    quantity: int
    tax: Decimal | None = None
    metadata: str | None = None
    sku: str | None = None
    formatted_price: str | None = Field(None, alias="formattedPrice")

    @field_validator("price", "tax", mode="before")
    @classmethod
    def normalize_decimal(cls, v: str | int | float | None) -> Decimal | None:
        """Convert string or number amounts to Decimal."""
        if v is None or v == "":
            return None
        try:
            return Decimal(str(v))
        except InvalidOperation as e:
            raise ValueError(f"Invalid decimal value: {v}") from e

    @field_validator("quantity", mode="before")
    @classmethod
    def normalize_quantity(cls, v: str | int) -> int:
        """Convert quantity to int."""
        return int(v)


class WebhookPayload(ATHMovilBaseModel):
    """Parsed and normalized webhook payload from ATH Movil.

    This model normalizes the various inconsistencies in the ATH Movil webhook API:
    - Field naming (dailyTransactionID vs dailyTransactionId, subTotal vs subtotal)
    - Data types (string decimals vs numbers)
    - Status values (CANCEL -> cancelled, COMPLETED -> completed)
    - Transaction types (ECOMMERCE -> ecommerce)

    Ref: https://github.com/evertec/athmovil-webhooks#webhook-payload-structure
    """

    # Transaction identification
    transaction_type: WebhookEventType = Field(..., alias="transactionType")
    status: WebhookStatus
    reference_number: str | None = Field(None, alias="referenceNumber")
    daily_transaction_id: str | None = None

    # Timestamps
    date: datetime
    transaction_date: datetime | None = None  # eCommerce only

    # Customer info
    name: str | None = None
    phone_number: str | None = Field(None, alias="phoneNumber")
    email: str | None = None
    message: str | None = None

    # Amounts (normalized to Decimal)
    total: Decimal
    tax: Decimal | None = None
    subtotal: Decimal | None = None
    fee: Decimal | None = None
    net_amount: Decimal | None = Field(None, alias="netAmount")
    total_refunded_amount: Decimal | None = None

    # Metadata
    metadata1: str | None = None
    metadata2: str | None = None
    items: list[WebhookItem] = Field(default_factory=lambda: [])

    # eCommerce-specific fields
    ecommerce_id: str | None = Field(None, alias="ecommerceId")
    business_name: str | None = Field(None, alias="businessName")
    is_non_profit: bool | None = Field(None, alias="isNonProfit")
    reference_transaction_id: str | None = Field(None, alias="referenceTransactionId")

    @model_validator(mode="before")
    @classmethod
    def normalize_field_names(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Handle API field name inconsistencies.

        The ATH Movil webhook API has inconsistent field naming:
        - dailyTransactionID (standard events) vs dailyTransactionId (eCommerce)
        - subTotal (eCommerce) vs subtotal (standard events)
        - totalRefundedAmount needs snake_case conversion

        Ref: https://github.com/evertec/athmovil-webhooks#webhook-payload-structure
        """
        # dailyTransactionID or dailyTransactionId -> daily_transaction_id
        if "dailyTransactionID" in data:
            data["daily_transaction_id"] = data.pop("dailyTransactionID")
        elif "dailyTransactionId" in data:
            data["daily_transaction_id"] = data.pop("dailyTransactionId")

        # subTotal -> subtotal (eCommerce events use subTotal)
        if "subTotal" in data and "subtotal" not in data:
            data["subtotal"] = data.pop("subTotal")

        # totalRefundedAmount -> total_refunded_amount
        if "totalRefundedAmount" in data:
            data["total_refunded_amount"] = data.pop("totalRefundedAmount")

        # transactionDate -> transaction_date (eCommerce only)
        if "transactionDate" in data:
            data["transaction_date"] = data.pop("transactionDate")

        return data

    @field_validator("transaction_type", mode="before")
    @classmethod
    def normalize_transaction_type(cls, v: object) -> str:
        """Normalize transaction type to lowercase.

        The API returns "ECOMMERCE" for completed/cancelled events
        but "ecommerce" for expired events.

        Ref: https://github.com/evertec/athmovil-webhooks#event-types
        """
        if isinstance(v, str):
            return v.lower()
        return str(v).lower()

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, v: object) -> str:
        """Normalize status values.

        The API returns:
        - "completed" for standard events
        - "COMPLETED" for eCommerce completed
        - "CANCEL" for eCommerce cancelled (note: not "CANCELLED")
        - "expired" for eCommerce expired

        We normalize to: completed, cancelled, expired

        Ref: https://github.com/evertec/athmovil-webhooks#event-types
        """
        status = str(v).lower() if v else ""
        if status == "cancel":
            return "cancelled"
        return status

    @field_validator(
        "total", "tax", "subtotal", "fee", "net_amount", "total_refunded_amount", mode="before"
    )
    @classmethod
    def normalize_decimal(cls, v: str | int | float | None) -> Decimal | None:
        """Convert string or number amounts to Decimal.

        Standard events send amounts as strings ("3.00").
        eCommerce events send amounts as numbers (3.00).

        Ref: https://github.com/evertec/athmovil-webhooks#webhook-payload-structure
        """
        if v is None or v == "":
            return None
        try:
            return Decimal(str(v))
        except InvalidOperation as e:
            raise ValueError(f"Invalid decimal value: {v}") from e

    @field_validator("date", "transaction_date", mode="before")
    @classmethod
    def parse_datetime(cls, v: str | datetime | None) -> datetime | None:
        """Parse datetime strings from webhook payload."""
        if v is None or v == "":
            return None
        if isinstance(v, datetime):
            return v

        # Normalize fractional seconds to 6 digits for %f compatibility
        # ATH Movil sends variable-length fractions like ".0", ".00", etc.
        if "." in v:
            base, frac = v.rsplit(".", 1)
            if frac.isdigit():
                v = f"{base}.{frac.ljust(6, '0')}"

        # Try common formats from ATH Movil webhooks
        for fmt in (
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
        ):
            try:
                return datetime.strptime(v, fmt)
            except ValueError:
                continue
        raise ValueError(f"Unable to parse datetime: {v}")

    @field_validator("phone_number", mode="before")
    @classmethod
    def normalize_phone(cls, v: str | int | None) -> str | None:
        """Convert phone number to string (API sometimes sends as number)."""
        if v is None:
            return None
        return str(v)


class WebhookSubscriptionRequest(ATHMovilBaseModel):
    """Request model for webhook subscription.

    Ref: https://github.com/evertec/athmovil-webhooks#subscribe-via-web-service
    """

    public_token: str = Field(..., alias="publicToken")
    private_token: str = Field(..., alias="privateToken")
    listener_url: str = Field(..., alias="listenerURL")
    payment_received_event: bool = Field(True, alias="paymentReceivedEvent")
    refund_sent_event: bool = Field(True, alias="refundSentEvent")
    donation_received_event: bool = Field(False, alias="donationReceivedEvent")
    ecommerce_payment_received_event: bool = Field(True, alias="ecommercePaymentReceivedEvent")
    ecommerce_payment_cancelled_event: bool = Field(True, alias="ecommercePaymentCancelledEvent")
    ecommerce_payment_expired_event: bool = Field(True, alias="ecommercePaymentExpiredEvent")

    @field_validator("listener_url")
    @classmethod
    def validate_https(cls, v: str) -> str:
        """Ensure listener URL uses HTTPS.

        ATH Movil requires HTTPS for webhook endpoints and rejects
        self-signed certificates.

        Ref: https://github.com/evertec/athmovil-webhooks#prerequisites
        """
        if not v.startswith("https://"):
            raise ValueError("Webhook listener URL must use HTTPS")
        return v

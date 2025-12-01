"""Pydantic models for ATH Movil payment API data structures."""

from datetime import datetime
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Annotated, Any

from pydantic import BeforeValidator, Field, field_validator, model_validator

from athm.models.base import ATHMovilBaseModel

# Shared constants
PHONE_NUMBER_PATTERN = r"^\d{10}$"


def _to_str(v: str | int | None) -> str | None:
    """Convert value to string if not None."""
    return str(v) if v is not None else None


def _validate_decimal(
    v: str | int | float,
    *,
    min_value: Decimal | None = None,
    max_value: Decimal | None = None,
    positive_only: bool = False,
    non_negative: bool = False,
) -> str:
    """Validate and format decimal amount to 2 decimal places."""
    try:
        decimal_val = Decimal(str(v))
    except InvalidOperation as e:
        raise ValueError(f"Invalid amount format: {v}") from e
    if positive_only and decimal_val <= 0:
        raise ValueError("Amount must be positive")
    if non_negative and decimal_val < 0:
        raise ValueError("Amount cannot be negative")
    if min_value is not None and decimal_val < min_value:
        raise ValueError(f"Total must be at least ${min_value}")
    if max_value is not None and decimal_val > max_value:
        raise ValueError(f"Total cannot exceed ${max_value}")
    return str(decimal_val.quantize(Decimal("0.01")))


# Reusable type for daily transaction ID (handles int-to-str conversion)
DailyTransactionId = Annotated[str | None, BeforeValidator(_to_str)]


class TransactionStatus(str, Enum):
    """Possible transaction status values."""

    OPEN = "OPEN"
    CONFIRM = "CONFIRM"
    COMPLETED = "COMPLETED"
    CANCEL = "CANCEL"


class PaymentItem(ATHMovilBaseModel):
    """Item in a payment request."""

    name: str = Field(..., max_length=255)
    description: str = Field(..., max_length=255)
    quantity: str
    price: str
    tax: str | None = None
    metadata: str | None = Field(None, max_length=255)
    sku: str | None = Field(None, max_length=100)
    formatted_price: str | None = Field(None, alias="formattedPrice")

    @field_validator("price", "tax", mode="before")
    @classmethod
    def validate_amount(cls, v: str | int | float | None) -> str | None:
        """Validate amount fields."""
        if v is None:
            return None
        return _validate_decimal(v, non_negative=True)

    @field_validator("quantity", mode="before")
    @classmethod
    def validate_quantity(cls, v: str | int) -> str:
        """Validate quantity is positive integer."""
        qty = int(v)
        if qty <= 0:
            raise ValueError("Quantity must be positive")
        return str(qty)


class PaymentRequest(ATHMovilBaseModel):
    """Request model for creating a payment."""

    public_token: str = Field(..., alias="publicToken")
    timeout: str = Field(default="600")
    total: str
    tax: str | None = None
    subtotal: str | None = None
    metadata1: str = Field(..., max_length=40)
    metadata2: str = Field(..., max_length=40)
    items: list[PaymentItem]
    phone_number: str = Field(..., alias="phoneNumber", pattern=PHONE_NUMBER_PATTERN)

    @field_validator("total")
    @classmethod
    def validate_total(cls, v: str) -> str:
        """Validate total amount."""
        return _validate_decimal(v, min_value=Decimal("1.00"), max_value=Decimal("1500.00"))

    @field_validator("tax", "subtotal")
    @classmethod
    def validate_amount(cls, v: str | None) -> str | None:
        """Validate tax and subtotal amounts."""
        if v is None:
            return None
        return _validate_decimal(v, non_negative=True, max_value=Decimal("1500.00"))

    @field_validator("timeout")
    @classmethod
    def validate_timeout(cls, v: str) -> str:
        """Validate timeout is at least 120 seconds."""
        timeout_val = int(v)
        if timeout_val < 120:
            raise ValueError("Timeout must be at least 120 seconds")
        return str(timeout_val)

    @model_validator(mode="after")
    def validate_totals(self) -> "PaymentRequest":
        """Validate that total equals subtotal plus tax when both are provided."""
        if self.subtotal and self.tax:
            subtotal_val = Decimal(self.subtotal)
            tax_val = Decimal(self.tax)
            total_val = Decimal(self.total)
            calculated_total = subtotal_val + tax_val
            if calculated_total != total_val:
                raise ValueError(
                    f"Total ({total_val}) must equal subtotal ({subtotal_val}) + tax ({tax_val})"
                )
        return self


class PaymentData(ATHMovilBaseModel):
    """Data returned from payment creation."""

    ecommerce_id: str = Field(..., alias="ecommerceId")
    auth_token: str


class PaymentResponse(ATHMovilBaseModel):
    """Response from payment creation."""

    status: str
    data: PaymentData


class FindPaymentRequest(ATHMovilBaseModel):
    """Request model for finding a payment."""

    ecommerce_id: str = Field(..., alias="ecommerceId")
    public_token: str = Field(..., alias="publicToken")


class TransactionData(ATHMovilBaseModel):
    """Detailed transaction information."""

    ecommerce_status: TransactionStatus = Field(..., alias="ecommerceStatus")
    ecommerce_id: str = Field(..., alias="ecommerceId")
    reference_number: str | None = Field(None, alias="referenceNumber")
    business_customer_id: str | None = Field(None, alias="businessCustomerId")
    transaction_date: datetime | None = Field(None, alias="transactionDate")
    daily_transaction_id: DailyTransactionId = Field(None, alias="dailyTransactionId")
    business_name: str | None = Field(None, alias="businessName")
    business_path: str | None = Field(None, alias="businessPath")
    industry: str | None = None
    subtotal: Decimal | None = Field(None, alias="subTotal")
    tax: Decimal | None = None
    total: Decimal | None = None
    fee: Decimal | None = None
    net_amount: Decimal | None = Field(None, alias="netAmount")
    total_refunded_amount: Decimal | None = Field(None, alias="totalRefundedAmount")
    metadata1: str | None = None
    metadata2: str | None = None
    items: list[PaymentItem] | None = None
    is_non_profit: bool | None = Field(None, alias="isNonProfit")

    @field_validator("transaction_date", mode="before")
    @classmethod
    def parse_transaction_date(cls, v: str | datetime | None) -> datetime | None:
        """Parse transaction date string."""
        if v is None or v == "":
            return None
        if isinstance(v, datetime):
            return v
        return datetime.strptime(v, "%Y-%m-%d %H:%M:%S")


class TransactionResponse(ATHMovilBaseModel):
    """Response from transaction status check."""

    status: str
    data: TransactionData | None = None


class UpdatePhoneRequest(ATHMovilBaseModel):
    """Request model for updating phone number."""

    ecommerce_id: str = Field(..., alias="ecommerceId")
    phone_number: str = Field(..., alias="phoneNumber", pattern=PHONE_NUMBER_PATTERN)


class CancelPaymentRequest(ATHMovilBaseModel):
    """Request model for canceling a payment."""

    ecommerce_id: str = Field(..., alias="ecommerceId")
    public_token: str = Field(..., alias="publicToken")


class RefundRequest(ATHMovilBaseModel):
    """Request model for processing a refund."""

    public_token: str = Field(..., alias="publicToken")
    private_token: str = Field(..., alias="privateToken")
    reference_number: str = Field(..., alias="referenceNumber")
    amount: str
    message: str | None = Field(None, max_length=50)

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: str) -> str:
        """Validate refund amount is positive."""
        return _validate_decimal(v, positive_only=True)


class RefundTransaction(ATHMovilBaseModel):
    """Refund transaction details."""

    transaction_type: str | None = Field(None, alias="transactionType")
    status: str | None = None
    refunded_amount: Decimal | None = Field(None, alias="refundedAmount")
    date: str | None = None  # Timestamp string
    reference_number: str | None = Field(None, alias="referenceNumber")
    daily_transaction_id: DailyTransactionId = Field(None, alias="dailyTransactionId")
    name: str | None = None
    phone_number: str | None = Field(None, alias="phoneNumber")
    email: str | None = None


class OriginalTransaction(ATHMovilBaseModel):
    """Original transaction details in refund response."""

    transaction_type: str | None = Field(None, alias="transactionType")
    status: str | None = None
    date: str | None = None  # Timestamp string
    reference_number: str | None = Field(None, alias="referenceNumber")
    daily_transaction_id: DailyTransactionId = Field(None, alias="dailyTransactionId")
    name: str | None = None
    phone_number: str | None = Field(None, alias="phoneNumber")
    email: str | None = None
    message: str | None = None
    total: Decimal | None = None
    tax: Decimal | None = None
    subtotal: Decimal | None = Field(None, alias="subTotal")
    fee: Decimal | None = None
    net_amount: Decimal | None = Field(None, alias="netAmount")
    total_refunded_amount: Decimal | None = Field(None, alias="totalRefundedAmount")
    metadata1: str | None = None
    metadata2: str | None = None
    items: list[PaymentItem] | None = None


class RefundData(ATHMovilBaseModel):
    """Data returned from refund request."""

    refund: RefundTransaction
    original_transaction: OriginalTransaction = Field(..., alias="originalTransaction")


class RefundResponse(ATHMovilBaseModel):
    """Response from refund request."""

    status: str
    data: RefundData


class APIError(ATHMovilBaseModel):
    """API error response."""

    status: str
    message: str
    errorcode: str | None = None
    data: Any | None = None


class SuccessResponse(ATHMovilBaseModel):
    """Generic success response."""

    status: str
    data: dict[str, Any] | str | None = None

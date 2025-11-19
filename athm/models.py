"""Pydantic models for ATH Móvil API data structures."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class TransactionStatus(str, Enum):
    """Possible transaction status values."""

    OPEN = "OPEN"
    CONFIRM = "CONFIRM"
    COMPLETED = "COMPLETED"
    CANCEL = "CANCEL"


class PaymentItem(BaseModel):
    """Item in a payment request."""

    model_config = ConfigDict(populate_by_name=True)

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
        """Validate and format amount fields to two decimal places."""
        if v is None:
            return v
        try:
            decimal_val = Decimal(str(v))
            if decimal_val < 0:
                raise ValueError("Amount cannot be negative")
            return str(decimal_val.quantize(Decimal("0.01")))
        except Exception as e:
            raise ValueError(f"Invalid amount format: {e}") from e

    @field_validator("quantity", mode="before")
    @classmethod
    def validate_quantity(cls, v: str | int) -> str:
        """Validate quantity is a positive integer."""
        try:
            qty = int(v)
            if qty <= 0:
                raise ValueError("Quantity must be positive")
            return str(qty)
        except ValueError as e:
            raise ValueError(f"Invalid quantity: {e}") from e


class PaymentRequest(BaseModel):
    """Request model for creating a payment."""

    model_config = ConfigDict(populate_by_name=True)

    public_token: str = Field(..., alias="publicToken")
    timeout: str = Field(default="600")
    total: str
    tax: str | None = None
    subtotal: str | None = None
    metadata1: str | None = Field(None, max_length=40)
    metadata2: str | None = Field(None, max_length=40)
    items: list[PaymentItem]
    phone_number: str = Field(..., alias="phoneNumber", pattern=r"^\d{10}$")

    @field_validator("total")
    @classmethod
    def validate_total(cls, v: str) -> str:
        """Validate total amount is between $1.00 and $1,500.00."""
        try:
            decimal_val = Decimal(v)
            if decimal_val < Decimal("1.00"):
                raise ValueError("Total must be at least $1.00")
            if decimal_val > Decimal("1500.00"):
                raise ValueError("Total cannot exceed $1,500.00")
            return str(decimal_val.quantize(Decimal("0.01")))
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"Invalid amount format: {e}") from e

    @field_validator("tax", "subtotal")
    @classmethod
    def validate_amount(cls, v: str | None) -> str | None:
        """Validate tax and subtotal amounts are non-negative and below $1,500.00."""
        if v is None:
            return v
        try:
            decimal_val = Decimal(v)
            if decimal_val < Decimal("0.00"):
                raise ValueError("Amount cannot be negative")
            if decimal_val > Decimal("1500.00"):
                raise ValueError("Amount cannot exceed $1,500.00")
            return str(decimal_val.quantize(Decimal("0.01")))
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"Invalid amount format: {e}") from e

    @field_validator("timeout")
    @classmethod
    def validate_timeout(cls, v: str) -> str:
        """Validate timeout is at least 120 seconds."""
        try:
            timeout_val = int(v)
            if timeout_val < 120:
                raise ValueError("Timeout must be at least 120 seconds")
            return str(timeout_val)
        except ValueError as e:
            raise ValueError(f"Invalid timeout: {e}") from e

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


class PaymentData(BaseModel):
    """Data returned from payment creation."""

    model_config = ConfigDict(populate_by_name=True)

    ecommerce_id: str = Field(..., alias="ecommerceId")
    auth_token: str


class PaymentResponse(BaseModel):
    """Response from payment creation."""

    status: str
    data: PaymentData


class FindPaymentRequest(BaseModel):
    """Request model for finding a payment."""

    model_config = ConfigDict(populate_by_name=True)

    ecommerce_id: str = Field(..., alias="ecommerceId")
    public_token: str = Field(..., alias="publicToken")


class TransactionData(BaseModel):
    """Detailed transaction information."""

    model_config = ConfigDict(populate_by_name=True)

    ecommerce_status: TransactionStatus = Field(..., alias="ecommerceStatus")
    ecommerce_id: str = Field(..., alias="ecommerceId")
    reference_number: str | None = Field(None, alias="referenceNumber")
    business_customer_id: str | None = Field(None, alias="businessCustomerId")
    transaction_date: datetime | None = Field(None, alias="transactionDate")
    daily_transaction_id: str | None = Field(None, alias="dailyTransactionId")
    business_name: str | None = Field(None, alias="businessName")
    business_path: str | None = Field(None, alias="businessPath")
    industry: str | None = None
    sub_total: Decimal | None = Field(None, alias="subTotal")
    tax: Decimal | None = None
    total: Decimal | None = None
    fee: Decimal | None = None
    net_amount: Decimal | None = Field(None, alias="netAmount")
    total_refunded_amount: Decimal | None = Field(None, alias="totalRefundedAmount")
    metadata1: str | None = None
    metadata2: str | None = None
    items: list[PaymentItem] | None = None
    is_non_profit: bool | None = Field(None, alias="isNonProfit")

    @field_validator("daily_transaction_id", mode="before")
    @classmethod
    def convert_daily_transaction_id(cls, v: str | int | None) -> str | None:
        """Convert daily transaction ID to string format."""
        if v is None:
            return v
        return str(v)

    @field_validator("transaction_date", mode="before")
    @classmethod
    def parse_transaction_date(cls, v: str | datetime | None) -> datetime | None:
        """Parse transaction date string to datetime object."""
        if v is None or v == "":
            return None
        if isinstance(v, datetime):
            return v
        if isinstance(v, str):
            try:
                return datetime.strptime(v, "%Y-%m-%d %H:%M:%S")
            except ValueError as e:
                raise ValueError(f"Invalid transaction_date format: {e}") from e
        raise ValueError(f"Unexpected type for transaction_date: {type(v)}")


class TransactionResponse(BaseModel):
    """Response from transaction status check."""

    status: str
    data: TransactionData | None = None


class UpdatePhoneRequest(BaseModel):
    """Request model for updating phone number."""

    model_config = ConfigDict(populate_by_name=True)

    ecommerce_id: str = Field(..., alias="ecommerceId")
    phone_number: str = Field(..., alias="phoneNumber", pattern=r"^\d{10}$")


class CancelPaymentRequest(BaseModel):
    """Request model for canceling a payment."""

    model_config = ConfigDict(populate_by_name=True)

    ecommerce_id: str = Field(..., alias="ecommerceId")
    public_token: str = Field(..., alias="publicToken")


class RefundRequest(BaseModel):
    """Request model for processing a refund."""

    model_config = ConfigDict(populate_by_name=True)

    public_token: str = Field(..., alias="publicToken")
    private_token: str = Field(..., alias="privateToken")
    reference_number: str = Field(..., alias="referenceNumber")
    amount: str
    message: str | None = Field(None, max_length=50)

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: str) -> str:
        """Validate refund amount is positive and properly formatted."""
        try:
            decimal_val = Decimal(v)
            if decimal_val <= 0:
                raise ValueError("Refund amount must be positive")
            return str(decimal_val.quantize(Decimal("0.01")))
        except Exception as e:
            raise ValueError(f"Invalid amount format: {e}") from e


class RefundTransaction(BaseModel):
    """Refund transaction details."""

    model_config = ConfigDict(populate_by_name=True)

    transaction_type: str | None = Field(None, alias="transactionType")
    status: str | None = None
    refunded_amount: Decimal | None = Field(None, alias="refundedAmount")
    date: str | None = None  # Timestamp string
    reference_number: str | None = Field(None, alias="referenceNumber")
    daily_transaction_id: str | None = Field(None, alias="dailyTransactionID")
    name: str | None = None
    phone_number: str | None = Field(None, alias="phoneNumber")
    email: str | None = None

    @field_validator("daily_transaction_id", mode="before")
    @classmethod
    def convert_daily_transaction_id(cls, v: str | int | None) -> str | None:
        """Convert daily transaction ID to string format."""
        if v is None:
            return v
        return str(v)


class OriginalTransaction(BaseModel):
    """Original transaction details in refund response."""

    model_config = ConfigDict(populate_by_name=True)

    transaction_type: str | None = Field(None, alias="transactionType")
    status: str | None = None
    date: str | None = None  # Timestamp string
    reference_number: str | None = Field(None, alias="referenceNumber")
    daily_transaction_id: str | None = Field(None, alias="dailyTransactionID")
    name: str | None = None
    phone_number: str | None = Field(None, alias="phoneNumber")
    email: str | None = None
    message: str | None = None
    total: Decimal | None = None
    tax: Decimal | None = None
    subtotal: Decimal | None = None
    fee: Decimal | None = None
    net_amount: Decimal | None = Field(None, alias="netAmount")
    total_refunded_amount: Decimal | None = Field(None, alias="totalRefundedAmount")
    metadata1: str | None = None
    metadata2: str | None = None
    items: list[PaymentItem] | None = None

    @field_validator("daily_transaction_id", mode="before")
    @classmethod
    def convert_daily_transaction_id(cls, v: str | int | None) -> str | None:
        """Convert daily transaction ID to string format."""
        if v is None:
            return v
        return str(v)


class RefundData(BaseModel):
    """Data returned from refund request."""

    model_config = ConfigDict(populate_by_name=True)

    refund: RefundTransaction
    original_transaction: OriginalTransaction = Field(..., alias="originalTransaction")


class RefundResponse(BaseModel):
    """Response from refund request."""

    status: str
    data: RefundData


class APIError(BaseModel):
    """API error response."""

    status: str
    message: str
    errorcode: str | None = None
    data: Any | None = None


class SuccessResponse(BaseModel):
    """Generic success response."""

    status: str
    data: dict[str, Any] | str | None = None

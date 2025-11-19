"""Internal utility functions for ATH Móvil library."""

import re
from decimal import Decimal
from typing import Any


def format_amount(amount: Any) -> str:
    """Format amount to proper decimal string.

    Args:
        amount: Amount value (string, int, float, or Decimal)

    Returns:
        Formatted amount string with 2 decimal places

    Raises:
        ValueError: If amount is invalid
    """
    try:
        decimal_amount = Decimal(str(amount))
        if decimal_amount < 0:
            raise ValueError("Amount cannot be negative")
        return str(decimal_amount.quantize(Decimal("0.01")))
    except Exception as e:
        raise ValueError(f"Invalid amount format: {e}") from e


def validate_phone_number(phone: str) -> str:
    """Validate and format phone number.

    Args:
        phone: Phone number string

    Returns:
        Validated phone number

    Raises:
        ValueError: If phone number is invalid
    """
    digits = "".join(filter(str.isdigit, phone))

    if len(digits) != 10:
        raise ValueError(f"Phone number must be 10 digits, got {len(digits)}")

    return digits


def truncate_string(text: str | None, max_length: int) -> str | None:
    """Truncate string to maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum allowed length

    Returns:
        Truncated string or None
    """
    if text is None:
        return None
    if len(text) <= max_length:
        return text

    return text[:max_length]


def mask_sensitive_data(data: str, visible_chars: int = 4) -> str:
    """Mask sensitive data for logging.

    Args:
        data: Sensitive data string
        visible_chars: Number of characters to keep visible

    Returns:
        Masked string
    """
    if not data or len(data) <= visible_chars:
        return "***"

    return data[:visible_chars] + "*" * (len(data) - visible_chars)


def is_valid_ecommerce_id(ecommerce_id: str) -> bool:
    """Check if ecommerce ID format is valid.

    Args:
        ecommerce_id: Ecommerce ID to validate

    Returns:
        True if valid UUID format
    """
    uuid_pattern = re.compile(
        r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
    )
    return bool(uuid_pattern.match(ecommerce_id))


def calculate_fee(amount: Decimal, fee_percentage: Decimal = Decimal("2.5")) -> Decimal:
    """Calculate transaction fee.

    Args:
        amount: Transaction amount
        fee_percentage: Fee percentage (default 2.5%)

    Returns:
        Calculated fee amount
    """
    fee = (amount * fee_percentage / 100).quantize(Decimal("0.01"))
    return fee


def calculate_net_amount(total: Decimal, fee: Decimal | None = None) -> Decimal:
    """Calculate net amount after fee.

    Args:
        total: Total transaction amount
        fee: Transaction fee (if None, calculated as 2.5%)

    Returns:
        Net amount after fee
    """
    if fee is None:
        fee = calculate_fee(total)
    return total - fee

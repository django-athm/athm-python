"""Unit tests for utility functions."""

from decimal import Decimal

import pytest

from athm._utils import (
    calculate_fee,
    calculate_net_amount,
    format_amount,
    is_valid_ecommerce_id,
    mask_sensitive_data,
    truncate_string,
    validate_phone_number,
)


class TestFormatAmount:
    def test_format_string_amount(self):
        assert format_amount("100") == "100.00"
        assert format_amount("100.5") == "100.50"
        assert format_amount("100.999") == "101.00"
        assert format_amount("0.01") == "0.01"

    def test_format_numeric_amount(self):
        assert format_amount(100) == "100.00"
        assert format_amount(100.5) == "100.50"
        assert format_amount(Decimal("100.123")) == "100.12"

    def test_format_negative_amount(self):
        with pytest.raises(ValueError, match="cannot be negative"):
            format_amount("-10.00")

        with pytest.raises(ValueError, match="cannot be negative"):
            format_amount(-10)

    def test_format_invalid_amount(self):
        with pytest.raises(ValueError, match="Invalid amount format"):
            format_amount("abc")

        with pytest.raises(ValueError, match="Invalid amount format"):
            format_amount(None)


class TestValidatePhoneNumber:
    def test_valid_phone_numbers(self):
        assert validate_phone_number("7875551234") == "7875551234"
        assert validate_phone_number("1234567890") == "1234567890"

    def test_phone_with_formatting(self):
        assert validate_phone_number("787-555-1234") == "7875551234"
        assert validate_phone_number("(787) 555-1234") == "7875551234"
        assert validate_phone_number("787.555.1234") == "7875551234"
        # Test that 11 digit phone numbers fail
        with pytest.raises(ValueError, match="must be 10 digits"):
            validate_phone_number("+1 787 555 1234")  # 11 digits

    def test_invalid_phone_length(self):
        with pytest.raises(ValueError, match="must be 10 digits"):
            validate_phone_number("123")

        with pytest.raises(ValueError, match="must be 10 digits"):
            validate_phone_number("12345678901")

        with pytest.raises(ValueError, match="must be 10 digits"):
            validate_phone_number("abc")


class TestTruncateString:
    def test_truncate_short_string(self):
        assert truncate_string("Hello", 10) == "Hello"
        assert truncate_string("Test", 4) == "Test"

    def test_truncate_long_string(self):
        assert truncate_string("Hello World", 5) == "Hello"
        assert truncate_string("ABCDEFGHIJK", 5) == "ABCDE"

    def test_truncate_none(self):
        assert truncate_string(None, 10) is None

    def test_truncate_exact_length(self):
        assert truncate_string("12345", 5) == "12345"


class TestMaskSensitiveData:
    def test_mask_normal_string(self):
        assert mask_sensitive_data("1234567890") == "1234******"
        assert mask_sensitive_data("secret_token_123") == "secr************"

    def test_mask_short_string(self):
        assert mask_sensitive_data("123") == "***"
        assert mask_sensitive_data("ab") == "***"

    def test_mask_empty_string(self):
        assert mask_sensitive_data("") == "***"
        assert mask_sensitive_data(None) == "***"

    def test_mask_custom_visible_chars(self):
        assert mask_sensitive_data("1234567890", visible_chars=6) == "123456****"
        assert mask_sensitive_data("token", visible_chars=2) == "to***"


class TestIsValidEcommerceId:
    def test_valid_uuid(self):
        assert is_valid_ecommerce_id("550e8400-e29b-41d4-a716-446655440000")
        assert is_valid_ecommerce_id("123e4567-e89b-12d3-a456-426614174000")
        assert is_valid_ecommerce_id("00000000-0000-0000-0000-000000000000")

    def test_invalid_uuid(self):
        assert not is_valid_ecommerce_id("not-a-uuid")
        assert not is_valid_ecommerce_id("550e8400-e29b-41d4-a716")  # Too short
        assert not is_valid_ecommerce_id("550e8400e29b41d4a716446655440000")  # No dashes
        assert not is_valid_ecommerce_id("")

    def test_uuid_case_insensitive(self):
        assert is_valid_ecommerce_id("550E8400-E29B-41D4-A716-446655440000")
        assert is_valid_ecommerce_id("550e8400-E29B-41d4-A716-446655440000")


class TestCalculateFee:
    def test_default_fee_percentage(self):
        assert calculate_fee(Decimal("100.00")) == Decimal("2.50")
        assert calculate_fee(Decimal("1000.00")) == Decimal("25.00")
        assert calculate_fee(Decimal("50.00")) == Decimal("1.25")

    def test_custom_fee_percentage(self):
        assert calculate_fee(Decimal("100.00"), Decimal("3.0")) == Decimal("3.00")
        assert calculate_fee(Decimal("100.00"), Decimal("1.5")) == Decimal("1.50")
        assert calculate_fee(Decimal("100.00"), Decimal("0.0")) == Decimal("0.00")

    def test_fee_rounding(self):
        assert calculate_fee(Decimal("100.00"), Decimal("2.35")) == Decimal("2.35")
        assert calculate_fee(Decimal("33.33"), Decimal("2.5")) == Decimal("0.83")
        assert calculate_fee(Decimal("10.01"), Decimal("2.5")) == Decimal("0.25")


class TestCalculateNetAmount:
    def test_net_amount_with_default_fee(self):
        assert calculate_net_amount(Decimal("100.00")) == Decimal("97.50")
        assert calculate_net_amount(Decimal("1000.00")) == Decimal("975.00")

    def test_net_amount_with_custom_fee(self):
        assert calculate_net_amount(Decimal("100.00"), Decimal("5.00")) == Decimal("95.00")
        assert calculate_net_amount(Decimal("100.00"), Decimal("0.00")) == Decimal("100.00")
        assert calculate_net_amount(Decimal("50.00"), Decimal("1.25")) == Decimal("48.75")

    def test_net_amount_consistency(self):
        total = Decimal("123.45")
        fee = calculate_fee(total)
        net = calculate_net_amount(total)

        # Net + fee should equal total
        assert net + fee == total

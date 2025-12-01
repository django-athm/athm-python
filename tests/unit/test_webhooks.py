"""Unit tests for webhook models and utilities."""

from decimal import Decimal
from typing import Any

import httpx
import pytest
from pytest_httpx import HTTPXMock

from athm.client import ATHMovilClient
from athm.constants import WEBHOOK_BASE_URL, WEBHOOK_SUBSCRIBE_ENDPOINT
from athm.exceptions import AuthenticationError, ValidationError
from athm.webhooks import (
    WebhookEventType,
    WebhookItem,
    WebhookStatus,
    WebhookSubscriptionRequest,
    parse_webhook,
)
from tests.conftest import SAMPLE_ECOMMERCE_ID


class TestParseWebhook:
    """Tests for parse_webhook() function and WebhookPayload model."""

    def test_parse_standard_payment(self, mock_webhook_payment_payload: dict[str, Any]):
        """Parse standard payment event with string decimals."""
        event = parse_webhook(mock_webhook_payment_payload)

        assert event.transaction_type == WebhookEventType.PAYMENT
        assert event.status == WebhookStatus.COMPLETED
        assert event.reference_number == "REF-2025-001234"
        assert event.daily_transaction_id == "12345"
        assert event.name == "John Doe"
        assert event.phone_number == "7875551234"
        assert event.email == "john@example.com"
        assert event.message == "Payment for order #123"
        assert event.total == Decimal("100.00")
        assert event.tax == Decimal("10.00")
        assert event.subtotal == Decimal("90.00")
        assert event.fee == Decimal("2.50")
        assert event.net_amount == Decimal("97.50")
        assert event.metadata1 == "Order #123"
        assert event.metadata2 == "Customer: John Doe"
        assert len(event.items) == 1
        assert event.items[0].name == "Product 1"
        assert event.items[0].price == Decimal("45.00")
        assert event.items[0].quantity == 2

    def test_parse_ecommerce_completed(
        self, mock_webhook_ecommerce_completed_payload: dict[str, Any]
    ):
        """Parse eCommerce completed event with numbers and different field names."""
        event = parse_webhook(mock_webhook_ecommerce_completed_payload)

        # Transaction type normalized from "ECOMMERCE" to "ecommerce"
        assert event.transaction_type == WebhookEventType.ECOMMERCE
        # Status normalized from "COMPLETED" to "completed"
        assert event.status == WebhookStatus.COMPLETED
        assert event.ecommerce_id == SAMPLE_ECOMMERCE_ID
        assert event.business_name == "Test Business"
        # Phone number converted from int to string
        assert event.phone_number == "7875551234"
        # Amounts converted from numbers to Decimal
        assert event.total == Decimal("100.00")
        assert event.tax == Decimal("10.00")
        # subTotal normalized to subtotal
        assert event.subtotal == Decimal("90.00")
        assert event.is_non_profit is False
        assert event.reference_transaction_id == "TXN123456"
        # Transaction date parsed
        assert event.transaction_date is not None

    def test_parse_ecommerce_cancelled(
        self, mock_webhook_ecommerce_cancelled_payload: dict[str, Any]
    ):
        """Parse eCommerce cancelled event with CANCEL -> cancelled normalization."""
        event = parse_webhook(mock_webhook_ecommerce_cancelled_payload)

        assert event.transaction_type == WebhookEventType.ECOMMERCE
        # CANCEL normalized to cancelled
        assert event.status == WebhookStatus.CANCELLED
        assert event.ecommerce_id == SAMPLE_ECOMMERCE_ID
        # Empty strings normalized to empty/None
        assert event.reference_number == ""
        assert event.name == ""

    def test_parse_refund(self, mock_webhook_refund_payload: dict[str, Any]):
        """Parse refund webhook event."""
        event = parse_webhook(mock_webhook_refund_payload)

        assert event.transaction_type == WebhookEventType.REFUND
        assert event.status == WebhookStatus.COMPLETED
        assert event.total == Decimal("50.00")
        assert event.total_refunded_amount == Decimal("50.00")

    def test_normalize_daily_transaction_id_uppercase(self):
        """Test dailyTransactionID (standard events) is normalized."""
        payload = {
            "transactionType": "payment",
            "status": "completed",
            "date": "2025-01-15 10:30:00",
            "total": "10.00",
            "dailyTransactionID": "99999",  # Uppercase ID
        }
        event = parse_webhook(payload)
        assert event.daily_transaction_id == "99999"

    def test_normalize_daily_transaction_id_camelcase(self):
        """Test dailyTransactionId (eCommerce events) is normalized."""
        payload = {
            "transactionType": "ECOMMERCE",
            "status": "COMPLETED",
            "date": "2025-01-15 10:30:00",
            "total": 10.00,
            "dailyTransactionId": "88888",  # camelCase
        }
        event = parse_webhook(payload)
        assert event.daily_transaction_id == "88888"

    def test_normalize_subtotal_variants(self):
        """Test subTotal vs subtotal field normalization."""
        # subTotal (eCommerce style)
        payload1 = {
            "transactionType": "ECOMMERCE",
            "status": "COMPLETED",
            "date": "2025-01-15 10:30:00",
            "total": 100.00,
            "subTotal": 90.00,
        }
        event1 = parse_webhook(payload1)
        assert event1.subtotal == Decimal("90.00")

        # subtotal (standard style)
        payload2 = {
            "transactionType": "payment",
            "status": "completed",
            "date": "2025-01-15 10:30:00",
            "total": "100.00",
            "subtotal": "90.00",
        }
        event2 = parse_webhook(payload2)
        assert event2.subtotal == Decimal("90.00")

    def test_parse_webhook_with_empty_optional_fields(self):
        """Test handling of empty/null optional fields."""
        payload = {
            "transactionType": "payment",
            "status": "completed",
            "date": "2025-01-15 10:30:00",
            "total": "10.00",
            "tax": "",  # Empty string
            "fee": None,  # Null
            "items": [],
        }
        event = parse_webhook(payload)
        assert event.tax is None
        assert event.fee is None
        assert event.items == []

    def test_parse_webhook_invalid_payload(self):
        """Test rejection of invalid payloads."""
        # Missing required field (transactionType)
        with pytest.raises(ValidationError, match="Invalid webhook payload"):
            parse_webhook({"status": "completed", "date": "2025-01-15", "total": "10"})

        # Missing required field (total)
        with pytest.raises(ValidationError, match="Invalid webhook payload"):
            parse_webhook(
                {"transactionType": "payment", "status": "completed", "date": "2025-01-15"}
            )

    def test_parse_webhook_invalid_decimal(self):
        """Test rejection of invalid decimal values."""
        payload = {
            "transactionType": "payment",
            "status": "completed",
            "date": "2025-01-15 10:30:00",
            "total": "not-a-number",
        }
        with pytest.raises(ValidationError, match="Invalid webhook payload"):
            parse_webhook(payload)

    def test_parse_webhook_item_with_null_tax(self):
        """Test item with null/empty tax field."""
        payload = {
            "transactionType": "payment",
            "status": "completed",
            "date": "2025-01-15 10:30:00",
            "total": "10.00",
            "items": [
                {
                    "name": "Product",
                    "description": "Desc",
                    "quantity": "1",
                    "price": "10.00",
                    "tax": None,
                }
            ],
        }
        event = parse_webhook(payload)
        assert event.items[0].tax is None

    def test_parse_webhook_null_date_handling(self):
        """Test null date field handling."""
        payload = {
            "transactionType": "ECOMMERCE",
            "status": "COMPLETED",
            "date": "2025-01-15 10:30:00",
            "total": 100.00,
            "transactionDate": "",  # Empty transaction date
        }
        event = parse_webhook(payload)
        assert event.transaction_date is None

    def test_parse_webhook_datetime_object(self):
        """Test passing datetime object directly."""
        from datetime import datetime

        now = datetime(2025, 1, 15, 10, 30, 0)
        payload = {
            "transactionType": "payment",
            "status": "completed",
            "date": now,  # Datetime object instead of string
            "total": "10.00",
        }
        event = parse_webhook(payload)
        assert event.date == now

    def test_parse_webhook_null_phone(self):
        """Test null phone number handling."""
        payload = {
            "transactionType": "payment",
            "status": "completed",
            "date": "2025-01-15 10:30:00",
            "total": "10.00",
            "phoneNumber": None,
        }
        event = parse_webhook(payload)
        assert event.phone_number is None

    def test_webhook_item_invalid_decimal(self):
        """Test WebhookItem with invalid decimal value."""
        with pytest.raises(ValueError, match="Invalid decimal"):
            WebhookItem(
                name="Product",
                description="Desc",
                quantity=1,
                price="not-a-number",
            )


class TestWebhookSubscriptionRequest:
    def test_https_required(self):
        """Test that HTTP URLs are rejected."""
        with pytest.raises(ValueError, match="must use HTTPS"):
            WebhookSubscriptionRequest(
                public_token="test",
                private_token="test",
                listener_url="http://example.com/webhook",
            )

    def test_serialization_with_aliases(self):
        """Test that model serializes with correct API field names."""
        request = WebhookSubscriptionRequest(
            public_token="test_public",
            private_token="test_private",
            listener_url="https://example.com/webhook",
            payment_received_event=True,
            donation_received_event=False,
        )
        data = request.model_dump(by_alias=True)

        assert data["publicToken"] == "test_public"
        assert data["privateToken"] == "test_private"
        assert data["listenerURL"] == "https://example.com/webhook"
        assert data["paymentReceivedEvent"] is True
        assert data["donationReceivedEvent"] is False


class TestSubscribeWebhook:
    """Tests for client.subscribe_webhook() method."""

    def test_subscribe_webhook_success(
        self,
        client: ATHMovilClient,
        httpx_mock: HTTPXMock,
        mock_webhook_subscription_response: dict[str, Any],
    ):
        httpx_mock.add_response(
            method="POST",
            url=f"{WEBHOOK_BASE_URL}{WEBHOOK_SUBSCRIBE_ENDPOINT}",
            json=mock_webhook_subscription_response,
            status_code=200,
        )

        response = client.subscribe_webhook(
            listener_url="https://example.com/webhook",
            payment_received=True,
            refund_sent=True,
        )

        assert response["status"] == "success"

        # Verify request was sent correctly
        request = httpx_mock.get_request()
        assert request is not None
        import json

        body = json.loads(request.content)
        assert body["publicToken"] == client.public_token
        assert body["privateToken"] == client.private_token
        assert body["listenerURL"] == "https://example.com/webhook"
        assert body["paymentReceivedEvent"] is True
        assert body["refundSentEvent"] is True

    def test_subscribe_webhook_selective_events(
        self,
        client: ATHMovilClient,
        httpx_mock: HTTPXMock,
        mock_webhook_subscription_response: dict[str, Any],
    ):
        """Test subscribing to only specific events."""
        httpx_mock.add_response(
            method="POST",
            url=f"{WEBHOOK_BASE_URL}{WEBHOOK_SUBSCRIBE_ENDPOINT}",
            json=mock_webhook_subscription_response,
            status_code=200,
        )

        client.subscribe_webhook(
            listener_url="https://example.com/webhook",
            payment_received=True,
            refund_sent=False,
            donation_received=False,
            ecommerce_completed=True,
            ecommerce_cancelled=False,
            ecommerce_expired=False,
        )

        request = httpx_mock.get_request()
        import json

        body = json.loads(request.content)
        assert body["paymentReceivedEvent"] is True
        assert body["refundSentEvent"] is False
        assert body["donationReceivedEvent"] is False
        assert body["ecommercePaymentReceivedEvent"] is True
        assert body["ecommercePaymentCancelledEvent"] is False
        assert body["ecommercePaymentExpiredEvent"] is False

    def test_subscribe_webhook_without_private_token(self, public_token: str):
        """Test that subscription fails without private_token."""
        client = ATHMovilClient(public_token=public_token)

        with pytest.raises(AuthenticationError, match="private_token is required"):
            client.subscribe_webhook(listener_url="https://example.com/webhook")

        client.close()

    def test_subscribe_webhook_invalid_url(self, client: ATHMovilClient):
        """Test that HTTP URLs are rejected."""
        with pytest.raises(ValidationError):
            client.subscribe_webhook(listener_url="http://example.com/webhook")

    def test_subscribe_webhook_timeout(
        self,
        client: ATHMovilClient,
        httpx_mock: HTTPXMock,
    ):
        """Test timeout handling during subscription."""

        def raise_timeout(request: httpx.Request) -> httpx.Response:
            raise httpx.TimeoutException("Connection timed out")

        httpx_mock.add_callback(raise_timeout)

        from athm.exceptions import TimeoutError

        with pytest.raises(TimeoutError, match="timed out"):
            client.subscribe_webhook(listener_url="https://example.com/webhook")

    def test_subscribe_webhook_api_error(
        self,
        client: ATHMovilClient,
        httpx_mock: HTTPXMock,
        mock_auth_error_response: dict[str, Any],
    ):
        """Test API error handling during subscription."""
        httpx_mock.add_response(
            method="POST",
            url=f"{WEBHOOK_BASE_URL}{WEBHOOK_SUBSCRIBE_ENDPOINT}",
            json=mock_auth_error_response,
            status_code=401,
        )

        with pytest.raises(AuthenticationError):
            client.subscribe_webhook(listener_url="https://example.com/webhook")

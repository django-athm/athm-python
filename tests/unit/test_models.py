"""Unit tests for Pydantic models."""

from datetime import datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from athm.models import (
    APIError,
    Environment,
    PaymentItem,
    PaymentRequest,
    PaymentResponse,
    RefundRequest,
    RefundResponse,
    TransactionData,
    TransactionResponse,
    TransactionStatus,
)


class TestPaymentItem:
    def test_valid_payment_item(self):
        item = PaymentItem(
            name="Test Product",
            description="A test product",
            quantity="5",
            price="10.00",
            tax="1.00",
            metadata="SKU123",
        )
        assert item.name == "Test Product"
        assert item.quantity == "5"
        assert item.price == "10.00"
        assert item.tax == "1.00"

    def test_payment_item_amount_formatting(self):
        item = PaymentItem(
            name="Test",
            description="Test",
            quantity="1",
            price="10.999",
            tax="1.111",
        )
        assert item.price == "11.00"
        assert item.tax == "1.11"

    def test_payment_item_negative_amount(self):
        with pytest.raises(ValidationError):
            PaymentItem(
                name="Test",
                description="Test",
                quantity="1",
                price="-10.00",
            )

    def test_payment_item_invalid_quantity(self):
        with pytest.raises(ValidationError):
            PaymentItem(
                name="Test",
                description="Test",
                quantity="0",  # Must be positive
                price="10.00",
            )

        with pytest.raises(ValidationError):
            PaymentItem(
                name="Test",
                description="Test",
                quantity="abc",  # Must be numeric
                price="10.00",
            )

    def test_payment_item_alias_support(self):
        item = PaymentItem(
            name="Test",
            description="Test",
            quantity="1",
            price="10.00",
            formattedPrice="$10.00",  # Using alias
        )
        assert item.formatted_price == "$10.00"

    def test_payment_item_field_length_validation(self):
        # Name and description max 255 chars
        item = PaymentItem(
            name="A" * 255,
            description="B" * 255,
            quantity="1",
            price="10.00",
            metadata="C" * 255,
        )
        assert len(item.name) == 255

        # Should fail with longer values
        with pytest.raises(ValidationError):
            PaymentItem(
                name="A" * 256,  # Too long
                description="Test",
                quantity="1",
                price="10.00",
            )


class TestPaymentRequest:
    def test_valid_payment_request(self):
        request = PaymentRequest(
            publicToken="test_token",
            total="100.00",
            phoneNumber="7875551234",
            tax="10.00",
            subtotal="90.00",
            metadata1="Order #123",
            metadata2="Customer: John",
            items=[
                PaymentItem(
                    name="Test", description="Test", quantity="1", price="90.00", tax="10.00"
                )
            ],
        )
        assert request.public_token == "test_token"
        assert request.total == "100.00"
        assert request.phone_number == "7875551234"
        assert request.env == Environment.PRODUCTION

    def test_payment_request_defaults(self):
        request = PaymentRequest(
            publicToken="test_token",
            total="100.00",
            phoneNumber="7875551234",
            items=[PaymentItem(name="Test", description="Test", quantity="1", price="100.00")],
        )
        assert request.timeout == "600"
        assert request.env == Environment.PRODUCTION
        assert request.tax is None
        assert request.subtotal is None

    def test_payment_request_items_required(self):
        # Items is required - should raise ValidationError without it
        with pytest.raises(ValidationError, match="Field required"):
            PaymentRequest(
                publicToken="test_token",
                total="100.00",
                phoneNumber="7875551234",
            )

    def test_payment_amount_validation(self):
        # Below minimum
        with pytest.raises(ValidationError, match="at least"):
            PaymentRequest(
                publicToken="test",
                total="0.99",
                phoneNumber="7875551234",
                items=[PaymentItem(name="Test", description="Test", quantity="1", price="0.99")],
            )

        # Above maximum
        with pytest.raises(ValidationError, match="exceed"):
            PaymentRequest(
                publicToken="test",
                total="1500.01",
                phoneNumber="7875551234",
                items=[PaymentItem(name="Test", description="Test", quantity="1", price="1500.01")],
            )

        # Valid boundary values
        request_min = PaymentRequest(
            publicToken="test",
            total="1.00",
            phoneNumber="7875551234",
            items=[PaymentItem(name="Test", description="Test", quantity="1", price="1.00")],
        )
        assert request_min.total == "1.00"

        request_max = PaymentRequest(
            publicToken="test",
            total="1500.00",
            phoneNumber="7875551234",
            items=[PaymentItem(name="Test", description="Test", quantity="1", price="1500.00")],
        )
        assert request_max.total == "1500.00"

    def test_payment_tax_subtotal_validation(self):
        # Tax and subtotal should allow values less than $1.00 (unlike total)
        request = PaymentRequest(
            publicToken="test",
            total="5.00",
            subtotal="4.50",
            tax="0.50",
            phoneNumber="7875551234",
            items=[
                PaymentItem(name="Test", description="Test", quantity="1", price="4.50", tax="0.50")
            ],
        )
        assert request.total == "5.00"
        assert request.subtotal == "4.50"
        assert request.tax == "0.50"

        # Tax can be zero
        request_zero_tax = PaymentRequest(
            publicToken="test",
            total="10.00",
            subtotal="10.00",
            tax="0.00",
            phoneNumber="7875551234",
            items=[PaymentItem(name="Test", description="Test", quantity="1", price="10.00")],
        )
        assert request_zero_tax.tax == "0.00"

        # Subtotal can be less than $1
        request_small_subtotal = PaymentRequest(
            publicToken="test",
            total="1.25",
            subtotal="0.75",
            tax="0.50",
            phoneNumber="7875551234",
            items=[
                PaymentItem(name="Test", description="Test", quantity="1", price="0.75", tax="0.50")
            ],
        )
        assert request_small_subtotal.subtotal == "0.75"

        # But negative values should fail
        with pytest.raises(ValidationError, match="negative"):
            PaymentRequest(
                publicToken="test",
                total="5.00",
                tax="-0.50",
                phoneNumber="7875551234",
                items=[PaymentItem(name="Test", description="Test", quantity="1", price="5.00")],
            )

    def test_payment_timeout_validation(self):
        # Valid timeout
        request = PaymentRequest(
            publicToken="test",
            total="10.00",
            phoneNumber="7875551234",
            timeout="300",
            items=[PaymentItem(name="Test", description="Test", quantity="1", price="10.00")],
        )
        assert request.timeout == "300"

        # Below minimum (120 seconds)
        with pytest.raises(ValidationError, match="at least 120"):
            PaymentRequest(
                publicToken="test",
                total="10.00",
                phoneNumber="7875551234",
                timeout="119",
                items=[PaymentItem(name="Test", description="Test", quantity="1", price="10.00")],
            )

        # High timeout values are allowed (API accepts > 600)
        request_high = PaymentRequest(
            publicToken="test",
            total="10.00",
            phoneNumber="7875551234",
            timeout="5000",  # Real API accepts this
            items=[PaymentItem(name="Test", description="Test", quantity="1", price="10.00")],
        )
        assert request_high.timeout == "5000"

    def test_phone_number_validation(self):
        # Valid phone number
        request = PaymentRequest(
            publicToken="test",
            total="10.00",
            phoneNumber="7875551234",
            items=[PaymentItem(name="Test", description="Test", quantity="1", price="10.00")],
        )
        assert request.phone_number == "7875551234"

        # Invalid phone numbers
        invalid_phones = [
            "123",  # Too short
            "12345678901",  # Too long
            "787-555-1234",  # Has dashes
            "abcdefghij",  # Non-numeric
        ]

        for phone in invalid_phones:
            with pytest.raises(ValidationError):
                PaymentRequest(
                    publicToken="test",
                    total="10.00",
                    phoneNumber=phone,
                    items=[
                        PaymentItem(name="Test", description="Test", quantity="1", price="10.00")
                    ],
                )

    def test_metadata_length_validation(self):
        # Valid metadata (40 chars)
        request = PaymentRequest(
            publicToken="test",
            total="10.00",
            phoneNumber="7875551234",
            metadata1="A" * 40,
            metadata2="B" * 40,
            items=[PaymentItem(name="Test", description="Test", quantity="1", price="10.00")],
        )
        assert len(request.metadata1) == 40

        # Too long metadata
        with pytest.raises(ValidationError):
            PaymentRequest(
                publicToken="test",
                total="10.00",
                phoneNumber="7875551234",
                metadata1="A" * 41,
                items=[PaymentItem(name="Test", description="Test", quantity="1", price="10.00")],
            )

    def test_payment_totals_validation(self):
        # Valid totals
        request = PaymentRequest(
            publicToken="test",
            total="100.00",
            subtotal="90.00",
            tax="10.00",
            phoneNumber="7875551234",
            items=[
                PaymentItem(
                    name="Test", description="Test", quantity="1", price="90.00", tax="10.00"
                )
            ],
        )
        assert request.total == "100.00"

        # Mismatched totals
        with pytest.raises(ValidationError, match=r"Total.*must equal"):
            PaymentRequest(
                publicToken="test",
                total="100.00",
                subtotal="80.00",
                tax="10.00",  # 80 + 10 != 100
                phoneNumber="7875551234",
                items=[
                    PaymentItem(
                        name="Test", description="Test", quantity="1", price="80.00", tax="10.00"
                    )
                ],
            )

    def test_payment_with_items(self):
        items = [
            PaymentItem(
                name="Product 1",
                description="Test",
                quantity="2",
                price="45.00",
            ),
            PaymentItem(
                name="Product 2",
                description="Test",
                quantity="1",
                price="10.00",
            ),
        ]

        request = PaymentRequest(
            publicToken="test",
            total="100.00",
            phoneNumber="7875551234",
            items=items,
        )
        assert len(request.items) == 2
        assert request.items[0].name == "Product 1"


class TestTransactionModels:
    def test_transaction_status_enum(self):
        assert TransactionStatus.OPEN.value == "OPEN"
        assert TransactionStatus.CONFIRM.value == "CONFIRM"
        assert TransactionStatus.COMPLETED.value == "COMPLETED"
        assert TransactionStatus.CANCEL.value == "CANCEL"

    def test_transaction_data(self):
        data = TransactionData(
            ecommerceStatus=TransactionStatus.CONFIRM,
            ecommerceId="uuid-123",
            referenceNumber="REF123",
            businessCustomerId="BUS456",
            transactionDate=datetime.now(),
            total=Decimal("100.00"),
            tax=Decimal("10.00"),
            subTotal=Decimal("90.00"),
            fee=Decimal("2.50"),
            netAmount=Decimal("97.50"),
            totalRefundedAmount=Decimal("0.00"),
        )

        assert data.ecommerce_status == TransactionStatus.CONFIRM
        assert data.ecommerce_id == "uuid-123"
        assert data.reference_number == "REF123"
        assert data.total == Decimal("100.00")

    def test_transaction_response(self):
        response = TransactionResponse(
            status="success",
            data={
                "ecommerceStatus": "COMPLETED",
                "ecommerceId": "uuid-123",
                "referenceNumber": "REF123",
                "total": 100.00,
            },
        )

        assert response.status == "success"
        assert response.data
        assert response.data.ecommerce_status == TransactionStatus.COMPLETED
        assert response.data.total == Decimal("100.00")

    def test_transaction_response_with_none_data(self):
        response = TransactionResponse(status="error", data=None)
        assert response.status == "error"
        assert response.data is None


class TestRefundModels:
    def test_refund_request(self):
        request = RefundRequest(
            publicToken="pub_token",
            privateToken="priv_token",
            referenceNumber="REF123",
            amount="50.00",
            message="Product return",
        )

        assert request.public_token == "pub_token"
        assert request.private_token == "priv_token"
        assert request.amount == "50.00"
        assert request.message == "Product return"

    def test_refund_amount_validation(self):
        # Negative amount
        with pytest.raises(ValidationError, match="positive"):
            RefundRequest(
                publicToken="pub",
                privateToken="priv",
                referenceNumber="REF",
                amount="-10.00",
            )

        # Zero amount
        with pytest.raises(ValidationError):
            RefundRequest(
                publicToken="pub",
                privateToken="priv",
                referenceNumber="REF",
                amount="0.00",
            )

    def test_refund_message_length(self):
        # Valid message (50 chars)
        request = RefundRequest(
            publicToken="pub",
            privateToken="priv",
            referenceNumber="REF",
            amount="10.00",
            message="A" * 50,
        )
        assert len(request.message) == 50

        # Too long message
        with pytest.raises(ValidationError):
            RefundRequest(
                publicToken="pub",
                privateToken="priv",
                referenceNumber="REF",
                amount="10.00",
                message="A" * 51,
            )

    def test_refund_response(self):
        response_data = {
            "status": "success",
            "data": {
                "refund": {
                    "transactionType": "REFUND",
                    "status": "COMPLETED",
                    "refundedAmount": 50.00,
                    "date": str(int(datetime.now().timestamp())),
                    "referenceNumber": "REFUND123",
                    "dailyTransactionID": "0107",
                    "name": "John Doe",
                    "phoneNumber": "(787) 555-1234",
                    "email": "john@example.com",
                },
                "originalTransaction": {
                    "transactionType": "PAYMENT",
                    "status": "COMPLETED",
                    "date": str(int(datetime.now().timestamp())),
                    "referenceNumber": "REF123",
                    "dailyTransactionID": "0106",
                    "name": "John Doe",
                    "phoneNumber": "(787) 555-1234",
                    "email": "john@example.com",
                    "message": "",
                    "total": 100.00,
                    "tax": 10.00,
                    "subtotal": 90.00,
                    "fee": 2.50,
                    "netAmount": 97.50,
                    "totalRefundedAmount": 50.00,
                    "metadata1": "Test",
                    "metadata2": "Test",
                    "items": [],
                },
            },
        }

        response = RefundResponse(**response_data)
        assert response.status == "success"
        assert response.data.refund.refunded_amount == Decimal("50.00")
        assert response.data.original_transaction.total == Decimal("100.00")


class TestAPIError:
    def test_api_error_full(self):
        error = APIError(
            status="error",
            message="Something went wrong",
            errorcode="BTRA_0001",
            data={"field": "value"},
        )

        assert error.status == "error"
        assert error.message == "Something went wrong"
        assert error.errorcode == "BTRA_0001"
        assert error.data == {"field": "value"}

    def test_api_error_minimal(self):
        error = APIError(
            status="error",
            message="Error occurred",
        )

        assert error.status == "error"
        assert error.message == "Error occurred"
        assert error.errorcode is None
        assert error.data is None


class TestModelAliases:
    def test_payment_response_aliases(self):
        response = PaymentResponse(
            status="success",
            data={
                "ecommerceId": "uuid-123",  # Using alias
                "auth_token": "token123",
            },
        )

        assert response.data.ecommerce_id == "uuid-123"
        # Check serialization uses aliases
        json_data = response.model_dump(by_alias=True)
        assert json_data["data"]["ecommerceId"] == "uuid-123"

    def test_transaction_data_aliases(self):
        data = TransactionData(
            ecommerceStatus="OPEN",  # Using alias
            ecommerceId="uuid-123",  # Using alias
            businessCustomerId="BUS456",  # Using alias
            transactionDate=datetime.now(),
        )

        assert data.ecommerce_status == TransactionStatus.OPEN
        assert data.ecommerce_id == "uuid-123"
        assert data.business_customer_id == "BUS456"


class TestEdgeCases:
    def test_payment_item_invalid_amount_format(self):
        with pytest.raises(ValidationError):
            PaymentItem(
                name="Test",
                description="Test",
                quantity="1",
                price="invalid",
            )

    def test_payment_request_none_amount(self):
        request = PaymentRequest(
            publicToken="test",
            total="100.00",
            phoneNumber="7875551234",
            subtotal=None,
            tax=None,
            items=[PaymentItem(name="Test", description="Test", quantity="1", price="100.00")],
        )
        assert request.subtotal is None
        assert request.tax is None

    def test_payment_request_invalid_amount_reraise(self):
        with pytest.raises(ValidationError):
            PaymentRequest(
                publicToken="test",
                total="0.50",
                phoneNumber="7875551234",
                items=[PaymentItem(name="Test", description="Test", quantity="1", price="0.50")],
            )

    def test_payment_request_invalid_amount_format(self):
        with pytest.raises(ValidationError):
            PaymentRequest(
                publicToken="test",
                total="not_a_number",
                phoneNumber="7875551234",
                items=[PaymentItem(name="Test", description="Test", quantity="1", price="10.00")],
            )

    def test_payment_request_invalid_timeout_format(self):
        with pytest.raises(ValidationError):
            PaymentRequest(
                publicToken="test",
                total="100.00",
                phoneNumber="7875551234",
                timeout="not_a_number",
                items=[PaymentItem(name="Test", description="Test", quantity="1", price="100.00")],
            )

    def test_payment_item_numeric_types(self):
        # API returns quantity as int, price/tax as float
        item = PaymentItem(
            name="Test",
            description="Test",
            quantity=1,  # int
            price=10.0,  # float
            tax=0.5,  # float
        )
        # Should be converted to strings
        assert item.quantity == "1"
        assert item.price == "10.00"
        assert item.tax == "0.50"

    def test_transaction_data_daily_transaction_id_as_int(self):
        from athm.models import TransactionData

        data = TransactionData(
            ecommerceStatus="COMPLETED",
            ecommerceId="uuid-123",
            dailyTransactionId=12345,  # API returns this as int
        )
        # Should be converted to string
        assert data.daily_transaction_id == "12345"

    def test_refund_daily_transaction_id_as_int(self):
        from athm.models import RefundResponse

        response_data = {
            "status": "success",
            "data": {
                "refund": {
                    "dailyTransactionID": 2,  # API returns this as int
                    "refundedAmount": 50.00,
                },
                "originalTransaction": {
                    "dailyTransactionID": 1,  # API returns this as int
                    "total": 100.00,
                },
            },
        }

        response = RefundResponse(**response_data)
        assert response.data.refund.daily_transaction_id == "2"
        assert response.data.original_transaction.daily_transaction_id == "1"

    def test_success_response_with_string_data(self):
        from athm.models import SuccessResponse

        # Cancel endpoint returns data as string
        response = SuccessResponse(
            status="success",
            data="Payment Canceled",
        )
        assert response.data == "Payment Canceled"

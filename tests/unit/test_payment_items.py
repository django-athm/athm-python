"""Unit tests for PaymentItem validation and items field in PaymentRequest."""

import pytest
from pydantic import ValidationError as PydanticValidationError

from athm.client import ATHMovilClient
from athm.exceptions import ValidationError
from athm.models import PaymentItem, PaymentRequest


class TestPaymentItemValidation:
    """Test PaymentItem field validation."""

    def test_valid_payment_item(self):
        """Test creating a valid payment item."""
        item = PaymentItem(
            name="Product",
            description="Description",
            quantity="1",
            price="10.00",
        )
        assert item.name == "Product"
        assert item.description == "Description"
        assert item.quantity == "1"
        assert item.price == "10.00"

    def test_payment_item_with_tax(self):
        """Test payment item with tax field."""
        item = PaymentItem(
            name="Product",
            description="Description",
            quantity="2",
            price="10.00",
            tax="1.50",
        )
        assert item.tax == "1.50"

    def test_payment_item_with_metadata(self):
        """Test payment item with optional metadata."""
        item = PaymentItem(
            name="Product",
            description="Description",
            quantity="1",
            price="10.00",
            metadata="Extra info",
            sku="SKU123",
        )
        assert item.metadata == "Extra info"
        assert item.sku == "SKU123"

    def test_payment_item_price_formatting(self):
        """Test that price is formatted to 2 decimal places."""
        item = PaymentItem(
            name="Product",
            description="Description",
            quantity="1",
            price="10.5",  # One decimal
        )
        assert item.price == "10.50"

        item2 = PaymentItem(
            name="Product",
            description="Description",
            quantity="1",
            price="10.999",  # Three decimals
        )
        assert item2.price == "11.00"  # Rounded

    def test_payment_item_negative_price(self):
        """Test that negative prices are rejected."""
        with pytest.raises(PydanticValidationError, match="Amount cannot be negative"):
            PaymentItem(
                name="Product",
                description="Description",
                quantity="1",
                price="-10.00",
            )

    def test_payment_item_invalid_quantity(self):
        """Test validation of quantity field."""
        # Zero quantity
        with pytest.raises(PydanticValidationError, match="Quantity must be positive"):
            PaymentItem(
                name="Product",
                description="Description",
                quantity="0",
                price="10.00",
            )

        # Negative quantity
        with pytest.raises(PydanticValidationError, match="Quantity must be positive"):
            PaymentItem(
                name="Product",
                description="Description",
                quantity="-1",
                price="10.00",
            )

        # Non-numeric quantity
        with pytest.raises(PydanticValidationError, match="invalid literal"):
            PaymentItem(
                name="Product",
                description="Description",
                quantity="abc",
                price="10.00",
            )

    def test_payment_item_quantity_conversion(self):
        """Test that quantity is converted to string."""
        item = PaymentItem(
            name="Product",
            description="Description",
            quantity=5,  # Pass as int
            price="10.00",
        )
        assert item.quantity == "5"
        assert isinstance(item.quantity, str)

    def test_payment_item_field_length(self):
        """Test field length validation."""
        # Name too long (max 255)
        with pytest.raises(PydanticValidationError, match="String should have at most 255"):
            PaymentItem(
                name="x" * 256,
                description="Description",
                quantity="1",
                price="10.00",
            )

        # Description too long (max 255)
        with pytest.raises(PydanticValidationError, match="String should have at most 255"):
            PaymentItem(
                name="Product",
                description="x" * 256,
                quantity="1",
                price="10.00",
            )

        # Metadata too long (max 255)
        with pytest.raises(PydanticValidationError, match="String should have at most 255"):
            PaymentItem(
                name="Product",
                description="Description",
                quantity="1",
                price="10.00",
                metadata="x" * 256,
            )

        # SKU too long (max 100)
        with pytest.raises(PydanticValidationError, match="String should have at most 100"):
            PaymentItem(
                name="Product",
                description="Description",
                quantity="1",
                price="10.00",
                sku="x" * 101,
            )


class TestPaymentRequestWithItems:
    """Test PaymentRequest with items field."""

    def test_payment_request_with_valid_items(self, public_token: str):
        """Test creating a payment request with valid items."""
        items = [
            PaymentItem(
                name="Product 1",
                description="Description 1",
                quantity="2",
                price="25.00",
                tax="2.50",
            ),
            PaymentItem(
                name="Product 2",
                description="Description 2",
                quantity="1",
                price="50.00",
                tax="5.00",
            ),
        ]

        request = PaymentRequest(
            public_token=public_token,
            total="107.50",
            tax="7.50",
            subtotal="100.00",
            phone_number="7875551234",
            metadata1="Test",
            metadata2="Test",
            items=items,
        )

        assert len(request.items) == 2
        assert request.items[0].name == "Product 1"
        assert request.items[1].name == "Product 2"

    def test_payment_request_empty_items(self, public_token: str):
        """Test that empty items list is accepted."""
        request = PaymentRequest(
            public_token=public_token,
            total="10.00",
            phone_number="7875551234",
            metadata1="Test",
            metadata2="Test",
            items=[],
        )
        assert request.items == []

    def test_payment_request_missing_items(self, public_token: str):
        """Test that items field is required."""
        with pytest.raises(PydanticValidationError, match="Field required"):
            PaymentRequest(
                public_token=public_token,
                total="10.00",
                phone_number="7875551234",
                metadata1="Test",
                metadata2="Test",
                # items field missing
            )

    def test_payment_request_invalid_items_type(self, public_token: str):
        """Test that items must be a list."""
        with pytest.raises(PydanticValidationError):
            PaymentRequest(
                public_token=public_token,
                total="10.00",
                phone_number="7875551234",
                metadata1="Test",
                metadata2="Test",
                items="not a list",  # Invalid type
            )

    def test_payment_request_items_from_dict(self, public_token: str):
        """Test creating payment request with items from dict."""
        request = PaymentRequest(
            public_token=public_token,
            total="55.00",
            tax="5.00",
            subtotal="50.00",
            phone_number="7875551234",
            metadata1="Test",
            metadata2="Test",
            items=[
                {
                    "name": "Product",
                    "description": "Description",
                    "quantity": "1",
                    "price": "50.00",
                    "tax": "5.00",
                }
            ],
        )

        assert len(request.items) == 1
        assert isinstance(request.items[0], PaymentItem)
        assert request.items[0].name == "Product"


class TestClientWithItems:
    """Test ATHMovilClient with items parameter."""

    def test_create_payment_with_items(
        self, client: ATHMovilClient, httpx_mock, mock_payment_response
    ):
        """Test create_payment with explicit items parameter."""
        from athm.constants import ENDPOINTS

        httpx_mock.add_response(
            method="POST",
            url=f"https://payments.athmovil.com{ENDPOINTS['payment']}",
            json=mock_payment_response,
            status_code=200,
        )

        items = [
            PaymentItem(
                name="Test Product",
                description="Test Description",
                quantity="2",
                price="50.00",
            )
        ]

        response = client.create_payment(
            total="100.00",
            phone_number="7875551234",
            metadata1="Test",
            metadata2="Test",
            items=items,
        )

        assert response.status == "success"

        # Verify the request was made with items
        request = httpx_mock.get_request()
        request_json = request.content.decode()
        assert "Test Product" in request_json
        assert "Test Description" in request_json

    def test_create_payment_with_empty_items(
        self, client: ATHMovilClient, httpx_mock, mock_payment_response
    ):
        """Test create_payment with empty items list."""
        from athm.constants import ENDPOINTS

        httpx_mock.add_response(
            method="POST",
            url=f"https://payments.athmovil.com{ENDPOINTS['payment']}",
            json=mock_payment_response,
            status_code=200,
        )

        response = client.create_payment(
            total="10.00",
            phone_number="7875551234",
            metadata1="Test",
            metadata2="Test",
            items=[],  # Empty list is valid
        )

        assert response.status == "success"

    def test_create_payment_without_items(self, client: ATHMovilClient):
        """Test that create_payment requires items parameter."""
        with pytest.raises(TypeError, match="missing 1 required positional argument: 'items'"):
            # This should fail because items is now required
            client.create_payment(
                total="10.00",
                phone_number="7875551234",
                # items parameter missing
            )

    def test_create_payment_items_validation(self, client: ATHMovilClient):
        """Test that invalid items are caught by validation."""
        with pytest.raises(ValidationError):
            # Invalid item - negative price
            items = [
                {
                    "name": "Product",
                    "description": "Description",
                    "quantity": "1",
                    "price": "-10.00",  # Negative price
                }
            ]
            client.create_payment(
                total="10.00",
                phone_number="7875551234",
                metadata1="Test",
                metadata2="Test",
                items=items,
            )

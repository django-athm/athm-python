from collections.abc import Generator
from datetime import datetime
from typing import Any

import pytest

from athm.client import ATHMovilClient
from athm.models import TransactionStatus

# Sample tokens for testing
SAMPLE_PUBLIC_TOKEN = "test_public_token_123456789"
SAMPLE_PRIVATE_TOKEN = "test_private_token_987654321"
SAMPLE_AUTH_TOKEN = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
)
SAMPLE_ECOMMERCE_ID = "550e8400-e29b-41d4-a716-446655440000"
SAMPLE_REFERENCE_NUMBER = "REF-2024-001234"


@pytest.fixture
def public_token() -> str:
    return SAMPLE_PUBLIC_TOKEN


@pytest.fixture
def private_token() -> str:
    return SAMPLE_PRIVATE_TOKEN


@pytest.fixture
def auth_token() -> str:
    return SAMPLE_AUTH_TOKEN


@pytest.fixture
def ecommerce_id() -> str:
    return SAMPLE_ECOMMERCE_ID


@pytest.fixture
def reference_number() -> str:
    return SAMPLE_REFERENCE_NUMBER


@pytest.fixture
def client(public_token: str, private_token: str) -> Generator[ATHMovilClient, None, None]:
    client = ATHMovilClient(
        public_token=public_token,
        private_token=private_token,
        timeout=5.0,
    )
    yield client
    client.close()


@pytest.fixture
def mock_payment_request() -> dict[str, Any]:
    return {
        "env": "production",
        "publicToken": SAMPLE_PUBLIC_TOKEN,
        "timeout": "600",
        "total": "100.00",
        "tax": "10.00",
        "subtotal": "90.00",
        "metadata1": "Order #123",
        "metadata2": "Customer: John Doe",
        "phoneNumber": "7875551234",
        "items": [
            {
                "name": "Product 1",
                "description": "Test product",
                "quantity": "2",
                "price": "45.00",
                "tax": "5.00",
            }
        ],
    }


@pytest.fixture
def mock_payment_response() -> dict[str, Any]:
    return {
        "status": "success",
        "data": {
            "ecommerceId": SAMPLE_ECOMMERCE_ID,
            "auth_token": SAMPLE_AUTH_TOKEN,
        },
    }


@pytest.fixture
def mock_transaction_response() -> dict[str, Any]:
    return {
        "status": "success",
        "data": {
            "ecommerceStatus": "CONFIRM",
            "ecommerceId": SAMPLE_ECOMMERCE_ID,
            "referenceNumber": SAMPLE_REFERENCE_NUMBER,
            "businessCustomerId": "BUS123",
            "transactionDate": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "dailyTransactionId": 12345,  # API returns as int
            "businessName": "Test Business",
            "businessPath": "/test",
            "industry": "Technology",
            "subTotal": 90.00,  # API returns as float
            "tax": 10.00,  # API returns as float
            "total": 100.00,  # API returns as float
            "fee": 2.50,  # API returns as float
            "netAmount": 97.50,  # API returns as float
            "totalRefundedAmount": 0.00,  # API returns as float
            "metadata1": "Order #123",
            "metadata2": "Customer: John Doe",
            "items": [
                {
                    "name": "Test Product",
                    "description": "Test",
                    "quantity": 1,  # API returns as int
                    "price": 90.0,  # API returns as float
                    "tax": 10.0,  # API returns as float
                }
            ],
            "isNonProfit": False,
        },
    }


@pytest.fixture
def mock_refund_response() -> dict[str, Any]:
    return {
        "status": "success",
        "data": {
            "refund": {
                "transactionType": "REFUND",
                "status": "COMPLETED",
                "refundedAmount": 50.00,
                "date": str(int(datetime.now().timestamp())),
                "referenceNumber": "REFUND123",
                "dailyTransactionId": 2,  # API returns as int
                "name": "John Doe",
                "phoneNumber": "(787) 555-1234",
                "email": "john@example.com",
            },
            "originalTransaction": {
                "transactionType": "PAYMENT",
                "status": "COMPLETED",
                "date": str(int(datetime.now().timestamp())),
                "referenceNumber": SAMPLE_REFERENCE_NUMBER,
                "dailyTransactionId": 1,  # API returns as int
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
                "metadata1": "Order #123",
                "metadata2": "Customer: John Doe",
                "items": [],
            },
        },
    }


@pytest.fixture
def mock_error_response() -> dict[str, Any]:
    return {
        "status": "error",
        "message": "Amount is below minimum",
        "errorcode": "BTRA_0001",
        "data": None,
    }


@pytest.fixture
def mock_auth_error_response() -> dict[str, Any]:
    return {
        "status": "error",
        "message": "Invalid authorization token",
        "errorcode": "BTRA_0017",
        "data": None,
    }


@pytest.fixture
def mock_success_response() -> dict[str, Any]:
    return {
        "status": "success",
        "data": {"message": "Operation completed successfully"},
    }


# Webhook payload fixtures based on ATH Movil webhook documentation
# Ref: https://github.com/evertec/athmovil-webhooks


@pytest.fixture
def mock_webhook_payment_payload() -> dict[str, Any]:
    """Standard payment webhook payload (uses string decimals)."""
    return {
        "transactionType": "payment",
        "status": "completed",
        "date": "2025-01-15 10:30:00",
        "referenceNumber": "REF-2025-001234",
        "dailyTransactionID": "12345",
        "name": "John Doe",
        "phoneNumber": "7875551234",
        "email": "john@example.com",
        "message": "Payment for order #123",
        "total": "100.00",
        "tax": "10.00",
        "subtotal": "90.00",
        "fee": "2.50",
        "netAmount": "97.50",
        "totalRefundedAmount": "0.00",
        "metadata1": "Order #123",
        "metadata2": "Customer: John Doe",
        "items": [
            {
                "name": "Product 1",
                "description": "Test product",
                "quantity": "2",
                "price": "45.00",
                "tax": "5.00",
                "metadata": "SKU123",
            }
        ],
    }


@pytest.fixture
def mock_webhook_ecommerce_completed_payload() -> dict[str, Any]:
    """eCommerce completed webhook payload (uses numbers, different field names)."""
    return {
        "transactionType": "ECOMMERCE",
        "status": "COMPLETED",
        "date": "2025-01-15 10:30:00",
        "transactionDate": "2025-01-15 10:25:00",
        "referenceNumber": "REF-2025-001234",
        "dailyTransactionId": "12345",
        "ecommerceId": SAMPLE_ECOMMERCE_ID,
        "businessName": "Test Business",
        "name": "John Doe",
        "phoneNumber": 7875551234,  # API sends as number for eCommerce
        "email": "john@example.com",
        "message": "",
        "total": 100.00,  # Numbers for eCommerce
        "tax": 10.00,
        "subTotal": 90.00,  # Note: subTotal not subtotal
        "fee": 2.50,
        "netAmount": 97.50,
        "totalRefundedAmount": 0.00,
        "metadata1": "Order #123",
        "metadata2": "Customer: John Doe",
        "isNonProfit": False,
        "referenceTransactionId": "TXN123456",
        "items": [
            {
                "name": "Product 1",
                "description": "Test product",
                "quantity": 2,
                "price": 45.00,
                "tax": 5.00,
                "sku": "SKU123",
                "formattedPrice": "$45.00",
                "metadata": "",
            }
        ],
    }


@pytest.fixture
def mock_webhook_ecommerce_cancelled_payload() -> dict[str, Any]:
    """eCommerce cancelled webhook payload."""
    return {
        "transactionType": "ECOMMERCE",
        "status": "CANCEL",  # Note: CANCEL not CANCELLED
        "date": "2025-01-15 10:30:00",
        "referenceNumber": "",
        "dailyTransactionId": "",
        "ecommerceId": SAMPLE_ECOMMERCE_ID,
        "businessName": "Test Business",
        "name": "",
        "phoneNumber": "",
        "email": "",
        "message": "",
        "total": 100.00,
        "tax": 10.00,
        "subTotal": 90.00,
        "fee": 0,
        "netAmount": 0,
        "totalRefundedAmount": 0,
        "metadata1": "Order #123",
        "metadata2": "",
        "isNonProfit": False,
        "items": [],
    }


@pytest.fixture
def mock_webhook_refund_payload() -> dict[str, Any]:
    """Refund webhook payload."""
    return {
        "transactionType": "refund",
        "status": "completed",
        "date": "2025-01-15 10:30:00",
        "referenceNumber": "REF-REFUND-001",
        "dailyTransactionID": "12346",
        "name": "John Doe",
        "phoneNumber": "7875551234",
        "email": "john@example.com",
        "message": "Refund for order #123",
        "total": "50.00",
        "tax": "5.00",
        "subtotal": "45.00",
        "fee": "0.00",
        "netAmount": "50.00",
        "totalRefundedAmount": "50.00",
        "metadata1": "",
        "metadata2": "",
        "items": [],
    }


@pytest.fixture
def mock_webhook_subscription_response() -> dict[str, Any]:
    """Successful webhook subscription response."""
    return {
        "status": "success",
        "data": {"message": "Webhook subscription updated successfully"},
    }


def create_mock_transaction(status: TransactionStatus = TransactionStatus.OPEN) -> dict[str, Any]:
    return {
        "status": "success",
        "data": {
            "ecommerceStatus": status.value,
            "ecommerceId": SAMPLE_ECOMMERCE_ID,
            "referenceNumber": SAMPLE_REFERENCE_NUMBER
            if status == TransactionStatus.COMPLETED
            else "",
            "businessCustomerId": "BUS123",
            "transactionDate": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if status == TransactionStatus.COMPLETED
            else "",
            "dailyTransactionId": 12345,  # API returns as int
            "businessName": "Test Business",
            "businessPath": "/test",
            "industry": "Technology",
            "subTotal": 90.00,  # API returns as float
            "tax": 10.00,  # API returns as float
            "total": 100.00,  # API returns as float
            "fee": 2.50,  # API returns as float
            "netAmount": 97.50,  # API returns as float
            "totalRefundedAmount": 0.00,  # API returns as float
            "metadata1": "Order #123",
            "metadata2": "Customer: John Doe",
            "items": [
                {
                    "name": "Test Product",
                    "description": "Test",
                    "quantity": 1,  # API returns as int
                    "price": 90.0,  # API returns as float
                    "tax": 10.0,  # API returns as float
                }
            ],
            "isNonProfit": False,
        },
    }

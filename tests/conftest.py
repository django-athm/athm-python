from collections.abc import Generator
from datetime import datetime
from typing import Any

import pytest
from pytest_httpx import HTTPXMock

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
                "dailyTransactionID": 2,  # API returns as int
                "name": "John Doe",
                "phoneNumber": "(787) 555-1234",
                "email": "john@example.com",
            },
            "originalTransaction": {
                "transactionType": "PAYMENT",
                "status": "COMPLETED",
                "date": str(int(datetime.now().timestamp())),
                "referenceNumber": SAMPLE_REFERENCE_NUMBER,
                "dailyTransactionID": 1,  # API returns as int
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


@pytest.fixture
def httpx_mock_client(httpx_mock: HTTPXMock) -> HTTPXMock:
    return httpx_mock

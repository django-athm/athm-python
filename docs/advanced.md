# Advanced Usage

Advanced patterns and features for production applications.

## Refunds

Process refunds on completed payments. Requires **private token**.

### Basic Refund

```python
from athm import ATHMovilClient

# Initialize with both tokens
client = ATHMovilClient(
    public_token=os.getenv("ATHM_PUBLIC_TOKEN"),
    private_token=os.getenv("ATHM_PRIVATE_TOKEN")  # Required for refunds
)

# Refund a completed payment
refund = client.refund_payment(
    reference_number="123456",  # From completed payment
    amount="50.00",             # Full or partial amount
    message="Refund for order #123"  # Optional, max 50 chars
)

print(f"Refund processed: {refund.reference_number}")
print(f"Amount refunded: ${refund.refunded_amount}")
```

### Partial Refunds

```python
# Original payment was $100
# Refund only $25
refund = client.refund_payment(
    reference_number="123456",
    amount="25.00",  # Partial amount
    message="Partial refund"
)

# Can refund remaining $75 later with another call
second_refund = client.refund_payment(
    reference_number="123456",
    amount="75.00",
    message="Remaining refund"
)
```

### Check Refund Eligibility

```python
from athm import RefundError

def can_refund(client: ATHMovilClient, reference_number: str) -> bool:
    """Check if a payment can be refunded."""
    try:
        # Get payment status
        # Note: Need to track ecommerce_id to check status
        status = client.find_payment(ecommerce_id)

        # Can only refund COMPLETED payments
        if status.data.status != "COMPLETED":
            return False

        # Check if already refunded (track in your DB)
        # ATH Móvil doesn't provide refund status via API

        return True

    except Exception:
        return False
```

### Refund Error Handling

```python
from athm import RefundError, AuthenticationError

try:
    refund = client.refund_payment(
        reference_number="123456",
        amount="50.00"
    )
except AuthenticationError:
    print("Missing or invalid private token")
except RefundError as e:
    if "not found" in str(e).lower():
        print("Invalid reference number")
    elif "already refunded" in str(e).lower():
        print("Payment already refunded")
    else:
        print(f"Refund failed: {e}")
```

### Track Refunds in Your Database

ATH Móvil doesn't provide refund history via API. Track refunds yourself:

```python
# Example database model (SQLAlchemy)
class Payment(Base):
    __tablename__ = 'payments'

    id = Column(Integer, primary_key=True)
    ecommerce_id = Column(String, unique=True)
    reference_number = Column(String, unique=True)
    amount = Column(Numeric(10, 2))
    refunded_amount = Column(Numeric(10, 2), default=0)
    status = Column(String)

def process_refund(payment_id: int, amount: Decimal) -> bool:
    """Process refund and update database."""
    payment = db.query(Payment).get(payment_id)

    # Check if refundable
    if payment.status != "COMPLETED":
        return False

    remaining = payment.amount - payment.refunded_amount
    if amount > remaining:
        return False

    # Process with ATH Móvil
    try:
        refund = client.refund_payment(
            reference_number=payment.reference_number,
            amount=str(amount)
        )

        # Update database
        payment.refunded_amount += amount
        if payment.refunded_amount >= payment.amount:
            payment.status = "REFUNDED"

        db.commit()
        return True

    except RefundError:
        db.rollback()
        return False
```

## Context Manager Pattern

Use context managers for automatic resource cleanup:

### Basic Context Manager

```python
from athm import ATHMovilClient

# Automatically calls client.close()
with ATHMovilClient(public_token="...") as client:
    payment = client.create_payment(
        total="50.00",
        phone_number="7875551234",
        subtotal="50.00",
        tax="0.00"
    )

    confirmed = client.wait_for_confirmation(payment.ecommerce_id)
    result = client.authorize_payment(payment.ecommerce_id)

    print(f"Reference: {result.data.reference_number}")

# Client is automatically closed here
```

### Nested Operations

```python
# Multiple clients (rare, but possible)
with ATHMovilClient(public_token="token1") as client1, \
     ATHMovilClient(public_token="token2") as client2:

    payment1 = client1.create_payment(...)
    payment2 = client2.create_payment(...)
```

### Manual vs Context Manager

```python
# Manual cleanup
client = ATHMovilClient(public_token="...")
try:
    payment = client.create_payment(...)
finally:
    client.close()  # Must remember to close

# Context manager (preferred)
with ATHMovilClient(public_token="...") as client:
    payment = client.create_payment(...)
# Automatic cleanup
```

## Custom Timeouts and Retries

### Configure Timeouts

```python
# Short timeout for fast-fail
client = ATHMovilClient(
    public_token="...",
    timeout=10  # 10 seconds (default: 30)
)

# Long timeout for slow connections
client = ATHMovilClient(
    public_token="...",
    timeout=60  # 60 seconds
)

# Disable timeout (not recommended)
client = ATHMovilClient(
    public_token="...",
    timeout=None  # Wait forever
)
```

### Configure Retries

```python
# More aggressive retries
client = ATHMovilClient(
    public_token="...",
    max_retries=5  # 5 retry attempts (default: 3)
)

# Disable retries
client = ATHMovilClient(
    public_token="...",
    max_retries=0  # Fail immediately
)
```

### Per-Operation Timeouts

```python
# Client default timeout
client = ATHMovilClient(public_token="...", timeout=30)

# Override for specific operation
payment = client.create_payment(...)  # Uses 30s timeout

# Longer wait for confirmation
confirmed = client.wait_for_confirmation(
    payment.ecommerce_id,
    polling_interval=2.0,
    max_attempts=300  # 10 minutes (300 * 2s)
)
```

## Testing

### Mock the Client

```python
from unittest.mock import Mock, patch
from athm import ATHMovilClient
from athm.models import PaymentResponse

def test_payment_creation():
    """Test payment creation with mocked client."""
    client = ATHMovilClient(public_token="test_token")

    # Mock the create_payment method
    with patch.object(client, 'create_payment') as mock_create:
        # Configure mock return value
        mock_create.return_value = PaymentResponse(
            ecommerce_id="test-123",
            auth_token="token-123"
        )

        # Test your code
        payment = client.create_payment(
            total="50.00",
            phone_number="7875551234",
            subtotal="50.00",
            tax="0.00"
        )

        assert payment.ecommerce_id == "test-123"
        mock_create.assert_called_once()
```

### Mock HTTP Responses

```python
import pytest
from unittest.mock import patch
from athm import ATHMovilClient, ValidationError

@pytest.fixture
def client():
    return ATHMovilClient(public_token="test_token")

def test_validation_error(client):
    """Test handling of validation errors."""
    with patch('httpx.Client.post') as mock_post:
        # Mock API error response
        mock_post.return_value.status_code = 400
        mock_post.return_value.json.return_value = {
            "errorCode": "BTRA_0001",
            "message": "Amount is below minimum"
        }

        with pytest.raises(ValidationError) as exc_info:
            client.create_payment(
                total="0.50",  # Below minimum
                phone_number="7875551234",
                subtotal="0.50",
                tax="0.00"
            )

        assert exc_info.value.error_code == "BTRA_0001"
```

### Test Fixtures

```python
import pytest
from athm import ATHMovilClient

@pytest.fixture
def athm_client():
    """Provide ATH Móvil client for tests."""
    return ATHMovilClient(public_token="test_token")

@pytest.fixture
def mock_payment_response():
    """Provide mock payment response."""
    return {
        "ecommerceId": "test-123",
        "authToken": "token-123"
    }

def test_with_fixtures(athm_client, mock_payment_response):
    """Test using fixtures."""
    with patch.object(athm_client, '_make_request') as mock_request:
        mock_request.return_value = mock_payment_response

        payment = athm_client.create_payment(...)
        assert payment.ecommerce_id == "test-123"
```

### Integration Tests

```python
import os
import pytest
from athm import ATHMovilClient

@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("ATHM_PUBLIC_TOKEN"),
    reason="No ATH token configured"
)
def test_real_payment_flow():
    """Integration test with real API (requires token)."""
    client = ATHMovilClient(public_token=os.getenv("ATHM_PUBLIC_TOKEN"))

    try:
        # Create test payment
        payment = client.create_payment(
            total="1.00",
            phone_number="7875551234",
            subtotal="1.00",
            tax="0.00",
            metadata1="Integration Test"
        )

        assert payment.ecommerce_id is not None

        # Check status
        status = client.find_payment(payment.ecommerce_id)
        assert status.data.status == "OPEN"

    finally:
        # Clean up
        try:
            client.cancel_payment(payment.ecommerce_id)
        except:
            pass
        client.close()
```

## Production Patterns

### Database Integration

```python
from sqlalchemy import Column, String, Numeric, DateTime, Enum
from datetime import datetime
import enum

class PaymentStatus(enum.Enum):
    PENDING = "pending"
    OPEN = "open"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"

class Payment(Base):
    __tablename__ = 'payments'

    id = Column(Integer, primary_key=True)
    ecommerce_id = Column(String, unique=True, index=True)
    reference_number = Column(String, unique=True, nullable=True)
    amount = Column(Numeric(10, 2), nullable=False)
    phone_number = Column(String(10), nullable=False)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

def create_tracked_payment(db, client: ATHMovilClient, amount: str, phone: str) -> Payment:
    """Create payment and track in database."""
    # Create in ATH Móvil
    payment = client.create_payment(
        total=amount,
        phone_number=phone,
        subtotal=amount,
        tax="0.00"
    )

    # Save to database
    db_payment = Payment(
        ecommerce_id=payment.ecommerce_id,
        amount=amount,
        phone_number=phone,
        status=PaymentStatus.OPEN
    )
    db.add(db_payment)
    db.commit()

    return db_payment
```

### Background Job Processing

```python
# Using Celery
from celery import Celery
from athm import ATHMovilClient, TimeoutError

app = Celery('tasks')

@app.task
def process_payment(ecommerce_id: str):
    """Background task to wait for payment confirmation."""
    client = ATHMovilClient(public_token=os.getenv("ATHM_PUBLIC_TOKEN"))

    try:
        # Wait for confirmation (up to 10 minutes)
        confirmed = client.wait_for_confirmation(
            ecommerce_id,
            polling_interval=2.0,
            max_attempts=300
        )

        # Authorize
        result = client.authorize_payment(ecommerce_id)

        # Update database
        update_payment_status(
            ecommerce_id,
            status="completed",
            reference_number=result.data.reference_number
        )

        # Send confirmation email
        send_confirmation_email(ecommerce_id)

    except TimeoutError:
        # Cancel on timeout
        client.cancel_payment(ecommerce_id)
        update_payment_status(ecommerce_id, status="cancelled")

    finally:
        client.close()

# Trigger from web request
@app.route('/payment', methods=['POST'])
def create_payment():
    payment = client.create_payment(...)

    # Queue background job
    process_payment.delay(payment.ecommerce_id)

    return {"ecommerce_id": payment.ecommerce_id}
```

### Logging and Monitoring

```python
import structlog
from athm import ATHMovilClient, ATHMovilError

logger = structlog.get_logger()

def monitored_payment(amount: str, phone: str) -> str | None:
    """Payment with comprehensive logging."""
    logger.info(
        "payment_initiated",
        amount=amount,
        phone=phone[-4:]  # Only log last 4 digits
    )

    client = ATHMovilClient(public_token=os.getenv("ATHM_PUBLIC_TOKEN"))

    try:
        # Create
        payment = client.create_payment(
            total=amount,
            phone_number=phone,
            subtotal=amount,
            tax="0.00"
        )
        logger.info(
            "payment_created",
            ecommerce_id=payment.ecommerce_id
        )

        # Wait
        confirmed = client.wait_for_confirmation(payment.ecommerce_id)
        logger.info(
            "payment_confirmed",
            ecommerce_id=payment.ecommerce_id
        )

        # Authorize
        result = client.authorize_payment(payment.ecommerce_id)
        logger.info(
            "payment_completed",
            ecommerce_id=payment.ecommerce_id,
            reference_number=result.data.reference_number
        )

        return result.data.reference_number

    except ATHMovilError as e:
        logger.error(
            "payment_failed",
            error_code=e.error_code,
            error_type=type(e).__name__,
            ecommerce_id=getattr(payment, 'ecommerce_id', None)
        )
        return None

    finally:
        client.close()
```

### Rate Limiting

```python
from ratelimit import limits, sleep_and_retry
import time

# Limit to 10 payments per minute
@sleep_and_retry
@limits(calls=10, period=60)
def create_payment_rate_limited(client: ATHMovilClient, **kwargs):
    """Create payment with rate limiting."""
    return client.create_payment(**kwargs)

# Usage
for order in orders:
    payment = create_payment_rate_limited(
        client,
        total=order.amount,
        phone_number=order.phone
    )
```

### Circuit Breaker Pattern

```python
from pybreaker import CircuitBreaker

# Trip breaker after 5 failures, half-open after 60s
breaker = CircuitBreaker(fail_max=5, timeout_duration=60)

@breaker
def create_payment_with_breaker(client: ATHMovilClient, **kwargs):
    """Create payment with circuit breaker."""
    return client.create_payment(**kwargs)

# Usage
try:
    payment = create_payment_with_breaker(client, ...)
except CircuitBreakerError:
    # Too many failures, circuit is open
    logger.error("ATH Móvil service unavailable")
    return error_response("Payment service temporarily unavailable")
```

## Environment-Specific Configuration

```python
import os
from dataclasses import dataclass

@dataclass
class ATHConfig:
    public_token: str
    private_token: str | None
    timeout: int
    max_retries: int

def get_config() -> ATHConfig:
    """Get environment-specific configuration."""
    env = os.getenv("ENVIRONMENT", "development")

    if env == "production":
        return ATHConfig(
            public_token=os.getenv("ATHM_PUBLIC_TOKEN"),
            private_token=os.getenv("ATHM_PRIVATE_TOKEN"),
            timeout=30,
            max_retries=3
        )
    elif env == "staging":
        return ATHConfig(
            public_token=os.getenv("ATHM_STAGING_PUBLIC_TOKEN"),
            private_token=os.getenv("ATHM_STAGING_PRIVATE_TOKEN"),
            timeout=60,
            max_retries=5
        )
    else:  # development
        return ATHConfig(
            public_token=os.getenv("ATHM_DEV_PUBLIC_TOKEN"),
            private_token=None,
            timeout=120,
            max_retries=1
        )

# Usage
config = get_config()
client = ATHMovilClient(
    public_token=config.public_token,
    private_token=config.private_token,
    timeout=config.timeout,
    max_retries=config.max_retries
)
```

## Webhook Alternative

While ATH Móvil doesn't provide webhooks, you can simulate them:

```python
# Background job that polls and calls webhook
@app.task
def poll_and_notify(ecommerce_id: str, webhook_url: str):
    """Poll for confirmation and notify via webhook."""
    client = ATHMovilClient(public_token=os.getenv("ATHM_PUBLIC_TOKEN"))

    try:
        # Wait for confirmation
        confirmed = client.wait_for_confirmation(ecommerce_id)

        # Authorize
        result = client.authorize_payment(ecommerce_id)

        # Call webhook
        import httpx
        httpx.post(webhook_url, json={
            "event": "payment.completed",
            "ecommerce_id": ecommerce_id,
            "reference_number": result.data.reference_number,
            "amount": result.data.total
        })

    finally:
        client.close()
```

## Next Steps

- **[API Reference](api-reference.md)** - Complete method documentation
- **[Error Handling](errors.md)** - All error codes and solutions
- **[Payment Flow Guide](guide.md)** - Step-by-step walkthrough

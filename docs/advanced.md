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

    confirmed = client.wait_for_confirmation(payment.data.ecommerce_id)
    result = client.authorize_payment(payment.data.ecommerce_id)

    print(f"Reference: {result.data.reference_number}")

# Client is automatically closed here
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
    payment.data.ecommerce_id,
    polling_interval=2.0,
    max_attempts=300  # 10 minutes (300 * 2s)
)
```

## Next Steps

- **[API Reference](api-reference.md)** - Complete method documentation
- **[Error Handling](errors.md)** - All error codes and solutions
- **[Payment Flow Guide](guide.md)** - Step-by-step walkthrough

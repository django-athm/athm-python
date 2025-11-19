# API Reference

Complete reference for the key classes and methods in the ATH Móvil Python library.

## Client

### ATHMovilClient

::: athm.client.ATHMovilClient
    options:
      show_source: false
      heading_level: 4
      members:
        - __init__
        - create_payment
        - find_payment
        - authorize_payment
        - wait_for_confirmation
        - process_complete_payment
        - update_phone_number
        - cancel_payment
        - refund_payment
        - close

## Models

### Payment Models

#### PaymentRequest

::: athm.models.PaymentRequest
    options:
      show_source: false
      heading_level: 5

#### PaymentResponse

::: athm.models.PaymentResponse
    options:
      show_source: false
      heading_level: 5

#### PaymentItem

::: athm.models.PaymentItem
    options:
      show_source: false
      heading_level: 5

### Transaction Models

#### TransactionResponse

::: athm.models.TransactionResponse
    options:
      show_source: false
      heading_level: 5

#### TransactionData

::: athm.models.TransactionData
    options:
      show_source: false
      heading_level: 5

#### TransactionStatus

::: athm.models.TransactionStatus
    options:
      show_source: false
      heading_level: 5
      members:
        - OPEN
        - CONFIRM
        - COMPLETED
        - CANCEL

### Refund Models

#### RefundRequest

::: athm.models.RefundRequest
    options:
      show_source: false
      heading_level: 5

#### RefundResponse

::: athm.models.RefundResponse
    options:
      show_source: false
      heading_level: 5

## Exceptions

### Exception Hierarchy

All exceptions inherit from `ATHMovilError`:

```python
ATHMovilError (base exception)
├── AuthenticationError          # Invalid tokens, auth failures
├── ValidationError              # Invalid amounts, phone, metadata
├── InvalidRequestError          # Malformed requests
├── TransactionError            # Transaction state errors
│   ├── PaymentError            # Payment-specific errors
│   └── RefundError             # Refund-specific errors
├── TimeoutError                # Network or polling timeout
├── RateLimitError              # Too many requests
├── NetworkError                # Connection issues
└── InternalServerError         # ATH Móvil server errors
```

### ATHMovilError

::: athm.exceptions.ATHMovilError
    options:
      show_source: false
      heading_level: 4

### AuthenticationError

::: athm.exceptions.AuthenticationError
    options:
      show_source: false
      heading_level: 4

### ValidationError

::: athm.exceptions.ValidationError
    options:
      show_source: false
      heading_level: 4

### TransactionError

::: athm.exceptions.TransactionError
    options:
      show_source: false
      heading_level: 4

### PaymentError

::: athm.exceptions.PaymentError
    options:
      show_source: false
      heading_level: 4

### RefundError

::: athm.exceptions.RefundError
    options:
      show_source: false
      heading_level: 4

### TimeoutError

::: athm.exceptions.TimeoutError
    options:
      show_source: false
      heading_level: 4

### NetworkError

::: athm.exceptions.NetworkError
    options:
      show_source: false
      heading_level: 4

## Quick Reference

### Common Operations

```python
from athm import ATHMovilClient

# Initialize
client = ATHMovilClient(public_token="...")

# Create payment
payment = client.create_payment(
    total="50.00",
    phone_number="7875551234",
    subtotal="50.00",
    tax="0.00"
)

# Check status
status = client.find_payment(payment.ecommerce_id)

# Wait for confirmation
confirmed = client.wait_for_confirmation(payment.ecommerce_id)

# Authorize
result = client.authorize_payment(payment.ecommerce_id)

# Refund (requires private_token)
refund = client.refund_payment(
    reference_number=result.data.reference_number,
    amount="50.00"
)

# Cleanup
client.close()
```

### Context Manager Pattern

```python
from athm import ATHMovilClient

with ATHMovilClient(public_token="...") as client:
    payment = client.create_payment(...)
    # ... rest of flow
# Automatically closes
```

### Amount Constraints

- **Minimum**: $1.00
- **Maximum**: $1,500.00
- **Format**: String with 2 decimal places (e.g., "50.00")
- **Validation**: Automatic via Pydantic

### Phone Number Format

- **Length**: Exactly 10 digits
- **Format**: String without dashes or spaces
- **Example**: "7875551234"
- **Validation**: Automatic pattern matching

### Metadata Limits

- **metadata1**: Max 40 characters
- **metadata2**: Max 40 characters
- **Use for**: Order IDs, customer info, tracking data

## Type Safety

All models use Pydantic for validation:

```python
from athm.models import PaymentRequest

# This will raise ValidationError
payment = PaymentRequest(
    total="9999.00",  # Exceeds max $1500
    phone="123",      # Invalid format
    metadata1="x" * 50  # Too long
)
```

## Environment Configuration

```python
# Production
client = ATHMovilClient(
    public_token="...",
    base_url="https://payments.athmovil.com"  # Default
)

# Custom timeout
client = ATHMovilClient(
    public_token="...",
    timeout=60  # Seconds
)

# Custom retries
client = ATHMovilClient(
    public_token="...",
    max_retries=5  # Automatic retry attempts
)
```

## See Also

- **[Payment Flow Guide](guide.md)** - Complete walkthrough
- **[Error Handling](errors.md)** - All error codes
- **[Advanced Usage](advanced.md)** - Refunds and testing

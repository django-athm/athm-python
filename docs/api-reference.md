# API Reference

Complete reference for the key classes and methods in the ATH Móvil unofficial library.

## Client

### ATHMovilClient

Main client for interacting with the ATH Móvil Payment API.

**Initialization:**

```python
from athm import ATHMovilClient

client = ATHMovilClient(
    public_token="your_public_token",
    private_token="your_private_token",  # Optional, required for refunds
    base_url="https://payments.athmovil.com",  # Default
    timeout=30,  # Request timeout in seconds
    max_retries=3,  # Automatic retry attempts
    verify_ssl=True  # SSL certificate verification
)
```

**Parameters:**

- `public_token` (str, required): Your ATH Business public token
- `private_token` (str, optional): Your ATH Business private token (required only for refunds)
- `base_url` (str): API base URL (defaults to production)
- `timeout` (int | float): Request timeout in seconds (default: 30)
- `max_retries` (int): Maximum number of retry attempts (default: 3)
- `verify_ssl` (bool): Whether to verify SSL certificates (default: True)

**Context Manager:**

```python
with ATHMovilClient(public_token="...") as client:
    payment = client.create_payment(...)
# Automatically closes connection
```

---

#### create_payment()

Create a new payment ticket.

```python
payment = client.create_payment(
    total="50.00",
    phone_number="7875551234",
    items=[
        {
            "name": "Product",
            "description": "Description",
            "quantity": "1",
            "price": "50.00",
        }
    ],
    subtotal="50.00",  # Optional
    tax="0.00",  # Optional
    metadata1="Order-123",  # Optional
    metadata2="Customer-456",  # Optional
    timeout=600  # Payment expiry in seconds (min: 120)
)
```

**Parameters:**

- `total` (str): Total payment amount ($1.00 - $1,500.00)
- `phone_number` (str): Customer's 10-digit phone number
- `items` (list[PaymentItem]): List of payment items (required)
- `subtotal` (str): Subtotal amount before tax (optional)
- `tax` (str): Tax amount (optional)
- `metadata1` (str, optional): Custom metadata (max 40 chars)
- `metadata2` (str, optional): Custom metadata (max 40 chars)
- `timeout` (int, optional): Payment timeout in seconds (min: 120)

**Returns:** `PaymentResponse` with `ecommerce_id` and `auth_token`

**Raises:** `ValidationError`, `AuthenticationError`, `NetworkError`

---

#### find_payment()

Check the status of a payment.

```python
status = client.find_payment(ecommerce_id="abc123")
```

**Parameters:**

- `ecommerce_id` (str): The payment ID from create_payment()

**Returns:** `TransactionResponse` with current payment status

**Raises:** `TransactionError`, `AuthenticationError`

---

#### wait_for_confirmation()

Wait for customer to confirm payment by polling status.

```python
client.wait_for_confirmation(
    ecommerce_id="abc123",
    timeout=300,  # Default: 5 minutes
    polling_interval=2.0  # Default: 2 seconds
)
```

**Parameters:**

- `ecommerce_id` (str): The payment ID from create_payment()
- `timeout` (int, optional): Maximum seconds to wait (default: 300)
- `polling_interval` (float, optional): Seconds between checks (default: 2.0)

**Returns:** `True` if payment was confirmed

**Raises:** `TimeoutError` (if timeout exceeded), `TransactionError` (if cancelled)

---

#### authorize_payment()

Authorize and complete a confirmed payment.

```python
result = client.authorize_payment(ecommerce_id="abc123")
reference_number = result.data.reference_number
```

**Parameters:**

- `ecommerce_id` (str): The payment ID from create_payment()

**Returns:** `TransactionResponse` with `reference_number`

**Raises:** `TransactionError` (if not confirmed yet), `AuthenticationError`

---

#### update_phone_number()

Update the phone number for an existing payment.

```python
client.update_phone_number(
    ecommerce_id="abc123",
    phone_number="7875559999"
)
```

**Parameters:**

- `ecommerce_id` (str): The payment ID
- `phone_number` (str): New 10-digit phone number

**Returns:** `SuccessResponse`

**Raises:** `ValidationError`, `TransactionError`

---

#### cancel_payment()

Cancel a pending payment.

```python
client.cancel_payment(ecommerce_id="abc123")
```

**Parameters:**

- `ecommerce_id` (str): The payment ID to cancel

**Returns:** `SuccessResponse`

**Raises:** `TransactionError` (if already completed)

---

#### refund_payment()

Refund a completed payment (requires `private_token`).

```python
refund = client.refund_payment(
    reference_number="123456",
    amount="50.00",
    message="Refund for order cancellation"  # Optional, max 50 chars
)
```

**Parameters:**

- `reference_number` (str): The reference number from completed payment
- `amount` (str): Refund amount (must match or be less than original)
- `message` (str, optional): Refund reason (max 50 chars)

**Returns:** `RefundResponse` with refund details

**Raises:** `TransactionError`, `AuthenticationError` (if no private_token)

---

#### close()

Close the HTTP client connection.

```python
client.close()
```

Always call this when done, or use the context manager pattern.

---

## Models

### PaymentRequest

Request model for creating payments.

```python
from athm.models import PaymentRequest

request = PaymentRequest(
    total="50.00",
    phone_number="7875551234",
    subtotal="50.00",
    tax="0.00",
    metadata1="Order-123",
    metadata2="Customer-456",
    timeout=600,
    items=[]  # Required field
)
```

**Fields:**

- `total` (str): Total amount
- `phone_number` (str): 10-digit phone number
- `items` (list[PaymentItem]): List of payment items (required)
- `subtotal` (str): Subtotal before tax
- `tax` (str): Tax amount
- `metadata1` (str | None): Custom metadata
- `metadata2` (str | None): Custom metadata
- `timeout` (int): Timeout in seconds

---

### PaymentResponse

Response from creating a payment.

```python
payment = client.create_payment(...)

print(payment.data.ecommerce_id)  # Payment ID
print(payment.data.auth_token)    # Authorization token
```

**Fields:**

- `ecommerce_id` (str): Unique payment identifier
- `auth_token` (str): Authorization token for this payment

---

### TransactionResponse

Response from payment status and authorization operations.

```python
status = client.find_payment(ecommerce_id)

print(status.status)  # "OPEN", "CONFIRM", "COMPLETED", "CANCEL"
print(status.data.reference_number)  # Available after authorization
print(status.data.daily_transaction_id)
```

**Fields:**

- `status` (str): Payment status
- `data` (TransactionData): Transaction details

**TransactionData fields:**

- `reference_number` (str | None): Transaction reference (after completion)
- `daily_transaction_id` (int | None): Daily transaction ID
- `name` (str | None): Customer name
- `phone_number` (str | None): Customer phone
- `metadata1` (str | None): Custom metadata
- `metadata2` (str | None): Custom metadata
- `tax` (str | None): Tax amount
- `subtotal` (str | None): Subtotal
- `total` (str | None): Total amount
- `fee` (str | None): Processing fee
- `net_amount` (str | None): Net amount after fee
- `total_refunded` (str | None): Total refunded amount
- `items` (list[PaymentItem] | None): Payment items

---

### TransactionStatus

Enum of possible payment statuses.

```python
from athm.models import TransactionStatus

# Available statuses:
TransactionStatus.OPEN       # Payment created, awaiting customer
TransactionStatus.CONFIRM    # Customer confirmed, ready to authorize
TransactionStatus.COMPLETED  # Payment authorized and completed
TransactionStatus.CANCEL     # Payment cancelled or timed out
```

---

### RefundRequest

Request model for refunds.

```python
from athm.models import RefundRequest

refund_req = RefundRequest(
    reference_number="123456",
    amount="50.00",
    message="Customer requested refund"
)
```

**Fields:**

- `reference_number` (str): Original payment reference
- `amount` (str): Refund amount
- `message` (str | None): Refund reason (max 50 chars)

---

### RefundResponse

Response from refund operations.

```python
refund = client.refund_payment(...)

print(refund.refund_status)  # "completed"
print(refund.reference_number)
```

**Fields:**

- `refund_status` (str): Refund status
- `reference_number` (str): Original transaction reference
- `date` (str | None): Refund date
- `daily_transaction_id` (str | None): Transaction ID

---

## Exceptions

### Exception Hierarchy

All exceptions inherit from `ATHMovilError`:

```
ATHMovilError (base exception)
├── AuthenticationError          # Invalid tokens, auth failures
├── ValidationError              # Invalid amounts, phone, metadata
├── TransactionError             # Transaction state errors
├── TimeoutError                 # Network or polling timeout
├── RateLimitError               # Too many requests
├── NetworkError                 # Connection issues
└── InternalServerError          # ATH Móvil server errors
```

### ATHMovilError

Base exception for all API errors.

```python
from athm import ATHMovilError

try:
    payment = client.create_payment(...)
except ATHMovilError as e:
    print(f"Error: {e}")
    print(f"Error code: {e.error_code}")
    print(f"Status code: {e.status_code}")
    print(f"Response: {e.response_data}")
```

**Attributes:**

- `message` (str): Error message
- `error_code` (str | None): ATH Móvil API error code
- `status_code` (int | None): HTTP status code
- `response_data` (dict | None): Full API response

---

### AuthenticationError

Raised when authentication fails.

```python
from athm import AuthenticationError

try:
    payment = client.create_payment(...)
except AuthenticationError as e:
    print("Invalid or expired token")
```

**Common error codes:** `token.invalid.header`, `token.expired`, `BTRA_0401`, `BTRA_0017`

---

### ValidationError

Raised when input validation fails.

```python
from athm import ValidationError

try:
    payment = client.create_payment(total="0.50", ...)  # Too low
except ValidationError as e:
    print(f"Invalid input: {e}")
```

**Common error codes:** `BTRA_0001` (amount too low), `BTRA_0004` (amount too high), `BTRA_0038` (metadata too long)

---

### TransactionError

Raised when transaction operations fail.

```python
from athm import TransactionError

try:
    result = client.authorize_payment(ecommerce_id)
except TransactionError as e:
    if e.error_code == "BTRA_0032":
        print("Payment not confirmed yet")
```

**Common error codes:** `BTRA_0032` (not confirmed), `BTRA_0037` (cancelled), `BTRA_0039` (expired)

---

### TimeoutError

Raised when requests or polling timeout.

```python
from athm import TimeoutError

try:
    client.wait_for_confirmation(ecommerce_id, timeout=300)
except TimeoutError:
    print("Customer didn't confirm in time")
    client.cancel_payment(ecommerce_id)
```

---

### NetworkError

Raised for network and connection issues.

```python
from athm import NetworkError

try:
    payment = client.create_payment(...)
except NetworkError as e:
    print("Network error, will retry")
```

**Error code:** `BTRA_9998`

---

### InternalServerError

Raised for ATH Móvil server errors.

```python
from athm import InternalServerError

try:
    payment = client.create_payment(...)
except InternalServerError as e:
    print("ATH Móvil server error")
```

**Error code:** `BTRA_9999`

---

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
    items=[
        {"name": "Product", "description": "Description", "quantity": "1", "price": "50.00"}
    ],
    subtotal="50.00",
    tax="0.00"
)

# Wait for confirmation
client.wait_for_confirmation(payment.data.ecommerce_id)

# Authorize
result = client.authorize_payment(payment.data.ecommerce_id)

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

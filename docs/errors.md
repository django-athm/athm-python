# Error Handling

Complete guide to handling errors in the ATH Móvil unofficial library.

## Exception Hierarchy

All exceptions inherit from `ATHMovilError`:

```
ATHMovilError (base exception)
├── AuthenticationError          # Invalid tokens, auth failures
├── ValidationError              # Invalid amounts, phone, metadata
├── InvalidRequestError          # Malformed requests
├── TransactionError             # Transaction state errors
│   ├── PaymentError             # Payment-specific errors
│   └── RefundError              # Refund-specific errors
├── TimeoutError                 # Network or polling timeout
├── RateLimitError               # Too many requests
├── NetworkError                 # Connection issues
└── InternalServerError          # ATH Móvil server errors
```

## Basic Error Handling

### Catch Specific Exceptions

```python
from athm import (
    ATHMovilClient,
    AuthenticationError,
    ValidationError,
    TransactionError,
    TimeoutError,
    ATHMovilError
)

client = ATHMovilClient(public_token="...")

try:
    payment = client.create_payment(
        total="50.00",
        phone_number="7875551234",
        subtotal="50.00",
        tax="0.00"
    )

except ValidationError as e:
    # Invalid amount, phone, or metadata
    print(f"Validation failed: {e}")
    print(f"Error code: {e.error_code}")

except AuthenticationError as e:
    # Invalid or expired token
    print(f"Authentication failed: {e}")
    print("Check your PUBLIC_TOKEN")

except TransactionError as e:
    # Transaction state errors
    print(f"Transaction error: {e}")

except TimeoutError as e:
    # Network or polling timeout
    print(f"Request timed out: {e}")

except ATHMovilError as e:
    # Catch-all for any API error
    print(f"ATH Móvil error: {e}")

finally:
    client.close()
```

### Exception Attributes

All exceptions include:

```python
try:
    payment = client.create_payment(...)
except ATHMovilError as e:
    print(f"Message: {e}")
    print(f"Error code: {e.error_code}")  # May be None
    print(f"Status code: {e.status_code}")  # May be None
    print(f"Response: {e.response}")  # Full API response
```

## Complete Error Code Reference

### Authentication Errors

Authentication failures, invalid or expired tokens.

| Error Code | Description | Solution |
|------------|-------------|----------|
| `token.invalid.header` | No authorization header provided | Ensure `public_token` is set when creating client |
| `token.expired` | Authorization token has expired | Generate new token in ATH Business portal |
| `BTRA_0401` | Authorization token issue | Check token format and validity |
| `BTRA_0402` | Authorization token issue | Check token format and validity |
| `BTRA_0403` | Authorization token issue | Check token format and validity |
| `BTRA_0017` | Invalid authorization token | Use correct public token from ATH Business |

**Recovery Strategy:**
```python
try:
    payment = client.create_payment(...)
except AuthenticationError as e:
    if "expired" in str(e).lower():
        # Token expired - user needs new one
        notify_admin("ATH token expired, please update")
    else:
        # Invalid token
        log_error(f"Check ATH_PUBLIC_TOKEN: {e}")
    raise  # Can't recover automatically
```

### Validation Errors

Invalid input data (amounts, phone numbers, metadata).

| Error Code | Description | Solution |
|------------|-------------|----------|
| `BTRA_0001` | Amount is below minimum ($1.00) | Set `total` to at least "1.00" |
| `BTRA_0004` | Amount exceeds maximum ($1,500.00) | Set `total` to maximum "1500.00" or split payment |
| `BTRA_0006` | Invalid format or required body missing | Check all required fields are provided |
| `BTRA_0013` | Amount cannot be zero | Set `total` to a positive value |
| `BTRA_0038` | Metadata exceeds 40 characters | Truncate `metadata1` or `metadata2` to 40 chars |
| `BTRA_0040` | Message exceeds 50 characters | Truncate refund message to 50 chars |

**Recovery Strategy:**
```python
from athm._utils import truncate_string, format_amount

try:
    payment = client.create_payment(
        total="50.00",
        phone_number="7875551234",
        subtotal="50.00",
        tax="0.00",
        metadata1=order_id  # Might be too long
    )
except ValidationError as e:
    if "BTRA_0038" in str(e):
        # Metadata too long, truncate and retry
        payment = client.create_payment(
            total="50.00",
            phone_number="7875551234",
            subtotal="50.00",
            tax="0.00",
            metadata1=truncate_string(order_id, 40)
        )
    elif "BTRA_0004" in str(e):
        # Amount too high
        print("Payment exceeds $1500 limit, please split")
        raise
    else:
        raise
```

### Transaction Errors

Payment state and lifecycle errors.

| Error Code | Description | Solution |
|------------|-------------|----------|
| `BTRA_0007` | Transaction ID does not exist | Check `ecommerce_id` is correct |
| `BTRA_0031` | Ecommerce ID does not exist | Verify payment was created successfully |
| `BTRA_0032` | Transaction status is not confirmed | Wait for customer to confirm before authorizing |
| `BTRA_0037` | Cannot confirm cancelled or failed transaction | Payment was cancelled, create new one |
| `BTRA_0039` | Transaction timeout has expired | Payment expired, create new one |

**Recovery Strategy:**
```python
try:
    result = client.authorize_payment(ecommerce_id)
except TransactionError as e:
    if "BTRA_0032" in str(e):
        # Not confirmed yet, wait longer
        print("Waiting for customer confirmation...")
        confirmed = client.wait_for_confirmation(ecommerce_id)
        result = client.authorize_payment(ecommerce_id)

    elif "BTRA_0037" in str(e) or "BTRA_0039" in str(e):
        # Cancelled or expired, restart
        print("Payment cancelled/expired, creating new one")
        new_payment = client.create_payment(...)
        return new_payment

    elif "BTRA_0031" in str(e):
        # ID doesn't exist - payment creation failed
        log_error(f"Invalid ecommerce_id: {ecommerce_id}")
        raise

    else:
        raise
```

### Business Errors

Business account configuration issues.

| Error Code | Description | Solution |
|------------|-------------|----------|
| `BTRA_0003` | Customer card cannot be same as business card | Customer must use different payment method |
| `BTRA_0009` | Business is not active | Contact ATH Business support |
| `BTRA_0010` | Business is not active | Contact ATH Business support |

**Recovery Strategy:**
```python
try:
    payment = client.create_payment(...)
except ATHMovilError as e:
    if "BTRA_0003" in str(e):
        # Customer using same card as merchant
        return "Cannot use same card for payment, please use different account"

    elif "BTRA_0009" in str(e) or "BTRA_0010" in str(e):
        # Business account inactive
        notify_admin("ATH Business account is inactive")
        raise

    else:
        raise
```

### Network Errors

Connection and communication issues.

| Error Code | Description | Solution |
|------------|-------------|----------|
| `BTRA_9998` | Communication error with ATH Móvil services | Retry request, check network connectivity |

**Recovery Strategy:**
```python
import time

max_retries = 3
for attempt in range(max_retries):
    try:
        payment = client.create_payment(...)
        break
    except NetworkError as e:
        if attempt < max_retries - 1:
            wait = 2 ** attempt  # Exponential backoff
            print(f"Network error, retrying in {wait}s...")
            time.sleep(wait)
        else:
            print("Network error persists after retries")
            raise
```

### Internal Server Errors

ATH Móvil server issues.

| Error Code | Description | Solution |
|------------|-------------|----------|
| `BTRA_9999` | Internal server error | Wait and retry, contact ATH support if persists |

**Recovery Strategy:**
```python
try:
    payment = client.create_payment(...)
except InternalServerError as e:
    # ATH Móvil server issue, retry with backoff
    print("Server error, will retry shortly")
    time.sleep(5)
    payment = client.create_payment(...)  # Retry once
```

## Complete Error Handling Pattern

Here's a production-ready error handling pattern:

```python
from athm import (
    ATHMovilClient,
    AuthenticationError,
    ValidationError,
    TransactionError,
    PaymentError,
    RefundError,
    TimeoutError,
    NetworkError,
    InternalServerError,
    ATHMovilError
)
import time
from typing import Optional


def create_payment_with_retry(
    client: ATHMovilClient,
    amount: str,
    phone: str,
    max_retries: int = 3
) -> Optional[str]:
    """
    Create payment with comprehensive error handling.

    Returns ecommerce_id on success, None on unrecoverable error.
    """
    for attempt in range(max_retries):
        try:
            payment = client.create_payment(
                total=amount,
                phone_number=phone,
                subtotal=amount,
                tax="0.00"
            )
            return payment.ecommerce_id

        except ValidationError as e:
            # Invalid data - don't retry, fix input
            print(f"Validation error: {e}")
            if "BTRA_0001" in str(e):
                print("Amount too low (min $1.00)")
            elif "BTRA_0004" in str(e):
                print("Amount too high (max $1500.00)")
            elif "BTRA_0038" in str(e):
                print("Metadata too long (max 40 chars)")
            return None

        except AuthenticationError as e:
            # Invalid token - don't retry, need new token
            print(f"Authentication error: {e}")
            print("Check your PUBLIC_TOKEN configuration")
            return None

        except NetworkError as e:
            # Network issue - retry with backoff
            if attempt < max_retries - 1:
                wait = 2 ** attempt
                print(f"Network error, retry {attempt + 1}/{max_retries} in {wait}s")
                time.sleep(wait)
                continue
            print("Network error persists, giving up")
            return None

        except InternalServerError as e:
            # Server error - retry with backoff
            if attempt < max_retries - 1:
                wait = 5
                print(f"Server error, retry {attempt + 1}/{max_retries} in {wait}s")
                time.sleep(wait)
                continue
            print("Server error persists, giving up")
            return None

        except TimeoutError as e:
            # Timeout - retry
            if attempt < max_retries - 1:
                print(f"Timeout, retry {attempt + 1}/{max_retries}")
                continue
            print("Timeout persists, giving up")
            return None

        except ATHMovilError as e:
            # Other errors
            print(f"ATH Móvil error: {e}")
            print(f"Error code: {e.error_code}")
            return None

    return None


def complete_payment_flow(
    client: ATHMovilClient,
    amount: str,
    phone: str
) -> Optional[str]:
    """
    Complete payment flow with error handling.

    Returns reference_number on success.
    """
    # 1. Create payment
    ecommerce_id = create_payment_with_retry(client, amount, phone)
    if not ecommerce_id:
        return None

    try:
        # 2. Wait for confirmation
        try:
            client.wait_for_confirmation(
                ecommerce_id,
                polling_interval=2.0,
                max_attempts=150  # 5 minutes
            )
        except TimeoutError:
            print("Customer didn't confirm, cancelling")
            client.cancel_payment(ecommerce_id)
            return None

        # 3. Authorize payment
        try:
            result = client.authorize_payment(ecommerce_id)
            return result.data.reference_number

        except TransactionError as e:
            if "BTRA_0032" in str(e):
                # Still not confirmed, wait more
                print("Still waiting for confirmation...")
                time.sleep(5)
                result = client.authorize_payment(ecommerce_id)
                return result.data.reference_number
            else:
                print(f"Transaction error: {e}")
                return None

    except Exception as e:
        # Unexpected error, try to clean up
        print(f"Unexpected error: {e}")
        try:
            client.cancel_payment(ecommerce_id)
        except:
            pass  # Best effort cleanup
        return None


# Usage
if __name__ == "__main__":
    client = ATHMovilClient(public_token="...")

    try:
        ref = complete_payment_flow(
            client,
            amount="25.00",
            phone="7875551234"
        )

        if ref:
            print(f"Payment successful: {ref}")
        else:
            print("Payment failed")

    finally:
        client.close()
```

## Logging Errors

### Safe Logging Pattern

Never log sensitive data (tokens, full phone numbers):

```python
from athm import ATHMovilClient, ATHMovilError
from athm._utils import mask_sensitive_data
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = ATHMovilClient(public_token="...")

try:
    payment = client.create_payment(
        total="50.00",
        phone_number="7875551234",
        subtotal="50.00",
        tax="0.00"
    )
    logger.info(f"Payment created: {payment.ecommerce_id}")

except ATHMovilError as e:
    # Log error safely
    logger.error(
        "Payment creation failed",
        extra={
            "error_code": e.error_code,
            "status_code": e.status_code,
            "error_message": str(e),
            # Don't log full response, may contain sensitive data
        }
    )
```

### Structured Logging

```python
import structlog

logger = structlog.get_logger()

try:
    payment = client.create_payment(...)
    logger.info(
        "payment_created",
        ecommerce_id=payment.ecommerce_id,
        amount="50.00"
    )
except ATHMovilError as e:
    logger.error(
        "payment_creation_failed",
        error_code=e.error_code,
        error_type=type(e).__name__,
        retryable=isinstance(e, (NetworkError, InternalServerError, TimeoutError))
    )
```

## Testing Error Scenarios

### Mock Errors for Testing

```python
from unittest.mock import Mock, patch
from athm import ATHMovilClient, ValidationError

def test_amount_too_high():
    client = ATHMovilClient(public_token="test")

    with patch.object(client, '_make_request') as mock_request:
        # Mock API error response
        mock_request.side_effect = ValidationError(
            "Amount exceeds maximum limit",
            error_code="BTRA_0004",
            status_code=400
        )

        with pytest.raises(ValidationError) as exc_info:
            client.create_payment(
                total="2000.00",  # Over limit
                phone_number="7875551234",
                subtotal="2000.00",
                tax="0.00"
            )

        assert exc_info.value.error_code == "BTRA_0004"
```

## Common Scenarios

### Scenario: Amount Validation

```python
from decimal import Decimal

def validate_amount(amount: str) -> str:
    """Validate and format amount before payment."""
    decimal_amount = Decimal(amount)

    if decimal_amount < Decimal("1.00"):
        raise ValueError("Amount must be at least $1.00")
    elif decimal_amount > Decimal("1500.00"):
        raise ValueError("Amount cannot exceed $1,500.00")

    # Format to 2 decimals
    return f"{decimal_amount:.2f}"

# Usage
try:
    validated = validate_amount("50")  # "50.00"
    payment = client.create_payment(
        total=validated,
        ...
    )
except ValueError as e:
    print(f"Invalid amount: {e}")
```

### Scenario: Polling Timeout

```python
# Set reasonable timeout based on use case
try:
    # Quick checkout: 2 minute timeout
    result = client.wait_for_confirmation(
        ecommerce_id,
        max_attempts=60  # 60 * 2s = 2 min
    )

except TimeoutError:
    # Graceful handling
    print("Payment timed out, sending reminder...")
    send_sms_reminder(phone_number)

    # Extended wait
    try:
        result = client.wait_for_confirmation(
            ecommerce_id,
            max_attempts=150  # Extra 5 minutes
        )
    except TimeoutError:
        # Give up
        client.cancel_payment(ecommerce_id)
```

### Scenario: Refund Errors

```python
from athm import RefundError

try:
    refund = client.refund_payment(
        reference_number="123456",
        amount="50.00",
        message="Refund for order #123"
    )
except RefundError as e:
    if "not found" in str(e).lower():
        print("Invalid reference number")
    elif "already refunded" in str(e).lower():
        print("Payment was already refunded")
    else:
        print(f"Refund failed: {e}")
```

## Next Steps

- **[API Reference](api-reference.md)** - Full method documentation
- **[Payment Flow Guide](guide.md)** - Complete payment walkthrough
- **[Advanced Usage](advanced.md)** - Refunds, testing, production patterns

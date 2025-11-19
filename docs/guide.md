# Payment Flow Guide

This guide walks through a complete ATH Móvil payment from creation to completion.

## Payment Lifecycle

ATH Móvil payments follow a state-based lifecycle with the following states:

### Payment States

| State | Description | Next Actions |
|-------|-------------|--------------|
| **OPEN** | Payment created, waiting for customer | Wait for confirmation or cancel |
| **CONFIRM** | Customer confirmed on ATH Móvil app | Authorize to complete |
| **COMPLETED** | Payment authorized and finalized | Can refund if needed |
| **CANCEL** | Payment cancelled or timed out | Cannot recover, create new payment |

## Payment Flow

The payment process follows these steps:

1. **Create payment** - Your app calls `create_payment()` and receives an `ecommerce_id`
2. **Push notification** - ATH Móvil sends notification to customer's phone
3. **Customer approval** - Customer opens ATH Móvil app and approves payment
4. **Poll for confirmation** - Your app polls for status change to `CONFIRM`
5. **Authorize payment** - Your app calls `authorize_payment()` to complete the transaction
6. **Completion** - Payment status changes to `COMPLETED` and you receive a `reference_number`

## Step-by-Step Implementation

### Step 1: Create the Payment

Initialize the client and create a payment:

```python
from athm import ATHMovilClient
import os

client = ATHMovilClient(public_token=os.getenv("ATHM_PUBLIC_TOKEN"))

# Create payment
payment = client.create_payment(
    total="50.00",
    phone_number="7875551234",  # Customer's phone
    subtotal="45.00",
    tax="5.00",
    metadata1="Order #12345",  # Optional: your reference
    metadata2="2 items",        # Optional: extra info
    items=[{
        "name": "Product Name",
        "description": "Product description",
        "quantity": "1",
        "price": "45.00",
        "tax": "5.00"
    }]
)

print(f"Payment created: {payment.ecommerce_id}")
print("Customer will receive a push notification")
```

**What happens:**
- Payment is created with `OPEN` status
- Customer receives push notification on their phone
- You get an `ecommerce_id` to track this payment

### Step 2: Wait for Customer Confirmation

The customer needs to open their ATH Móvil app and approve the payment:

```python
# Option 1: Automatic polling (recommended)
try:
    confirmed = client.wait_for_confirmation(
        payment.ecommerce_id,
        polling_interval=2.0,  # Check every 2 seconds
        max_attempts=150       # 5 minutes max (150 * 2s)
    )
    print("Customer confirmed!")
except TimeoutError:
    print("Customer didn't confirm in time")
    client.cancel_payment(payment.ecommerce_id)
```

```python
# Option 2: Manual status checking
import time

max_wait = 300  # 5 minutes
elapsed = 0

while elapsed < max_wait:
    status = client.find_payment(payment.ecommerce_id)

    if status.data.status == "CONFIRM":
        print("Customer confirmed!")
        break
    elif status.data.status == "CANCEL":
        print("Payment was cancelled")
        break

    time.sleep(2)
    elapsed += 2
else:
    print("Timeout waiting for confirmation")
```

**What happens:**
- Your app polls ATH Móvil API every 2 seconds
- Customer sees the payment request in their app
- Customer approves or rejects
- Status changes to `CONFIRM` when approved

!!! tip "Polling Best Practices"
    - Use 2-second intervals (don't poll too frequently)
    - Set reasonable timeout (5-10 minutes typical)
    - Always cancel on timeout to clean up

### Step 3: Authorize the Payment

Once confirmed, you must authorize to finalize:

```python
# Authorize completes the payment
result = client.authorize_payment(payment.ecommerce_id)

print(f"Payment completed!")
print(f"Reference number: {result.data.reference_number}")
print(f"Total: ${result.data.total}")
print(f"Status: {result.data.status}")  # "COMPLETED"
```

**What happens:**
- Payment is finalized and funds are transferred
- You receive a `reference_number` for your records
- Status changes to `COMPLETED`
- Customer receives confirmation

!!! warning "Must Authorize Within 10 Minutes"
    After customer confirms, you have ~10 minutes to authorize before the payment expires.

### Step 4: Error Handling

Always handle errors gracefully:

```python
from athm import (
    ATHMovilClient,
    AuthenticationError,
    ValidationError,
    TransactionError,
    TimeoutError
)

try:
    # Create payment
    payment = client.create_payment(
        total="50.00",
        phone_number="7875551234",
        subtotal="50.00",
        tax="0.00"
    )

    # Wait for confirmation
    try:
        confirmed = client.wait_for_confirmation(
            payment.ecommerce_id,
            max_attempts=150
        )
    except TimeoutError:
        # Customer didn't confirm, clean up
        client.cancel_payment(payment.ecommerce_id)
        print("Payment cancelled due to timeout")
        return

    # Authorize
    result = client.authorize_payment(payment.ecommerce_id)
    print(f"Success! Reference: {result.data.reference_number}")

except ValidationError as e:
    print(f"Invalid data: {e}")
except AuthenticationError as e:
    print(f"Authentication failed: {e}")
except TransactionError as e:
    print(f"Transaction error: {e}")
finally:
    client.close()
```

## Complete Example

Here's a full production-ready payment flow:

```python
from athm import ATHMovilClient, TimeoutError, TransactionError
import os

def process_payment(amount: str, phone: str, order_id: str) -> str | None:
    """
    Process an ATH Móvil payment.

    Returns reference_number on success, None on failure.
    """
    client = ATHMovilClient(public_token=os.getenv("ATHM_PUBLIC_TOKEN"))

    try:
        # 1. Create payment
        payment = client.create_payment(
            total=amount,
            phone_number=phone,
            subtotal=amount,
            tax="0.00",
            metadata1=f"Order {order_id}"
        )

        print(f"Payment created: {payment.ecommerce_id}")
        print(f"Waiting for customer {phone} to confirm...")

        # 2. Wait for customer confirmation (5 minute timeout)
        try:
            client.wait_for_confirmation(
                payment.ecommerce_id,
                polling_interval=2.0,
                max_attempts=150  # 5 minutes
            )
        except TimeoutError:
            print("Customer didn't confirm in time, cancelling...")
            client.cancel_payment(payment.ecommerce_id)
            return None

        # 3. Authorize payment
        result = client.authorize_payment(payment.ecommerce_id)

        print(f"Payment completed!")
        print(f"  Reference: {result.data.reference_number}")
        print(f"  Amount: ${result.data.total}")

        return result.data.reference_number

    except TransactionError as e:
        print(f"Transaction failed: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None
    finally:
        client.close()

# Usage
if __name__ == "__main__":
    ref = process_payment(
        amount="25.50",
        phone="7875551234",
        order_id="ORD-12345"
    )

    if ref:
        print(f"Save this reference: {ref}")
    else:
        print("Payment failed")
```

## Convenience Method

For simple cases, use `process_complete_payment()` which combines all steps:

```python
from athm import ATHMovilClient

client = ATHMovilClient(public_token=os.getenv("ATHM_PUBLIC_TOKEN"))

try:
    # Does create + wait + authorize in one call
    result = client.process_complete_payment(
        total="50.00",
        phone_number="7875551234",
        subtotal="50.00",
        tax="0.00",
        polling_interval=2.0,
        max_wait_time=300.0  # 5 minutes
    )

    print(f"Complete! Reference: {result.data.reference_number}")

except Exception as e:
    print(f"Payment failed: {e}")
finally:
    client.close()
```

!!! tip "When to Use process_complete_payment()"
    - **Use it for**: Simple flows, CLI tools, scripts
    - **Avoid it for**: Web apps (blocks thread), complex error handling, custom UX

## Phone Number Confirmation

ATH Móvil sends push notifications to the customer's phone. The phone number must:

- Be 10 digits
- Be registered with ATH Móvil
- Match the customer's ATH Móvil account

### Update Phone Number

If the customer provides a different phone number:

```python
# After payment creation, before confirmation
client.update_phone_number(
    ecommerce_id=payment.ecommerce_id,
    phone_number="7875559999"
)

# Now wait for confirmation on the new number
client.wait_for_confirmation(payment.ecommerce_id)
```

## Common Patterns

### Pattern: Webhook Alternative

If you don't want to poll, implement a customer redirect:

```python
# 1. Create payment
payment = client.create_payment(...)

# 2. Show customer a page with payment.ecommerce_id
#    Customer opens ATH Móvil app and confirms

# 3. Customer returns to your site, you check status
status = client.find_payment(payment.ecommerce_id)

if status.data.status == "CONFIRM":
    # Authorize it
    result = client.authorize_payment(payment.ecommerce_id)
```

### Pattern: Background Job

For async frameworks:

```python
# In request handler
payment = client.create_payment(...)
enqueue_job("check_payment", payment.ecommerce_id)
return {"payment_id": payment.ecommerce_id}

# In background worker
def check_payment(ecommerce_id):
    result = client.wait_for_confirmation(ecommerce_id)
    client.authorize_payment(ecommerce_id)
    # Update your database, send email, etc.
```

## Next Steps

- **[API Reference](api-reference.md)** - Detailed method documentation
- **[Error Handling](errors.md)** - All error codes and recovery
- **[Advanced Usage](advanced.md)** - Refunds, testing, customization

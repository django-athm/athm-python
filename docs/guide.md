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
    total="5.00",
    phone_number="7875551234",  # Customer's phone
    metadata1="Order #12345",  # Optional: your reference
    items=[{
        "name": "Product Name",
        "description": "Product description",
        "quantity": "1",
        "price": "5.00",
    }]
)

print(f"Payment created: {payment.data.ecommerce_id}")
print("Customer will receive a push notification")
```

**What happens:**

- Payment is created with `OPEN` status
- Customer receives push notification on their phone
- You get an `ecommerce_id` to track this payment

### Step 2: Wait for Customer Confirmation

The customer needs to open their ATH Móvil app and approve the payment:

```python
try:
    client.wait_for_confirmation(payment.data.ecommerce_id, timeout=300)
    print("Customer confirmed!")
except TimeoutError:
    print("Timeout - cancelling payment")
    client.cancel_payment(payment.data.ecommerce_id)
except TransactionError:
    print("Payment was cancelled")
```

**What happens:**

- Customer receives push notification on their phone
- Your app polls ATH Móvil API every 2 seconds
- Customer opens app and approves or rejects
- Status changes to `CONFIRM` when approved

### Step 3: Authorize the Payment

Once confirmed, authorize within 10 minutes to finalize:

```python
result = client.authorize_payment(payment.data.ecommerce_id)

print(f"Payment completed!")
print(f"Reference number: {result.data.reference_number}")
print(f"Total: ${result.data.total}")
print(f"Status: {result.data.ecommerce_status}")  # "COMPLETED"
```

**What happens:**

- Payment is finalized and funds are transferred
- You receive a `reference_number` for your records
- Status changes to `COMPLETED`
- Customer receives confirmation

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
        total="5.00",
        phone_number="7875551234",
        items=[{
            "name": "Product Name",
            "description": "Product Description",
            "quantity": "1",
            "price": "5.00",
        }],
    )

    # Wait for confirmation
    client.wait_for_confirmation(payment.data.ecommerce_id)

    # Authorize
    result = client.authorize_payment(payment.data.ecommerce_id)
    print(f"Success! Reference: {result.data.reference_number}")

except ValidationError as e:
    print(f"Invalid data: {e}")
except AuthenticationError as e:
    print(f"Authentication failed: {e}")
except TimeoutError as e:
    print(f"Payment timed out: {e}")
    client.cancel_payment(payment.data.ecommerce_id)
except TransactionError as e:
    print(f"Transaction error: {e}")
finally:
    client.close()
```

## Complete Example

Here's a full production-ready payment flow:

```python
from athm import ATHMovilClient, TransactionError, TimeoutError
import os

def process_payment(amount: str, phone_number: str, order_id: str) -> str | None:
    """Process an ATH Móvil payment. Returns reference_number on success."""
    client = ATHMovilClient(public_token=os.getenv("ATHM_PUBLIC_TOKEN"))

    try:
        # 1. Create payment
        payment = client.create_payment(
            total=amount,
            phone_number=phone_number,
            metadata1=f"Order {order_id}",
            items=[{
                "name": "Order Item",
                "description": f"Order {order_id}",
                "quantity": "1",
                "price": amount,
            }],
        )

        print(f"Payment created: {payment.data.ecommerce_id}")
        print(f"Waiting for customer {phone_number} to confirm...")

        # 2. Wait for confirmation
        client.wait_for_confirmation(payment.data.ecommerce_id, timeout=300)

        # 3. Authorize payment
        result = client.authorize_payment(payment.data.ecommerce_id)

        print(f"Payment completed!")
        print(f"  Reference: {result.data.reference_number}")
        print(f"  Amount: ${result.data.total}")

        return result.data.reference_number

    except TimeoutError:
        print("Customer didn't confirm in time, cancelling...")
        client.cancel_payment(payment.data.ecommerce_id)
        return None
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
        amount="5.00",
        phone_number="7875551234",
        order_id="ORD-12345"
    )

    if ref:
        print(f"Save this reference: {ref}")
    else:
        print("Payment failed")
```

### Update Phone Number

If the customer provides a different phone number:

```python
# After payment creation, before confirmation
client.update_phone_number(
    ecommerce_id=payment.data.ecommerce_id,
    phone_number="7875559999"
)

# Wait for confirmation on the new number
client.wait_for_confirmation(payment.data.ecommerce_id)
```

## Webhooks

Webhooks provide real-time notifications when transactions occur. Instead of polling for status changes, ATH Movil will POST to your endpoint.

### Subscribing to Webhooks

Register your HTTPS endpoint to receive webhook notifications:

```python
from athm import ATHMovilClient
import os

# Private token is required for webhook subscriptions
client = ATHMovilClient(
    public_token=os.getenv("ATHM_PUBLIC_TOKEN"),
    private_token=os.getenv("ATHM_PRIVATE_TOKEN"),
)

# Subscribe to webhook events
client.subscribe_webhook(
    listener_url="https://yoursite.com/webhooks/athm",
    payment_received=True,
    refund_sent=True,
    ecommerce_completed=True,
    ecommerce_cancelled=True,
    ecommerce_expired=True,
)
```

**Requirements:**

- Listener URL must use HTTPS (no self-signed certificates)
- Private token is required for subscription

### Handling Webhook Events

When ATH Movil sends a webhook to your endpoint, use `parse_webhook()` to validate and normalize the payload:

```python
from athm import parse_webhook, WebhookEventType, WebhookStatus, ValidationError

# In your web framework (FastAPI, Flask, Django, etc.)
@app.post("/webhooks/athm")
async def handle_athm_webhook(request: Request):
    try:
        payload = await request.json()
        event = parse_webhook(payload)

        match event.transaction_type:
            case WebhookEventType.PAYMENT:
                print(f"Payment received: ${event.total} from {event.name}")
                print(f"Reference: {event.reference_number}")

            case WebhookEventType.REFUND:
                print(f"Refund sent: ${event.total}")

            case WebhookEventType.ECOMMERCE:
                if event.status == WebhookStatus.COMPLETED:
                    print(f"eCommerce order {event.ecommerce_id} completed")
                elif event.status == WebhookStatus.CANCELLED:
                    print(f"eCommerce order {event.ecommerce_id} cancelled")
                elif event.status == WebhookStatus.EXPIRED:
                    print(f"eCommerce order {event.ecommerce_id} expired")

            case WebhookEventType.DONATION:
                print(f"Donation received: ${event.total}")

        return {"status": "ok"}

    except ValidationError as e:
        print(f"Invalid webhook payload: {e}")
        return {"status": "error"}, 400
```

### Webhook Event Types

| Event Type | Description |
|------------|-------------|
| `SIMULATED` | Test/simulated payment (sandbox) |
| `PAYMENT` | Standard payment received |
| `DONATION` | Donation received |
| `REFUND` | Refund sent to customer |
| `ECOMMERCE` | eCommerce transaction (check `status` for completed/cancelled/expired) |

### Webhook Payload Normalization

The `parse_webhook()` function automatically normalizes inconsistencies in the ATH Movil webhook API:

- **Field names**: `dailyTransactionID` vs `dailyTransactionId` -> `daily_transaction_id`
- **Data types**: String decimals (`"100.00"`) and numbers (`100.00`) -> `Decimal`
- **Status values**: `CANCEL` -> `cancelled`, `COMPLETED` -> `completed`
- **Transaction types**: `ECOMMERCE` -> `ecommerce`

This means you always get consistent, typed data regardless of which event type you receive.

## Next Steps

- **[API Reference](api-reference.md)** - Detailed method documentation
- **[Error Handling](errors.md)** - All error codes and recovery

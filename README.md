# ATH Móvil Unofficial Python Library

![PyPI - Version](https://img.shields.io/pypi/v/athm)
[![Python Versions](https://img.shields.io/pypi/pyversions/athm.svg)](https://pypi.org/project/athm/)
[![codecov](https://codecov.io/gh/django-athm/athm-python/graph/badge.svg?token=97F3WYLT3M)](https://codecov.io/gh/django-athm/athm-python)
[![Read the Docs](https://img.shields.io/readthedocs/athm-python)](https://athm-python.readthedocs.io/en/latest/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/django-athm/athm-python/actions/workflows/test.yml/badge.svg)](https://github.com/django-athm/athm-python/actions/workflows/test.yml)

A modern, type-safe Python library for the ATH Móvil payment platform.

> **Note**: This is an unofficial, third-party library and is not affiliated with, endorsed by, or supported by ATH Móvil or EVERTEC. For official API documentation, see the [ATH Móvil Payment Button API](https://github.com/evertec/ATHM-Payment-Button-API).

> Developed with AI assistance using Claude Code (claude.ai)

## Features

- Full ATH Móvil Payment Button API support
- Webhook support for real-time transaction notifications
- Simple synchronous client
- Strict type safety with mypy
- Pydantic data validation
- Automatic retries with exponential backoff
- Comprehensive error handling

## Installation

```bash
pip install athm
```

Or with uv:

```bash
uv add athm
```

## Quick Start

```python
from athm import ATHMovilClient

# Note: private token is only required for processing refunds
client = ATHMovilClient(public_token="your_public_token", private_token="your_private_token")

payment = client.create_payment(
    total="5.00",
    phone_number="7875551234",
    metadata1="Order #123",
    items=[
        {
            "name": "Product Name",
            "description": "Product Description",
            "quantity": "1",
            "price": "5.00",
        }
    ],
)

# Wait for customer confirmation
client.wait_for_confirmation(payment.data.ecommerce_id)

# Authorize payment
payment_result = client.authorize_payment(payment.data.ecommerce_id)
print(f"Payment completed: {payment_result.data.reference_number}")

# Refund the payment (requires a client initialized with private token)
refund_result = client.refund_payment(
    reference_number=payment_result.data.reference_number,
    amount="5.00",
)
```

## Configuration

Get your credentials from your ATH Business account settings.

```python
client = ATHMovilClient(
    public_token=os.getenv("ATHM_PUBLIC_TOKEN"),
    private_token=os.getenv("ATHM_PRIVATE_TOKEN"),  # Required for refunds
)
```

## Supported Operations

- Create payments
- Check payment status
- Authorize confirmed payments
- Cancel payments
- Process full and partial refunds
- Update phone numbers
- Subscribe to webhook notifications
- Parse and validate webhook payloads

## Error Handling

```python
from athm.exceptions import ValidationError, ATHMovilError

try:
    payment = client.create_payment(
        total="5.00",
        phone_number="7875551234",  # Customer's phone number with ATH Móvil account
        items=[{"name": "Test", "description": "Test", "quantity": "1", "price": "5.00"}],
    )
except ValidationError as e:
    print(f"Invalid data: {e}")
except ATHMovilError as e:
    print(f"Error: {e}")
```

## Context Manager

```python
with ATHMovilClient(public_token="token") as client:
    payment = client.create_payment(
        total="5.00",
        phone_number="7875551234",  # Customer's phone number with ATH Móvil account
        items=[{"name": "Test", "description": "Test", "quantity": "1", "price": "5.00"}],
    )
    # Client is automatically closed when exiting the context
```

## Webhooks

Subscribe to real-time transaction notifications:

```python
# Subscribe to webhooks (requires private token)
client = ATHMovilClient(
    public_token="your_public_token",
    private_token="your_private_token",
)

client.subscribe_webhook(
    listener_url="https://yoursite.com/webhook",
    payment_received_event=True,
    refund_sent_event=True,
    ecommerce_payment_received_event=True,
    ecommerce_payment_cancelled_event=True,
    ecommerce_payment_expired_event=True,
)
```

Parse incoming webhook payloads in your endpoint:

```python
from athm.webhooks import parse_webhook, WebhookEventType, WebhookStatus

@app.post("/webhook")
async def handle_webhook(request: Request):
    payload = await request.json()
    event = parse_webhook(payload)

    if event.status == WebhookStatus.COMPLETED:
        if event.transaction_type == WebhookEventType.PAYMENT:
            # Standard payment completed
            print(f"Payment received: {event.reference_number} for ${event.total}")
        elif event.transaction_type == WebhookEventType.ECOMMERCE:
            # eCommerce payment completed
            print(f"Order {event.ecommerce_id} completed: ${event.total}")
        elif event.transaction_type == WebhookEventType.REFUND:
            # Refund processed
            print(f"Refund sent: {event.reference_number}")

    elif event.status == WebhookStatus.CANCELLED:
        print(f"Transaction cancelled: {event.ecommerce_id}")

    elif event.status == WebhookStatus.EXPIRED:
        print(f"Transaction expired: {event.ecommerce_id}")

    return {"status": "ok"}
```

## Documentation

- [Full Documentation](https://athm-python.readthedocs.io)
- [API Reference](https://athm-python.readthedocs.io/en/latest/api-reference/)

## Development

```bash
git clone https://github.com/django-athm/athm-python.git
cd athm-python
uv sync --all-extras --dev
uv run pytest
```

### Code Quality

```bash
uv run ruff format
uv run ruff check
uv run mypy athm
```

## Requirements

- Python 3.10+
- httpx
- pydantic

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

MIT License - see [LICENSE](LICENSE) for details.

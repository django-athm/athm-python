# ATH Móvil Unofficial Library

A modern, type-safe Python library for integrating ATH Móvil payments into your application.

ATH Móvil is Puerto Rico's leading mobile payment platform. This library provides a simple, Pythonic interface to create payments, check status, and process refunds.

!!! warning "Third-Party Library"
    This is an unofficial, third-party library and is not affiliated with, endorsed by, or supported by ATH Móvil or EVERTEC. For official API documentation, see the [ATH Móvil Payment Button API](https://github.com/evertec/ATHM-Payment-Button-API).

## Quick Start

### Installation

```bash
pip install athm
```

### Example

```python
from athm import ATHMovilClient

# Initialize client
client = ATHMovilClient(public_token="YOUR_PUBLIC_TOKEN")

# Create payment
payment = client.create_payment(
    total="5.00",
    phone_number="7875551234",  # Customer's phone number with ATH Móvil account
    items=[
        {
            "name": "Product Name",
            "description": "Product Description",
            "quantity": "1",
            "price": "5.00",
        }
    ],
)

# Wait for customer to confirm on their phone
confirmed = client.wait_for_confirmation(payment.ecommerce_id)

# Authorize the payment
result = client.authorize_payment(payment.ecommerce_id)
print(f"Payment completed! Reference: {result.data.reference_number}")
```

## Features

- **Type-safe**: Full type hints and Pydantic validation
- **Simple API**: Pythonic interface, sensible defaults
- **Automatic retries**: Built-in exponential backoff
- **Comprehensive errors**: Specific exceptions for each error type
- **Well-tested**: Comprehensive test suite with high coverage

## Next Steps

- **[Installation Guide](installation.md)** - Get your tokens and set up
- **[Payment Flow Guide](guide.md)** - Complete walkthrough with diagrams
- **[API Reference](api-reference.md)** - Client methods and models
- **[Error Handling](errors.md)** - All error codes and solutions
- **[Advanced Usage](advanced.md)** - Refunds, testing, and customization

## Requirements

- Python 3.10+
- ATH Business account with API credentials

## Links

- [GitHub Repository](https://github.com/django-athm/athm-python)
- [Official ATH Móvil API](https://github.com/evertec/ATHM-Payment-Button-API)
- [PyPI Package](https://pypi.org/project/athm/)

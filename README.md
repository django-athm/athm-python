# ATH Móvil Python Library

[![PyPI version](https://badge.fury.io/py/athm.svg)](https://badge.fury.io/py/athm)
[![Python Versions](https://img.shields.io/pypi/pyversions/athm.svg)](https://pypi.org/project/athm/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/yourusername/athm-python/actions/workflows/test.yml/badge.svg)](https://github.com/yourusername/athm-python/actions/workflows/test.yml)

A modern, type-safe Python library for the ATH Móvil payment platform.

> **Note**: This is an unofficial, third-party library and is not affiliated with, endorsed by, or supported by ATH Móvil or EVERTEC. For official API documentation, see the [ATH Móvil Payment Button API](https://github.com/evertec/ATHM-Payment-Button-API).

## Features

- Full ATH Móvil Payment Button API support
- Simple synchronous client
- Strict type safety with mypy
- Pydantic data validation
- Automatic retries with exponential backoff
- Comprehensive error handling
- High test coverage

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

client = ATHMovilClient(public_token="your_public_token")

payment = client.create_payment(
    total="100.00",
    phone_number="7875551234",  # Customer's phone number with ATH Móvil account
    metadata1="Order #123",
    items=[
        {
            "name": "Product Name",
            "description": "Product Description",
            "quantity": "1",
            "price": "100.00",
        }
    ],
)

confirmed = client.wait_for_confirmation(payment.data.ecommerce_id)

if confirmed:
    result = client.authorize_payment(payment.data.ecommerce_id)
    print(f"Payment completed: {result.data.reference_number}")
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
- Update phone numbers
- Cancel payments
- Process full and partial refunds

## Error Handling

```python
from athm.exceptions import ValidationError, ATHMovilError

try:
    payment = client.create_payment(
        total="0.50",  # Below minimum - will raise ValidationError
        phone_number="7875551234",  # Customer's phone number with ATH Móvil account
        items=[{"name": "Test", "description": "Test", "quantity": "1", "price": "0.50"}],
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
        total="100.00",
        phone_number="7875551234",  # Customer's phone number with ATH Móvil account
        items=[{"name": "Test", "description": "Test", "quantity": "1", "price": "100.00"}],
    )
    # Client is automatically closed when exiting the context
```

## Documentation

- [Full Documentation](https://athm-python.readthedocs.io)
- [API Reference](https://athm-python.readthedocs.io/en/latest/api/)

## Development

```bash
git clone https://github.com/yourusername/athm-python.git
cd athm-python
uv sync --all-extras --dev
uv run pytest
```

### Code Quality

```bash
uv run ruff format athm tests
uv run ruff check athm tests --fix
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

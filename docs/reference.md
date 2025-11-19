# Official API Reference

This page explains the relationship between this Python library and the official ATH Móvil API.

## Official ATH Móvil API Documentation

The authoritative source for ATH Móvil API specifications:

**[ATH Móvil Payment Button API](https://github.com/evertec/ATHM-Payment-Button-API)**

This repository, maintained by EVERTEC (ATH Móvil's parent company), contains:

- Complete REST API specifications
- Payment button integration guides
- Web and mobile integration examples
- Official error code documentation
- API endpoint details
- Authentication specifications

## This Library vs. Official API

### What This Library Provides

The `athm` Python library is a **wrapper** around the official ATH Móvil REST API that provides:

- **Pythonic interface**: Use native Python objects instead of raw HTTP requests
- **Type safety**: Pydantic models with automatic validation
- **Error handling**: Specific Python exceptions mapped to API error codes
- **Automatic retries**: Built-in exponential backoff for transient failures
- **Convenience methods**: High-level operations like `wait_for_confirmation()` and `process_complete_payment()`
- **Best practices**: Proper timeout handling, resource cleanup, logging patterns

### When to Use the Official Docs

Consult the official API documentation when you need:

1. **Understanding payment flows**: The official docs explain how ATH Móvil payments work conceptually
2. **Business account setup**: How to register and configure your ATH Business account
3. **Button integration**: If you need the JavaScript payment button (not covered by this library)
4. **API changes**: Official announcements of new features or deprecations
5. **Deep API details**: Exact HTTP request/response formats

### When to Use This Library's Docs

Use this library's documentation when:

1. **Implementing in Python**: You're building a Python application
2. **Quick integration**: You want to start accepting payments quickly
3. **Type safety**: You need compile-time validation of payment data
4. **Error handling**: You want idiomatic Python exception handling
5. **Advanced features**: You need refunds, polling, testing patterns

## API Endpoints Used

This library uses the following ATH Móvil API endpoints:

| Endpoint | Library Method | Purpose |
|----------|----------------|---------|
| `POST /api/business-transaction/ecommerce/payment` | `create_payment()` | Create new payment |
| `POST /api/business-transaction/ecommerce/business/findPayment` | `find_payment()` | Check payment status |
| `POST /api/business-transaction/ecommerce/authorization` | `authorize_payment()` | Complete payment |
| `POST /api/business-transaction/ecommerce/business/updatePhoneNumber` | `update_phone_number()` | Update customer phone |
| `POST /api/business-transaction/ecommerce/business/cancel` | `cancel_payment()` | Cancel payment |
| `POST /api/business-transaction/ecommerce/refund` | `refund_payment()` | Process refund |

All endpoints use:
- **Base URL**: `https://payments.athmovil.com`
- **Content-Type**: `application/json`
- **Authentication**: Bearer token in `Authorization` header

## Raw API Example vs. This Library

### Using Raw API (curl)

```bash
curl -X POST https://payments.athmovil.com/api/business-transaction/ecommerce/payment \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_PUBLIC_TOKEN" \
  -d '{
    "publicToken": "YOUR_PUBLIC_TOKEN",
    "total": 50.00,
    "phoneNumber": "7875551234",
    "tax": 5.00,
    "subtotal": 45.00,
    "metadata1": "Order #123"
  }'
```

### Using This Library

```python
from athm import ATHMovilClient

client = ATHMovilClient(public_token="YOUR_PUBLIC_TOKEN")

payment = client.create_payment(
    total="50.00",
    phone_number="7875551234",
    tax="5.00",
    subtotal="45.00",
    metadata1="Order #123"
)
```

**Benefits of the library:**
- No manual HTTP headers or JSON serialization
- Automatic type conversion (strings to proper JSON types)
- Input validation before API call
- Typed response object with autocomplete
- Automatic error handling and retries

## Authentication

Both the library and raw API use the same authentication mechanism:

### Public Token

- Required for all payment operations
- Format: Long alphanumeric string
- Generated in ATH Business portal under **API Credentials**
- Passed as `Bearer` token in `Authorization` header
- The library handles this automatically

### Private Token

- Required only for refunds
- Separate from public token
- More privileged access
- Should be stored more securely

```python
# Library handles both tokens
client = ATHMovilClient(
    public_token="YOUR_PUBLIC_TOKEN",
    private_token="YOUR_PRIVATE_TOKEN"  # Optional, for refunds
)
```

## Data Models Mapping

### Payment Request

**Official API JSON:**
```json
{
  "publicToken": "token",
  "total": 50.00,
  "phoneNumber": "7875551234",
  "tax": 5.00,
  "subtotal": 45.00,
  "metadata1": "Order #123",
  "metadata2": "Customer info",
  "items": [
    {
      "name": "Product",
      "description": "Description",
      "quantity": "1",
      "price": "45.00",
      "tax": "5.00"
    }
  ]
}
```

**This Library:**
```python
from athm.models import PaymentRequest, PaymentItem

request = PaymentRequest(
    total="50.00",
    phone_number="7875551234",
    tax="5.00",
    subtotal="45.00",
    metadata1="Order #123",
    metadata2="Customer info",
    items=[
        PaymentItem(
            name="Product",
            description="Description",
            quantity="1",
            price="45.00",
            tax="5.00"
        )
    ]
)
```

**Library benefits:**
- Field validation (e.g., amount between $1-$1500)
- Phone number format checking
- Metadata length validation (40 chars)
- Type hints for IDE autocomplete
- Automatic camelCase conversion

## Error Codes

Both the library and official API use the same error codes (e.g., `BTRA_0001`, `BTRA_0032`).

**Official API** returns errors as JSON:
```json
{
  "errorCode": "BTRA_0001",
  "message": "Amount is below minimum ($1.00)"
}
```

**This Library** raises Python exceptions:
```python
from athm import ValidationError

try:
    payment = client.create_payment(total="0.50", ...)
except ValidationError as e:
    print(e.error_code)  # "BTRA_0001"
    print(e)             # "Amount is below minimum ($1.00)"
```

See the **[Error Handling Guide](errors.md)** for complete error code reference.

## Payment Flow Comparison

### Official API Flow (Manual)

1. **Create payment**: `POST /payment` → get `ecommerce_id`
2. **Poll for status**: `POST /findPayment` every 2s
3. **Check status**: Wait until `status == "CONFIRM"`
4. **Authorize**: `POST /authorization`
5. **Handle errors**: Parse JSON error responses

### Library Flow (Automatic)

```python
# Equivalent to all steps above
payment = client.create_payment(...)
confirmed = client.wait_for_confirmation(payment.ecommerce_id)
result = client.authorize_payment(payment.ecommerce_id)
```

Or even simpler:
```python
# One-liner for entire flow
result = client.process_complete_payment(total="50.00", phone_number="7875551234")
```

## Rate Limiting

The official API has rate limits (not publicly documented). This library:

- Implements automatic retry with exponential backoff
- Catches `429 Too Many Requests` and raises `RateLimitError`
- Allows configurable `max_retries` (default: 3)

```python
client = ATHMovilClient(
    public_token="...",
    max_retries=5  # Increase retry attempts
)
```

## SSL/TLS

Both the library and official API require HTTPS:

- **Production endpoint**: `https://payments.athmovil.com`
- **TLS**: Minimum TLS 1.2
- **Certificate verification**: Enabled by default

```python
# Library defaults to secure settings
client = ATHMovilClient(
    public_token="...",
    verify_ssl=True  # Default, recommended
)
```

## Additional Resources

### Official Documentation
- [ATH Móvil API GitHub](https://github.com/evertec/ATHM-Payment-Button-API)
- [ATH Business Portal](https://athmovilbusiness.com/)

### This Library
- [API Reference](api-reference.md) - Python method documentation
- [Payment Flow Guide](guide.md) - Step-by-step walkthrough
- [Error Handling](errors.md) - Complete error guide
- [Installation](installation.md) - Setup and configuration

### Community
- [Report Issues](https://github.com/django-athm/athm-python/issues)
- [Feature Requests](https://github.com/django-athm/athm-python/issues/new)

## Contributing

If you find discrepancies between this library and the official API:

1. Check the [official API documentation](https://github.com/evertec/ATHM-Payment-Button-API) first
2. [Report an issue](https://github.com/django-athm/athm-python/issues) with details
3. Include API response examples if possible

This library aims to stay synchronized with the official ATH Móvil API specifications.

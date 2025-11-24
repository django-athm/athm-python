# Installation

!!! danger "No Test Environment Available"
    **Important**: ATH Móvil does not provide a sandbox or test environment. All API calls are made to the production environment with real money transactions. You must have:

    - An active ATH Business account with a registered payment card
    - An active ATH Móvil personal account (separate from business account)
    - Different payment cards for your business and personal accounts

    When testing, you will create real payment requests that require actual confirmation and cancellation.

## Prerequisites

- Python 3.10 or higher
- **ATH Business account** with API credentials
- **ATH Móvil personal account** for testing (must use different payment card than business account)

## Install the Package

### Using pip

```bash
pip install athm
```

### Using uv (recommended for modern projects)

```bash
uv add athm
```

### Verify Installation

```python
import athm
print(athm.__version__)
```

## Get Your API Credentials

To use the ATH Móvil API, you need API tokens from ATH Business.

### 1. Sign Up for ATH Business

1. Visit [ATH Business](https://athmovilbusiness.com/) or directly download the app
2. Create an account or log in
3. Complete merchant verification

### 2. Generate API Tokens

Once your account is verified:

1. Navigate to **Settings** > **API Credentials**
2. Generate your **Public Token** (required for all operations)
3. Generate your **Private Token** (required for refunds only)

!!! warning "Keep Tokens Secret"
    Never commit your tokens to version control. Always use environment variables or secure secret management.

### Token Types

| Token Type | Required For | Permissions |
|------------|--------------|-------------|
| **Public Token** | All payment operations | Create, check, authorize, cancel payments |
| **Private Token** | Refunds only | Process refunds on completed payments |

!!! warning "Token Expiration"
    Tokens can expire. When you receive `token.expired` or `BTRA_0401`/`BTRA_0402`/`BTRA_0403` errors, generate new tokens from the ATH Business portal.

## Configure Environment Variables

### Create a `.env` file

```bash
# .env
ATHM_PUBLIC_TOKEN=your_public_token_here
ATHM_PRIVATE_TOKEN=your_private_token_here  # Optional, only for refunds
```

### Using python-dotenv (recommended)

```bash
pip install python-dotenv
```

```python
from dotenv import load_dotenv
from athm import ATHMovilClient
import os

# Load .env file
load_dotenv()

client = ATHMovilClient(
    public_token=os.getenv("ATHM_PUBLIC_TOKEN"),
    private_token=os.getenv("ATHM_PRIVATE_TOKEN")
)
```

## Test Your Setup

```python
from athm import ATHMovilClient
import os

client = ATHMovilClient(public_token=os.getenv("ATHM_PUBLIC_TOKEN"))

try:
    payment = client.create_payment(
        total="1.00",
        phone_number="7875551234",
        items=[{"name": "Test", "description": "Test", "quantity": "1", "price": "1.00"}]
    )
    print(f"Success! Payment ID: {payment.data.ecommerce_id}")

    client.cancel_payment(payment.data.ecommerce_id)
    print("Test payment cancelled")
except Exception as e:
    print(f"Error: {e}")
finally:
    client.close()
```

## Next Steps

Now that you're set up, learn how to:

- **[Process a payment](guide.md)** - Complete payment flow with diagrams
- **[Handle errors](errors.md)** - Robust error handling
- **[Use the API](api-reference.md)** - Full API reference

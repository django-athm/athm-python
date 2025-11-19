# Installation

!!! danger "No Test Environment Available"
    **Important**: ATH Móvil does not provide a sandbox or test environment. All API calls are made to the production environment with real money transactions. You must have:

    - An active ATH Business account with a registered payment card
    - An active ATH Móvil personal account (separate from business account)
    - Different payment cards for your business and personal accounts

    When testing, you will create real payment requests that require actual confirmation and cancellation.

## Prerequisites

Before installing the library, ensure you have:

### Required Accounts

1. **ATH Business Account**
   - Active merchant account with verified business information
   - Registered payment card linked to the business account
   - Access to ATH Business app or web portal for API credential management

2. **ATH Móvil Personal Account**
   - Active personal ATH Móvil account for testing
   - Must use a **different payment card** than your business account
   - Cannot use the same card for customer and merchant transactions (will trigger error BTRA_0003)

### Technical Requirements

- Python 3.10 or higher
- Active internet connection (all API calls require HTTPS)
- Secure environment for storing API credentials

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

### Token Lifecycle and Expiry

!!! warning "Token Expiration"
    API tokens can expire after a period specified by ATH Business. When a token expires:

    - You will receive error `token.expired` or `BTRA_0401`/`BTRA_0402`/`BTRA_0403`
    - You must generate new tokens from the ATH Business portal
    - No automatic token refresh is available

**Best practices:**

- Monitor for authentication errors in your application logs
- Have a process to quickly rotate expired tokens
- Store tokens securely using environment variables or secret managers
- Never hardcode tokens in your source code

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

Run this quick test to verify everything is configured correctly:

```python
from athm import ATHMovilClient
import os

# Initialize client
client = ATHMovilClient(public_token=os.getenv("ATHM_PUBLIC_TOKEN"))

# Create a test payment (won't charge anyone)
try:
    payment = client.create_payment(
        total="1.00",
        phone_number="7875551234",  # Your phone number with ATH Móvil account
        subtotal="1.00",
        tax="0.00",
        metadata1="Installation Test"
    )
    print(f"Success! Payment ID: {payment.data.ecommerce_id}")

    # Cancel the test payment
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

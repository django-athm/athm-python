# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`athm` is a modern, type-safe Python library for the ATH Móvil payment platform. It provides a synchronous client for interacting with the ATH Móvil Payment Button API with strict type safety, Pydantic validation, and comprehensive error handling.

## Development Commands

### Setup
```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies with dev extras
uv sync --all-extras --dev

# Install pre-commit hooks
pre-commit install
```

### Testing
```bash
# Run all tests
uv run pytest

# Run tests with coverage report
uv run pytest --cov=athm --cov-report=term-missing --cov-report=html

# Run specific test file
uv run pytest tests/unit/test_client.py

# Run specific test function
uv run pytest tests/unit/test_client.py::test_create_payment

# Run with verbose output
uv run pytest -v

# Skip integration tests (default behavior)
uv run pytest -m "not integration"

# Run integration tests only
uv run pytest -m integration
```

**Important**: Coverage threshold is 95% minimum (configured in pyproject.toml). The CI enforces 100% coverage.

### Code Quality
```bash
# Type checking
uv run mypy athm

# Linting
uv run ruff check athm tests

# Auto-fix linting issues
uv run ruff check athm tests --fix

# Format code
uv run ruff format athm tests

# Run all pre-commit hooks
pre-commit run --all-files

# Run security checks
uv run bandit -r athm
```

### Building and Documentation
```bash
# Build package
uv build

# Serve documentation locally
uv run mkdocs serve

# Build documentation
uv run mkdocs build
```

## Architecture

### Core Components

**`athm/client.py`** - The `ATHMovilClient` class is the main entry point. It:
- Manages HTTP client lifecycle (supports context manager pattern)
- Implements retry logic with exponential backoff
- Stores auth tokens internally for convenience
- Provides both low-level methods (create, find, authorize) and high-level convenience methods (wait_for_confirmation, process_complete_payment)

**`athm/models.py`** - Pydantic models for request/response validation:
- All models use strict validation with custom validators
- Decimal amounts are validated and formatted to 2 decimal places
- Phone numbers must be exactly 10 digits
- API field names use camelCase via aliases (e.g., `ecommerce_id` → `ecommerceId`)

**`athm/exceptions.py`** - Exception hierarchy with intelligent error classification:
- Exceptions are created from API error codes using `create_exception_from_response()`
- Error codes are categorized (auth, validation, transaction, business, network, internal)
- Each exception includes error_code, status_code, and response_data

**`athm/constants.py`** - API configuration and error code mappings:
- Base URL, endpoints, and headers
- Error code sets for classification
- Business rules (MIN_AMOUNT=$1.00, MAX_AMOUNT=$1500.00, MIN_TIMEOUT=120s)

### Payment Flow

The typical payment flow involves multiple sequential steps:

1. **Create Payment** → Returns `ecommerce_id` and `auth_token`
2. **Poll Status** → Wait for customer to confirm in ATH Móvil app (status: OPEN → CONFIRM)
3. **Authorize Payment** → Complete the transaction (status: CONFIRM → COMPLETED)

The client stores auth tokens internally keyed by `ecommerce_id`, so you don't need to manually track them between create and authorize calls.

### Key Design Patterns

- **Automatic Retries**: Network errors and timeouts automatically retry up to `max_retries` (default: 3) with exponential backoff
- **Context Manager**: Use `with ATHMovilClient(...) as client:` for automatic cleanup
- **Lazy Client Init**: The httpx.Client is only created when first needed (via `sync_client` property)
- **Token Storage**: Auth tokens are stored in `_auth_tokens` dict after create_payment, retrieved automatically in authorize_payment
- **Polling Helper**: `wait_for_confirmation()` blocks while polling status - meant for simple scripts, not concurrent applications

### Type Safety

This library uses strict mypy configuration:
- All functions have complete type hints
- Uses `typing-extensions` for Python 3.10 compatibility (`Self` type)
- Pydantic provides runtime validation
- Custom TypedDicts in `athm/types.py` for headers and JSON objects

## Important Conventions

### Testing
- Mock external API calls using `pytest-httpx`
- Unit tests in `tests/unit/`
- Integration tests should be marked with `@pytest.mark.integration`
- Use fixtures from `tests/conftest.py` for common test data
- Test both success and error cases

### Error Handling
When adding new error codes:
1. Add to `ErrorCode` enum in constants.py
2. Add to appropriate category set (AUTHENTICATION_ERROR_CODES, etc.)
3. Add user-friendly message to ERROR_MESSAGES dict
4. The exception hierarchy will automatically classify it

### Docstrings
Use Google-style docstrings:
```python
def example(param: str) -> int:
    """Short description.

    Longer description if needed.

    Args:
        param: Description

    Returns:
        Description

    Raises:
        ExceptionType: When it happens
    """
```

### Commit Messages
Use conventional commits format (enforced by commitizen):
```
type(scope): description

feat(client): add webhook signature validation
fix(models): handle null values in payment response
docs(readme): update installation instructions
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

## ATH Móvil Business Rules

- Minimum payment amount: $1.00
- Maximum payment amount: $1,500.00
- Minimum timeout: 120 seconds
- Maximum metadata length: 40 characters
- Maximum refund message length: 50 characters
- Phone numbers: Must be 10 digits (Puerto Rico format)
- Private token required only for refunds

## Pre-commit Hooks

The following checks run automatically before each commit:
- Ruff formatting and linting
- mypy type checking (strict mode, athm/ only)
- YAML, JSON, TOML validation
- Bandit security scanning
- Commitizen message validation
- Trailing whitespace, end-of-file fixes
- Private key detection

If pre-commit modifies files (e.g., formatting), stage the changes and commit again.

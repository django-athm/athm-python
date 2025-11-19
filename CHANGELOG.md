# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release of the ATH Móvil unofficial library
- Complete implementation of ATH Móvil Payment Button API v2
- Support for all payment operations:
  - Create payment tickets
  - Check payment status
  - Authorize confirmed payments
  - Update phone numbers
  - Cancel payments
  - Process refunds (full and partial)
- Synchronous client implementation with modern Python practices
- Comprehensive Pydantic models for request/response validation
- Custom exception hierarchy for proper error handling
- Automatic retry logic with exponential backoff
- Helper methods for common workflows:
  - `wait_for_confirmation()` - Poll until payment confirmed
  - `process_complete_payment()` - End-to-end payment flow
- Type hints throughout with py.typed marker
- 100% test coverage with pytest
- Comprehensive documentation and examples
- CI/CD with GitHub Actions
- Pre-commit hooks for code quality
- Support for Python 3.10+

### Security
- Secure token handling
- SSL/TLS verification by default
- Private token protection for refund operations

### Documentation
- Comprehensive README with quick start guide
- API reference documentation
- Multiple example scripts demonstrating common use cases
- Error handling best practices

## [0.1.0] - TBD

_Initial release - see Unreleased section above for features_

[Unreleased]: https://github.com/django-athm/athm-python/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/django-athm/athm-python/releases/tag/v0.1.0

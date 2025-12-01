# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


_Initial release - see Unreleased section above for features_

[Unreleased]: https://github.com/django-athm/athm-python/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/django-athm/athm-python/releases/tag/v0.1.0


## v0.4.0 (2025-12-01)

### Feat

- **webhooks**: add webhook support for transaction notifications

### Fix

- sync version to 0.3.0 across all version files

### Refactor

- simplify models and consolidate error code mappings

## v0.3.0 (2025-11-24)

### Fix

- use ErrorCode enum and make items parameter explicit
- **docs**: correct PaymentResponse field access in documentation

## v0.2.0 (2025-11-19)

### Fix

- **client**: improve validation error message formatting

## v0.2.0b0 (2025-11-19)

### Feat

- implement ATH Móvil Python SDK with full API support

### Fix

- **docs**: add missing pymdown-extensions dependency for MkDocs
- **docs**: address API documentation inconsistencies

### Refactor

- **docs**: convert API reference to clean markdown format
- consolidate CI workflows and improve project documentation

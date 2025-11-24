"""Type definitions for ATH Móvil library."""

import sys

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

# Timeout type
Timeout = float | int | None

__all__ = [
    "Self",
    "Timeout",
]

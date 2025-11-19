"""Type definitions for ATH Móvil library."""

import sys
from typing import TYPE_CHECKING, Any, TypeVar

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

# Type aliases
JSONDict = dict[str, Any]
Headers = dict[str, str]

# Generic type for response models
T = TypeVar("T")

# Timeout type
Timeout = float | int | None

# Export for type checking
if TYPE_CHECKING:
    from athm.client import ATHMovilClient  # noqa: F401

__all__ = [
    "Headers",
    "JSONDict",
    "Self",
    "T",
    "Timeout",
]

"""
Universal Attribute (ATTR) model implementation

This module implements the formal symbolic algebra for recursive attribute structures
as described in the defensive disclosure.
"""

from .core import ATTR, ATTRPattern, ATTRQuery, ATTRPath
from .algebra import ATTRAlgebra, UnificationResult
from .serialization import ATTRSerializer

__all__ = [
    "ATTR",
    "ATTRPattern", 
    "ATTRQuery",
    "ATTRPath",
    "ATTRAlgebra",
    "UnificationResult",
    "ATTRSerializer"
]
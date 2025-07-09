"""
ThinkingMesh: Symbolic Memory Architecture and Distributed Semantic Mesh Protocol

This package implements a novel approach to distributed AI systems using:
- Universal Attribute (ATTR) recursive symbolic modeling
- Schema-emergent symbolic memory architecture  
- Thinking Mesh Protocol over Zenoh for distributed reasoning

Author: Samuel Elsner
License: CC-BY 4.0 / Public Domain (defensive disclosure) + MIT (implementation)
"""

__version__ = "0.1.0"
__author__ = "Samuel Elsner"
__license__ = "CC-BY 4.0 / MIT"

from .attr.core import ATTR, ATTRPattern, ATTRQuery
from .memory.symbolic import SymbolicMemory
from .agents.base import ThinkingMeshAgent

__all__ = [
    "ATTR",
    "ATTRPattern", 
    "ATTRQuery",
    "SymbolicMemory",
    "ThinkingMeshAgent"
]
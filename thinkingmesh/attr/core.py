"""
Core implementation of the Universal Attribute (ATTR) model

Implements the formal symbolic algebra:
attribute : attribute[attribute[...]]

Where each attribute can be:
- An atomic value (symbol, number, string)  
- A nested attribute structure
- A variable (for pattern matching)
"""

import time
from typing import Any, Dict, List, Optional, Union, Set
from dataclasses import dataclass
from pydantic import BaseModel


class ATTRValue:
    """Base class for all ATTR values"""
    pass


@dataclass(frozen=True)
class ATTRAtom(ATTRValue):
    """Atomic value in ATTR system"""
    value: Union[str, int, float, bool]
    
    def __str__(self) -> str:
        if isinstance(self.value, str):
            return f'"{self.value}"'
        return str(self.value)
    
    def __repr__(self) -> str:
        return f"ATTRAtom({self.value!r})"


@dataclass(frozen=True)
class ATTRVariable(ATTRValue):
    """Variable for pattern matching and unification"""
    name: str
    
    def __str__(self) -> str:
        return f"?{self.name}"
    
    def __repr__(self) -> str:
        return f"ATTRVariable({self.name!r})"


@dataclass(frozen=True)
class ATTR(ATTRValue):
    """
    Universal Attribute: recursive symbolic structure
    
    Form: attribute : [attribute[attribute[...]]]
    
    Examples:
    - ATTR("temperature", ATTRAtom(25.3))
    - ATTR("sensor", [ATTR("id", ATTRAtom("temp_01")), ATTR("status", ATTRAtom("active"))])
    """
    key: str
    value: Union[ATTRValue, List["ATTR"]]
    timestamp: Optional[float] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            object.__setattr__(self, 'timestamp', time.time())
    
    def __str__(self) -> str:
        if isinstance(self.value, list):
            nested = ", ".join(str(attr) for attr in self.value)
            return f"{self.key}: [{nested}]"
        else:
            return f"{self.key}: {self.value}"
    
    def __repr__(self) -> str:
        return f"ATTR({self.key!r}, {self.value!r})"
    
    def is_atomic(self) -> bool:
        """Check if this ATTR has an atomic value"""
        return isinstance(self.value, ATTRAtom)
    
    def is_nested(self) -> bool:
        """Check if this ATTR has nested attributes"""
        return isinstance(self.value, list)
    
    def is_variable(self) -> bool:
        """Check if this ATTR has a variable value"""
        return isinstance(self.value, ATTRVariable)
    
    def get_nested_attr(self, key: str) -> Optional["ATTR"]:
        """Get a nested attribute by key"""
        if not self.is_nested():
            return None
        
        for attr in self.value:
            if attr.key == key:
                return attr
        return None
    
    def get_all_keys(self) -> Set[str]:
        """Get all keys in this attribute structure"""
        keys = {self.key}
        if self.is_nested():
            for attr in self.value:
                keys.update(attr.get_all_keys())
        return keys
    
    def depth(self) -> int:
        """Calculate the depth of nested structure"""
        if not self.is_nested():
            return 1
        return 1 + max((attr.depth() for attr in self.value), default=0)


@dataclass
class ATTRPath:
    """
    Represents a path through an ATTR structure
    
    Examples:
    - ATTRPath(["car", "engine", "rpm"])
    - ATTRPath(["sensor", "readings", "temperature"])
    """
    segments: List[str]
    
    def __str__(self) -> str:
        return ".".join(self.segments)
    
    def __repr__(self) -> str:
        return f"ATTRPath({self.segments!r})"
    
    @classmethod
    def parse(cls, path_str: str) -> "ATTRPath":
        """Parse a dot-separated path string"""
        return cls(path_str.split("."))
    
    def resolve(self, attr: ATTR) -> Optional[ATTRValue]:
        """
        Resolve this path in the given ATTR structure
        
        Examples:
        - ATTRPath(["engine", "rpm"]).resolve(car_attr) → ATTRAtom(9500)
        """
        current = attr
        
        for segment in self.segments:
            if current.key == segment:
                # If this is the last segment, return the value
                if len(self.segments) == 1:
                    return current.value
                # Continue traversal with remaining segments
                path = ATTRPath(self.segments[1:])
                if current.is_nested():
                    # Search in nested attributes
                    for nested_attr in current.value:
                        result = path.resolve(nested_attr)
                        if result is not None:
                            return result
                return None
            
            elif current.is_nested():
                # Search for segment in nested attributes
                for nested_attr in current.value:
                    if nested_attr.key == segment:
                        if len(self.segments) == 1:
                            return nested_attr.value
                        # Continue with remaining path
                        remaining_path = ATTRPath(self.segments[1:])
                        return remaining_path.resolve(nested_attr)
                return None
        
        return None


@dataclass
class ATTRPattern:
    """
    Pattern for matching ATTR structures
    
    Supports:
    - Variable binding (?x, ?y, etc.)
    - Structural matching
    - Value constraints
    """
    template: ATTR
    constraints: List[str] = None
    
    def __post_init__(self):
        if self.constraints is None:
            self.constraints = []
    
    def __str__(self) -> str:
        pattern_str = str(self.template)
        if self.constraints:
            constraints_str = " WHERE " + " AND ".join(self.constraints)
            return pattern_str + constraints_str
        return pattern_str
    
    def extract_variables(self) -> Set[str]:
        """Extract all variable names from the pattern"""
        variables = set()
        
        def extract_from_value(value: ATTRValue):
            if isinstance(value, ATTRVariable):
                variables.add(value.name)
            elif isinstance(value, list):
                for attr in value:
                    extract_from_value(attr.value)
        
        extract_from_value(self.template.value)
        return variables


@dataclass
class ATTRQuery:
    """
    Query for searching ATTR structures
    
    Supports:
    - Path-based queries: car.engine.rpm > 10000
    - Pattern matching: motor: [rpm: ?x] WHERE ?x > 9000
    - Structural queries
    """
    pattern: ATTRPattern
    conditions: List[str] = None
    
    def __post_init__(self):
        if self.conditions is None:
            self.conditions = []
    
    def __str__(self) -> str:
        query_str = str(self.pattern)
        if self.conditions:
            conditions_str = " AND ".join(self.conditions)
            if " WHERE " in query_str:
                return query_str + " AND " + conditions_str
            else:
                return query_str + " WHERE " + conditions_str
        return query_str


# Convenience constructors
def attr_atom(value: Union[str, int, float, bool]) -> ATTRAtom:
    """Create an atomic ATTR value"""
    return ATTRAtom(value)


def attr_var(name: str) -> ATTRVariable:
    """Create an ATTR variable for pattern matching"""
    return ATTRVariable(name)


def attr(key: str, value: Union[ATTRValue, List[ATTR], str, int, float, bool]) -> ATTR:
    """
    Convenience constructor for ATTR
    
    Examples:
    - attr("temperature", 25.3)
    - attr("sensor", [attr("id", "temp_01"), attr("status", "active")])
    """
    if isinstance(value, (str, int, float, bool)):
        value = attr_atom(value)
    elif isinstance(value, list) and all(isinstance(item, ATTR) for item in value):
        pass  # Already a list of ATTR
    elif not isinstance(value, ATTRValue):
        raise ValueError(f"Invalid value type for ATTR: {type(value)}")
    
    return ATTR(key, value)
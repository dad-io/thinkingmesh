"""
ATTR Symbolic Algebra Operations

Implements the formal algebra operations:
- Union (∪): Merging attribute structures  
- Subsumption (⊆): Substructure testing
- Unification (≈): Pattern matching with variable binding
- Projection (.): Path resolution
"""

from typing import Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass
from .core import ATTR, ATTRAtom, ATTRVariable, ATTRValue, ATTRPattern, ATTRPath


@dataclass
class UnificationResult:
    """Result of unifying two ATTR structures"""
    success: bool
    bindings: Dict[str, ATTRValue]
    unified: Optional[ATTR] = None
    
    def __str__(self) -> str:
        if not self.success:
            return "Unification failed"
        
        binding_strs = [f"?{var} = {val}" for var, val in self.bindings.items()]
        bindings_str = ", ".join(binding_strs) if binding_strs else "no bindings"
        return f"Unified: {self.unified} | Bindings: {bindings_str}"


class ATTRAlgebra:
    """
    Symbolic algebra operations for ATTR structures
    
    Implements the formal operators defined in the defensive disclosure:
    - : (attribute definition)
    - [...] (nesting)
    - . (path resolution) 
    - ∪ (union)
    - ⊆ (subsumption)
    - ≈ (unification)
    """
    
    @staticmethod
    def union(attr1: ATTR, attr2: ATTR) -> ATTR:
        """
        Union operation (∪): Merge two attribute structures
        
        Rules:
        - If keys match, recursively merge values
        - If keys differ, include both attributes
        - Atomic values: later value overwrites
        - Nested values: merge recursively
        
        Example:
        car: [engine: [rpm: 9500]] ∪ car: [engine: [temp: 80]] 
        → car: [engine: [rpm: 9500, temp: 80]]
        """
        if attr1.key != attr2.key:
            # Different keys - cannot directly merge
            raise ValueError(f"Cannot union attributes with different keys: {attr1.key} vs {attr2.key}")
        
        # Same key - merge values
        if attr1.is_atomic() and attr2.is_atomic():
            # Atomic values: second overwrites first
            return ATTR(attr1.key, attr2.value)
        
        elif attr1.is_atomic() and attr2.is_nested():
            # Atomic + Nested: nested takes precedence
            return attr2
        
        elif attr1.is_nested() and attr2.is_atomic():
            # Nested + Atomic: atomic overwrites
            return ATTR(attr1.key, attr2.value)
        
        elif attr1.is_nested() and attr2.is_nested():
            # Both nested: merge attribute lists
            merged_attrs = {}
            
            # Add all attributes from first structure
            for attr in attr1.value:
                merged_attrs[attr.key] = attr
            
            # Merge/add attributes from second structure
            for attr in attr2.value:
                if attr.key in merged_attrs:
                    # Recursively merge
                    merged_attrs[attr.key] = ATTRAlgebra.union(merged_attrs[attr.key], attr)
                else:
                    # New attribute
                    merged_attrs[attr.key] = attr
            
            return ATTR(attr1.key, list(merged_attrs.values()))
        
        else:
            # Handle variable cases
            if attr1.is_variable():
                return attr2
            elif attr2.is_variable():
                return attr1
            else:
                raise ValueError(f"Cannot union incompatible value types: {type(attr1.value)} vs {type(attr2.value)}")
    
    @staticmethod
    def subsumes(container: ATTR, contained: ATTR) -> bool:
        """
        Subsumption test (⊆): Check if one structure contains another
        
        Rules:
        - container ⊆ contained if contained has all attributes of container
        - Values must match or be compatible
        - Variables in container can match any value in contained
        
        Example:
        rpm: 9500 ⊆ motor: [rpm: 9500, temp: 60] → True
        """
        if container.key != contained.key and not container.is_variable():
            return False
        
        if container.is_atomic():
            if contained.is_atomic():
                return container.value.value == contained.value.value
            else:
                return False
        
        elif container.is_variable():
            # Variable matches anything
            return True
        
        elif container.is_nested():
            if not contained.is_nested():
                return False
            
            # Check that all attributes in container exist in contained
            contained_keys = {attr.key: attr for attr in contained.value}
            
            for container_attr in container.value:
                if container_attr.key not in contained_keys:
                    return False
                
                # Recursively check subsumption
                if not ATTRAlgebra.subsumes(container_attr, contained_keys[container_attr.key]):
                    return False
            
            return True
        
        return False
    
    @staticmethod
    def unify(pattern: ATTR, data: ATTR, bindings: Optional[Dict[str, ATTRValue]] = None) -> UnificationResult:
        """
        Unification operation (≈): Match pattern against data with variable binding
        
        Rules:
        - Variables in pattern bind to corresponding values in data
        - Non-variable values must match exactly
        - Nested structures unify recursively
        - Returns bindings and unified structure
        
        Example:
        motor: [rpm: ?x] ≈ motor: [rpm: 12000] → ?x = 12000
        """
        if bindings is None:
            bindings = {}
        
        # Check key compatibility
        if pattern.key != data.key:
            return UnificationResult(False, bindings)
        
        # Handle pattern variables
        if pattern.is_variable():
            var_name = pattern.value.name
            if var_name in bindings:
                # Variable already bound - check consistency
                if bindings[var_name] != data.value:
                    return UnificationResult(False, bindings)
            else:
                # Bind variable
                bindings[var_name] = data.value
            
            return UnificationResult(True, bindings, data)
        
        # Handle atomic values
        if pattern.is_atomic() and data.is_atomic():
            if pattern.value.value == data.value.value:
                return UnificationResult(True, bindings, data)
            else:
                return UnificationResult(False, bindings)
        
        # Handle nested structures
        if pattern.is_nested() and data.is_nested():
            # Create maps for efficient lookup
            data_attrs = {attr.key: attr for attr in data.value}
            unified_attrs = []
            
            # Unify each pattern attribute with corresponding data attribute
            for pattern_attr in pattern.value:
                if pattern_attr.key in data_attrs:
                    result = ATTRAlgebra.unify(pattern_attr, data_attrs[pattern_attr.key], bindings)
                    if not result.success:
                        return UnificationResult(False, bindings)
                    unified_attrs.append(result.unified)
                    bindings.update(result.bindings)
                else:
                    # Pattern attribute not found in data
                    return UnificationResult(False, bindings)
            
            # Add any remaining data attributes not in pattern
            pattern_keys = {attr.key for attr in pattern.value}
            for data_attr in data.value:
                if data_attr.key not in pattern_keys:
                    unified_attrs.append(data_attr)
            
            unified = ATTR(pattern.key, unified_attrs)
            return UnificationResult(True, bindings, unified)
        
        # Type mismatch
        return UnificationResult(False, bindings)
    
    @staticmethod
    def project(attr: ATTR, path: ATTRPath) -> Optional[ATTRValue]:
        """
        Projection operation (.): Resolve a path in an attribute structure
        
        Examples:
        - car.engine.rpm → 9500
        - sensor.readings.temperature → 25.3
        """
        return path.resolve(attr)
    
    @staticmethod
    def match_pattern(pattern: ATTRPattern, data: ATTR) -> UnificationResult:
        """
        Match a pattern against data, handling constraints
        
        Combines unification with constraint evaluation
        """
        result = ATTRAlgebra.unify(pattern.template, data)
        
        if not result.success:
            return result
        
        # Evaluate constraints
        for constraint in pattern.constraints:
            if not ATTRAlgebra._evaluate_constraint(constraint, result.bindings):
                return UnificationResult(False, result.bindings)
        
        return result
    
    @staticmethod
    def _evaluate_constraint(constraint: str, bindings: Dict[str, ATTRValue]) -> bool:
        """
        Evaluate a constraint expression with variable bindings
        
        Simple constraint evaluation - in practice would use a proper parser
        """
        # Simplified constraint evaluation
        # In practice, would implement a proper expression parser
        
        # Handle simple comparisons like "?x > 9000"
        if ">" in constraint:
            left, right = constraint.split(">", 1)
            left, right = left.strip(), right.strip()
            
            if left.startswith("?") and left[1:] in bindings:
                var_value = bindings[left[1:]]
                if isinstance(var_value, ATTRAtom) and isinstance(var_value.value, (int, float)):
                    try:
                        threshold = float(right)
                        return var_value.value > threshold
                    except ValueError:
                        return False
        
        elif "=" in constraint:
            left, right = constraint.split("=", 1)
            left, right = left.strip(), right.strip()
            
            if left.startswith("?") and left[1:] in bindings:
                var_value = bindings[left[1:]]
                if isinstance(var_value, ATTRAtom):
                    return str(var_value.value) == right.strip('"\'')
        
        return True  # Default to true for unhandled constraints
    
    @staticmethod
    def compress_similar(attrs: List[ATTR], similarity_threshold: float = 0.8) -> List[ATTR]:
        """
        Compress similar ATTR structures by extracting common patterns
        
        Part of the schema-emergent compression layer
        """
        if len(attrs) < 2:
            return attrs
        
        # Simple compression: find exactly matching structures
        unique_attrs = []
        compressed_count = {}
        
        for attr in attrs:
            attr_str = str(attr)
            found_match = False
            
            for unique_attr in unique_attrs:
                if str(unique_attr) == attr_str:
                    compressed_count[attr_str] = compressed_count.get(attr_str, 1) + 1
                    found_match = True
                    break
            
            if not found_match:
                unique_attrs.append(attr)
                compressed_count[attr_str] = 1
        
        return unique_attrs
    
    @staticmethod
    def generalize_pattern(attrs: List[ATTR]) -> Optional[ATTRPattern]:
        """
        Generate a pattern that generalizes multiple similar ATTR structures
        
        Part of schema discovery mechanism
        """
        if not attrs:
            return None
        
        if len(attrs) == 1:
            # Single attribute - convert values to variables
            return ATTRAlgebra._generalize_single(attrs[0])
        
        # Find common structure across all attributes
        base_attr = attrs[0]
        
        # Simple generalization: if all have same key, generalize values
        if all(attr.key == base_attr.key for attr in attrs):
            if all(attr.is_atomic() for attr in attrs):
                # All atomic - create variable
                var_name = f"var_{base_attr.key}"
                pattern_attr = ATTR(base_attr.key, ATTRVariable(var_name))
                return ATTRPattern(pattern_attr)
            
            elif all(attr.is_nested() for attr in attrs):
                # All nested - recursively generalize
                # This is a simplified version - full implementation would be more sophisticated
                return ATTRPattern(base_attr)  # Placeholder
        
        return None
    
    @staticmethod
    def _generalize_single(attr: ATTR) -> ATTRPattern:
        """Generate a pattern from a single ATTR by converting values to variables"""
        if attr.is_atomic():
            var_name = f"var_{attr.key}"
            pattern_attr = ATTR(attr.key, ATTRVariable(var_name))
            return ATTRPattern(pattern_attr)
        
        elif attr.is_nested():
            # Recursively generalize nested attributes
            generalized_nested = []
            for nested_attr in attr.value:
                nested_pattern = ATTRAlgebra._generalize_single(nested_attr)
                generalized_nested.append(nested_pattern.template)
            
            pattern_attr = ATTR(attr.key, generalized_nested)
            return ATTRPattern(pattern_attr)
        
        else:
            # Already a variable
            return ATTRPattern(attr)
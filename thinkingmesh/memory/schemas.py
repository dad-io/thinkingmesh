"""
Schema Cache: Emergent schemas via pattern folding

Stores and manages schemas that emerge from repeated patterns in the data.
Enables schema-based compression and structural reasoning.
"""

import time
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from ..attr.core import ATTR, ATTRPattern
from ..attr.algebra import ATTRAlgebra


@dataclass
class Schema:
    """
    An emergent schema discovered from data patterns
    
    Represents a structural template that captures common
    patterns across multiple ATTR observations
    """
    name: str
    template: ATTRPattern
    instances: List[ATTR]
    frequency: int
    compression_ratio: float
    discovered_at: float
    last_updated: float
    tags: Set[str]
    
    def __post_init__(self):
        if self.discovered_at is None:
            self.discovered_at = time.time()
        if self.last_updated is None:
            self.last_updated = self.discovered_at
        if self.tags is None:
            self.tags = set()
    
    def update_with_instance(self, instance: ATTR) -> None:
        """Update schema with a new matching instance"""
        self.instances.append(instance)
        self.frequency += 1
        self.last_updated = time.time()
        
        # Recalculate compression ratio
        self._update_compression_ratio()
    
    def _update_compression_ratio(self) -> None:
        """Update the compression ratio based on current instances"""
        if not self.instances:
            self.compression_ratio = 1.0
            return
        
        # Calculate size of individual instances vs. schema + instances
        individual_size = sum(len(str(instance)) for instance in self.instances)
        schema_size = len(str(self.template))
        
        # Simplified compression calculation
        if individual_size > 0:
            self.compression_ratio = schema_size / individual_size
        else:
            self.compression_ratio = 1.0


@dataclass
class SchemaEvolution:
    """Tracks how a schema evolves over time"""
    schema_name: str
    evolution_steps: List[Tuple[float, ATTRPattern]]  # (timestamp, pattern)
    
    def add_evolution_step(self, pattern: ATTRPattern) -> None:
        """Add a new evolution step"""
        self.evolution_steps.append((time.time(), pattern))


class SchemaCache:
    """
    Cache for emergent schemas discovered through pattern folding
    
    Provides:
    - Automatic schema discovery from repeated patterns
    - Schema evolution tracking
    - Compression-based schema evaluation
    - Schema-based data compression and decompression
    """
    
    def __init__(self, min_frequency: int = 3, max_schemas: int = 1000):
        self.schemas: Dict[str, Schema] = {}
        self.schema_evolution: Dict[str, SchemaEvolution] = {}
        self.pattern_frequency: Dict[str, int] = {}  # pattern signature -> frequency
        self.min_frequency = min_frequency
        self.max_schemas = max_schemas
        self._instance_to_schemas: Dict[str, List[str]] = {}  # instance signature -> schema names
    
    def discover_schema(self, instances: List[ATTR], schema_name: Optional[str] = None) -> Optional[Schema]:
        """
        Discover a schema from a collection of instances
        
        Args:
            instances: List of ATTR instances to analyze
            schema_name: Optional name for the schema
        
        Returns:
            Discovered schema or None if no pattern found
        """
        if len(instances) < self.min_frequency:
            return None
        
        # Generate pattern that generalizes the instances
        pattern = ATTRAlgebra.generalize_pattern(instances)
        if pattern is None:
            return None
        
        # Generate schema name if not provided
        if schema_name is None:
            pattern_sig = self._get_pattern_signature(pattern)
            schema_name = f"schema_{pattern_sig}_{int(time.time())}"
        
        # Calculate compression ratio
        individual_size = sum(len(str(instance)) for instance in instances)
        schema_size = len(str(pattern))
        compression_ratio = schema_size / individual_size if individual_size > 0 else 1.0
        
        # Create schema
        schema = Schema(
            name=schema_name,
            template=pattern,
            instances=instances.copy(),
            frequency=len(instances),
            compression_ratio=compression_ratio,
            discovered_at=time.time(),
            last_updated=time.time(),
            tags=set()
        )
        
        self.schemas[schema_name] = schema
        
        # Update pattern frequency tracking
        pattern_sig = self._get_pattern_signature(pattern)
        self.pattern_frequency[pattern_sig] = self.pattern_frequency.get(pattern_sig, 0) + len(instances)
        
        # Update instance tracking
        for instance in instances:
            instance_sig = self._get_instance_signature(instance)
            if instance_sig not in self._instance_to_schemas:
                self._instance_to_schemas[instance_sig] = []
            self._instance_to_schemas[instance_sig].append(schema_name)
        
        # Maintain cache size
        if len(self.schemas) > self.max_schemas:
            self._evict_least_useful_schema()
        
        return schema
    
    def find_matching_schemas(self, attr: ATTR) -> List[Tuple[Schema, dict]]:
        """
        Find schemas that match the given ATTR instance
        
        Args:
            attr: ATTR instance to match
        
        Returns:
            List of (schema, bindings) tuples for matching schemas
        """
        matches = []
        
        for schema in self.schemas.values():
            match_result = ATTRAlgebra.match_pattern(schema.template, attr)
            if match_result.success:
                matches.append((schema, match_result.bindings))
        
        # Sort by frequency (most frequent first)
        matches.sort(key=lambda x: x[0].frequency, reverse=True)
        return matches
    
    def update_schemas(self, new_instances: List[ATTR]) -> List[str]:
        """
        Update existing schemas with new instances
        
        Args:
            new_instances: New ATTR instances to process
        
        Returns:
            List of schema names that were updated
        """
        updated_schemas = []
        
        for instance in new_instances:
            matching_schemas = self.find_matching_schemas(instance)
            
            for schema, bindings in matching_schemas:
                schema.update_with_instance(instance)
                updated_schemas.append(schema.name)
                
                # Update instance tracking
                instance_sig = self._get_instance_signature(instance)
                if instance_sig not in self._instance_to_schemas:
                    self._instance_to_schemas[instance_sig] = []
                if schema.name not in self._instance_to_schemas[instance_sig]:
                    self._instance_to_schemas[instance_sig].append(schema.name)
        
        return list(set(updated_schemas))  # Remove duplicates
    
    def evolve_schema(self, schema_name: str, new_instances: List[ATTR]) -> bool:
        """
        Evolve an existing schema based on new instances
        
        Args:
            schema_name: Name of schema to evolve
            new_instances: New instances that might change the schema
        
        Returns:
            True if schema was evolved
        """
        if schema_name not in self.schemas:
            return False
        
        schema = self.schemas[schema_name]
        all_instances = schema.instances + new_instances
        
        # Generate new pattern from all instances
        new_pattern = ATTRAlgebra.generalize_pattern(all_instances)
        if new_pattern is None:
            return False
        
        # Check if pattern actually changed
        if str(new_pattern) == str(schema.template):
            # Pattern unchanged, just add instances
            for instance in new_instances:
                schema.update_with_instance(instance)
            return True
        
        # Track evolution
        if schema_name not in self.schema_evolution:
            self.schema_evolution[schema_name] = SchemaEvolution(schema_name, [])
        
        self.schema_evolution[schema_name].add_evolution_step(schema.template)
        
        # Update schema with new pattern
        schema.template = new_pattern
        for instance in new_instances:
            schema.update_with_instance(instance)
        
        return True
    
    def compress_instances(self, instances: List[ATTR]) -> Tuple[List[str], Dict[str, Schema]]:
        """
        Compress instances using existing schemas
        
        Args:
            instances: List of ATTR instances to compress
        
        Returns:
            Tuple of (schema_references, referenced_schemas)
        """
        schema_references = []
        referenced_schemas = {}
        
        for instance in instances:
            matching_schemas = self.find_matching_schemas(instance)
            
            if matching_schemas:
                # Use best matching schema (highest frequency)
                best_schema, bindings = matching_schemas[0]
                
                # Create compressed reference
                ref = f"{best_schema.name}({self._bindings_to_string(bindings)})"
                schema_references.append(ref)
                referenced_schemas[best_schema.name] = best_schema
            else:
                # No schema match - store as raw instance
                schema_references.append(f"raw({str(instance)})")
        
        return schema_references, referenced_schemas
    
    def get_schema_by_name(self, name: str) -> Optional[Schema]:
        """Get schema by name"""
        return self.schemas.get(name)
    
    def get_schemas_by_frequency(self, min_freq: int = 0) -> List[Schema]:
        """Get schemas filtered by minimum frequency"""
        return [
            schema for schema in self.schemas.values()
            if schema.frequency >= min_freq
        ]
    
    def get_most_compressive_schemas(self, limit: int = 10) -> List[Schema]:
        """Get schemas with best compression ratios"""
        sorted_schemas = sorted(
            self.schemas.values(),
            key=lambda s: s.compression_ratio
        )
        return sorted_schemas[:limit]
    
    def prune_ineffective_schemas(self, min_compression_ratio: float = 0.8, min_frequency: int = 2) -> int:
        """
        Remove schemas that don't provide good compression or are rarely used
        
        Args:
            min_compression_ratio: Minimum compression ratio to keep
            min_frequency: Minimum frequency to keep
        
        Returns:
            Number of schemas removed
        """
        schemas_to_remove = []
        
        for name, schema in self.schemas.items():
            if (schema.compression_ratio > min_compression_ratio or 
                schema.frequency < min_frequency):
                schemas_to_remove.append(name)
        
        # Remove schemas
        for name in schemas_to_remove:
            del self.schemas[name]
            
            # Clean up evolution tracking
            if name in self.schema_evolution:
                del self.schema_evolution[name]
            
            # Clean up instance tracking
            for instance_schemas in self._instance_to_schemas.values():
                if name in instance_schemas:
                    instance_schemas.remove(name)
        
        return len(schemas_to_remove)
    
    def _evict_least_useful_schema(self) -> None:
        """Evict the least useful schema when cache is full"""
        if not self.schemas:
            return
        
        # Find schema with worst combination of low frequency and poor compression
        worst_score = float('inf')
        worst_schema = None
        
        for name, schema in self.schemas.items():
            # Score combines frequency and compression (lower is worse)
            score = schema.frequency * (1 / max(schema.compression_ratio, 0.01))
            if score < worst_score:
                worst_score = score
                worst_schema = name
        
        if worst_schema:
            del self.schemas[worst_schema]
            
            # Clean up related data
            if worst_schema in self.schema_evolution:
                del self.schema_evolution[worst_schema]
    
    def _get_pattern_signature(self, pattern: ATTRPattern) -> str:
        """Generate a signature for a pattern"""
        return str(pattern)[:50]  # Use first 50 chars as signature
    
    def _get_instance_signature(self, instance: ATTR) -> str:
        """Generate a signature for an instance"""
        return str(instance)
    
    def _bindings_to_string(self, bindings: dict) -> str:
        """Convert bindings dictionary to string representation"""
        binding_pairs = [f"{k}={v}" for k, v in bindings.items()]
        return ",".join(binding_pairs)
    
    def get_statistics(self) -> dict:
        """Get schema cache statistics"""
        if not self.schemas:
            return {
                "total_schemas": 0,
                "average_frequency": 0.0,
                "average_compression_ratio": 0.0,
                "total_instances_covered": 0,
                "evolved_schemas": 0
            }
        
        total_schemas = len(self.schemas)
        total_instances = sum(len(schema.instances) for schema in self.schemas.values())
        avg_frequency = sum(schema.frequency for schema in self.schemas.values()) / total_schemas
        avg_compression = sum(schema.compression_ratio for schema in self.schemas.values()) / total_schemas
        evolved_schemas = len(self.schema_evolution)
        
        return {
            "total_schemas": total_schemas,
            "average_frequency": avg_frequency,
            "average_compression_ratio": avg_compression,
            "total_instances_covered": total_instances,
            "evolved_schemas": evolved_schemas,
            "cache_usage": f"{total_schemas}/{self.max_schemas}"
        }
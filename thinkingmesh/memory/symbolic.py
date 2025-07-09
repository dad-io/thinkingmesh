"""
SymbolicMemory: Unified interface to the symbolic memory architecture

Orchestrates all memory components and provides a high-level interface
for storing observations, discovering patterns, and executing queries.
"""

import time
from typing import Dict, List, Optional, Set, Tuple
from ..attr.core import ATTR, ATTRPattern, ATTRQuery, ATTRPath
from .episodic import EpisodicMemory
from .concepts import ConceptStore
from .working import WorkingMemory
from .schemas import SchemaCache
from .query import QueryEngine, QueryResult


class SymbolicMemory:
    """
    Unified symbolic memory system
    
    Integrates all memory components:
    - Episodic Memory: Time-indexed observations
    - Concept Store: Generalized patterns  
    - Working Memory: Active query context
    - Schema Cache: Emergent structural templates
    - Query Engine: Unified query interface
    """
    
    def __init__(self, 
                 max_episodic_entries: int = 10000,
                 max_working_entries: int = 100,
                 max_schemas: int = 1000):
        # Initialize memory components
        self.episodic_memory = EpisodicMemory(max_entries=max_episodic_entries)
        self.concept_store = ConceptStore()
        self.working_memory = WorkingMemory(max_entries=max_working_entries)
        self.schema_cache = SchemaCache(max_schemas=max_schemas)
        
        # Initialize query engine with all components
        self.query_engine = QueryEngine(
            self.episodic_memory,
            self.concept_store,
            self.working_memory,
            self.schema_cache
        )
        
        # Learning parameters
        self.auto_concept_discovery = True
        self.auto_schema_discovery = True
        self.compression_threshold = 0.8
        
        # Statistics
        self.stats = {
            "observations_stored": 0,
            "concepts_discovered": 0,
            "schemas_discovered": 0,
            "queries_executed": 0
        }
    
    def store_observation(self, attr: ATTR, source: Optional[str] = None) -> None:
        """
        Store a new observation in symbolic memory
        
        This is the primary input method for new data. The observation
        is stored in episodic memory and triggers pattern discovery.
        
        Args:
            attr: ATTR observation to store
            source: Optional source identifier
        """
        # Store in episodic memory
        self.episodic_memory.store(attr, source)
        self.stats["observations_stored"] += 1
        
        # Reinforce existing concepts
        if self.auto_concept_discovery:
            reinforced_concepts = self.concept_store.reinforce_concepts(attr)
            
            # Trigger concept discovery if no existing concepts matched
            if not reinforced_concepts:
                self._try_discover_concepts()
        
        # Update schemas
        if self.auto_schema_discovery:
            self._update_schemas([attr])
        
        # Periodic maintenance
        if self.stats["observations_stored"] % 100 == 0:
            self._periodic_maintenance()
    
    def query(self, pattern: ATTRPattern, conditions: Optional[List[str]] = None) -> QueryResult:
        """
        Execute a symbolic query
        
        Args:
            pattern: ATTR pattern to match
            conditions: Optional list of conditions to apply
        
        Returns:
            QueryResult with matches and metadata
        """
        query = ATTRQuery(pattern, conditions or [])
        result = self.query_engine.query(query)
        self.stats["queries_executed"] += 1
        return result
    
    def query_path(self, path_str: str, source_attr: Optional[ATTR] = None) -> QueryResult:
        """
        Execute a path-based query (e.g., "car.engine.rpm")
        
        Args:
            path_str: Dot-separated path string
            source_attr: Optional specific ATTR to search in
        
        Returns:
            QueryResult with resolved values
        """
        path = ATTRPath.parse(path_str)
        result = self.query_engine.path_query(path, source_attr)
        self.stats["queries_executed"] += 1
        return result
    
    def discover_concept(self, name: str, instances: List[ATTR]) -> bool:
        """
        Manually discover a concept from instances
        
        Args:
            name: Name for the new concept
            instances: List of ATTR instances to generalize
        
        Returns:
            True if concept was successfully created
        """
        concept = self.concept_store.create_concept(name, instances)
        if concept:
            self.stats["concepts_discovered"] += 1
            return True
        return False
    
    def discover_schema(self, name: str, instances: List[ATTR]) -> bool:
        """
        Manually discover a schema from instances
        
        Args:
            name: Name for the new schema
            instances: List of ATTR instances to analyze
        
        Returns:
            True if schema was successfully created
        """
        schema = self.schema_cache.discover_schema(instances, name)
        if schema:
            self.stats["schemas_discovered"] += 1
            return True
        return False
    
    def get_recent_observations(self, count: int = 10) -> List[ATTR]:
        """Get recent observations from episodic memory"""
        entries = self.episodic_memory.get_recent(count)
        return [entry.attr for entry in entries]
    
    def get_concepts(self, min_confidence: float = 0.0) -> List[str]:
        """Get concept names filtered by confidence"""
        concepts = self.concept_store.get_concepts_by_confidence(min_confidence)
        return [concept.name for concept in concepts]
    
    def get_schemas(self, min_frequency: int = 0) -> List[str]:
        """Get schema names filtered by frequency"""
        schemas = self.schema_cache.get_schemas_by_frequency(min_freq=min_frequency)
        return [schema.name for schema in schemas]
    
    def compress_memory(self) -> Dict[str, int]:
        """
        Compress memory by removing redundancy
        
        Returns:
            Dictionary with compression statistics
        """
        stats = {}
        
        # Compress episodic memory
        episodic_removed = self.episodic_memory.compress_similar(self.compression_threshold)
        stats["episodic_entries_removed"] = episodic_removed
        
        # Prune weak concepts
        concepts_removed = self.concept_store.prune_weak_concepts()
        stats["concepts_removed"] = concepts_removed
        
        # Prune ineffective schemas  
        schemas_removed = self.schema_cache.prune_ineffective_schemas()
        stats["schemas_removed"] = schemas_removed
        
        # Clean up working memory
        working_cleaned = self.working_memory.cleanup_expired()
        stats["working_memory_cleaned"] = working_cleaned
        
        return stats
    
    def _try_discover_concepts(self) -> None:
        """Try to discover new concepts from recent observations"""
        recent_obs = self.get_recent_observations(50)  # Look at recent 50 observations
        
        if len(recent_obs) < 3:
            return
        
        # Get suggestions for new concepts
        suggestions = self.concept_store.suggest_new_concepts(recent_obs, min_instances=3)
        
        for suggested_name in suggestions:
            # Group observations by key for this suggestion
            key = suggested_name.split('_')[1]  # Extract key from suggested name
            matching_obs = [obs for obs in recent_obs if obs.key == key]
            
            if len(matching_obs) >= 3:
                concept = self.concept_store.create_concept(suggested_name, matching_obs)
                if concept:
                    self.stats["concepts_discovered"] += 1
    
    def _update_schemas(self, new_instances: List[ATTR]) -> None:
        """Update schemas with new instances"""
        updated_schemas = self.schema_cache.update_schemas(new_instances)
        
        # Try to discover new schemas if no existing schemas were updated
        if not updated_schemas and len(new_instances) >= 3:
            schema = self.schema_cache.discover_schema(new_instances)
            if schema:
                self.stats["schemas_discovered"] += 1
    
    def _periodic_maintenance(self) -> None:
        """Perform periodic maintenance tasks"""
        # Clean up expired working memory
        self.working_memory.cleanup_expired()
        
        # Compress memory if it's getting full
        episodic_stats = self.episodic_memory.get_statistics()
        if episodic_stats["total_entries"] > episodic_stats.get("max_entries", 10000) * 0.9:
            self.compress_memory()
    
    def get_memory_statistics(self) -> Dict[str, any]:
        """Get comprehensive memory statistics"""
        return {
            "overview": self.stats.copy(),
            "episodic_memory": self.episodic_memory.get_statistics(),
            "concept_store": self.concept_store.get_concept_statistics(),
            "working_memory": self.working_memory.get_statistics(),
            "schema_cache": self.schema_cache.get_statistics(),
            "query_engine": self.query_engine.get_statistics()
        }
    
    def export_knowledge(self) -> Dict[str, any]:
        """
        Export current knowledge state
        
        Returns:
            Dictionary containing all discoverable knowledge
        """
        return {
            "concepts": {
                name: {
                    "pattern": str(concept.pattern),
                    "instances_count": len(concept.instances),
                    "confidence": concept.confidence
                }
                for name, concept in self.concept_store.concepts.items()
            },
            "schemas": {
                name: {
                    "template": str(schema.template),
                    "frequency": schema.frequency,
                    "compression_ratio": schema.compression_ratio
                }
                for name, schema in self.schema_cache.schemas.items()
            },
            "statistics": self.get_memory_statistics()
        }
    
    def reset(self) -> None:
        """Reset all memory components"""
        self.episodic_memory = EpisodicMemory()
        self.concept_store = ConceptStore()
        self.working_memory = WorkingMemory()
        self.schema_cache = SchemaCache()
        
        # Reinitialize query engine
        self.query_engine = QueryEngine(
            self.episodic_memory,
            self.concept_store,
            self.working_memory,
            self.schema_cache
        )
        
        # Reset statistics
        self.stats = {
            "observations_stored": 0,
            "concepts_discovered": 0,
            "schemas_discovered": 0,
            "queries_executed": 0
        }
"""
Working Memory: Query context and partial bindings

Maintains active query state, partial variable bindings, and intermediate
reasoning results during symbolic processing.
"""

import time
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass
from ..attr.core import ATTR, ATTRPattern, ATTRQuery, ATTRVariable, ATTRValue


@dataclass
class WorkingMemoryEntry:
    """Entry in working memory with context and bindings"""
    query_id: str
    pattern: ATTRPattern
    bindings: Dict[str, ATTRValue]
    partial_matches: List[ATTR]
    created_at: float
    last_accessed: float
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
        if self.last_accessed is None:
            self.last_accessed = self.created_at


@dataclass
class QueryContext:
    """Context for an active query operation"""
    query_id: str
    original_query: ATTRQuery
    current_step: int
    max_steps: int
    intermediate_results: List[Dict[str, ATTRValue]]
    started_at: float
    timeout_seconds: float
    
    def is_expired(self) -> bool:
        """Check if this query context has expired"""
        return time.time() - self.started_at > self.timeout_seconds
    
    def add_result(self, bindings: Dict[str, ATTRValue]) -> None:
        """Add intermediate result to query context"""
        self.intermediate_results.append(bindings.copy())
        self.current_step += 1
    
    def is_complete(self) -> bool:
        """Check if query has reached completion"""
        return self.current_step >= self.max_steps


class WorkingMemory:
    """
    Working memory for active query processing
    
    Provides:
    - Active query context management
    - Partial variable binding storage
    - Intermediate result tracking
    - Query state persistence across reasoning steps
    """
    
    def __init__(self, max_entries: int = 100, default_timeout: float = 300.0):
        self.entries: Dict[str, WorkingMemoryEntry] = {}
        self.query_contexts: Dict[str, QueryContext] = {}
        self.global_bindings: Dict[str, ATTRValue] = {}  # Cross-query persistent bindings
        self.max_entries = max_entries
        self.default_timeout = default_timeout
    
    def create_query_context(self, query: ATTRQuery, max_steps: int = 10, timeout: Optional[float] = None) -> str:
        """
        Create a new query context for multi-step reasoning
        
        Args:
            query: The ATTR query to process
            max_steps: Maximum reasoning steps
            timeout: Query timeout in seconds
        
        Returns:
            Query ID for tracking this context
        """
        query_id = f"query_{int(time.time() * 1000000)}"
        
        context = QueryContext(
            query_id=query_id,
            original_query=query,
            current_step=0,
            max_steps=max_steps,
            intermediate_results=[],
            started_at=time.time(),
            timeout_seconds=timeout or self.default_timeout
        )
        
        self.query_contexts[query_id] = context
        return query_id
    
    def get_query_context(self, query_id: str) -> Optional[QueryContext]:
        """Get query context by ID"""
        context = self.query_contexts.get(query_id)
        if context and context.is_expired():
            # Clean up expired context
            del self.query_contexts[query_id]
            return None
        return context
    
    def update_bindings(self, query_id: str, new_bindings: Dict[str, ATTRValue]) -> bool:
        """
        Update variable bindings for a query
        
        Args:
            query_id: Query ID
            new_bindings: New variable bindings to add/update
        
        Returns:
            True if update was successful
        """
        if query_id not in self.entries:
            return False
        
        entry = self.entries[query_id]
        entry.bindings.update(new_bindings)
        entry.last_accessed = time.time()
        
        # Also update query context if it exists
        if query_id in self.query_contexts:
            context = self.query_contexts[query_id]
            context.add_result(new_bindings)
        
        return True
    
    def add_partial_match(self, query_id: str, match: ATTR) -> bool:
        """
        Add a partial match to working memory
        
        Args:
            query_id: Query ID
            match: Partially matching ATTR structure
        
        Returns:
            True if added successfully
        """
        if query_id not in self.entries:
            return False
        
        entry = self.entries[query_id]
        entry.partial_matches.append(match)
        entry.last_accessed = time.time()
        return True
    
    def create_entry(self, query_id: str, pattern: ATTRPattern, initial_bindings: Optional[Dict[str, ATTRValue]] = None) -> WorkingMemoryEntry:
        """
        Create a new working memory entry
        
        Args:
            query_id: Unique query identifier
            pattern: ATTR pattern being processed
            initial_bindings: Optional initial variable bindings
        
        Returns:
            Created working memory entry
        """
        if initial_bindings is None:
            initial_bindings = {}
        
        entry = WorkingMemoryEntry(
            query_id=query_id,
            pattern=pattern,
            bindings=initial_bindings.copy(),
            partial_matches=[],
            created_at=time.time(),
            last_accessed=time.time()
        )
        
        self.entries[query_id] = entry
        
        # Maintain size limit
        if len(self.entries) > self.max_entries:
            self._evict_oldest()
        
        return entry
    
    def get_entry(self, query_id: str) -> Optional[WorkingMemoryEntry]:
        """Get working memory entry by query ID"""
        entry = self.entries.get(query_id)
        if entry:
            entry.last_accessed = time.time()
        return entry
    
    def get_bindings(self, query_id: str) -> Dict[str, ATTRValue]:
        """Get current variable bindings for a query"""
        entry = self.entries.get(query_id)
        if entry:
            entry.last_accessed = time.time()
            return entry.bindings.copy()
        return {}
    
    def set_global_binding(self, variable: str, value: ATTRValue) -> None:
        """
        Set a global binding that persists across queries
        
        Args:
            variable: Variable name (without ? prefix)
            value: Value to bind to variable
        """
        self.global_bindings[variable] = value
    
    def get_global_binding(self, variable: str) -> Optional[ATTRValue]:
        """Get a global binding value"""
        return self.global_bindings.get(variable)
    
    def resolve_variable(self, query_id: str, variable: str) -> Optional[ATTRValue]:
        """
        Resolve a variable from query-local or global bindings
        
        Args:
            query_id: Query ID to check for local bindings
            variable: Variable name to resolve
        
        Returns:
            Resolved value or None if not bound
        """
        # Check query-local bindings first
        entry = self.entries.get(query_id)
        if entry and variable in entry.bindings:
            return entry.bindings[variable]
        
        # Check global bindings
        return self.global_bindings.get(variable)
    
    def substitute_variables(self, query_id: str, attr: ATTR) -> ATTR:
        """
        Substitute bound variables in an ATTR structure
        
        Args:
            query_id: Query ID for context
            attr: ATTR structure potentially containing variables
        
        Returns:
            ATTR structure with variables substituted
        """
        if attr.is_variable():
            var_name = attr.value.name
            bound_value = self.resolve_variable(query_id, var_name)
            if bound_value:
                return ATTR(attr.key, bound_value, attr.timestamp)
            return attr
        
        elif attr.is_nested():
            substituted_nested = []
            for nested_attr in attr.value:
                substituted_nested.append(self.substitute_variables(query_id, nested_attr))
            return ATTR(attr.key, substituted_nested, attr.timestamp)
        
        else:
            # Atomic value - no substitution needed
            return attr
    
    def find_unbound_variables(self, query_id: str, pattern: ATTRPattern) -> Set[str]:
        """
        Find variables in pattern that are not yet bound
        
        Args:
            query_id: Query ID for context
            pattern: Pattern to analyze
        
        Returns:
            Set of unbound variable names
        """
        all_variables = pattern.extract_variables()
        unbound = set()
        
        for var in all_variables:
            if self.resolve_variable(query_id, var) is None:
                unbound.add(var)
        
        return unbound
    
    def cleanup_expired(self) -> int:
        """
        Remove expired entries and query contexts
        
        Returns:
            Number of items cleaned up
        """
        current_time = time.time()
        cleanup_count = 0
        
        # Clean up expired query contexts
        expired_contexts = [
            query_id for query_id, context in self.query_contexts.items()
            if context.is_expired()
        ]
        
        for query_id in expired_contexts:
            del self.query_contexts[query_id]
            cleanup_count += 1
        
        # Clean up old working memory entries (older than 1 hour)
        max_age = 3600  # 1 hour
        expired_entries = [
            query_id for query_id, entry in self.entries.items()
            if current_time - entry.last_accessed > max_age
        ]
        
        for query_id in expired_entries:
            del self.entries[query_id]
            cleanup_count += 1
        
        return cleanup_count
    
    def _evict_oldest(self) -> None:
        """Evict oldest entry when memory is full"""
        if not self.entries:
            return
        
        oldest_query_id = min(
            self.entries.keys(),
            key=lambda qid: self.entries[qid].last_accessed
        )
        
        del self.entries[oldest_query_id]
    
    def get_active_queries(self) -> List[QueryContext]:
        """Get all active query contexts"""
        # Clean up expired contexts first
        self.cleanup_expired()
        return list(self.query_contexts.values())
    
    def get_statistics(self) -> dict:
        """Get working memory statistics"""
        active_queries = len(self.query_contexts)
        total_entries = len(self.entries)
        global_bindings_count = len(self.global_bindings)
        
        if self.entries:
            total_bindings = sum(len(entry.bindings) for entry in self.entries.values())
            total_partial_matches = sum(len(entry.partial_matches) for entry in self.entries.values())
        else:
            total_bindings = 0
            total_partial_matches = 0
        
        return {
            "active_queries": active_queries,
            "total_entries": total_entries,
            "global_bindings": global_bindings_count,
            "total_local_bindings": total_bindings,
            "total_partial_matches": total_partial_matches,
            "memory_usage": f"{total_entries}/{self.max_entries}"
        }
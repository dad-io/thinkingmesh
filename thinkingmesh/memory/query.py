"""
Query Engine: Unification, filtering, and recall

Orchestrates symbolic queries across all memory components,
providing unified access to episodic, conceptual, and schematic knowledge.
"""

import time
from typing import Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass
from ..attr.core import ATTR, ATTRPattern, ATTRQuery, ATTRPath
from ..attr.algebra import ATTRAlgebra, UnificationResult
from .episodic import EpisodicMemory
from .concepts import ConceptStore, Concept
from .working import WorkingMemory
from .schemas import SchemaCache, Schema


@dataclass
class QueryResult:
    """Result of a symbolic query operation"""
    success: bool
    matches: List[ATTR]
    bindings: List[Dict[str, any]]
    concepts_activated: List[str]
    schemas_used: List[str]
    execution_time: float
    query_id: str
    
    def get_best_match(self) -> Optional[ATTR]:
        """Get the best matching result"""
        return self.matches[0] if self.matches else None
    
    def get_all_bindings(self) -> Dict[str, Set[any]]:
        """Get all unique bindings across all matches"""
        all_bindings = {}
        for binding_dict in self.bindings:
            for var, value in binding_dict.items():
                if var not in all_bindings:
                    all_bindings[var] = set()
                all_bindings[var].add(value)
        return all_bindings


@dataclass
class QueryPlan:
    """Execution plan for complex queries"""
    query_id: str
    original_query: ATTRQuery
    steps: List[str]  # Description of each step
    estimated_cost: float
    
    def add_step(self, description: str, cost: float = 1.0) -> None:
        """Add a step to the query plan"""
        self.steps.append(description)
        self.estimated_cost += cost


class QueryEngine:
    """
    Unified query engine for symbolic memory
    
    Orchestrates queries across:
    - Episodic memory (time-indexed observations)
    - Concept store (generalized patterns)
    - Schema cache (structural templates)
    - Working memory (active context)
    """
    
    def __init__(self, 
                 episodic_memory: EpisodicMemory,
                 concept_store: ConceptStore,
                 working_memory: WorkingMemory,
                 schema_cache: SchemaCache):
        self.episodic_memory = episodic_memory
        self.concept_store = concept_store
        self.working_memory = working_memory
        self.schema_cache = schema_cache
        self.query_statistics = {
            "total_queries": 0,
            "successful_queries": 0,
            "average_execution_time": 0.0
        }
    
    def query(self, query: ATTRQuery, use_concepts: bool = True, use_schemas: bool = True) -> QueryResult:
        """
        Execute a symbolic query across all memory components
        
        Args:
            query: ATTR query to execute
            use_concepts: Whether to use concept store
            use_schemas: Whether to use schema cache
        
        Returns:
            QueryResult with matches and metadata
        """
        start_time = time.time()
        query_id = self.working_memory.create_query_context(query)
        
        matches = []
        all_bindings = []
        concepts_activated = []
        schemas_used = []
        
        try:
            # Phase 1: Direct episodic memory search
            episodic_matches = self._search_episodic(query.pattern, query_id)
            matches.extend([match for match, bindings in episodic_matches])
            all_bindings.extend([bindings for match, bindings in episodic_matches])
            
            # Phase 2: Concept-based search
            if use_concepts:
                concept_matches, activated_concepts = self._search_concepts(query.pattern, query_id)
                matches.extend([match for match, bindings in concept_matches])
                all_bindings.extend([bindings for match, bindings in concept_matches])
                concepts_activated.extend(activated_concepts)
            
            # Phase 3: Schema-based search and expansion
            if use_schemas:
                schema_matches, used_schemas = self._search_schemas(query.pattern, query_id)
                matches.extend([match for match, bindings in schema_matches])
                all_bindings.extend([bindings for match, bindings in schema_matches])
                schemas_used.extend(used_schemas)
            
            # Phase 4: Apply query conditions/constraints
            if query.conditions:
                matches, all_bindings = self._apply_conditions(matches, all_bindings, query.conditions, query_id)
            
            # Remove duplicates while preserving order
            unique_matches = []
            unique_bindings = []
            seen_matches = set()
            
            for i, match in enumerate(matches):
                match_str = str(match)
                if match_str not in seen_matches:
                    unique_matches.append(match)
                    unique_bindings.append(all_bindings[i] if i < len(all_bindings) else {})
                    seen_matches.add(match_str)
            
            execution_time = time.time() - start_time
            success = len(unique_matches) > 0
            
            # Update statistics
            self.query_statistics["total_queries"] += 1
            if success:
                self.query_statistics["successful_queries"] += 1
            
            # Update average execution time
            total_time = (self.query_statistics["average_execution_time"] * 
                         (self.query_statistics["total_queries"] - 1) + execution_time)
            self.query_statistics["average_execution_time"] = total_time / self.query_statistics["total_queries"]
            
            return QueryResult(
                success=success,
                matches=unique_matches,
                bindings=unique_bindings,
                concepts_activated=list(set(concepts_activated)),
                schemas_used=list(set(schemas_used)),
                execution_time=execution_time,
                query_id=query_id
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            # Return empty result on error
            return QueryResult(
                success=False,
                matches=[],
                bindings=[],
                concepts_activated=[],
                schemas_used=[],
                execution_time=execution_time,
                query_id=query_id
            )
    
    def _search_episodic(self, pattern: ATTRPattern, query_id: str) -> List[Tuple[ATTR, dict]]:
        """Search episodic memory for pattern matches"""
        return self.episodic_memory.search_pattern(pattern)
    
    def _search_concepts(self, pattern: ATTRPattern, query_id: str) -> Tuple[List[Tuple[ATTR, dict]], List[str]]:
        """Search concept store and return matches from concept instances"""
        matches = []
        activated_concepts = []
        
        # Find concepts that might contain relevant instances
        for concept in self.concept_store.get_all_concepts():
            # Check if concept pattern is compatible with query pattern
            compatibility_result = ATTRAlgebra.unify(pattern.template, concept.pattern.template)
            
            if compatibility_result.success:
                activated_concepts.append(concept.name)
                
                # Search instances within this concept
                for instance in concept.instances:
                    match_result = ATTRAlgebra.match_pattern(pattern, instance)
                    if match_result.success:
                        matches.append((instance, match_result.bindings))
        
        return matches, activated_concepts
    
    def _search_schemas(self, pattern: ATTRPattern, query_id: str) -> Tuple[List[Tuple[ATTR, dict]], List[str]]:
        """Search schema cache and expand compressed instances"""
        matches = []
        used_schemas = []
        
        # Find schemas that match the pattern
        matching_schemas = self.schema_cache.find_matching_schemas(pattern.template)
        
        for schema, schema_bindings in matching_schemas:
            used_schemas.append(schema.name)
            
            # Search instances within this schema
            for instance in schema.instances:
                match_result = ATTRAlgebra.match_pattern(pattern, instance)
                if match_result.success:
                    matches.append((instance, match_result.bindings))
        
        return matches, used_schemas
    
    def _apply_conditions(self, matches: List[ATTR], bindings: List[dict], conditions: List[str], query_id: str) -> Tuple[List[ATTR], List[dict]]:
        """Apply query conditions to filter results"""
        filtered_matches = []
        filtered_bindings = []
        
        for i, (match, binding) in enumerate(zip(matches, bindings)):
            if self._evaluate_conditions(conditions, binding):
                filtered_matches.append(match)
                filtered_bindings.append(binding)
        
        return filtered_matches, filtered_bindings
    
    def _evaluate_conditions(self, conditions: List[str], bindings: dict) -> bool:
        """Evaluate query conditions against variable bindings"""
        for condition in conditions:
            if not self._evaluate_single_condition(condition, bindings):
                return False
        return True
    
    def _evaluate_single_condition(self, condition: str, bindings: dict) -> bool:
        """Evaluate a single condition"""
        # Simplified condition evaluation
        # In practice, would use a proper expression parser
        
        condition = condition.strip()
        
        # Handle comparison operators
        for op in [" >= ", " <= ", " > ", " < ", " = ", " != "]:
            if op in condition:
                left, right = condition.split(op, 1)
                left, right = left.strip(), right.strip()
                
                # Resolve variables
                if left.startswith("?") and left[1:] in bindings:
                    left_val = bindings[left[1:]]
                    if hasattr(left_val, 'value'):  # ATTRAtom
                        left_val = left_val.value
                else:
                    continue  # Can't evaluate without variable binding
                
                # Parse right side
                try:
                    if right.startswith('"') and right.endswith('"'):
                        right_val = right[1:-1]  # String literal
                    else:
                        right_val = float(right)  # Numeric literal
                except ValueError:
                    continue  # Can't parse right side
                
                # Evaluate comparison
                if op.strip() == ">":
                    return left_val > right_val
                elif op.strip() == "<":
                    return left_val < right_val
                elif op.strip() == ">=":
                    return left_val >= right_val
                elif op.strip() == "<=":
                    return left_val <= right_val
                elif op.strip() == "=":
                    return left_val == right_val
                elif op.strip() == "!=":
                    return left_val != right_val
        
        return True  # Default to true for unrecognized conditions
    
    def create_query_plan(self, query: ATTRQuery) -> QueryPlan:
        """
        Create an execution plan for a complex query
        
        Args:
            query: ATTR query to plan
        
        Returns:
            QueryPlan with estimated steps and costs
        """
        plan = QueryPlan(
            query_id=f"plan_{int(time.time() * 1000000)}",
            original_query=query,
            steps=[],
            estimated_cost=0.0
        )
        
        # Analyze query complexity
        variables = query.pattern.extract_variables()
        has_conditions = bool(query.conditions)
        
        # Plan episodic search
        plan.add_step("Search episodic memory for direct matches", 1.0)
        
        # Plan concept search if beneficial
        if len(variables) > 0:
            plan.add_step("Search concept store for pattern matches", 2.0)
        
        # Plan schema search for structural matches
        plan.add_step("Search schema cache for structural matches", 1.5)
        
        # Plan condition evaluation
        if has_conditions:
            plan.add_step(f"Apply {len(query.conditions)} conditions to filter results", 
                         0.5 * len(query.conditions))
        
        return plan
    
    def path_query(self, path: ATTRPath, source_attr: Optional[ATTR] = None) -> QueryResult:
        """
        Execute a path-based query (e.g., car.engine.rpm)
        
        Args:
            path: ATTRPath to resolve
            source_attr: Optional specific ATTR to search in
        
        Returns:
            QueryResult with resolved values
        """
        start_time = time.time()
        query_id = f"path_query_{int(time.time() * 1000000)}"
        
        matches = []
        bindings = []
        
        if source_attr:
            # Search in specific ATTR
            result = path.resolve(source_attr)
            if result:
                matches.append(source_attr)
                bindings.append({})
        else:
            # Search across all episodic memory
            for entry in self.episodic_memory.get_recent(1000):  # Search recent entries
                result = path.resolve(entry.attr)
                if result:
                    matches.append(entry.attr)
                    bindings.append({})
        
        execution_time = time.time() - start_time
        
        return QueryResult(
            success=len(matches) > 0,
            matches=matches,
            bindings=bindings,
            concepts_activated=[],
            schemas_used=[],
            execution_time=execution_time,
            query_id=query_id
        )
    
    def get_statistics(self) -> dict:
        """Get query engine statistics"""
        return self.query_statistics.copy()
"""
Concept Store: Generalized patterns and higher-order symbolic concepts

Stores folded structures that represent abstractions and generalizations
discovered from episodic observations. Enables schema-emergent reasoning.
"""

from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
import time
from ..attr.core import ATTR, ATTRPattern
from ..attr.algebra import ATTRAlgebra


@dataclass
class Concept:
    """
    A generalized concept extracted from patterns
    
    Represents a higher-order symbolic structure that captures
    common patterns across multiple observations
    """
    name: str
    pattern: ATTRPattern
    instances: List[ATTR]
    confidence: float
    created_at: float
    last_reinforced: float
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
        if self.last_reinforced is None:
            self.last_reinforced = self.created_at
    
    def reinforce(self, new_instance: ATTR) -> None:
        """Reinforce this concept with a new matching instance"""
        self.instances.append(new_instance)
        self.last_reinforced = time.time()
        
        # Update confidence based on instance count
        self.confidence = min(1.0, len(self.instances) / 10.0)  # Max confidence at 10 instances
    
    def get_generalization_strength(self) -> float:
        """Calculate how well this concept generalizes"""
        if len(self.instances) < 2:
            return 0.0
        
        # Simple measure: number of variables in pattern vs total pattern size
        variables = self.pattern.extract_variables()
        # This is a simplified calculation - in practice would be more sophisticated
        return len(variables) / max(1, len(str(self.pattern)))


class ConceptStore:
    """
    Storage and management of generalized concepts
    
    Provides:
    - Pattern-based concept creation
    - Concept reinforcement and evolution
    - Hierarchical concept organization
    - Concept-based reasoning and inference
    """
    
    def __init__(self):
        self.concepts: Dict[str, Concept] = {}
        self.concept_hierarchy: Dict[str, Set[str]] = {}  # parent -> children
        self.instance_to_concepts: Dict[str, Set[str]] = {}  # instance signature -> concept names
    
    def create_concept(self, name: str, instances: List[ATTR], min_confidence: float = 0.5) -> Optional[Concept]:
        """
        Create a new concept from a set of instances
        
        Args:
            name: Name for the new concept
            instances: List of ATTR instances to generalize
            min_confidence: Minimum confidence threshold for concept creation
        
        Returns:
            Created concept or None if generalization failed
        """
        if len(instances) < 2:
            return None
        
        # Generate pattern that generalizes the instances
        pattern = ATTRAlgebra.generalize_pattern(instances)
        if pattern is None:
            return None
        
        # Calculate initial confidence
        confidence = min(1.0, len(instances) / 5.0)  # Confidence increases with more instances
        
        if confidence < min_confidence:
            return None
        
        concept = Concept(
            name=name,
            pattern=pattern,
            instances=instances.copy(),
            confidence=confidence,
            created_at=time.time(),
            last_reinforced=time.time()
        )
        
        self.concepts[name] = concept
        
        # Update instance tracking
        for instance in instances:
            instance_sig = self._get_instance_signature(instance)
            if instance_sig not in self.instance_to_concepts:
                self.instance_to_concepts[instance_sig] = set()
            self.instance_to_concepts[instance_sig].add(name)
        
        return concept
    
    def find_matching_concepts(self, attr: ATTR) -> List[Tuple[Concept, dict]]:
        """
        Find concepts that match the given ATTR instance
        
        Args:
            attr: ATTR instance to match against concepts
        
        Returns:
            List of (concept, bindings) tuples for matching concepts
        """
        matches = []
        
        for concept in self.concepts.values():
            match_result = ATTRAlgebra.match_pattern(concept.pattern, attr)
            if match_result.success:
                matches.append((concept, match_result.bindings))
        
        # Sort by confidence (most confident first)
        matches.sort(key=lambda x: x[0].confidence, reverse=True)
        return matches
    
    def reinforce_concepts(self, attr: ATTR) -> List[str]:
        """
        Reinforce existing concepts with a new instance
        
        Args:
            attr: New ATTR instance that might reinforce existing concepts
        
        Returns:
            List of concept names that were reinforced
        """
        reinforced = []
        
        matching_concepts = self.find_matching_concepts(attr)
        for concept, bindings in matching_concepts:
            concept.reinforce(attr)
            reinforced.append(concept.name)
            
            # Update instance tracking
            instance_sig = self._get_instance_signature(attr)
            if instance_sig not in self.instance_to_concepts:
                self.instance_to_concepts[instance_sig] = set()
            self.instance_to_concepts[instance_sig].add(concept.name)
        
        return reinforced
    
    def suggest_new_concepts(self, recent_instances: List[ATTR], min_instances: int = 3) -> List[str]:
        """
        Suggest new concepts based on patterns in recent instances
        
        Args:
            recent_instances: Recent ATTR observations
            min_instances: Minimum instances required to suggest a concept
        
        Returns:
            List of suggested concept names
        """
        suggestions = []
        
        if len(recent_instances) < min_instances:
            return suggestions
        
        # Group instances by key for pattern detection
        key_groups = {}
        for instance in recent_instances:
            key = instance.key
            if key not in key_groups:
                key_groups[key] = []
            key_groups[key].append(instance)
        
        # Look for groups with enough instances to form concepts
        for key, instances in key_groups.items():
            if len(instances) >= min_instances:
                # Check if we already have a concept for this pattern
                existing_matches = []
                for instance in instances[:2]:  # Check first two instances
                    matches = self.find_matching_concepts(instance)
                    existing_matches.extend([m[0].name for m in matches])
                
                if not existing_matches:  # No existing concept covers these instances
                    suggested_name = f"concept_{key}_{int(time.time())}"
                    suggestions.append(suggested_name)
        
        return suggestions
    
    def create_hierarchical_concept(self, parent_name: str, child_concepts: List[str]) -> Optional[Concept]:
        """
        Create a hierarchical concept that generalizes multiple child concepts
        
        Args:
            parent_name: Name for the parent concept
            child_concepts: List of child concept names to generalize
        
        Returns:
            Created parent concept or None if failed
        """
        if len(child_concepts) < 2:
            return None
        
        # Collect all instances from child concepts
        all_instances = []
        for child_name in child_concepts:
            if child_name in self.concepts:
                all_instances.extend(self.concepts[child_name].instances)
        
        if len(all_instances) < 2:
            return None
        
        # Create parent concept
        parent_concept = self.create_concept(parent_name, all_instances)
        if parent_concept:
            # Update hierarchy
            self.concept_hierarchy[parent_name] = set(child_concepts)
            
            # Mark child concepts as having this parent
            for child_name in child_concepts:
                if child_name in self.concepts:
                    # Could add parent reference to child concept if needed
                    pass
        
        return parent_concept
    
    def get_concept_by_name(self, name: str) -> Optional[Concept]:
        """Get a concept by name"""
        return self.concepts.get(name)
    
    def get_all_concepts(self) -> List[Concept]:
        """Get all stored concepts"""
        return list(self.concepts.values())
    
    def get_concepts_by_confidence(self, min_confidence: float = 0.0) -> List[Concept]:
        """Get concepts filtered by minimum confidence"""
        return [
            concept for concept in self.concepts.values()
            if concept.confidence >= min_confidence
        ]
    
    def prune_weak_concepts(self, min_confidence: float = 0.3, max_age_hours: float = 24.0) -> int:
        """
        Remove concepts that are weak or too old
        
        Args:
            min_confidence: Minimum confidence to keep concept
            max_age_hours: Maximum age in hours before considering for pruning
        
        Returns:
            Number of concepts removed
        """
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        concepts_to_remove = []
        
        for name, concept in self.concepts.items():
            age = current_time - concept.created_at
            
            # Remove if low confidence and old, or very low confidence
            if (concept.confidence < min_confidence and age > max_age_seconds) or concept.confidence < 0.1:
                concepts_to_remove.append(name)
        
        # Remove concepts
        for name in concepts_to_remove:
            del self.concepts[name]
            
            # Clean up hierarchy references
            if name in self.concept_hierarchy:
                del self.concept_hierarchy[name]
            
            # Clean up instance tracking
            for instance_concepts in self.instance_to_concepts.values():
                instance_concepts.discard(name)
        
        return len(concepts_to_remove)
    
    def _get_instance_signature(self, attr: ATTR) -> str:
        """Generate a signature string for an ATTR instance"""
        # Simple signature based on structure
        return str(attr)
    
    def get_concept_statistics(self) -> dict:
        """Get statistics about the concept store"""
        if not self.concepts:
            return {
                "total_concepts": 0,
                "average_confidence": 0.0,
                "total_instances": 0,
                "hierarchical_concepts": 0
            }
        
        total_concepts = len(self.concepts)
        total_instances = sum(len(concept.instances) for concept in self.concepts.values())
        avg_confidence = sum(concept.confidence for concept in self.concepts.values()) / total_concepts
        hierarchical_concepts = len(self.concept_hierarchy)
        
        return {
            "total_concepts": total_concepts,
            "average_confidence": avg_confidence,
            "total_instances": total_instances,
            "hierarchical_concepts": hierarchical_concepts,
            "concepts_by_confidence": {
                "high (>0.8)": len([c for c in self.concepts.values() if c.confidence > 0.8]),
                "medium (0.5-0.8)": len([c for c in self.concepts.values() if 0.5 <= c.confidence <= 0.8]),
                "low (<0.5)": len([c for c in self.concepts.values() if c.confidence < 0.5])
            }
        }
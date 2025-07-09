"""
Episodic Memory: Time-indexed storage of ATTR observations

Stores raw observations as they occur, maintaining temporal ordering
and enabling time-based queries and pattern discovery.
"""

import time
from typing import List, Optional, Iterator, Tuple
from dataclasses import dataclass
from ..attr.core import ATTR, ATTRPattern
from ..attr.algebra import ATTRAlgebra


@dataclass
class EpisodicEntry:
    """Single entry in episodic memory"""
    attr: ATTR
    timestamp: float
    source: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


class EpisodicMemory:
    """
    Time-indexed storage of ATTR observations
    
    Provides:
    - Chronological storage of observations
    - Time-based retrieval and filtering
    - Pattern-based search across temporal data
    - Memory consolidation and compression
    """
    
    def __init__(self, max_entries: int = 10000):
        self.entries: List[EpisodicEntry] = []
        self.max_entries = max_entries
        self._index_by_key: dict[str, List[int]] = {}  # key -> list of entry indices
    
    def store(self, attr: ATTR, source: Optional[str] = None) -> None:
        """
        Store an ATTR observation in episodic memory
        
        Args:
            attr: The ATTR structure to store
            source: Optional source identifier (e.g., sensor ID, agent name)
        """
        timestamp = attr.timestamp if attr.timestamp else time.time()
        entry = EpisodicEntry(attr, timestamp, source)
        
        # Add to main storage
        self.entries.append(entry)
        
        # Update index
        if attr.key not in self._index_by_key:
            self._index_by_key[attr.key] = []
        self._index_by_key[attr.key].append(len(self.entries) - 1)
        
        # Maintain size limit
        if len(self.entries) > self.max_entries:
            self._evict_oldest()
    
    def _evict_oldest(self) -> None:
        """Remove oldest entries when memory is full"""
        if not self.entries:
            return
        
        # Remove oldest entry
        removed_entry = self.entries.pop(0)
        
        # Update indices
        removed_key = removed_entry.attr.key
        if removed_key in self._index_by_key:
            # Decrement all indices for this key
            self._index_by_key[removed_key] = [
                idx - 1 for idx in self._index_by_key[removed_key] if idx > 0
            ]
            if not self._index_by_key[removed_key]:
                del self._index_by_key[removed_key]
        
        # Decrement all other indices
        for key in self._index_by_key:
            self._index_by_key[key] = [idx - 1 for idx in self._index_by_key[key]]
    
    def get_recent(self, count: int = 10) -> List[EpisodicEntry]:
        """Get the most recent entries"""
        return self.entries[-count:] if self.entries else []
    
    def get_by_timerange(self, start_time: float, end_time: float) -> List[EpisodicEntry]:
        """
        Get entries within a time range
        
        Args:
            start_time: Start timestamp (inclusive)
            end_time: End timestamp (inclusive)
        """
        return [
            entry for entry in self.entries
            if start_time <= entry.timestamp <= end_time
        ]
    
    def get_by_key(self, key: str, limit: Optional[int] = None) -> List[EpisodicEntry]:
        """
        Get all entries with a specific key
        
        Args:
            key: The attribute key to search for
            limit: Optional limit on number of results
        """
        if key not in self._index_by_key:
            return []
        
        indices = self._index_by_key[key]
        if limit:
            indices = indices[-limit:]  # Get most recent
        
        return [self.entries[i] for i in indices]
    
    def search_pattern(self, pattern: ATTRPattern, limit: Optional[int] = None) -> List[Tuple[EpisodicEntry, dict]]:
        """
        Search for entries matching a pattern
        
        Args:
            pattern: ATTR pattern to match
            limit: Optional limit on results
        
        Returns:
            List of (entry, bindings) tuples for successful matches
        """
        results = []
        
        for entry in reversed(self.entries):  # Search recent first
            match_result = ATTRAlgebra.match_pattern(pattern, entry.attr)
            if match_result.success:
                results.append((entry, match_result.bindings))
                
                if limit and len(results) >= limit:
                    break
        
        return results
    
    def get_temporal_patterns(self, window_size: int = 5) -> List[List[EpisodicEntry]]:
        """
        Find temporal patterns in recent observations
        
        Args:
            window_size: Size of sliding window for pattern detection
        
        Returns:
            List of temporal sequences that might represent patterns
        """
        if len(self.entries) < window_size:
            return []
        
        patterns = []
        
        # Simple sliding window approach
        for i in range(len(self.entries) - window_size + 1):
            window = self.entries[i:i + window_size]
            
            # Check if this window shows interesting temporal structure
            if self._is_interesting_sequence(window):
                patterns.append(window)
        
        return patterns
    
    def _is_interesting_sequence(self, sequence: List[EpisodicEntry]) -> bool:
        """
        Determine if a sequence of entries represents an interesting pattern
        
        Simple heuristics:
        - Repeated keys in sequence
        - Regular time intervals
        - Similar value patterns
        """
        if len(sequence) < 2:
            return False
        
        # Check for repeated keys
        keys = [entry.attr.key for entry in sequence]
        if len(set(keys)) == 1:  # All same key
            return True
        
        # Check for regular time intervals
        intervals = [
            sequence[i+1].timestamp - sequence[i].timestamp 
            for i in range(len(sequence) - 1)
        ]
        
        if intervals:
            avg_interval = sum(intervals) / len(intervals)
            # Check if intervals are roughly regular (within 20% variance)
            variance = sum((interval - avg_interval) ** 2 for interval in intervals) / len(intervals)
            std_dev = variance ** 0.5
            if std_dev / avg_interval < 0.2:  # Low variance = regular pattern
                return True
        
        return False
    
    def compress_similar(self, similarity_threshold: float = 0.9) -> int:
        """
        Compress similar entries to save memory
        
        Args:
            similarity_threshold: Threshold for considering entries similar
        
        Returns:
            Number of entries removed through compression
        """
        if len(self.entries) < 2:
            return 0
        
        original_count = len(self.entries)
        
        # Group entries by key for more efficient comparison
        key_groups = {}
        for i, entry in enumerate(self.entries):
            key = entry.attr.key
            if key not in key_groups:
                key_groups[key] = []
            key_groups[key].append((i, entry))
        
        # Find and mark duplicates within each key group
        entries_to_remove = set()
        
        for key, group in key_groups.items():
            for i in range(len(group)):
                if group[i][0] in entries_to_remove:
                    continue
                
                for j in range(i + 1, len(group)):
                    if group[j][0] in entries_to_remove:
                        continue
                    
                    # Check similarity
                    entry1, entry2 = group[i][1], group[j][1]
                    if self._entries_similar(entry1, entry2, similarity_threshold):
                        # Keep the more recent one
                        if entry1.timestamp < entry2.timestamp:
                            entries_to_remove.add(group[i][0])
                        else:
                            entries_to_remove.add(group[j][0])
        
        # Remove marked entries (in reverse order to maintain indices)
        for idx in sorted(entries_to_remove, reverse=True):
            del self.entries[idx]
        
        # Rebuild index
        self._rebuild_index()
        
        return original_count - len(self.entries)
    
    def _entries_similar(self, entry1: EpisodicEntry, entry2: EpisodicEntry, threshold: float) -> bool:
        """Check if two entries are similar enough to be compressed"""
        # Simple similarity: same key and same string representation
        if entry1.attr.key != entry2.attr.key:
            return False
        
        # For now, exact match on string representation
        return str(entry1.attr) == str(entry2.attr)
    
    def _rebuild_index(self) -> None:
        """Rebuild the key index after modifications"""
        self._index_by_key.clear()
        
        for i, entry in enumerate(self.entries):
            key = entry.attr.key
            if key not in self._index_by_key:
                self._index_by_key[key] = []
            self._index_by_key[key].append(i)
    
    def get_statistics(self) -> dict:
        """Get memory statistics"""
        total_entries = len(self.entries)
        unique_keys = len(self._index_by_key)
        
        if total_entries == 0:
            return {
                "total_entries": 0,
                "unique_keys": 0,
                "memory_usage": 0,
                "oldest_timestamp": None,
                "newest_timestamp": None
            }
        
        oldest = min(entry.timestamp for entry in self.entries)
        newest = max(entry.timestamp for entry in self.entries)
        
        return {
            "total_entries": total_entries,
            "unique_keys": unique_keys,
            "memory_usage": f"{total_entries}/{self.max_entries}",
            "oldest_timestamp": oldest,
            "newest_timestamp": newest,
            "time_span_seconds": newest - oldest
        }
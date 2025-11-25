"""
Semantic Rule Base Class

This module defines the abstract interface for all semantic rules.
Uses the Strategy pattern to allow pluggable rule implementations.

Design principles:
- Open/Closed: Open for extension (new rules), closed for modification
- Interface Segregation: Minimal interface with only essential methods
- Liskov Substitution: All rules are interchangeable
"""

from abc import ABC, abstractmethod
from typing import List
from ..models import Chunk


class SemanticRule(ABC):
    """
    Abstract base class for semantic merging rules.
    
    Each rule defines:
    1. Pattern: Sequence of chunk categories to match (e.g., ["SujV", "SV"])
    2. Result category: Category for merged chunk (e.g., "SV")
    3. Condition: Optional condition that must be satisfied
    
    **Polymorphism Example:**
    Subclasses override check_condition() to implement specific logic.
    Each rule can be used interchangeably through the same interface.
    
    **Encapsulation Example:**
    Pattern and result_category are encapsulated as instance attributes.
    Internal logic is hidden; clients only call check_condition() and apply().
    """
    
    def __init__(self, pattern: List[str], result_category: str, rule_id: str = ""):
        """
        Initialize a semantic rule.
        
        Args:
            pattern: List of chunk categories to match
            result_category: Category for the merged result
            rule_id: Identifier for debugging/logging
        """
        self.pattern = pattern
        self.result_category = result_category
        self.rule_id = rule_id or self.__class__.__name__
    
    def matches_pattern(self, chunks: List[Chunk], start_idx: int) -> bool:
        """
        Check if chunks starting at start_idx match this rule's pattern.
        
        Args:
            chunks: List of chunks
            start_idx: Starting index to check
        
        Returns:
            True if pattern matches
        """
        if start_idx + len(self.pattern) > len(chunks):
            return False
        
        for i, expected_cat in enumerate(self.pattern):
            if chunks[start_idx + i].category != expected_cat:
                return False
        
        return True
    
    @abstractmethod
    def check_condition(self, chunks: List[Chunk], start_idx: int) -> bool:
        """
        Check if the rule's condition is satisfied.
        
        **Abstract Method (Inheritance):**
        Subclasses MUST implement this method with their specific logic.
        This enforces a contract while allowing flexible implementations.
        
        Args:
            chunks: List of all chunks
            start_idx: Starting index of the match
        
        Returns:
            True if condition is satisfied
        """
        pass
    
    def apply(self, chunks: List[Chunk], start_idx: int) -> Chunk:
        """
        Apply the rule: merge matched chunks into a single chunk.
        
        Args:
            chunks: List of chunks
            start_idx: Starting index of the match
        
        Returns:
            Merged chunk
        """
        matched_chunks = chunks[start_idx:start_idx + len(self.pattern)]
        all_tokens = []
        for chunk in matched_chunks:
            all_tokens.extend(chunk.tokens)
        
        return Chunk(self.result_category, all_tokens)
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"{self.rule_id}({' + '.join(self.pattern)} → {self.result_category})"

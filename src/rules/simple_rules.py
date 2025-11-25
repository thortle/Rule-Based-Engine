"""
Simple Semantic Rules

This module contains simple rules that don't require complex condition checking.
Most pattern-based merging falls into this category.

Examples:
- Subject + Verb: [SujV] + [SV] → [SV]
- Adverb + Verb: [SAdv] + [SV] → [SV]
- Preposition + Noun: [SP] + [SN] → [SP]
"""

from typing import List
from .base import SemanticRule
from ..models import Chunk


class AdjacentRule(SemanticRule):
    """
    Rule that matches adjacent chunks with no special conditions.
    
    This handles most simple merging patterns where chunks should be
    combined if they appear next to each other with matching categories.
    
    **Inheritance Example:**
    AdjacentRule inherits from SemanticRule and overrides check_condition()
    with a trivial implementation that always returns True.
    
    **Polymorphism Example:**
    Despite its simple implementation, AdjacentRule can be used anywhere
    a SemanticRule is expected, demonstrating polymorphic behavior.
    """
    
    def check_condition(self, chunks: List[Chunk], start_idx: int) -> bool:
        """
        Adjacent chunks always satisfy the condition.
        
        Returns:
            Always True - no special condition needed
        """
        return True

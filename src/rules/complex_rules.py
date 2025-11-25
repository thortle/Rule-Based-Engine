"""
Complex Semantic Rules

This module contains rules with sophisticated condition checking logic.
Each rule encapsulates specific linguistic knowledge for semantic merging.

Examples:
- Temporal expressions: "18 h 30" + "ce lundi"
- Prepositional chains: "en urgences" + "à l'hôpital"
- Verb-object relations: "révèle" + "l'impensable"

Design: Each rule is a self-contained class with clear responsibility.
"""

from typing import List
from .base import SemanticRule
from .constants import TEMPORAL_WORDS, PREPOSITIONS
from ..models import Chunk


class TemporalMergeRule(SemanticRule):
    """
    Merge temporal noun phrases: [SN] + [SN] → [SN]
    
    Condition: Both chunks must contain temporal expressions.
    
    Example: "18 h 30" + "ce lundi 27 janvier" → "18 h 30 ce lundi 27 janvier"
    
    **Inheritance + Polymorphism Example:**
    Inherits from SemanticRule and overrides check_condition() with
    temporal-specific logic. Can be used interchangeably with other rules.
    """
    
    def check_condition(self, chunks: List[Chunk], start_idx: int) -> bool:
        """
        Both chunks must contain temporal words.
        
        Returns:
            True if all matched chunks contain temporal expressions
        """
        matched_chunks = chunks[start_idx:start_idx + len(self.pattern)]
        
        for chunk in matched_chunks:
            chunk_words = set(chunk.text.lower().split())
            # Encapsulation: Uses TEMPORAL_WORDS constant
            if not (chunk_words & TEMPORAL_WORDS):
                return False
        
        return True


class PrepositionalChainRule(SemanticRule):
    """
    Merge prepositional chains: [SN] + [SN] → [SN]
    
    Condition: Both chunks must contain prepositions.
    
    Example: "en urgences" + "à l'hôpital" → "en urgences à l'hôpital"
    
    **Single Responsibility Principle:**
    This class has ONE job: identify and merge prepositional chains.
    It doesn't handle other merging logic.
    """
    
    def check_condition(self, chunks: List[Chunk], start_idx: int) -> bool:
        """
        Both chunks must contain prepositions.
        
        Checks both by:
        1. UPOS tag (ADP = adposition)
        2. Lexical lookup in PREPOSITIONS set
        
        Returns:
            True if all matched chunks contain prepositions
        """
        matched_chunks = chunks[start_idx:start_idx + len(self.pattern)]
        
        for chunk in matched_chunks:
            # Check by UPOS tag
            has_prep = any(t.upos == 'ADP' for t in chunk.tokens)
            
            # Also check by text (lexical lookup)
            chunk_words = set(chunk.text.lower().split())
            has_prep = has_prep or bool(chunk_words & PREPOSITIONS)
            
            if not has_prep:
                return False
        
        return True


class VerbDirectObjectRule(SemanticRule):
    """
    Merge verb with direct object: [SV] + [SN] → [SV]
    
    Condition: No punctuation between chunks.
    
    Example: "révèle" + "l'impensable" → "révèle l'impensable"
    
    **Encapsulation Example:**
    The logic for detecting punctuation is encapsulated within this class.
    Clients don't need to know HOW it checks for punctuation.
    """
    
    def check_condition(self, chunks: List[Chunk], start_idx: int) -> bool:
        """
        Chunks must be adjacent with no punctuation.
        
        Returns:
            True if no punctuation chunk exists between matched chunks
        """
        matched_chunks = chunks[start_idx:start_idx + len(self.pattern)]
        return not any(c.category == 'Pct' for c in matched_chunks)


class AdverbialIntroducerRule(SemanticRule):
    """
    Merge sentence-initial adverbial phrase: [SN] + [Pct] + [SN] + [SV] → [SV]
    
    Condition: First chunk has preposition, followed by comma.
    
    Example: "De retour aux urgences" + "," + "les médecins" + "sont"
             → "De retour aux urgences , les médecins sont"
    
    **Polymorphism Example:**
    Despite having more complex pattern (4 chunks) and logic,
    this rule works identically to other rules through the SemanticRule interface.
    """
    
    def check_condition(self, chunks: List[Chunk], start_idx: int) -> bool:
        """
        First chunk must have preposition, second must be comma.
        
        Returns:
            True if pattern matches adverbial introducer structure
        """
        matched_chunks = chunks[start_idx:start_idx + len(self.pattern)]
        
        if len(matched_chunks) < 2:
            return False
        
        # First chunk has preposition
        first_chunk = matched_chunks[0]
        has_prep = any(t.upos == 'ADP' for t in first_chunk.tokens)
        chunk_words = set(first_chunk.text.lower().split())
        has_prep = has_prep or bool(chunk_words & PREPOSITIONS)
        
        # Second is comma
        second_chunk = matched_chunks[1]
        is_comma = (second_chunk.category == 'Pct' and 
                   second_chunk.text.strip() == ',')
        
        return has_prep and is_comma

#!/usr/bin/env python3
"""
Core Data Models for Rule-Based French Text Chunker

Simple, focused data classes representing linguistic entities.
These are intentionally minimal - OOP complexity belongs in the
chunking/merging logic, not in data structures.

Design Philosophy:
- Data classes should be SIMPLE containers
- Add methods only when they simplify calling code
- Avoid over-engineering with unnecessary features
"""

from typing import List, Dict, Optional
from dataclasses import dataclass


# ============================================================================
# TOKEN CLASS
# ============================================================================

@dataclass(frozen=True)
class Token:
    """
    Represents a single token with Universal Dependencies annotation.
    
    Immutable (frozen) to prevent accidental modification during processing.
    """
    
    id: int
    text: str
    lemma: str
    upos: str
    xpos: str = "_"
    feats: str = "_"
    head: int = 0
    deprel: str = "root"
    deps: str = "_"
    misc: str = "_"
    
    @classmethod
    def from_conllu(cls, line: str) -> 'Token':
        """Create Token from CoNLL-U format line."""
        fields = line.strip().split('\t')
        return cls.from_fields(fields)
    
    @classmethod
    def from_fields(cls, fields: List[str]) -> 'Token':
        """Create Token from list of CoNLL-U fields."""
        return cls(
            id=int(fields[0]),
            text=fields[1],
            lemma=fields[2],
            upos=fields[3],
            xpos=fields[4] if len(fields) > 4 else "_",
            feats=fields[5] if len(fields) > 5 else "_",
            head=int(fields[6]),
            deprel=fields[7],
            deps=fields[8] if len(fields) > 8 else "_",
            misc=fields[9] if len(fields) > 9 else "_"
        )
    
    @property
    def base_deprel(self) -> str:
        """Get base dependency relation without subtypes (e.g., 'nsubj' from 'nsubj:pass')."""
        return self.deprel.split(':')[0]
    
    def is_root(self) -> bool:
        """Check if this token is the root of the sentence."""
        return self.head == 0
    
    def is_punctuation(self) -> bool:
        """Check if this token is punctuation."""
        return self.upos == 'PUNCT'


# ============================================================================
# CHUNK CLASS
# ============================================================================

class Chunk:
    """
    Represents a syntactic or semantic chunk (phrase).
    
    Simple container with automatic token sorting and text generation.
    """
    
    def __init__(self, category: str, tokens: List[Token]):
        """Initialize chunk with category and tokens (auto-sorted by ID)."""
        self.category = category
        self.tokens = sorted(tokens, key=lambda t: t.id)
    
    @property
    def text(self) -> str:
        """Get space-separated text of all tokens."""
        return ' '.join(token.text for token in self.tokens)
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"[{self.category}] {self.text}"


# ============================================================================
# SENTENCE CLASS
# ============================================================================

class Sentence:
    """
    Represents a sentence with Universal Dependencies annotation.
    
    Provides access to tokens and basic dependency tree navigation.
    """
    
    def __init__(self, sent_id: str, text: str, tokens: List[Token]):
        """Initialize sentence with ID, text, and tokens."""
        self.sent_id = sent_id
        self.text = text
        self.tokens = tokens
        self._token_map: Dict[int, Token] = {token.id: token for token in tokens}
    
    def get_token(self, token_id: int) -> Optional[Token]:
        """Get token by ID, or None if not found."""
        return self._token_map.get(token_id)
    
    def has_token(self, token_id: int) -> bool:
        """Check if sentence contains token with given ID."""
        return token_id in self._token_map
    
    def get_children(self, token_id: int) -> List[Token]:
        """Get all tokens that have the given token as their head."""
        return [token for token in self.tokens if token.head == token_id]
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"Sentence(id={self.sent_id}, tokens={len(self.tokens)})"


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = ['Token', 'Chunk', 'Sentence']

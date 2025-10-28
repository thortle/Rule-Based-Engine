#!/usr/bin/env python3
"""
Chunker Classes - OOP Architecture for Text Chunking

This module provides abstract and concrete chunker implementations
following the Strategy pattern for text segmentation.

Design Philosophy:
- Single Responsibility: Each chunker has ONE job
- Strategy Pattern: Swap chunking algorithms easily
- Simplicity: ~200 lines total, methods under 50 lines
"""

from abc import ABC, abstractmethod
from typing import List, Set, Dict
from models import Token, Chunk, Sentence


# ============================================================================
# ABSTRACT BASE CLASS
# ============================================================================

class Chunker(ABC):
    """
    Abstract base class for text chunking strategies.
    
    Defines the interface that all chunkers must implement.
    """
    
    @abstractmethod
    def chunk_sentence(self, sentence: Sentence) -> List[Chunk]:
        """
        Chunk a single sentence into syntactic/semantic phrases.
        
        Args:
            sentence: Sentence to chunk
            
        Returns:
            List of chunks in original order
        """
        pass


# ============================================================================
# UNIVERSAL DEPENDENCIES CHUNKER
# ============================================================================

class UDChunker(Chunker):
    """
    Universal Dependencies-based chunker for French text.
    
    Strategy:
    1. Identify phrase-internal relations (tokens that merge)
    2. Build chunks by collecting complete constituents  
    3. Handle special cases (prepositions, copulas, appositions)
    
    Principle: Each token belongs to exactly ONE chunk.
    """
    
    # Relations that keep tokens in the same phrase
    MERGE_RELATIONS = {
        'det', 'amod', 'nummod', 'nmod',  # Noun phrase internal
        'flat:name', 'flat', 'fixed', 'compound',  # Multi-word expressions
        'aux', 'aux:pass', 'aux:tense',  # Verb auxiliaries
        'case',  # Prepositions
        'appos',  # Appositions (e.g., "hôpital Rangueil")
    }
    
    # Relations excluded from noun phrase merging
    EXCLUDE_FROM_NP = {'cop'}  # Copulas need separate treatment
    
    def chunk_sentence(self, sentence: Sentence) -> List[Chunk]:
        """Extract linguistically-principled chunks from sentence."""
        processed = set()
        chunks = []
        
        # Build phrase mapping
        token_to_head = self._build_phrase_mapping(sentence)
        phrase_heads = set()
        
        # Process tokens in order
        for token in sentence.tokens:
            if token.id in processed:
                continue
                
            if token.is_punctuation():
                chunks.append(Chunk('Pct', [token]))
                processed.add(token.id)
                continue
            
            # Get phrase head for this token
            head_id = token_to_head.get(token.id, token.id)
            
            if head_id in phrase_heads:
                continue
                
            phrase_heads.add(head_id)
            
            # Collect phrase tokens
            phrase_token_ids = self._collect_phrase(sentence, head_id)
            phrase_tokens = [sentence.get_token(tid) for tid in sorted(phrase_token_ids)]
            processed.update(phrase_token_ids)
            
            # Determine category and create chunk
            head_token = sentence.get_token(head_id)
            category = self._categorize_token(head_token)
            chunks.append(Chunk(category, phrase_tokens))
        
        # Sort by position
        chunks.sort(key=lambda c: c.tokens[0].id)
        return chunks
    
    def _build_phrase_mapping(self, sentence: Sentence) -> Dict[int, int]:
        """Map each token to its phrase head."""
        mapping = {}
        for token in sentence.tokens:
            if not token.is_punctuation():
                mapping[token.id] = self._find_phrase_head(sentence, token.id)
        return mapping
    
    def _find_phrase_head(self, sentence: Sentence, token_id: int) -> int:
        """
        Find phrase head by following merge relations upward.
        
        Returns the ID of the phrase head.
        """
        token = sentence.get_token(token_id)
        
        # Copulas are their own phrase heads
        if token.base_deprel in self.EXCLUDE_FROM_NP:
            return token_id
        
        # Check if connected to parent via merge relation
        if token.head != 0 and sentence.has_token(token.head):
            if token.base_deprel in self.MERGE_RELATIONS:
                return self._find_phrase_head(sentence, token.head)
        
        return token_id
    
    def _collect_phrase(self, sentence: Sentence, head_id: int) -> Set[int]:
        """
        Collect all tokens belonging to phrase headed by head_id.
        
        Includes head and all dependents connected via merge relations.
        """
        if not sentence.has_token(head_id):
            return set()
        
        head_token = sentence.get_token(head_id)
        phrase_tokens = {head_id}
        
        # Collect children via merge relations
        for child in sentence.get_children(head_id):
            if child.is_punctuation() or child.base_deprel in self.EXCLUDE_FROM_NP:
                continue
            
            # Merge if relation matches
            if child.base_deprel in self.MERGE_RELATIONS:
                child_phrase = self._collect_phrase(sentence, child.id)
                phrase_tokens.update(child_phrase)
            
            # Special case: proper names modifying nouns
            elif head_token.upos in ['NOUN', 'PROPN'] and child.upos == 'PROPN':
                if child.base_deprel in ['nmod', 'appos']:
                    child_phrase = self._collect_phrase(sentence, child.id)
                    phrase_tokens.update(child_phrase)
        
        return phrase_tokens
    
    def _categorize_token(self, token: Token) -> str:
        """
        Map UD POS tag to French chunk category.
        
        Categories:
            SN   - Syntagme Nominal (noun phrase)
            SV   - Syntagme Verbal (verb phrase)
            SP   - Syntagme Prépositionnel (prepositional phrase)
            SAdj - Syntagme Adjectival (adjective phrase)
            SAdv - Syntagme Adverbial (adverb phrase)
            SujV - Sujet pronominal (subject pronoun)
            CSub - Conjonction de subordination
            Coord - Coordination
            Pro_Obj - Pronom objet
            Pct  - Ponctuation
        """
        upos = token.upos
        deprel = token.base_deprel
        
        # Pronouns: distinguish subject vs object
        if upos == 'PRON':
            if deprel in ['nsubj', 'nsubj:pass', 'expl:subj']:
                return 'SujV'
            elif deprel in ['obj', 'iobj', 'obl', 'expl']:
                return 'Pro_Obj'
            return 'SujV'
        
        # POS-based categorization
        if upos in ['VERB', 'AUX']:
            return 'SV'
        if upos in ['NOUN', 'PROPN', 'NUM']:
            return 'SN'
        if upos == 'ADP':
            return 'SP'
        if upos == 'ADJ':
            return 'SAdj'
        if upos == 'ADV':
            return 'SAdv'
        if upos == 'SCONJ':
            return 'CSub'
        if upos == 'CCONJ':
            return 'Coord'
        if upos == 'DET':
            return 'SN'
        if upos == 'PUNCT':
            return 'Pct'
        
        # Default to noun phrase
        return 'SN'


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = ['Chunker', 'UDChunker']

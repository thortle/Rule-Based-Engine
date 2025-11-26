#!/usr/bin/env python3
"""
Linguistic Chunker - UD-based phrase chunking for French text

This module provides:
1. Data structures for Universal Dependencies tokens and sentences
2. Improved chunking algorithm that creates complete syntactic phrases
3. Mapping from UD POS tags to French chunk categories

All functionality consolidated into one module for clean architecture.
"""

from typing import List, Set, Dict


# ============================================================================
# DATA STRUCTURES
# ============================================================================

class UDToken:
    """
    Represents a single token in Universal Dependencies format.
    
    Attributes:
        id: Token ID (1-indexed)
        text: Surface form
        lemma: Lemma/dictionary form
        upos: Universal POS tag (NOUN, VERB, etc.)
        xpos: Language-specific POS tag
        feats: Morphological features
        head: ID of syntactic head (0 = root)
        deprel: Dependency relation (nsubj, obj, etc.)
        deps: Enhanced dependencies
        misc: Miscellaneous annotations
    """
    def __init__(self, conllu_fields: List[str]):
        """Initialize from CoNLL-U format fields"""
        self.id = int(conllu_fields[0])
        self.text = conllu_fields[1]
        self.lemma = conllu_fields[2]
        self.upos = conllu_fields[3]
        self.xpos = conllu_fields[4]
        self.feats = conllu_fields[5]
        self.head = int(conllu_fields[6])
        self.deprel = conllu_fields[7]
        self.deps = conllu_fields[8] if len(conllu_fields) > 8 else "_"
        self.misc = conllu_fields[9] if len(conllu_fields) > 9 else "_"
    
    def __repr__(self):
        return f"UDToken(id={self.id}, text='{self.text}', upos={self.upos}, head={self.head}, deprel={self.deprel})"


class UDSentence:
    """
    Represents a sentence with Universal Dependencies annotation.
    
    Attributes:
        sent_id: Sentence identifier
        text: Raw sentence text
        tokens: List of UDToken objects
        token_map: Dict mapping token ID to UDToken
    """
    def __init__(self, sent_id: str, text: str, tokens: List[UDToken]):
        self.sent_id = sent_id
        self.text = text
        self.tokens = tokens
        self.token_map: Dict[int, UDToken] = {token.id: token for token in tokens}
    
    def get_children(self, token_id: int) -> List[UDToken]:
        """Get all tokens that have the given token as their head"""
        return [token for token in self.tokens if token.head == token_id]
    
    def __repr__(self):
        return f"UDSentence(id={self.sent_id}, tokens={len(self.tokens)})"


class Chunk:
    """
    Represents a syntactic chunk (phrase).
    
    Attributes:
        category: Chunk category (SN, SV, SP, etc.)
        tokens: List of UDToken objects in this chunk
        text: Surface text of the chunk
    """
    def __init__(self, category: str, tokens: List[UDToken]):
        self.category = category
        self.tokens = sorted(tokens, key=lambda t: t.id)
        self.text = " ".join([token.text for token in self.tokens])
    
    def __repr__(self):
        return f"[{self.category}] {self.text}"


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def map_ud_to_chunk_category(token: UDToken) -> str:
    """
    Map Universal Dependencies POS tag to French chunk category.
    
    Categories:
        SN  - Syntagme Nominal (noun phrase)
        SV  - Syntagme Verbal (verb phrase)
        SP  - Syntagme Prépositionnel (prepositional phrase)
        SAdj - Syntagme Adjectival (adjective phrase)
        SAdv - Syntagme Adverbial (adverb phrase)
        SujV - Sujet pronominal (subject pronoun)
        CSub - Conjonction de subordination (subordinating conjunction)
        Coord - Coordination (coordinating conjunction)
        Pro_Obj - Pronom objet (object pronoun)
        Pct - Ponctuation (punctuation)
    
    Args:
        token: UDToken to categorize
    
    Returns:
        Chunk category string
    """
    upos = token.upos
    deprel = token.deprel.split(':')[0]  # Base relation without subtypes
    
    # Pronouns: distinguish subject vs object
    if upos == 'PRON':
        if deprel in ['nsubj', 'nsubj:pass', 'expl:subj']:
            return 'SujV'  # Subject pronoun
        elif deprel in ['obj', 'iobj', 'obl', 'expl']:
            return 'Pro_Obj'  # Object pronoun
        else:
            return 'SujV'  # Default to subject
    
    # Verbs and auxiliaries
    if upos in ['VERB', 'AUX']:
        return 'SV'
    
    # Nouns and proper nouns
    if upos in ['NOUN', 'PROPN', 'NUM']:
        return 'SN'
    
    # Prepositions
    if upos == 'ADP':
        return 'SP'
    
    # Adjectives
    if upos == 'ADJ':
        return 'SAdj'
    
    # Adverbs
    if upos == 'ADV':
        return 'SAdv'
    
    # Subordinating conjunctions
    if upos == 'SCONJ':
        return 'CSub'
    
    # Coordinating conjunctions
    if upos == 'CCONJ':
        return 'Coord'
    
    # Determiners (part of noun phrases)
    if upos == 'DET':
        return 'SN'
    
    # Punctuation
    if upos == 'PUNCT':
        return 'Pct'
    
    # Default: treat as noun phrase
    return 'SN'


# ============================================================================
# CHUNKING ALGORITHM
# ============================================================================


def extract_linguistic_chunks_v2(sentence: UDSentence) -> List[Chunk]:
    """
    Extract linguistically-principled chunks using a simplified, correct algorithm.
    
    Strategy:
    1. Identify phrase-internal relations (tokens that merge)
    2. Build chunks by collecting complete constituents
    3. Handle prepositional phrases specially (PREP + NP = one chunk)
    
    Key principle: Each token belongs to exactly ONE chunk.
    """
    
    # Define which dependency relations keep tokens in the same phrase
    MERGE_RELATIONS = {
        'det', 'amod', 'nummod', 'nmod',  # Noun phrase internal
        'flat:name', 'flat', 'fixed', 'compound',  # Multi-word expressions
        'aux', 'aux:pass', 'aux:tense',  # Verb auxiliaries (removed 'cop')
        'case',  # Prepositions (special handling)
        'appos',  # Appositions (for "hôpital Rangueil")
    }
    
    # Relations that should NOT merge (copulas need special handling)
    EXCLUDE_FROM_NP = {
        'cop',  # Copulas like "est" should not merge into time NPs
    }
    
    processed = set()
    chunks = []
    
    def get_phrase_head(token_id: int) -> int:
        """
        Find the phrase head for a token by following merge relations upward.
        Returns the ID of the phrase head.
        """
        token = sentence.token_map[token_id]
        
        # FIX: Don't merge copulas into NPs
        base_rel = token.deprel.split(':')[0]
        if base_rel in EXCLUDE_FROM_NP:
            return token_id  # Copula is its own phrase head
        
        # Check if this token's head is via a merge relation
        if token.head != 0 and token.head in sentence.token_map:
            parent = sentence.token_map[token.head]
            parent_rel = token.deprel.split(':')[0]
            
            # If connected via merge relation, recurse to find phrase head
            if parent_rel in MERGE_RELATIONS:
                return get_phrase_head(token.head)
        
        # This token is the phrase head
        return token_id
    
    def collect_phrase_tokens(head_id: int) -> Set[int]:
        """
        Collect all tokens that belong to the phrase headed by head_id.
        This includes the head and all dependents connected via merge relations.
        
        IMPROVEMENTS:
        - Excludes copulas from NPs (they connect with predicates)
        - Includes appositions (for "hôpital Rangueil")
        - Better handling of prepositional phrases
        """
        if head_id not in sentence.token_map:
            return set()
        
        head_token = sentence.token_map[head_id]
        phrase_tokens = {head_id}
        
        # Collect all children connected via merge relations
        for child in sentence.get_children(head_id):
            if child.upos == 'PUNCT':
                continue
            
            base_rel = child.deprel.split(':')[0]
            
            # FIX: Don't merge copulas into NPs
            if base_rel in EXCLUDE_FROM_NP:
                continue
            
            # Merge if relation is in MERGE_RELATIONS
            if base_rel in MERGE_RELATIONS:
                # Recursively collect this child's subtree
                child_phrase = collect_phrase_tokens(child.id)
                phrase_tokens.update(child_phrase)
            
            # IMPROVEMENT: Also merge proper names that modify nouns (for "docteur Moulin")
            elif head_token.upos in ['NOUN', 'PROPN'] and child.upos == 'PROPN':
                if base_rel in ['nmod', 'appos']:
                    child_phrase = collect_phrase_tokens(child.id)
                    phrase_tokens.update(child_phrase)
        
        return phrase_tokens
    
    # Step 1: Build phrase groups - each token knows its phrase head
    token_to_phrase_head = {}
    for token in sentence.tokens:
        if token.upos != 'PUNCT':
            phrase_head = get_phrase_head(token.id)
            token_to_phrase_head[token.id] = phrase_head
    
    # Step 2: For each unique phrase head, create a chunk
    phrase_heads_seen = set()
    
    # Process tokens in order
    for token in sentence.tokens:
        if token.id in processed:
            continue
        
        if token.upos == 'PUNCT':
            # Punctuation gets its own chunk
            chunks.append(Chunk('Pct', [token]))
            processed.add(token.id)
            continue
        
        # Find this token's phrase head
        phrase_head_id = token_to_phrase_head.get(token.id, token.id)
        
        # Skip if we've already processed this phrase
        if phrase_head_id in phrase_heads_seen:
            continue
        
        phrase_heads_seen.add(phrase_head_id)
        
        # Collect all tokens in this phrase
        phrase_token_ids = collect_phrase_tokens(phrase_head_id)
        phrase_tokens = [sentence.token_map[tid] for tid in sorted(phrase_token_ids)]
        
        # Mark all as processed
        processed.update(phrase_token_ids)
        
        # Determine chunk category from phrase head
        head_token = sentence.token_map[phrase_head_id]
        category = map_ud_to_chunk_category(head_token)
        
        # Create chunk
        chunks.append(Chunk(category, phrase_tokens))
    
    # Sort chunks by position
    chunks.sort(key=lambda c: c.tokens[0].id)
    
    return chunks
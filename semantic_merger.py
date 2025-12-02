#!/usr/bin/env python3
"""
Semantic Merger - Level 2 Rule-Based Chunk Merging

This module implements the second level of the two-level chunking architecture.
It takes syntactic chunks from Level 1 (UD-based) and merges them based on
semantic rules and patterns.

Level 1 (UD): [SujV] Il [SV] est [SN] 18 h 30 ...
Level 2 (Semantic): [SV] Il est [SN] 18 h 30 ...

Rules applied:
1. Subject-Verb: [SujV] + [SV] → [SV]
2. Temporal: [SN] + [SN] → [SN] (if both temporal)
3. PP Completion: [SP] + [SN] → [SP]
4. Adverb-Verb: [SAdv] + [SV] → [SV]
5. Coordination: [SN] + [Coord] + [SN] → [SN]
"""

import json
from typing import List, Dict, Any, Optional, Set
from linguistic_chunker import Chunk, UDToken


# ============================================================================
# LEXICAL INDICATORS
# ============================================================================

TEMPORAL_WORDS = {
    # Time expressions
    'h', 'heure', 'heures', 'minute', 'minutes', 'seconde', 'secondes',
    'matin', 'midi', 'après-midi', 'soir', 'nuit', 'minuit',
    
    # Days
    'lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi', 'dimanche',
    'jour', 'jours', 'journée',
    
    # Months
    'janvier', 'février', 'mars', 'avril', 'mai', 'juin',
    'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre',
    'mois',
    
    # Other temporal
    'an', 'ans', 'année', 'années', 'semaine', 'semaines',
    'hier', 'aujourd\'hui', 'demain', 'maintenant',
    'ce', 'cette', 'dernier', 'dernière', 'prochain', 'prochaine'
}

PREPOSITIONS = {
    'à', 'de', 'en', 'dans', 'sur', 'sous', 'pour', 'par', 'avec',
    'sans', 'chez', 'vers', 'contre', 'depuis', 'pendant', 'avant',
    'après', 'devant', 'derrière', 'entre', 'parmi', 'selon'
}

RELATIVE_PRONOUNS = {
    'qui', 'que', 'qu\'', 'dont', 'où', 'lequel', 'laquelle',
    'lesquels', 'lesquelles', 'auquel', 'duquel', 'auxquels'
}

SPEECH_VERBS = {
    'dire', 'confier', 'rappeler', 'poursuivre', 'ajouter', 'conclure',
    'affirmer', 'déclarer', 'expliquer', 'raconter', 'répondre',
    'demander', 'interroger', 'préciser'
}

QUANTITY_WORDS = {
    'kilo', 'kilos', 'gramme', 'grammes', 'litre', 'litres',
    'mètre', 'mètres', 'centimètre', 'kilomètre',
    'heure', 'heures', 'minute', 'minutes', 'jour', 'jours'
}


# ============================================================================
# RULE LOADING
# ============================================================================

def load_semantic_rules(rules_file: str) -> List[Dict[str, Any]]:
    """
    Load semantic merging rules from JSON file.
    
    Expected format:
    [
        {
            "rule_id": "subject_verb",
            "pattern": ["SujV", "SV"],
            "result_category": "SV",
            "condition": "adjacent",
            "description": "Merge subject pronoun with verb"
        },
        ...
    ]
    
    Args:
        rules_file: Path to JSON rules file
    
    Returns:
        List of rule dictionaries
    """
    try:
        with open(rules_file, 'r', encoding='utf-8') as f:
            rules = json.load(f)
        
        # Filter for semantic rules (if mixed with other rule types)
        semantic_rules = []
        for rule in rules:
            if isinstance(rule, dict) and 'pattern' in rule:
                # Check if it's a semantic rule (has pattern as list of categories)
                if isinstance(rule.get('pattern'), list):
                    semantic_rules.append(rule)
        
        return semantic_rules if semantic_rules else rules
    except FileNotFoundError:
        print(f"[WARN] Rules file not found: {rules_file}")
        return []
    except json.JSONDecodeError:
        print(f"[WARN] Invalid JSON in rules file: {rules_file}")
        return []


# ============================================================================
# TOKEN-LEVEL CONDITION HELPERS
# ============================================================================

def chunk_has_preposition(chunk: Chunk) -> bool:
    """
    Check if a chunk contains a preposition.
    
    Args:
        chunk: Chunk to check
    
    Returns:
        True if chunk contains a preposition
    """
    # Check by UPOS tag
    if any(t.upos == 'ADP' for t in chunk.tokens):
        return True
    
    # Also check by text (for cases where tagging might differ)
    chunk_words = set(chunk.text.lower().split())
    return bool(chunk_words & PREPOSITIONS)


def chunk_starts_with_preposition(chunk: Chunk) -> bool:
    """
    Check if a chunk starts with a preposition.
    
    Args:
        chunk: Chunk to check
    
    Returns:
        True if first token is a preposition
    """
    if not chunk.tokens:
        return False
    
    first_token = chunk.tokens[0]
    return first_token.upos == 'ADP' or first_token.text.lower() in PREPOSITIONS


def chunk_is_quantity(chunk: Chunk) -> bool:
    """
    Check if a chunk represents a quantity or measurement.
    
    Args:
        chunk: Chunk to check
    
    Returns:
        True if chunk is a quantity
    """
    # Check for numbers
    if any(t.upos == 'NUM' for t in chunk.tokens):
        return True
    
    # Check for quantity words
    chunk_words = set(chunk.text.lower().split())
    return bool(chunk_words & QUANTITY_WORDS)


def chunk_starts_with_relative(chunk: Chunk) -> bool:
    """
    Check if a chunk starts with a relative pronoun.
    
    Args:
        chunk: Chunk to check
    
    Returns:
        True if first word is a relative pronoun
    """
    if not chunk.tokens:
        return False
    
    first_word = chunk.tokens[0].text.lower()
    return first_word in RELATIVE_PRONOUNS


def chunk_is_speech_verb(chunk: Chunk) -> bool:
    """
    Check if a chunk contains a speech/quotation verb.
    
    Args:
        chunk: Chunk to check
    
    Returns:
        True if chunk contains speech verb
    """
    for token in chunk.tokens:
        if token.lemma.lower() in SPEECH_VERBS:
            return True
    return False


def chunk_is_comma(chunk: Chunk) -> bool:
    """
    Check if a chunk is just a comma punctuation.
    
    Args:
        chunk: Chunk to check
    
    Returns:
        True if chunk is a comma
    """
    return chunk.category == 'Pct' and chunk.text.strip() == ','


def both_have_preposition(chunks: List[Chunk]) -> bool:
    """
    Check if all chunks in list contain prepositions.
    
    Args:
        chunks: List of chunks to check
    
    Returns:
        True if all chunks have prepositions
    """
    return all(chunk_has_preposition(c) for c in chunks)


# ============================================================================
# PATTERN MATCHING
# ============================================================================

def matches_pattern(chunks: List[Chunk], pattern: List[str], start_idx: int) -> bool:
    """
    Check if chunks starting at start_idx match the given pattern.
    
    Args:
        chunks: List of Chunk objects
        pattern: List of chunk categories (e.g., ["SujV", "SV"])
        start_idx: Starting index in chunks list
    
    Returns:
        True if pattern matches, False otherwise
    """
    # Check bounds
    if start_idx + len(pattern) > len(chunks):
        return False
    
    # Check each position
    for i, expected_cat in enumerate(pattern):
        actual_cat = chunks[start_idx + i].category
        if actual_cat != expected_cat:
            return False
    
    return True


def is_temporal_chunk(chunk: Chunk) -> bool:
    """
    Check if a chunk contains temporal expressions.
    
    Args:
        chunk: Chunk to check
    
    Returns:
        True if chunk contains temporal words
    """
    chunk_text_lower = chunk.text.lower()
    chunk_words = set(chunk_text_lower.split())
    
    # Check if any temporal word appears in chunk
    return bool(chunk_words & TEMPORAL_WORDS)


def check_condition(chunks: List[Chunk], rule: Dict[str, Any], match_start: int) -> bool:
    """
    Check if the condition for a rule is satisfied.
    
    Supported conditions:
    - "adjacent": Chunks must be adjacent (always true for pattern matching)
    - "both_temporal": Both chunks must contain temporal expressions
    - "same_np_structure": Both chunks are noun phrases with similar structure
    - "title_followed_by_propn": First chunk ends with title, second is proper noun
    - "both_have_preposition": All matched chunks contain prepositions
    - "first_is_quantity_second_has_prep": First chunk is quantity, second has preposition
    - "sv_starts_with_relative": SV chunk starts with relative pronoun
    - "is_speech_verb": Chunk contains a speech/quotation verb
    - "pct_is_comma": Punctuation chunk is a comma
    - "adjacent_no_punctuation": Chunks are adjacent with no punctuation between
    - "first_is_adverbial_and_comma": First chunk is adverbial, followed by comma
    
    Args:
        chunks: List of all chunks
        rule: Rule dictionary
        match_start: Starting index of the match
    
    Returns:
        True if condition is satisfied
    """
    condition = rule.get('condition')
    pattern_len = len(rule['pattern'])
    matched_chunks = chunks[match_start:match_start + pattern_len]
    
    # No condition means always apply
    if not condition:
        return True
    
    if condition == 'adjacent':
        # Always true for our pattern matching
        return True
    
    elif condition == 'both_temporal':
        # Check if all matched chunks are temporal
        return all(is_temporal_chunk(c) for c in matched_chunks)
    
    elif condition == 'same_np_structure':
        # All chunks should be noun phrases
        return all(c.category == 'SN' for c in matched_chunks)
    
    elif condition == 'title_followed_by_propn':
        # First chunk contains a title word, second contains proper noun
        titles = {'docteur', 'professeur', 'monsieur', 'madame', 'mademoiselle'}
        first_chunk = matched_chunks[0]
        second_chunk = matched_chunks[1]
        
        first_has_title = any(w.lower() in titles for w in first_chunk.text.split())
        second_has_propn = any(t.upos == 'PROPN' for t in second_chunk.tokens)
        
        return first_has_title and second_has_propn
    
    elif condition == 'both_have_preposition':
        # All matched chunks must contain prepositions
        return both_have_preposition(matched_chunks)
    
    elif condition == 'first_is_quantity_second_has_prep':
        # First chunk is quantity, second has preposition
        if len(matched_chunks) < 2:
            return False
        return chunk_is_quantity(matched_chunks[0]) and chunk_has_preposition(matched_chunks[1])
    
    elif condition == 'sv_starts_with_relative':
        # SV chunk starts with relative pronoun
        if not matched_chunks:
            return False
        # Find SV chunk in matched chunks
        for chunk in matched_chunks:
            if chunk.category == 'SV':
                return chunk_starts_with_relative(chunk)
        return False
    
    elif condition == 'is_speech_verb':
        # At least one chunk contains a speech verb
        return any(chunk_is_speech_verb(c) for c in matched_chunks)
    
    elif condition == 'pct_is_comma':
        # Punctuation chunk is a comma
        return any(chunk_is_comma(c) for c in matched_chunks)
    
    elif condition == 'adjacent_no_punctuation':
        # Chunks are adjacent and none are punctuation
        return not any(c.category == 'Pct' for c in matched_chunks)
    
    elif condition == 'first_is_adverbial_and_comma':
        # First chunk has prepositional content, followed by comma
        if len(matched_chunks) < 2:
            return False
        first_has_prep = chunk_has_preposition(matched_chunks[0])
        second_is_comma = chunk_is_comma(matched_chunks[1]) if len(matched_chunks) > 1 else False
        return first_has_prep and second_is_comma
    
    # Unknown condition - default to False for safety
    print(f"[WARN] Unknown condition: {condition}")
    return False


# ============================================================================
# CHUNK MERGING
# ============================================================================

def merge_chunks(chunks_to_merge: List[Chunk], result_category: str) -> Chunk:
    """
    Merge multiple chunks into a single chunk.
    
    Args:
        chunks_to_merge: List of Chunk objects to merge
        result_category: Category for the merged chunk
    
    Returns:
        New merged Chunk object
    """
    # Collect all tokens from all chunks
    all_tokens = []
    for chunk in chunks_to_merge:
        all_tokens.extend(chunk.tokens)
    
    # Create new merged chunk
    return Chunk(result_category, all_tokens)


def apply_semantic_rules(chunks: List[Chunk], rules: List[Dict[str, Any]], 
                        multi_pass: bool = False, max_passes: int = 10,
                        debug: bool = False) -> List[Chunk]:
    """
    Apply semantic merging rules to Level 1 chunks to produce Level 2 chunks.
    
    Strategy:
    - Iterate through chunks
    - For each position, try to match rules
    - If a rule matches and condition is satisfied, merge chunks
    - If multi_pass=True, repeat until no more rules can be applied (convergence)
    
    Args:
        chunks: List of Level 1 Chunk objects
        rules: List of semantic rule dictionaries
        multi_pass: If True, apply rules iteratively until convergence
        max_passes: Maximum number of passes (prevents infinite loops)
        debug: If True, print detailed debug information
    
    Returns:
        List of Level 2 Chunk objects (merged)
    """
    if not rules:
        print("[WARN] No semantic rules loaded, returning Level 1 chunks unchanged")
        return chunks
    
    # Work with a copy to avoid modifying original
    result = list(chunks)
    
    # Track statistics
    total_merges = 0
    pass_count = 0
    
    # Multi-pass loop
    while True:
        pass_count += 1
        merges_this_pass = 0
        
        if debug:
            print(f"\n--- Pass {pass_count} (chunks: {len(result)}) ---")
        
        # Single pass through chunks
        i = 0
        while i < len(result):
            matched = False
            
            # Try each rule at current position
            for rule in rules:
                pattern = rule['pattern']
                rule_id = rule.get('rule_id', 'unknown')
                
                # Check if pattern matches at position i
                if matches_pattern(result, pattern, i):
                    # Check if condition is satisfied
                    if check_condition(result, rule, i):
                        # Apply the merge
                        pattern_len = len(pattern)
                        chunks_to_merge = result[i:i + pattern_len]
                        
                        if debug:
                            print(f"  [{i}] Applying rule '{rule_id}':")
                            print(f"      Before: {' + '.join(str(c) for c in chunks_to_merge)}")
                        
                        merged_chunk = merge_chunks(chunks_to_merge, rule['result_category'])
                        
                        if debug:
                            print(f"      After:  {merged_chunk}")
                        
                        # Replace matched chunks with merged chunk
                        result[i:i + pattern_len] = [merged_chunk]
                        
                        merges_this_pass += 1
                        total_merges += 1
                        matched = True
                        break  # Move to next position after successful merge
                    elif debug:
                        # Pattern matched but condition failed
                        rule_id = rule.get('rule_id', 'unknown')
                        condition = rule.get('condition', 'none')
                        print(f"  [{i}] Rule '{rule_id}' matched but condition '{condition}' failed")
            
            # Move to next position
            i += 1
        
        # Check convergence
        if debug:
            print(f"--- Pass {pass_count} complete: {merges_this_pass} merges ---")
        
        # Stop if no merges in this pass, or if single-pass mode, or max passes reached
        if merges_this_pass == 0:
            if debug:
                print(f"[OK] Convergence reached after {pass_count} pass(es)")
            break
        
        if not multi_pass:
            break
        
        if pass_count >= max_passes:
            print(f"[WARN] Max passes ({max_passes}) reached, stopping")
            break
    
    if not debug:
        print(f"[OK] Applied {total_merges} semantic merges in {pass_count} pass(es)")
    
    return result


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def merge_level1_to_level2(level1_chunks: List[Chunk], rules_file: str,
                          multi_pass: bool = False, max_passes: int = 10,
                          debug: bool = False) -> List[Chunk]:
    """
    Main entry point: Apply semantic merging to Level 1 chunks.
    
    Args:
        level1_chunks: List of Level 1 (UD-based) chunks
        rules_file: Path to semantic rules JSON file
        multi_pass: If True, apply rules iteratively until convergence
        max_passes: Maximum number of passes (prevents infinite loops)
        debug: If True, print detailed debug information
    
    Returns:
        List of Level 2 (semantically merged) chunks
    """
    print("\nApplying Level 2 semantic merging...")
    
    if debug:
        print("Debug mode enabled")
    
    # Load rules
    rules = load_semantic_rules(rules_file)
    if not rules:
        print("[WARN] No rules loaded, skipping semantic merging")
        return level1_chunks
    
    print(f"[OK] Loaded {len(rules)} semantic rules")
    
    if multi_pass:
        print(f"[OK] Multi-pass mode enabled (max {max_passes} passes)")
    
    # Apply rules
    level2_chunks = apply_semantic_rules(level1_chunks, rules, 
                                        multi_pass=multi_pass, 
                                        max_passes=max_passes,
                                        debug=debug)
    
    # Statistics
    reduction = len(level1_chunks) - len(level2_chunks)
    reduction_pct = (reduction / len(level1_chunks)) * 100 if level1_chunks else 0
    
    print(f"[OK] Level 1 chunks: {len(level1_chunks)}")
    print(f"[OK] Level 2 chunks: {len(level2_chunks)}")
    print(f"[OK] Reduction: {reduction} chunks ({reduction_pct:.1f}%)")
    
    return level2_chunks


# ============================================================================
# TESTING
# ============================================================================

if __name__ == '__main__':
    """Test semantic merger with sample chunks"""
    print("Semantic Merger - Test Mode")
    print("=" * 80)
    
    # Create sample chunks for testing
    from linguistic_chunker import UDToken
    
    # Sample: "Il est 18 h 30"
    token1 = UDToken(['1', 'Il', 'lui', 'PRON', '_', '_', '2', 'nsubj', '_', '_'])
    token2 = UDToken(['2', 'est', 'être', 'AUX', '_', '_', '0', 'cop', '_', '_'])
    token3 = UDToken(['3', '18', '18', 'NUM', '_', '_', '4', 'nummod', '_', '_'])
    token4 = UDToken(['4', 'h', 'h', 'NOUN', '_', '_', '0', 'root', '_', '_'])
    token5 = UDToken(['5', '30', '30', 'NUM', '_', '_', '4', 'nmod', '_', '_'])
    
    chunk1 = Chunk('SujV', [token1])
    chunk2 = Chunk('SV', [token2])
    chunk3 = Chunk('SN', [token3, token4, token5])
    
    test_chunks = [chunk1, chunk2, chunk3]
    
    print("\nTest chunks:")
    for chunk in test_chunks:
        print(f"  {chunk}")
    
    # Create a simple test rule
    test_rules = [
        {
            "rule_id": "subject_verb",
            "pattern": ["SujV", "SV"],
            "result_category": "SV",
            "condition": "adjacent",
            "description": "Merge subject pronoun with verb"
        }
    ]
    
    print("\nApplying semantic rules...")
    result = apply_semantic_rules(test_chunks, test_rules)
    
    print("\nResult chunks:")
    for chunk in result:
        print(f"  {chunk}")
    
    print("\n" + "=" * 80)
    print("Test complete!")

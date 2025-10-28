#!/usr/bin/env python3
"""
Semantic Rules - OOP-Based Rule Engine for Level 2 Chunk Merging

This module implements semantic merging rules using the Strategy pattern.
Each rule encapsulates a specific pattern-matching and condition-checking logic.

Architecture:
- SemanticRule ABC: Interface for all semantic rules
- Concrete rule classes: Implement specific semantic patterns
- SemanticMerger: Orchestrator that applies rules to chunks

Design principle: Keep it simple!
- Only create rule classes for COMPLEX conditions
- Simple "adjacent" pattern matching stays in base class
- No over-engineering - functions are OK where they work
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Set
from .models import Chunk


# ============================================================================
# LEXICAL INDICATORS (Shared Constants)
# ============================================================================

TEMPORAL_WORDS: Set[str] = {
    'h', 'heure', 'heures', 'minute', 'minutes', 'seconde', 'secondes',
    'matin', 'midi', 'après-midi', 'soir', 'nuit', 'minuit',
    'lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi', 'dimanche',
    'jour', 'jours', 'journée',
    'janvier', 'février', 'mars', 'avril', 'mai', 'juin',
    'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre',
    'mois', 'an', 'ans', 'année', 'années', 'semaine', 'semaines',
    'hier', 'aujourd\'hui', 'demain', 'maintenant',
    'ce', 'cette', 'dernier', 'dernière', 'prochain', 'prochaine'
}

PREPOSITIONS: Set[str] = {
    'à', 'de', 'en', 'dans', 'sur', 'sous', 'pour', 'par', 'avec',
    'sans', 'chez', 'vers', 'contre', 'depuis', 'pendant', 'avant',
    'après', 'devant', 'derrière', 'entre', 'parmi', 'selon'
}

RELATIVE_PRONOUNS: Set[str] = {
    'qui', 'que', 'qu\'', 'dont', 'où', 'lequel', 'laquelle',
    'lesquels', 'lesquelles', 'auquel', 'duquel', 'auxquels'
}

QUANTITY_WORDS: Set[str] = {
    'kilo', 'kilos', 'gramme', 'grammes', 'litre', 'litres',
    'mètre', 'mètres', 'centimètre', 'kilomètre',
    'heure', 'heures', 'minute', 'minutes', 'jour', 'jours'
}


# ============================================================================
# SEMANTIC RULE BASE CLASS
# ============================================================================

class SemanticRule(ABC):
    """
    Abstract base class for semantic merging rules.
    
    Each rule defines:
    1. Pattern: Sequence of chunk categories to match (e.g., ["SujV", "SV"])
    2. Result category: Category for merged chunk (e.g., "SV")
    3. Condition: Optional condition that must be satisfied
    
    Subclasses implement check_condition() for complex conditions.
    Simple "adjacent" rules don't need subclasses.
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
        return f"{self.rule_id}({' + '.join(self.pattern)} → {self.result_category})"


# ============================================================================
# SIMPLE RULE (For "adjacent" condition)
# ============================================================================

class AdjacentRule(SemanticRule):
    """
    Rule that matches adjacent chunks with no special conditions.
    
    This handles most simple merging patterns:
    - Subject + Verb: [SujV] + [SV] → [SV]
    - Adverb + Verb: [SAdv] + [SV] → [SV]
    - Preposition + Noun: [SP] + [SN] → [SP]
    - etc.
    """
    
    def check_condition(self, chunks: List[Chunk], start_idx: int) -> bool:
        """Adjacent chunks always satisfy the condition."""
        return True


# ============================================================================
# COMPLEX CONDITION RULES
# ============================================================================

class TemporalMergeRule(SemanticRule):
    """
    Merge temporal noun phrases: [SN] + [SN] → [SN]
    Condition: Both chunks must contain temporal expressions.
    Example: "18 h 30" + "ce lundi 27 janvier"
    """
    
    def check_condition(self, chunks: List[Chunk], start_idx: int) -> bool:
        """Both chunks must contain temporal words."""
        matched_chunks = chunks[start_idx:start_idx + len(self.pattern)]
        
        for chunk in matched_chunks:
            chunk_words = set(chunk.text.lower().split())
            if not (chunk_words & TEMPORAL_WORDS):
                return False
        
        return True


class PrepositionalChainRule(SemanticRule):
    """
    Merge prepositional chains: [SN] + [SN] → [SN]
    Condition: Both chunks must contain prepositions.
    Example: "en urgences" + "à l'hôpital"
    """
    
    def check_condition(self, chunks: List[Chunk], start_idx: int) -> bool:
        """Both chunks must contain prepositions."""
        matched_chunks = chunks[start_idx:start_idx + len(self.pattern)]
        
        for chunk in matched_chunks:
            # Check by UPOS tag
            has_prep = any(t.upos == 'ADP' for t in chunk.tokens)
            # Also check by text
            chunk_words = set(chunk.text.lower().split())
            has_prep = has_prep or bool(chunk_words & PREPOSITIONS)
            
            if not has_prep:
                return False
        
        return True


class VerbDirectObjectRule(SemanticRule):
    """
    Merge verb with direct object: [SV] + [SN] → [SV]
    Condition: No punctuation between chunks.
    Example: "révèle" + "l'impensable"
    """
    
    def check_condition(self, chunks: List[Chunk], start_idx: int) -> bool:
        """Chunks must be adjacent with no punctuation."""
        matched_chunks = chunks[start_idx:start_idx + len(self.pattern)]
        return not any(c.category == 'Pct' for c in matched_chunks)


class AdverbialIntroducerRule(SemanticRule):
    """
    Merge sentence-initial adverbial: [SN] + [Pct] + [SN] + [SV] → [SV]
    Condition: First chunk has preposition, followed by comma.
    Example: "De retour aux urgences" + "," + "les médecins" + "sont"
    """
    
    def check_condition(self, chunks: List[Chunk], start_idx: int) -> bool:
        """First chunk must have preposition, second must be comma."""
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


# ============================================================================
# SEMANTIC MERGER (Orchestrator)
# ============================================================================

class SemanticMerger:
    """
    Orchestrates semantic rule application to merge Level 1 chunks into Level 2.
    
    Uses Strategy pattern: Each rule is a pluggable strategy for merging.
    Supports multi-pass iterative merging until convergence.
    """
    
    def __init__(self, rules: List[SemanticRule]):
        """
        Initialize merger with a list of semantic rules.
        
        Args:
            rules: List of SemanticRule instances
        """
        self.rules = rules
    
    def merge(self, chunks: List[Chunk], multi_pass: bool = False, 
             max_passes: int = 10, debug: bool = False) -> List[Chunk]:
        """
        Apply semantic rules to merge chunks.
        
        Args:
            chunks: List of Level 1 chunks
            multi_pass: If True, apply rules iteratively until convergence
            max_passes: Maximum number of passes
            debug: If True, print detailed debug information
        
        Returns:
            List of Level 2 merged chunks
        """
        if not self.rules:
            print("No semantic rules, returning chunks unchanged")
            return chunks
        
        result = list(chunks)
        total_merges = 0
        pass_count = 0
        
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
                for rule in self.rules:
                    if rule.matches_pattern(result, i):
                        if rule.check_condition(result, i):
                            # Apply the merge
                            if debug:
                                chunks_before = result[i:i + len(rule.pattern)]
                                print(f"  [{i}] {rule.rule_id}:")
                                print(f"      Before: {' + '.join(str(c) for c in chunks_before)}")
                            
                            merged = rule.apply(result, i)
                            
                            if debug:
                                print(f"      After:  {merged}")
                            
                            # Replace matched chunks with merged chunk
                            result[i:i + len(rule.pattern)] = [merged]
                            
                            merges_this_pass += 1
                            total_merges += 1
                            matched = True
                            break  # Move to next position
                
                i += 1
            
            if debug:
                print(f"--- Pass {pass_count} complete: {merges_this_pass} merges ---")
            
            # Check convergence
            if merges_this_pass == 0:
                if debug:
                    print(f"Convergence reached after {pass_count} pass(es)")
                break
            
            if not multi_pass:
                break
            
            if pass_count >= max_passes:
                print(f"Max passes ({max_passes}) reached")
                break
        
        if not debug:
            print(f"Applied {total_merges} semantic merges in {pass_count} pass(es)")
        
        return result


# ============================================================================
# RULE FACTORY
# ============================================================================

def create_rules_from_json(rules_data: List[Dict[str, Any]]) -> List[SemanticRule]:
    """
    Create SemanticRule instances from JSON rule definitions.
    
    Maps condition types to appropriate rule classes:
    - "adjacent" → AdjacentRule
    - "both_temporal" → TemporalMergeRule
    - "both_have_preposition" → PrepositionalChainRule
    - "adjacent_no_punctuation" → VerbDirectObjectRule
    - "first_is_adverbial_and_comma" → AdverbialIntroducerRule
    
    Args:
        rules_data: List of rule dictionaries from JSON
    
    Returns:
        List of SemanticRule instances
    """
    rules = []
    
    for rule_dict in rules_data:
        pattern = rule_dict.get('pattern', [])
        result_cat = rule_dict.get('result_category', '')
        rule_id = rule_dict.get('rule_id', '')
        condition = rule_dict.get('condition', 'adjacent')
        
        # Map condition to rule class
        if condition == 'both_temporal':
            rule = TemporalMergeRule(pattern, result_cat, rule_id)
        elif condition == 'both_have_preposition':
            rule = PrepositionalChainRule(pattern, result_cat, rule_id)
        elif condition == 'adjacent_no_punctuation':
            rule = VerbDirectObjectRule(pattern, result_cat, rule_id)
        elif condition == 'first_is_adverbial_and_comma':
            rule = AdverbialIntroducerRule(pattern, result_cat, rule_id)
        else:
            # Default: "adjacent" and other simple conditions
            rule = AdjacentRule(pattern, result_cat, rule_id)
        
        rules.append(rule)
    
    return rules

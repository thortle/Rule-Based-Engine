#!/usr/bin/env python3
"""
Chunk Validator - Level 1.5 Constituent Validation

This module implements linguistic constituency tests to validate that chunks
correspond to valid syntactic constituents. It bridges the gap between 
UD-based dependency parsing (Level 1) and semantic merging (Level 2).

Based on constituency tests from linguistic theory:
1. Pronominal substitution (can chunk be replaced by a pronoun?)
2. Coordination (can two instances be coordinated with 'et'?)
3. Dislocation (can it be moved with pronominal resumption?)
4. Cleft construction (works with 'C'est ... que/qui'?)
5. Fragment answer (can it answer a question in isolation?)

References:
- Syntaxe course (M2 IDL - UGA), TD1 slides
- Universal Dependencies framework
- French constituent structure principles
"""

from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple
from linguistic_chunker import Chunk, UDToken, UDSentence
import json
import re


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class ValidationScore:
    """
    Scores for individual constituency tests and aggregate.
    
    All scores range from 0.0 (fails test) to 1.0 (passes test).
    Partial scores (0.3, 0.5, 0.7) indicate uncertain cases.
    
    Attributes:
        substitution: Pronominal substitution test score
        coordination: Coordination test score
        dislocation: Dislocation test score
        cleft: Cleft construction test score
        fragment: Fragment answer test score
        aggregate: Overall constituency score (weighted average or minimum)
    """
    substitution: float = 0.0
    coordination: float = 0.0
    dislocation: float = 0.0
    cleft: float = 0.0
    fragment: float = 0.0
    aggregate: float = 0.0
    
    def __repr__(self):
        return f"ValidationScore(agg={self.aggregate:.2f}, sub={self.substitution:.2f}, coord={self.coordination:.2f}, disl={self.dislocation:.2f}, cleft={self.cleft:.2f}, frag={self.fragment:.2f})"


@dataclass
class ValidatedChunk:
    """
    A chunk with constituency validation metadata.
    
    Attributes:
        chunk: Original Chunk object from Level 1
        score: ValidationScore with test results
        flags: List of issues/warnings (e.g., ["low_substitution", "possible_split"])
        passed: Whether chunk meets minimum validation threshold
    """
    chunk: Chunk
    score: ValidationScore
    flags: List[str] = field(default_factory=list)
    passed: bool = True
    
    @property
    def text(self) -> str:
        """Convenience property for chunk text"""
        return self.chunk.text
    
    @property
    def category(self) -> str:
        """Convenience property for chunk category"""
        return self.chunk.category
    
    @property
    def tokens(self) -> List[UDToken]:
        """Convenience property for chunk tokens"""
        return self.chunk.tokens
    
    def __repr__(self):
        status = "✓" if self.passed else "✗"
        flags_str = f" [{', '.join(self.flags)}]" if self.flags else ""
        return f"{status} [{self.category}] {self.text} {self.score}{flags_str}"


# ============================================================================
# FRENCH LINGUISTIC PATTERNS
# ============================================================================

class FrenchPatterns:
    """
    French linguistic patterns for constituency tests.
    
    These patterns are used to construct test sentences and recognize
    valid constituency constructions in French.
    """
    
    # Pronouns for substitution test
    SUBJECT_PRONOUNS = {'il', 'elle', 'ils', 'elles', 'on', 'cela', 'ça', 'ce'}
    OBJECT_PRONOUNS = {'le', 'la', 'les', 'l\''}
    OBLIQUE_PRONOUNS = {'lui', 'leur', 'y', 'en'}
    REFLEXIVE_PRONOUNS = {'me', 'm\'', 'te', 't\'', 'se', 's\'', 'nous', 'vous'}
    
    # Cleft constructions
    CLEFT_PATTERNS = [
        r"^c'est\s+(.+?)\s+(que|qui)",  # c'est ... que/qui
        r"^ce\s+sont\s+(.+?)\s+(que|qui)",  # ce sont ... que/qui
    ]
    
    # Question words for fragment answer test
    QUESTION_WORDS = {
        'qui': ['SN', 'SujV'],  # who (person)
        'que': ['SN', 'SV'],  # what
        'quoi': ['SN'],  # what
        'où': ['SP', 'SAdv'],  # where
        'quand': ['SAdv', 'SP'],  # when
        'comment': ['SAdv'],  # how
        'pourquoi': ['SP', 'SAdv'],  # why
        'combien': ['SN', 'SAdv'],  # how many/much
        'lequel': ['SN'],  # which one
        'laquelle': ['SN'],
        'lesquels': ['SN'],
        'lesquelles': ['SN'],
    }
    
    # Coordination markers
    COORDINATORS = {'et', 'ou', 'mais', 'ni', 'or', 'car'}
    
    # Prepositions for dislocation (à, de required for en/y)
    PREPOSITIONS_TO_Y = {'à', 'dans', 'sur', 'sous', 'chez', 'vers'}
    PREPOSITIONS_TO_EN = {'de', 'des', 'du'}


# ============================================================================
# CHUNK VALIDATOR
# ============================================================================

class ChunkValidator:
    """
    Validates chunks using linguistic constituency tests.
    
    This class implements five constituency tests based on French syntax:
    1. Pronominal substitution
    2. Coordination
    3. Dislocation
    4. Cleft construction
    5. Fragment answer
    
    Usage:
        validator = ChunkValidator(lang='fr')
        validated_chunks = validator.validate_all(chunks, sentence, ud_tree)
    """
    
    def __init__(self, lang: str = 'fr', patterns_file: Optional[str] = None):
        """
        Initialize chunk validator.
        
        Args:
            lang: Language code ('fr' for French)
            patterns_file: Optional JSON file with custom patterns
        """
        self.lang = lang
        self.patterns = FrenchPatterns()
        
        # Load custom patterns if provided
        if patterns_file:
            self._load_patterns(patterns_file)
        
        # Weights for aggregate score calculation
        # Equal weights by default, but can be customized
        self.weights = {
            'substitution': 0.25,
            'coordination': 0.20,
            'dislocation': 0.20,
            'cleft': 0.20,
            'fragment': 0.15,
        }
    
    def _load_patterns(self, patterns_file: str):
        """Load custom linguistic patterns from JSON file"""
        try:
            with open(patterns_file, 'r', encoding='utf-8') as f:
                custom_patterns = json.load(f)
                # Update patterns from file
                # (Implementation can be extended)
                print(f"✓ Loaded custom patterns from {patterns_file}")
        except FileNotFoundError:
            print(f"⚠️  Patterns file not found: {patterns_file}")
        except json.JSONDecodeError as e:
            print(f"⚠️  Error parsing patterns file: {e}")
    
    # ========================================================================
    # VALIDATION INTERFACE
    # ========================================================================
    
    def validate_chunk(self, chunk: Chunk, sentence: UDSentence, 
                      all_chunks: List[Chunk]) -> ValidatedChunk:
        """
        Validate a single chunk using all constituency tests.
        
        Args:
            chunk: Chunk to validate
            sentence: Original UDSentence for context
            all_chunks: All chunks in sentence (for coordination test)
        
        Returns:
            ValidatedChunk with scores and flags
        """
        # Check if this is a structural marker (function word)
        is_structural = chunk.category in ['Coord', 'CSub', 'Pct']
        
        # Run all five tests
        sub_score = self.test_pronominal_substitution(chunk, sentence)
        coord_score = self.test_coordination(chunk, all_chunks)
        disl_score = self.test_dislocation(chunk, sentence)
        cleft_score = self.test_cleft(chunk, sentence)
        frag_score = self.test_fragment_answer(chunk, sentence)
        
        # Create validation score
        score = ValidationScore(
            substitution=sub_score,
            coordination=coord_score,
            dislocation=disl_score,
            cleft=cleft_score,
            fragment=frag_score,
            aggregate=self._calculate_aggregate(
                sub_score, coord_score, disl_score, cleft_score, frag_score
            )
        )
        
        # Generate flags for low-scoring tests
        flags = self._generate_flags(score, chunk)
        
        # Determine pass/fail
        # Structural markers don't need to pass constituency tests
        if is_structural:
            passed = True  # Accept as valid structural markers
            flags.append("structural_marker")
        else:
            passed = score.aggregate >= 0.4  # Normal threshold
        
        return ValidatedChunk(chunk=chunk, score=score, flags=flags, passed=passed)
    
    def validate_all(self, chunks: List[Chunk], sentence: UDSentence) -> List[ValidatedChunk]:
        """
        Validate all chunks in a sentence.
        
        Structural markers (Coord, CSub, Pct) are automatically marked as passed
        without running full constituency tests, since they serve a different
        linguistic function.
        
        Args:
            chunks: List of chunks from Level 1
            sentence: Original UDSentence
        
        Returns:
            List of ValidatedChunk objects with scores
        """
        validated = []
        for chunk in chunks:
            validated_chunk = self.validate_chunk(chunk, sentence, chunks)
            validated.append(validated_chunk)
        return validated
    
    def _calculate_aggregate(self, sub: float, coord: float, disl: float, 
                            cleft: float, frag: float) -> float:
        """
        Calculate aggregate constituency score.
        
        Strategy: Weighted average, but penalize if any critical test fails badly.
        
        Args:
            sub, coord, disl, cleft, frag: Individual test scores
        
        Returns:
            Aggregate score (0.0 - 1.0)
        """
        # Weighted average
        weighted = (
            sub * self.weights['substitution'] +
            coord * self.weights['coordination'] +
            disl * self.weights['dislocation'] +
            cleft * self.weights['cleft'] +
            frag * self.weights['fragment']
        )
        
        # Apply penalty if substitution OR coordination fail badly (< 0.2)
        # These are the most reliable tests
        if sub < 0.2 or coord < 0.2:
            weighted *= 0.7  # 30% penalty
        
        return round(weighted, 3)
    
    def _generate_flags(self, score: ValidationScore, chunk: Chunk) -> List[str]:
        """
        Generate warning flags based on test scores.
        
        Args:
            score: ValidationScore object
            chunk: Original chunk
        
        Returns:
            List of flag strings
        """
        flags = []
        
        if score.substitution < 0.3:
            flags.append("low_substitution")
        if score.coordination < 0.3:
            flags.append("low_coordination")
        if score.dislocation < 0.3:
            flags.append("low_dislocation")
        if score.cleft < 0.3:
            flags.append("low_cleft")
        if score.fragment < 0.3:
            flags.append("low_fragment")
        
        # Check for single-token chunks (often problematic)
        if len(chunk.tokens) == 1:
            flags.append("single_token")
        
        # Check for very long chunks (might need splitting)
        if len(chunk.tokens) > 10:
            flags.append("very_long")
        
        return flags
    
    # ========================================================================
    # CONSTITUENCY TESTS (TO BE IMPLEMENTED)
    # ========================================================================
    
    def test_pronominal_substitution(self, chunk: Chunk, sentence: UDSentence) -> float:
        """
        Test if chunk can be replaced by a pronoun.
        
        Linguistic principle: A constituent can be replaced by a pronoun
        while maintaining grammaticality. Different chunk types map to
        different pronouns:
        - SN (noun phrases) → il, elle, le, la, cela
        - SP (prepositional phrases) → y (location), en (partitive)
        - SujV (subject pronouns) → already pronouns (n/a)
        
        Strategy:
        1. Check chunk category
        2. Verify content words present (not just function words)
        3. Check POS patterns for pronominalizability
        4. Apply penalties for problematic cases
        
        Args:
            chunk: Chunk to test
            sentence: Full sentence context
        
        Returns:
            Score 0.0 - 1.0 (0.0 = cannot substitute, 1.0 = clear substitution)
        """
        score = 0.5  # Default neutral score
        
        # Check if chunk has content words
        content_pos = {'NOUN', 'PROPN', 'NUM'}
        has_content = any(t.upos in content_pos for t in chunk.tokens)
        
        # SN (Noun phrases) - highest substitutability
        if chunk.category == 'SN':
            if has_content:
                score = 0.9
                # Check for proper structure (has determiner or head noun)
                has_det = any(t.upos == 'DET' for t in chunk.tokens)
                has_noun = any(t.upos in {'NOUN', 'PROPN'} for t in chunk.tokens)
                if has_det and has_noun:
                    score = 1.0  # Perfect structure
                elif has_noun:
                    score = 0.85  # Missing det but has noun
            else:
                score = 0.3  # No content words (likely just determiners)
        
        # SP (Prepositional phrases) - can be replaced by y/en
        elif chunk.category == 'SP':
            # Check for preposition + nominal
            has_prep = any(t.upos == 'ADP' for t in chunk.tokens)
            if has_prep and has_content:
                # Check preposition type for y/en compatibility
                first_token = chunk.tokens[0]
                if first_token.upos == 'ADP':
                    prep_lemma = first_token.lemma.lower()
                    # Prepositions compatible with 'y'
                    if prep_lemma in self.patterns.PREPOSITIONS_TO_Y:
                        score = 0.8
                    # Prepositions compatible with 'en'
                    elif prep_lemma in self.patterns.PREPOSITIONS_TO_EN:
                        score = 0.8
                    else:
                        score = 0.6  # Other prepositions (less clear)
            else:
                score = 0.4  # Incomplete PP
        
        # SujV (Subject pronouns) - already pronouns
        elif chunk.category == 'SujV':
            # Already a pronoun, so substitution test not applicable
            # But presence indicates a valid constituent
            score = 0.7  # Neutral-positive (it's already minimal)
        
        # SV (Verb phrases) - complex, lower substitutability
        elif chunk.category == 'SV':
            has_verb = any(t.upos in {'VERB', 'AUX'} for t in chunk.tokens)
            if has_verb:
                # VPs can sometimes be replaced by "le faire", "ainsi", etc.
                # but this is less reliable than NP pronouns
                score = 0.5
            else:
                score = 0.2
        
        # SAdj/SAdv - low substitutability
        elif chunk.category in ['SAdj', 'SAdv']:
            score = 0.4  # Adjectives/adverbs rarely pronominalize well
        
        # Coordination, subordination - not substitutable
        elif chunk.category in ['Coord', 'CSub']:
            score = 0.1  # Function words, not constituents
        
        # Punctuation
        elif chunk.category == 'Pct':
            score = 0.0  # Not a constituent
        
        # Apply penalties
        # Single token chunks (unless proper nouns)
        if len(chunk.tokens) == 1:
            if chunk.tokens[0].upos not in {'PROPN', 'PRON'}:
                score *= 0.7
        
        # Only function words (no content)
        if not has_content and chunk.category not in ['SujV', 'Pro_Obj']:
            score *= 0.3
        
        return round(score, 3)
    
    def test_coordination(self, chunk: Chunk, all_chunks: List[Chunk]) -> float:
        """
        Test if chunk can be coordinated with similar chunks.
        
        Linguistic principle: True constituents can be coordinated with
        other constituents of the same type using "et", "ou", "mais".
        Example: "[le chat] et [la souris]" ✓
        
        Strategy:
        1. Find chunks with same category in sentence
        2. Check structural similarity (POS patterns, length)
        3. Verify syntactic parallelism
        4. Higher score if multiple similar chunks exist
        
        Args:
            chunk: Chunk to test
            all_chunks: All chunks in sentence
        
        Returns:
            Score 0.0 - 1.0 (0.0 = no coordination, 1.0 = clear coordination)
        """
        score = 0.4  # Default neutral score
        
        # Punctuation and connectors cannot be coordinated
        if chunk.category in ['Pct', 'Coord', 'CSub']:
            return 0.0
        
        # Find similar chunks (same category, exclude self)
        similar_chunks = [c for c in all_chunks 
                         if c.category == chunk.category and c != chunk]
        
        if not similar_chunks:
            # No similar chunks to coordinate with
            # This is neutral, not negative (sentence might only have one SN)
            return 0.5
        
        # Score based on number of similar chunks
        # More similar chunks = higher confidence that category is well-defined
        similar_count = len(similar_chunks)
        if similar_count >= 3:
            score = 0.9  # Many coordination partners
        elif similar_count == 2:
            score = 0.8
        elif similar_count == 1:
            score = 0.7
        
        # Check structural similarity with most similar chunk
        # Compare POS patterns and length
        chunk_pos_pattern = tuple(t.upos for t in chunk.tokens)
        
        best_similarity = 0.0
        for other in similar_chunks:
            other_pos_pattern = tuple(t.upos for t in other.tokens)
            
            # Calculate pattern similarity
            if chunk_pos_pattern == other_pos_pattern:
                # Identical patterns - perfect coordination candidate
                similarity = 1.0
            else:
                # Partial similarity based on shared POS tags
                common = set(chunk_pos_pattern) & set(other_pos_pattern)
                total = set(chunk_pos_pattern) | set(other_pos_pattern)
                similarity = len(common) / len(total) if total else 0.0
            
            # Length similarity (prefer similar-length chunks)
            len_ratio = min(len(chunk.tokens), len(other.tokens)) / max(len(chunk.tokens), len(other.tokens))
            similarity = (similarity + len_ratio) / 2
            
            best_similarity = max(best_similarity, similarity)
        
        # Combine count-based score with structural similarity
        final_score = (score + best_similarity) / 2
        
        # Boost for highly coordinable categories
        if chunk.category in ['SN', 'SAdj', 'SP']:
            final_score = min(1.0, final_score * 1.1)
        
        # Penalty for categories that coordinate less well
        elif chunk.category in ['SV', 'SAdv']:
            final_score *= 0.9
        
        return round(final_score, 3)
    
    def test_dislocation(self, chunk: Chunk, sentence: UDSentence) -> float:
        """
        Test if chunk can be dislocated with pronominal resumption.
        
        Linguistic principle: Constituents can be moved to sentence periphery
        (left or right) with a resumptive pronoun.
        Example: "Le petit chat, Kim le regarde" (left dislocation)
                 "À Paris, j'y vais demain" (locative with y)
        
        Strategy:
        1. Check if chunk can be an argument (not predicate)
        2. Determine appropriate resumptive pronoun (le/la/y/en)
        3. Verify chunk is not already a function word
        4. Check syntactic role (objects/obliques dislocate better)
        
        Args:
            chunk: Chunk to test
            sentence: Full sentence context
        
        Returns:
            Score 0.0 - 1.0 (0.0 = cannot dislocate, 1.0 = clear dislocation)
        """
        score = 0.4  # Default neutral
        
        # Check for content words
        has_content = any(t.upos in {'NOUN', 'PROPN', 'NUM'} for t in chunk.tokens)
        
        # SN (Noun phrases) - excellent dislocation candidates
        if chunk.category == 'SN':
            if has_content:
                # Check syntactic role via dependency relations
                # Objects and complements dislocate well
                deprels = {t.deprel.split(':')[0] for t in chunk.tokens}
                if deprels & {'obj', 'iobj', 'obl', 'nmod'}:
                    score = 0.9  # Clear argument role
                else:
                    score = 0.7  # Possible argument
            else:
                score = 0.3  # No content (unlikely to dislocate)
        
        # SP (Prepositional phrases) - very good dislocation candidates
        elif chunk.category == 'SP':
            has_prep = any(t.upos == 'ADP' for t in chunk.tokens)
            if has_prep and has_content:
                # Check preposition type
                first_token = chunk.tokens[0]
                if first_token.upos == 'ADP':
                    prep_lemma = first_token.lemma.lower()
                    # Locative prepositions → y
                    if prep_lemma in self.patterns.PREPOSITIONS_TO_Y:
                        score = 0.85  # "À Paris, j'y vais"
                    # Partitive de → en
                    elif prep_lemma in self.patterns.PREPOSITIONS_TO_EN:
                        score = 0.85  # "De ce livre, j'en parle"
                    else:
                        score = 0.6  # Other PPs (less standard)
            else:
                score = 0.3
        
        # SujV (Subject pronouns) - generally don't dislocate
        # (Subjects are usually in canonical position)
        elif chunk.category == 'SujV':
            score = 0.3  # Low but not zero (emphatic contexts possible)
        
        # SV (Verb phrases) - predicates don't dislocate
        elif chunk.category == 'SV':
            score = 0.2  # Very low (verbs are predicates)
        
        # SAdv (Adverbials) - can sometimes dislocate
        elif chunk.category == 'SAdv':
            # Temporal/manner adverbs can be fronted
            score = 0.5
        
        # SAdj (Adjectives) - rarely dislocate
        elif chunk.category == 'SAdj':
            score = 0.3
        
        # Function words - cannot dislocate
        elif chunk.category in ['Coord', 'CSub', 'Pct']:
            score = 0.0
        
        # Apply penalties
        # Single token (unless proper noun)
        if len(chunk.tokens) == 1:
            if chunk.tokens[0].upos not in {'PROPN'}:
                score *= 0.7
        
        # Only function words
        if not has_content and chunk.category not in ['SujV']:
            score *= 0.3
        
        return round(score, 3)
    
    def test_cleft(self, chunk: Chunk, sentence: UDSentence) -> float:
        """
        Test if chunk works in cleft construction.
        
        Linguistic principle: Constituents can appear in cleft sentences
        for focus/emphasis: "C'est [CHUNK] que/qui ..."
        Example: "C'est [le petit chat] qui a mangé"
        
        Strategy:
        1. Check chunk category (NPs work best)
        2. Verify not a verb or auxiliary (predicates don't cleft)
        3. Check for content words (focused elements must be meaningful)
        4. Consider semantic appropriateness for focus
        
        Args:
            chunk: Chunk to test
            sentence: Full sentence context
        
        Returns:
            Score 0.0 - 1.0 (0.0 = incompatible, 1.0 = clear cleft)
        """
        score = 0.4  # Default neutral
        
        # Check for content words
        has_content = any(t.upos in {'NOUN', 'PROPN', 'NUM', 'ADJ'} 
                         for t in chunk.tokens)
        
        # SN (Noun phrases) - best cleft candidates
        if chunk.category == 'SN':
            if has_content:
                # Check if it's a full NP (not just determiner)
                has_noun = any(t.upos in {'NOUN', 'PROPN'} for t in chunk.tokens)
                if has_noun:
                    score = 0.95  # "C'est [le petit chat] qui..."
                else:
                    score = 0.6  # Just numbers or partial
            else:
                score = 0.3  # Only determiners (not focus-worthy)
        
        # SP (Prepositional phrases) - good cleft candidates for adjuncts
        elif chunk.category == 'SP':
            has_prep = any(t.upos == 'ADP' for t in chunk.tokens)
            if has_prep and has_content:
                score = 0.75  # "C'est [à Paris] que je vais"
            else:
                score = 0.4
        
        # SAdv (Adverbials) - can cleft for emphasis
        elif chunk.category == 'SAdv':
            # "C'est [hier] que je l'ai vu"
            score = 0.65
        
        # SAdj (Adjectives) - can cleft in predicate position
        elif chunk.category == 'SAdj':
            # "C'est [très grand] qu'il est"
            score = 0.5
        
        # SujV (Subject pronouns) - can cleft emphatic subjects
        elif chunk.category == 'SujV':
            # "C'est [lui] qui a mangé"
            score = 0.6
        
        # SV (Verb phrases) - predicates don't cleft well
        elif chunk.category == 'SV':
            # Verbs are the predicate, not the focused argument
            score = 0.15
        
        # Function words - cannot cleft
        elif chunk.category in ['Coord', 'CSub', 'Pct']:
            score = 0.0
        
        # Pro_Obj (Object pronouns) - already clitics, don't cleft
        elif chunk.category == 'Pro_Obj':
            score = 0.2
        
        # Additional checks
        # Verbs and auxiliaries should not be clefted
        has_verb = any(t.upos in {'VERB', 'AUX'} for t in chunk.tokens)
        if has_verb and chunk.category == 'SV':
            score *= 0.2  # Strong penalty for verbs
        
        # Single function words
        if len(chunk.tokens) == 1 and not has_content:
            score *= 0.3
        
        return round(score, 3)
    
    def test_fragment_answer(self, chunk: Chunk, sentence: UDSentence) -> float:
        """
        Test if chunk can answer a question in isolation.
        
        Linguistic principle: True constituents can serve as fragment answers
        to appropriate questions.
        Example: Q: "Qui a rencontré une souris?" A: "[Le petit chat]" ✓
        
        Strategy:
        1. Check if chunk has content words (not just function words)
        2. Map chunk category to compatible question types
        3. Verify semantic completeness (can stand alone)
        4. Check that chunk is not dependent on sentence structure
        
        Args:
            chunk: Chunk to test
            sentence: Full sentence context
        
        Returns:
            Score 0.0 - 1.0 (0.0 = cannot answer, 1.0 = clear fragment)
        """
        score = 0.4  # Default neutral
        
        # Check for content words (essential for fragment answers)
        content_pos = {'NOUN', 'PROPN', 'NUM', 'VERB', 'ADJ', 'ADV'}
        has_content = any(t.upos in content_pos for t in chunk.tokens)
        
        if not has_content:
            # No content words → cannot be meaningful fragment answer
            return 0.1
        
        # Count content words
        content_count = sum(1 for t in chunk.tokens if t.upos in content_pos)
        
        # SN (Noun phrases) - excellent fragment answers
        if chunk.category == 'SN':
            # Can answer: Qui? Que? Quoi? Combien? Quel? Lequel?
            has_noun = any(t.upos in {'NOUN', 'PROPN'} for t in chunk.tokens)
            has_det = any(t.upos == 'DET' for t in chunk.tokens)
            
            if has_noun:
                if has_det or len(chunk.tokens) >= 2:
                    score = 0.95  # Full NP: "le petit chat"
                else:
                    score = 0.8  # Bare noun: "Paris"
            else:
                score = 0.6  # Numbers or partial: "trois"
        
        # SP (Prepositional phrases) - good fragment answers
        elif chunk.category == 'SP':
            # Can answer: Où? Quand? Comment? Pourquoi?
            has_prep = any(t.upos == 'ADP' for t in chunk.tokens)
            if has_prep and content_count >= 1:
                score = 0.85  # "à Paris", "avec soin"
            else:
                score = 0.5
        
        # SAdv (Adverbials) - good fragment answers
        elif chunk.category == 'SAdv':
            # Can answer: Quand? Comment? Où? Combien?
            if content_count >= 1:
                score = 0.8  # "hier", "très vite"
            else:
                score = 0.4
        
        # SV (Verb phrases) - can answer "Que fait-il?"
        elif chunk.category == 'SV':
            has_verb = any(t.upos in {'VERB', 'AUX'} for t in chunk.tokens)
            if has_verb:
                score = 0.7  # "mange une pomme"
            else:
                score = 0.3
        
        # SAdj (Adjectives) - can answer "Comment?"
        elif chunk.category == 'SAdj':
            has_adj = any(t.upos == 'ADJ' for t in chunk.tokens)
            if has_adj:
                score = 0.65  # "très grand"
            else:
                score = 0.3
        
        # SujV (Subject pronouns) - weak fragment answers
        elif chunk.category == 'SujV':
            # Pronouns can answer "Qui?" but lack specificity
            score = 0.4  # "il", "elle" (not very informative)
        
        # Pro_Obj (Object pronouns) - very weak fragments
        elif chunk.category == 'Pro_Obj':
            score = 0.2  # Clitics don't stand alone well
        
        # Function words - cannot be fragments
        elif chunk.category in ['Coord', 'CSub', 'Pct']:
            score = 0.0
        
        # Boost for multi-word chunks (more complete)
        if len(chunk.tokens) >= 3 and content_count >= 2:
            score = min(1.0, score * 1.1)
        
        # Penalty for single function words
        if len(chunk.tokens) == 1 and not has_content:
            score *= 0.2
        
        return round(score, 3)
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def get_statistics(self, validated_chunks: List[ValidatedChunk]) -> Dict[str, float]:
        """
        Calculate validation statistics for a set of chunks.
        
        Args:
            validated_chunks: List of validated chunks
        
        Returns:
            Dictionary with statistical metrics
        """
        if not validated_chunks:
            return {}
        
        scores = [vc.score for vc in validated_chunks]
        
        return {
            'total_chunks': len(validated_chunks),
            'passed_chunks': sum(1 for vc in validated_chunks if vc.passed),
            'pass_rate': sum(1 for vc in validated_chunks if vc.passed) / len(validated_chunks),
            'avg_aggregate': sum(s.aggregate for s in scores) / len(scores),
            'avg_substitution': sum(s.substitution for s in scores) / len(scores),
            'avg_coordination': sum(s.coordination for s in scores) / len(scores),
            'avg_dislocation': sum(s.dislocation for s in scores) / len(scores),
            'avg_cleft': sum(s.cleft for s in scores) / len(scores),
            'avg_fragment': sum(s.fragment for s in scores) / len(scores),
            'min_aggregate': min(s.aggregate for s in scores),
            'max_aggregate': max(s.aggregate for s in scores),
        }
    
    def filter_by_score(self, validated_chunks: List[ValidatedChunk], 
                       min_score: float = 0.4) -> List[ValidatedChunk]:
        """
        Filter chunks by minimum aggregate score.
        
        Args:
            validated_chunks: List of validated chunks
            min_score: Minimum acceptable aggregate score
        
        Returns:
            Filtered list of chunks
        """
        return [vc for vc in validated_chunks if vc.score.aggregate >= min_score]
    
    def get_low_confidence_chunks(self, validated_chunks: List[ValidatedChunk],
                                 threshold: float = 0.4) -> List[ValidatedChunk]:
        """
        Get chunks with low validation scores for manual review.
        
        Args:
            validated_chunks: List of validated chunks
            threshold: Score threshold for "low confidence"
        
        Returns:
            List of low-confidence chunks
        """
        return [vc for vc in validated_chunks if vc.score.aggregate < threshold]


# ============================================================================
# MAIN (FOR TESTING)
# ============================================================================

if __name__ == "__main__":
    print("Chunk Validator - Level 1.5 Constituent Validation")
    print("=" * 60)
    print("\nThis module provides constituency validation for chunks.")
    print("Use it as part of the main pipeline or import for testing.")
    print("\nExample usage:")
    print("    from chunk_validator import ChunkValidator")
    print("    validator = ChunkValidator(lang='fr')")
    print("    validated = validator.validate_all(chunks, sentence)")

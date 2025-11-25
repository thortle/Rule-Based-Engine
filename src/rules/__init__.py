"""
Semantic Rules Module - Organized Rule-Based Engine

This package contains the semantic rule system for Level 2 chunk merging.
Files are organized by responsibility to maintain readability and extensibility.

Exports:
    - SemanticRule: Abstract base class for all rules
    - AdjacentRule: Simple rule for adjacent chunks
    - Complex rules: TemporalMergeRule, PrepositionalChainRule, etc.
    - SemanticMerger: Orchestrator for applying rules
    - create_rules_from_json: Factory for creating rules from JSON
    - Constants: TEMPORAL_WORDS, PREPOSITIONS, etc.
"""

from .constants import (
    TEMPORAL_WORDS,
    PREPOSITIONS,
    RELATIVE_PRONOUNS,
    QUANTITY_WORDS
)

from .base import SemanticRule
from .simple_rules import AdjacentRule
from .complex_rules import (
    TemporalMergeRule,
    PrepositionalChainRule,
    VerbDirectObjectRule,
    AdverbialIntroducerRule
)
from .merger import SemanticMerger
from .factory import create_rules_from_json

__all__ = [
    # Base class
    'SemanticRule',
    
    # Simple rules
    'AdjacentRule',
    
    # Complex rules
    'TemporalMergeRule',
    'PrepositionalChainRule',
    'VerbDirectObjectRule',
    'AdverbialIntroducerRule',
    
    # Orchestrator
    'SemanticMerger',
    
    # Factory
    'create_rules_from_json',
    
    # Constants
    'TEMPORAL_WORDS',
    'PREPOSITIONS',
    'RELATIVE_PRONOUNS',
    'QUANTITY_WORDS',
]

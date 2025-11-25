"""
Rule Factory - Dynamic Rule Creation from JSON

This module implements the Factory pattern to create SemanticRule instances
from JSON configuration files. This allows adding new rules without code changes.

Design patterns:
- Factory: Centralizes object creation logic
- Open/Closed Principle: Open for extension (new rules), closed for modification
"""

from typing import List, Dict, Any
from .base import SemanticRule
from .simple_rules import AdjacentRule
from .complex_rules import (
    TemporalMergeRule,
    PrepositionalChainRule,
    VerbDirectObjectRule,
    AdverbialIntroducerRule
)


# Mapping: condition string → rule class
# **Factory Pattern Example:**
# This map allows creating the correct rule class based on JSON configuration
RULE_CLASS_MAP = {
    'both_temporal': TemporalMergeRule,
    'both_have_preposition': PrepositionalChainRule,
    'adjacent_no_punctuation': VerbDirectObjectRule,
    'first_is_adverbial_and_comma': AdverbialIntroducerRule,
}


def create_rules_from_json(rules_data: List[Dict[str, Any]]) -> List[SemanticRule]:
    """
    Create SemanticRule instances from JSON rule definitions.
    
    **Factory Pattern Implementation:**
    This function acts as a factory that:
    1. Reads configuration data (JSON)
    2. Selects the appropriate class from RULE_CLASS_MAP
    3. Instantiates and returns the correct rule object
    
    **Open/Closed Principle (SOLID):**
    To add a new rule type:
    1. Create new rule class (extends SemanticRule)
    2. Add mapping to RULE_CLASS_MAP
    3. Add rule to JSON config
    NO modification of existing code needed!
    
    Maps condition types to appropriate rule classes:
    - "adjacent" → AdjacentRule (default)
    - "both_temporal" → TemporalMergeRule
    - "both_have_preposition" → PrepositionalChainRule
    - "adjacent_no_punctuation" → VerbDirectObjectRule
    - "first_is_adverbial_and_comma" → AdverbialIntroducerRule
    
    Args:
        rules_data: List of rule dictionaries from JSON
    
    Returns:
        List of SemanticRule instances
    
    Example JSON:
        {
            "rule_id": "temporal_merge",
            "pattern": ["SN", "SN"],
            "result_category": "SN",
            "condition": "both_temporal"
        }
    """
    rules = []
    
    for rule_dict in rules_data:
        pattern = rule_dict.get('pattern', [])
        result_cat = rule_dict.get('result_category', '')
        rule_id = rule_dict.get('rule_id', '')
        condition = rule_dict.get('condition', 'adjacent')
        
        # Factory: Map condition to rule class
        # Uses .get() with default to handle unknown conditions gracefully
        rule_class = RULE_CLASS_MAP.get(condition, AdjacentRule)
        
        # Instantiate the appropriate rule class
        rule = rule_class(pattern, result_cat, rule_id)
        rules.append(rule)
    
    return rules

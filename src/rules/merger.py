"""
Semantic Merger - Rule Application Orchestrator

This module coordinates the application of semantic rules to merge chunks.
It implements the orchestration logic with support for multi-pass merging.

Design patterns:
- Strategy: Uses interchangeable SemanticRule strategies
- Dependency Inversion: Depends on SemanticRule abstraction, not concrete classes
"""

from typing import List
from .base import SemanticRule
from ..models import Chunk


class SemanticMerger:
    """
    Orchestrates semantic rule application to merge Level 1 chunks into Level 2.
    
    Uses Strategy pattern: Each rule is a pluggable strategy for merging.
    Supports multi-pass iterative merging until convergence.
    
    **Dependency Inversion Principle (SOLID):**
    SemanticMerger depends on the SemanticRule ABSTRACTION, not concrete classes.
    This allows injecting ANY rule implementation without modifying this class.
    
    **Single Responsibility Principle (SOLID):**
    This class has ONE job: orchestrate rule application.
    It doesn't implement merging logic itself - that's delegated to rules.
    
    **Encapsulation Example:**
    The merging algorithm details are hidden inside merge().
    Clients just call merge() and get results - implementation is encapsulated.
    """
    
    def __init__(self, rules: List[SemanticRule]):
        """
        Initialize merger with a list of semantic rules.
        
        Args:
            rules: List of SemanticRule instances (dependency injection)
        """
        self.rules = rules
    
    def merge(self, chunks: List[Chunk], multi_pass: bool = False, 
             max_passes: int = 10, debug: bool = False) -> List[Chunk]:
        """
        Apply semantic rules to merge chunks.
        
        **Strategy Pattern in Action:**
        Iterates through self.rules and applies each strategy (rule).
        Each rule implements check_condition() and apply() differently,
        but they're all used through the same SemanticRule interface.
        
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
                # **Polymorphism in action:** Each rule behaves differently
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

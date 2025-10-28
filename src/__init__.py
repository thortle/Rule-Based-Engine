#!/usr/bin/env python3
"""
Rule-Based French Text Chunker - Core Package

This package contains the core modules for UD-based French text chunking.
"""

from .models import Token, Chunk, Sentence
from .chunkers import Chunker, UDChunker
from .semantic_rules import SemanticRule, SemanticMerger, create_rules_from_json
from .pipeline import ChunkerPipeline

__all__ = [
    'Token', 'Chunk', 'Sentence',
    'Chunker', 'UDChunker',
    'SemanticRule', 'SemanticMerger', 'create_rules_from_json',
    'ChunkerPipeline'
]

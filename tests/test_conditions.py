#!/usr/bin/env python3
"""
Tests for token-level condition checking functions
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from linguistic_chunker import UDToken, Chunk
from semantic_merger import (
    chunk_has_preposition,
    chunk_starts_with_preposition,
    chunk_is_quantity,
    chunk_starts_with_relative,
    chunk_is_speech_verb,
    chunk_is_comma,
    is_temporal_chunk,
    both_have_preposition
)


def create_test_token(id, text, lemma, upos, head=0, deprel='root'):
    """Helper to create test tokens"""
    fields = [str(id), text, lemma, upos, '_', '_', str(head), deprel, '_', '_']
    return UDToken(fields)


def test_chunk_has_preposition():
    """Test preposition detection"""
    # Test with ADP tag
    token1 = create_test_token(1, 'à', 'à', 'ADP')
    token2 = create_test_token(2, 'Paris', 'Paris', 'PROPN')
    chunk = Chunk('SP', [token1, token2])
    
    assert chunk_has_preposition(chunk) == True
    
    # Test without preposition
    token3 = create_test_token(1, 'le', 'le', 'DET')
    token4 = create_test_token(2, 'docteur', 'docteur', 'NOUN')
    chunk2 = Chunk('SN', [token3, token4])
    
    assert chunk_has_preposition(chunk2) == False


def test_chunk_starts_with_preposition():
    """Test if chunk starts with preposition"""
    token1 = create_test_token(1, 'à', 'à', 'ADP')
    token2 = create_test_token(2, 'Paris', 'Paris', 'PROPN')
    chunk = Chunk('SP', [token1, token2])
    
    assert chunk_starts_with_preposition(chunk) == True
    
    # Test chunk not starting with preposition (Paris first)
    token3 = create_test_token(1, 'Paris', 'Paris', 'PROPN')
    token4 = create_test_token(2, 'de', 'de', 'ADP')
    chunk2 = Chunk('SP', [token3, token4])
    assert chunk_starts_with_preposition(chunk2) == False


def test_chunk_is_quantity():
    """Test quantity detection"""
    # Test with number
    token1 = create_test_token(1, '75', '75', 'NUM')
    token2 = create_test_token(2, 'kilos', 'kilo', 'NOUN')
    chunk = Chunk('SN', [token1, token2])
    
    assert chunk_is_quantity(chunk) == True
    
    # Test without quantity
    token3 = create_test_token(1, 'le', 'le', 'DET')
    token4 = create_test_token(2, 'docteur', 'docteur', 'NOUN')
    chunk2 = Chunk('SN', [token3, token4])
    
    assert chunk_is_quantity(chunk2) == False


def test_chunk_starts_with_relative():
    """Test relative pronoun detection"""
    token1 = create_test_token(1, 'qui', 'qui', 'PRON')
    token2 = create_test_token(2, 'est', 'être', 'AUX')
    chunk = Chunk('SV', [token1, token2])
    
    assert chunk_starts_with_relative(chunk) == True
    
    # Test with non-relative
    token3 = create_test_token(1, 'il', 'il', 'PRON')
    chunk2 = Chunk('SujV', [token3])
    
    assert chunk_starts_with_relative(chunk2) == False


def test_chunk_is_speech_verb():
    """Test speech verb detection"""
    token1 = create_test_token(1, 'confie', 'confier', 'VERB')
    chunk = Chunk('SV', [token1])
    
    assert chunk_is_speech_verb(chunk) == True
    
    # Test with non-speech verb
    token2 = create_test_token(1, 'marche', 'marcher', 'VERB')
    chunk2 = Chunk('SV', [token2])
    
    assert chunk_is_speech_verb(chunk2) == False


def test_chunk_is_comma():
    """Test comma detection"""
    token1 = create_test_token(1, ',', ',', 'PUNCT')
    chunk = Chunk('Pct', [token1])
    
    assert chunk_is_comma(chunk) == True
    
    # Test with non-comma
    token2 = create_test_token(1, '.', '.', 'PUNCT')
    chunk2 = Chunk('Pct', [token2])
    
    assert chunk_is_comma(chunk2) == False


def test_is_temporal_chunk():
    """Test temporal chunk detection"""
    # Test temporal
    token1 = create_test_token(1, '18', '18', 'NUM')
    token2 = create_test_token(2, 'h', 'h', 'NOUN')
    token3 = create_test_token(3, '30', '30', 'NUM')
    chunk = Chunk('SN', [token1, token2, token3])
    
    assert is_temporal_chunk(chunk) == True
    
    # Test non-temporal
    token4 = create_test_token(1, 'le', 'le', 'DET')
    token5 = create_test_token(2, 'chat', 'chat', 'NOUN')
    chunk2 = Chunk('SN', [token4, token5])
    
    assert is_temporal_chunk(chunk2) == False


def test_both_have_preposition():
    """Test that all chunks have prepositions"""
    # Create chunks with prepositions
    token1 = create_test_token(1, 'à', 'à', 'ADP')
    token2 = create_test_token(2, 'Paris', 'Paris', 'PROPN')
    chunk1 = Chunk('SP', [token1, token2])
    
    token3 = create_test_token(1, 'de', 'de', 'ADP')
    token4 = create_test_token(2, 'Lyon', 'Lyon', 'PROPN')
    chunk2 = Chunk('SP', [token3, token4])
    
    assert both_have_preposition([chunk1, chunk2]) == True
    
    # Test with one non-preposition chunk
    token5 = create_test_token(1, 'le', 'le', 'DET')
    token6 = create_test_token(2, 'chat', 'chat', 'NOUN')
    chunk3 = Chunk('SN', [token5, token6])
    
    assert both_have_preposition([chunk1, chunk3]) == False


if __name__ == '__main__':
    """Run all tests"""
    print("Running condition checking tests...")
    
    test_chunk_has_preposition()
    print("✓ test_chunk_has_preposition passed")
    
    test_chunk_starts_with_preposition()
    print("✓ test_chunk_starts_with_preposition passed")
    
    test_chunk_is_quantity()
    print("✓ test_chunk_is_quantity passed")
    
    test_chunk_starts_with_relative()
    print("✓ test_chunk_starts_with_relative passed")
    
    test_chunk_is_speech_verb()
    print("✓ test_chunk_is_speech_verb passed")
    
    test_chunk_is_comma()
    print("✓ test_chunk_is_comma passed")
    
    test_is_temporal_chunk()
    print("✓ test_is_temporal_chunk passed")
    
    test_both_have_preposition()
    print("✓ test_both_have_preposition passed")
    
    print("\n✅ All tests passed!")

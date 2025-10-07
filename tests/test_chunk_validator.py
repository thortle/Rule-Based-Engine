#!/usr/bin/env python3
"""
Tests for ChunkValidator - Constituent Validation Tests

This module tests the five linguistic constituency tests:
1. Pronominal substitution
2. Coordination  
3. Dislocation
4. Cleft construction
5. Fragment answer
"""

import sys
import os
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from linguistic_chunker import UDToken, UDSentence, Chunk
from chunk_validator import ChunkValidator, ValidatedChunk, ValidationScore


def create_test_token(id, text, lemma, upos, head=0, deprel='root'):
    """Helper to create test tokens"""
    fields = [str(id), text, lemma, upos, '_', '_', str(head), deprel, '_', '_']
    return UDToken(fields)


def create_test_sentence(tokens):
    """Helper to create test sentence"""
    text = " ".join([t.text for t in tokens])
    return UDSentence('test', text, tokens)


class TestPronominalSubstitution(unittest.TestCase):
    """Test pronominal substitution scoring"""
    
    def setUp(self):
        self.validator = ChunkValidator(lang='fr')
    
    def test_full_noun_phrase(self):
        """Full NP should score high"""
        tokens = [
            create_test_token(1, 'le', 'le', 'DET', 2, 'det'),
            create_test_token(2, 'chat', 'chat', 'NOUN', 0, 'root'),
            create_test_token(3, 'noir', 'noir', 'ADJ', 2, 'amod')
        ]
        chunk = Chunk('SN', tokens)
        sentence = create_test_sentence(tokens)
        
        score = self.validator.test_pronominal_substitution(chunk, sentence)
        self.assertGreater(score, 0.8, "Full NP should score > 0.8")
    
    def test_bare_noun(self):
        """Bare noun should score moderately"""
        tokens = [
            create_test_token(1, 'Paris', 'Paris', 'PROPN', 0, 'root')
        ]
        chunk = Chunk('SN', tokens)
        sentence = create_test_sentence(tokens)
        
        score = self.validator.test_pronominal_substitution(chunk, sentence)
        self.assertGreater(score, 0.7, "Proper noun should score > 0.7")
    
    def test_prepositional_phrase_with_a(self):
        """PP with 'à' should score high (y pronoun)"""
        tokens = [
            create_test_token(1, 'à', 'à', 'ADP', 2, 'case'),
            create_test_token(2, 'Paris', 'Paris', 'PROPN', 0, 'root')
        ]
        chunk = Chunk('SP', tokens)
        sentence = create_test_sentence(tokens)
        
        score = self.validator.test_pronominal_substitution(chunk, sentence)
        self.assertGreater(score, 0.7, "PP with 'à' should score > 0.7 (y)")
    
    def test_subject_pronoun(self):
        """Subject pronoun should score neutral"""
        tokens = [
            create_test_token(1, 'il', 'il', 'PRON', 0, 'root')
        ]
        chunk = Chunk('SujV', tokens)
        sentence = create_test_sentence(tokens)
        
        score = self.validator.test_pronominal_substitution(chunk, sentence)
        self.assertGreater(score, 0.5, "Subject pronoun should be > 0.5")
        self.assertLess(score, 0.9, "Already pronoun, should be < 0.9")
    
    def test_function_words_only(self):
        """Only function words should score low"""
        tokens = [
            create_test_token(1, 'le', 'le', 'DET', 0, 'root')
        ]
        chunk = Chunk('SN', tokens)
        sentence = create_test_sentence(tokens)
        
        score = self.validator.test_pronominal_substitution(chunk, sentence)
        self.assertLess(score, 0.4, "Only determiner should score < 0.4")
    
    def test_punctuation(self):
        """Punctuation should score 0"""
        tokens = [
            create_test_token(1, ',', ',', 'PUNCT', 0, 'punct')
        ]
        chunk = Chunk('Pct', tokens)
        sentence = create_test_sentence(tokens)
        
        score = self.validator.test_pronominal_substitution(chunk, sentence)
        self.assertEqual(score, 0.0, "Punctuation should score 0")


class TestCoordination(unittest.TestCase):
    """Test coordination scoring"""
    
    def setUp(self):
        self.validator = ChunkValidator(lang='fr')
    
    def test_multiple_similar_chunks(self):
        """Multiple SN chunks should score high"""
        tokens1 = [create_test_token(1, 'le', 'le', 'DET'),
                   create_test_token(2, 'chat', 'chat', 'NOUN')]
        tokens2 = [create_test_token(3, 'la', 'la', 'DET'),
                   create_test_token(4, 'souris', 'souris', 'NOUN')]
        tokens3 = [create_test_token(5, 'le', 'le', 'DET'),
                   create_test_token(6, 'chien', 'chien', 'NOUN')]
        
        chunk1 = Chunk('SN', tokens1)
        chunk2 = Chunk('SN', tokens2)
        chunk3 = Chunk('SN', tokens3)
        
        all_chunks = [chunk1, chunk2, chunk3]
        sentence = create_test_sentence(tokens1 + tokens2 + tokens3)
        
        score = self.validator.test_coordination(chunk1, all_chunks)
        self.assertGreater(score, 0.7, "With similar chunks should score > 0.7")
    
    def test_identical_structure(self):
        """Identical POS patterns should score very high"""
        tokens1 = [create_test_token(1, 'le', 'le', 'DET'),
                   create_test_token(2, 'chat', 'chat', 'NOUN')]
        tokens2 = [create_test_token(3, 'la', 'la', 'DET'),
                   create_test_token(4, 'souris', 'souris', 'NOUN')]
        
        chunk1 = Chunk('SN', tokens1)
        chunk2 = Chunk('SN', tokens2)
        all_chunks = [chunk1, chunk2]
        
        score = self.validator.test_coordination(chunk1, all_chunks)
        self.assertGreater(score, 0.8, "Identical structure should score > 0.8")
    
    def test_no_similar_chunks(self):
        """No similar chunks should score neutral"""
        tokens1 = [create_test_token(1, 'le', 'le', 'DET'),
                   create_test_token(2, 'chat', 'chat', 'NOUN')]
        tokens2 = [create_test_token(3, 'dort', 'dormir', 'VERB')]
        
        chunk1 = Chunk('SN', tokens1)
        chunk2 = Chunk('SV', tokens2)
        all_chunks = [chunk1, chunk2]
        
        score = self.validator.test_coordination(chunk1, all_chunks)
        self.assertEqual(score, 0.5, "No similar chunks should score 0.5")
    
    def test_punctuation_cannot_coordinate(self):
        """Punctuation should score 0"""
        tokens = [create_test_token(1, ',', ',', 'PUNCT')]
        chunk = Chunk('Pct', tokens)
        all_chunks = [chunk]
        
        score = self.validator.test_coordination(chunk, all_chunks)
        self.assertEqual(score, 0.0, "Punctuation should score 0")


class TestDislocation(unittest.TestCase):
    """Test dislocation scoring"""
    
    def setUp(self):
        self.validator = ChunkValidator(lang='fr')
    
    def test_noun_phrase_object(self):
        """NP object should score high"""
        tokens = [
            create_test_token(1, 'le', 'le', 'DET', 2, 'det'),
            create_test_token(2, 'chat', 'chat', 'NOUN', 0, 'obj')
        ]
        chunk = Chunk('SN', tokens)
        sentence = create_test_sentence(tokens)
        
        score = self.validator.test_dislocation(chunk, sentence)
        self.assertGreater(score, 0.8, "NP object should score > 0.8")
    
    def test_locative_pp(self):
        """PP with locative preposition should score high"""
        tokens = [
            create_test_token(1, 'à', 'à', 'ADP', 2, 'case'),
            create_test_token(2, 'Paris', 'Paris', 'PROPN', 0, 'obl')
        ]
        chunk = Chunk('SP', tokens)
        sentence = create_test_sentence(tokens)
        
        score = self.validator.test_dislocation(chunk, sentence)
        self.assertGreater(score, 0.7, "Locative PP should score > 0.7 (y)")
    
    def test_partitive_pp(self):
        """PP with 'de' should score high"""
        tokens = [
            create_test_token(1, 'de', 'de', 'ADP', 3, 'case'),
            create_test_token(2, 'ce', 'ce', 'DET', 3, 'det'),
            create_test_token(3, 'livre', 'livre', 'NOUN', 0, 'obl')
        ]
        chunk = Chunk('SP', tokens)
        sentence = create_test_sentence(tokens)
        
        score = self.validator.test_dislocation(chunk, sentence)
        self.assertGreater(score, 0.7, "Partitive PP should score > 0.7 (en)")
    
    def test_verb_phrase(self):
        """Verb phrase (predicate) should score low"""
        tokens = [
            create_test_token(1, 'mange', 'manger', 'VERB', 0, 'root')
        ]
        chunk = Chunk('SV', tokens)
        sentence = create_test_sentence(tokens)
        
        score = self.validator.test_dislocation(chunk, sentence)
        self.assertLess(score, 0.3, "Verb (predicate) should score < 0.3")


class TestCleft(unittest.TestCase):
    """Test cleft construction scoring"""
    
    def setUp(self):
        self.validator = ChunkValidator(lang='fr')
    
    def test_full_noun_phrase(self):
        """Full NP should score very high in cleft"""
        tokens = [
            create_test_token(1, 'le', 'le', 'DET', 2, 'det'),
            create_test_token(2, 'chat', 'chat', 'NOUN', 0, 'root'),
            create_test_token(3, 'noir', 'noir', 'ADJ', 2, 'amod')
        ]
        chunk = Chunk('SN', tokens)
        sentence = create_test_sentence(tokens)
        
        score = self.validator.test_cleft(chunk, sentence)
        self.assertGreater(score, 0.9, "Full NP should score > 0.9 in cleft")
    
    def test_prepositional_phrase(self):
        """PP should score moderately in cleft"""
        tokens = [
            create_test_token(1, 'à', 'à', 'ADP', 2, 'case'),
            create_test_token(2, 'Paris', 'Paris', 'PROPN', 0, 'obl')
        ]
        chunk = Chunk('SP', tokens)
        sentence = create_test_sentence(tokens)
        
        score = self.validator.test_cleft(chunk, sentence)
        self.assertGreater(score, 0.6, "PP should score > 0.6 in cleft")
    
    def test_verb_phrase(self):
        """Verb phrase should score low (predicates don't cleft)"""
        tokens = [
            create_test_token(1, 'mange', 'manger', 'VERB', 0, 'root')
        ]
        chunk = Chunk('SV', tokens)
        sentence = create_test_sentence(tokens)
        
        score = self.validator.test_cleft(chunk, sentence)
        self.assertLess(score, 0.2, "Verb should score < 0.2 in cleft")


class TestFragmentAnswer(unittest.TestCase):
    """Test fragment answer scoring"""
    
    def setUp(self):
        self.validator = ChunkValidator(lang='fr')
    
    def test_full_noun_phrase(self):
        """Full NP should be good fragment answer"""
        tokens = [
            create_test_token(1, 'le', 'le', 'DET', 2, 'det'),
            create_test_token(2, 'chat', 'chat', 'NOUN', 0, 'root'),
            create_test_token(3, 'noir', 'noir', 'ADJ', 2, 'amod')
        ]
        chunk = Chunk('SN', tokens)
        sentence = create_test_sentence(tokens)
        
        score = self.validator.test_fragment_answer(chunk, sentence)
        self.assertGreater(score, 0.9, "Full NP should score > 0.9 as fragment")
    
    def test_prepositional_phrase(self):
        """PP should be good fragment answer"""
        tokens = [
            create_test_token(1, 'à', 'à', 'ADP', 2, 'case'),
            create_test_token(2, 'Paris', 'Paris', 'PROPN', 0, 'obl')
        ]
        chunk = Chunk('SP', tokens)
        sentence = create_test_sentence(tokens)
        
        score = self.validator.test_fragment_answer(chunk, sentence)
        self.assertGreater(score, 0.8, "PP should score > 0.8 as fragment")
    
    def test_adverb(self):
        """Adverb should be good fragment answer"""
        tokens = [
            create_test_token(1, 'hier', 'hier', 'ADV', 0, 'advmod')
        ]
        chunk = Chunk('SAdv', tokens)
        sentence = create_test_sentence(tokens)
        
        score = self.validator.test_fragment_answer(chunk, sentence)
        self.assertGreater(score, 0.7, "Adverb should score > 0.7 as fragment")
    
    def test_function_word_only(self):
        """Only function words should score low"""
        tokens = [
            create_test_token(1, 'le', 'le', 'DET', 0, 'det')
        ]
        chunk = Chunk('SN', tokens)
        sentence = create_test_sentence(tokens)
        
        score = self.validator.test_fragment_answer(chunk, sentence)
        self.assertLess(score, 0.2, "Only determiner should score < 0.2")
    
    def test_punctuation(self):
        """Punctuation should score 0"""
        tokens = [
            create_test_token(1, ',', ',', 'PUNCT', 0, 'punct')
        ]
        chunk = Chunk('Pct', tokens)
        sentence = create_test_sentence(tokens)
        
        score = self.validator.test_fragment_answer(chunk, sentence)
        self.assertLessEqual(score, 0.1, "Punctuation should score <= 0.1")


class TestValidationIntegration(unittest.TestCase):
    """Test full validation workflow"""
    
    def setUp(self):
        self.validator = ChunkValidator(lang='fr')
    
    def test_validate_chunk(self):
        """Test validating a single chunk"""
        tokens = [
            create_test_token(1, 'le', 'le', 'DET', 2, 'det'),
            create_test_token(2, 'chat', 'chat', 'NOUN', 0, 'root')
        ]
        chunk = Chunk('SN', tokens)
        sentence = create_test_sentence(tokens)
        
        validated = self.validator.validate_chunk(chunk, sentence, [chunk])
        
        self.assertIsInstance(validated, ValidatedChunk)
        self.assertIsInstance(validated.score, ValidationScore)
        self.assertGreater(validated.score.aggregate, 0.5)
        self.assertTrue(validated.passed)
    
    def test_validate_all(self):
        """Test validating multiple chunks"""
        tokens1 = [create_test_token(1, 'le', 'le', 'DET'),
                   create_test_token(2, 'chat', 'chat', 'NOUN')]
        tokens2 = [create_test_token(3, 'dort', 'dormir', 'VERB')]
        
        chunk1 = Chunk('SN', tokens1)
        chunk2 = Chunk('SV', tokens2)
        chunks = [chunk1, chunk2]
        
        sentence = create_test_sentence(tokens1 + tokens2)
        validated_chunks = self.validator.validate_all(chunks, sentence)
        
        self.assertEqual(len(validated_chunks), 2)
        self.assertTrue(all(isinstance(vc, ValidatedChunk) for vc in validated_chunks))
    
    def test_get_statistics(self):
        """Test statistics calculation"""
        tokens = [create_test_token(1, 'le', 'le', 'DET'),
                  create_test_token(2, 'chat', 'chat', 'NOUN')]
        chunk = Chunk('SN', tokens)
        sentence = create_test_sentence(tokens)
        
        validated = self.validator.validate_chunk(chunk, sentence, [chunk])
        stats = self.validator.get_statistics([validated])
        
        self.assertIn('total_chunks', stats)
        self.assertIn('passed_chunks', stats)
        self.assertIn('avg_aggregate', stats)
        self.assertEqual(stats['total_chunks'], 1)
    
    def test_filter_by_score(self):
        """Test filtering by minimum score"""
        tokens1 = [create_test_token(1, 'le', 'le', 'DET'),
                   create_test_token(2, 'chat', 'chat', 'NOUN')]
        tokens2 = [create_test_token(3, ',', ',', 'PUNCT')]
        
        chunk1 = Chunk('SN', tokens1)
        chunk2 = Chunk('Pct', tokens2)
        sentence = create_test_sentence(tokens1 + tokens2)
        
        validated = self.validator.validate_all([chunk1, chunk2], sentence)
        filtered = self.validator.filter_by_score(validated, min_score=0.4)
        
        # Punctuation should be filtered out
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].category, 'SN')


if __name__ == '__main__':
    print("=" * 70)
    print("CHUNK VALIDATOR TEST SUITE")
    print("=" * 70)
    print("\nTesting five linguistic constituency tests:")
    print("  1. Pronominal substitution")
    print("  2. Coordination")
    print("  3. Dislocation")
    print("  4. Cleft construction")
    print("  5. Fragment answer")
    print("\n" + "=" * 70 + "\n")
    
    unittest.main(verbosity=2)

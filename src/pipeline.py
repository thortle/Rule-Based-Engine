#!/usr/bin/env python3
"""
Pipeline Orchestration for UD-Based French Text Chunker

Facade pattern for coordinating the two-level chunking pipeline:
- Level 1: UD-based syntactic chunking
- Level 2: Semantic rule-based merging
"""

import os
import json
import stanza
from pathlib import Path
from typing import List, Tuple, Dict, Any

from .models import Token, Sentence, Chunk
from .chunkers import UDChunker
from .rules import SemanticMerger, create_rules_from_json


class ChunkerPipeline:
    """
    Facade orchestrating the two-level French text chunking pipeline.
    
    Responsibilities:
    - Parse raw text to CoNLL-U format using Stanza
    - Convert CoNLL-U to structured sentence objects
    - Apply Level 1 UD-based chunking
    - Apply Level 2 semantic merging
    - Save formatted output
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize pipeline with configuration.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.chunker = UDChunker()
        self.stanza_pipeline = None  # Lazy-loaded
        self.semantic_merger = None  # Lazy-loaded
    
    def run(self, text_file: str, output_dir: str) -> Tuple[List[Tuple], List[Tuple]]:
        """
        Run complete two-level chunking pipeline.
        
        Args:
            text_file: Path to input text file
            output_dir: Directory for output files
            
        Returns:
            Tuple of (level1_results, level2_results)
            Each result is list of (sentence/text, chunks) tuples
        """
        # Read input text
        with open(text_file, 'r', encoding='utf-8') as f:
            text = f.read().strip()
        
        # Parse to structured sentences
        sentences = self._parse_to_sentences(text, output_dir)
        
        # Level 1: UD-based chunking
        level1_results = self._apply_level1(sentences)
        
        # Level 2: Semantic merging (if enabled)
        if self.config['pipeline']['enable_level2']:
            level2_results = self._apply_level2(level1_results)
        else:
            level2_results = [(sent.text, chunks) for sent, chunks in level1_results]
        
        # Save outputs
        if self.config['output']['save_level1']:
            self._save_output(
                os.path.join(output_dir, 'gorafi_medical_level1.txt'),
                sentences
            )
        
        if self.config['output']['save_level2']:
            self._save_level2_output(
                os.path.join(output_dir, 'gorafi_medical_level2.txt'),
                level2_results
            )
        
        return level1_results, level2_results
    
    def _parse_to_sentences(self, text: str, output_dir: str) -> List[Sentence]:
        """
        Parse raw text to Sentence objects via CoNLL-U.
        
        Args:
            text: Raw input text
            output_dir: Directory for intermediate files
            
        Returns:
            List of Sentence objects
        """
        # Initialize Stanza pipeline (lazy)
        if self.stanza_pipeline is None:
            self.stanza_pipeline = stanza.Pipeline(
                'fr',
                processors='tokenize,mwt,pos,lemma,depparse',
                logging_level='ERROR'
            )
        
        # Parse text
        doc = self.stanza_pipeline(text)
        
        # Save CoNLL-U
        conllu_file = os.path.join(output_dir, '../gorafi_medical.conllu')
        self._write_conllu(doc, conllu_file)
        
        # Convert to Sentence objects
        sentences = []
        for sent_idx, sent in enumerate(doc.sentences, 1):
            tokens = []
            for word in sent.words:
                token = Token.from_fields([
                    str(word.id),
                    word.text,
                    word.lemma or '_',
                    word.upos or '_',
                    word.xpos or '_',
                    word.feats or '_',
                    str(word.head),
                    word.deprel or '_',
                    '_',  # deps
                    '_'   # misc
                ])
                tokens.append(token)
            
            sent_text = " ".join([w.text for w in sent.words])
            sentences.append(Sentence(str(sent_idx), sent_text, tokens))
        
        # Save JSON representation
        json_file = os.path.join(output_dir, '../gorafi_medical.json')
        self._write_json(sentences, json_file)
        
        return sentences
    
    def _write_conllu(self, doc, output_file: str):
        """Write Stanza document to CoNLL-U format."""
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            for sent in doc.sentences:
                for word in sent.words:
                    line = f"{word.id}\t{word.text}\t{word.lemma or '_'}\t" \
                           f"{word.upos or '_'}\t{word.xpos or '_'}\t" \
                           f"{word.feats or '_'}\t{word.head}\t" \
                           f"{word.deprel or '_'}\t_\t_\n"
                    f.write(line)
                f.write("\n")
    
    def _write_json(self, sentences: List[Sentence], output_file: str):
        """Write sentences to JSON format."""
        sentences_json = []
        for sentence in sentences:
            tokens_json = [
                {
                    "id": token.id,
                    "form": token.text,
                    "lemma": token.lemma,
                    "upos": token.upos,
                    "head": token.head,
                    "deprel": token.deprel
                }
                for token in sentence.tokens
            ]
            sentences_json.append(tokens_json)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(sentences_json, f, ensure_ascii=False, indent=2)
    
    def _apply_level1(self, sentences: List[Sentence]) -> List[Tuple[Sentence, List[Chunk]]]:
        """
        Apply Level 1 UD-based chunking.
        
        Args:
            sentences: List of Sentence objects
            
        Returns:
            List of (sentence, chunks) tuples
        """
        results = []
        for sentence in sentences:
            chunks = self.chunker.chunk_sentence(sentence)
            results.append((sentence, chunks))
        return results
    
    def _apply_level2(self, level1_results: List[Tuple[Sentence, List[Chunk]]]) -> List[Tuple[str, List[Chunk]]]:
        """
        Apply Level 2 semantic merging.
        
        Args:
            level1_results: Results from Level 1 chunking
            
        Returns:
            List of (sentence_text, chunks) tuples
        """
        # Initialize semantic merger (lazy)
        if self.semantic_merger is None:
            rules_file = self.config['level2_semantic_merger']['rules_file']
            with open(rules_file, 'r', encoding='utf-8') as f:
                rules_data = json.load(f)
            rules = create_rules_from_json(rules_data)
            self.semantic_merger = SemanticMerger(rules)
        
        # Apply merging to each sentence
        results = []
        merger_config = self.config['level2_semantic_merger']
        for sentence, level1_chunks in level1_results:
            level2_chunks = self.semantic_merger.merge(
                level1_chunks,
                multi_pass=merger_config.get('multi_pass', False),
                max_passes=merger_config.get('max_passes', 10),
                debug=merger_config.get('debug', False)
            )
            results.append((sentence.text, level2_chunks))
        
        return results
    
    def _save_output(self, output_file: str, sentences: List[Sentence]):
        """
        Save Level 1 chunked output.
        
        Args:
            output_file: Path to output file
            sentences: List of Sentence objects
        """
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            for sentence in sentences:
                chunks = self.chunker.chunk_sentence(sentence)
                formatted = self._format_chunks(chunks)
                f.write(formatted + "\n\n")
    
    def _save_level2_output(self, output_file: str, results: List[Tuple[str, List[Chunk]]]):
        """
        Save Level 2 chunked output.
        
        Args:
            output_file: Path to output file
            results: List of (sentence_text, chunks) tuples
        """
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            for _, chunks in results:
                formatted = self._format_chunks(chunks)
                f.write(formatted + "\n\n")
    
    def _format_chunks(self, chunks: List[Chunk]) -> str:
        """
        Format chunks as text with category labels.
        
        Args:
            chunks: List of Chunk objects
            
        Returns:
            Formatted string: "[SN] Jean-Noël C. [SV] est admis ..."
        """
        parts = []
        for chunk in chunks:
            text = " ".join([token.text for token in chunk.tokens])
            parts.append(f"[{chunk.category}] {text}")
        return " ".join(parts)
    
    @staticmethod
    def compute_statistics(results: List[Tuple]) -> Dict[str, Any]:
        """
        Compute statistics for chunking results.
        
        Args:
            results: List of (sentence/text, chunks) tuples
            
        Returns:
            Dictionary with statistics
        """
        chunks_list = [chunks for _, chunks in results]
        total_chunks = sum(len(chunks) for chunks in chunks_list)
        total_tokens = sum(sum(len(c.tokens) for c in chunks) for chunks in chunks_list)
        sv_count = sum(1 for chunks in chunks_list for c in chunks if c.category == 'SV')
        sn_count = sum(1 for chunks in chunks_list for c in chunks if c.category == 'SN')
        
        return {
            'total_chunks': total_chunks,
            'total_tokens': total_tokens,
            'tokens_per_chunk': total_tokens / total_chunks if total_chunks > 0 else 0,
            'sv_count': sv_count,
            'sn_count': sn_count
        }

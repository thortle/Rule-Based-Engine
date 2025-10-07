#!/usr/bin/env python3
"""
UD-Based French Text Chunker

Main script demonstrating Universal Dependencies-based chunking
vs. rule-based chunking on French text.

Workflow:
1. Parse text with Stanza/UDPipe → CoNLL-U format
2. Save CoNLL-U file
3. Use CONLLU-to-JSON project to parse CoNLL-U → JSON
4. Extract chunks from JSON format
5. Output chunked text

Usage:
    python main.py [--config config.json] [--debug] [--multi-pass]
"""

import sys
import os
import json
import stanza
import argparse
from pathlib import Path
import importlib.util

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from linguistic_chunker import (
    UDSentence, 
    UDToken, 
    extract_linguistic_chunks_v2,
    map_ud_to_chunk_category
)
from semantic_merger import merge_level1_to_level2
from chunk_validator import ChunkValidator, ValidatedChunk


# ============================================================================
# CONFIGURATION
# ============================================================================

def load_config(config_file: str = "config.json") -> dict:
    """
    Load configuration from JSON file.
    
    Args:
        config_file: Path to configuration file
    
    Returns:
        Configuration dictionary
    """
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print(f"✓ Loaded configuration from {config_file}")
        return config
    except FileNotFoundError:
        print(f"⚠️  Configuration file not found: {config_file}")
        print("Using default configuration")
        return get_default_config()
    except json.JSONDecodeError as e:
        print(f"⚠️  Error parsing configuration file: {e}")
        print("Using default configuration")
        return get_default_config()


def get_default_config() -> dict:
    """Return default configuration"""
    return {
        "pipeline": {
            "enable_level1": True,
            "enable_validation": False,
            "enable_level2": True
        },
        "validation": {
            "min_score": 0.4,
            "filter_low_scores": False,
            "show_scores": True,
            "show_statistics": True
        },
        "level2_semantic_merger": {
            "rules_file": "lang_fr/semantic_rules.json",
            "multi_pass": False,
            "max_passes": 10,
            "debug": False
        },
        "output": {
            "format": "text",
            "save_level1": True,
            "save_validation": False,
            "save_level2": True,
            "output_dir": "data/output"
        },
        "performance": {
            "show_statistics": True,
            "show_timing": False,
            "verbose": False
        }
    }


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def print_header(text, char="="):
    """Print formatted header"""
    print("\n" + char * 80)
    print(text)
    print(char * 80)


def print_section(text):
    """Print section divider"""
    print("\n" + "-" * 80)
    print(text)
    print("-" * 80)


def parse_text_to_conllu(text, output_file):
    """
    Step 1: Parse French text with Stanza and save as CoNLL-U file.
    
    Args:
        text: Raw French text
        output_file: Path to save CoNLL-U output
        
    Returns:
        Path to generated CoNLL-U file
    """
    print("🔄 Step 1: Parsing text with Stanza (UDPipe) → CoNLL-U format...")
    nlp = stanza.Pipeline('fr', processors='tokenize,mwt,pos,lemma,depparse',
                         logging_level='ERROR')
    doc = nlp(text)
    
    # Write CoNLL-U format
    with open(output_file, 'w', encoding='utf-8') as f:
        for sent in doc.sentences:
            for word in sent.words:
                # CoNLL-U format: ID FORM LEMMA UPOS XPOS FEATS HEAD DEPREL DEPS MISC
                line = f"{word.id}\t{word.text}\t{word.lemma or '_'}\t{word.upos or '_'}\t{word.xpos or '_'}\t{word.feats or '_'}\t{word.head}\t{word.deprel or '_'}\t_\t_\n"
                f.write(line)
            f.write("\n")  # Blank line between sentences
    
    print(f"✓ CoNLL-U file saved: {output_file}")
    return output_file


def conllu_to_json(conllu_file, json_output_file):
    """
    Step 2-3: Parse CoNLL-U file directly and save to JSON format (with HEAD field).
    
    Note: We parse CoNLL-U directly instead of using CONLLU-to-JSON because we need
    the HEAD field for dependency tree traversal.
    
    Args:
        conllu_file: Path to CoNLL-U file
        json_output_file: Path to save JSON output
        
    Returns:
        List of UDSentence objects
    """
    print("🔄 Step 2: Parsing CoNLL-U file and extracting dependency structure...")
    
    # Parse CoNLL-U file directly to extract all fields including HEAD
    sentences_json = []
    current_sentence = []
    
    with open(conllu_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # Skip comments
            if line.startswith('#'):
                continue
            
            # Empty line = sentence boundary
            if not line:
                if current_sentence:
                    sentences_json.append(current_sentence)
                    current_sentence = []
                continue
            
            # Parse token line
            parts = line.split('\t')
            if len(parts) >= 8:
                # Skip multi-word tokens (e.g., "1-2")
                if '-' in parts[0] or '.' in parts[0]:
                    continue
                
                try:
                    # Extract all relevant fields including HEAD
                    current_sentence.append({
                        "id": parts[0],
                        "form": parts[1],
                        "lemma": parts[2],
                        "upos": parts[3],
                        "head": int(parts[6]),  # THIS IS CRITICAL for dependency tree!
                        "deprel": parts[7]
                    })
                except (ValueError, IndexError):
                    continue
    
    # Don't forget last sentence
    if current_sentence:
        sentences_json.append(current_sentence)
    
    print(f"✓ Parsed {len(sentences_json)} sentences with dependency structure")
    
    # Save JSON file
    with open(json_output_file, 'w', encoding='utf-8') as f:
        json.dump(sentences_json, f, ensure_ascii=False, indent=2)
    print(f"✓ JSON file saved with HEAD field: {json_output_file}")
    
    # Convert JSON format to UDSentence objects for chunking
    print("🔄 Step 3: Converting JSON to UDSentence format...")
    sentences = []
    for sent_idx, sent_json in enumerate(sentences_json, 1):
        tokens = []
        sent_text = " ".join([token["form"] for token in sent_json])
        
        for token_json in sent_json:
            # Create UDToken from JSON fields (now includes HEAD!)
            token = UDToken([
                str(token_json["id"]),
                token_json["form"],
                token_json["lemma"],
                token_json["upos"],
                "_",  # xpos
                "_",  # feats
                str(token_json["head"]),  # Now properly extracted from CoNLL-U
                token_json["deprel"],
                "_",  # deps
                "_"   # misc
            ])
            tokens.append(token)
        
        sentences.append(UDSentence(str(sent_idx), sent_text, tokens))
    
    print(f"✓ Converted to UDSentence format")
    return sentences


def format_chunks_to_text(sentence, chunks):
    """
    Step 4: Convert chunks to formatted text with square brackets.
    
    Args:
        sentence: UDSentence object
        chunks: List of Chunk objects from extract_chunks()
    
    Returns:
        Formatted string: "[SN] Jean-Noël C. [SV] est admis ..."
    """
    output_parts = []
    for chunk in chunks:
        category = chunk.category
        text = " ".join([token.text for token in chunk.tokens])
        output_parts.append(f"[{category}] {text}")
    
    return " ".join(output_parts)


def save_chunked_output(output_file, ud_sentences):
    """
    Step 5: Save chunked text to output file.
    
    Args:
        output_file: Output file path for chunked text
        ud_sentences: List of UDSentence objects
    
    Returns:
        Number of sentences written
    """
    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"✓ Created output directory: {output_dir}")
    
    sentence_count = 0
    with open(output_file, 'w', encoding='utf-8') as f:
        for sentence in ud_sentences:
            chunks = extract_linguistic_chunks_v2(sentence)
            formatted = format_chunks_to_text(sentence, chunks)
            f.write(formatted + "\n\n")
            sentence_count += 1
    
    return sentence_count


def main():
    """Main demonstration"""
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='UD-Based French Text Chunker')
    parser.add_argument('--config', default='config.json', help='Path to configuration file')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--multi-pass', action='store_true', help='Enable multi-pass merging')
    parser.add_argument('--max-passes', type=int, help='Maximum number of passes (default from config)')
    parser.add_argument('--validate', action='store_true', help='Enable Level 1.5 constituent validation')
    parser.add_argument('--min-score', type=float, help='Minimum validation score (default 0.4)')
    parser.add_argument('--filter-low-scores', action='store_true', help='Filter out low-scoring chunks')
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Override config with command-line arguments
    if args.debug:
        config['level2_semantic_merger']['debug'] = True
    if args.multi_pass:
        config['level2_semantic_merger']['multi_pass'] = True
    if args.max_passes:
        config['level2_semantic_merger']['max_passes'] = args.max_passes
    if args.validate:
        config['pipeline']['enable_validation'] = True
    if args.min_score:
        config['validation']['min_score'] = args.min_score
    if args.filter_low_scores:
        config['validation']['filter_low_scores'] = True
    
    print_header("UD-BASED FRENCH TEXT CHUNKER", "=")
    print("\nDemonstrating Universal Dependencies-based chunking")
    print("Test: French satirical news article (479 tokens)")
    print("\nConfiguration:")
    print(f"  • Level 1 (UD): {'Enabled' if config['pipeline']['enable_level1'] else 'Disabled'}")
    print(f"  • Level 1.5 (Validation): {'Enabled' if config['pipeline']['enable_validation'] else 'Disabled'}")
    if config['pipeline']['enable_validation']:
        print(f"    - Min score: {config['validation']['min_score']}")
        print(f"    - Filter low scores: {'Yes' if config['validation']['filter_low_scores'] else 'No'}")
    print(f"  • Level 2 (Semantic): {'Enabled' if config['pipeline']['enable_level2'] else 'Disabled'}")
    print(f"  • Multi-pass: {'Yes' if config['level2_semantic_merger']['multi_pass'] else 'No'}")
    print(f"  • Debug mode: {'Yes' if config['level2_semantic_merger']['debug'] else 'No'}")
    print("\nWorkflow:")
    print("  1. Text → Stanza/UDPipe → CoNLL-U file")
    print("  2. CoNLL-U → CONLLU-to-JSON → JSON format")
    print("  3. JSON → Extract Level 1 UD-based chunks")
    if config['pipeline']['enable_validation']:
        print("  4. Level 1 → Apply Level 1.5 constituent validation")
        print("  5. Validated chunks → Apply Level 2 semantic merging")
        print("  6. Format and save Level 1, validation, and Level 2 outputs")
    else:
        print("  4. Level 1 → Apply Level 2 semantic merging")
        print("  5. Format and save both Level 1 and Level 2 outputs")
    
    # Get file paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    text_file = os.path.join(script_dir, 'data', 'gorafi_medical.txt')
    conllu_file = os.path.join(script_dir, 'data', 'gorafi_medical.conllu')
    json_file = os.path.join(script_dir, 'data', 'gorafi_medical.json')
    
    output_dir = os.path.join(script_dir, config['output']['output_dir'])
    os.makedirs(output_dir, exist_ok=True)
    
    output_file_level1 = os.path.join(output_dir, 'gorafi_medical_level1.txt')
    output_file_validation = os.path.join(output_dir, 'gorafi_medical_validation.txt')
    output_file_level2 = os.path.join(output_dir, 'gorafi_medical_level2.txt')
    semantic_rules_file = os.path.join(script_dir, config['level2_semantic_merger']['rules_file'])
    
    # Load test text
    print("\n📂 Loading test text...")
    with open(text_file, 'r', encoding='utf-8') as f:
        text = f.read().strip()
    
    # Parse text → CoNLL-U
    print("\n🔄 Step 1: Parsing text to CoNLL-U format...")
    parse_text_to_conllu(text, conllu_file)
    print(f"✓ Generated CoNLL-U file: {conllu_file}")
    
    # CoNLL-U → JSON → UDSentence format
    print("\n🔄 Step 2: Converting CoNLL-U to JSON and UDSentence objects...")
    ud_sentences = conllu_to_json(conllu_file, json_file)
    print(f"✓ Generated JSON file: {json_file}")
    print(f"✓ Loaded {len(ud_sentences)} sentences")
    
    # Run Level 1: UD-based linguistic chunker
    if not config['pipeline']['enable_level1']:
        print("\n⚠️  Level 1 disabled in configuration, skipping...")
        return
    
    print("\n🔄 Step 3: Running Level 1 (UD-based) linguistic chunker...")
    level1_results = []
    for sentence in ud_sentences:
        chunks = extract_linguistic_chunks_v2(sentence)
        level1_results.append((sentence, chunks))
    print("✓ Level 1 linguistic chunking complete")
    
    # Run Level 1.5: Constituent Validation (optional)
    validation_results = []
    if config['pipeline']['enable_validation']:
        print("\n🔄 Step 3.5: Running Level 1.5 (constituent validation)...")
        validator = ChunkValidator(lang='fr')
        
        for sentence, chunks in level1_results:
            validated_chunks = validator.validate_all(chunks, sentence)
            validation_results.append((sentence, validated_chunks))
        
        print("✓ Level 1.5 constituent validation complete")
        
        # Show validation statistics
        if config['validation']['show_statistics']:
            all_validated = [vc for _, vcs in validation_results for vc in vcs]
            stats = validator.get_statistics(all_validated)
            
            print("\n📊 Validation Statistics:")
            print(f"   Total chunks: {stats['total_chunks']}")
            print(f"   Passed chunks: {stats['passed_chunks']} ({stats['pass_rate']*100:.1f}%)")
            print(f"   Avg aggregate score: {stats['avg_aggregate']:.3f}")
            print(f"   Score range: {stats['min_aggregate']:.3f} - {stats['max_aggregate']:.3f}")
            print(f"   Avg substitution: {stats['avg_substitution']:.3f}")
            print(f"   Avg coordination: {stats['avg_coordination']:.3f}")
            print(f"   Avg dislocation: {stats['avg_dislocation']:.3f}")
            print(f"   Avg cleft: {stats['avg_cleft']:.3f}")
            print(f"   Avg fragment: {stats['avg_fragment']:.3f}")
            
            # Show low-confidence chunks
            low_conf = validator.get_low_confidence_chunks(
                all_validated, 
                threshold=config['validation']['min_score']
            )
            if low_conf:
                print(f"\n⚠️  Low-confidence chunks ({len(low_conf)}):")
                for vc in low_conf[:5]:  # Show first 5
                    print(f"      {vc}")
                if len(low_conf) > 5:
                    print(f"      ... and {len(low_conf) - 5} more")
        
        # Filter low-scoring chunks if requested
        if config['validation']['filter_low_scores']:
            print(f"\n🔍 Filtering chunks with score < {config['validation']['min_score']}...")
            filtered_results = []
            for sentence, validated_chunks in validation_results:
                filtered = validator.filter_by_score(
                    validated_chunks, 
                    min_score=config['validation']['min_score']
                )
                # Extract original chunks from validated chunks
                chunks = [vc.chunk for vc in filtered]
                filtered_results.append((sentence, chunks))
            
            # Update level1_results for Level 2
            level1_results = filtered_results
            total_before = sum(len(vcs) for _, vcs in validation_results)
            total_after = sum(len(cs) for _, cs in filtered_results)
            print(f"✓ Filtered {total_before - total_after} low-scoring chunks")
    
    # Run Level 2: Semantic merger
    if not config['pipeline']['enable_level2']:
        print("\n⚠️  Level 2 disabled in configuration, skipping semantic merging...")
        level2_results = [(sent.text, chunks) for sent, chunks in level1_results]
    else:
        print("\n🔄 Step 4: Running Level 2 (semantic merger)...")
        level2_results = []
        for sentence, level1_chunks in level1_results:
            level2_chunks = merge_level1_to_level2(
                level1_chunks, 
                semantic_rules_file,
                multi_pass=config['level2_semantic_merger']['multi_pass'],
                max_passes=config['level2_semantic_merger']['max_passes'],
                debug=config['level2_semantic_merger']['debug']
            )
            level2_results.append((sentence.text, level2_chunks))
        print("✓ Level 2 semantic merging complete")
    
    # Save Level 1 output
    if config['output']['save_level1']:
        print("\n🔄 Step 5: Saving Level 1 output to file...")
        sentence_count = save_chunked_output(output_file_level1, ud_sentences)
        print(f"✓ Saved {sentence_count} Level 1 sentences to: {output_file_level1}")
    
    # Save validation output
    if config['pipeline']['enable_validation'] and config['output'].get('save_validation', False):
        print("\n🔄 Step 5.5: Saving validation output to file...")
        with open(output_file_validation, 'w', encoding='utf-8') as f:
            for sentence, validated_chunks in validation_results:
                f.write(f"=== {sentence.text} ===\n\n")
                for vc in validated_chunks:
                    f.write(f"{vc}\n")
                f.write("\n")
        print(f"✓ Saved validation results to: {output_file_validation}")
    
    # Save Level 2 output
    if config['output']['save_level2']:
        print("\n🔄 Step 6: Saving Level 2 output to file...")
        output_dir = os.path.dirname(output_file_level2)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
    with open(output_file_level2, 'w', encoding='utf-8') as f:
        for sent_text, chunks in level2_results:
            formatted = format_chunks_to_text(None, chunks)
            f.write(formatted + "\n\n")
    print(f"✓ Saved {len(level2_results)} Level 2 sentences to: {output_file_level2}")
    
    # ========================================================================
    # DISPLAY RESULTS
    # ========================================================================
    
    print_header("TWO-LEVEL CHUNKING RESULTS", "=")
    
    # Level 1 Statistics
    print("\n📊 LEVEL 1 (UD-Based) Statistics:")
    # Extract chunks from level1_results (which now contains (sentence, chunks))
    level1_chunks_list = [chunks for _, chunks in level1_results]
    level1_total = sum(len(chunks) for chunks in level1_chunks_list)
    level1_tokens = sum(sum(len(c.tokens) for c in chunks) for chunks in level1_chunks_list)
    level1_sv = sum(1 for chunks in level1_chunks_list for c in chunks if c.category == 'SV')
    level1_sn = sum(1 for chunks in level1_chunks_list for c in chunks if c.category == 'SN')
    
    print(f"   Total chunks: {level1_total}")
    print(f"   Total tokens: {level1_tokens}")
    print(f"   Tokens/chunk: {level1_tokens/level1_total:.2f}")
    print(f"   [SV] verb chunks: {level1_sv}")
    print(f"   [SN] noun chunks: {level1_sn}")
    
    # Level 2 Statistics
    print("\n📊 LEVEL 2 (Semantic Merger) Statistics:")
    level2_total = sum(len(chunks) for _, chunks in level2_results)
    level2_tokens = sum(sum(len(c.tokens) for c in chunks) for _, chunks in level2_results)
    level2_sv = sum(1 for _, chunks in level2_results for c in chunks if c.category == 'SV')
    level2_sn = sum(1 for _, chunks in level2_results for c in chunks if c.category == 'SN')
    
    print(f"   Total chunks: {level2_total}")
    print(f"   Total tokens: {level2_tokens}")
    print(f"   Tokens/chunk: {level2_tokens/level2_total:.2f}")
    print(f"   [SV] verb chunks: {level2_sv}")
    print(f"   [SN] noun chunks: {level2_sn}")
    
    # Improvement metrics
    reduction = level1_total - level2_total
    reduction_pct = (reduction / level1_total * 100) if level1_total > 0 else 0
    tokens_improvement = (level2_tokens/level2_total) / (level1_tokens/level1_total) if level1_total > 0 else 0
    
    print("\n📈 Improvement (Level 1 → Level 2):")
    print(f"   Chunk reduction: {reduction} ({reduction_pct:.1f}%)")
    print(f"   Tokens/chunk improvement: {tokens_improvement:.2f}x")
    
    print("\n📄 Sample Output (First 3 sentences - Level 2):\n")
    
    for i, (sent_text, chunks) in enumerate(level2_results[:3], 1):
        print_section(f"Sentence {i}")
        print(f"{sent_text}\n")
        for chunk in chunks:
            print(f"  {chunk}")
    
    # ========================================================================
    # SUMMARY
    # ========================================================================
    
    print_header("SUMMARY", "=")
    
    validation_info = ""
    if config['pipeline']['enable_validation']:
        validation_info = f"""
LEVEL 1.5 (CONSTITUENT VALIDATION):
• Five linguistic tests: substitution, coordination, dislocation, cleft, fragment
• Aggregate scoring with configurable threshold
• Low-confidence chunk identification
• Optional filtering of invalid constituents
"""
    
    print(f"""
✅ TWO-LEVEL CHUNKING COMPLETE

LEVEL 1 (UD-BASED):
• Syntactic phrase detection using dependency relations
• Merge relations: det, amod, nummod, flat:name, aux, case, appos
• Copula exclusion, proper name merging, apposition handling
{validation_info}
LEVEL 2 (SEMANTIC MERGER):
• Subject-verb merging (SujV + SV → SV)
• Prepositional phrase completion (SP + SN → SP)
• Temporal expression merging (SN + SN → SN)
• Adverb-verb combinations (SAdv + SV → SV)
• Coordination handling (SN + Coord + SN → SN)

RESULTS:
• Level 1: {level1_total} chunks, {level1_tokens/level1_total:.2f} tokens/chunk
• Level 2: {level2_total} chunks, {level2_tokens/level2_total:.2f} tokens/chunk
• Improvement: {reduction_pct:.1f}% reduction, {tokens_improvement:.2f}x token density

NEXT STEPS:
• Analyze validation scores and refine chunking rules
• Integrate with downstream NLP tasks
• Extend to other French corpora
""")
    
    print_header("✅ PHASE B COMPLETE", "=")
    print()
    print(f"📄 Level 1 output: {output_file_level1}")
    print(f"📄 Level 2 output: {output_file_level2}")
    print(f"📊 {sentence_count} sentences processed")
    print()


if __name__ == '__main__':
    main()

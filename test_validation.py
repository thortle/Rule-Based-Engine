#!/usr/bin/env python3
"""
Test Validation on Existing Corpus

This script tests the constituent validation feature on the pre-parsed
gorafi_medical corpus without requiring Stanza.
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from linguistic_chunker import UDSentence, UDToken, extract_linguistic_chunks_v2
from chunk_validator import ChunkValidator


def load_json_as_udsentences(json_file):
    """Load JSON file and convert to UDSentence objects"""
    with open(json_file, 'r', encoding='utf-8') as f:
        sentences_json = json.load(f)
    
    sentences = []
    for sent_idx, sent_json in enumerate(sentences_json, 1):
        tokens = []
        sent_text = " ".join([token["form"] for token in sent_json])
        
        for token_json in sent_json:
            token = UDToken([
                str(token_json["id"]),
                token_json["form"],
                token_json["lemma"],
                token_json["upos"],
                "_",  # xpos
                "_",  # feats
                str(token_json["head"]),
                token_json["deprel"],
                "_",  # deps
                "_"   # misc
            ])
            tokens.append(token)
        
        sentences.append(UDSentence(str(sent_idx), sent_text, tokens))
    
    return sentences


def print_header(text, char="="):
    """Print formatted header"""
    print(f"\n{char * 70}")
    print(f"{text:^70}")
    print(f"{char * 70}\n")


def main():
    """Test validation on corpus"""
    
    print_header("CONSTITUENT VALIDATION TEST", "=")
    print("Testing Level 1.5 validation on gorafi_medical corpus\n")
    
    # Load data
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_file = os.path.join(script_dir, 'data', 'gorafi_medical.json')
    
    print(f"📂 Loading corpus from: {json_file}")
    sentences = load_json_as_udsentences(json_file)
    print(f"✓ Loaded {len(sentences)} sentences\n")
    
    # Initialize validator
    print("🔧 Initializing ChunkValidator...")
    validator = ChunkValidator(lang='fr')
    print("✓ Validator ready\n")
    
    # Run Level 1 chunking + validation
    print_header("RUNNING VALIDATION", "-")
    
    all_validated = []
    for idx, sentence in enumerate(sentences, 1):
        # Level 1: Extract chunks
        chunks = extract_linguistic_chunks_v2(sentence)
        
        # Level 1.5: Validate chunks
        validated_chunks = validator.validate_all(chunks, sentence)
        all_validated.extend(validated_chunks)
        
        if idx <= 3:  # Show first 3 sentences
            print(f"\n📄 Sentence {idx}:")
            print(f"   {sentence.text[:80]}...")
            print(f"   Chunks: {len(chunks)}, Validated: {len(validated_chunks)}")
    
    print(f"\n✓ Validated {len(all_validated)} chunks across {len(sentences)} sentences")
    
    # Statistics
    print_header("VALIDATION STATISTICS", "=")
    
    stats = validator.get_statistics(all_validated)
    
    print(f"📊 Overall Statistics:")
    print(f"   Total chunks: {stats['total_chunks']}")
    print(f"   Passed chunks: {stats['passed_chunks']} ({stats['pass_rate']*100:.1f}%)")
    print(f"   Failed chunks: {stats['total_chunks'] - stats['passed_chunks']} ({(1-stats['pass_rate'])*100:.1f}%)")
    print(f"\n📈 Aggregate Scores:")
    print(f"   Mean: {stats['avg_aggregate']:.3f}")
    print(f"   Min:  {stats['min_aggregate']:.3f}")
    print(f"   Max:  {stats['max_aggregate']:.3f}")
    print(f"\n📋 Test Scores (averages):")
    print(f"   Pronominal substitution: {stats['avg_substitution']:.3f}")
    print(f"   Coordination:            {stats['avg_coordination']:.3f}")
    print(f"   Dislocation:             {stats['avg_dislocation']:.3f}")
    print(f"   Cleft construction:      {stats['avg_cleft']:.3f}")
    print(f"   Fragment answer:         {stats['avg_fragment']:.3f}")
    
    # Score distribution
    print_header("SCORE DISTRIBUTION", "-")
    
    score_ranges = {
        'Excellent (0.8-1.0)': [0.8, 1.0],
        'Good (0.6-0.8)': [0.6, 0.8],
        'Moderate (0.4-0.6)': [0.4, 0.6],
        'Low (0.2-0.4)': [0.2, 0.4],
        'Poor (0.0-0.2)': [0.0, 0.2],
    }
    
    for label, (min_s, max_s) in score_ranges.items():
        count = sum(1 for vc in all_validated 
                   if min_s <= vc.score.aggregate < max_s or (max_s == 1.0 and vc.score.aggregate == 1.0))
        pct = count / len(all_validated) * 100 if all_validated else 0
        bar = "█" * int(pct / 2)  # Scale to 50 chars max
        print(f"   {label:25} {count:3} ({pct:5.1f}%) {bar}")
    
    # Low-confidence chunks
    print_header("LOW-CONFIDENCE CHUNKS", "-")
    
    low_conf = validator.get_low_confidence_chunks(all_validated, threshold=0.4)
    print(f"\n⚠️  Found {len(low_conf)} low-confidence chunks (score < 0.4):\n")
    
    for i, vc in enumerate(low_conf[:10], 1):  # Show first 10
        print(f"{i:2}. {vc}")
    
    if len(low_conf) > 10:
        print(f"\n   ... and {len(low_conf) - 10} more low-confidence chunks")
    
    # High-confidence chunks
    print_header("HIGH-CONFIDENCE CHUNKS", "-")
    
    high_conf = [vc for vc in all_validated if vc.score.aggregate >= 0.8]
    print(f"\n✓ Found {len(high_conf)} high-confidence chunks (score >= 0.8):\n")
    
    for i, vc in enumerate(high_conf[:10], 1):  # Show first 10
        print(f"{i:2}. {vc}")
    
    if len(high_conf) > 10:
        print(f"\n   ... and {len(high_conf) - 10} more high-confidence chunks")
    
    # Category analysis
    print_header("ANALYSIS BY CHUNK CATEGORY", "-")
    
    categories = {}
    for vc in all_validated:
        cat = vc.category
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(vc.score.aggregate)
    
    print("\nAverage scores by category:\n")
    for cat in sorted(categories.keys()):
        scores = categories[cat]
        avg = sum(scores) / len(scores)
        count = len(scores)
        print(f"   {cat:10} ({count:3} chunks): {avg:.3f}")
    
    # Summary
    print_header("SUMMARY", "=")
    
    print(f"""
✅ VALIDATION COMPLETE

CORPUS:
• {len(sentences)} sentences
• {stats['total_chunks']} chunks validated

RESULTS:
• Pass rate: {stats['pass_rate']*100:.1f}%
• Average score: {stats['avg_aggregate']:.3f}
• Score range: {stats['min_aggregate']:.3f} - {stats['max_aggregate']:.3f}

TOP PERFORMING TEST:
• {max([('Substitution', stats['avg_substitution']), 
       ('Coordination', stats['avg_coordination']),
       ('Dislocation', stats['avg_dislocation']),
       ('Cleft', stats['avg_cleft']),
       ('Fragment', stats['avg_fragment'])], key=lambda x: x[1])[0]}

INSIGHTS:
• {len(high_conf)} chunks are strong constituents (>= 0.8)
• {len(low_conf)} chunks need review (< 0.4)
• Validation successfully identifies linguistic quality
""")
    
    print("=" * 70)


if __name__ == '__main__':
    main()

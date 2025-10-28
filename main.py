#!/usr/bin/env python3
"""
UD-Based French Text Chunker

Main entry point for the two-level French text chunking system.

Usage:
    python main.py [--config config.json] [--debug] [--multi-pass]
"""

import os
import json
import argparse
from pipeline import ChunkerPipeline


def load_config(config_file: str = "config.json") -> dict:
    """Load configuration from JSON file or return defaults."""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "pipeline": {"enable_level1": True, "enable_level2": True},
            "level2_semantic_merger": {
                "rules_file": "lang_fr/semantic_rules.json",
                "multi_pass": False,
                "max_passes": 10,
                "debug": False
            },
            "output": {
                "save_level1": True,
                "save_level2": True,
                "output_dir": "data/output"
            }
        }


def print_header(text, char="="):
    """Print formatted header."""
    print(f"\n{char * 80}\n{text}\n{char * 80}")


def print_section(text):
    """Print section divider."""
    print(f"\n{'-' * 80}\n{text}\n{'-' * 80}")


def main():
    """Main entry point."""
    # Parse arguments
    parser = argparse.ArgumentParser(description='UD-Based French Text Chunker')
    parser.add_argument('--config', default='config.json', help='Configuration file')
    parser.add_argument('--debug', action='store_true', help='Debug mode')
    parser.add_argument('--multi-pass', action='store_true', help='Multi-pass merging')
    parser.add_argument('--max-passes', type=int, help='Max passes (overrides config)')
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    if args.debug:
        config['level2_semantic_merger']['debug'] = True
    if args.multi_pass:
        config['level2_semantic_merger']['multi_pass'] = True
    if args.max_passes:
        config['level2_semantic_merger']['max_passes'] = args.max_passes
    
    # Print header
    print_header("UD-BASED FRENCH TEXT CHUNKER")
    print(f"\n• Level 1 (UD): {'Enabled' if config['pipeline']['enable_level1'] else 'Disabled'}")
    print(f"• Level 2 (Semantic): {'Enabled' if config['pipeline']['enable_level2'] else 'Disabled'}")
    print(f"• Multi-pass: {'Yes' if config['level2_semantic_merger']['multi_pass'] else 'No'}")
    
    # Setup paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    text_file = os.path.join(script_dir, 'data', 'gorafi_medical.txt')
    output_dir = os.path.join(script_dir, config['output']['output_dir'])
    os.makedirs(output_dir, exist_ok=True)
    
    # Run pipeline
    print("\n🔄 Running chunking pipeline...")
    pipeline = ChunkerPipeline(config)
    level1_results, level2_results = pipeline.run(text_file, output_dir)
    print("✓ Pipeline complete")
    
    # Display statistics
    print_header("TWO-LEVEL CHUNKING RESULTS")
    
    stats_l1 = ChunkerPipeline.compute_statistics(level1_results)
    stats_l2 = ChunkerPipeline.compute_statistics(level2_results)
    
    print("\nLEVEL 1 (UD-Based):")
    print(f"   Total chunks: {stats_l1['total_chunks']}")
    print(f"   Tokens/chunk: {stats_l1['tokens_per_chunk']:.2f}")
    
    print("\nLEVEL 2 (Semantic Merger):")
    print(f"   Total chunks: {stats_l2['total_chunks']}")
    print(f"   Tokens/chunk: {stats_l2['tokens_per_chunk']:.2f}")
    
    reduction = stats_l1['total_chunks'] - stats_l2['total_chunks']
    reduction_pct = (reduction / stats_l1['total_chunks'] * 100) if stats_l1['total_chunks'] > 0 else 0
    improvement = stats_l2['tokens_per_chunk'] / stats_l1['tokens_per_chunk'] if stats_l1['tokens_per_chunk'] > 0 else 0
    
    print("\n📈 Improvement:")
    print(f"   Chunk reduction: {reduction} ({reduction_pct:.1f}%)")
    print(f"   Tokens/chunk improvement: {improvement:.2f}x")
    
    # Sample output
    print("\n📄 Sample Output (First 3 sentences - Level 2):\n")
    for i, (sent_text, chunks) in enumerate(level2_results[:3], 1):
        print_section(f"Sentence {i}")
        print(f"{sent_text}\n")
        for chunk in chunks:
            print(f"  {chunk}")
    
    print_header("COMPLETE")
    print(f"\nOutput files:")
    print(f"  • Level 1: {output_dir}/gorafi_medical_level1.txt")
    print(f"  • Level 2: {output_dir}/gorafi_medical_level2.txt")
    print(f"\n{len(level2_results)} sentences processed\n")


if __name__ == '__main__':
    main()

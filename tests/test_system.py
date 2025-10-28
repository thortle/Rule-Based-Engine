#!/usr/bin/env python3
"""
System Integration Tests - Rule-Based French Text Chunker

Tests the complete pipeline and verifies final results.
Focus: End-to-end functionality, not internal implementation details.

This is the ONLY test file needed for demonstration and validation.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.pipeline import ChunkerPipeline


def count_chunks(results):
    """Count total chunks from pipeline results."""
    return sum(len(chunks) for _, chunks in results)


def test_pipeline_level1_only():
    """Test Level 1 (UD-based chunking) produces expected output."""
    print("\n" + "="*80)
    print("TEST 1: Level 1 (UD-Based Chunking)")
    print("="*80)
    
    config = {
        "pipeline": {
            "enable_level1": True,
            "enable_level2": False
        },
        "level2_semantic_merger": {
            "rules_file": "lang_fr/semantic_rules.json",
            "multi_pass": False
        },
        "output": {
            "save_level1": False,
            "save_level2": False
        }
    }
    
    pipeline = ChunkerPipeline(config)
    level1_results, _ = pipeline.run("data/gorafi_medical.txt", "data/output")
    
    # Count total chunks
    total_chunks = count_chunks(level1_results)
    
    # Verify Level 1 results
    assert total_chunks == 268, \
        f"Expected 268 Level 1 chunks, got {total_chunks}"
    
    print(f"[OK] Level 1 chunking: {total_chunks} chunks")
    print(f"[OK] Sentences processed: {len(level1_results)}")
    print("="*80)
    print("PASSED\n")


def test_pipeline_level2_single_pass():
    """Test Level 2 with single-pass semantic merging."""
    print("="*80)
    print("TEST 2: Level 2 (Single-Pass Semantic Merging)")
    print("="*80)
    
    config = {
        "pipeline": {
            "enable_level1": True,
            "enable_level2": True
        },
        "level2_semantic_merger": {
            "rules_file": "lang_fr/semantic_rules.json",
            "multi_pass": False
        },
        "output": {
            "save_level1": False,
            "save_level2": False
        }
    }
    
    pipeline = ChunkerPipeline(config)
    level1_results, level2_results = pipeline.run("data/gorafi_medical.txt", "data/output")
    
    # Count chunks
    level1_chunks = count_chunks(level1_results)
    level2_chunks = count_chunks(level2_results)
    
    # Verify results
    assert level1_chunks == 268, \
        f"Expected 268 Level 1 chunks, got {level1_chunks}"
    assert level2_chunks == 201, \
        f"Expected 201 Level 2 chunks (single-pass), got {level2_chunks}"
    
    reduction = level1_chunks - level2_chunks
    reduction_pct = (reduction / level1_chunks) * 100
    
    print(f"[OK] Level 1: {level1_chunks} chunks")
    print(f"[OK] Level 2: {level2_chunks} chunks")
    print(f"[OK] Reduction: {reduction} chunks ({reduction_pct:.1f}%)")
    print("="*80)
    print("PASSED\n")


def test_pipeline_level2_multi_pass():
    """Test Level 2 with multi-pass semantic merging (BASELINE)."""
    print("="*80)
    print("TEST 3: Level 2 (Multi-Pass Semantic Merging) - BASELINE")
    print("="*80)
    
    config = {
        "pipeline": {
            "enable_level1": True,
            "enable_level2": True
        },
        "level2_semantic_merger": {
            "rules_file": "lang_fr/semantic_rules.json",
            "multi_pass": True,
            "max_passes": 10
        },
        "output": {
            "save_level1": False,
            "save_level2": False
        }
    }
    
    pipeline = ChunkerPipeline(config)
    level1_results, level2_results = pipeline.run("data/gorafi_medical.txt", "data/output")
    
    # Count chunks
    level1_chunks = count_chunks(level1_results)
    level2_chunks = count_chunks(level2_results)
    
    # Verify BASELINE results (268→142 chunks, 47% reduction)
    assert level1_chunks == 268, \
        f"Expected 268 Level 1 chunks, got {level1_chunks}"
    assert level2_chunks == 142, \
        f"Expected 142 Level 2 chunks (multi-pass), got {level2_chunks}"
    
    reduction = level1_chunks - level2_chunks
    reduction_pct = (reduction / level1_chunks) * 100
    
    # Round for comparison (floating point precision)
    assert round(reduction_pct, 1) == 47.0, \
        f"Expected 47.0% reduction, got {reduction_pct:.1f}%"
    
    print(f"[OK] Level 1: {level1_chunks} chunks")
    print(f"[OK] Level 2: {level2_chunks} chunks")
    print(f"[OK] Reduction: {reduction} chunks ({reduction_pct:.1f}%)")
    print("\n[BASELINE VERIFIED] 268->142 chunks (47% reduction)")
    print("="*80)
    print("PASSED\n")


def test_output_files():
    """Test that output files are created correctly."""
    print("="*80)
    print("TEST 4: Output File Generation")
    print("="*80)
    
    config = {
        "pipeline": {
            "enable_level1": True,
            "enable_level2": True
        },
        "level2_semantic_merger": {
            "rules_file": "lang_fr/semantic_rules.json",
            "multi_pass": True,
            "max_passes": 10
        },
        "output": {
            "save_level1": True,
            "save_level2": True
        }
    }
    
    pipeline = ChunkerPipeline(config)
    pipeline.run("data/gorafi_medical.txt", "data/output")
    
    # Check that output files were created
    level1_file = Path("data/output/gorafi_medical_level1.txt")
    level2_file = Path("data/output/gorafi_medical_level2.txt")
    
    assert level1_file.exists(), f"Level 1 output file not created: {level1_file}"
    assert level2_file.exists(), f"Level 2 output file not created: {level2_file}"
    
    # Check that files have content
    level1_size = level1_file.stat().st_size
    level2_size = level2_file.stat().st_size
    
    assert level1_size > 0, "Level 1 output file is empty"
    assert level2_size > 0, "Level 2 output file is empty"
    
    print(f"[OK] Level 1 output: {level1_file} ({level1_size} bytes)")
    print(f"[OK] Level 2 output: {level2_file} ({level2_size} bytes)")
    print("="*80)
    print("PASSED\n")


def main():
    """Run all system tests."""
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "  SYSTEM INTEGRATION TESTS - Rule-Based French Text Chunker".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "="*78 + "╝")
    print()
    
    tests = [
        test_pipeline_level1_only,
        test_pipeline_level2_single_pass,
        test_pipeline_level2_multi_pass,
        test_output_files
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"\n❌ FAILED: {test_func.__name__}")
            print(f"   Error: {e}\n")
            failed += 1
        except Exception as e:
            print(f"\n❌ ERROR in {test_func.__name__}")
            print(f"   {type(e).__name__}: {e}\n")
            failed += 1
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total tests: {len(tests)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print("="*80)
    
    if failed == 0:
        print("\nALL TESTS PASSED! System is working correctly.")
    else:
        print(f"\n{failed} test(s) failed. Please review the errors above.")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

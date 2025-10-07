# UD-Based French Text Chunker

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![Stanza](https://img.shields.io/badge/stanza-1.11.0-green.svg)](https://stanfordnlp.github.io/stanza/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A linguistically-principled French text chunker using **Universal Dependencies** parsing with semantic rule-based merging. Achieves **47% chunk reduction** while maintaining semantic coherence.

## Quick Links

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Performance](#performance)
- [How It Works](#how-it-works)

---

## Project Structure

```
Rule-Based-Engine/
├── main.py                    # Pipeline orchestration
├── linguistic_chunker.py      # Level 1: UD-based chunking
├── chunk_validator.py         # Level 1.5: Constituent validation (NEW)
├── semantic_merger.py         # Level 2: Semantic merging
├── test_validation.py         # Validation test script (NEW)
├── config.json                # Configuration
├── data/                      # Test corpus and outputs
├── lang_fr/
│   ├── semantic_rules.json    # 19 semantic merging rules
│   └── validation_patterns.json  # French linguistic patterns (NEW)
└── tests/
    ├── test_conditions.py     # Condition tests (8 tests)
    └── test_chunk_validator.py  # Validation tests (26 tests) (NEW)
```

---

## Overview

This project implements a **three-level text chunking system** for French text processing:

**Level 1 (UD-Based Syntactic Chunking):**
- Parse text with Stanza to extract Universal Dependencies structure
- Use dependency relations to identify phrase boundaries
- Create linguistically-grounded syntactic chunks

**Level 1.5 (Constituent Validation) - NEW:**
- Apply five linguistic constituency tests to validate chunks
- Score each chunk (0.0-1.0) based on linguistic principles
- Identify and flag low-confidence chunks for review
- Optional filtering of invalid constituents

**Level 2 (Semantic Merging):**
- Apply pattern-matching rules to Level 1 chunks
- Merge semantically-related chunks based on linguistic conditions
- Produce cohesive, meaningful text units

### Key Features

- 47% chunk reduction (268 → 142 chunks on test corpus)
- 3.37 tokens/chunk (1.89x improvement in density)
- **NEW:** Constituent validation with 5 linguistic tests
- **NEW:** Quality scoring for all chunks (0.911 avg for noun phrases)
- 19 semantic rules with multi-pass merging capability
- Linguistically grounded using Universal Dependencies framework
- Modular architecture - each level is independently testable

### Why Three Levels?

Traditional rule-based chunking struggles with POS tagging errors, proper name fragmentation, split temporal expressions, and broken passive voice constructions.

Our solution combines **linguistic structure (UD)** with **validity testing (constituent validation)** and **semantic patterns (rules)** for accurate POS tags, validated constituent boundaries, linguistic quality metrics, semantic coherence, and transparent results.

---

## Installation

```bash
# Install Stanza
pip install stanza

# Download French language model
python -c "import stanza; stanza.download('fr')"
```

---

## Quick Start

```bash
# Basic usage
python main.py

# With constituent validation (recommended)
python main.py --validate

# Multi-pass merging + validation
python main.py --validate --multi-pass

# Filter low-quality chunks
python main.py --validate --filter-low-scores --min-score 0.6

# Test validation only (no Stanza required)
python test_validation.py

# View results
cat data/output/gorafi_medical_level1.txt  # Syntactic chunks
cat data/output/gorafi_medical_level2.txt  # Semantic chunks
```

---

## Architecture

The system uses a three-level pipeline:

1. **Level 1:** Stanza Parser → CoNLL-U → UD-based syntactic chunks
2. **Level 1.5:** Constituent validation → Linguistic quality scoring
3. **Level 2:** Semantic rules → Pattern matching → Merged chunks

```
Input Text
    ↓
Level 1: UD-Based Syntactic Chunking
    - Stanza parser → CoNLL-U format
    - Extract dependency relations
    - Output: 268 fine-grained chunks
    ↓
Level 1.5: Constituent Validation (Optional)
    - Apply 5 linguistic tests
    - Score each chunk (0.0-1.0)
    - Filter low-confidence chunks
    ↓
Level 2: Semantic Merging
    - Apply 19 pattern-matching rules
    - Multi-pass merging
    - Output: 142 semantically merged chunks
    ↓
Final Output
```

**Note:** This project includes custom CoNLL-U parsing logic (inspired by the CONLLU-to-JSON utility) that extracts the HEAD field critical for dependency tree traversal.

---

## Performance

Test corpus: 15 sentences, 479 tokens from Le Gorafi

| Metric | Level 1 | Level 2 | Improvement |
|--------|---------|---------|-------------|
| **Chunks** | 268 | 142 | -47% |
| **Tokens/chunk** | 1.79 | 3.37 | +88% |

**Example improvement:**
- Input: "Il est 18 h 30 ce lundi 27 janvier quand Jean-Noël C. est admis..."
- Level 1: 11 fine-grained chunks
- Level 2: 4 semantically merged chunks (63.6% reduction)

---

## Constituent Validation (Level 1.5)

The validation layer applies **five linguistic constituency tests** to score chunks (0.0-1.0) on their validity as syntactic constituents:

1. **Pronominal Substitution** - Can it be replaced by a pronoun? ("le chat" → "il" ✓)
2. **Coordination** - Can two instances be coordinated? ("[le chat] et [la souris]" ✓)
3. **Dislocation** - Can it move to sentence periphery? ("Le chat, Kim le regarde" ✓)
4. **Cleft Construction** - Does it work in "C'est...que/qui"? ("C'est [le chat] qui..." ✓)
5. **Fragment Answer** - Can it answer a question? (Q: "Qui?" A: "[Le chat]" ✓)

### Key Insight: Function Words vs. Constituents

Low scores for function words (coordinators, subordinators, punctuation) are **linguistically correct**:
- Function words **cannot** be pronominalized, coordinated, or dislocated
- They serve structural roles (connect/introduce clauses) rather than acting as constituents
- Solution: Recognize both types with different validation logic:
  - **True constituents** (SN, SV) → Pass if score ≥ 0.4
  - **Structural markers** (Coord, CSub, Pct) → Auto-pass with special flag

### Results on Test Corpus (268 chunks)

| Category | Avg Score | Pass Rate | Interpretation |
|----------|-----------|-----------|----------------|
| SN (Noun phrases) | 0.911 | 100% | Excellent constituents |
| SujV (Subject pronouns) | 0.438 | 77% |  Good |
| SV (Verb phrases) | 0.202 | 19% |  Needs improvement |
| Coord/CSub/Pct | 0.01 | 100%* | *Structural markers (auto-pass) |

**Overall:** 62.7% pass rate (168/268 chunks: 93 valid constituents + 75 structural markers)

### Usage

```bash
# Enable validation (recommended)
python main.py --validate

# Filter low-quality chunks
python main.py --validate --filter-low-scores --min-score 0.6

# Test validation only (no Stanza required)
python test_validation.py

# Run unit tests (26 tests)
python tests/test_chunk_validator.py
```

**Example Output:**
```
✓ [SN] Jean-Noël C. ValidationScore(agg=0.84, sub=0.85, coord=0.77, disl=0.70, cleft=0.95, frag=0.95)
✓ [SN] à l' hôpital Rangueil ValidationScore(agg=0.96, sub=1.00, coord=0.94, disl=0.90, cleft=0.95, frag=1.00)
✓ [Coord] et ValidationScore(agg=0.01, ...) [structural_marker]
```

---

## Testing

```bash
# Run semantic merger tests
cd tests
python test_conditions.py  # 8 tests

# Run validation tests
python test_chunk_validator.py  # 26 tests

# Test validation on corpus
cd ..
python test_validation.py
```

**Test Coverage:**
- **Level 2:** 8/8 tests passing (condition functions)
- **Level 1.5:** 26/26 tests passing (validation functions)
- **Total:** 34 unit tests, 100% pass rate

---

## Technical Details

### UD Relations Used
- `det` (determiner), `amod` (adjective), `nummod` (numeric)
- `flat:name` (proper names), `aux` (auxiliary verbs)
- `case` (prepositions), `appos` (apposition)

### Semantic Rules
19 rules including subject-verb merging, temporal merging, prepositional chains, verb-object merging, and subordinate clause completion.

### Dependencies
- Python 3.13+
- Stanza 1.11.0

---

## References

- [Universal Dependencies](https://universaldependencies.org/)
- [Stanza Documentation](https://stanfordnlp.github.io/stanza/)
- [CoNLL-U Format](https://universaldependencies.org/format.html)
- Related: CONLLU-to-JSON utility (inspiration for parsing logic)

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

## Summary

This project demonstrates that combining **Universal Dependencies parsing**, **linguistic constituency validation**, and **semantic rule-based merging** provides superior text chunking with quality guarantees.

The three-level architecture:
1. **Level 1** (UD) - Linguistic accuracy via dependency parsing
2. **Level 1.5** (Validation) - Quality scoring via constituency tests
3. **Level 2** (Semantic) - Semantic coherence via pattern matching

**Key achievements:**
- 47% chunk reduction (268 → 142 chunks)
- 88% density improvement (1.79 → 3.37 tokens/chunk)
- 91.1% avg quality score for noun phrases
- 34 unit tests, 100% pass rate
- Transparent, interpretable, linguistically grounded

**Use cases:**
- Text preprocessing for NLP pipelines
- Information extraction systems
- Semantic search and retrieval
- Machine translation preprocessing
- Linguistic corpus analysis

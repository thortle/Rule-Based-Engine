# UD-Based French Text Chunker

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![Stanza](https://img.shields.io/badge/stanza-1.11.0-green.svg)](https://stanfordnlp.github.io/stanza/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A linguistically-principled French text chunker using Universal Dependencies parsing with semantic rule-based merging.

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
├── semantic_merger.py         # Level 2: Semantic merging
├── config.json                # Configuration
├── data/                      # Test corpus and outputs
├── lang_fr/
│   └── semantic_rules.json    # 19 semantic merging rules
└── tests/
    └── test_conditions.py     # Condition tests (8 tests)
```

---

## Overview

This project implements a two-level text chunking system for French text processing:

**Level 1 (UD-Based Syntactic Chunking):**
- Parse text with Stanza to extract Universal Dependencies structure
- Use dependency relations to identify phrase boundaries
- Create linguistically-grounded syntactic chunks

**Level 2 (Semantic Merging):**
- Apply pattern-matching rules to Level 1 chunks
- Merge semantically-related chunks based on linguistic conditions
- Produce cohesive, meaningful text units

### Key Features

- 47% chunk reduction (268 to 142 chunks on test corpus)
- 3.37 tokens/chunk (1.89x improvement in density)
- 19 semantic rules with multi-pass merging capability
- Linguistically grounded using Universal Dependencies framework
- Modular architecture - each level is independently testable

### Why Two Levels?

Traditional rule-based chunking struggles with POS tagging errors, proper name fragmentation, split temporal expressions, and broken passive voice constructions.

Our solution combines linguistic structure (UD) with semantic patterns (rules) for accurate POS tags, semantic coherence, and transparent results.

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

# Multi-pass merging
python main.py --multi-pass

# View results
cat data/output/gorafi_medical_level1.txt  # Syntactic chunks
cat data/output/gorafi_medical_level2.txt  # Semantic chunks
```

---

## Architecture

The system uses a two-level pipeline:

1. **Level 1:** Stanza Parser to CoNLL-U to UD-based syntactic chunks
2. **Level 2:** Semantic rules to Pattern matching to Merged chunks

```
Input Text
    ↓
Level 1: UD-Based Syntactic Chunking
    - Stanza parser to CoNLL-U format
    - Extract dependency relations
    - Output: 268 fine-grained chunks
    ↓
Level 2: Semantic Merging
    - Apply 19 pattern-matching rules
    - Multi-pass merging
    - Output: 142 semantically merged chunks
    ↓
Final Output
```

This project includes custom CoNLL-U parsing logic (inspired by the CONLLU-to-JSON utility) that extracts the HEAD field critical for dependency tree traversal.

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

## Testing

```bash
# Run semantic merger tests
cd tests
python test_conditions.py  # 8 tests
```

**Test Coverage:**
- Level 2: 8/8 tests passing (condition functions)

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

This project demonstrates that combining Universal Dependencies parsing and semantic rule-based merging provides superior text chunking.

The two-level architecture:
1. Level 1 (UD) - Linguistic accuracy via dependency parsing
2. Level 2 (Semantic) - Semantic coherence via pattern matching

**Key achievements:**
- 47% chunk reduction (268 to 142 chunks)
- 88% density improvement (1.79 to 3.37 tokens/chunk)
- 8 unit tests passing
- Transparent, interpretable, linguistically grounded

**Use cases:**
- Text preprocessing for NLP pipelines
- Information extraction systems
- Semantic search and retrieval
- Machine translation preprocessing
- Linguistic corpus analysis

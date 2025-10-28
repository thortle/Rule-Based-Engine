# UD-Based French Text Chunker

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![Stanza](https://img.shields.io/badge/stanza-1.11.0-green.svg)](https://stanfordnlp.github.io/stanza/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A linguistically-principled French text chunker using Universal Dependencies parsing with semantic rule-based merging. **Now featuring a clean OOP architecture with SOLID principles.**

## Quick Links

- [Installation](#installation)
- [Quick Start](#quick-start)
- [OOP Architecture](#oop-architecture)
- [Performance](#performance)
- [How It Works](#how-it-works)
- [OOP Refactoring Benefits](#oop-refactoring-benefits)

---

## Project Structure

```
Rule-Based-Engine/
├── main.py                    # CLI entry point
├── models.py                  # Data models: Token, Chunk, Sentence
├── chunkers.py                # Chunker ABC + UDChunker implementation
├── semantic_rules.py          # SemanticRule ABC + concrete rules + SemanticMerger
├── pipeline.py                # ChunkerPipeline orchestration facade
├── config.json                # Pipeline configuration
├── data/                      # Test corpus and outputs
├── lang_fr/
│   └── semantic_rules.json    # Semantic merging rules
└── tests/
    └── test_system.py         # System integration tests
```

---

## Overview

This project implements a two-level text chunking system for French text processing using a modern OOP architecture with SOLID principles:

**Level 1 (UD-Based Syntactic Chunking):**
- Parse text with Stanza to extract Universal Dependencies structure
- Use dependency relations to identify phrase boundaries via `UDChunker` class
- Create linguistically-grounded syntactic chunks

**Level 2 (Semantic Merging):**
- Apply pattern-matching rules via `SemanticRule` hierarchy
- Merge semantically-related chunks using `SemanticMerger` orchestrator
- Produce cohesive, meaningful text units

### Key Features

- 47% chunk reduction (268 to 142 chunks on test corpus)
- 3.37 tokens/chunk (1.89x improvement in density)
- 19 semantic rules with multi-pass merging capability
- Clean OOP architecture with Strategy, Facade, and Factory patterns
- System integration tests validating end-to-end functionality
- SOLID principles applied throughout (see OOP_ANALYSIS.md for details)
- Linguistically grounded using Universal Dependencies framework

### Why Two Levels?

Traditional rule-based chunking struggles with POS tagging errors, proper name fragmentation, split temporal expressions, and broken passive voice constructions.

Our solution combines linguistic structure (UD) with semantic patterns (rules) for accurate POS tags, semantic coherence, and transparent results.

### OOP Architecture

The system is built using SOLID principles with clear separation of concerns:
- **Strategy Pattern**: Swappable chunking algorithms and semantic rules
- **Facade Pattern**: Simplified interface to complex subsystem
- **Factory Pattern**: Dynamic rule creation from JSON configuration

For detailed architecture analysis and OOP benefits, see [OOP_ANALYSIS.md](OOP_ANALYSIS.md).

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

The system follows a two-level pipeline architecture:

```
Input Text
    ↓
ChunkerPipeline.run()
    ↓
Level 1: UDChunker (UD-Based Syntactic Chunking)
    - Stanza parser to CoNLL-U format
    - Extract dependency relations
    - Build phrase mappings (det, amod, flat:name, etc.)
    - Output: 268 fine-grained syntactic chunks
    ↓
Level 2: SemanticMerger (Semantic Merging)
    - Load 19 rules from JSON via factory
    - Apply rules iteratively (multi-pass support)
    - Merge semantically-related chunks
    - Output: 142 semantically merged chunks
    ↓
Save formatted output (Level 1 & Level 2 files)
```

### Core Components

- **models.py**: Data structures (Token, Chunk, Sentence)
- **chunkers.py**: Chunker ABC and UDChunker implementation
- **semantic_rules.py**: SemanticRule ABC, concrete rules, and SemanticMerger
- **pipeline.py**: ChunkerPipeline facade orchestrating the workflow
- **main.py**: CLI entry point with configuration handling

### Design Patterns

The architecture uses three key design patterns:
- **Strategy Pattern**: Swappable chunking algorithms and semantic rules
- **Facade Pattern**: ChunkerPipeline simplifies complex subsystem interactions
- **Factory Pattern**: Dynamic rule creation from JSON configuration

This project includes custom CoNLL-U parsing logic that extracts the HEAD field critical for dependency tree traversal.

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

The project includes system integration tests validating end-to-end functionality:

```bash
# Run integration tests
cd /Users/thortle/Desktop/Univ/M2/OOP/project/Rule-Based-Engine
source venv/bin/activate
python tests/test_system.py
```

**Test Coverage:**
1. Level 1 (UD-based chunking): 268 chunks
2. Level 2 (single-pass merging): 268 to 201 chunks (25% reduction)
3. Level 2 (multi-pass merging): 268 to 142 chunks (47% reduction - baseline)
4. Output file generation

All tests verify the baseline performance is maintained.

---

## OOP Refactoring

This project was refactored from a procedural codebase to a clean OOP architecture following SOLID principles. The refactoring improved maintainability, scalability, and code quality without sacrificing performance.

**Key Improvements:**
- 75% reduction in main orchestration file
- Clear separation of concerns with focused modules
- Strategy, Facade, and Factory patterns for extensibility
- SOLID principles applied throughout

**Example - Adding a new chunker:**
```python
class NeuralChunker(Chunker):
    def chunk_sentence(self, sentence: Sentence) -> List[Chunk]:
        # Neural network-based chunking
        return neural_chunks

# Use it - no changes to existing code
pipeline = ChunkerPipeline(chunker=NeuralChunker())
```

**Example - Adding new semantic rules:**
```json
{
    "name": "quotation_merge",
    "condition": "both_are_quotations",
    "description": "Merge quotation marks with content"
}
```

For detailed analysis of OOP benefits, design patterns, SOLID principles, and real-world impact scenarios, see **[OOP_ANALYSIS.md](OOP_ANALYSIS.md)**.

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

This project demonstrates that combining Universal Dependencies parsing with semantic rule-based merging provides superior text chunking, **especially when built with clean OOP architecture**.

### Two-Level Architecture:
1. **Level 1 (UD)** - Linguistic accuracy via dependency parsing with `UDChunker`
2. **Level 2 (Semantic)** - Semantic coherence via pattern matching with `SemanticMerger`

### Performance Achievements:
- 47% chunk reduction (268 to 142 chunks)
- 88% density improvement (1.79 to 3.37 tokens/chunk)
- Linguistically grounded and interpretable

### Code Quality Achievements:
- 75% reduction in main.py (507 to 127 lines)
- SOLID principles throughout (Strategy, Facade, Factory patterns)
- Extensible: Add new chunkers/rules without modifying existing code
- Maintainable: Each component has single, clear responsibility
- Testable: System integration tests validate end-to-end functionality

### Use Cases:
- Text preprocessing for NLP pipelines
- Information extraction systems
- Semantic search and retrieval
- Machine translation preprocessing
- Linguistic corpus analysis

### For Developers:
This codebase serves as an **excellent example** of how to apply OOP and SOLID principles to improve a procedural codebase without over-engineering. See [OOP Refactoring Benefits](#oop-refactoring-benefits) for detailed analysis.

**Key lesson**: OOP is a tool, not a goal. Use it when it simplifies, avoid it when it complicates.

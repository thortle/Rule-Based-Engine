# Rule-Based French Text Chunker

A two-level linguistic chunking system using Universal Dependencies and semantic rules.

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![Stanza](https://img.shields.io/badge/stanza-1.11.0-green.svg)](https://stanfordnlp.github.io/stanza/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Branches

| Branch | Purpose |
|--------|---------|
| `procedural-branch` | Original procedural implementation |
| `main` | OOP/SOLID refactoring (this branch) |

The `main` branch is a refactoring of the procedural version to apply object-oriented design and SOLID principles. Both branches produce identical output; only the architecture differs.

---

## What It Does

This system segments French text into meaningful linguistic units (chunks) using a two-level approach:

**Level 1 (Syntactic):** Uses Universal Dependencies parsing to create fine-grained grammatical chunks based on dependency relations.

**Level 2 (Semantic):** Applies pattern-matching rules to merge related chunks into larger meaningful units (temporal expressions, named entities, verb phrases).

```
Input:  "Il est 18 h 30 ce lundi 27 janvier quand Jean-Noël C. est admis aux urgences."

Level 1: [Il] [est] [18] [h] [30] [ce] [lundi] [27] [janvier] [quand] [Jean-Noël C.] [est admis] [aux urgences]

Level 2: [Il est] [18 h 30 ce lundi 27 janvier] [quand] [Jean-Noël C. est admis aux urgences]
```

---

## Current State

The system is functional and produces correct output. The semantic rules have not been extensively fine-tuned for all edge cases, but the architecture supports easy rule adjustment via the JSON configuration. The test corpus (`data/gorafi_medical.txt`) is included so anyone can run the pipeline and verify results.

---

## Installation

```bash
git clone https://github.com/thortle/Rule-Based-Engine.git
cd Rule-Based-Engine
python3 -m venv venv && source venv/bin/activate
pip install stanza
python -c "import stanza; stanza.download('fr')"
```

---

## Usage

```bash
source venv/bin/activate
python scripts/main.py --multi-pass
```

Output files are saved to `data/output/`.

---

## How It Works

### Level 1: UD-Based Chunking

The chunker uses Stanza to parse text into Universal Dependencies format, then groups tokens into phrases based on dependency relations. Tokens connected by phrase-internal relations (determiners, modifiers, auxiliaries) are merged into single chunks.

For example, in "le chat noir", the tokens share phrase-internal relations and form one nominal chunk rather than three separate units.

### Level 2: Semantic Merging

The merger applies rules from `lang_fr/semantic_rules.json` to combine adjacent chunks. Each rule specifies:
- A pattern of chunk categories to match (e.g., `["SujV", "SV"]`)
- A result category for the merged chunk
- A condition that must be satisfied

Rules are applied iteratively until no more merges are possible.

---

## Project Structure

```
Rule-Based-Engine/
├── src/
│   ├── models.py          # Data structures: Token, Chunk, Sentence
│   ├── chunkers.py        # Chunker abstract class + UDChunker
│   ├── pipeline.py        # ChunkerPipeline facade
│   └── rules/
│       ├── base.py        # SemanticRule abstract class
│       ├── complex_rules.py
│       ├── merger.py      # SemanticMerger orchestrator
│       └── factory.py     # Rule creation from JSON
├── scripts/main.py        # CLI entry point
├── config/config.json     # Pipeline configuration
├── lang_fr/semantic_rules.json  # French merging rules (19 rules)
├── data/
│   ├── gorafi_medical.txt       # Test corpus
│   └── output/                  # Generated results
└── tests/test_system.py
```

---

## OOP Principles Applied

### Encapsulation

Data and behavior are bundled together, hiding implementation details.

**Token** stores linguistic annotations and exposes a `base_deprel` property that extracts the base relation from subtypes (e.g., `"nsubj:pass"` becomes `"nsubj"`). Callers use the property without knowing about the string manipulation.

```python
@dataclass(frozen=True)
class Token:
    id: int
    text: str
    deprel: str
    # ...
    
    @property
    def base_deprel(self) -> str:
        return self.deprel.split(':')[0]
```

**Chunk** automatically sorts tokens by position and computes text on demand:

```python
class Chunk:
    def __init__(self, category: str, tokens: List[Token]):
        self.tokens = sorted(tokens, key=lambda t: t.id)
    
    @property
    def text(self) -> str:
        return ' '.join(t.text for t in self.tokens)
```

### Inheritance

Abstract base classes define contracts that concrete classes must follow.

**Chunker hierarchy:** `Chunker` (abstract) defines the `chunk_sentence()` interface. `UDChunker` implements it using Universal Dependencies.

```python
class Chunker(ABC):
    @abstractmethod
    def chunk_sentence(self, sentence: Sentence) -> List[Chunk]:
        pass

class UDChunker(Chunker):
    def chunk_sentence(self, sentence: Sentence) -> List[Chunk]:
        # UD-based implementation
```

**SemanticRule hierarchy:** 19 rule classes inherit from `SemanticRule` and implement `check_condition()` with their specific logic.

### Polymorphism

The same interface works with different implementations.

`SemanticMerger` holds a list of `SemanticRule` objects and calls `check_condition()` on each without knowing which concrete rule class it is:

```python
class SemanticMerger:
    def __init__(self, rules: List[SemanticRule]):
        self.rules = rules
    
    def merge(self, chunks):
        for rule in self.rules:
            if rule.check_condition(chunks, i):  # Works for any rule type
                merged = rule.apply(chunks, i)
```

This replaced a 150-line `if/elif` chain in the procedural version.

---

## SOLID Principles Applied

| Principle | Application |
|-----------|-------------|
| **Single Responsibility** | Each class has one job. `Token` stores data, `UDChunker` creates chunks, `SemanticMerger` applies rules. |
| **Open/Closed** | Add new chunkers or rules by creating subclasses, not modifying existing code. |
| **Liskov Substitution** | Any `Chunker` subclass works wherever `Chunker` is expected. |
| **Interface Segregation** | `Chunker` has one method: `chunk_sentence()`. |
| **Dependency Inversion** | `ChunkerPipeline` depends on `Chunker` abstraction, not `UDChunker` concrete class. |

---

## Adding New Languages

The rule logic is language-agnostic. To add English support:

1. Create `lang_en/semantic_rules.json` with English patterns
2. Update `config/config.json` to point to the new rules file
3. Download the Stanza English model: `stanza.download('en')`

No Python code changes required.

---

## Testing

```bash
python tests/test_system.py
```

The tests verify that Level 1 produces 268 chunks and Level 2 (multi-pass) reduces them to 142 on the included test corpus.

---

## References

- [Universal Dependencies](https://universaldependencies.org/)
- [Stanza NLP](https://stanfordnlp.github.io/stanza/)

---

## License

MIT License - See LICENSE file.

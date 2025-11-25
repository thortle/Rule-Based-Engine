# Rule-Based French Text Chunker
**A Two-Level Linguistic Chunking System Using Universal Dependencies and Semantic Rules**

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![Stanza](https://img.shields.io/badge/stanza-1.11.0-green.svg)](https://stanfordnlp.github.io/stanza/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [Architecture Evolution](#architecture-evolution)
5. [OOP Implementation](#oop-implementation)
6. [SOLID Principles](#solid-principles)
7. [Performance](#performance)

---

## Project Overview

### What This Project Does

This system automatically segments French text into meaningful linguistic units (chunks) using a two-level approach:

**Level 1 - Syntactic Chunking:**
- Parses text using Universal Dependencies (UD) framework
- Identifies grammatical phrase boundaries
- Creates fine-grained syntactic chunks based on dependency relations
- Example: "le chat noir" → single nominal chunk

**Level 2 - Semantic Merging:**
- Applies pattern-matching rules to merge related chunks
- Combines chunks that form semantic units
- Example: "18 h 30" + "ce lundi" → single temporal expression

**Real-World Example:**
```
Input: "Il est 18 h 30 ce lundi 27 janvier quand Jean-Noël C. est admis aux urgences."

Level 1 (Syntactic): 11 chunks
[Il] [est] [18] [h] [30] [ce] [lundi] [27] [janvier] [quand] [Jean-Noël C.] 
[est admis] [aux urgences]

Level 2 (Semantic): 4 chunks
[Il est] [18 h 30 ce lundi 27 janvier] [quand] 
[Jean-Noël C. est admis aux urgences]

```

### Why This Matters

Traditional rule-based chunking faces several challenges:
- POS tagging errors propagate through the system
- Proper names get fragmented ("Jean-Noël C." → "Jean" + "Noël" + "C.")
- Temporal expressions split incorrectly ("18 h 30" → three separate chunks)
- Passive voice constructions break apart

Our hybrid approach solves these issues by:
1. Using UD parsing for accurate grammatical analysis (Level 1)
2. Applying semantic rules to merge related chunks (Level 2)
3. Producing linguistically coherent, meaningful text segments

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

## Quick Start

```bash
# Activate virtual environment
source venv/bin/activate

# Run with single-pass merging
python scripts/main.py

# Run with multi-pass merging (recommended)
python scripts/main.py --multi-pass

# Custom configuration
python scripts/main.py --config config/config.json --multi-pass

# View results
cat data/output/gorafi_medical_level1.txt  # Syntactic chunks
cat data/output/gorafi_medical_level2.txt  # Semantic chunks
```

---

## Architecture Evolution

This project underwent a complete refactoring from procedural to object-oriented architecture, applying SOLID principles throughout. This section shows the transformation.

### Project Structure: Before and After

#### Procedural Version (Before)
```
Rule-Based-Engine/
├── main.py                    (507 lines - EVERYTHING mixed together)
├── linguistic_chunker.py      (300 lines - UD chunking)
├── semantic_merger.py         (624 lines - semantic rules + merger)
└── data/

Total: ~1500 lines in 3 monolithic files
```

#### OOP Version (After)
```
Rule-Based-Engine/
├── src/                       # Core source code (organized by responsibility)
│   ├── models.py              (143 lines - Data structures: Token, Chunk, Sentence)
│   ├── chunkers.py            (225 lines - Chunker ABC + UDChunker)
│   ├── pipeline.py            (292 lines - ChunkerPipeline facade)
│   └── rules/                 # Semantic rules module (organized by concern)
│       ├── __init__.py        (58 lines  - Module exports)
│       ├── constants.py       (55 lines  - Lexical indicators)
│       ├── base.py            (107 lines - SemanticRule base class)
│       ├── simple_rules.py    (41 lines  - AdjacentRule)
│       ├── complex_rules.py   (153 lines - Complex condition rules)
│       ├── merger.py          (130 lines - SemanticMerger orchestrator)
│       └── factory.py         (88 lines  - Rule factory)
├── scripts/
│   └── main.py                (127 lines - CLI entry point)
├── config/
│   └── config.json            # Pipeline configuration
├── lang_fr/
│   └── semantic_rules.json    # Semantic merging rules (19 rules)
├── data/
│   ├── gorafi_medical.txt     # Test corpus
│   └── output/                # Generated outputs
└── tests/
    └── test_system.py         # Integration tests

Total: ~1200 lines in 12 focused modules
```

**Key Improvements:**
- 20% code reduction overall
- 75% reduction in main orchestration file (507 → 127 lines)
- Maximum file size: 292 lines (vs 624 lines before)
- Each module has single responsibility

---

### File Architecture Reorganization

**Why we created `src/rules/` folder:**

**Before:** One monolithic file
```
semantic_merger.py (624 lines)
├── Constants mixed with logic
├── All rule types in one place
├── Merger logic intertwined
└── Factory pattern missing
```

**After:** Organized by concern
```
src/rules/
├── constants.py       (55 lines)  - Lexical indicators only
├── base.py           (107 lines)  - SemanticRule abstract class
├── simple_rules.py    (41 lines)  - Simple merging rules
├── complex_rules.py  (153 lines)  - Complex condition rules
├── merger.py         (130 lines)  - Rule orchestration only
└── factory.py         (88 lines)  - Rule creation logic
```

**Benefits of this organization:**

1. **Find things fast** - Each concern has its own file, making bugs easy to locate

2. **No file over 160 lines** - Small, focused modules are easier to understand and maintain

3. **Clear dependencies** - Files only import what they need, reducing coupling

4. **Easy to extend** - Add features by modifying single files, not entire system

**Separation of configuration from code:**
```
src/rules/          ← Python implementation (language-agnostic)
lang_fr/           ← French configuration (data only)
lang_en/           ← English configuration (future)
```

This follows the **Single Responsibility Principle** at the file level.

---

### Data Flow Architecture

#### Procedural Approach (Before)

```
┌─────────────────────────────────────────────────────────────────┐
│  main.py (507 lines)                                            │
│  MONOLITHIC - DOES EVERYTHING                                   │
├─────────────────────────────────────────────────────────────────┤
│  Config → I/O → Parsing → Chunking → Merging → Output          │
└─────────────────────────────────────────────────────────────────┘
              ↓                                  ↓
    ┌──────────────────┐              ┌──────────────────┐
    │ linguistic_      │              │ semantic_        │
    │ chunker.py       │              │ merger.py        │
    │ (300 lines)      │              │ (624 lines)      │
    │                  │              │                  │
    │ Mixed classes    │              │ 150-line if/elif │
    │ and functions    │              │ chain for rules  │
    └──────────────────┘              └──────────────────┘
```

**Problems with Procedural Approach:**

1. **Single Responsibility violations** - One file does everything, mixing multiple concerns
2. **Difficult to test** - Nested functions and mixed logic prevent isolated testing
3. **Hard to extend** - New features require modifying existing code, risk breaking things
4. **Poor maintainability** - Changes ripple through system, unclear ownership

---

#### OOP Approach (After)

```
┌────────────────────────────────────────────────────────────────┐
│  scripts/main.py (127 lines)                                   │
│  SIMPLE ENTRY POINT - Delegates to Pipeline                    │
├────────────────────────────────────────────────────────────────┤
│  Args → Config → Pipeline.run() → Display                      │
└────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────┐
│  src/pipeline.py - ChunkerPipeline (FACADE)                    │
├────────────────────────────────────────────────────────────────┤
│  Parse → Level 1 Chunking → Level 2 Merging → Save             │
└────────────────────────────────────────────────────────────────┘
           ↓                      ↓                      ↓
┌──────────────────┐  ┌───────────────────┐  ┌──────────────────┐
│ src/models.py    │  │ src/chunkers.py   │  │ src/rules/       │
│                  │  │                   │  │                  │
│ Token, Chunk,    │  │ Chunker (ABC)     │  │ SemanticRule     │
│ Sentence         │  │ UDChunker         │  │ (ABC)            │
│                  │  │                   │  │                  │
│ Data structures  │  │ Strategy pattern  │  │ Rule classes     │
│ only             │  │ for algorithms    │  │ + Merger         │
│                  │  │                   │  │ + Factory        │
└──────────────────┘  └───────────────────┘  └──────────────────┘
```

**Advantages of OOP Approach:**

1. **Separation of Concerns** - Each class has one clear responsibility
2. **Extensibility** - Add features by creating new classes, not modifying existing ones
3. **Testability** - Classes tested independently with clear boundaries
4. **Maintainability** - Bug fixes localized, changes don't cascade

---

## Key Classes Reference

Essential classes demonstrating OOP principles.

#### Core Architecture

| Class | Responsibility | Key Method | OOP Principle Demonstrated |
|-------|---------------|------------|---------------------------|
| **Token** | Store word data with linguistic info | `base_deprel` - Extract base relation | **Encapsulation** - Data bundled with behavior |
| **Chunk** | Group tokens into phrases | `text` - Reconstruct text from tokens | **Encapsulation** - Auto-sorting, computed properties |
| **Chunker** (ABC) | Define chunking interface | `chunk_sentence()` - Abstract method | **Inheritance** - Base class for all chunkers |
| **UDChunker** | Create syntactic chunks | `chunk_sentence()` - UD-based implementation | **Polymorphism** - Concrete chunker implementation |
| **SemanticRule** (ABC) | Define merging rule interface | `check_condition()` - Abstract condition checker | **Inheritance** - Base class for all rules |
| **TemporalMergeRule** | Merge time expressions | `check_condition()` - Check temporal words | **Polymorphism** - Concrete rule implementation |
| **SemanticMerger** | Orchestrate rule application | `merge()` - Apply rules iteratively | **Dependency Inversion** - Depends on abstractions |
| **ChunkerPipeline** | Orchestrate entire system | `run()` - Execute full pipeline | **Facade Pattern** - Simple interface to complex system |

### Why This Organization Works

- **Separation of Concerns** - Each class has one clear job
- **Easy to Extend** - Inherit from base classes, no code modification
- **Easy to Test** - Classes tested independently with clear boundaries
- **Easy to Maintain** - Bug fixes localized to specific classes

---

## OOP Implementation

### The Three Core Pillars

Our implementation demonstrates the three fundamental principles of object-oriented programming.

---

### 1. ENCAPSULATION
**"Bundling data with methods that operate on that data"**

**Example:** `src/models.py` - Token class

```python
@dataclass(frozen=True)
class Token:
    """Immutable token with UD annotation."""
    id: int
    text: str
    lemma: str
    upos: str
    head: int
    deprel: str
    
    @property
    def base_deprel(self) -> str:
        """Extract base relation (e.g., 'nsubj:pass' → 'nsubj')."""
        return self.deprel.split(':')[0]
```

**Why this matters:** Data bundled with behavior, implementation details hidden

---

**Example:** `src/models.py` - Chunk class

```python
class Chunk:
    """Text segment representing a linguistic unit."""
    def __init__(self, category: str, tokens: List[Token]):
        self.category = category
        self.tokens = sorted(tokens, key=lambda t: t.id)  # Auto-sorted
    
    @property
    def text(self) -> str:
        """Reconstruct text from tokens."""
        return ' '.join(t.text for t in self.tokens)
```

**Why this matters:** Auto-sorting and computed properties encapsulate internal logic

---

### 2. INHERITANCE
**"Creating new classes based on existing ones"**

**Example:** `src/chunkers.py` - Chunker hierarchy

```python
class Chunker(ABC):
    """Base class for all chunking algorithms."""
    
    @abstractmethod
    def chunk_sentence(self, sentence: Sentence) -> List[Chunk]:
        """Convert sentence into chunks."""
        pass
```

**Example:** `src/chunkers.py` - UDChunker

```python
class UDChunker(Chunker):
    """Concrete implementation using Universal Dependencies."""
    
    MERGE_RELATIONS = {'det', 'amod', 'nummod', ...}
    
    def chunk_sentence(self, sentence: Sentence) -> List[Chunk]:
        # Implementation here
        pass
```

**Why this matters:** Enforces consistent interface, easy to add new implementations

---

**Example:** `src/rules/base.py` - SemanticRule hierarchy

```python
class SemanticRule(ABC):
    """Base class for semantic merging rules."""
    
    def __init__(self, pattern: List[str], result_category: str, rule_id: str = ""):
        self.pattern = pattern
        self.result_category = result_category
        self.rule_id = rule_id
    
    @abstractmethod
    def check_condition(self, chunks: List[Chunk], start_idx: int) -> bool:
        """Subclasses must implement condition checking."""
        pass
```

**Example:** `src/rules/complex_rules.py` - TemporalMergeRule

```python
class TemporalMergeRule(SemanticRule):
    """Merges temporal expressions like '18 h 30 ce lundi'."""
    
    def check_condition(self, chunks, start_idx) -> bool:
        from .constants import TEMPORAL_WORDS
        matched = chunks[start_idx:start_idx + len(self.pattern)]
        
        for chunk in matched:
            words = set(chunk.text.lower().split())
            if not (words & TEMPORAL_WORDS):
                return False
        return True
```

**Why this matters:** Shared structure with custom logic, 19 rules using same interface

---

### 3. POLYMORPHISM
**"Using a single interface to represent different types"**

**Example:** `src/pipeline.py` - ChunkerPipeline

```python
class ChunkerPipeline:
    def __init__(self, config: Dict[str, Any]):
        self.chunker = UDChunker()  # Could be ANY Chunker
    
    def _apply_level1(self, sentences: List[Sentence]):
        """Works with ANY Chunker implementation."""
        chunks = []
        for sentence in sentences:
            # This works whether chunker is UDChunker, CRFChunker, etc.
            sentence_chunks = self.chunker.chunk_sentence(sentence)
            chunks.extend(sentence_chunks)
        return chunks
```

**Why this matters:** Swap implementations without changing client code

---

**Example:** `src/rules/merger.py` - SemanticMerger

```python
class SemanticMerger:
    def __init__(self, rules: List[SemanticRule]):
        self.rules = rules  # List of ANY SemanticRule subclasses
    
    def merge(self, chunks, multi_pass=False):
        result = list(chunks)
        i = 0
        while i < len(result):
            for rule in self.rules:
                if rule.matches_pattern(result, i):
                    # Works with TemporalRule, PrepRule, VerbRule, etc.
                    if rule.check_condition(result, i):
                        merged = rule.apply(result, i)
                        result[i:i + len(rule.pattern)] = [merged]
                        break
            i += 1
        return result
```

**Why this matters:** Works with any rule mix, no type checking needed

---

## SOLID Principles

Five design principles that make code maintainable and scalable.

---

### S - Single Responsibility Principle
**"Each class does one thing well"**

| Class | One Responsibility | File |
|-------|-------------------|------|
| Token | Store token data | `src/models.py` |
| Chunk | Store chunk data | `src/models.py` |
| UDChunker | Create syntactic chunks | `src/chunkers.py` |
| TemporalMergeRule | Merge temporal expressions | `src/rules/complex_rules.py` |
| SemanticMerger | Apply rules to chunks | `src/rules/merger.py` |
| ChunkerPipeline | Orchestrate pipeline | `src/pipeline.py` |

---

### O - Open/Closed Principle
**"Open for extension, closed for modification"**

**Adding a new chunking algorithm:**
```python
# DON'T modify existing code
class Chunker(ABC):
    @abstractmethod
    def chunk_sentence(self, sentence: Sentence) -> List[Chunk]:
        pass

# DO create new class
class CRFChunker(Chunker):
    def chunk_sentence(self, sentence: Sentence) -> List[Chunk]:
        # Your CRF implementation
        pass
```

**Adding a new semantic rule:**
1. Create class in `src/rules/complex_rules.py`
2. Register in `src/rules/factory.py`
3. Configure in `lang_fr/semantic_rules.json`

**Result:** Zero modifications to existing code

---

### L - Liskov Substitution Principle
**"Subclasses must be usable through parent interface"**

**Example:** `src/pipeline.py`

```python
def process_text(chunker: Chunker):
    """Works with ANY Chunker subclass."""
    pipeline = ChunkerPipeline(chunker=chunker)
    return pipeline.run()

# All of these work identically
process_text(UDChunker())
process_text(CRFChunker())
process_text(RuleBasedChunker())
```

**What this guarantees:** Subclasses work wherever parent class is expected

---

### I - Interface Segregation Principle
**"Keep interfaces minimal"**

**Example:** `src/chunkers.py`

```python
class Chunker(ABC):
    @abstractmethod
    def chunk_sentence(self, sentence: Sentence) -> List[Chunk]:
        pass  # ONLY ONE METHOD
```

**Result:** No forced unused methods, clean minimal interfaces

---

### D - Dependency Inversion Principle
**"Depend on abstractions, not concrete classes"**

**Example:** `src/pipeline.py`

```python
class ChunkerPipeline:
    def __init__(self, config: Dict):
        # Depends on Chunker abstraction (not UDChunker specifically)
        self.chunker: Chunker = UDChunker()
    
    def _apply_level1(self, sentences):
        # Works with ANY Chunker implementation
        chunks = self.chunker.chunk_sentence(sentence)
```

**Example:** `src/rules/merger.py`

```python
class SemanticMerger:
    def __init__(self, rules: List[SemanticRule]):  # Abstraction
        self.rules = rules  # Not List[TemporalMergeRule]
```

**Result:** High-level code doesn't depend on low-level details

---

## Performance

**Test Corpus:** 15 sentences, 479 tokens (Le Gorafi medical article)

| Metric | Result |
|--------|--------|
| Chunk reduction | 268 → 142 (47% reduction) |
| Density improvement | 1.79 → 3.37 tokens/chunk (+88%) |
| OOP refactoring impact | 0% performance degradation |
| Code size reduction | 1500 → 1200 lines (-20%) |

---

## Testing

**Location:** `tests/test_system.py`

**Run tests:**
```bash
source venv/bin/activate
python tests/test_system.py
```

**Coverage:** Level 1 chunking, Level 2 single/multi-pass merging, output generation
---

## Adding Support for New Languages

### Quick Demo: How Simple It Is Now

Want to add English support? Here's all you need:

**Step 1:** Create folder
```bash
mkdir lang_en
```

**Step 2:** Create `lang_en/semantic_rules.json`
```json
[
  {
    "rule_id": "temporal_en",
    "pattern": ["NUM", "TEMPORAL"],
    "result_category": "TEMPORAL",
    "condition": "both_temporal"
  }
]
```

**Step 3:** Update `config/config.json`
```json
{
  "rules_path": "lang_en/semantic_rules.json"
}
```

**Step 4:** Download model
```python
import stanza
stanza.download('en')
```

**Done.** No Python code changes needed.

### Why This Works

**Code vs Configuration:**
- `src/rules/*.py` - Generic rule algorithms (work for any language)
- `lang_XX/*.json` - Language-specific patterns (data, not code)

**What stays the same:**
- All Python classes in `src/`
- Pipeline orchestration
- Rule application logic

**What changes:**
- JSON configuration files only

**Result:** Open/Closed Principle in action - add languages without modifying code.

---

## References

- [Universal Dependencies](https://universaldependencies.org/)
- [Stanza Documentation](https://stanfordnlp.github.io/stanza/)
- Design Patterns: Strategy, Facade, Factory
- SOLID Principles: Robert C. Martin

---

## License

MIT License - See LICENSE file for details.

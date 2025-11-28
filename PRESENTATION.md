# Project Presentation – Rule-Based French Text Chunker

---

## Slide 1 – Title & Context

- **Title:** Refactoring a Rule-Based French Text Chunker with OOP & SOLID
- **Goal:** Take an older procedural system and reorganize it using
  object-oriented design and SOLID principles **without losing performance**.
- **Scope:**
  - More scalable
  - Easier to maintain and debug
  - Easier to read and extend

**Talking points:**
- Original code was working, but hard to evolve.
- Constraint: keep the same behaviour and performance, only change
  the architecture.

---

## Slide 2 – What the Chunker Does (Two-Level Architecture)

- **Goal:** Automatically segment French text into meaningful linguistic
  units ("chunks").

- **Level 1 – Syntactic Chunking (UD-based):**
  - Uses Universal Dependencies parsing
  - Produces fine-grained grammatical chunks

- **Level 2 – Semantic Merging (Rule-based):**
  - Applies pattern-matching rules
  - Merges chunks into larger meaningful units (temporal, named entities…)

```
┌──────────────────────────────────────────────────────────────────────┐
│  Input Text                                                          │
│  "Il est 18 h 30 ce lundi 27 janvier quand Jean-Noël C. est admis…"  │
└──────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
                 ┌──────────────────────────┐
                 │  Level 1: UD Chunker     │
                 │  (Syntactic)             │
                 └──────────────────────────┘
                                │
                                ▼
       [Il] [est] [18] [h] [30] [ce] [lundi] ... (11 chunks)
                                │
                                ▼
                 ┌──────────────────────────┐
                 │  Level 2: Semantic       │
                 │  Merger (Rule-based)     │
                 └──────────────────────────┘
                                │
                                ▼
       [Il est] [18 h 30 ce lundi 27 janvier] [quand] ... (4 chunks)
```

**Talking points:**
- Level 1 is grammar-oriented (dependency relations).
- Level 2 is meaning-oriented (merge related chunks).
- Result: fewer, denser, more interpretable segments.

---

## Slide 3 – Procedural Architecture (Before) – UML Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                   main.py  (507 lines)                              │
│           ORCHESTRATOR – Controls everything, mixed logic           │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌───────┐  │
│  │ Config  │ → │  I/O    │ → │ Parsing │ → │Chunking │ → │Merging│  │
│  │ loading │   │ read/   │   │ (calls  │   │ (calls  │   │(calls │  │
│  │         │   │ write   │   │ Stanza) │   │ ling.   │   │sem.   │  │
│  │         │   │ files   │   │         │   │ chunker)│   │merger)│  │
│  └─────────┘   └─────────┘   └─────────┘   └─────────┘   └───────┘  │
│                                                               │     │
│                                                               ▼     │
│                                                          [ Output ] │
└─────────────────────────────────────────────────────────────────────┘
          │                                        │
          ▼                                        ▼
┌─────────────────────────┐          ┌─────────────────────────────────┐
│ linguistic_chunker.py   │          │ semantic_merger.py (624 lines)  │
│ (300 lines)             │          │                                 │
│                         │          │  ┌───────────────────────────┐  │
│  Contains:              │          │  │ 150-line if/elif chain    │  │
│  - UD chunking          │          │  │ to select which rule      │  │
│    algorithm            │          │  │ applies to chunks         │  │
│  - Helper functions     │          │  └───────────────────────────┘  │
│  - Some classes         │          │  - Constants mixed with logic   │
│                         │          │  - All 19 rule types here       │
│  Called BY main.py      │          │  Called BY main.py              │
└─────────────────────────┘          └─────────────────────────────────┘
```

**What each file does:**
- **`main.py`** = Does everything: loads config, reads files, calls chunker, calls merger, saves output (all mixed together)
- **`linguistic_chunker.py`** = Contains the chunking algorithm (called by main to do Level 1 work)
- **`semantic_merger.py`** = Contains the merging rules (called by main to do Level 2 work)

**File layout:**
```
Rule-Based-Engine/
├── main.py               (507 lines – orchestration + I/O + config)
├── linguistic_chunker.py (300 lines – UD chunking algorithm)
├── semantic_merger.py    (624 lines – all rules + merger logic)
└── data/

Total: ~1500 lines in 3 monolithic files
```

**Limitations:**
- **Single Responsibility violated** – main.py does too many things
- **Tight coupling** – main.py must know about chunker AND merger internals
- **Hard to extend** – adding a rule means editing semantic_merger.py AND main.py
- **Hard to test** – can't test components independently
- **Hard to debug** – changes ripple through multiple files

**Talking points:**
- Explain: main.py is the "boss" that controls everything, but also does config loading, I/O, etc.
- linguistic_chunker and semantic_merger are "workers" called by main.py
- Problem: responsibilities are mixed - the boss does too much
- Point out the 150-line `if/elif` chain in `semantic_merger.py` for rule selection
- Conclude: it worked, but couldn't scale or evolve safely

---

## Slide 4 – OOP Architecture (After) – UML Data Flow

```
┌───────────────────────────────────────────────────────────────────┐
│                   scripts/main.py  (127 lines)                    │
│              THIN ENTRY POINT – Only handles CLI                  │
├───────────────────────────────────────────────────────────────────┤
│    Parse args  →  Load config  →  pipeline.run()  →  Display      │
│                                                                   │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌───────────────────────────────────────────────────────────────────┐
│       src/pipeline.py – ChunkerPipeline (FACADE PATTERN)          │
│                                                                   │
│  The "conductor" – coordinates all modules:                       │
├───────────────────────────────────────────────────────────────────┤
│  1. Parse text (Stanza)                                           │
│  2. Level 1: Call chunker.chunk_sentence()                        │
│  3. Level 2: Call merger.merge()                                  │
│  4. Save output files                                             │
└───────────────────────────────────────────────────────────────────┘
         │                │                     │
         ▼                ▼                     ▼
┌─────────────────┐ ┌─────────────────┐ ┌──────────────────────────┐
│  src/models.py  │ │ src/chunkers.py │ │      src/rules/          │
│                 │ │                 │ │                          │
│  Data holders:  │ │  Chunking:      │ │  Rule system:            │
│  - Token        │ │  - «ABC»        │ │  - «ABC»                 │
│  - Chunk        │ │    Chunker      │ │    SemanticRule          │
│  - Sentence     │ │         ▲       │ │         ▲                │
│                 │ │         │       │ │         │                │
│  (no logic,     │ │  - UDChunker    │ │  - TemporalMergeRule     │
│   just data)    │ │                 │ │  - PrepMergeRule         │
│                 │ │  Does Level 1   │ │  - VerbMergeRule ...     │
│                 │ │                 │ │                          │
│                 │ │                 │ │  - SemanticMerger        │
│                 │ │                 │ │    (applies rules)       │
│                 │ │                 │ │  - RuleFactory           │
│                 │ │                 │ │    (creates rules)       │
└─────────────────┘ └─────────────────┘ └──────────────────────────┘
                                         ▲
                                         │
                                         │ reads rule patterns from
                                         │
                          ┌──────────────────────────────┐
                          │ lang_fr/semantic_rules.json  │
                          │ (configuration data)         │
                          └──────────────────────────────┘
```

**What each module does:**
- **`scripts/main.py`** = Entry point only: parse CLI args, load config, call `pipeline.run()`
- **`ChunkerPipeline`** = **FACADE PATTERN** - has ONE method: `run()`
  - Simple interface from outside: just call `run()`
  - Behind the scenes, `run()` delegates to:
    1. Parsing (Stanza library)
    2. Level 1 chunking (UDChunker class)
    3. Level 2 merging (SemanticMerger class)
    4. Saving output files (I/O operations)
- **`models.py`** = Data structures (Token, Chunk, Sentence) - no algorithms
- **`chunkers.py`** = Chunking algorithms (abstract Chunker + concrete UDChunker)
- **`rules/`** = Everything about semantic rules:
  - Rule classes (TemporalMergeRule, PrepMergeRule...)
  - SemanticMerger (applies rules to chunks)
  - RuleFactory (creates rule objects from JSON config)

**Config files:**
- **`config/config.json`** = System settings (input path, output path, which language)
- **`lang_fr/semantic_rules.json`** = French rule patterns (data, not code)

**New file layout:**
```
Rule-Based-Engine/
├── src/                        # Business logic (organized by responsibility)
│   ├── models.py               # Data structures
│   ├── chunkers.py             # Chunking algorithms
│   ├── pipeline.py             # Facade (orchestrator)
│   └── rules/                  # Rule system (organized module)
│       ├── base.py             # SemanticRule ABC
│       ├── simple_rules.py     # Simple rules
│       ├── complex_rules.py    # Complex condition rules
│       ├── merger.py           # SemanticMerger
│       ├── factory.py          # RuleFactory
│       └── constants.py        # Lexical indicators
├── scripts/main.py             # CLI entry point (thin)
├── config/config.json          # System configuration
├── lang_fr/semantic_rules.json # French rules (data)
└── tests/test_system.py        # Tests
```

**Key improvements vs procedural:**
- **Clear separation:** Entry point (`main.py`) → Facade(`ChunkerPipeline.run()`) → Specialized modules (`UDChunker.chunk_sentence()` / `SemanticMerger.merge()`)
- **Single responsibility:** Each class/module has ONE job
- **Loose coupling:** Classes communicate through abstract interfaces (`Chunker`, `SemanticRule`)
- **Easy to test:** Each class can be tested independently
- **Easy to extend:** Add new `Chunker` subclass or `SemanticRule` subclass without touching existing code

**Talking points:**
- Explain the **facade pattern**: 
  - ChunkerPipeline has ONE simple method: `run()`
  - Like a restaurant waiter - you give ONE order ("Menu #3"), they coordinate kitchen/wine/service behind the scenes
  - You don't call the kitchen directly, the wine cellar directly, etc. - just the waiter
- In our case: `main.py` just calls `pipeline.run()`, doesn't need to know about parsing, chunking, merging details
- Behind `run()`, the facade delegates: parsing → chunking → merging → saving
- Contrast with procedural: main.py had to manually call each step and coordinate them itself
- Highlight: config is separate from code (data vs logic)
- Emphasize: same work gets done, but responsibilities are clearly split

---

## Slide 5 – Encapsulation: Token & Chunk

**Concept:** Data + behaviour bundled together; internal details hidden.

**Example 1 – `Token`** (`src/models.py`):
```python
@dataclass(frozen=True)
class Token:
    id: int
    text: str
    lemma: str
    upos: str
    head: int
    deprel: str

    @property
    def base_deprel(self) -> str:
        return self.deprel.split(':')[0]
```

**Example 2 – `Chunk`** (`src/models.py`):
```python
class Chunk:
    def __init__(self, category: str, tokens: List[Token]):
        self.category = category
        self.tokens = sorted(tokens, key=lambda t: t.id)  # auto-sorted

    @property
    def text(self) -> str:
        return ' '.join(t.text for t in self.tokens)
```

**Talking points:**
- `Token.base_deprel` property hides the string-splitting logic (`deprel.split(':')[0]`) inside the class.
- `Chunk.__init__()` auto-sorts tokens; `Chunk.text` property computes text on demand.
- No more helper functions scattered across files.

---

## Slide 6 – Inheritance: Two Parallel Hierarchies

**Concept:** Create new classes based on existing ones; enforce a contract via abstract methods.

**We have two inheritance hierarchies – same pattern, different domains:**

| Hierarchy | Parent (ABC) | Abstract Method | Child Example | Purpose |
|-----------|--------------|-----------------|---------------|---------|
| Chunking | `Chunker` | `chunk_sentence()` | `UDChunker` | Level 1 processing |
| Rules | `SemanticRule` | `check_condition()` | `TemporalMergeRule` | Level 2 processing |

**Detailed example – Chunker hierarchy** (`src/chunkers.py`):
```python
# Parent – abstract contract
class Chunker(ABC):
    @abstractmethod
    def chunk_sentence(self, sentence: Sentence) -> List[Chunk]:
        pass

# Child – concrete implementation
class UDChunker(Chunker):
    MERGE_RELATIONS = {"det", "amod", "nummod", ...}

    def chunk_sentence(self, sentence: Sentence) -> List[Chunk]:
        # UD-based implementation
        ...
```

**Same pattern applies to SemanticRule:**
- `SemanticRule` (parent) defines abstract `check_condition()`
- 19 child classes (`TemporalMergeRule`, `PrepMergeRule`, `VerbMergeRule`...) each implement their own `check_condition()` logic

**Talking points:**
- Both hierarchies follow the same pattern: abstract parent defines the contract, concrete children implement it.
- `ChunkerPipeline` calls `self.chunker.chunk_sentence()` – doesn't know which `Chunker` subclass.
- `SemanticMerger` calls `rule.check_condition()` – doesn't know which `SemanticRule` subclass.
- This enables polymorphism (next slide).

---

## Slide 7 – Polymorphism: One Interface, Multiple Implementations

**Concept:** Call the same method on different objects – each behaves according to its own implementation.

**We use polymorphism in two places – same pattern:**

| Caller | Holds | Calls | Could be any... |
|--------|-------|-------|-----------------|
| `ChunkerPipeline` | `self.chunker: Chunker` | `chunk_sentence()` | `UDChunker`, `CRFChunker`, ... |
| `SemanticMerger` | `self.rules: List[SemanticRule]` | `check_condition()` | `TemporalMergeRule`, `PrepMergeRule`, ... |

**Detailed example – ChunkerPipeline** (`src/pipeline.py`):
```python
class ChunkerPipeline:
    def __init__(self, config: Dict[str, Any]):
        self.chunker = UDChunker()  # could be ANY Chunker subclass

    def _apply_level1(self, sentences: List[Sentence]):
        for sentence in sentences:
            # Same call works for ANY Chunker implementation
            sentence_chunks = self.chunker.chunk_sentence(sentence)
            ...
```

**Same pattern in SemanticMerger:**
```python
# SemanticMerger.merge() iterates and calls rule.check_condition()
# without knowing if rule is TemporalMergeRule, PrepMergeRule, etc.
for rule in self.rules:
    if rule.check_condition(result, i):  # polymorphic call
        ...
```

**Key benefit:** No `if/elif` chains to check types – polymorphism handles dispatch automatically.

**Talking points:**
- Swap `self.chunker = CRFChunker()` – no other code changes needed.
- Add a new rule class – `SemanticMerger` works with it immediately.
- This replaced the 150-line `if/elif` chain from the procedural version.

---

## Slide 8 – SOLID Principles Overview

**All five SOLID principles are demonstrated in our architecture:**

| Principle | How We Apply It |
|-----------|-----------------|
| **S**ingle Responsibility | Each class has ONE job (see table below) |
| **O**pen/Closed | Add new `Chunker` or `SemanticRule` subclass without modifying existing code |
| **L**iskov Substitution | Any `Chunker` subclass works wherever `Chunker` is expected |
| **I**nterface Segregation | `Chunker` has only ONE abstract method: `chunk_sentence()` |
| **D**ependency Inversion | `ChunkerPipeline` depends on `Chunker` (abstraction), not `UDChunker` (concrete) |

**SRP in detail – each class, one job:**

| Class | Responsibility | File |
|-------|----------------|------|
| `Token` | Store token data + `base_deprel` property | `src/models.py` |
| `Chunk` | Store chunk data + `text` property | `src/models.py` |
| `UDChunker` | `chunk_sentence()` – syntactic chunking | `src/chunkers.py` |
| `SemanticMerger` | `merge()` – apply rules to chunks | `src/rules/merger.py` |
| `TemporalMergeRule` | `check_condition()` – temporal logic | `src/rules/complex_rules.py` |
| `ChunkerPipeline` | `run()` – orchestrate the pipeline | `src/pipeline.py` |

**OCP in action – extending without modifying:**
```python
# To add a new chunking algorithm:
# 1. Create new class (don't touch existing code)
class CRFChunker(Chunker):
    def chunk_sentence(self, sentence: Sentence) -> List[Chunk]:
        # CRF-based implementation
        ...

# Same pattern for adding new SemanticRule subclasses
```

**Talking points:**
- SRP: "If we need to change X, we only touch this class/file."
- OCP: We extend by **adding** classes, not modifying existing ones.
- LSP, ISP, DIP: These ensure the abstractions work correctly (subclasses are substitutable, interfaces are minimal, dependencies point to abstractions).

---

## Slide 9 – File & Folder Architecture

**Before – one big file:**
```
semantic_merger.py (624 lines)
├── Constants mixed with logic
├── All rule types in one place
├── Merger logic intertwined
└── No factory pattern
```

**After – organized by concern:**
```
src/rules/
├── constants.py       (55 lines)  – lexical indicators only
├── base.py           (107 lines)  – SemanticRule ABC
├── simple_rules.py    (41 lines)  – simple rules
├── complex_rules.py  (153 lines)  – complex condition rules
├── merger.py         (130 lines)  – orchestration only
└── factory.py         (88 lines)  – rule creation
```

**Separation of code & configuration:**
```
src/rules/        ← Python implementation (language-agnostic)
lang_fr/          ← French configuration (data only)
lang_en/          ← English configuration (future)
```

**Talking points:**
- No file over ~160 lines in `src/rules/`.
- Find things fast, debug easily, extend safely.
- Rule **logic** is generic; rule **patterns** are data (JSON).

---

## Slide 10 – Gains Obtained

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Total lines of code | ~1500 | ~1200 | −20% |
| `main.py` size | 507 lines | 127 lines | −75% |
| Max file size | 624 lines | 292 lines | −53% |
| Largest rule file | 624 lines | 153 lines | −75% |

**Performance (same corpus, same output):**
| Metric | Before | After |
|--------|--------|-------|
| Chunks produced | 268 | 142 (−47%) |
| Tokens per chunk | 1.79 | 3.37 (+88%) |
| OOP overhead | — | **0%** |

**Qualitative gains:**
- Each module has one responsibility
- Easy to locate bugs
- Easy to add features without breaking existing code
- Tests confirm behaviour is unchanged (`tests/test_system.py`)

**Talking points:**
- We achieved all this without sacrificing performance.
- The system is now ready to grow.

---

## Slide 11 – Demo: Adding a New Language

**Goal:** Add English support **without changing Python code**.

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

**Step 4:** Download Stanza model
```python
import stanza
stanza.download('en')
```

**Done.** No changes in `src/`.

**Talking points:**
- This is OCP in action: extend by adding config, not modifying code.
- Demonstrates scalability of the new architecture.

---

## Slide 12 – Conclusion

**What we started with:**
- A procedural, monolithic but functional rule-based engine.

**What we achieved:**
- Clean OOP architecture with clear responsibilities
- SOLID-compliant design (SRP, OCP, LSP, ISP, DIP)
- Organized file structure, no repetition
- Same performance, far more extensible

**Key takeaways:**
- Refactoring architecture improves maintainability **without sacrificing
  performance**.
- OOP and SOLID are not just theory – they directly impact how easy it is
  to evolve real-world systems.

**Talking points:**
- Link back to course objectives.
- Optionally mention future work: new languages, new chunking algorithms,
  new rule types – all using the same architecture.

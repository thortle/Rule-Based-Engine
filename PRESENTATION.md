# Project Presentation – Rule-Based French Text Chunker

## Slide 1 – Title & Context
- **Title:** Refactoring a Rule-Based Text Chunker with OOP & SOLID
- **Goal:** Take an older procedural system and reorganize it using
  object-oriented design and SOLID principles **without losing performance**.
- **Scope:**
  - Make the codebase more scalable
  - Easier to maintain and debug
  - Easier to read and extend

**Talking points:**
- Briefly set the scene: original code was working and reasonably optimized,
  but hard to evolve.
- Emphasize constraint: keep the same behaviour and performance, only change
  the architecture.

---

## Slide 2 – What the Project Does (High Level)
- **Problem:** Automatically segment French text into meaningful linguistic
  units ("chunks").
- **Two-level approach:**
  - **Level 1 – Syntactic chunking** with Universal Dependencies (UD)
  - **Level 2 – Semantic merging** using rule-based patterns
- **Goal:** produce linguistically coherent units like temporal expressions,
  named entities, etc.

**Talking points:**
- Show the **input sentence** and the two levels of output.
- Stress that Level 1 is grammar-oriented, Level 2 is meaning-oriented.

Example:
```text
Input: "Il est 18 h 30 ce lundi 27 janvier quand Jean-Noël C. est admis aux urgences."

Level 1 (Syntactic): 11 chunks
[Il] [est] [18] [h] [30] [ce] [lundi] [27] [janvier] [quand] [Jean-Noël C.]
[est admis] [aux urgences]

Level 2 (Semantic): 4 chunks
[Il est] [18 h 30 ce lundi 27 janvier] [quand]
[Jean-Noël C. est admis aux urgences]
```
---

## Slide 3 – What OOP & SOLID are bringing to the table?
- **Main pain in the procedural version:**
  - One big orchestration file (`main.py` ~500 lines)
  - Monolithic `semantic_merger.py` (~600 lines) mixing rules, constants, and
    control flow
  - Hard to test in isolation, hard to add features safely
- **Solution:**
  - **Encapsulation:** keep linguistic concepts and algorithms self-contained
  - **Inheritance & polymorphism:** share common interfaces
    (chunkers, rules) and plug in new behaviour
  - **SOLID:** reduce coupling, make extension predictable and safe

**Talking points:**
- Phrase it as: "Basically, we changed *how* the responsibilities are distributed."

---

## Slide 4 – Procedural Architecture: Before Refactoring
- **Project layout (before):**
```text
Rule-Based-Engine/
├── main.py              (507 lines – everything mixed together)
├── linguistic_chunker.py (300 lines – UD chunking)
├── semantic_merger.py    (624 lines – semantic rules + merger)
└── data/

Total: ~1500 lines in 3 monolithic files
```
- **Characteristics:**
  - Mixed concerns: I/O, configuration, parsing, chunking, merging
  - Long `if/elif` chains for rule selection
  - Limited separation between domain concepts (Token, Chunk, Rule, Pipeline)

**Talking points:**
- Show how responsibilities were tangled (config, pipeline, rules all in
  `main.py` / `semantic_merger.py`).
- Mention specific pain points: debugging and adding a new rule or language
  meant touching core files.

---

## Slide 5 – OOP Architecture: After Refactoring
- **New layout (after):**
```text
Rule-Based-Engine/
├── src/
│   ├── models.py          – Token, Chunk, Sentence (data structures)
│   ├── chunkers.py        – Chunker ABC + UDChunker
│   ├── pipeline.py        – ChunkerPipeline (facade)
│   └── rules/
│       ├── constants.py   – Lexical indicators
│       ├── base.py        – SemanticRule base class
│       ├── simple_rules.py – Simple merging rules
│       ├── complex_rules.py – Complex condition rules
│       ├── merger.py      – SemanticMerger orchestrator
│       └── factory.py     – Rule factory
├── scripts/main.py        – CLI entry point
├── config/config.json     – Pipeline configuration
├── lang_fr/semantic_rules.json – Language-specific rule config
└── tests/test_system.py   – Integration tests
```
- **Quantitative impact:**
  - Total code: ~1500 → ~1200 lines (−20%)
  - `main.py`: 507 → 127 lines (−75%)
  - Not a single core file is over ~300 lines

**Talking points:**
- Highlight that now each module has **one clear responsibility**.
- This slide prepares for concrete OOP / SOLID examples.

---

## Slide 6 – Data Flow: Before vs After
- **Before:**
```text
main.py (507 lines) – does everything
Config → I/O → Parsing → Chunking → Merging → Output

linguistic_chunker.py – mixed classes and functions
semantic_merger.py – 150-line if/elif chain for rules
```

- **After:**
```text
scripts/main.py – simple entry point
Args → Config → ChunkerPipeline.run() → Display

ChunkerPipeline (src/pipeline.py):
Parse → Level 1 Chunking → Level 2 Merging → Save

Then delegates to:
- src/models.py – Token, Chunk, Sentence
- src/chunkers.py – Chunker (ABC), UDChunker
- src/rules/ – SemanticRule, concrete rules, SemanticMerger, RuleFactory
```

**Talking points:**
- Emphasize the **facade** pattern: high-level pipeline vs low-level modules.
- The same logical steps exist, but the responsibilities are clearly split.

---

## Slide 7 – Key OOP Concepts: Encapsulation (Token & Chunk)
- **Example 1 – `Token` (encapsulating UD annotation):**
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
- **Example 2 – `Chunk` (encapsulating token groups):**
```python
class Chunk:
    def __init__(self, category: str, tokens: List[Token]):
        self.category = category
        self.tokens = sorted(tokens, key=lambda t: t.id)

    @property
    def text(self) -> str:
        return ' '.join(t.text for t in self.tokens)
```

**Talking points:**
- Explain that **data + behaviour** live together: no need for helper
  functions scattered in `main.py`.
- Internal details are hidden (e.g. sorting tokens, stripping UD suffixes).
- This makes unit testing and reuse easier.

---

## Slide 8 – Inheritance: Chunker Hierarchy
- **Parent class – `Chunker` (interface):**
```python
class Chunker(ABC):
    @abstractmethod
    def chunk_sentence(self, sentence: Sentence) -> List[Chunk]:
        pass
```
- **Child class – `UDChunker`:**
```python
class UDChunker(Chunker):
    MERGE_RELATIONS = {"det", "amod", "nummod", ...}

    def chunk_sentence(self, sentence: Sentence) -> List[Chunk]:
        # UD-based implementation
        ...
```

**Talking points:**
- Here is the **parent interface** and a **concrete child**.
- The rest of the code depends on `Chunker`, not `UDChunker`.
- This prepares the ground for polymorphism and the Open/Closed Principle.

---

## Slide 9 – Inheritance: SemanticRule Hierarchy
- **Parent class – `SemanticRule`:**
```python
class SemanticRule(ABC):
    def __init__(self, pattern: List[str], result_category: str, rule_id: str = ""):
        self.pattern = pattern
        self.result_category = result_category
        self.rule_id = rule_id

    @abstractmethod
    def check_condition(self, chunks: List[Chunk], start_idx: int) -> bool:
        pass
```
- **Child class – `TemporalMergeRule`:**
```python
class TemporalMergeRule(SemanticRule):
    def check_condition(self, chunks, start_idx) -> bool:
        from .constants import TEMPORAL_WORDS
        matched = chunks[start_idx:start_idx + len(self.pattern)]
        for chunk in matched:
            words = set(chunk.text.lower().split())
            if not (words & TEMPORAL_WORDS):
                return False
        return True
```

**Talking points:**
- Show again the **parent** and a **specialized child**.
- Mention that there are multiple rule types (temporal, prepositional, etc.)
  all sharing the same interface.

---

## Slide 10 – Polymorphism: Using Chunker Abstraction
- **Polymorphism in `ChunkerPipeline`:**
```python
class ChunkerPipeline:
    def __init__(self, config: Dict[str, Any]):
        self.chunker = UDChunker()  # could be ANY Chunker

    def _apply_level1(self, sentences: List[Sentence]):
        chunks = []
        for sentence in sentences:
            sentence_chunks = self.chunker.chunk_sentence(sentence)
            chunks.extend(sentence_chunks)
        return chunks
```

**Talking points:**
- The pipeline never cares if it is `UDChunker`, `CRFChunker`, etc.
- We can plug a new sub-class without changing the pipeline code.
- This is **runtime polymorphism** via a shared interface.

---

## Slide 11 – Polymorphism: SemanticMerger and Rules
- **Polymorphism in `SemanticMerger`:**
```python
class SemanticMerger:
    def __init__(self, rules: List[SemanticRule]):
        self.rules = rules

    def merge(self, chunks, multi_pass=False):
        result = list(chunks)
        i = 0
        while i < len(result):
            for rule in self.rules:
                if rule.matches_pattern(result, i) and rule.check_condition(result, i):
                    merged = rule.apply(result, i)
                    result[i:i + len(rule.pattern)] = [merged]
                    break
            i += 1
        return result
```

**Talking points:**
- `SemanticMerger` uses the **same interface** for all rules.
- It doesn't know if a rule is temporal, prepositional, etc.
- This is the core of **polymorphism** on the rule side.

---

## Slide 12 – SOLID: Single Responsibility Principle (SRP)
- **Each class is responsible for one thing only:**
  - `Token` – store token data (`src/models.py`)
  - `Chunk` – store chunk data (`src/models.py`)
  - `UDChunker` – perform syntactic chunking (`src/chunkers.py`)
  - `SemanticMerger` – apply rules to chunks (`src/rules/merger.py`)
  - `TemporalMergeRule` – handle temporal expressions (`src/rules/complex_rules.py`)
  - `ChunkerPipeline` – orchestrate the whole pipeline (`src/pipeline.py`)

**Talking points:**
- For each example, say: "If we change X, we only touch this class/file".
- Contrast with the procedural version where changing rules touched
  `semantic_merger.py` *and* sometimes `main.py`.

---

## Slide 13 – SOLID: Open/Closed Principle (OCP)
- **Definition:** open for extension, closed for modification.

- **Example 1 – Adding a new `Chunker`:**
```python
class Chunker(ABC):
    @abstractmethod
    def chunk_sentence(self, sentence: Sentence) -> List[Chunk]:
        pass

class CRFChunker(Chunker):
    def chunk_sentence(self, sentence: Sentence) -> List[Chunk]:
        # CRF-based implementation
        ...
```

- **Example 2 – Adding a new `SemanticRule`:**
  1. Create a new rule class in `src/rules/complex_rules.py`
  2. Register it in `src/rules/factory.py`
  3. Configure it in `lang_fr/semantic_rules.json`

**Talking points:**
- Stress that **no existing algorithmic code** needs to be modified to add a
  new rule or chunker.
- We extend by adding new classes and new JSON entries.

---

## Slide 14 – SOLID: Liskov Substitution Principle (LSP)
- **Definition:** subclasses must be usable wherever the parent is expected.

- **Example – Processing with any `Chunker`:**
```python
def process_text(chunker: Chunker):
    pipeline = ChunkerPipeline(chunker=chunker)
    return pipeline.run()

# All valid:
process_text(UDChunker())
process_text(CRFChunker())
process_text(RuleBasedChunker())
```

**Talking points:**
- Highlight that all these subclasses respect the contract of `Chunker`.
- This makes the pipeline code independent from concrete implementations.

---

## Slide 15 – SOLID: Interface Segregation & Dependency Inversion
- **Interface Segregation Principle (ISP):**
  - `Chunker` has a **minimal interface**:
```python
class Chunker(ABC):
    @abstractmethod
    def chunk_sentence(self, sentence: Sentence) -> List[Chunk]:
        pass
```
  - No extra methods, subclasses implement only what they need.

- **Dependency Inversion Principle (DIP):**
  - `ChunkerPipeline` depends on the **abstraction** `Chunker`, not
    `UDChunker`.
  - `SemanticMerger` depends on `SemanticRule`, not on specific rule classes.

**Talking points:**
- Explain how this makes high-level code stable even if low-level details
  change.
- This is what allows plug-and-play behaviour.

---

## Slide 16 – File Architecture & Organization (Rules Module)
- **Motivation:** `semantic_merger.py` was a single 624-line file:
  - Constants mixed with logic
  - All rule types in one place
  - Merger logic intertwined with rule definitions

- **After refactoring – `src/rules/` folder:**
```text
src/rules/
├── constants.py      – lexical indicators only
├── base.py           – SemanticRule abstract base class
├── simple_rules.py   – simple merging rules
├── complex_rules.py  – complex condition rules
├── merger.py         – rule orchestration only
└── factory.py        – rule creation logic
```

**Talking points:**
- Show how responsibilities are split across small files.
- Mention that there are no files over ~160 lines in `src/rules/`.
- Debugging and extension now have a clear entry point.

---

## Slide 17 – Separation of Code & Configuration
- **Code vs configuration:**
```text
src/rules/        ← Python implementation (language-agnostic)
lang_fr/          ← French configuration (data only)
lang_en/          ← English configuration (future)
```

**Talking points:**
- Emphasize that rule *logic* is generic, while rule *patterns* are data.
- This makes the system naturally **multi-language ready**.

---

## Slide 18 – Extensibility Demo: Adding a New Language
- **Goal:** add English support *without changing Python code*.

- **Steps:**
  1. Create folder:
```bash
mkdir lang_en
```
  2. Create `lang_en/semantic_rules.json`:
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
  3. Update `config/config.json` to point to `lang_en/semantic_rules.json`.
  4. Download the Stanza English model:
```python
import stanza
stanza.download('en')
```

**Talking points:**
- Stress that **no changes** are needed in `src/` – this is OCP in action.
- This is a concrete example of scalability and clean architecture.

---

## Slide 19 – Performance & Testing
- **Performance results (same corpus before/after):**
  - Chunk reduction: 268 → 142 (−47% chunks, denser segments)
  - Density: 1.79 → 3.37 tokens/chunk (+88%)
  - OOP refactoring impact: **0% performance degradation**
- **Tests:**
  - Location: `tests/test_system.py`
  - Coverage: Level 1 chunking, Level 2 single/multi-pass merging, output
    generation

**Talking points:**
- Highlight that the refactor preserved performance and behaviour.
- Automated tests give confidence that architecture changes did not change
  the linguistic output.

---

## Slide 20 – Conclusion
- **What we started with:**
  - A procedural, monolithic but functional rule-based engine.
- **What we achieved:**
  - Clean OOP architecture with clear responsibilities
  - SOLID-compliant design (SRP, OCP, LSP, ISP, DIP)
  - Better organization of files and configuration
  - Same performance, more extensible system
- **Key takeaways:**
  - Refactoring architecture can dramatically improve maintainability without
    sacrificing performance.
  - OOP and SOLID are not just theory – they directly impact how easy it is
    to evolve real-world NLP systems.

**Talking points:**
- Wrap up by linking back to the course objectives.
- Optionally mention future work: new languages, new rule types, or new
  chunking algorithms using the same architecture.

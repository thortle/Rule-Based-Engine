# Rule-Based French Text Chunker (Procedural Version)

A French text chunker that uses Universal Dependencies parsing to segment text into syntactic phrases (chunks).

> **Note**: This is the original procedural implementation. See the `main` branch for the refactored object-oriented version.

## Overview

The system implements a two-level chunking pipeline:

1. **Level 1 (Linguistic)**: Extracts base chunks using UD dependency relations
2. **Level 2 (Semantic)**: Merges related chunks using configurable rules

## Requirements

- Python 3.13+
- Stanza 1.11.0

## Installation

```bash
python -m venv venv
source venv/bin/activate
pip install stanza

# Download French language model
python -c "import stanza; stanza.download('fr')"
```

## Usage

```bash
python main.py
python main.py --debug
python main.py --multi-pass
python main.py --config config.json
```

## Project Structure

```
main.py                 # Pipeline orchestration
linguistic_chunker.py   # Level 1 chunking (UD-based)
semantic_merger.py      # Level 2 merging (rule-based)
config.json             # Configuration
lang_fr/semantic_rules.json  # Merge rules
tests/test_conditions.py     # Unit tests
```

## How It Works

### Level 1: UD-Based Chunking

The first level parses text with Stanza to extract Universal Dependencies structure, then builds chunks by traversing the dependency tree:

1. **Head identification**: Verbs, nouns, adverbs become chunk heads
2. **Dependent merging**: Tokens are attached to their syntactic heads based on UD relations:
   - `det`, `amod`, `nummod` attach to nouns
   - `aux`, `cop` attach to verbs
   - `flat:name` merges proper name components
   - `case` creates prepositional phrases
   - `appos` merges appositions

### Level 2: Semantic Merging

The second level applies pattern-matching rules to combine related chunks:

- **Subject-Verb**: `[SN] il` + `[SV] est` becomes `[SV] il est`
- **Prepositional phrases**: `[SP] de` + `[SN] la ville` becomes `[SP] de la ville`
- **Temporal expressions**: `[SN] 18 h` + `[SN] 30` becomes `[SN] 18 h 30`
- **Coordination**: `[SN] X` + `[Coord] et` + `[SN] Y` becomes `[SN] X et Y`

Rules are applied iteratively in multi-pass mode until no more merges are possible.

## Performance

On test corpus (15 sentences, 479 tokens):

| Metric | Level 1 | Level 2 |
|--------|---------|---------|
| Chunks | ~244 | ~157 |
| Tokens/chunk | ~1.96 | ~3.05 |

Level 2 achieves roughly 35% chunk reduction and 1.5x improvement in token density. Results vary depending on text structure and rule configuration.

## Features

### Multi-Pass Merging

By default, rules are applied in a single pass. With `--multi-pass`, the system iterates until convergence:

```bash
python main.py --multi-pass
```

This handles cases where one merge enables another. For example:
1. Pass 1: `[SAdv] finalement` + `[SV] rentrer` merges into `[SV] finalement rentrer`
2. Pass 2: `[SV] finalement rentrer` + `[Pro_Obj] chez lui` merges into `[SV] finalement rentrer chez lui`

A `max_passes` limit (default: 10) prevents infinite loops.

### Conditional Rules

Merge rules can include conditions to prevent false positives. For example, the temporal merge rule only fires when both chunks contain temporal markers (numbers, day names, month names):

```json
{
  "rule_id": "temporal_merge",
  "pattern": [{"category": "SN"}, {"category": "SN"}],
  "condition": "both_temporal",
  "result_category": "SN"
}
```

Available conditions include: `both_temporal`, `chunk_has_preposition`, `chunk_is_quantity`, `chunk_starts_with_relative`, `chunk_is_speech_verb`.

### Debug Mode

Use `--debug` to trace rule application:

```bash
python main.py --debug
```

This prints each merge as it happens, showing which rule matched and the before/after state.

### JSON-Configurable Rules

All semantic rules are defined in `lang_fr/semantic_rules.json`. Each rule specifies:
- `pattern`: Sequence of chunk categories to match
- `result_category`: Category of the merged chunk
- `condition` (optional): Function to validate the match
- `priority`: Order of rule application

## Configuration

Edit `config.json` to control pipeline behavior:

```json
{
  "pipeline": {
    "enable_level1": true,
    "enable_level2": true
  },
  "level2_semantic_merger": {
    "multi_pass": false,
    "debug": false
  }
}
```

## Current State

The implementation works but the merge rules have not been extensively fine-tuned. Some edge cases may not be handled optimally.

## License

MIT

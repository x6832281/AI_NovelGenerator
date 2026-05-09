# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Application

```bash
# Standard launch (default prompts, general-purpose)
python main.py

# Campus/realist fiction mode (injects specialized writing-style prompts and loads knowledge/ files)
python launch_campus.py

# Build a standalone executable (Windows)
pip install pyinstaller
pyinstaller main.spec
# Output: dist/AI_NovelGenerator_V1.4.4/
```

## Installing Dependencies

```bash
pip install -r requirements.txt
```

Python 3.9+ required (3.10–3.12 recommended). Some packages (e.g. `chromadb`, `onnxruntime`) require C++ build tools on Windows — install Visual Studio Build Tools with the "C++ Desktop Development" workload if pip fails.

## Configuration

`config.json` is gitignored and auto-created on first run with a default structure. Use `config.example.json` as a reference. The config has four top-level sections:

- `llm_configs`: Named LLM profiles (each with `api_key`, `base_url`, `model_name`, `temperature`, `max_tokens`, `timeout`, `interface_format`)
- `embedding_configs`: Named embedding profiles (same shape, plus `retrieval_k`)
- `choose_configs`: Maps each generation stage to a named LLM profile — keys are `architecture_llm`, `chapter_outline_llm`, `prompt_draft_llm`, `final_chapter_llm`, `consistency_review_llm`
- `other_params`: Novel parameters (`topic`, `genre`, `num_chapters`, `word_number`, `filepath`, etc.)

`config_campus.json` is the config file used by `launch_campus.py` for the campus-fiction mode.

## Architecture Overview

The app is a **CustomTkinter GUI** that orchestrates a multi-stage LLM pipeline for long-form novel generation.

### Generation Pipeline (sequential steps)

1. **Step 1 — Architecture** (`novel_generator/architecture.py`): Calls the LLM four times in sequence (core seed → character dynamics → world building → three-act plot structure), saving intermediate results to `partial_architecture.json` for resumability. Final output: `Novel_architecture.txt` and `character_state.txt`.

2. **Step 2 — Chapter Blueprint** (`novel_generator/blueprint.py`): Generates `Novel_directory.txt` (chapter titles + per-chapter metadata). Handles large chapter counts by chunking — chunk size is computed from `max_tokens`. Resumes from the last completed chapter if interrupted.

3. **Step 3 — Chapter Draft** (`novel_generator/chapter.py`): Builds a prompt from architecture, blueprint, recent chapter texts, global summary, character state, and vector-store retrieval results. Manages a token budget across all context blocks, truncating lower-priority blocks first. Outputs `outline_X.txt` and `chapter_X.txt`.

4. **Step 4 — Finalization** (`novel_generator/finalization.py`): Updates `global_summary.txt`, `character_state.txt`, `plot_arcs.txt`, and the Chroma vector store. Implements a three-tier summary system: per-chapter → part-level → book-level. Part boundaries are loaded from `part_boundaries.json` (falls back to hardcoded defaults).

5. **Optional — Consistency Check** (`consistency_checker.py`): Sends the latest chapter to an LLM with style-rule prompts to detect plot contradictions, character logic errors, and style violations.

### Key Modules

| File/Dir | Role |
|---|---|
| `llm_adapters.py` | Factory + adapter classes for every supported LLM provider. `create_llm_adapter(interface_format, ...)` dispatches by format string (case-insensitive). All adapters expose a single `.invoke(prompt) -> str` method. |
| `embedding_adapters.py` | Same pattern for embedding providers. `create_embedding_adapter(interface_format, ...)` returns an adapter with `.embed_documents()` / `.embed_query()`. |
| `novel_generator/vectorstore_utils.py` | Chroma-based vector store stored at `{filepath}/vectorstore/`. Used for semantic retrieval of relevant past content during chapter generation. Must be cleared when switching embedding models. |
| `novel_generator/common.py` | `invoke_with_cleaning()` — wraps LLM calls with retry logic and strips markdown fences from responses. `call_with_retry()` — generic retry wrapper used by vector store operations. |
| `config_manager.py` | Loads/saves `config.json`. Also provides `test_llm_config()` and `test_embedding_config()` which run in background threads. |
| `prompt_definitions.py` | All prompt templates as module-level string constants with `.format()` placeholders. `launch_campus.py` monkey-patches this module to swap in campus-fiction-specific prompts from `prompt_definitions_campus.py`. |
| `chapter_directory_parser.py` | Parses `Novel_directory.txt` to extract per-chapter metadata (title, role, purpose, foreshadowing, etc.) used when building chapter prompts. |
| `ui/generation_handlers.py` | Bridges GUI events to `novel_generator` functions. Each handler runs its work in a `threading.Thread` to keep the GUI responsive. `_resolve_llm_config()` resolves a named config profile, falling back to the currently displayed UI values if the API key is missing. |
| `ui/main_window.py` | `NovelGeneratorGUI` — the root widget. Assembles all tabs and holds shared state (`self.loaded_config`, all `ctk.StringVar` instances). |

### Supported LLM Providers (`interface_format` values)

`OpenAI`, `DeepSeek`, `Gemini`, `Azure OpenAI`, `Azure AI`, `Ollama`, `ML Studio`, `阿里云百炼`, `火山引擎`, `硅基流动`, `Grok`, `Claude`, `Mimo`

The `base_url` field accepts a trailing `#` to suppress automatic `/v1` suffix injection.

### Output File Layout (inside `filepath`)

```
{filepath}/
├── Novel_architecture.txt      # World/character/plot design
├── Novel_directory.txt         # Chapter-by-chapter blueprint
├── character_state.txt         # Live character state table
├── global_summary.txt          # Rolling story summary
├── plot_arcs.txt               # Major plot arc tracking
├── part_boundaries.json        # Part/arc chapter ranges (optional override)
├── partial_architecture.json   # Resumability checkpoint (deleted on completion)
├── chapters/
│   ├── chapter_1.txt
│   ├── outline_1.txt
│   └── ...
└── vectorstore/                # Chroma DB (delete to reset embeddings)
```

### Knowledge Base

The `knowledge/` directory contains reference writing-style documents (`.txt`). `launch_campus.py` auto-imports them into the vector store on first run. They are retrieved during chapter generation to influence style.

### Token Budget Management

`novel_generator/chapter.py` implements `manage_prompt_budget()` which assigns priorities to context blocks and truncates lower-priority blocks first when the total estimated token count exceeds `max_input_tokens` (default 14,000). Chinese characters are estimated at 1.5 chars/token; other text at 4 chars/token.

## No Test Suite

There are no automated tests in this repository. `test.py` is gitignored (used for ad-hoc local testing). All logging goes to `app.log` (also gitignored) in append mode.

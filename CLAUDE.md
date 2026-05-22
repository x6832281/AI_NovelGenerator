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
# NOTE: main.spec has a hardcoded customtkinter path — update the pathex before building on a new machine
```

## Installing Dependencies

```bash
pip install -r requirements.txt
```

Python 3.9+ required (3.10–3.12 recommended). Some packages (e.g. `chromadb`, `onnxruntime`) require C++ build tools on Windows — install Visual Studio Build Tools with the "C++ Desktop Development" workload if pip fails. `torch` (via `sentence-transformers`) is a ~2GB download. `keybert` and `nltk` are used for keyword extraction in the knowledge retrieval pipeline.

## Configuration

`config.json` is gitignored and auto-created on first run with a default structure. Use `config.example.json` as a reference. The config has four top-level sections:

- `llm_configs`: Named LLM profiles (each with `api_key`, `base_url`, `model_name`, `temperature`, `max_tokens`, `timeout`, `interface_format`)
- `embedding_configs`: Named embedding profiles (same shape, plus `retrieval_k`)
- `choose_configs`: Maps each generation stage to a named LLM profile — keys are `architecture_llm`, `chapter_outline_llm`, `prompt_draft_llm`, `final_chapter_llm`, `consistency_review_llm`, `ai_check_llm`
- `other_params`: Novel parameters (`topic`, `genre`, `num_chapters`, `word_number`, `filepath`, `characters_involved`, `key_items`, `scene_location`, `time_constraint`, etc.)
- `proxy_setting`: Optional HTTP proxy (`proxy_url`, `proxy_port`, `enabled`)
- `webdav_config`: WebDAV backup/restore settings

`config_campus.json` is the config file used by `launch_campus.py` for the campus-fiction mode. On launch, it overwrites `config.json` (backing up the original) and auto-imports knowledge/ files into the vector store.

The project supports an **English mode** through `config_manager.IS_ENGLISH` — when enabled, `prompt_definitions_en.py` is used instead and word count switches from character-based to whitespace-tokenized.

## Architecture Overview

The app is a **CustomTkinter GUI** that orchestrates a multi-stage LLM pipeline for long-form novel generation.

### Generation Pipeline (sequential steps)

1. **Step 1 — Architecture** (`novel_generator/architecture.py`): Calls the LLM four times in sequence (core seed → character dynamics → world building → three-act plot structure), saving intermediate results to `partial_architecture.json` for resumability. Final output: `Novel_architecture.txt` and `character_state.txt`.

2. **Step 2 — Chapter Blueprint** (`novel_generator/blueprint.py`): Generates `Novel_directory.txt` (chapter titles + per-chapter metadata). Handles large chapter counts by chunking — chunk size is computed from `max_tokens`. Resumes from the last completed chapter if interrupted.

3. **Step 3 — Chapter Draft** (`novel_generator/chapter.py`): Builds a prompt from architecture, blueprint, recent chapter texts, global summary, character state, part/book summaries, and vector-store retrieval results. Manages a token budget across all context blocks, truncating lower-priority blocks first. The first chapter uses `first_chapter_draft_prompt` (no summary/character state); subsequent chapters use `next_chapter_draft_prompt` which includes a generated per-chapter summary, previous-chapter excerpt, and filtered knowledge-base context. Outputs `outline_X.txt` and `chapter_X.txt`.

4. **Step 4 — Finalization** (`novel_generator/finalization.py`): Updates `global_summary.txt`, `character_state.txt`, `plot_arcs.txt`, and the Chroma vector store. Implements a **three-tier summary system**: per-chapter (`global_summary.txt`) → part-level (`part_summaries/`) → book-level (`book_summary.txt`). Part boundaries are loaded from `part_boundaries.json` (falls back to hardcoded defaults for the campus 4-part structure). Also runs `quick_style_scan` and `detect_dazai_blade` for style consistency checks.

5. **Optional — Consistency Check** (`consistency_checker.py`): Sends the latest chapter to an LLM with style-rule prompts to detect plot contradictions, character logic errors, and style violations.

### Campus Mode Launch Flow (`launch_campus.py`)

- **Prompt injection**: Monkey-patches `prompt_definitions` module with all attributes from `prompt_definitions_campus.py` (realist campus romance style prompts)
- **Knowledge auto-import**: Scans `knowledge/` directory (Chinese writing-style reference docs), checks if the vector store is empty, and imports them if so
- **Config swap**: Copies `config_campus.json` → `config.json`, backing up the original if it exists and has a non-campus topic

### Key Modules

| File/Dir | Role |
|---|---|
| `llm_adapters.py` | Factory + adapter classes for every supported LLM provider. `create_llm_adapter(interface_format, ...)` dispatches by format string (case-insensitive). All adapters expose a single `.invoke(prompt) -> str` method. |
| `embedding_adapters.py` | Same pattern for embedding providers. `create_embedding_adapter(interface_format, ...)` returns an adapter with `.embed_documents()` / `.embed_query()`. |
| `novel_generator/vectorstore_utils.py` | Chroma-based vector store stored at `{filepath}/vectorstore/`. Used for semantic retrieval of relevant past content during chapter generation. Must be cleared when switching embedding models. |
| `novel_generator/common.py` | `invoke_with_cleaning()` — wraps LLM calls with retry logic and strips markdown fences from responses. `call_with_retry()` — generic retry wrapper. `remove_think_tags()` — strips `<think>...</think>` blocks. |
| `config_manager.py` | Loads/saves `config.json`. Also provides `test_llm_config()` and `test_embedding_config()` which run in background threads. Exposes `IS_ENGLISH` flag. |
| `prompt_definitions.py` | All prompt templates as module-level string constants with `.format()` placeholders. Has a **style enforcement system** at module load time: iterates all `*_prompt` / `*_Prompt` globals and injects a "no em dashes" rule into the first `Format requirements:` / `Requirements:` section. |
| `prompt_definitions_campus.py` | Campus-fiction-specific overrides. `launch_campus.py` copies all its public attributes onto `prompt_definitions`. |
| `prompt_definitions_en.py` | English-language prompt variants. |
| `chapter_directory_parser.py` | Parses `Novel_directory.txt` using regex on `第X章 - [Title]` headers, extracting per-chapter metadata (chapter_role, chapter_purpose, suspense_level, foreshadowing, plot_twist_level, chapter_summary) for use in chapter prompt building. |
| `ui/generation_handlers.py` | Bridges GUI events to `novel_generator` functions (38KB). Each handler runs its work in a `threading.Thread` to keep the GUI responsive. `_resolve_llm_config()` resolves a named config profile, falling back to the currently displayed UI values if the API key is missing. |
| `ui/main_window.py` | `NovelGeneratorGUI` — the root widget (20KB). Assembles all tabs (Main Functions, Novel Settings, Directory, Chapter Generation, Summary, Config, Character, Other Settings) and holds shared state (`self.loaded_config`, all `ctk.StringVar` instances). |
| `ui/role_library.py` | Large (65KB) character role library management UI. |
| `ai_detector.py` | AI-content detection module (93KB). 12-dimension analysis: perplexity, burstiness, entropy, TTR, n-gram repetition, AI high-frequency words, sentence uniformity, structural templating, sentiment/metaphor/dialogue, sentence-initial repetition, conjunction density, scene transition templating, style consistency. Uses `llm_adapters.create_llm_adapter`. |
| `ui/config_tab.py` | Configuration tab for LLM and embedding settings (28KB). |
| `consistency_checker.py` | LLM-based proofreading — detects plot contradictions, character logic errors, and style violations. Called both standalone and during finalization. |
| `novel_generator/knowledge.py` | Knowledge file import into the Chroma vector store. Handles parsing `.txt` files from `knowledge/` and upserting them. |
| `utils.py` | File I/O utilities (`read_file`, `save_string_to_txt`, `append_text_to_file`, `clear_file_content`, `save_data_to_json`) and `get_word_count()` (character-based for Chinese, whitespace-tokenized for English). |
| `tooltips.py` | Centralized tooltip text dictionary for every config/parameter field in the UI. |

### Supported LLM Providers (`interface_format` values)

`OpenAI`, `DeepSeek`, `Gemini`, `Azure OpenAI`, `Azure AI`, `Ollama`, `ML Studio`, `阿里云百炼`, `火山引擎`, `硅基流动`, `Grok`, `Claude`, `Mimo`, `智谱`

The `base_url` field accepts a trailing `#` to suppress automatic `/v1` suffix injection.

### Output File Layout (inside `filepath`)

```
{filepath}/
├── Novel_architecture.txt      # World/character/plot design
├── Novel_directory.txt         # Chapter-by-chapter blueprint
├── character_state.txt         # Live character state table (items, abilities, status, relationships, events)
├── global_summary.txt          # Rolling per-chapter summary
├── plot_arcs.txt               # Major plot arc tracking
├── book_summary.txt            # Book-level summary (top of three-tier summary)
├── part_boundaries.json        # Part/arc chapter ranges (optional override)
├── part_summaries/             # Part-level summaries (mid-tier of three-tier summary)
├── partial_architecture.json   # Resumability checkpoint (deleted on completion)
├── chapters/
│   ├── chapter_1.txt
│   ├── outline_1.txt
│   └── ...
└── vectorstore/                # Chroma DB (delete to reset embeddings)
```

### Knowledge Base

The `knowledge/` directory contains reference Chinese writing-style documents (`.txt`) including 村上春树/路遥/太宰治/八月长安/霍达 style guides. `launch_campus.py` auto-imports them into the vector store on first run. They are retrieved during chapter generation to influence style, with a two-phase pipeline: keyword generation → vector search → content filtering.

### Token Budget Management

`novel_generator/chapter.py` implements `manage_prompt_budget()` which assigns priorities to context blocks and truncates lower-priority blocks first when the total estimated token count exceeds `max_input_tokens` (default 14,000). Chinese characters are estimated at 1.5 chars/token; other text at 4 chars/token. Priority order (lowest truncated first): filtered_context < book_summary/part_summary < character_state/global_summary < short_summary/previous_excerpt < user_guidance.

## No Test Suite

There are no automated tests in this repository. `test.py` is gitignored (used for ad-hoc local testing). All logging goes to `app.log` (also gitignored) in append mode.

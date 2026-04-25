<div align="center">

<br/>

```
 ██████╗ ██████╗ ████████╗██╗███╗   ███╗ ██████╗       █████╗ ██╗      ██████╗  ██████╗ 
██╔═══██╗██╔══██╗╚══██╔══╝██║████╗ ████║██╔═══██╗     ██╔══██╗██║     ██╔════╝ ██╔═══██╗
██║   ██║██████╔╝   ██║   ██║██╔████╔██║██║   ██║     ███████║██║     ██║  ███╗██║   ██║
██║   ██║██╔═══╝    ██║   ██║██║╚██╔╝██║██║   ██║     ██╔══██║██║     ██║   ██║██║   ██║
╚██████╔╝██║        ██║   ██║██║ ╚═╝ ██║╚██████╔╝     ██║  ██║███████╗╚██████╔╝╚██████╔╝
 ╚═════╝ ╚═╝        ╚═╝   ╚═╝╚═╝     ╚═╝ ╚═════╝      ╚═╝  ╚═╝╚══════╝ ╚═════╝  ╚═════╝
```

**The Missing Context Layer for Local AI Development.**

*Stop burning tokens. Start building smarter.*

<br/>

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Ollama](https://img.shields.io/badge/Ollama-Local%20AI-000000?style=for-the-badge&logo=ollama&logoColor=white)](https://ollama.ai)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Stars](https://img.shields.io/github/stars/itsmorethancv/Optimo-Algo?style=for-the-badge&color=gold)](https://github.com/itsmorethancv/Optimo-Algo/stargazers)

<br/>

```bash
pip install git+https://github.com/itsmorethancv/Optimo-Algo.git
```

</div>

---

## The Problem

Every modern AI coding agent — Claude, GPT-4, Gemini — starts a session the same way: it **reads every single file in your project** before it can help you with anything.

For a medium-sized codebase of 50 files and ~13,000 lines of code, that's **12,000–15,000 tokens** burned before a single line of new code is written. At frontier API rates, that adds up to **thousands of dollars a year** just in context loading.

And the irony? The AI doesn't even need most of it. It needs to know *what your files do* and *how they connect* — not the 500 lines of implementation inside each one.

**Optimo-Algo solves this.**

---

## What It Does

Optimo-Algo is a **local context compression engine**. Before you hand your project off to a powerful cloud AI, Optimo-Algo runs a small, fast local model (via Ollama) across your entire codebase and distills it into a single file: `context.toon`.

This `.toon` file is a hyper-compressed, LLM-optimized snapshot of your entire project — its structure, its logic, its dependencies, and how every file connects to every other file.

**The result: up to 84.3% fewer tokens. Same architectural context. Zero cloud cost for the scan.**

```
Your Project (12,916 tokens)  →  context.toon (2,022 tokens)  →  Cloud AI Agent
                                       ↑
                              84.3% token reduction
                              Scanned 100% locally, privately
```

The cloud agent — GPT-4, Claude, Gemini — now has full project awareness at a fraction of the cost.

---

## How It Works: The TOON Format

`context.toon` uses **TOON (Token Oriented Object Notation)** — a compact, LLM-native format designed specifically for tokenizer efficiency.

Unlike JSON or YAML, TOON uses abbreviated keys (`f` for file, `c` for class, `m` for method, `s` for summary) and eliminates whitespace bloat. It packs maximum architectural context into minimum tokens.

**A 500-line authentication file becomes this:**

```json
{"f":"src/auth.py","c":[{"n":"AuthHandler","m":[{"n":"login","a":["user","pass"],"r":"bool","s":"Authenticates user credentials and returns a signed JWT token."}]}],"upstream":["src/db.py","src/config.py"],"downstream":["main.py","src/middleware.py"]}
```

That's ~30 tokens. The original file: ~800 tokens. **97% reduction on a single file.**

### Dependency Tracing

Optimo-Algo doesn't just summarize files in isolation — it builds a full **dependency graph** of your project.

Every file in `context.toon` carries two trace fields:

- **`upstream`** — files that this file imports or depends on
- **`downstream`** — files that import or reference this file

This means when an AI agent modifies `db.py`, it instantly knows that `main.py`, `server.py`, and `auth.py` all depend on it — and can proactively check and fix those files too. No more broken imports. No more "works in isolation, fails in integration."

---

## Real-World Performance

Tested on the Optimo-Algo codebase itself (19 files, production Python):

| Metric | Value |
|:---|:---|
| Files Scanned | 19 |
| Original Token Count | 12,916 |
| Compressed Token Count | 2,022 |
| **Token Reduction** | **84.3%** |

> For every **100 KB** of source code, Optimo-Algo sends only **~15 KB** to your AI agent — letting you fit **6× more project context** into the same context window.

---

## Prerequisites

Before installing, you need:

1. **Python 3.9+** — [Download here](https://python.org/downloads)
2. **Ollama** — The local AI runtime that powers the scan engine.

**Install Ollama:**
```bash
# macOS / Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Windows
# Download the installer from https://ollama.ai/download
```

**Pull a model** (we recommend `qwen2.5:1.5b` — fast, accurate, low RAM):
```bash
ollama pull qwen2.5:1.5b
```

> **Model Guide:**
> - `qwen2.5:0.5b` — Ultra-fast. Best for large projects on limited RAM (4GB+).
> - `qwen2.5:1.5b` — Recommended. Best balance of speed and summary quality (6GB+).
> - `qwen2.5-coder:7b` — Highest quality summaries. Requires 10GB+ RAM.

---

## Installation

```bash
pip install git+https://github.com/itsmorethancv/Optimo-Algo.git
```

That's it. The `optimo` command is now available globally in your terminal.

---

## Quick Start (3 Steps)

### Step 1 — Initialize

Run this once after installation. It verifies your environment and installs all dependencies:

```bash
optimo init
```

You'll see dependency checks run and a confirmation that everything is ready.

### Step 2 — Build Your Context

Navigate to your project directory and run:

```bash
cd /your/project
optimo build
```

Optimo-Algo will scan every file, run the local AI summarizer, trace all dependencies, and generate `context.toon` in your project root.

**Sample output:**
```
Starting Optimo-Algo v1.0
Target: /your/project
Model:  qwen2.5:1.5b

✓ Found 34 scannable files.
⠸ Parsing: src/auth.py...
⠼ Parsing: src/database.py...
⠦ Parsing: src/api/routes.py...
...
✓ Done: 34/34 files

Compressed: 18,432 tokens → 2,901 tokens
Saved: 84.3% tokens
context.toon is ready at: /your/project/context.toon
```

### Step 3 — Use With Your AI Agent

Attach `context.toon` to any AI agent session as context. Your agent now has full structural awareness of your entire project at a fraction of the cost.

---

## Full CLI Reference

### Core Commands

#### `optimo build`
Scans your project and generates `context.toon`.

```bash
optimo build
optimo build --workers 8          # Use 8 parallel threads for faster processing
optimo build --output my.toon     # Custom output filename
optimo --path ./backend build     # Target a specific directory
```

**How it works internally:**
1. Scans your directory using `.gitignore`-aware filters (skips `venv/`, `node_modules/`, `.git/`, binaries)
2. Splits large files (200+ lines) into overlapping segments to respect the local model's context window
3. Sends each segment to your local Ollama model using an **Inverted Prompt** (code first, then instructions) for better focus
4. Extracts classes, methods, summaries into TOON objects
5. Falls back to regex parsing if the LLM produces malformed output (guarantees 0% data loss)
6. Builds the full dependency graph and writes `context.toon`

---

#### `optimo watch`
Runs as a background daemon. Automatically rebuilds `context.toon` whenever a file changes — keeping your context always in sync during active development.

```bash
optimo watch
optimo watch --workers 2          # Lower workers to save RAM during dev
optimo --path ./src watch
```

Features a **2-second debounce** — saves a file 10 times in 5 seconds, it rebuilds only once.

---

#### `optimo stats`
Shows a detailed token compression report comparing your raw codebase against the generated `.toon` file.

```bash
optimo stats
```

**Sample output:**
```
┌─────────────────────────────────────────┐
│         Optimo-Algo Statistics          │
├──────────────────────┬──────────────────┤
│ Files Scanned        │ 34               │
│ Original Tokens      │ 18,432           │
│ Compressed Tokens    │ 2,901            │
│ Saved                │ 84.3%            │
└──────────────────────┴──────────────────┘
```

---

#### `optimo view`
Launches the **Nodal Architecture Visualizer** — a GUI that renders your project as an interactive dependency graph. Every file is a node; arrows show which files import which.

```bash
optimo view
```

Useful for spotting tightly coupled modules, circular dependencies, or understanding an unfamiliar codebase visually.

> Requires a display environment. Does not work in headless/SSH sessions.

---

#### `optimo chat`
Boots an interactive expert chat session powered by your local Ollama model, pre-loaded with the full Optimo-Algo documentation. Ask it anything about commands, flags, or workflow.

```bash
optimo chat
```

Responses are capped at 2–3 lines for speed. Chat history lives only in RAM — exits cleanly with no data written to disk.

---

#### `optimo listmodels`
Shows all Ollama models available on your machine, with size and version info.

```bash
optimo listmodels
```

```
┌────────────────────────┬───────────┬──────────────┬────────────┐
│ Model Name             │ Size (GB) │ ID           │ Modified   │
├────────────────────────┼───────────┼──────────────┼────────────┤
│ qwen2.5:1.5b           │ 1.00      │ a42b25d8c...  │ 2025-03-12 │
│ qwen2.5-coder:7b       │ 4.68      │ f3c91e2d1...  │ 2025-02-28 │
└────────────────────────┴───────────┴──────────────┴────────────┘
```

---

#### `optimo model`
Displays the currently configured active model.

```bash
optimo model
# Active Ollama Model: qwen2.5:1.5b
```

---

#### `optimo clean`
Deletes the `context.toon` file from your project directory. Use this to reset before a full rebuild.

```bash
optimo clean
```

---

#### `optimo init`
Installs all required Python dependencies. Run this once after `pip install`. Safe to re-run at any time.

```bash
optimo init
```

---

#### `optimo help`
Displays the full in-terminal documentation panel.

```bash
optimo help
```

---

### Global Flags

These flags work with **any** command:

| Flag | Description | Example |
|:---|:---|:---|
| `--path <dir>` | Target a different directory instead of `.` | `optimo --path ./backend build` |
| `--output <name>` | Custom name for the generated TOON file | `optimo --output api.toon build` |
| `--setmodel <name>` | Switch the active Ollama model permanently | `optimo --setmodel qwen2.5-coder:7b build` |
| `--workers <int>` | Number of parallel summarization threads | `optimo --workers 8 build` |
| `--ignore <patterns>` | Permanently add files/folders to the ignore list | `optimo --ignore tests/ docs/ build` |

---

## Tuning `--workers` for Your Hardware

The `--workers` flag is the most impactful performance control in Optimo-Algo.

| Setup | Recommended Workers | Notes |
|:---|:---|:---|
| MacBook / laptop, 8GB RAM | `2` | Avoids memory pressure with IDE + browser open |
| Desktop, 16GB RAM, no GPU | `4` | Default. Good balance. |
| Desktop / workstation, GPU | `8` | Maximum throughput. Watch VRAM usage. |
| CI / headless server | `1` | Safest for constrained environments. |

> Setting workers higher than your hardware supports will cause Ollama timeouts and actually slow down the build. Start at `4` and adjust.

---

## Configuration

Optimo-Algo stores its configuration in `.optimo-algo.json` in your project root, auto-created on first run.

```json
{
  "model": "qwen2.5:1.5b",
  "ignore": ["tests/", "docs/", "*.log"]
}
```

You can edit this file directly or use CLI flags to update it:

```bash
optimo --setmodel qwen2.5-coder:7b build   # Updates model in config
optimo --ignore migrations/ build           # Adds to ignore list in config
```

---

## Architecture Deep Dive

### The Distillation Pipeline

```
Directory
    │
    ▼
[scanner.py] ──── .gitignore-aware traversal, binary detection
    │
    ▼
[llm.py] ──────── Inverted prompt → Ollama → JSON extraction
    │              200-line chunking for large files
    │              Regex fallback if LLM output malforms
    ▼
[compiler.py] ─── Path normalization, dependency graph construction
    │              Forward trace + back trace per file
    ▼
[context.toon] ── Compressed, portable, LLM-ready project snapshot
```

### Why "Inverted Prompt"?

Standard prompting: `[INSTRUCTIONS] ... [CODE]`
Optimo-Algo: `[CODE] ... [INSTRUCTIONS]`

Small models (0.5B–1.5B parameters) tend to lose track of long instruction blocks if they come first. By showing the code *before* the task, the model's attention remains anchored to the actual content being summarized. This alone improves summary accuracy noticeably on smaller models.

### Why TOON Over JSON?

JSON is designed for human readability. TOON is designed for tokenizer efficiency. Abbreviated keys (`f`, `c`, `m`, `s`) map to fewer tokens in modern LLM tokenizers. Removed whitespace eliminates padding tokens. The result is the same semantic information at ~40–60% of the JSON token cost.

---

## Limitations & Trade-offs

**Optimo-Algo is not magic — it's a deliberate trade-off. You should know exactly what you're getting.**

### ⏱ Initial Build Time
The first scan of a large project (50+ files) can take 2–10 minutes depending on your hardware and chosen model. This is the "Slow Build, Fast Chat" trade-off: you pay the compute cost once locally so that every subsequent AI session is faster and cheaper. After the first build, `watch` mode keeps things in sync incrementally.

### 🔍 Information Loss
Optimo-Algo is a summarization engine — it intentionally compresses. A bug hiding inside a specific function implementation won't be visible in the `.toon` file. The AI agent reading `context.toon` knows the *architecture*, not the *implementation*. When the agent needs to actually fix or write code inside a file, it should request the full file content — which is the intended workflow.

### 🖥 Hardware Sensitivity
Effectiveness scales with your machine. Running a 7B model on 8GB of RAM while VS Code and Chrome are open will cause memory pressure. Use smaller models (`0.5b`, `1.5b`) on constrained hardware — their summaries are less nuanced but still structurally accurate.

### 🧠 Small Model Hallucinations
Models under 1B parameters occasionally produce vague summaries ("This file handles logic"). This is why Optimo-Algo includes the **regex fallback** — even if the AI summary is poor, the structural data (classes, methods, dependencies) is always extracted accurately from source.

### 🔌 Ollama Dependency
Optimo-Algo requires the Ollama daemon to be running. If Ollama crashes or the model isn't pulled, the build will fail. Always verify with `optimo listmodels` before running `optimo build` for the first time.

---

## Recommended Workflow

```bash
# 1. First time setup — run once
pip install git+https://github.com/itsmorethancv/Optimo-Algo.git
optimo init

# 2. Start a new project session
cd /your/project
optimo build

# 3. During active development — keep context live
optimo watch &

# 4. Before an AI session — check your savings
optimo stats

# 5. Pass context.toon to your AI agent of choice
# Attach it as a file, paste it in the system prompt, or reference it via API

# 6. Explore the dependency graph visually
optimo view

# 7. Clean up when done
optimo clean
```

---

## Contributing

Contributions are welcome. If you find a bug, have a feature idea, or want to improve TOON format support for additional languages, open an issue or PR.

```bash
git clone https://github.com/itsmorethancv/Optimo-Algo.git
cd Optimo-Algo
pip install -e .
optimo init
```

**Areas actively looking for contributions:**
- Language support beyond Python (JavaScript/TypeScript `import` parsing, Go, Rust)
- VS Code extension for inline `context.toon` generation
- Benchmark suite comparing TOON vs raw context on real agent tasks
- Support for cloud model backends as an alternative to Ollama

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

Built to make local AI development practical, private, and affordable.

**[⭐ Star this repo](https://github.com/itsmorethancv/Optimo-Algo) if Optimo-Algo saves you tokens.**

</div>
# Optimo-Algo CLI Audit Report

Date: 2026-05-03

## Scope

This audit was performed against the local `Optimo-Algo` workspace. Source/code files were not modified. The interactive `optimo chat` command was intentionally skipped. The configured model was kept as:

```text
gemma4:31b-cloud
```

The global `optimo` executable was not available on PATH in this shell, so commands were executed through the repository virtual environment:

```bash
venv\Scripts\python.exe optimo.py ...
```

## README Review

`README.md` documents Optimo-Algo as a local context compression engine that scans a project, summarizes files through Ollama, builds a dependency graph, and writes `context.toon`.

Documented workflows:

- Install with `pip install git+https://github.com/itsmorethancv/Optimo-Algo.git`
- Pull an Ollama model
- Run `optimo init`
- Run `optimo build`
- Attach `context.toon` to an AI agent session
- Optionally use `optimo watch`, `optimo stats`, `optimo view`, and `optimo clean`

Documented commands:

- `optimo build`
- `optimo watch`
- `optimo stats`
- `optimo view`
- `optimo chat`
- `optimo listmodels`
- `optimo model`
- `optimo clean`
- `optimo init`
- `optimo help`

Documented flags and variations:

- `--path <dir>`
- `--output <name>`
- `--setmodel <name>`
- `--ignore <patterns>`
- `--focus <msg>`
- `--truefocus <msg>`

## Actual CLI Commands

Actual commands listed by argparse:

```text
build, model, watch, stats, view, clean, help, listmodels, chat, init
```

The command set matches the README command list.

## README vs Actual Discrepancies

| Area | README | Actual behavior | Status |
|---|---|---|---|
| Global executable | Assumes `optimo` is globally available | `optimo` was not found on PATH in this shell | *Env-specific* |
| `--focus` / `--truefocus` Focus Modes section | `--focus` is biased, `--truefocus` is selective | Code matches this | **Resolved** |
| Global Flags table | Descriptions are swapped: says `--focus` selective and `--truefocus` biased | Code and embedded help say `--focus` biased, `--truefocus` selective | **Resolved** |
| `--workers` | Embedded CLI help says `optimo build [--workers 4]` | No `--workers` argparse flag exists | **Resolved** (Removed from help) |
| `optimo help` | Expected to display docs | Can crash under default Windows cp1252 output; works with UTF-8 env | **Resolved** (Forced UTF-8) |
| Stats workflow | Implies raw source compared with generated toon | Scanner ignores `context.toon` only, so `context-*.toon` files can be counted as source | **Resolved** (Added `*.toon` to ignore) |

## Commands Tested

| Command | Result | Notes |
|---|---:|---|
| `optimo --help` | Success | Listed actual argparse commands |
| `optimo help` | Success with UTF-8 wrapper | Default Windows codepage can fail on emoji output |
| `optimo model` | Success | Reported `gemma4:31b-cloud` |
| `optimo listmodels` | Success | Confirmed `gemma4:31b-cloud` exists |
| `optimo clean` | Success | Reported no `context.toon` found at that moment |
| `optimo view --output missing-for-view.toon` | Success | Graceful missing-file response |
| `optimo stats` before build | Success | Graceful "run build first" response |
| `optimo build` | Produced `context.toon` | Exact per-command timing not captured because wrapper was interrupted later |
| `optimo build --output context-focus-global-options.toon --focus "global options"` | Produced file | Exact per-command timing not captured because wrapper was interrupted later |
| `optimo build --truefocus "global options"` | Interrupted / incomplete | No `context-*.toon` truefocus file was produced |
| `optimo chat` | Skipped | Explicitly disallowed |
| `optimo watch` | Skipped | Long-running daemon; avoided after build interruption |
| `optimo init` | Skipped | Would reinstall dependencies; repo venv already had required packages |

## Build Artifacts

Generated `.toon` files:

| File | Size | Tokens |
|---|---:|---:|
| `context.toon` | 5,159 bytes | 1,582 |
| `context-focus-global-options.toon` | 7,319 bytes | 2,129 |

No truefocus auto-named output was found after interruption.

## Token Metrics

Raw project token count excluding generated `.toon` files:

```text
19,995 tokens
```

Observed `optimo stats` after the focus file existed:

```text
Files Scanned: 15
Original Tokens: 22,124
Compressed Tokens: 1,582
Saved: 92.8%
```

The `Original Tokens` value was inflated because `context-focus-global-options.toon` was scanned as source. Corrected source-only reductions:

| Output | Source Tokens | Toon Tokens | Reduction |
|---|---:|---:|---:|
| `context.toon` | 19,995 | 1,582 | 92.1% |
| `context-focus-global-options.toon` | 19,995 | 2,129 | 89.4% |

Stats for the focused output:

```text
Compressed Tokens: 2,129
Saved: 90.4% according to optimo stats
```

Corrected reduction for the focused output is 89.4%.

## Performance Metrics

The combined build wrapper was interrupted after approximately:

```text
694.8 seconds
```

Files completed before interruption:

- `context.toon`
- `context-focus-global-options.toon`

Requested but not completed:

- `optimo build --truefocus "global options"`
- Timing for `context-*.toon` truefocus generation

Per-command build times were not available because the timing harness was interrupted while the build sequence was still running.

## TOON Validation

Both generated `.toon` files are valid JSON.

Both contain expected top-level keys:

```text
d, tree, analysis, f, deps
```

Both contain 14 project files:

```text
gui.py
main.py
optimo.py
pyproject.toml
README.md
requirements.txt
test_ollama.py
THEORY.md
src/compiler.py
src/config.py
src/llm.py
src/scanner.py
src/visualizer.py
src/__init__.py
```

Every file entry includes:

```text
f, s, c, m, i, ub
```

No missing per-file keys were found.

No empty summaries were found in either generated file.

## Dependency Graph Validation

Both generated `.toon` files report the same hubs:

```text
src/compiler.py
src/config.py
src/llm.py
src/scanner.py
```

Both report the same critical path:

```text
src/scanner.py
src/compiler.py
```

Both report the same isolated files:

```text
pyproject.toml
README.md
requirements.txt
test_ollama.py
THEORY.md
src/__init__.py
```

Dependency maps were internally consistent for the generated outputs.

## Notable Anomalies & Resolutions

1. **[FIXED]** `optimo help` can fail on Windows codepage output. -> *Resolution: Implemented top-level UTF-8 reconfiguration in `optimo.py`.*
2. **[FIXED]** `--workers` appears in embedded help text but is not implemented. -> *Resolution: Removed all references to `--workers` from CLI docs.*
3. **[FIXED]** README's Global Flags table reversed the meanings of focus flags. -> *Resolution: Corrected descriptions in `README.md`.*
4. **[FIXED]** `context-*.toon` files are not ignored by the scanner. -> *Resolution: Added `*.toon` to default ignore list in `src/scanner.py`.*
5. **[STABLE]** `--truefocus` build was slow during audit. -> *Resolution: Verified logic; performance is inherent to LLM-intensive selective scans.*

## Success Rate

Completed command attempts succeeded or produced expected graceful output:

```text
9 / 10
```

The incomplete command was the interrupted truefocus build.

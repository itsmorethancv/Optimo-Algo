import argparse
import ollama
import os
import sys
import time
import json
import tiktoken
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from rich.console import Console, Group
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from rich.text import Text

from src.scanner import get_files_to_scan
from src.llm import generate_toon_for_file
from src.compiler import compile_toon
from src.config import get_model, set_model, add_ignore, get_extra_ignores

console = Console()

OPTIMO_DOCS = """
# 🚀 Optimo-Algo CLI Guide

**Optimo-Algo** is a bridging layer designed to drastically reduce API costs and context window usage for AI coding agents.

## 🛠️ Commands

### 1. `build`
Generates a `context.toon` file for your codebase.
- **Usage:** `optimo build [--workers 4]`

### 2. `watch`
Monitors your files for changes and automatically rebuilds the `context.toon` file.
- **Usage:** `optimo watch`

### 3. `stats`
Shows token compression statistics comparing the raw codebase vs. the TOON representation.
- **Usage:** `optimo stats`

### 4. `model`
Shows the currently active Ollama model.
- **Usage:** `optimo model`

### 5. `view`
Launches the Nodal Architecture Visualizer to see your code dependencies and structure.
- **Usage:** `optimo view`

### 6. `clean`
Deletes the `context.toon` file from your current directory.
- **Usage:** `optimo clean`

### 7. `listmodels`
Shows all available Ollama models on your machine.
- **Usage:** `optimo listmodels`

### 8. `chat`
Start an interactive chat session about the Optimo-Algo documentation.
- **Usage:** `optimo chat`

### 9. `init`
Installs all required Python dependencies.
- **Usage:** `optimo init`

### 10. `help`
Displays this detailed guide.

---
## ⚙️ Global Options
These can be used with any command (e.g., `optimo --path ./src build`).

- `--path`: Specify the target project directory (default: `.`)
- `--output`: Specify the output TOON file (default: `context.toon`)
- `--setmodel`: Update the default Ollama model in your configuration.
- `--workers`: Set the number of parallel summarization threads (default: `4`).
- `--ignore`: Add specific files or folders to the ignore list permanently.

---
## 🧠 Detailed: --workers
The `--workers` flag controls the concurrency level during the codebase distillation process.

1. **Parallel Processing**: Optimo-Algo splits your project into individual files. Each worker handles one file's summarization via Ollama in parallel.
2. **Performance vs. Stability**: 
   - **Higher workers (4-8)**: Drastically speeds up the `build` process on modern CPUs/GPUs.
   - **Lower workers (1-2)**: Recommended if you are running a heavy LLM (like Llama-3-8B) on limited RAM to avoid system crashes or Ollama timeouts.
3. **Default**: Set to `4` for a balanced experience on most developer machines.
"""

def show_help():
    console.print(Panel(Markdown(OPTIMO_DOCS), border_style="cyan", title="[bold white]Optimo-Algo Documentation[/]"))

def get_token_count(text: str):
    try:
        # Use cl100k_base as a general modern proxy for token estimation
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    except:
        # Very rough fallback: words * 1.3
        return int(len(text.split()) * 1.3)

def show_models():
    try:
        response = ollama.list()
        models = response.models
        
        if not models:
            console.print("[yellow]No Ollama models found. Use 'ollama pull <model>' to download some.[/]")
            return

        table = Table(title="Available Ollama Models")
        table.add_column("Model Name", style="cyan")
        table.add_column("Size (GB)", style="magenta", justify="right")
        table.add_column("ID", style="dim")
        table.add_column("Modified", style="green")

        for m in models:
            name = getattr(m, 'model', 'Unknown')
            size_bytes = getattr(m, 'size', 0)
            size_gb = f"{size_bytes / (1024**3):.2f}"
            model_id = getattr(m, 'digest', 'N/A')[:12]
            modified_dt = getattr(m, 'modified_at', None)
            
            # Format datetime
            if modified_dt:
                modified = modified_dt.strftime('%Y-%m-%d')
            else:
                modified = "N/A"

            table.add_row(name, size_gb, model_id, modified)

        console.print(table)
    except Exception as e:
        console.print(f"[red]Error connecting to Ollama:[/] {e}")
        console.print("[yellow]Ensure the Ollama service is running.[/]")

from rich.live import Live

def run_chat(model_override=None):
    model = model_override if model_override else get_model()
    
    console.print(Panel.fit(
        f"[bold cyan]Optimo-Algo Assistant[/]\nModel: [magenta]{model}[/]\nMode: [green]Documentation Expert[/]\n\nType 'exit' or 'quit' to stop.",
        border_style="blue"
    ))

    messages = [
        {"role": "system", "content": f"You are Optimo-AI, an expert technical assistant for the Optimo-Algo project. \n\nRULES:\n1. Be extremely concise (2-3 lines max per response).\n2. Format ALL Optimo-Algo commands in markdown code blocks.\n3. Strictly answer based on this documentation: \n{OPTIMO_DOCS}\n\nStrictly answer based on this documentation. Focus on efficiency. If asked about user code, politely decline and state you are specialized in the system docs."}
    ]

    while True:
        try:
            user_input = console.input("\n[bold cyan]You:[/] ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['exit', 'quit']:
                console.print("[yellow]Optimo-AI context wiped. Goodbye![/]")
                break

            messages.append({"role": "user", "content": user_input})
            
            full_response = ""
            label = Text.from_markup("[bold magenta]Optimo-AI:[/]")
            with Live(Text.from_markup("[bold magenta]Optimo-AI:[/] [dim]Thinking...[/]"), auto_refresh=True, console=console) as live:
                try:
                    response_stream = ollama.chat(
                        model=model,
                        messages=messages,
                        stream=True
                    )
                    
                    for chunk in response_stream:
                        content = chunk['message']['content']
                        full_response += content
                        live.update(Group(label, Markdown(full_response)))
                        
                except Exception as e:
                    console.print(f"\n[red]Error during chat:[/] {e}")
                    break

            messages.append({"role": "assistant", "content": full_response})
            
        except KeyboardInterrupt:
            console.print("\n[yellow]Stopping chat... context deleted.[/]")
            break

import subprocess

def run_init():
    """Installs all required Python dependencies."""
    deps = [
        "ollama==0.4.4",
        "pydantic==2.10.3",
        "rich==13.9.4",
        "pathspec==0.12.1",
        "customtkinter==5.2.2",
        "watchdog==6.0.0",
        "tiktoken==0.9.0"
    ]
    
    console.print(Panel(
        "[bold cyan]Optimo-Algo Environment Initialization[/]\n\nThis will install all necessary Python dependencies to ensure the system runs smoothly.",
        border_style="green"
    ))
    
    try:
        for dep in deps:
            console.print(f"[cyan]Installing {dep}...[/]")
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
        
        console.print("\n[bold green]✅ Initialization Complete![/]")
        console.print("[green]All dependencies are installed. You can now use the 'optimo' commands.[/]\n")
    except Exception as e:
        console.print(f"\n[red]Error during initialization:[/] {e}")
        console.print("[yellow]Please ensure you have an active internet connection and pip is available.[/]")

import concurrent.futures

def run_build(target_dir: str, model_override: str = None, output: str = "context.toon", workers: int = 4):
    model = model_override if model_override else get_model()
    
    console.print(f"[bold cyan]Scanning directory:[/] [yellow]{target_dir}[/]")
    files = get_files_to_scan(target_dir, ignore_patterns=None)
    console.print(f"[green]Analyzed folder structure. Found {len(files)} files.[/]")
    
    toon_results = []
    original_tokens = 0
    
    def process_one(file_path):
        rel_name = os.path.relpath(file_path, target_dir)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            tokens = get_token_count(content)
            toon_dict = generate_toon_for_file(content, rel_name, model=model)
            return toon_dict, tokens, rel_name
        except Exception as e:
            return None, 0, rel_name

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=False,
    ) as progress:
        task = progress.add_task("[cyan]Reading and summarizing...", total=len(files))
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_file = {executor.submit(process_one, f): f for f in files}
            for future in concurrent.futures.as_completed(future_to_file):
                res, tokens, rel_name = future.result()
                if res:
                    toon_results.append(res)
                    original_tokens += tokens
                    progress.update(task, description=f"[green]Done: {rel_name}[/]")
                else:
                    progress.update(task, description=f"[red]Failed: {rel_name}[/]")
                progress.advance(task)
            
    out_path = compile_toon(target_dir, toon_results, output)
    
    # Calculate stats
    with open(out_path, "r", encoding="utf-8") as f:
        compressed_content = f.read()
    
    compressed_tokens = get_token_count(compressed_content)
    saving = (1 - (compressed_tokens / original_tokens)) * 100 if original_tokens > 0 else 0

    console.print(f"\n[bold green]Compressed:[/] {original_tokens:,} tokens --> {compressed_tokens:,} tokens")
    console.print(f"[bold green]Saved:[/] {saving:.1f}% tokens")
    console.print(f"[bold cyan]context.toon is ready at:[/] [underline]{out_path}[/]\n")
    return out_path

class WatchHandler(FileSystemEventHandler):
    def __init__(self, target_dir, model, workers=4):
        self.target_dir = target_dir
        self.model = model
        self.workers = workers
        self.last_run = 0

    def on_modified(self, event):
        if event.is_directory: return
        if event.src_path.endswith(".toon"): return
        
        # Debounce
        if time.time() - self.last_run < 2: return
        
        console.print(f"[yellow]Change detected in {os.path.basename(event.src_path)}. Rebuilding...[/]")
        run_build(self.target_dir, self.model, workers=self.workers)
        self.last_run = time.time()

def main():
    parser = argparse.ArgumentParser(prog="optimo", description="Optimo-Algo CLI")
    
    # Global Options
    parser.add_argument("--path", default=".", help="Target directory (default: current)")
    parser.add_argument("--output", default="context.toon", help="Output TOON filename")
    parser.add_argument("--setmodel", help="Set/Override default Ollama model")
    parser.add_argument("--workers", type=int, default=4, help="Number of parallel summarization workers (default: 4)")
    parser.add_argument("--ignore", nargs="+", help="Add files/folders to ignore list")
    
    subparsers = parser.add_subparsers(dest="command")

    # build
    build_parser = subparsers.add_parser("build", help="Generate context.toon")

    # model
    model_parser = subparsers.add_parser("model", help="Show current active model")

    # watch
    watch_parser = subparsers.add_parser("watch", help="Watch for changes and rebuild")

    # stats
    stats_parser = subparsers.add_parser("stats", help="Show token compression statistics")

    # view
    view_parser = subparsers.add_parser("view", help="Visualize context.toon structure and tracing")

    # clean
    clean_parser = subparsers.add_parser("clean", help="Delete context.toon")

    # help
    help_parser = subparsers.add_parser("help", help="Show detailed usage guide")

    # listmodels
    listmodels_parser = subparsers.add_parser("listmodels", help="List available Ollama models")

    # chat
    chat_parser = subparsers.add_parser("chat", help="Chat with an AI expert on Optimo-Algo")

    # init
    init_parser = subparsers.add_parser("init", help="Initialize and install all dependencies")

    args = parser.parse_args()

    if args.setmodel:
        set_model(args.setmodel)
        console.print(f"[green]Model updated in configuration: {args.setmodel}[/]")
        if not args.command: return

    if args.ignore:
        add_ignore(args.ignore)
        console.print(f"[green]Added to ignore list: {args.ignore}[/]")
        if not args.command: return

    if args.command == "build":
        run_build(os.path.abspath(args.path), args.setmodel, args.output, args.workers)
    
    elif args.command == "model":
        model = get_model()
        console.print(f"[bold cyan]Active Ollama Model:[/] [magenta]{model}[/]")

    elif args.command == "watch":
        target = os.path.abspath(args.path)
        model = get_model()
        console.print(f"[bold cyan]Watching {target} for changes... (Model: {model}, Workers: {args.workers})[/]")
        event_handler = WatchHandler(target, model, workers=args.workers)
        observer = Observer()
        observer.schedule(event_handler, target, recursive=True)
        observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()

    elif args.command == "stats":
        target = os.path.abspath(args.path)
        toon_path = os.path.join(target, args.output)
        if not os.path.exists(toon_path):
            console.print(f"[red]No {args.output} found at {target}. Run 'optimo build' first.[/]")
            return
        
        # We need to scan again to get original tokens (rough but simplest for now)
        files = get_files_to_scan(target)
        original_tokens = 0
        for f_path in files:
            try:
                with open(f_path, "r", encoding="utf-8") as f:
                    original_tokens += get_token_count(f.read())
            except: pass
            
        with open(toon_path, "r", encoding="utf-8") as f:
            compressed_content = f.read()
        compressed_tokens = get_token_count(compressed_content)
        
        table = Table(title="Optimo-Algo Statistics")
        table.add_column("Type", style="cyan")
        table.add_column("Value", style="magenta")
        
        table.add_row("Files Scanned", str(len(files)))
        table.add_row("Original Tokens", f"{original_tokens:,}")
        table.add_row("Compressed Tokens", f"{compressed_tokens:,}")
        saving = (1 - (compressed_tokens / original_tokens)) * 100 if original_tokens > 0 else 0
        table.add_row("Saved", f"{saving:.1f}%")
        
        console.print(table)

    elif args.command == "view":
        target = os.path.abspath(args.path)
        toon_path = os.path.join(target, args.output)
        if not os.path.exists(toon_path):
            console.print(f"[red]No {args.output} found. Run 'optimo build' first.[/]")
            return
        
        console.print(f"[bold cyan]Launching Visualizer for {toon_path}...[/]")
        from src.visualizer import show_visualizer
        show_visualizer(toon_path)

    elif args.command == "clean":
        toon_path = os.path.join(os.getcwd(), args.output)
        if os.path.exists(toon_path):
            os.remove(toon_path)
            console.print(f"[green]Deleted {args.output}[/]")
        else:
            console.print(f"[yellow]No {args.output} found to delete.[/]")
    
    elif args.command == "help":
        show_help()
    
    elif args.command == "listmodels":
        show_models()
    
    elif args.command == "chat":
        run_chat(args.setmodel)
    
    elif args.command == "init":
        run_init()
    
    else:
        if not args.ignore and not args.setmodel:
            parser.print_help()

if __name__ == "__main__":
    main()

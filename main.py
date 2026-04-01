import argparse
import os
from typing import List

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.scanner import get_files_to_scan
from src.llm import generate_toon_for_file
from src.compiler import compile_toon

console = Console()

def main():
    parser = argparse.ArgumentParser(description="Optimo-Algo: Local Codebase TOON Compressor")
    parser.add_argument("path", help="The absolute or relative path to the directory you want to scan")
    parser.add_argument("--model", default="qwen2.5:1.5b", help="The Ollama model to use for generating summaries. Defaults to qwen2.5:1.5b for speed.")
    parser.add_argument("--output", default="context.toon", help="The output TOON file name")
    
    args = parser.parse_args()
    
    target_dir = os.path.abspath(args.path)
    
    if not os.path.isdir(target_dir):
        console.print(f"[bold red]Error:[/] The path '{target_dir}' is not a valid directory.")
        return
        
    console.print(f"[bold green]Starting Optimo-Algo[/] [cyan]v1.0[/]")
    console.print(f"Target: [yellow]{target_dir}[/]")
    console.print(f"Model: [magenta]{args.model}[/]\n")
    
    # 1. Scanning
    with console.status(f"[cyan]Scanning directory {target_dir} for source files...[/]") as status:
        files = get_files_to_scan(target_dir)
        console.print(f"[green]✓ Found {len(files)} scannable files.[/]")
        
    if not files:
        console.print("[yellow]No valid files found to scan. Exiting.[/]")
        return
        
    toon_results = []
    
    # 2. LLM Summarization
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=False,
    ) as progress:
        task = progress.add_task("[cyan]Processing files with local LLM...", total=len(files))
        
        for file_path in files:
            # We want to give it the relative file name for cleaner TOON output
            rel_name = os.path.relpath(file_path, target_dir)
            progress.update(task, description=f"[cyan]Parsing: [yellow]{rel_name}[/]...")
            
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    
                toon_dict = generate_toon_for_file(content, rel_name, model=args.model)
                toon_results.append(toon_dict)
                
            except Exception as e:
                console.print(f"[red]Error reading file {file_path}: {e}[/]")
                
            progress.advance(task)
            
    # 3. Compilation
    with console.status("[magenta]Compiling TOON object graph...[/]") as status:
        out_path = compile_toon(target_dir, toon_results, args.output)
        
    console.print(f"\n[bold green]Success![/] Codebase successfully compressed into [bold cyan]{args.output}[/].")
    console.print(f"Path: [underline]{out_path}[/]")

if __name__ == "__main__":
    main()

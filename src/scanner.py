import os
import re
import pathspec
from src.config import get_extra_ignores

def extract_imports(file_content: str, filename: str, project_root: str) -> list[str]:
    """
    Extracts import statements from a Python file and normalizes them to relative file paths.
    Returns a list of imported file paths (e.g., ['src/llm.py', 'src/config.py']).
    """
    imports = []
    
    # Match: from X import Y, import X, from X import *
    import_patterns = [
        r'^from\s+([\w\.]+)\s+import',  # from module import X
        r'^import\s+([\w\.]+)',          # import module
    ]
    
    for line in file_content.splitlines():
        line = line.strip()
        if line.startswith('#') or not line:
            continue
            
        for pattern in import_patterns:
            match = re.match(pattern, line)
            if match:
                module = match.group(1)
                # Skip standard library and third-party (don't contain dots or start with standard names)
                if '.' in module or module not in ['sys', 'os', 'json', 're', 'time', 'logging', 'threading', 'concurrent', 'argparse', 'pathspec', 'ollama', 'tiktoken', 'watchdog', 'rich', 'customtkinter']:
                    # Convert module path to file path (src.llm -> src/llm.py)
                    file_path = module.replace('.', '/') + '.py'
                    # Only add if it looks like a local import
                    if file_path.startswith('src/') or not '/' in file_path:
                        imports.append(file_path)
                break
    
    return list(set(imports))  # Remove duplicates

def get_files_to_scan(directory_path: str, ignore_patterns: list[str] = None):
    """
    Recursively scans the directory, skipping ignored files, 
    and returns a list of absolute paths pointing to source code.
    """
    if ignore_patterns is None:
         # Default reasonable ignores
         ignore_patterns = [
             ".git/", "node_modules/", "venv/", ".venv/", "__pycache__/", 
             "*.pyc", "*.jpg", "*.png", "*.mp4", "*.exe", ".env",
             "release/", ".gitignore", "dist-electron/", "dist/",
             "context.toon", ".optimo-algo.json"
         ]
         # Add user-defined ignores from config
         ignore_patterns.extend(get_extra_ignores())
         
    # We can use pathspec like .gitignore parsing for robust matching
    spec = pathspec.PathSpec.from_lines(pathspec.patterns.GitWildMatchPattern, ignore_patterns)
    
    scannable_files = []
    
    for root, dirs, files in os.walk(directory_path):
        # Filter directories in-place to prevent walking down ignored trees
        dirs[:] = [d for d in dirs if not spec.match_file(os.path.join(os.path.relpath(root, directory_path), d) + "/")]
        
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, directory_path)
            
            # Skip if matched by ignore pattern
            if spec.match_file(rel_path):
                continue
                
            scannable_files.append(file_path)
            
    return scannable_files

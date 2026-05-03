import ollama
import json
import logging
import time
import re


def repair_json(malformed_json: str) -> str:
    """
    Attempts to repair common JSON formatting issues from LLM output.
    """
    # Remove control characters and common issues
    fixed = malformed_json.replace('\t', ' ')
    fixed = re.sub(r',\s*}', '}', fixed)  # Remove trailing commas before }
    fixed = re.sub(r',\s*]', ']', fixed)  # Remove trailing commas before ]
    
    # Try to fix unterminated strings by finding unclosed quotes at line end
    lines = fixed.split('\n')
    for i, line in enumerate(lines):
        quote_count = line.count('"') - (line.count('\\"'))
        if quote_count % 2 == 1:  # Odd number of quotes = unterminated
            # Add closing quote
            lines[i] = line.rstrip(',') + '"'
    
    fixed = '\n'.join(lines)
    return fixed.strip()


SYSTEM_PROMPT = """You are a technical code analyzer. 
TASK: Extract logical structure and high-level briefs from code.
RESPONSE: Output ONLY valid JSON with keys "s", "c", "m".
RULES: 
1. Use ultra-compact "Agent-to-Agent" language for "s":
   - No articles (a, an, the). Omit "it", "this", "the".
   - Use only base verb forms.
   - Combine related words into CamelCase (e.g., "sendPrompt", "processFile").
   - Drop vowels ONLY if the word remains easily recognizable.
   - NEVER drop vowels from technical names, classes, or functions.
   - Example: "It utilizes AI and sends it the prompt" -> "utilAI sendPrompt".
2. Be extremely brief.
3. If empty, return []."""


def extract_imports_from_code(file_content: str) -> list[str]:
    """
    Comprehensive import extractor for Python, JS, TS, JSX, and TSX.
    This is the GROUND TRUTH for dependency graph edges - it never delegates
    to the LLM. Fast, regex-only, runs before any LLM call.

    Returns raw import paths as written in code (relative or absolute-style).
    Resolution against the actual file tree happens in compiler.py.
    """
    imports = []

    PYTHON_STDLIB = {
        'sys', 'os', 'json', 're', 'time', 'logging', 'threading', 'concurrent',
        'argparse', 'pathspec', 'typing', 'collections', 'functools', 'itertools',
        'math', 'random', 'datetime', 'io', 'abc', 'copy', 'enum', 'dataclasses',
        'subprocess', 'shutil', 'glob', 'traceback', 'inspect', 'hashlib', 'base64',
        'urllib', 'http', 'socket', 'struct', 'ctypes', 'weakref', 'contextlib'
    }
    THIRD_PARTY = {
        'ollama', 'tiktoken', 'watchdog', 'rich', 'customtkinter', 'pydantic',
        'flask', 'fastapi', 'django', 'sqlalchemy', 'requests', 'httpx', 'aiohttp',
        'numpy', 'pandas', 'PIL', 'cv2', 'torch', 'tensorflow', 'sklearn'
    }

    # Strip multi-line comments / block comments first to avoid false matches
    # Remove /* ... */ style block comments
    clean = re.sub(r'/\*.*?\*/', '', file_content, flags=re.DOTALL)
    # Remove Python triple-quoted strings only if they span, to avoid stripping docstrings in middle
    # (keeping it simple: just work line-by-line below)

    lines = clean.splitlines()

    # Join continued lines for multi-line JS imports: `import {\n  X,\n  Y\n} from './Z'`
    joined = re.sub(r'\}\s*from', '} from', clean)

    # --- Python ---
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue

        # from src.module import X
        m = re.match(r'^from\s+([\w\.]+)\s+import', stripped)
        if m:
            module = m.group(1)
            top = module.split('.')[0]
            if top not in PYTHON_STDLIB and top not in THIRD_PARTY:
                # Convert dot-notation to path
                file_path = module.replace('.', '/') + '.py'
                imports.append(file_path)
            continue

        # import src.module or import module
        m = re.match(r'^import\s+([\w\.]+)', stripped)
        if m:
            module = m.group(1)
            top = module.split('.')[0]
            if top not in PYTHON_STDLIB and top not in THIRD_PARTY:
                file_path = module.replace('.', '/') + '.py'
                imports.append(file_path)
            continue

    # --- JS / TS (work on joined content to handle multi-line imports) ---
    # Static: import ... from 'path'
    for m in re.finditer(r'\bimport\b[^(][^;]*?\bfrom\s+[\'"]([^\'"]+)[\'"]', joined):
        path = m.group(1)
        # Keep relative and @-alias paths (resolve @-alias in compiler)
        if path.startswith('.') or path.startswith('@/'):
            imports.append(path)

    # export { X } from 'path'  (re-exports)
    for m in re.finditer(r'\bexport\b[^;]*?\bfrom\s+[\'"]([^\'"]+)[\'"]', joined):
        path = m.group(1)
        if path.startswith('.') or path.startswith('@/'):
            imports.append(path)

    # Dynamic: import('path') or require('path')
    for m in re.finditer(r'(?:import|require)\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)', joined):
        path = m.group(1)
        if path.startswith('.') or path.startswith('@/'):
            imports.append(path)

    # Side-effect only: import 'path'
    for m in re.finditer(r"\bimport\s+['\"]([^'\"]+)['\"]", joined):
        path = m.group(1)
        if path.startswith('.') or path.startswith('@/'):
            imports.append(path)

    return list(set(imports))


def extract_classes_and_functions(file_content: str) -> dict:
    """
    Fallback parser to extract classes and functions from Python code directly.
    Used when LLM JSON parsing fails.
    """
    classes = []
    functions = []
    
    for line in file_content.splitlines():
        line = line.strip()
        
        # Match: class ClassName
        if line.startswith('class '):
            match = re.match(r'class\s+(\w+)', line)
            if match:
                classes.append(match.group(1))
        
        # Match: def function_name (at module level or after class)
        elif line.startswith('def '):
            match = re.match(r'def\s+(\w+)\s*\(', line)
            if match:
                functions.append(match.group(1))
    
    return {"c": classes, "m": functions}


def generate_toon_for_file(file_content: str, filename: str, model: str = "gemma3:1b", focus: str = None, retries: int = 3) -> dict:
    """
    Sends file to Ollama for TOON summarization using chunked processing for large files.
    """
    CHUNK_SIZE = 250
    lines = file_content.splitlines()
    num_lines = len(lines)
    
    # Extract imports globally (local regex, very fast)
    imports = extract_imports_from_code(file_content)
    
    # Create chunks
    if num_lines <= CHUNK_SIZE:
        chunks = [file_content]
    else:
        chunks = ['\n'.join(lines[i:i+CHUNK_SIZE]) for i in range(0, num_lines, CHUNK_SIZE)]
    
    all_summaries = []
    all_classes = set()
    all_methods = set()
    
    focus_block = f"\n        5. CRITICAL FOCUS: {focus}\n" if focus else ""
    
    for i, chunk_content in enumerate(chunks):
        segment_info = f" (Part {i+1}/{len(chunks)})" if len(chunks) > 1 else ""
        
        prompt = f"""<CODE_SEGMENT>
File: {filename}
{segment_info}
{chunk_content}
</CODE_SEGMENT>

        <TASK>
        1. Synthesize an "Agent-to-Agent" technical brief (CamelCase, no articles, base verbs) for the code above. Store in "s".
        2. Extract all class names into "c". 
        3. Extract all function/method names into "m".
        4. Output strict JSON only.{focus_block}
        </TASK>"""

        success = False
        for attempt in range(retries + 1):
            try:
                response = ollama.chat(
                    model=model, 
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ], 
                    format="json", 
                    options={
                        "num_predict": 300,
                        "temperature": 0.0
                    }
                )
                
                content = response['message']['content'].strip()
                
                if '```json' in content:
                    content = content.split('```json')[1].split('```')[0].strip()
                elif '```' in content:
                    content = content.split('```')[1].split('```')[0].strip()
                
                if attempt > 0: content = repair_json(content)
                
                data = json.loads(content)
                
                s = data.get("s", f"Logic segment {i+1}")
                all_summaries.append(s if not segment_info else f"[{i*CHUNK_SIZE}-{min((i+1)*CHUNK_SIZE, num_lines)}]: {s}")
                
                all_classes.update(data.get("c", []))
                all_methods.update(data.get("m", []))
                
                success = True
                break
                
            except Exception as e:
                if attempt < retries:
                    time.sleep(1.0) # Longer backoff
                    continue
        
        if not success:
            # Deterministic forced fallback instead of "unavailable"
            fallback = extract_classes_and_functions(chunk_content)
            c_count = len(fallback.get("c", []))
            m_count = len(fallback.get("m", []))
            forced_summary = f"def {c_count}Cls {m_count}Func"
            
            all_summaries.append(f"[{i*CHUNK_SIZE}-{min((i+1)*CHUNK_SIZE, num_lines)}]: {forced_summary}" if segment_info else forced_summary)
            all_classes.update(fallback.get("c", []))
            all_methods.update(fallback.get("m", []))

    return {
        "f": filename,
        "s": all_summaries if len(all_summaries) > 1 else (all_summaries[0] if all_summaries else "Empty file"),
        "c": list(all_classes),
        "m": list(all_methods),
        "i": imports
    }

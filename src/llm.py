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
1. Use "caveman-language" for "s": NO VOWELS, no articles (a, an, the), use only one form of verb,and small and simple english words.
2. Be extremely brief. Just enough words to understand logic.
3. If empty, return []."""

def extract_imports_from_code(file_content: str) -> list[str]:
    """
    Simple import extraction from Python code.
    Returns normalized local imports only (src/module.py format).
    """
    imports = []
    stdlib = {'sys', 'os', 'json', 're', 'time', 'logging', 'threading', 'concurrent', 
              'argparse', 'pathspec', 'typing', 'collections', 'functools', 'itertools'}
    thirdparty = {'ollama', 'tiktoken', 'watchdog', 'rich', 'customtkinter', 'pydantic'}
    
    for line in file_content.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        # from src.module import X
        match = re.match(r'^from\s+([\w\.]+)\s+import', line)
        if match:
            module = match.group(1)
            if module.startswith('src.'):
                file_path = module.replace('.', '/') + '.py'
                imports.append(file_path)
            continue
        
        # import module
        match = re.match(r'^import\s+([\w\.]+)', line)
        if match:
            module = match.group(1).split('.')[0]
            if module.startswith('src'):
                file_path = module.replace('.', '/') + '.py'
                imports.append(file_path)
    
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


def generate_toon_for_file(file_content: str, filename: str, model: str = "gemma3:1b", retries: int = 1) -> dict:
    """
    Sends file to Ollama for TOON summarization using chunked processing for large files.
    """
    CHUNK_SIZE = 200
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
    
    for i, chunk_content in enumerate(chunks):
        segment_info = f" (Part {i+1}/{len(chunks)})" if len(chunks) > 1 else ""
        
        # INVERTED PROMPT: Code then Instruction
        prompt = f"""<CODE_SEGMENT>
File: {filename}
{segment_info}
{chunk_content}
</CODE_SEGMENT>

        <TASK>
        1. Synthesize a caveman-style technical brief (NO VOWELS, no articles, one verb form) for the code above. Store in "s".
        2. Extract all class names into "c". 
        3. Extract all function/method names into "m".
        4. Output strict JSON only.
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
                        "num_predict": 256,
                        "temperature": 0.0
                    }
                )
                
                content = response['message']['content'].strip()
                
                # Clean and parse JSON
                if '```json' in content:
                    content = content.split('```json')[1].split('```')[0].strip()
                elif '```' in content:
                    content = content.split('```')[1].split('```')[0].strip()
                
                if attempt > 0: content = repair_json(content)
                
                data = json.loads(content)
                
                # Extract results
                s = data.get("s", f"Code segment {i+1}")
                all_summaries.append(s if not segment_info else f"[{i*CHUNK_SIZE}-{min((i+1)*CHUNK_SIZE, num_lines)}]: {s}")
                
                all_classes.update(data.get("c", []))
                all_methods.update(data.get("m", []))
                
                success = True
                break
                
            except Exception as e:
                if attempt < retries:
                    time.sleep(0.5)
                    continue
        
        if not success:
            # Fallback for this specific chunk
            fallback = extract_classes_and_functions(chunk_content)
            all_summaries.append(f"[{i*CHUNK_SIZE}-{min((i+1)*CHUNK_SIZE, num_lines)}]: Summary unavailable (fallback)")
            all_classes.update(fallback.get("c", []))
            all_methods.update(fallback.get("m", []))

    # Final result
    return {
        "f": filename,
        "s": all_summaries if len(all_summaries) > 1 else (all_summaries[0] if all_summaries else "No summary"),
        "c": list(all_classes),
        "m": list(all_methods),
        "i": imports
    }



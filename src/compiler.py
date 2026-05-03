import json
import os
import posixpath
import time

# Extensions to try when resolving an import without one
_RESOLVE_EXTS = [".ts", ".tsx", ".js", ".jsx", ".py", ".mts", ".cts"]


def resolve_import(importing_file: str, import_path: str, file_map: dict) -> str | None:
    """
    Resolves an import path to a key in file_map.

    Handles:
    - Absolute-style local paths: 'src/utils' → 'src/utils.ts'
    - Relative paths: './utils', '../services/hermes'
    - Directory index files: './components' → 'src/components/index.tsx'
    - All common web + Python extensions
    - Python dot-notation: 'src.config' → 'src/config.py'

    Returns the matching key in file_map, or None if unresolved.
    """
    # Normalize backslashes
    import_path = import_path.replace("\\", "/")

    # Python dot-notation: src.config -> src/config.py
    if "." in import_path and not import_path.startswith(".") and "/" not in import_path:
        candidate = import_path.replace(".", "/") + ".py"
        if candidate in file_map:
            return candidate

    # Resolve relative paths against the importing file's directory
    if import_path.startswith("."):
        base_dir = posixpath.dirname(importing_file)
        resolved = posixpath.normpath(posixpath.join(base_dir, import_path)).replace("\\", "/")
    else:
        # Already an absolute-style path (e.g., 'src/utils', '@/components/Header')
        # Strip leading @ aliases
        if import_path.startswith("@/"):
            import_path = "src/" + import_path[2:]
        resolved = import_path

    # Direct match (already has extension)
    if resolved in file_map:
        return resolved

    # Try appending known extensions
    for ext in _RESOLVE_EXTS:
        candidate = resolved + ext
        if candidate in file_map:
            return candidate

    # Try as a directory with index files
    for ext in _RESOLVE_EXTS:
        candidate = resolved + "/index" + ext
        if candidate in file_map:
            return candidate

    return None


def compile_toon(project_path: str, file_structures: list[dict], output_file: str = "context.toon"):
    """
    Takes the array of parsed TOON dictionaries from multiple files and nests them
    under the root directory to form a single cohesive TOON map of the codebase.
    Also builds a dependency graph showing which files call/import which other files.
    """

    base_dir = os.path.basename(os.path.normpath(project_path))

    # file_map: normalized path -> structure
    # used_by_map: normalized path -> list of files that import it
    file_map = {}
    used_by_map = {}

    # First pass: normalize all paths and populate maps
    for structure in file_structures:
        if structure and "f" in structure:
            filename = structure["f"].replace("\\", "/")
            structure["f"] = filename
            file_map[filename] = structure
            used_by_map[filename] = []

    # Second pass: resolve imports and build reverse dependency edges
    for structure in file_structures:
        if structure and "f" in structure:
            src_file = structure["f"]
            raw_imports = structure.get("i", [])
            resolved_imports = []

            for raw in raw_imports:
                resolved = resolve_import(src_file, raw, file_map)
                if resolved:
                    resolved_imports.append(resolved)
                    if src_file not in used_by_map[resolved]:
                        used_by_map[resolved].append(src_file)
                # else: external/unresolvable import, silently drop it

            # Overwrite "i" with only the resolved, local imports
            structure["i"] = resolved_imports

    # Third pass: attach used_by lists to each structure
    for structure in file_structures:
        if structure and "f" in structure:
            structure["ub"] = used_by_map.get(structure["f"], [])

    # --- Intelligence / Reasoning Layer ---
    importance_scores = {}
    hubs = []
    isolated = []

    for fname, structure in file_map.items():
        fan_in = len(used_by_map.get(fname, []))
        fan_out = len(structure.get("i", []))
        score = (fan_in * 2) + fan_out
        importance_scores[fname] = score

        # Hub: imported by 3+ files
        if fan_in >= 3:
            hubs.append(fname)

        # Truly isolated: NO edges at all after resolution
        # (not just "isolated because the graph was broken")
        if fan_in == 0 and fan_out == 0:
            isolated.append(fname)

    # Critical path: top 20% by importance (min 1 file)
    sorted_files = sorted(importance_scores.items(), key=lambda x: x[1], reverse=True)
    threshold_idx = max(1, len(sorted_files) // 5)
    critical_path = [f[0] for f in sorted_files[:threshold_idx] if f[1] > 0]

    analysis = {
        "importance": importance_scores,
        "hubs": hubs,
        "critical_path": critical_path,
        "isolated": isolated,
        "timestamp": time.time()
    }

    # Build nested directory tree for the visualizer sidebar
    project_tree = {}
    for structure in file_structures:
        if structure and "f" in structure:
            path_parts = structure["f"].split("/")
            curr = project_tree
            for part in path_parts[:-1]:
                if part not in curr:
                    curr[part] = {}
                curr = curr[part]
            curr[path_parts[-1]] = "FILE"

    toon_map = {
        "d": base_dir,
        "f": [],
        "tree": project_tree,
        "analysis": analysis
    }

    for structure in file_structures:
        if structure:
            toon_map["f"].append(structure)

    toon_map["deps"] = {
        "graph": used_by_map,
        "map": {
            fname: {"i": file_map[fname].get("i", []), "ub": file_map[fname].get("ub", [])}
            for fname in file_map
        }
    }

    # Write TOON: one file per line for readability + token efficiency
    with open(os.path.join(project_path, output_file), "w", encoding="utf-8") as f:
        f.write(
            '{"d":' + json.dumps(base_dir) +
            ',"tree":' + json.dumps(project_tree) +
            ',"analysis":' + json.dumps(analysis) +
            ',"f":[\n'
        )
        for i, entry in enumerate(toon_map["f"]):
            comma = "," if i < len(toon_map["f"]) - 1 else ""
            f.write(f'  {json.dumps(entry, separators=(",", ":"))}{comma}\n')
        f.write('],"deps":' + json.dumps(toon_map["deps"], separators=(',', ':')) + '}')

    return os.path.join(project_path, output_file)

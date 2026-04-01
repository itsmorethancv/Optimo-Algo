import json
import os

def compile_toon(project_path: str, file_structures: list[dict], output_file: str = "context.toon"):
    """
    Takes the array of parsed TOON dictionaries from multiple files and nests them
    under the root directory to form a single cohesive TOON map of the codebase.
    Also builds a dependency graph showing which files call/import which other files.
    """
    
    # Extract the base folder name
    base_dir = os.path.basename(os.path.normpath(project_path))
    
    # Build reverse dependency map: for each file, track which files use it
    file_map = {}  # filename -> file structure
    used_by_map = {}  # filename -> list of files that import it
    
    # First pass: create file map and initialize used_by tracking
    for structure in file_structures:
        if structure and "f" in structure:
            filename = structure["f"]
            file_map[filename] = structure
            used_by_map[filename] = []
    
    # Second pass: build reverse dependencies
    for structure in file_structures:
        if structure and "f" in structure:
            filename = structure["f"]
            imports = structure.get("i", [])
            
            # For each import, add current file to its "used_by" list
            for imported_file in imports:
                if imported_file in used_by_map:
                    if filename not in used_by_map[imported_file]:
                        used_by_map[imported_file].append(filename)
    
    # Third pass: add "used_by" information to each structure
    for structure in file_structures:
        if structure and "f" in structure:
            filename = structure["f"]
            structure["ub"] = used_by_map.get(filename, [])
    
    # Build a nested tree structure for folder/file visualization
    project_tree = {}
    for structure in file_structures:
        if structure and "f" in structure:
            path_parts = structure["f"].replace("\\", "/").split("/")
            curr = project_tree
            for part in path_parts[:-1]:
                if part not in curr: curr[part] = {}
                curr = curr[part]
            curr[path_parts[-1]] = "FILE"

    # The root of our TOON structure
    toon_map = {
        "d": base_dir,
        "f": [],
        "tree": project_tree
    }
    
    for structure in file_structures:
        if structure:  # if not empty
            toon_map["f"].append(structure)
    
    # Add a global dependency index at the root level
    toon_map["deps"] = {
        "graph": used_by_map,  # which files use which
        "map": {fname: {"i": file_map[fname].get("i", []), "ub": file_map[fname].get("ub", [])} 
                for fname in file_map}
    }
    
    # Custom formatted JSON export: One line per file for human readability
    # but still compact for token efficiency.
    with open(os.path.join(project_path, output_file), "w", encoding="utf-8") as f:
        f.write('{"d":' + json.dumps(base_dir) + ',"tree":' + json.dumps(project_tree) + ',"f":[\n')
        
        for i, entry in enumerate(toon_map["f"]):
            comma = "," if i < len(toon_map["f"]) - 1 else ""
            # Dump entry with compact separators
            line = json.dumps(entry, separators=(',', ':'))
            f.write(f'  {line}{comma}\n')
            
        f.write('],"deps":' + json.dumps(toon_map["deps"], separators=(',', ':')) + '}')
        
    return os.path.join(project_path, output_file)

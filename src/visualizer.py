import customtkinter as ctk
import tkinter as tk
import json
import os
import math

class ToonVisualizer(ctk.CTk):
    def __init__(self, toon_data: dict, file_path: str):
        super().__init__()
        self.toon_data = toon_data
        self.file_path = file_path
        
        self.normalize_paths()
        
        self.title(f"Optimo-Algo | Nodal Visualizer - {os.path.basename(file_path)}")
        self.geometry("1100x800")

        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        # Interaction state
        self.drag_item = None
        self.drag_data = {"x": 0, "y": 0, "name": None}
        self.nodes = {}  # filename -> (x, y)
        self.node_ids = {} # filename -> list of canvas ids (oval, text)

        # Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(1, weight=1)

        # Header
        self.header = ctk.CTkFrame(self, height=60, corner_radius=0)
        self.header.grid(row=0, column=0, columnspan=2, sticky="ew")
        self.header_label = ctk.CTkLabel(self.header, text="Nodal Architecture Graph", 
                                         font=ctk.CTkFont(size=20, weight="bold"))
        self.header_label.pack(side="left", padx=20, pady=10)

        # Trace Switch
        self.trace_var = tk.BooleanVar(value=True)
        self.trace_switch = ctk.CTkSwitch(self.header, text="Trace Dependencies", 
                                          variable=self.trace_var, command=self.update_view)
        self.trace_switch.pack(side="right", padx=20, pady=10)

        # Sidebar (Tree)
        self.sidebar = ctk.CTkScrollableFrame(self, width=280, label_text="Project Tree")
        self.sidebar.grid(row=1, column=0, padx=(20, 10), pady=20, sticky="nsew")
        
        # Main Canvas (Graph)
        self.canvas_frame = ctk.CTkFrame(self)
        self.canvas_frame.grid(row=1, column=1, padx=(10, 20), pady=20, sticky="nsew")
        self.canvas_frame.grid_columnconfigure(0, weight=1)
        self.canvas_frame.grid_rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(self.canvas_frame, bg="#1a1a1a", highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")

        self.setup_ui()
        
        # Bind resize
        self.canvas.bind("<Configure>", self.on_resize)

    def normalize_paths(self):
        if "f" in self.toon_data:
            for entry in self.toon_data["f"]:
                if "f" in entry: entry["f"] = entry["f"].replace("\\", "/")
                if "i" in entry: entry["i"] = [i.replace("\\", "/") for i in entry["i"]]
        
        if "deps" in self.toon_data and "map" in self.toon_data["deps"]:
            new_map = {}
            for k, v in self.toon_data["deps"]["map"].items():
                nk = k.replace("\\", "/")
                new_map[nk] = {
                    "i": [i.replace("\\", "/") for i in v.get("i", [])],
                    "ub": [u.replace("\\", "/") for u in v.get("ub", [])]
                }
            self.toon_data["deps"]["map"] = new_map

    def setup_ui(self):
        # Build Sidebar Tree from pre-calculated toon structure
        tree = self.toon_data.get("tree", {})
        files_info = {f["f"]: f for f in self.toon_data.get("f", [])}
        root_name = self.toon_data.get("d", "Project")
        self.populate_sidebar(tree, 0, root_name, files_info)

    def populate_sidebar(self, tree, indent, label_text, files_info):
        self.add_sidebar_row(label_text, indent, is_dir=True)
        for name, sub in sorted(tree.items(), key=lambda x: (x[1] == "FILE", x[0])):
            if sub == "FILE":
                full_path = self.find_full_path(name, files_info)
                entry = files_info.get(full_path, {})
                self.add_sidebar_row(name, indent + 1, is_dir=False)
                for cls in entry.get("c", []): self.add_sidebar_row(cls, indent + 2, icon="🔷")
                for mth in entry.get("m", []): self.add_sidebar_row(mth, indent + 2, icon="⚙️")
            else:
                self.populate_sidebar(sub, indent + 1, name, files_info)

    def find_full_path(self, filename, files_info):
        for path in files_info:
            if path.endswith(filename): return path
        return filename

    def add_sidebar_row(self, text, indent, is_dir=False, icon=None):
        if not icon: icon = "📁" if is_dir else "📄"
        label = ctk.CTkLabel(self.sidebar, text=f"{'  ' * indent}{icon} {text}", anchor="w", font=ctk.CTkFont(size=12))
        label.pack(fill="x", padx=5, pady=1)

    def on_resize(self, event):
        if not self.nodes:
            self.calculate_initial_layout()
        self.draw_graph()

    def calculate_initial_layout(self):
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        if width <= 1: return

        tree = self.toon_data.get("tree", {})
        self.nodes = {}
        
        # Determine levels
        levels = {} # level -> [list of nodes]
        def traverse(sub_tree, level, parent_path):
            if level not in levels: levels[level] = []
            for name, sub in sub_tree.items():
                full_path = f"{parent_path}/{name}".strip("/")
                if sub == "FILE":
                    levels[level].append(full_path)
                else:
                    traverse(sub, level + 1, full_path)
        
        traverse(tree, 1, "")
        
        # Position nodes hierarchically
        y_step = 140
        for level, nodes in levels.items():
            count = len(nodes)
            x_step = width / (count + 1)
            for i, node_path in enumerate(nodes):
                self.nodes[node_path] = (x_step * (i + 1), 80 + (level-1) * y_step)

    def draw_graph(self):
        self.canvas.delete("all")
        
        # Draw Arrows first (so they are behind nodes)
        if self.trace_var.get():
            deps_map = self.toon_data.get("deps", {}).get("map", {})
            for src_file, info in deps_map.items():
                if src_file in self.nodes:
                    sx, sy = self.nodes[src_file]
                    for imp in info.get("i", []):
                        if imp in self.nodes:
                            tx, ty = self.nodes[imp]
                            self.draw_arrow(sx, sy, tx, ty, color="#3498db")

        # Draw Nodes and bind events
        self.node_ids = {}
        for fname, (x, y) in self.nodes.items():
            tag = f"node_{fname.replace('/', '_')}"
            
            # Shadow/Ring
            self.canvas.create_oval(x-15, y-15, x+15, y+15, fill="#2c3e50", outline="#34495e", width=4, tags=(tag, "node"))
            # Core
            node_id = self.canvas.create_oval(x-12, y-12, x+12, y+12, fill="#1f538d", outline="white", width=2, tags=(tag, "node"))
            # Text
            text_id = self.canvas.create_text(x, y+28, text=os.path.basename(fname), fill="white", 
                                             font=("Arial", 11, "bold"), tags=(tag, "node"))
            
            self.node_ids[fname] = (node_id, text_id)
            
            # Rebind drag & move to these specific tags
            self.canvas.tag_bind(tag, "<ButtonPress-1>", lambda e, name=fname: self.on_node_press(e, name))
            self.canvas.tag_bind(tag, "<B1-Motion>", self.on_node_motion)

    def on_node_press(self, event, name):
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y
        self.drag_data["name"] = name

    def on_node_motion(self, event):
        fname = self.drag_data["name"]
        if not fname: return

        # Calculate delta
        dx = event.x - self.drag_data["x"]
        dy = event.y - self.drag_data["y"]
        
        # Update node data
        cx, cy = self.nodes[fname]
        self.nodes[fname] = (cx + dx, cy + dy)
        
        # Update drag reference
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y
        
        # Fast Redraw
        self.draw_graph()

    def draw_arrow(self, x1, y1, x2, y2, color="#3498db"):
        angle = math.atan2(y2 - y1, x2 - x1)
        offset = 18
        nx1, ny1 = x1 + offset * math.cos(angle), y1 + offset * math.sin(angle)
        nx2, ny2 = x2 - offset * math.cos(angle), y2 - offset * math.sin(angle)
        self.canvas.create_line(nx1, ny1, nx2, ny2, fill=color, arrow=tk.LAST, width=2, 
                                arrowshape=(12,14,6), smooth=True)

    def update_view(self):
        self.draw_graph()

def show_visualizer(toon_path):
    try:
        with open(toon_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        app = ToonVisualizer(data, toon_path)
        app.mainloop()
    except Exception as e:
        import traceback
        print(f"Error launching visualizer: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        show_visualizer(sys.argv[1])
    else:
        print("Usage: python visualizer.py <path_to_toon>")

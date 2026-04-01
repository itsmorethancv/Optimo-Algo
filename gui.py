import customtkinter as ctk
from tkinter import filedialog
import threading
import os
import json
import logging
from src.config import get_model, set_model
from src.scanner import get_files_to_scan
from src.llm import generate_toon_for_file
from src.compiler import compile_toon

# Set appearance and theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class OptimoGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.default_model = get_model()

        self.title("Optimo-Algo | TOON Compressor")
        self.geometry("800x600")

        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        # Header
        self.header_label = ctk.CTkLabel(self, text="Optimo-Algo Encoder", font=ctk.CTkFont(size=24, weight="bold"))
        self.header_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        # Controls Frame
        self.controls_frame = ctk.CTkFrame(self)
        self.controls_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.controls_frame.grid_columnconfigure(1, weight=1)

        self.select_btn = ctk.CTkButton(self.controls_frame, text="Select Target Folder", command=self.select_folder)
        self.select_btn.grid(row=0, column=0, padx=10, pady=10)

        self.folder_label = ctk.CTkLabel(self.controls_frame, text="No folder selected", text_color="gray")
        self.folder_label.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        self.model_label = ctk.CTkLabel(self.controls_frame, text="Ollama Model:")
        self.model_label.grid(row=0, column=2, padx=10, pady=10)

        # Assuming the user usually has standard models, Qwen2.5 is excellent for this
        self.model_entry = ctk.CTkEntry(self.controls_frame, width=150, placeholder_text=self.default_model)
        self.model_entry.insert(0, self.default_model)
        self.model_entry.grid(row=0, column=3, padx=10, pady=10)

        self.run_btn = ctk.CTkButton(self.controls_frame, text="▶ Run Compression", fg_color="green", hover_color="darkgreen", command=self.start_processing)
        self.run_btn.grid(row=0, column=4, padx=10, pady=10)

        # Progress Bar
        self.progress_bar = ctk.CTkProgressBar(self)
        self.progress_bar.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.progress_bar.set(0)

        # Log Terminal
        self.log_textbox = ctk.CTkTextbox(self, font=("Consolas", 12))
        self.log_textbox.grid(row=3, column=0, padx=20, pady=(0, 20), sticky="nsew")

        self.selected_path = None

    def log(self, message: str):
        # Insert log message safely from thread
        def _update():
            self.log_textbox.insert(ctk.END, message + "\n")
            self.log_textbox.see(ctk.END)
        self.after(0, _update)

    def select_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.selected_path = folder_selected
            self.folder_label.configure(text=self.selected_path, text_color="white")
            self.log(f"[*] Target folder set to: {self.selected_path}")

    def start_processing(self):
        if not self.selected_path:
            self.log("[!] Error: No folder selected.")
            return

        # Disable button during run
        self.run_btn.configure(state="disabled")
        self.progress_bar.set(0)
        self.log("\n[====================================]")
        self.log("[*] Starting Optimo Compression Sequence...")
        
        selected_model = self.model_entry.get().strip()
        if not selected_model:
            selected_model = "qwen2.5:0.5b"
            
        self.log(f"[*] Expected Ollama Model: {selected_model}")

        # Run the heavy processing in a separate thread so the GUI doesn't freeze
        thread = threading.Thread(target=self.process_files, args=(self.selected_path, selected_model))
        thread.start()

    def process_files(self, target_dir, model_name):
        self.log(f"[*] Scanning {target_dir} for scannable files...")
        files = get_files_to_scan(target_dir)

        if not files:
            self.log("[!] No scannable files found. Check your directory or ignore lists.")
            self.after(0, lambda: self.run_btn.configure(state="normal"))
            return

        self.log(f"[+] Found {len(files)} files to process.")
        toon_results = []
        total_files = len(files)
        completed = 0

        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            def process_one(f_path):
                rel_name = os.path.relpath(f_path, target_dir)
                try:
                    with open(f_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    return generate_toon_for_file(content, rel_name, model=model_name), rel_name
                except Exception as e:
                    self.log(f"[!] Error processing {rel_name}: {e}")
                    return None, rel_name

            future_to_file = {executor.submit(process_one, f): f for f in files}
            for future in concurrent.futures.as_completed(future_to_file):
                res, rel_name = future.result()
                if res:
                    toon_results.append(res)
                    self.log(f"[+] Successfully extracted TOON for {rel_name}")
                
                completed += 1
                self.after(0, lambda val=float(completed) / total_files: self.progress_bar.set(val))

        self.log("[*] Compiling all generated structures into single JSON TOON tree...")
        
        try:
            out_file = "context.toon"
            out_path = compile_toon(target_dir, toon_results, out_file)
            self.log(f"\n[bold green]SUCCESS: Codebase compressed to {out_path}[/]")
            
            # Print a quick preview
            with open(out_path, "r", encoding="utf-8") as f:
                self.log("\n--- 'context.toon' Preview ---")
                preview = f.read()[:500] 
                self.log(preview + ("..." if len(preview) == 500 else ""))
                
        except Exception as e:
            self.log(f"[!] Failed to compile TOON: {e}")

        # Restore run button
        self.after(0, lambda: self.run_btn.configure(state="normal"))
        self.log("[*] Ready.")

if __name__ == "__main__":
    app = OptimoGUI()
    app.mainloop()

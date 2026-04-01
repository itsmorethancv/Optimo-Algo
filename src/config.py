import json
import os

CONFIG_FILE = ".optimo-algo.json"

DEFAULT_CONFIG = {
    "model": "gemma3:1b",
    "extra_ignores": []
}

def get_config_path():
    # Store config in the current working directory for per-project settings
    return os.path.join(os.getcwd(), CONFIG_FILE)

def load_config():
    path = get_config_path()
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                config = json.load(f)
                # Merge with defaults to ensure all keys exist
                return {**DEFAULT_CONFIG, **config}
        except:
            return DEFAULT_CONFIG
    return DEFAULT_CONFIG

def save_config(config):
    path = get_config_path()
    with open(path, "w") as f:
        json.dump(config, f, indent=4)

def set_model(model_name: str):
    config = load_config()
    config["model"] = model_name
    save_config(config)

def add_ignore(patterns: list[str]):
    config = load_config()
    existing = set(config.get("extra_ignores", []))
    for p in patterns:
        existing.add(p)
    config["extra_ignores"] = list(existing)
    save_config(config)

def get_model():
    return load_config().get("model", "qwen2.5:0.5b")

def get_extra_ignores():
    return load_config().get("extra_ignores", [])

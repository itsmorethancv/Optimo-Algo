# 🚀 Optimo-Algo

**Optimo-Algo** is a technical bridging layer for AI coding agents. It scans your codebase, distilling logic into a lightweight `.toon` token-compressed representation, which can save up to **90% in token usage** when feeding context to local or cloud LLMs.

---

## ⚡ One-Command Installation

To install Optimo-Algo globally on your machine, copy and paste this command:

```bash
pip install git+https://github.com/itsmorethancv/Optimo-Algo.git
```

---

## 🛠️ Quick Start

Once installed, follow these three simple steps:

1. **Initialize**: Run this in your project folder to ensure all dependencies are perfectly synced.
   ```bash
   optimo init
   ```

2. **Build your Context**: Generate your first `context.toon` file.
   ```bash
   optimo build
   ```

3. **Watch for Changes**: Keep your context updated automatically as you code.
   ```bash
   optimo watch
   ```

---

## 📖 Available Commands

| Command | Description |
| :--- | :--- |
| `optimo build` | Scans the codebase and creates `context.toon`. |
| `optimo watch` | Live-monitors files and updates the context on save. |
| `optimo stats` | Shows token compression efficiency. |
| `optimo view` | Launches the Nodal Architecture Visualizer. |
| `optimo chat` | Start an AI tutor session about Optimo-Algo. |
| `optimo listmodels`| Shows available Ollama models. |
| `optimo help` | Displays the full CLI guide. |

---

## ⚙️ Configuration
You can set a default model globally so you don't have to specify it every time:
```bash
optimo --setmodel llama3
```

---

*Made with ❤️ by [itsmorethancv](https://github.com/itsmorethancv)*

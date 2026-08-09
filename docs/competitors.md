# Competitor Comparison — jiuwenswarm-jupyterlab

This document maps the competitive landscape for AI-in-notebook tools as of mid-2025.

---

## Direct Competitors

### Jupyter AI (official JupyterLab extension)

**Made by:** Project Jupyter (official)
**Install:** `pip install jupyter-ai`
**GitHub:** [jupyterlab/jupyter-ai](https://github.com/jupyterlab/jupyter-ai)

The most direct competitor. An official JupyterLab extension with a sidebar chat panel and `%%ai` cell magic. Supports many LLM providers (OpenAI, Anthropic, Cohere, Hugging Face, local models via Ollama) through a LangChain backend.

| Feature | Jupyter AI | jiuwenswarm-jupyterlab |
|---|---|---|
| Cell magic (`%%ai` / `%%jiuwen`) | Yes | Yes |
| Sidebar chat panel | Yes | Yes |
| Swarm map — visualize parallel agents | No | Yes |
| Multi-agent teams | No — single agent only | Yes — full team mode |
| Skill system (persistent, per-task instructions) | No | Yes |
| Memory across sessions | No | Yes |
| Agent reads live notebook variables | Limited | Yes — full namespace access |
| Pinned variables always injected into context | No | Yes (`%jiuwen_pin`) |
| Agent inserts cells into notebook | No | Yes (`insert_notebook_cell`) |
| Agent reads cell outputs | No | Yes (`read_notebook_cell`) |
| Export conversation history to Markdown | No | Yes (`%jiuwen_export`) |
| Continue session with trimmed context | No | Yes (`%jiuwen_replay`) |
| Multi-kernel support (several notebooks open) | No | Yes |
| Session list grouped by notebook | No | Yes |
| Session filter / search | No | Yes |
| Live cost display in status bar | No | Yes |
| Slack / Discord / Telegram channel integration | No | Yes (via JiuwenSwarm channels) |
| Works in Google Colab | Partially | Yes |
| Works in Kaggle Notebooks | No | Yes |
| Requires running server | No | No |
| Open source | Yes | Yes |

**Summary:** Jupyter AI is the obvious comparison point for any reviewer. jiuwenswarm-jupyterlab wins on multi-agent capability, skill system, memory, notebook-native tools, and conversation management. Jupyter AI wins on LLM provider breadth and being the official first-party extension.

---

### GitHub Copilot in VS Code Notebooks

**Made by:** GitHub / Microsoft
**Access:** Via VS Code with Jupyter extension + GitHub Copilot subscription

GitHub Copilot adds AI completions and a chat panel to VS Code's Jupyter notebook support. It is not a JupyterLab extension — it only works inside VS Code.

| Feature | Copilot Notebooks | jiuwenswarm-jupyterlab |
|---|---|---|
| Works in JupyterLab (browser) | No — VS Code only | Yes |
| Works in Colab / Kaggle | No | Yes |
| Code completions (inline ghost text) | Yes | No (not planned) |
| Chat panel | Yes | Yes |
| Multi-agent | No | Yes |
| Reads notebook variables | Limited | Yes |
| Session export / replay | No | Yes |
| Requires subscription | Yes ($10–19/month) | No |

**Summary:** Not a true JupyterLab competitor — different environment. For users locked into VS Code Notebooks, Copilot is the alternative. For users who actually use JupyterLab or browser-based notebooks, this is not a realistic alternative.

---

## Partial Competitors (adjacent tools)

### ChatGPT Code Interpreter / Advanced Data Analysis

**Made by:** OpenAI
**Access:** ChatGPT Plus / Team / Enterprise subscription

A browser-based sandboxed Python environment where GPT-4 writes and runs code, reads files, and produces outputs. Not a Jupyter extension — a standalone product.

| Feature | ChatGPT Code Interpreter | jiuwenswarm-jupyterlab |
|---|---|---|
| Works inside your existing notebook | No — separate product | Yes |
| Access to your live variables and data | No — you upload files | Yes |
| Multi-agent | No | Yes |
| Persistent sessions across restarts | Limited | Yes |
| Works with your own LLM API | No | Yes |
| Private data stays local | No — sent to OpenAI | Yes (can run fully local) |

**Summary:** Serves a similar user goal (data science help from AI) but completely different model. ChatGPT Code Interpreter requires uploading data and leaving your notebook environment. jiuwenswarm-jupyterlab runs inside your kernel with your live data.

---

### Continue.dev

**Made by:** Continue
**Install:** VS Code / JetBrains extension
**GitHub:** [continuedev/continue](https://github.com/continuedev/continue)

An open-source AI coding assistant for VS Code and JetBrains. Has some notebook support via VS Code Jupyter extension. Supports custom models and a slash-command system.

| Feature | Continue.dev | jiuwenswarm-jupyterlab |
|---|---|---|
| Works in JupyterLab (browser) | No | Yes |
| Multi-agent teams | No | Yes |
| Swarm visualization | No | Yes |
| Custom commands / skills | Yes (slash commands) | Yes (skills system) |
| Works with local models | Yes | Yes |

**Summary:** Primarily an IDE tool with limited notebook presence. Not a direct threat in the JupyterLab market.

---

### Marimo

**Made by:** Marimo
**Install:** `pip install marimo`
**Website:** [marimo.io](https://marimo.io)

A next-generation Python notebook format where cells are reactive (like a spreadsheet — change one cell, dependents re-run). Has built-in AI features for generating and editing cells.

| Feature | Marimo | jiuwenswarm-jupyterlab |
|---|---|---|
| Works in existing `.ipynb` notebooks | No — different format | Yes |
| JupyterLab compatible | No | Yes |
| Multi-agent | No | Yes |
| AI cell generation | Yes (single-shot) | Yes (via agent) |
| Reactive cell execution | Yes | No |

**Summary:** A different product category — a new notebook format rather than an extension. Requires users to move away from `.ipynb` and standard JupyterLab. Not a direct competitor for users who want AI inside their existing notebooks.

---

## Feature Gap Summary

Features that **no competitor has** and jiuwenswarm-jupyterlab provides:

| Feature | Status |
|---|---|
| Multi-agent teams running inside a Jupyter kernel | Implemented |
| Live swarm map showing parallel agents in JupyterLab | Implemented |
| Agent reads live Python variables directly from kernel | Implemented |
| Agent inserts runnable code cells into the notebook | Implemented |
| Pinned variables always injected into agent context | Implemented |
| Export full conversation history to Markdown | Implemented |
| Continue session in fresh context via replay | Implemented |
| Multi-kernel support — several notebooks open at once | Implemented |
| Session list grouped by notebook with filter | Implemented |
| Live session cost display in JupyterLab status bar | Implemented |
| Persistent skill system scoped to agent tasks | Implemented (via JiuwenSwarm) |
| Session memory that persists across notebook restarts | Implemented |
| Works in Colab, Kaggle, and remote Jupyter servers | Implemented |

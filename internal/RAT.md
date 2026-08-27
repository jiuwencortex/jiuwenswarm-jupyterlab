# Requirements Analysis — jiuwenswarm-jupyterlab

---

## Source of Demand

- **Proactive Planning** — New Features / Technology Innovation
- **Product Requirements** — JiuwenSwarm Product / Developer Reach & Notebook Integration

---

## Demand Background

### WHY

Data scientists, ML engineers, and researchers spend most of their working time inside
Jupyter notebooks. Their primary tool for exploration, modelling, and analysis is the
notebook — not a browser chat window, not an IDE.

Accessing JiuwenSwarm's agent capabilities today requires leaving the notebook: opening
a web UI, switching windows, copying outputs back. This context switch breaks the
notebook-centric workflow and prevents JiuwenSwarm from acting on live kernel data
(variables, DataFrames, model objects, cell outputs) without the user manually
copy-pasting content into a chat box.

The goal is to bring JiuwenSwarm directly into the notebook kernel: the agent can read
live variables, insert code cells, and stream responses into the cell output area —
all without the user leaving the notebook or starting any external process.

A secondary goal is to cover environments without the JupyterLab frontend (Google Colab,
Kaggle Notebooks, classic Jupyter Notebook, VS Code Notebooks, PyCharm) where browser
extensions and sidebar panels are not available. These environments represent a large
portion of active data science usage and must be supported with the same core
capabilities.

### WHEN

New feature, proactively planned. No commercial project deadline.
Targeted for delivery as part of the JiuwenSwarm platform release.

### WHAT

The feature is delivered as two components:

---

**Component 1 — Python package (`jiuwenswarm_jupyter`)**

Works in any Jupyter environment: JupyterLab, classic Notebook, Google Colab, Kaggle,
VS Code Notebooks, PyCharm Jupyter.

| Capability | Magic / API | Description |
|---|---|---|
| Query the agent | `%%jiuwen` / `%jiuwen` | Send a question or instruction; stream the response below the cell |
| Error debugging | `%jiuwen_error` | Forward the last notebook exception to the agent automatically |
| Mode selection | `--mode agent / code / team / code.team` | Single agent, code-focused, or multi-agent team |
| Named sessions | `--session NAME` | Maintain separate conversation threads in the same notebook |
| Context injection | automatic | Agent sees live variables, DataFrames, recent cell outputs, imported packages |
| Pinned variables | `%jiuwen_pin` / `%jiuwen_unpin` | Always inject specific variables, even with `--no-context` |
| Session management | `%jiuwen_clear` | Reset a session without restarting the kernel |
| History export | `%jiuwen_export` | Save conversation history to a Markdown file |
| Session replay | `%jiuwen_replay` | Continue in a fresh session with recent context replayed |
| Configuration | `%jiuwen_config` | Set per-notebook defaults (mode, timeout, model) |
| Widgets panel | `%jiuwen_panel` | ipywidgets GUI panel for environments where magic syntax is inconvenient |
| Embedded chat UI | `%jiuwen_chat` | Full themed chat interface (chat.html) embedded in cell output; comm-connected to kernel; primary interface for Colab / Kaggle / classic Notebook |
| Read variables | `read_variable(name)` | Agent reads any Python object from the kernel namespace |
| Read cells | `read_notebook_cell(index)` | Agent reads source and output of any executed cell |
| Insert cells | `insert_notebook_cell(source)` | Agent inserts a runnable code cell into the notebook |
| Rewrite cells | `replace_notebook_cell(index, source)` | Agent rewrites an existing cell; diff shown before applying |

---

**Component 2 — JupyterLab frontend extension (`@jiuwenswarm/jupyterlab`)**

Requires JupyterLab 4+ in the browser. Bundled into the Python wheel; no separate npm install.

| Capability | Component | Description |
|---|---|---|
| Sidebar chat panel | `ChatPanel.ts` | Persistent chat UI (chat.html iframe) in the JupyterLab sidebar; stays open across notebook tabs |
| Session browser | `SessionListPanel.ts` | Lists sessions per notebook with filter input; groups by kernel when multiple notebooks are open |
| Swarm map | `SwarmMapPanel.ts` | Live visualisation of multi-agent team activity |
| Status bar | `StatusIndicator.ts` | Connection state, session cost, active notebook label |
| Multi-kernel support | `WsClient.ts` | One comm connection per open notebook; tab-switch routes to the correct kernel |
| In-notebook cell insertion | `comm_handler.py` ↔ TypeScript | Agent inserts cells directly; no copy-paste required |
| Diff dialog | TypeScript | Apply/Cancel dialog when agent rewrites an existing cell |

---

### Requirement Type

☑ **Functionality** (excluding Trust)
☑ **Operation and Maintenance Methods** (multi-environment deployment)

---

## Needs Assessment

### Requirement Decomposition

| Sub-requirement | Scope |
|---|---|
| Cell magic + Python API | `magics/jiuwen.py`, `magics/error.py`, `client.py`, `session.py`, `context.py`, `display.py` |
| Notebook introspection tools | `notebook_tools.py` |
| Session history (export / replay / pin) | `client.py`, `magics/session/`, `config.py`, `context.py` |
| Embedded chat UI (`%jiuwen_chat`) | `magics/chat.py`, `packages/shared-webview/chat.html`, `pyproject.toml` force-include |
| JupyterLab sidebar panel | `packages/frontend/src/ChatPanel.ts`, `comm_handler.py` |
| Session list + filter | `SessionManager.ts`, `SessionListPanel.ts` |
| Swarm map | `SwarmMapPanel.ts`, `SwarmState.ts`, `SwarmStateManager.ts` |
| Multi-kernel support | `WsClient.ts`, `SessionManager.ts`, `index.ts` |
| Status bar | `StatusIndicator.ts` |

### Constraints

**No streaming to the cell output when sidebar is active:**
When the JupyterLab sidebar panel is connected, responses are rendered inside the
sidebar iframe. The cell output area remains blank for that exchange. Users who prefer
output in the cell should use `%%jiuwen` without the sidebar open.

**`%jiuwen_chat` requires `Jupyter.notebook.kernel.comm_manager`:**
The embedded chat UI (cell output iframe) bridges to the kernel using the classic
Jupyter JavaScript API (`Jupyter.notebook.kernel.comm_manager.new_comm`). This API is
available in Google Colab, Kaggle Notebooks, and classic Jupyter Notebook. It is not
available as a JavaScript global in JupyterLab 4+, where the sidebar panel is the
correct interface instead.

**`insert_notebook_cell` — actual insertion requires the sidebar:**
Without the JupyterLab frontend extension, the agent cannot insert cells directly.
The proposed cell source is displayed in the cell output area with a `# [jiuwen]` tag;
the user must copy it into a new cell manually.

**`replace_notebook_cell` — diff dialog requires the sidebar:**
Without the frontend extension, a coloured unified diff is rendered in the cell output
instead of an interactive Apply/Cancel dialog.

**chat.html — single copy, bundled at build time:**
`packages/shared-webview/chat.html` is the canonical source. It is bundled into the
Python wheel via hatchling `force-include` and placed at
`jiuwenswarm_jupyter/static/chat.html` inside the installed package. In development
(`pip install -e .`), `magics/chat.py` falls back to the source tree path automatically.
Keeping two manually maintained copies must be avoided.

**No streaming to messaging platforms:**
This integration does not include real-time streaming to external channels (Slack,
Telegram, etc.). That is the scope of the `connect/` module in the main OpenJiuwen
platform.

### Impact of Requirement Implementation on Existing Systems

**JiuWenSwarm (agent runtime):** No changes required. The integration imports
`JiuWenSwarm` as a library and calls its existing API. All agent modes, memory,
skills, and tool systems are unchanged.

**JupyterLab:** No changes to JupyterLab itself. The frontend extension uses the
standard JupyterLab plugin API and Jupyter comm protocol. Installs and uninstalls
cleanly.

**Existing notebook users:** No impact. Loading the extension is opt-in via
`%load_ext jiuwenswarm_jupyter`. Auto-load requires an explicit `ipython_config.py`
entry.

**Kernel performance:** Context injection reads `ip.user_ns` and cell history on
every `%%jiuwen` call. For notebooks with very large objects, context building may
add latency. The `--no-context` flag suppresses this. Pinned variables bypass the
full namespace sweep.

### External Dependencies

| Dependency | Reason | Version |
|---|---|---|
| `ipython` | Magic registration, cell/line magic API, `ip.user_ns` namespace access | ≥ 8.0 |
| `ipywidgets` | `%jiuwen_panel` ipywidgets control panel | ≥ 8.0 |
| `jiuwenswarm` | Agent runtime — `JiuWenSwarm` class, all agent modes | Current |
| JupyterLab | Frontend extension plugin system, Jupyter comm, IComm API | 4.x |
| Node.js + npm | TypeScript build toolchain (development / release only) | 18+ |
| `hatchling` | Python wheel build; `force-include` for chat.html bundling | ≥ 1.21 |

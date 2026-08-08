# Architecture — jiuwenswarm-jupyterlab

## Overview

`jiuwenswarm-jupyterlab` provides three layers on top of JiuwenSwarm:

1. **Phase 1 — Python package (`jiuwenswarm_jupyter`)** — in-process API and `%%jiuwen` cell magic. Works in any Jupyter environment (JupyterLab, classic Notebook, VS Code Notebooks, Google Colab, Kaggle).

2. **Phase 2 — JupyterLab frontend extension (`@jiuwenswarm/jupyterlab`)** — TypeScript sidebar panel with persistent chat UI and swarm map, embedded as iframes loaded from the shared-webview HTML files. Communication uses Jupyter comm (in-process, no external server).

3. **Phase 3 — Notebook-native tools** — `read_variable`, `read_notebook_cell`, `insert_notebook_cell` let the agent inspect and modify notebook state directly.

All three phases call the same in-process `JiuWenSwarm` facade; no external server or WebSocket is required.

---

## Project layout

```
jiuwenswarm-jupyterlab/
├── jiuwenswarm_jupyter/         Python package
│   ├── __init__.py              Extension entry point; wires Phase 1+2+3 on load
│   ├── magic.py                 %%jiuwen / %jiuwen cell magic           [Phase 1]
│   ├── client.py                JupyterSwarm wrapper around JiuWenSwarm [Phase 1]
│   ├── context.py               Notebook context extractor              [Phase 1]
│   ├── display.py               IPython streaming output renderer       [Phase 1]
│   ├── session.py               Session ID management + registry        [Phase 1]
│   ├── comm_handler.py          Kernel comm target + event streaming    [Phase 2]
│   └── notebook_tools.py        read_variable / read_notebook_cell /   [Phase 3]
│                                insert_notebook_cell
│
├── packages/
│   ├── shared-webview/          Copied from jiuwenswarm-ide + Jupyter bridge patch
│   │   ├── chat.html            Chat UI (vanilla JS, no build step)
│   │   ├── swarm_map.html       Swarm map visualisation
│   │   └── icon.svg
│   │
│   └── frontend/                TypeScript JupyterLab extension (Phase 2)
│       ├── src/
│       │   ├── index.ts         Extension entry point + plugin registration
│       │   ├── WsClient.ts      Kernel comm bridge (replaces WebSocket)
│       │   ├── SessionManager.ts Session registry
│       │   ├── protocol.ts      Shared message types
│       │   ├── NotebookContextCollector.ts  Active notebook context
│       │   ├── SwarmState.ts    State model for swarm map
│       │   ├── SwarmStateManager.ts  Live state updates from kernel
│       │   ├── ChatPanel.ts     Sidebar chat panel (iframe + bridge)
│       │   ├── SwarmMapPanel.ts Swarm map panel (iframe + postMessage)
│       │   └── StatusIndicator.ts  Status bar widget
│       ├── package.json
│       ├── tsconfig.json
│       └── webpack.config.js
│
├── docs/
├── pyproject.toml               Python package config (hatchling)
├── package.json                 npm workspace root
└── README.md
```

---

## Phase 1: In-process Python API

### Data flow

```
%%jiuwen cell magic
    │
    ▼
magic.py  ─── parse options ──► JupyterSwarm.run_sync()
                                        │
                    context.py ◄────────┤
                    (ip.user_ns,        │
                     history_manager)   │
                                        ▼
                              JiuWenSwarm.process_message_stream()
                                        │  (in same Python process)
                                        ▼
                             AsyncIterator[AgentResponseChunk]
                                        │
                                        ▼
                              display.py / StreamRenderer
                              (IPython display + update_display)
                                        │
                                        ▼
                              Cell output area (live-updating HTML)
```

### Session persistence

Each notebook kernel gets one `JupyterSwarm` instance stored in the IPython namespace as `_jiuwen`. Subsequent `%%jiuwen` cells in the same notebook continue the same conversation. Named sessions (`--session research`) create separate `JupyterSwarm` instances in a thread-safe registry.

### Context injection

Before each request, `context.py` extracts:
- All non-private variables from `ip.user_ns` with type summaries
- Pandas DataFrames: shape, dtypes, `.head(3)` preview
- NumPy arrays: shape and dtype
- Last 5 cell inputs from `ip.history_manager`

This is injected as a fenced block before the user query, so the agent understands the notebook state without the user explaining it.

### Async event loop handling

`JupyterSwarm.run_sync()` detects whether an event loop is already running (ipykernel runs inside asyncio) and applies `nest_asyncio` to allow `asyncio.run()` inside a running loop. If `nest_asyncio` is not installed, a thread is spawned with its own event loop.

---

## Phase 2: JupyterLab sidebar panel

### Architecture

The JupyterLab extension is a standard JupyterFrontEndPlugin that:
1. Registers a sidebar chat panel (iframe embedding `chat.html`)
2. Registers a main-area swarm map panel (iframe embedding `swarm_map.html`)
3. Adds a status bar indicator showing connection state and active agent count
4. Exposes command palette entries for opening panels and creating sessions

### Shared-webview reuse

`chat.html` and `swarm_map.html` are the same files used by the VS Code and JetBrains IDE plugins. They contain a bridge detection block that detects which host environment they are running in:

```javascript
function send(msg) {
  if (vscodeApi) {
    vscodeApi.postMessage(msg);         // VS Code
  } else if (window.__jb_send) {
    window.__jb_send(JSON.stringify(msg)); // JetBrains
  } else if (window.__jupyter_send) {
    window.__jupyter_send(JSON.stringify(msg)); // JupyterLab (added here)
  } else {
    console.warn('[webview] no bridge available, msg:', msg);
  }
}
```

`ChatPanel.ts` installs `window.__jupyter_send` on the iframe's `contentWindow` after the iframe loads. This function routes messages to `KernelCommClient.send()`, which sends them to the Python kernel via Jupyter comm.

Incoming events (from the Python kernel via comm) are forwarded to the iframe as `postMessage` calls, which the `window.addEventListener('message', ...)` handler in `chat.html` picks up.

### Kernel comm protocol

`comm_handler.py` registers the `jiuwenswarm` comm target when `load_ipython_extension` runs. It tries two registration paths to support all Jupyter versions:

```
1. comm package (JupyterLab 4+ / Jupyter 7+):
   comm.get_comm_manager().register_target("jiuwenswarm", handler)

2. ipykernel legacy (classic Notebook / older JupyterLab):
   kernel.comm_manager.register_target("jiuwenswarm", handler)
```

Once registered, the flow for each user message is:

```
TypeScript ChatPanel
    │  comm.send({ type: "send_message", query, mode, session_id })
    ▼
comm_handler._handle_send_message()
    │  builds full_query (with context if inject_context=True)
    │  calls JiuWenSwarm.process_message_stream()
    │
    ├─ chat.delta  → comm.send({ type: "chat.delta", delta: "..." })
    ├─ tool.call   → comm.send({ type: "tool.call", name: "...", args: {} })
    ├─ tool.result → comm.send({ type: "tool.result", result: "..." })
    ├─ team.*      → comm.send({ type: "team.member.spawned", ... })
    └─ chat.final  → comm.send({ type: "chat.final", text: "..." })
    ▼
TypeScript KernelCommClient
    │  forwards every event to ChatPanel via window.postMessage
    ▼
chat.html (iframe)
    │  handleHostMessage(event) — same handler as VS Code / JetBrains
    ▼
UI renders streamed response
```

The event schema is identical to the IDE WebSocket events, so `chat.html` and `swarm_map.html` require no changes.

Cancel is handled via `comm.send({ type: "cancel", session_id })` which calls `asyncio.Task.cancel()` on the running stream.

### Distribution

The extension is distributed as a Python package that bundles the built TypeScript frontend. The `pyproject.toml` `[tool.hatch.build.targets.wheel.shared-data]` section copies `packages/frontend/dist/` to `share/jupyter/labextensions/@jiuwenswarm/jupyterlab/`. JupyterLab discovers the extension automatically from that path.

---

## Phase 3: Notebook-native tools

`notebook_tools.py` provides three functions that operate directly on the live notebook kernel state.

### `read_notebook_cell(cell_index)`

Reads from `ip.history_manager.get_tail()` (execution history) and `ip.user_ns["Out"]` (output dict).  Returns a dict with `source`, `output`, and `line_number`.

### `read_variable(name)`

Reads from `ip.user_ns[name]`.  Dispatches to type-specific formatters:
- `DataFrame` → shape, dtypes, `.head(5)`, `.describe()`
- `ndarray` → shape, dtype, min/max/mean, first values
- `dict` / `list` → length + JSON preview
- anything else → `repr()` truncated to 3000 chars

### `insert_notebook_cell(source, cell_type, execute)`

Two paths:

```
Phase 2 active (JupyterLab sidebar connected):
    comm.create_comm("jiuwenswarm_cell_insert").open(payload)
    → TypeScript frontend receives comm_open message
    → uses JupyterLab notebook API to insert the cell
    → optionally executes it immediately

Phase 1 only (no sidebar):
    IPython.display.HTML renders the source as a formatted
    code block in the cell output area with a copy hint
```

### Tool schema

`TOOL_DEFINITIONS` in `notebook_tools.py` is a list of JSON Schema tool definitions matching the agent's tool-calling format. `get_dispatcher()` returns a `dict[name → callable]` for direct integration with `JiuWenSwarm`.

---

## Relation to jiuwenswarm-ide

| Concern | jiuwenswarm-ide | jiuwenswarm-jupyterlab |
|---|---|---|
| Transport | WebSocket (port 18092, E2AEnvelope) | Jupyter comm (in-process) |
| VS Code bridge | `vscodeApi.postMessage` | not applicable |
| JetBrains bridge | `window.__jb_send` / JCEF | not applicable |
| JupyterLab bridge | not applicable | `window.__jupyter_send` / postMessage |
| Shared-webview HTML | source | copied + bridge patch |
| Context collection | active editor file, workspace | notebook variables, cell history, imported packages |
| Session ID prefix | `vscode_*` / `jb_*` | `jupyter_*` |
| Agent API | `JiuWenSwarm` via WebSocket | `JiuWenSwarm` direct in-process |
| Notebook tools | not applicable | `read_variable`, `read_notebook_cell`, `insert_notebook_cell` |
| Cell insertion | diff/patch to file | comm → JupyterLab notebook API (Phase 2) or display block (Phase 1) |

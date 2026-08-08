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
│   ├── magic.py                 %%jiuwen / %jiuwen / %jiuwen_error /   [Phase 1]
│   │                            %jiuwen_clear
│   ├── config.py                JiuwenConfig dataclass + %jiuwen_config [Phase 1]
│   ├── widgets.py               ipywidgets panel + %jiuwen_panel magic  [Phase 1]
│   ├── client.py                JupyterSwarm wrapper around JiuWenSwarm [Phase 1]
│   ├── context.py               Notebook context extractor              [Phase 1]
│   ├── display.py               IPython streaming output renderer;      [Phase 1]
│   │                            markdown→HTML via `markdown` pkg or fallback
│   ├── session.py               Session ID, registry, restart recovery  [Phase 1]
│   ├── comm_handler.py          Kernel comm target + event streaming    [Phase 2]
│   └── notebook_tools.py        read_variable / read_notebook_cell /   [Phase 3]
│                                insert_notebook_cell / replace_notebook_cell
│                                (confirm_execute, diff dialog, cell tagging)
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
│       │   ├── SessionListPanel.ts  Session browser (sidebar, rank 501)
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

**Restart recovery:** On load, `session.py` checks `~/.jiuwenswarm/jupyter_sessions.json` for a previously saved session ID keyed by working directory (`os.getcwd()`). If found and younger than 30 days, the same session ID is restored so the agent can continue the conversation after a kernel restart. The session ID is saved every time a new default session is created.

### Per-notebook configuration

`config.py` provides `JiuwenConfig` — a dataclass storing per-notebook defaults (`mode`, `timeout`, `inject_context`, `model`). The `%jiuwen_config` magic lets users view or change these from any cell. The current config is stored in `_jiuwen_config` in the IPython namespace. Individual `%%jiuwen` flag overrides take precedence over config values.

### Error auto-forwarding (`%jiuwen_error`)

`magic.py` registers `%jiuwen_error` as a line magic. When called after an exception, it reads `sys.last_type`, `sys.last_value`, and `sys.last_traceback` to format the full traceback, retrieves the failing cell source from `ip.history_manager.get_tail(n=1)`, and sends the combined context to the default swarm session. An optional extra message on the same line is appended to the query.

### ipywidgets panel (`%jiuwen_panel`)

`widgets.py` provides `show_jiuwen_panel(ip=None)` — an optional ipywidgets UI. It displays mode/timeout/context controls and a query text area inside the cell output. `run_sync()` is called on the Send button click so output streams into the panel's `Output` widget. Requires `pip install ipywidgets`. Gracefully degrades (prints install instructions) when ipywidgets is absent. `register_panel_magic(ip)` registers the `%jiuwen_panel` line magic.

### Session clear (`%jiuwen_clear`)

`magic.py` registers `%jiuwen_clear` as a line magic. Called with no arguments, it calls `session.clear_session(None)`, which removes the current default session ID from the registry, then calls `get_default_swarm(ip)` to create a fresh `JupyterSwarm` with a new auto-generated session ID. The new instance replaces `ip.user_ns["_jiuwen"]` and a confirmation message prints the new session ID. Called with an argument (`%jiuwen_clear research`), it clears that named session only.

### Keyboard interrupt handling in Phase 1

Both `%%jiuwen` and `%jiuwen_error` wrap the `run_sync()` call in `try/except KeyboardInterrupt`. When the user presses Ctrl+C (kernel interrupt) while a cell is running, the exception is caught and `[JiuwenSwarm] Query cancelled.` is printed — the interrupt does not propagate and crash the kernel.

### Phase 1/2 status on load

`load_ipython_extension` in `__init__.py` calls `register_comm_target(ip)` and prints one of:
- `[JiuwenSwarm] Phase 2 active — JupyterLab comm connected.` when the comm target registered successfully (JupyterLab 4+ with frontend installed)
- `[JiuwenSwarm] Phase 1 mode — JupyterLab sidebar not detected. Cell insertion will show display blocks.` otherwise

### `JupyterSwarm` mode setter and instance timeout

`client.py` exposes a `mode` property setter and a `timeout` float attribute (default 300 s). Both are written by `%jiuwen_config` when the user changes settings, so configuration changes propagate to the live swarm instance without requiring a new session. `run()` uses `self.timeout` as the default when no per-call `timeout` kwarg is given.

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

The JupyterLab extension is a standard `JupyterFrontEndPlugin` that:
1. Registers a sidebar chat panel (iframe embedding `chat.html`, rank 500)
2. Registers a sidebar session list panel (`SessionListPanel`, rank 501)
3. Registers a main-area swarm map panel (iframe embedding `swarm_map.html`)
4. Adds a status bar indicator showing connection state and active agent count
5. Exposes command palette entries and keyboard shortcuts
6. Registers a `jiuwenswarm_cell_insert` comm target for agent-initiated cell insertion
7. Registers a `jiuwenswarm_cell_replace` comm target for agent-initiated cell rewrites with diff review

**Keyboard shortcuts** registered in `index.ts`:
- `Cmd/Ctrl+Shift+J` → `open-chat`
- `Cmd/Ctrl+Shift+N` → `new-session`

**`jiuwenswarm_cell_insert` comm target:** When the Python `insert_notebook_cell()` function runs in a Phase 2 environment, it opens a one-shot comm of this target name with a payload containing `source`, `cell_type`, `execute`, and `jiuwen_generated`. TypeScript receives this via `kernel.registerCommTarget()` and calls the `_handleCellInsert()` function, which uses `NotebookActions.insertBelow`, `setSource`, optional `changeCellType`, `setMetadata('jiuwen_generated', true)`, and optionally `NotebookActions.run()`.

**`jiuwenswarm_cell_replace` comm target:** When the Python `replace_notebook_cell()` function runs in a Phase 2 environment, it opens a one-shot comm with payload `{old_source, new_source, line_no}`. TypeScript `_handleCellReplace()` finds the matching cell by content (`old_source`), renders a before/after HTML diff inside a `showDialog` Widget body, and applies `sharedModel.setSource(new_source)` only if the user clicks Apply.

**Cell tagging:** Cells inserted via comm are tagged `cell.metadata.jiuwen_generated = true`. In Phase 1 environments (no frontend), the source is prepended with `# [jiuwen] Generated by JiuwenSwarm` so agent-generated code is identifiable in any environment.

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

`notebook_tools.py` provides four functions that operate directly on the live notebook kernel state.

### `read_notebook_cell(cell_index)`

Reads from `ip.history_manager.get_tail()` (execution history) and `ip.user_ns["Out"]` (output dict).  Returns a dict with `source`, `output`, and `line_number`.

### `read_variable(name)`

Reads from `ip.user_ns[name]`.  Dispatches to type-specific formatters:
- `DataFrame` → shape, dtypes, `.head(5)`, `.describe()`
- `ndarray` → shape, dtype, min/max/mean, first values
- `dict` / `list` → length + JSON preview
- anything else → `repr()` truncated to 3000 chars

### `insert_notebook_cell(source, cell_type, execute, confirm_execute)`

Two paths:

```
Phase 2 active (JupyterLab sidebar connected):
    _comm_insert() → comm.create_comm("jiuwenswarm_cell_insert").open(payload)
    Payload: { source, cell_type, execute, confirm_execute, jiuwen_generated: true }
    → TypeScript _handleCellInsert():
        NotebookActions.insertBelow() + sharedModel.setSource()
        if confirm_execute: showDialog("Run generated cell?") before executing
        if execute (and confirmed): NotebookActions.run()
        cell.model.setMetadata('jiuwen_generated', true)

Phase 1 only (no sidebar):
    _display_proposed_cell() renders the source as formatted HTML
    if confirm_execute and execute: input("Run? [y/N]") before notifying user
```

### `replace_notebook_cell(cell_index, new_source)`

Two paths:

```
Phase 2 active (JupyterLab sidebar connected):
    _comm_replace() → comm.create_comm("jiuwenswarm_cell_replace").open(payload)
    Payload: { old_source, new_source, line_no }
    → TypeScript _handleCellReplace():
        Find cell whose sharedModel.getSource().trim() === old_source.trim()
        Build before/after HTML diff (red old, green new) in a Lumino Widget
        showDialog("Apply cell rewrite?", body=diffWidget, [Cancel, Apply])
        On Apply: cell.sharedModel.setSource(new_source)

Phase 1 only (no sidebar):
    _display_diff() renders a coloured unified diff (difflib.unified_diff)
    as HTML in the cell output area — user applies the change manually
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
| Notebook tools | not applicable | `read_variable`, `read_notebook_cell`, `insert_notebook_cell`, `replace_notebook_cell` |
| Cell insertion | diff/patch to file | comm → JupyterLab notebook API (Phase 2) or display block (Phase 1) |
| Cell rewrite | diff/patch to file | comm → diff dialog → `sharedModel.setSource()` (Phase 2) or `difflib` HTML (Phase 1) |

# Architecture — jiuwenswarm-jupyterlab

## Overview

`jiuwenswarm-jupyterlab` integrates JiuwenSwarm into Jupyter environments across two layers:

- **Python kernel layer** (`jiuwenswarm_jupyter`) — cell magics, a Python API, notebook introspection tools, and a Jupyter comm handler. Works in any Jupyter environment: JupyterLab, classic Notebook, VS Code Notebooks, Google Colab, Kaggle.

- **JupyterLab frontend extension** (`@jiuwenswarm/jupyterlab`) — TypeScript sidebar panel with persistent chat UI, session browser, swarm map, and status bar indicator. Communicates with the Python layer via Jupyter comm; no external server or WebSocket is required.

Both layers call the same in-process `JiuWenSwarm` facade, which lives inside the notebook kernel process.

---

## Project layout

```
jiuwenswarm-jupyterlab/
├── jiuwenswarm_jupyter/         Python package
│   ├── __init__.py              Extension entry point; registers comm, magics, tools
│   ├── magic.py                 %%jiuwen / %jiuwen / %jiuwen_error /
│   │                            %jiuwen_clear / %jiuwen_export / %jiuwen_replay /
│   │                            %jiuwen_pin / %jiuwen_unpin
│   ├── config.py                JiuwenConfig dataclass + %jiuwen_config magic
│   ├── widgets.py               ipywidgets panel + %jiuwen_panel magic
│   ├── client.py                JupyterSwarm wrapper around JiuWenSwarm
│   ├── context.py               Notebook context extractor (variables, cells, packages)
│   ├── display.py               IPython streaming output renderer;
│   │                            markdown→HTML via `markdown` pkg or fallback
│   ├── session.py               Session ID, registry, restart recovery
│   ├── comm_handler.py          Kernel comm target + event streaming to frontend
│   └── notebook_tools.py        read_variable / read_notebook_cell /
│                                insert_notebook_cell / replace_notebook_cell
│
├── packages/
│   ├── shared-webview/          Copied from jiuwenswarm-ide + Jupyter bridge patch
│   │   ├── chat.html            Chat UI (vanilla JS, no build step)
│   │   ├── swarm_map.html       Swarm map visualisation
│   │   └── icon.svg
│   │
│   └── frontend/                TypeScript JupyterLab extension
│       ├── src/
│       │   ├── index.ts         Extension entry point + plugin registration
│       │   ├── WsClient.ts      Kernel comm bridge (one IComm per kernel)
│       │   ├── SessionManager.ts Session registry, partitioned by kernel
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

## Python kernel layer

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

### Session management

Each notebook kernel gets one `JupyterSwarm` instance stored in the IPython namespace as `_jiuwen`. Subsequent `%%jiuwen` cells in the same notebook continue the same conversation. Named sessions (`--session research`) create separate `JupyterSwarm` instances in a thread-safe registry.

**Restart recovery:** On load, `session.py` checks `~/.jiuwenswarm/jupyter_sessions.json` for a previously saved session ID keyed by working directory (`os.getcwd()`). If found and younger than 30 days, the same session ID is restored so the agent can continue the conversation after a kernel restart. The session ID is saved every time a new default session is created.

**Conversation history:** Each `JupyterSwarm` instance maintains `_history` — a list of `{timestamp, mode, query, response}` dicts appended after every successful `run()` call. Used by `%jiuwen_export` and `%jiuwen_replay`.

### Per-notebook configuration

`config.py` provides `JiuwenConfig` — a dataclass storing per-notebook defaults (`mode`, `timeout`, `inject_context`, `model`, `pinned_vars`). The `%jiuwen_config` magic lets users view or change these from any cell. The current config is stored in `_jiuwen_config` in the IPython namespace. Individual `%%jiuwen` flag overrides take precedence over config values.

### Error auto-forwarding (`%jiuwen_error`)

`magic.py` registers `%jiuwen_error` as a line magic. When called after an exception, it reads `sys.last_type`, `sys.last_value`, and `sys.last_traceback` to format the full traceback, retrieves the failing cell source from `ip.history_manager.get_tail(n=1)`, and sends the combined context to the default swarm session. An optional extra message on the same line is appended to the query.

### ipywidgets panel (`%jiuwen_panel`)

`widgets.py` provides `show_jiuwen_panel(ip=None)` — an optional ipywidgets UI. It displays mode/timeout/context controls and a query text area inside the cell output. `run_sync()` is called on the Send button click so output streams into the panel's `Output` widget. Requires `pip install ipywidgets`. Gracefully degrades (prints install instructions) when ipywidgets is absent. `register_panel_magic(ip)` registers the `%jiuwen_panel` line magic.

### Session clear (`%jiuwen_clear`)

`magic.py` registers `%jiuwen_clear` as a line magic. Called with no arguments, it calls `session.clear_session(None)`, which removes the current default session ID from the registry, then calls `get_default_swarm(ip)` to create a fresh `JupyterSwarm` with a new auto-generated session ID. The new instance replaces `ip.user_ns["_jiuwen"]` and a confirmation message prints the new session ID. Called with an argument (`%jiuwen_clear research`), it clears that named session only.

### Session export (`%jiuwen_export`)

`magic.py` registers `%jiuwen_export`. It reads `JupyterSwarm._history` — a list of `{timestamp, mode, query, response}` dicts appended after every successful `run()` call in `client.py` — and writes them to a markdown file in `os.getcwd()`. Supports an optional `--session NAME` flag to export named sessions.

### Session replay (`%jiuwen_replay`)

`magic.py` registers `%jiuwen_replay [N]`. It reads the last N entries from `JupyterSwarm._history`, formats them into a single context message, calls `session.clear_session()` to create a fresh default session, then sends the context message with `inject_context=False`. The new session inherits the key facts from the old conversation without carrying stale tool call state.

### Pinned variables (`%jiuwen_pin` / `%jiuwen_unpin`)

`config.py` adds a `pinned_vars: list` field to `JiuwenConfig`. `magic.py` registers `%jiuwen_pin` (appends names) and `%jiuwen_unpin` (removes names or clears all). `context.py` accepts a `pinned_vars` parameter in `build_context_block()`: pinned variables are extracted first via `_extract_pinned_variables()` into a dedicated **Pinned variables** section, and excluded from the normal `_extract_variables()` sweep to avoid duplication. `client.py` reads `cfg.pinned_vars` from `get_config(ip)` on every `run()` call. When `inject_context=False` but `pinned_vars` is non-empty, only the pinned section is injected.

### Keyboard interrupt handling

Both `%%jiuwen` and `%jiuwen_error` wrap the `run_sync()` call in `try/except KeyboardInterrupt`. When the user presses Ctrl+C (kernel interrupt) while a cell is running, the exception is caught and `[JiuwenSwarm] Query cancelled.` is printed — the interrupt does not propagate and crash the kernel.

### Status on load

`load_ipython_extension` in `__init__.py` calls `register_comm_target(ip)` and prints one of:
- `[JiuwenSwarm] Sidebar connected — JupyterLab comm active.` when the comm target registered successfully (JupyterLab 4+ with frontend installed)
- `[JiuwenSwarm] Running without sidebar — cell insertion will use display blocks.` otherwise

### `JupyterSwarm` mode setter and instance timeout

`client.py` exposes a `mode` property setter and a `timeout` float attribute (default 300 s). Both are written by `%jiuwen_config` when the user changes settings, so configuration changes propagate to the live swarm instance without requiring a new session. `run()` uses `self.timeout` as the default when no per-call `timeout` kwarg is given.

### Context injection

Before each request, `context.py` extracts:
- **Pinned variables** (always, even with `--no-context`) — from `cfg.pinned_vars`, rendered in a dedicated top section
- All non-private variables from `ip.user_ns` with type summaries (skipping any already pinned)
- Pandas DataFrames: shape, dtypes, `.head(3)` preview
- NumPy arrays: shape and dtype
- Last 5 cell inputs from `ip.history_manager`

This is injected as a fenced block before the user query, so the agent understands the notebook state without the user explaining it.

### Async event loop handling

`JupyterSwarm.run_sync()` detects whether an event loop is already running (ipykernel runs inside asyncio) and applies `nest_asyncio` to allow `asyncio.run()` inside a running loop. If `nest_asyncio` is not installed, a thread is spawned with its own event loop.

---

## JupyterLab frontend extension

### Plugin registration

The JupyterLab extension is a standard `JupyterFrontEndPlugin` that registers:
1. Sidebar chat panel (iframe embedding `chat.html`, rank 500)
2. Sidebar session list panel (`SessionListPanel`, rank 501)
3. Main-area swarm map panel (iframe embedding `swarm_map.html`)
4. Status bar indicator (connection state, cost, active kernel label)
5. Command palette entries and keyboard shortcuts
6. `jiuwenswarm_cell_insert` comm target for agent-initiated cell insertion
7. `jiuwenswarm_cell_replace` comm target for agent-initiated cell rewrites with diff review

**Keyboard shortcuts** registered in `index.ts`:
- `Cmd/Ctrl+Shift+J` → `open-chat`
- `Cmd/Ctrl+Shift+N` → `new-session`

### Cell comm targets

**`jiuwenswarm_cell_insert`:** When the Python `insert_notebook_cell()` function is called from a kernel connected to the JupyterLab sidebar, it opens a one-shot comm of this target name with a payload containing `source`, `cell_type`, `execute`, and `jiuwen_generated`. TypeScript receives this via `kernel.registerCommTarget()` and calls `_handleCellInsert()`, which uses `NotebookActions.insertBelow`, `setSource`, optional `changeCellType`, `setMetadata('jiuwen_generated', true)`, and optionally `NotebookActions.run()`.

**`jiuwenswarm_cell_replace`:** When the Python `replace_notebook_cell()` function is called from a kernel connected to the JupyterLab sidebar, it opens a one-shot comm with payload `{old_source, new_source, line_no}`. TypeScript `_handleCellReplace()` finds the matching cell by content, renders a before/after HTML diff inside a `showDialog` Widget body, and applies `sharedModel.setSource(new_source)` only if the user clicks Apply.

**Cell tagging:** Cells inserted via comm are tagged `cell.metadata.jiuwen_generated = true`. In environments without the sidebar, the source is prepended with `# [jiuwen] Generated by JiuwenSwarm` so agent-generated code is identifiable everywhere.

### Shared-webview reuse

`chat.html` and `swarm_map.html` are the same files used by the VS Code and JetBrains IDE plugins. They contain a bridge detection block that selects the right message transport at runtime:

```javascript
function send(msg) {
  if (vscodeApi) {
    vscodeApi.postMessage(msg);              // VS Code
  } else if (window.__jb_send) {
    window.__jb_send(JSON.stringify(msg));   // JetBrains
  } else if (window.__jupyter_send) {
    window.__jupyter_send(JSON.stringify(msg)); // JupyterLab
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

### Multi-kernel support

Each open notebook tab has its own Python kernel (a separate OS process). The frontend keeps one `IComm` per kernel in `KernelCommClient._comms: Map<string, IComm>`.

**Connection lifecycle:**

```
tracker.currentChanged fires (user switches tab)
    │
    ▼
_wireKernel(panel)                        ← skipped if already connected
    ├─ kernel.registerCommTarget(...)       always idempotent
    ├─ client.connectKernel(id, kernel)    guarded by _comms.has(id)
    ├─ sessionMgr.registerKernel({id, label})
    ├─ client.setActiveKernel(id)
    └─ sessionMgr.refresh()               requests session list from this kernel

panel.sessionContext.kernelChanged fires (kernel restart)
    └─ _wireKernel(panel)                  re-wires with new kernel object
       (_wiredPanelIds set prevents stacking listeners per panel)

tracker.widgetRemoved fires (notebook tab closed)
    └─ client.disconnectKernel(id)
       sessionMgr.unregisterKernel(id)
       _wiredPanelIds.delete(panel.id)
```

**Active kernel routing:** `client.send()` always routes to `_comms.get(_activeKernelId)`. Switching tabs sets `_activeKernelId` on both the client and `SessionManager`, so chat messages go to the focused notebook's kernel without user action.

**Session partitioning:** `SessionManager._sessionsByKernel: Map<string, SessionInfo[]>` stores sessions per kernel. The `sessions` getter returns only the active kernel's sessions (used by `ChatPanel`). `SessionListPanel` uses `allKernels()` and `getKernelSessions()` to render grouped sections when more than one kernel is connected; single-kernel stays flat.

**Python side:** Each kernel is a separate process with its own `comm_handler.py` and `_active_tasks` dict, so isolation is automatic.

### Status bar

`StatusIndicator` receives `client: KernelCommClient`, `swarmMgr: SwarmStateManager`, and `sessionMgr: SessionManager`. It:
- Listens to `chat.final` events and accumulates `usage.cost_usd` into `_sessionCost`. The cost resets when the active kernel changes.
- Reads `sessionMgr.allKernels()` and `client.activeKernelId` on every update. When more than one kernel is connected, the active notebook filename is appended to the status text.
- Status text format: `⬤ JiuwenSwarm: ready · analysis.ipynb · $0.0031`

### Session list filter

`SessionListPanel` has a filter `<input>` element between the header row and the session list. Typing sets `_filter` (lowercased) and triggers `_render()`. Sessions are matched by checking if their title (or `session_id`) lowercased includes the filter string. The filter applies to both flat and grouped (multi-kernel) views.

### Distribution

The extension is distributed as a Python package that bundles the built TypeScript frontend. The `pyproject.toml` `[tool.hatch.build.targets.wheel.shared-data]` section copies `packages/frontend/dist/` to `share/jupyter/labextensions/@jiuwenswarm/jupyterlab/`. JupyterLab discovers the extension automatically from that path.

---

## Notebook-native tools

`notebook_tools.py` provides four functions that operate directly on the live notebook kernel state. They are also registered as agent tools so the agent can call them automatically during a conversation.

### `read_notebook_cell(cell_index)`

Reads from `ip.history_manager.get_tail()` (execution history) and `ip.user_ns["Out"]` (output dict). Returns a dict with `source`, `output`, and `line_number`.

### `read_variable(name)`

Reads from `ip.user_ns[name]`. Dispatches to type-specific formatters:
- `DataFrame` → shape, dtypes, `.head(5)`, `.describe()`
- `ndarray` → shape, dtype, min/max/mean, first values
- `dict` / `list` → length + JSON preview
- anything else → `repr()` truncated to 3000 chars

### `insert_notebook_cell(source, cell_type, execute, confirm_execute)`

Two paths depending on whether the JupyterLab sidebar is connected:

```
Sidebar connected:
    _comm_insert() → comm.create_comm("jiuwenswarm_cell_insert").open(payload)
    Payload: { source, cell_type, execute, confirm_execute, jiuwen_generated: true }
    → TypeScript _handleCellInsert():
        NotebookActions.insertBelow() + sharedModel.setSource()
        if confirm_execute: showDialog("Run generated cell?") before executing
        if execute (and confirmed): NotebookActions.run()
        cell.model.setMetadata('jiuwen_generated', true)

No sidebar (Colab, classic Notebook, etc.):
    _display_proposed_cell() renders the source as formatted HTML
    if confirm_execute and execute: input("Run? [y/N]") before notifying user
```

### `replace_notebook_cell(cell_index, new_source)`

Two paths:

```
Sidebar connected:
    _comm_replace() → comm.create_comm("jiuwenswarm_cell_replace").open(payload)
    Payload: { old_source, new_source, line_no }
    → TypeScript _handleCellReplace():
        Find cell whose sharedModel.getSource().trim() === old_source.trim()
        Build before/after HTML diff (red old, green new) in a Lumino Widget
        showDialog("Apply cell rewrite?", body=diffWidget, [Cancel, Apply])
        On Apply: cell.sharedModel.setSource(new_source)

No sidebar:
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
| Cell insertion | diff/patch to file | comm → JupyterLab notebook API (sidebar) or display block (no sidebar) |
| Cell rewrite | diff/patch to file | comm → diff dialog → `sharedModel.setSource()` (sidebar) or `difflib` HTML (no sidebar) |

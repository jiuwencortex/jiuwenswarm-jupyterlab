# System Investigation — jiuwenswarm-jupyterlab

**Related document:** `RAT.md` — product requirements and business background.
This document covers architecture, decomposition, sequence diagrams, technical
constraints, system impact, and external dependencies.

---

## Feature Scope

`jiuwenswarm-jupyterlab` adds JiuwenSwarm agent capabilities directly into the Jupyter
notebook kernel. It has two components:

1. **Python package (`jiuwenswarm_jupyter`)** — cell magics, Python API, notebook
   context injection, session management, conversation history tools, notebook
   introspection tools, and an embedded chat UI. Works in any Jupyter environment.

2. **JupyterLab frontend extension (`@jiuwenswarm/jupyterlab`)** — TypeScript sidebar
   panels (chat, sessions, swarm map), status bar indicator, multi-kernel comm
   management. Requires JupyterLab 4+ in the browser.

Both components connect to `JiuWenSwarm` — the same agent runtime used by the CLI
and IDE plugin — running in-process inside the notebook kernel. No external server,
no WebSocket to an outside process, no separate port.

---

## Architecture

```
                 ┌───────────────────────────────────────────────────────────────────┐
                 │                    User's Jupyter environment                      │
                 │                                                                   │
                 │   %%jiuwen / %jiuwen_*        %jiuwen_chat        sidebar panel   │
                 │   (any Jupyter env)           (Colab, Kaggle,     (JupyterLab     │
                 │                                classic Notebook)   4+ only)       │
                 └──────────┬──────────────────────────┬──────────────────┬──────────┘
                            │                          │                  │
                 IPython magic                IPython magic +   Jupyter comm (IComm)
                            │                JS comm bridge     via TypeScript ext.
                            │                          │                  │
                            ▼                          ▼                  │
┌───────────────────────────────────────────────────────────────────────  │ ──────────┐
│                     jiuwenswarm_jupyter  (Python package, in kernel)    │            │
│                                                                         │            │
│  magics/          IPython magic package                                 │            │
│   ├── jiuwen.py    %%jiuwen / %jiuwen                                   │            │
│   ├── error.py     %jiuwen_error                                        │            │
│   ├── chat.py      %jiuwen_chat                                         │            │
│   ├── session/     clear · export · replay · pin · unpin · memory       │            │
│   └── analysis/    explain · test · audit · story · profile ·           │            │
│                    guard · safe · todo · diff                           │            │
│                                                                         │            │
│  client.py ────── JupyterSwarm (wraps JiuWenSwarm, tracks history)      │            │
│  context.py ───── namespace extraction; pinned variables                │            │
│  session.py ───── per-notebook session registry                         │            │
│  display.py ───── streaming IPython output renderer                     │            │
│  comm_handler.py  'jiuwenswarm' Jupyter comm target ◄────────────────── ┘            │
│  notebook_tools.py  read_variable / read_notebook_cell /                             │
│                     insert_notebook_cell / replace_notebook_cell                     │
│  config.py ────── JiuwenConfig; %jiuwen_config magic                                │
│  widgets.py ───── ipywidgets panel; %jiuwen_panel magic                              │
└─────────────────────────────────────┬────────────────────────────────────────────────┘
                                      │  in-process Python call (no server, no port)
                                      ▼
                       ┌──────────────────────────────────┐
                       │   JiuWenSwarm  (agent runtime)    │
                       │   same OS process as the kernel   │
                       │   single / team / code modes      │
                       └──────────────────────────────────┘


         ┌──────────────────────────────────────────────────────────────────────┐
         │            @jiuwenswarm/jupyterlab  (TypeScript, browser)             │
         │                                                                      │
         │  index.ts ─────── plugin init, kernel wiring, widgetRemoved cleanup  │
         │  WsClient.ts ──── IComm registry (one IComm per open notebook)       │
         │  SessionManager.ts  session list partitioned by kernel                │
         │  ChatPanel.ts ──── sidebar chat  (chat.html iframe + postMessage)     │
         │  SessionListPanel.ts  session browser with filter                     │
         │  SwarmMapPanel.ts ─ live swarm map (swarm_map.html iframe)            │
         │  StatusIndicator.ts  status bar — state / cost / active kernel        │
         └──────────────────────────────┬───────────────────────────────────────┘
                                        │  Jupyter comm (IComm, one per kernel)
                                        ▼
                            comm_handler.py  in the Python kernel
```

### Design principles

**In-process, no external server.**
`JiuWenSwarm` is imported as a Python library and instantiated directly inside the
notebook kernel. No port, no WebSocket, no background process. The kernel IS the
server.

**Jupyter comm as IPC.**
The TypeScript extension communicates with the Python kernel exclusively via the
standard Jupyter comm protocol. The event schema is identical to the IDE WebSocket
protocol, so `chat.html` and `swarm_map.html` are shared without modification.

**Single canonical HTML source.**
`packages/shared-webview/chat.html` is used by the JupyterLab sidebar (served as a
labextension asset), by the `%jiuwen_chat` magic (embedded as iframe `srcdoc`), and
by the VS Code and JetBrains IDE plugins. One file; no copies in the source tree.

**Environment-agnostic core.**
All cell magics and Python API features work identically in JupyterLab, classic
Notebook, Colab, Kaggle, VS Code, and PyCharm. The TypeScript extension and the
`%jiuwen_chat` magic are additive — they add GUI on top of the same core.

---

## Module layout

```
jiuwenswarm-jupyterlab/
├── jiuwenswarm_jupyter/         Python package (installed into the kernel)
│   ├── __init__.py              Extension entry point; registers comm, magics, tools
│   ├── magics/                  IPython magic package
│   │   ├── jiuwen.py            %%jiuwen / %jiuwen
│   │   ├── error.py             %jiuwen_error
│   │   ├── chat.py              %jiuwen_chat
│   │   ├── session/             clear · export · replay · pin · unpin · memory
│   │   └── analysis/            explain · test · audit · story · profile · guard · safe · todo · diff
│   ├── client.py                JupyterSwarm — wraps JiuWenSwarm; tracks _history
│   ├── context.py               Notebook context extractor; pinned variable injection
│   ├── display.py               Streaming IPython output renderer (markdown→HTML)
│   ├── session.py               Session registry; per-notebook session ID persistence
│   ├── comm_handler.py          'jiuwenswarm' comm target; event fan-out to frontend
│   ├── notebook_tools.py        Agent-callable notebook tools (read/insert/replace)
│   ├── config.py                JiuwenConfig dataclass; %jiuwen_config magic
│   └── widgets.py               ipywidgets panel; %jiuwen_panel magic
│
├── packages/
│   ├── shared-webview/
│   │   ├── chat.html            Canonical chat UI — shared with IDE plugins
│   │   │                        Bundled into wheel via pyproject.toml force-include
│   │   ├── swarm_map.html       Swarm map visualisation
│   │   └── icon.svg
│   │
│   └── frontend/                TypeScript JupyterLab extension
│       └── src/
│           ├── index.ts         Plugin registration; kernel wiring; cleanup
│           ├── WsClient.ts      KernelCommClient — IComm per kernel; active routing
│           ├── SessionManager.ts Session registry partitioned by kernel ID
│           ├── protocol.ts      Shared TypeScript message types
│           ├── ChatPanel.ts     Sidebar chat (chat.html iframe + __jupyter_send bridge)
│           ├── SessionListPanel.ts  Session browser with filter; grouped by kernel
│           ├── SwarmMapPanel.ts Swarm map (swarm_map.html iframe + SwarmStateManager)
│           ├── SwarmState.ts    State model for agent team activity
│           ├── SwarmStateManager.ts  State updates from kernel events
│           └── StatusIndicator.ts   Status bar — connection / cost / active kernel
│
├── docs/
├── pyproject.toml               Python build config; force-include for chat.html
├── package.json                 npm workspace root
└── README.md
```

---

## Key Sequence Diagrams

### 1. `%%jiuwen` cell magic — end to end

The most common path. Works in every environment.

```
User (notebook cell)    magics/jiuwen.py  context.py      client.py / JiuWenSwarm    display.py
        │                   │                  │                     │                    │
        │  %%jiuwen --mode code                │                     │                    │
        │  Write a train/test split            │                     │                    │
        │──────────────────►│                  │                     │                    │
        │                   │  parse options   │                     │                    │
        │                   │  (mode, session, │                     │                    │
        │                   │   no-context)    │                     │                    │
        │                   │                  │                     │                    │
        │                   │  build_context_block()                 │                    │
        │                   │─────────────────►│                     │                    │
        │                   │                  │  ip.user_ns scan    │                    │
        │                   │                  │  pinned vars        │                    │
        │                   │                  │  cell history       │                    │
        │                   │◄─ context block ─│                     │                    │
        │                   │                  │                     │                    │
        │                   │  JupyterSwarm.run_sync(query + context, mode="code")        │
        │                   │─────────────────────────────────────────►                  │
        │                   │                  │                     │                    │
        │                   │                  │                     │  stream events     │
        │                   │                  │                     │─────────────────► │
        │                   │                  │                     │  chat.delta        │
        │◄ streamed text ───────────────────────────────────────────────────────────────│
        │  appears below    │                  │                     │  tool.call         │
        │  the cell         │                  │                     │  tool.result       │
        │  in real time     │                  │                     │  chat.final        │
        │                   │                  │                     │◄─────────────────  │
        │                   │  append to _history (timestamp, mode, query, response)     │
        │                   │◄─────────────────────────────────────────                  │
        │                   │                  │                     │                    │
        │  [Ctrl+C]         │                  │                     │                    │
        │──────────────────►│  KeyboardInterrupt caught              │                    │
        │◄── "[JiuwenSwarm] Query cancelled."  │                     │                    │
```

---

### 2. JupyterLab sidebar panel — user sends a message

Applies when the TypeScript extension is installed and a notebook is open.

```
User (sidebar)   ChatPanel.ts     WsClient.ts      IComm       comm_handler.py   JiuWenSwarm
     │               │                │               │                │               │
     │  type query   │                │               │                │               │
     │  press Enter  │                │               │                │               │
     │──────────────►│                │               │                │               │
     │               │  _onIframeMessage(e)           │                │               │
     │               │  client.send({type:"send_message", query, mode, session_id})    │
     │               │───────────────►│               │                │               │
     │               │                │  comm.send()  │                │               │
     │               │                │──────────────►│                │               │
     │               │                │               │  kernel recv   │               │
     │               │                │               │───────────────►│               │
     │               │                │               │                │  build context│
     │               │                │               │                │  call JiuWen  │
     │               │                │               │                │──────────────►│
     │               │                │               │                │               │
     │               │                │               │                │  chat.delta   │
     │               │                │               │◄── comm.send ──│◄──────────────│
     │               │◄── postMessage─│◄── on_msg ────│                │               │
     │  streamed     │  handleHostMessage(event)       │                │               │
     │◄── text ──────│  renders delta in chat UI       │                │               │
     │               │                │               │                │               │
     │               │                │               │  chat.final    │               │
     │               │                │               │◄── comm.send ──│◄──────────────│
     │               │◄── postMessage─│◄── on_msg ────│                │               │
     │  response     │  render final; update cost     │                │               │
     │◄── complete ──│  update status bar             │                │               │
```

**Tab switch (multi-kernel):**
When the user switches to a different notebook tab, `tracker.currentChanged` fires
in `index.ts`. If the new notebook's kernel already has a comm, `setActiveKernel(id)`
routes subsequent sends to that kernel without reconnecting. If not seen before,
`_wireKernel()` opens a new IComm and registers it. `SessionManager.setActiveKernel()`
switches the session list view to show only sessions for the newly active kernel.

---

### 3. `%jiuwen_chat` — embedded panel in cell output

Applies in Colab, Kaggle, and classic Jupyter Notebook. The chat.html UI is
embedded directly in the cell output as an iframe; a JavaScript bridge connects
it to the running kernel via the classic Jupyter comm API.

```
User (notebook)   magics/chat.py         Cell output HTML + JS          comm_handler.py  JiuWenSwarm
      │                │                          │                              │               │
      │  %jiuwen_chat  │                          │                              │               │
      │───────────────►│                          │                              │               │
      │                │  read chat.html from     │                              │               │
      │                │  jiuwenswarm_jupyter/     │                              │               │
      │                │  static/chat.html (wheel) │                              │               │
      │                │  or packages/shared-      │                              │               │
      │                │  webview/chat.html (dev)  │                              │               │
      │                │                           │                              │               │
      │                │  html.escape(chat_html)   │                              │               │
      │                │  → srcdoc attribute        │                              │               │
      │                │  + JS bridge script        │                              │               │
      │                │  IPython.display.HTML()    │                              │               │
      │                │──────────────────────────►│                              │               │
      │                │                           │                              │               │
      │                │            [iframe loads; JS bridge runs]                │               │
      │                │                           │                              │               │
      │                │                           │  Jupyter.notebook.kernel.    │               │
      │                │                           │  comm_manager.new_comm(      │               │
      │                │                           │    'jiuwenswarm', {})        │               │
      │                │                           │─────────────────────────────►│               │
      │                │                           │                              │  registered   │
      │                │                           │                              │  target fires │
      │                │                           │                              │               │
      │                │                           │  iframe.contentWindow.       │               │
      │                │                           │  __jupyter_send installed    │               │
      │                │                           │                              │               │
      │                │                           │  postMessage({type:'connected',...})         │
      │                │                           │→ iframe: chat.html shows connected state      │
      │                │                           │                              │               │
      │  type query in │                           │                              │               │
      │  chat UI       │                           │                              │               │
      │───────────────────────────────────────────►│                              │               │
      │                │                           │  chat.html calls             │               │
      │                │                           │  window.__jupyter_send(msg)  │               │
      │                │                           │  comm.send(msg)              │               │
      │                │                           │─────────────────────────────►│               │
      │                │                           │                              │──────────────►│
      │                │                           │                              │  chat.delta   │
      │                │                           │◄── comm on_msg ──────────────│◄──────────────│
      │                │                           │  postMessage(event) to iframe│               │
      │  streamed text │                           │→ handleHostMessage renders   │               │
      │◄───────────────────────────────────────────│                              │               │
```

---

### 4. `insert_notebook_cell` — with and without sidebar

```
                With sidebar (JupyterLab)           Without sidebar (Colab, Kaggle, etc.)
                        │                                          │
  Agent calls           │                           Agent calls   │
  insert_notebook_cell()│                           insert_notebook_cell()
                        │                                          │
  notebook_tools.py     │                           notebook_tools.py
  _comm_insert()        │                           _comm_insert() → False (no comm)
  comm.open({type:"insert_cell", source, ...})      _display_proposed_cell(source, cell_type)
        │               │                                          │
        │  IComm        │                           IPython.display.HTML()
        ▼               │                                          │
  TypeScript receives   │                           Cell output shows:
  "insert_cell" message │                           ┌─────────────────────────────────┐
  uses JupyterLab       │                           │ ▷ Proposed code cell (JiuwenSwarm)│
  NotebookPanel API     │                           │ # [jiuwen] Generated by JiuwenSwarm│
  to create a new cell  │                           │ <source code>                   │
  with the given source │                           └─────────────────────────────────┘
  tagged                │                           user copies cell manually
  jiuwen_generated:true │                                          │
```

---

## Component Breakdown

### `jiuwenswarm_jupyter` — Python package

| Module | Responsibility |
|---|---|
| `__init__.py` | `load_ipython_extension` entry point; registers magics, comm target, exposes `_jiuwen` and `_jiuwen_config` to the namespace |
| `magics/jiuwen.py` | `%%jiuwen` / `%jiuwen` — primary query magic |
| `magics/error.py` | `%jiuwen_error` — forward last exception to the agent |
| `magics/chat.py` | `%jiuwen_chat` — embed full chat UI in cell output |
| `magics/session/` | `%jiuwen_clear`, `%jiuwen_export`, `%jiuwen_replay`, `%jiuwen_pin`, `%jiuwen_unpin`, `%jiuwen_memory` — conversation lifecycle, context, persistent notes |
| `magics/analysis/` | `%%jiuwen_explain`, `%%jiuwen_test`, `%jiuwen_audit`, `%jiuwen_story`, `%%jiuwen_profile`, `%%jiuwen_guard`, `%%jiuwen_safe`, `%jiuwen_todo`, `%jiuwen_diff` — code intelligence and safety |
| `client.py` | `JupyterSwarm` — thin wrapper around `JiuWenSwarm`; adds `_history` list; `run_sync()` drives the stream; `get_history()` / `clear_history()` |
| `context.py` | `build_context_block(ip, pinned_vars)` — scans `ip.user_ns`, formats DataFrames / arrays / dicts; extracts cell history; injects pinned vars first |
| `display.py` | `StreamingOutput` — IPython `Output` widget; appends deltas in real time; renders markdown as HTML via `markdown` package or escaped pre-block fallback |
| `session.py` | Session registry keyed by notebook session ID (from `ip.history_manager`); creates `JupyterSwarm` on first access; persists session IDs across kernel restarts via `_jiuwen_session_id` in `ip.user_ns` |
| `comm_handler.py` | `register_comm_target(ip)` — tries `comm` package then `ipykernel` legacy; on each incoming `send_message` event: builds context, streams `JiuWenSwarm`, fans out events to all open comms; returns `True` if registered in a live Jupyter environment |
| `notebook_tools.py` | `read_variable`, `read_notebook_cell`, `insert_notebook_cell`, `replace_notebook_cell`; sidebar path tries `comm.create_comm()` first; no-sidebar path renders HTML in output |
| `config.py` | `JiuwenConfig(frozen=False)` — `mode`, `timeout`, `model`, `inject_context`, `pinned_vars`; `get_config(ip)` returns or creates per-notebook config stored in `ip.user_ns["_jiuwen_config"]` |
| `widgets.py` | `show_jiuwen_panel(ip)` — ipywidgets `VBox` with mode dropdown, timeout slider, context toggle, session field, query textarea, send button, `Output` widget; `%jiuwen_panel` magic |

---

### `packages/frontend` — TypeScript JupyterLab extension

| Module | Responsibility |
|---|---|
| `index.ts` | Registers 4 plugins (chat, sessions, swarm, status); tracks notebook tabs via `INotebookTracker`; calls `_wireKernel()` on `currentChanged` and `kernelChanged`; calls `disconnectKernel()` + `unregisterKernel()` on `widgetRemoved`; uses `_wiredPanelIds: Set<string>` to prevent duplicate listeners |
| `WsClient.ts` | `KernelCommClient` — `_comms: Map<string, IComm>`; `_activeKernelId: string | null`; `connectKernel()`, `disconnectKernel()`, `setActiveKernel()`; `send()` routes to active comm; `onEvent()` subscriber pattern |
| `SessionManager.ts` | `_sessionsByKernel: Map<string, SessionInfo[]>`; `sessions` getter returns active kernel's list; `allKernels()` for grouped rendering; `registerKernel()` / `unregisterKernel()` |
| `protocol.ts` | Shared TypeScript interfaces: `SessionInfo`, `KernelInfo`, `KernelEvent`, `KernelBoundMessage`, `AgentMode` |
| `ChatPanel.ts` | Creates `<iframe>` pointing to served `chat.html`; installs `contentWindow.__jupyter_send` on load; routes `postMessage` → `client.send()`; routes `client.onEvent()` → `iframe.contentWindow.postMessage()` |
| `SessionListPanel.ts` | Renders session list; groups by kernel when `allKernels().length > 1`; filters by title/session_id; `New Session` and `Switch` buttons |
| `SwarmMapPanel.ts` | Hosts `swarm_map.html` iframe; `SwarmStateManager` processes team events and pushes state diffs via `postMessage` |
| `StatusIndicator.ts` | JupyterLab `StatusBarItem`; shows connection state dot, active kernel label (when multiple kernels open), accumulated session cost from `chat.final` usage events |

---

## Technical Constraints

**`%jiuwen_chat` comm API availability:**
`Jupyter.notebook.kernel.comm_manager.new_comm()` is a classic Notebook JavaScript
global. Available in Colab, Kaggle, classic Notebook. Not exposed as a global in
JupyterLab 4+ (where the TypeScript extension provides the comm instead). The magic
logs a warning and shows an error card in the iframe if the API is not found.

**Streaming — cell magic vs sidebar:**
Cell magic streaming uses an IPython `Output` widget or direct `display()` calls,
updating the cell output area incrementally. Sidebar streaming uses `postMessage`
events to the chat.html iframe. When the sidebar is connected and a cell magic cell
is run simultaneously, both receive events — the sidebar shows the response, the cell
output shows it again. This is intentional (both surfaces are live); no deduplication.

**Keyboard interrupt handling:**
`JupyterSwarm.run_sync()` wraps the async event loop in a thread so the cell magic is
synchronous from IPython's perspective. `KeyboardInterrupt` raised during the stream
(Kernel → Interrupt) is caught by the `except KeyboardInterrupt` block in `_run_magic`
and prints a cancellation message. The in-flight `JiuWenSwarm` task is cancelled.

**Session ID persistence across kernel restarts:**
The default session ID is stored in `ip.user_ns["_jiuwen_session_id"]`. On kernel
restart this variable is lost. `session.py` uses `ip.history_manager.session_number`
as a fallback key so that repeated restarts generate consistent (but new) session IDs.
Explicit named sessions (`--session NAME`) survive as long as the session registry
module-level dict is alive (i.e., within the same kernel process).

**`replace_notebook_cell` cell identification:**
The cell is located by matching against `ip.history_manager.get_tail(1000)` using the
`cell_index` argument. The index is zero-based into the execution history, not the
visual cell number. The TypeScript side locates the cell in `NotebookPanel` by matching
`old_source` content — positional index is not used, making the match robust to cell
reordering.

**Multi-kernel tab switch latency:**
When the user switches to a notebook whose kernel has not yet been wired, `_wireKernel()`
must open a new IComm before the sidebar can send a message. Opening a comm requires a
round-trip to the kernel. The status bar shows "Connecting…" during this window.

---

## Impact on Existing Systems

### JiuWenSwarm agent runtime

No changes required. `JupyterSwarm` wraps `JiuWenSwarm` with a thin layer that adds
`_history` tracking. All agent modes, memory, skills, tool dispatch, and streaming
events are unchanged. The integration is read-only from the runtime's perspective.

### JupyterLab

The extension installs as a standard JupyterLab labextension. It uses only public
JupyterLab APIs (`INotebookTracker`, `IStatusBar`, `Widget`, `IComm`). No JupyterLab
internal APIs are used. Uninstalling the extension (`pip uninstall jiuwenswarm-jupyter`)
removes it cleanly.

### Existing notebook users

Opt-in only. The extension does nothing until `%load_ext jiuwenswarm_jupyter` is called.
Auto-load requires an explicit `ipython_config.py` entry. No existing notebooks are
affected.

### Performance

Context injection (`build_context_block`) runs on every `%%jiuwen` call. For notebooks
with very large objects in `user_ns`, the snapshot step may add 50–200 ms. `--no-context`
suppresses this entirely. Pinned variables bypass the full namespace sweep and are
extracted individually.

### Security

No credentials are introduced by the integration. JiuWenSwarm reads API keys from
`~/.jiuwenswarm/config/.env` (the same file used by the CLI and IDE plugin). No keys
are stored in the notebook, cell outputs, or session files.

---

## External Dependencies

### Python

| Package | Version | Purpose |
|---|---|---|
| `ipython` | ≥ 8.0 | Magic registration, `ip.user_ns`, `ip.history_manager`, `IPython.display` |
| `ipywidgets` | ≥ 8.0 | `%jiuwen_panel` ipywidgets GUI; `Output` widget for streaming |
| `jiuwenswarm` | current | `JiuWenSwarm` agent runtime |
| `markdown` | optional | Markdown → HTML rendering in `display.py`; plain pre-block fallback if absent |
| `comm` | optional | New-style Jupyter comm registration (`comm.get_comm_manager()`); falls back to `ipykernel` |
| `hatchling` | ≥ 1.21 | Python build backend; `force-include` for bundling `chat.html` |

### TypeScript / Node.js (build only)

| Package | Purpose |
|---|---|
| `@jupyterlab/application` | Plugin registration API |
| `@jupyterlab/notebook` | `INotebookTracker` for tab tracking |
| `@jupyterlab/statusbar` | `IStatusBar` for status indicator |
| `@jupyterlab/services` | `IComm`, kernel session API |
| `@lumino/widgets` | `Widget` base class for panels |
| `webpack` | TypeScript bundle; outputs to `packages/frontend/dist/` |

### Runtime (user must supply)

| Dependency | Required for | Notes |
|---|---|---|
| JupyterLab 4.x | Frontend extension, sidebar, multi-kernel | Not required for cell magics |
| JiuwenSwarm API key | Any agent call | Read from `~/.jiuwenswarm/config/.env` |
| Python 3.10+ | All | `str | None` union syntax, `match` statements |

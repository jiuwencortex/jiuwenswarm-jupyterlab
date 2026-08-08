# Architecture — jiuwenswarm-jupyterlab

## Overview

`jiuwenswarm-jupyterlab` provides two surfaces for running JiuwenSwarm inside Jupyter:

1. **Python package (`jiuwenswarm_jupyter`)** — in-process API and `%%jiuwen` cell magic. Works in any Jupyter environment (JupyterLab, classic Notebook, VS Code Notebooks, Google Colab, Kaggle).

2. **JupyterLab frontend extension (`@jiuwenswarm/jupyterlab`)** — TypeScript sidebar panel with persistent chat UI and swarm map, embedded as iframes loaded from the shared-webview HTML files.

Both surfaces call the same in-process `JiuWenSwarm` facade; no external server or WebSocket is required.

---

## Project layout

```
jiuwenswarm-jupyterlab/
├── jiuwenswarm_jupyter/         Python package (Phase 1 core)
│   ├── __init__.py              load_ipython_extension entry point
│   ├── magic.py                 %%jiuwen / %jiuwen cell magic
│   ├── client.py                JupyterSwarm wrapper around JiuWenSwarm
│   ├── context.py               Notebook context extractor
│   ├── display.py               IPython streaming output renderer
│   └── session.py               Session ID management + registry
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

The Python kernel side registers a `jiuwenswarm` comm target:

```python
# Python side (in jiuwenswarm_jupyter, Phase 2)
def _register_comm_target(kernel):
    @kernel.comm_info('jiuwenswarm')
    def target(comm, open_msg):
        @comm.on_msg
        def receive(msg):
            data = msg['content']['data']
            # Route to JupyterSwarm, stream events back via comm.send()
```

The event schema is identical to the IDE WebSocket events (`chat.delta`, `chat.final`, `tool.call`, `tool.result`, `swarm_snapshot`, etc.), so the shared-webview HTML requires no changes to handle them.

### Distribution

The extension is distributed as a Python package that bundles the built TypeScript frontend. The `pyproject.toml` `[tool.hatch.build.targets.wheel.shared-data]` section copies `packages/frontend/dist/` to `share/jupyter/labextensions/@jiuwenswarm/jupyterlab/`. JupyterLab discovers the extension automatically from that path.

---

## Relation to jiuwenswarm-ide

| Concern | jiuwenswarm-ide | jiuwenswarm-jupyterlab |
|---|---|---|
| Transport | WebSocket (port 18092, E2AEnvelope) | Jupyter comm (in-process) |
| VS Code bridge | `vscodeApi.postMessage` | not applicable |
| JetBrains bridge | `window.__jb_send` / JCEF | not applicable |
| JupyterLab bridge | not applicable | `window.__jupyter_send` / postMessage |
| Shared-webview HTML | source | copied + bridge patch |
| Context collection | active editor file, workspace | notebook variables, cell history |
| Session ID prefix | `vscode_*` / `jb_*` | `jupyter_*` |
| Agent API | `JiuWenSwarm` via WebSocket | `JiuWenSwarm` direct in-process |

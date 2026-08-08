# Roadmap — jiuwenswarm-jupyterlab

## Phase 1 — Core in-process API (complete)

**Target:** `pip install jiuwenswarm-jupyter` → `%%jiuwen` works in any notebook.

- [x] `JupyterSwarm` client wrapper around `JiuWenSwarm`
- [x] `%%jiuwen` cell magic with `--mode`, `--session`, `--no-context`, `--timeout` options
- [x] `%jiuwen` line magic
- [x] Streaming IPython output via `display()` / `update_display()` (live-updating cell output)
- [x] Tool call collapsible blocks in output
- [x] Notebook context extractor (variables, DataFrames, cell history, imported packages)
- [x] Per-notebook default session + named sessions
- [x] `nest_asyncio` compatibility for running inside ipykernel event loop
- [x] Auto-load via `ipython_config.py`
- [x] `_jiuwen` convenience variable auto-injected into namespace on load

## Phase 2 — JupyterLab sidebar panel (complete)

**Target:** Persistent chat panel in JupyterLab sidebar with swarm map, matching IDE plugin UX.

- [x] Python kernel comm target registration (`comm_handler.py`) — supports both `comm` package (JupyterLab 4+) and `ipykernel` (classic Notebook)
- [x] Event streaming from kernel to frontend via comm (`chat.delta`, `chat.final`, `tool.call`, `tool.result`, `team.*`)
- [x] Cancellation support via `cancel` message type
- [x] Skills list request/response over comm
- [x] `KernelCommClient` TypeScript comm bridge
- [x] `ChatPanel` iframe rendering in JupyterLab sidebar (shared `chat.html` + `__jupyter_send` bridge)
- [x] `SwarmMapPanel` as secondary main-area tab (shared `swarm_map.html` + postMessage)
- [x] `StatusIndicator` in JupyterLab status bar (connection state + active agent count)
- [x] Session management (`SessionManager.ts`)
- [x] Live swarm state updates (`SwarmStateManager.ts`, `SwarmState.ts`)
- [x] Command palette entries (Open Chat, Open Swarm Map, New Session)
- [x] TypeScript frontend build config (Webpack + tsconfig)
- [ ] Webpack build producing distributable labextension bundle (requires `npm install && npm run build`)
- [ ] Session list UI in sidebar (browse history, switch sessions) — backend done, frontend pending
- [ ] Skills browser UI in sidebar — backend done, frontend pending

## Phase 3 — Notebook-native agent tools (complete)

**Target:** Agent can read and write notebook cells directly.

- [x] `read_notebook_cell(cell_index)` — reads source and output of any executed cell
- [x] `read_variable(name)` — full formatted inspection: DataFrame, ndarray, dict, list, any object
- [x] `insert_notebook_cell(source, cell_type, execute)` — Phase 2 path: actual comm insert; Phase 1 fallback: formatted display block
- [x] Tool definitions schema (`TOOL_DEFINITIONS`) for agent registration
- [x] Tool dispatcher (`get_dispatcher()`) — callable dict for direct integration
- [x] All three tools exposed at top-level `from jiuwenswarm_jupyter import read_variable, ...`
- [ ] Auto-execute proposed cells with user confirmation (opt-in) — Phase 2+ only
- [ ] Diff view for agent-generated cell edits (future)

## Phase 4 — Remote and cloud environments

- [ ] Google Colab: confirm `pip install` works, add Colab-specific setup guide
- [ ] JupyterHub: multi-user isolation (one swarm instance per kernel session)
- [ ] Remote Jupyter servers: document SSH tunnel or reverse proxy setup
- [ ] `%jiuwen_config` line magic for per-notebook configuration overrides

## Out of scope

- Notebook diff / version control integration (separate project)
- Non-Jupyter Python REPL integration

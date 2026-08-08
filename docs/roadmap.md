# Roadmap — jiuwenswarm-jupyterlab

## Phase 1 — Core in-process API (implemented)

**Target:** `pip install jiuwenswarm-jupyter` → `%%jiuwen` works in any notebook.

- [x] `JupyterSwarm` client wrapper around `JiuWenSwarm`
- [x] `%%jiuwen` cell magic with `--mode`, `--session`, `--no-context`, `--timeout` options
- [x] `%jiuwen` line magic
- [x] Streaming IPython output via `display()` / `update_display()` (live-updating cell output)
- [x] Tool call collapsible blocks in output
- [x] Notebook context extractor (variables, DataFrames, cell history)
- [x] Per-notebook default session + named sessions
- [x] `nest_asyncio` compatibility for running inside ipykernel event loop
- [x] Auto-load via `ipython_config.py`

## Phase 2 — JupyterLab sidebar panel

**Target:** Persistent chat panel in JupyterLab sidebar with swarm map, matching IDE plugin UX.

- [ ] Jupyter comm target registration on Python side
- [ ] `KernelCommClient` fully wired to live kernel (comm open/close lifecycle)
- [ ] `ChatPanel` iframe rendering in JupyterLab sidebar
- [ ] `SwarmMapPanel` as secondary main-area tab
- [ ] `StatusIndicator` in JupyterLab status bar
- [ ] Session list in sidebar (browse history, switch sessions)
- [ ] Skills browser in sidebar
- [ ] Webpack build producing distributable labextension bundle
- [ ] Python package data configuration for labextension auto-discovery
- [ ] `jupyter labextension develop` workflow for local development

## Phase 3 — Notebook-native agent tools

**Target:** Agent can read and write notebook cells directly.

- [ ] `read_notebook_cell(cell_index)` tool — agent reads any cell's source and output
- [ ] `insert_notebook_cell(source, cell_type)` tool — agent proposes new code cells
- [ ] `read_variable(name)` tool — agent inspects specific Python variables by name
- [ ] Auto-execute proposed cells with user confirmation (opt-in)
- [ ] Diff view for agent-generated cell edits (similar to IDE plugin diff workflow)

## Phase 4 — Remote and cloud environments

- [ ] Google Colab: confirm `pip install` works, add Colab-specific setup guide
- [ ] JupyterHub: multi-user isolation (one swarm instance per kernel session)
- [ ] Remote Jupyter servers: document SSH tunnel or reverse proxy setup
- [ ] `%jiuwen_config` line magic for per-notebook configuration overrides

## Out of scope

- Notebook diff / version control integration (separate project)
- Non-Jupyter Python REPL integration

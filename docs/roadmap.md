# Roadmap — jiuwenswarm-jupyterlab

Phases 1, 2, and 3 are implemented. This file tracks what remains.

---

## Remaining — Phase 2 (JupyterLab sidebar panel)

- [ ] Webpack build producing a distributable labextension bundle — needs `npm install && npm run build` to be run and the output committed or published to PyPI
- [ ] Session list UI in sidebar — browse session history, switch between sessions (backend done, frontend not built)
- [ ] Skills browser UI in sidebar — list and toggle skills from the JupyterLab sidebar (backend done, frontend not built)

## Remaining — Phase 3 (Notebook-native tools)

- [ ] Auto-execute proposed cells with user confirmation (opt-in) — agent inserts cell and asks kernel to run it; user sees result in place
- [ ] Diff view for agent-generated cell edits — show what changed when agent rewrites an existing cell, similar to IDE plugin diff workflow

## Phase 4 — Remote and cloud environments

- [ ] Google Colab: confirm `pip install` works end-to-end, add Colab-specific setup guide to docs
- [ ] JupyterHub: multi-user isolation — one swarm instance per kernel session, no shared state
- [ ] Remote Jupyter servers: document SSH tunnel or reverse proxy setup for remote kernels
- [ ] `%jiuwen_config` line magic for per-notebook configuration overrides (model, mode, timeout)

## Phase 5 — UX & Deep Integration

Items not in the original plan, identified during implementation:

- [ ] Kernel restart recovery — after kernel restart, auto-restore the `_jiuwen` session so the conversation continues without the user having to re-run `%load_ext`
- [ ] Error auto-forwarding — when a cell throws an exception, auto-populate the chat input with the error and the failing cell code so the user can ask the agent to fix it in one click
- [ ] Keyboard shortcuts — `Cmd+Shift+J` opens the chat panel, `Cmd+Shift+Enter` sends the current cell to the agent
- [ ] Agent-generated cell tagging — mark cells inserted by the agent with notebook metadata (`cell.metadata.jiuwen_generated: true`) so they are visually distinguishable from user-written cells
- [ ] Save conversation with notebook — persist the session context in `.ipynb` metadata on save; restore it when the notebook is reopened so conversations survive between sessions
- [ ] ipywidgets UI — replace `%%jiuwen` flag syntax (`--mode`, `--session`) with interactive dropdowns and inputs rendered in the cell output
- [ ] Multi-kernel support — one chat panel that can switch between multiple open notebooks (kernels), each with its own session

## Out of scope

- Notebook diff / version control integration (separate project)
- Non-Jupyter Python REPL integration

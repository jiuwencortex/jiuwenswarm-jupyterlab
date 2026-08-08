# Roadmap — jiuwenswarm-jupyterlab

Phases 1–3 and the majority of Phase 5 are implemented. See `architecture.md` and `user/USER_GUIDE.md` for what is already built. This file tracks only what remains.

---

## Phase 2 — JupyterLab sidebar panel

- [ ] Webpack build — produce a distributable labextension bundle (`npm install && npm run build`) and publish the wheel to PyPI

## Phase 3 — Notebook-native tools

- [ ] Auto-execute proposed cells with user confirmation (opt-in) — agent inserts cell and asks kernel to run it; user sees result in place
- [ ] Diff view for agent-generated cell edits — show what changed when agent rewrites an existing cell, similar to IDE plugin diff workflow

## Phase 4 — Remote and cloud environments

- [ ] Google Colab: confirm `pip install` works end-to-end, add Colab-specific setup guide to docs
- [ ] JupyterHub: multi-user isolation — one swarm instance per kernel session, no shared state
- [ ] Remote Jupyter servers: document SSH tunnel or reverse proxy setup for remote kernels

## Phase 5 — Remaining UX items

- [ ] Save conversation with notebook — persist session context in `.ipynb` metadata on save; restore when the notebook is reopened
- [ ] ipywidgets UI — replace `%%jiuwen` flag syntax (`--mode`, `--session`) with interactive dropdowns rendered in cell output
- [ ] Multi-kernel support — one chat panel that can switch between multiple open notebooks, each with its own session

## Out of scope

- Notebook diff / version control integration (separate project)
- Non-Jupyter Python REPL integration

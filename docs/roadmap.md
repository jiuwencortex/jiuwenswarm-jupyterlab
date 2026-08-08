# Roadmap — jiuwenswarm-jupyterlab

All Phase 1–3 features and the majority of Phase 4–5 are implemented. See `architecture.md` and `user/USER_GUIDE.md` for what is already built. This file tracks only what remains.

---

## Phase 2 — JupyterLab sidebar panel

- [ ] **Webpack build** — produce a distributable labextension bundle (`npm install && npm run build` in `packages/frontend/`) and publish the Python wheel to PyPI with the bundled frontend

## Phase 3 — Notebook-native tools

- [ ] **Diff view for agent-generated cell edits** — when the agent rewrites an existing cell, show a before/after diff using `difflib.HtmlDiff` in the output area; in Phase 2, a JupyterLab dialog with Apply/Cancel before committing the change

## Phase 5 — Remaining UX items

- [ ] **Multi-kernel support** — one chat panel that can switch between multiple open notebooks in the same JupyterLab window, each with its own kernel and session; requires changes to `SessionListPanel` and `KernelCommClient`

## Out of scope

- Notebook diff / version control integration (separate project)
- Non-Jupyter Python REPL integration

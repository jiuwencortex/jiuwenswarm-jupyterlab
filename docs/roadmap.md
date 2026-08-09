# Roadmap — jiuwenswarm-jupyterlab

All Phase 1–3 features are implemented. See `architecture.md` and `user/USER_GUIDE.md` for what is built. The webpack build and PyPI publish steps are in `docs/operations/PUBLISHING.md`.

---

## Remaining development

Items are scoped to this package only. They require no changes to `jiuwenswarm` core unless noted.

---

### Session export _(small)_

A `%jiuwen_export` line magic (and optional sidebar button) that saves the full conversation history of the current session to a markdown or JSON file in the working directory. Useful for archiving research conversations alongside notebooks.

**Scope:** Python only (`magic.py` + `session.py`). No TypeScript changes needed.

---

### Cost display _(small)_

`ChatFinalEvent` already carries `usage.cost_usd` in the comm protocol. Accumulate per-session cost and show it in the status bar indicator or as a footnote in the chat panel after each response.

**Scope:** `StatusIndicator.ts` or `ChatPanel.ts`. No Python changes needed.

---

### Active kernel label in status bar _(small)_

When more than one kernel is connected, the status bar currently shows connection state but not which notebook is active. Add the notebook filename (e.g. `⚡ analysis.ipynb`) so the user always knows where messages are going.

**Scope:** `StatusIndicator.ts` + `SessionManager.ts` (expose active kernel label). No Python changes needed.

---

### Session search / filter _(small)_

Add a filter text input at the top of the Sessions panel. Filters by session title across all kernels. Relevant once a user accumulates 10+ sessions.

**Scope:** `SessionListPanel.ts` only.

---

### `%jiuwen_replay` magic _(small)_

Re-send the last N conversation turns to a new fresh session (for when a conversation has gone off-topic and the user wants to start clean but with the same context). `N` defaults to 3 and is configurable.

**Scope:** Python only (`magic.py` + `session.py`).

---

### Pinned variables _(medium)_

`%jiuwen_pin df_train results_dict` marks specific namespace variables to always inject into context regardless of the auto-context sweep. `%jiuwen_unpin` removes them. Reduces noise in large namespaces where most variables are irrelevant.

**Scope:** `context.py` + `config.py` + `magic.py`.

---

### Kernel disconnect cleanup _(small, bug-fix quality)_

When a notebook tab is closed, its kernel entry remains in `SessionManager._sessionsByKernel` and the Sessions panel until the next refresh. Wire `tracker.widgetRemoved` in `index.ts` to call `client.disconnectKernel(id)` and `sessionMgr.unregisterKernel(id)` on close.

**Scope:** `index.ts` only. `unregisterKernel()` already exists in `SessionManager.ts`.

---

## Out of scope

- Notebook diff / version control integration (separate project)
- Non-Jupyter Python REPL integration
- API key management, `jiuwenswarm-init` simplification, or any change to `jiuwenswarm` core

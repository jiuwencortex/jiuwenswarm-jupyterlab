# Roadmap — jiuwenswarm-jupyterlab

All Phase 1–3 features are implemented. See `architecture.md` and `user/USER_GUIDE.md` for what is built. The webpack build and PyPI publish steps are in `docs/operations/PUBLISHING.md`.

---

## Remaining development

Items are scoped to this package only. They require no changes to `jiuwenswarm` core.

---

### Multi-kernel support _(large)_

One chat panel that can address multiple simultaneously open notebooks, each with its own kernel and conversation session.

**Requires architectural changes:**
- `KernelCommClient`: become a registry of `{kernelId → comm}` instead of a single connection
- `index.ts` `currentChanged` handler: accumulate kernel connections rather than replace the active one
- `SessionListPanel`: group sessions by notebook/kernel; clicking switches the active target
- `ChatPanel` / `comm_handler`: route messages to the correct kernel comm based on the selected session

---

## Out of scope

- Notebook diff / version control integration (separate project)
- Non-Jupyter Python REPL integration
- API key management, `jiuwenswarm-init` simplification, or any change to `jiuwenswarm` core

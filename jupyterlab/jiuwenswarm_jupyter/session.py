"""Session ID management and per-notebook JupyterSwarm instance registry.

Sessions survive kernel restarts: the last active session ID for each
working directory is persisted to ``~/.jiuwenswarm/jupyter_sessions.json``
and restored automatically when the extension reloads after a restart.
"""

from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path
from uuid import uuid4

# ---------------------------------------------------------------------------
# Restart persistence
# ---------------------------------------------------------------------------

_SESSIONS_FILE = Path.home() / ".jiuwenswarm" / "jupyter_sessions.json"
_MAX_SESSION_AGE_DAYS = 30


def _load_persisted() -> dict[str, dict]:
    try:
        if _SESSIONS_FILE.exists():
            return json.loads(_SESSIONS_FILE.read_text())
    except Exception:
        pass
    return {}


def _save_persisted(data: dict[str, dict]) -> None:
    try:
        _SESSIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
        _SESSIONS_FILE.write_text(json.dumps(data, indent=2))
    except Exception:
        pass


def _notebook_key() -> str:
    """Stable key for the current notebook environment (current working directory)."""
    return os.getcwd()


def save_session_for_restart(session_id: str) -> None:
    """Persist *session_id* so it can be restored after a kernel restart."""
    key = _notebook_key()
    data = _load_persisted()
    data[key] = {"session_id": session_id, "saved_at": time.time()}
    _save_persisted(data)


def restore_session_from_restart() -> str | None:
    """Return the last saved session ID for the current directory, or *None*.

    Returns *None* if no entry exists or the entry is older than
    :data:`_MAX_SESSION_AGE_DAYS`.
    """
    key = _notebook_key()
    data = _load_persisted()
    entry = data.get(key)
    if not entry:
        return None
    age_days = (time.time() - entry.get("saved_at", 0)) / 86400
    if age_days > _MAX_SESSION_AGE_DAYS:
        data.pop(key, None)
        _save_persisted(data)
        return None
    return entry.get("session_id")


# ---------------------------------------------------------------------------
# Session ID helpers
# ---------------------------------------------------------------------------


def make_session_id(name: str | None = None) -> str:
    """Return a session ID in the ``jupyter_<name|uuid>`` format."""
    suffix = name if name else uuid4().hex[:12]
    return f"jupyter_{suffix}"


# ---------------------------------------------------------------------------
# In-process registry (thread-safe)
# ---------------------------------------------------------------------------

_lock = threading.Lock()
_registry: dict[str, "JupyterSwarm"] = {}  # noqa: F821 – forward ref
_default_key = "__notebook_default__"


def get_default_swarm(ip=None) -> "JupyterSwarm":  # noqa: F821
    """Return (or create) the per-notebook default :class:`JupyterSwarm`.

    On first call after a kernel restart, the previous session ID is restored
    from disk so the conversation continues without extra setup.  The instance
    is stored in the IPython namespace as ``_jiuwen``.
    """
    from .client import JupyterSwarm

    if ip is not None:
        existing = ip.user_ns.get("_jiuwen")
        if isinstance(existing, JupyterSwarm):
            return existing

    with _lock:
        if _default_key not in _registry:
            restored_id = restore_session_from_restart()
            if restored_id:
                swarm = JupyterSwarm(session_id=restored_id)
                print(f"[jiuwenswarm] Restored session: {restored_id}")
            else:
                swarm = JupyterSwarm()
            _registry[_default_key] = swarm
            # Persist for the next restart
            save_session_for_restart(swarm.session_id)

        swarm = _registry[_default_key]

    if ip is not None:
        ip.user_ns["_jiuwen"] = swarm

    return swarm


def get_named_swarm(name: str) -> "JupyterSwarm":  # noqa: F821
    """Return (or create) a named :class:`JupyterSwarm` session."""
    from .client import JupyterSwarm

    with _lock:
        if name not in _registry:
            _registry[name] = JupyterSwarm(session_id=make_session_id(name))
        return _registry[name]


def clear_session(name: str | None = None) -> None:
    """Remove a session from the registry so the next call creates a fresh one.

    Also clears the persisted restart entry when clearing the default session.
    """
    key = name if name else _default_key
    with _lock:
        _registry.pop(key, None)
    if name is None:
        data = _load_persisted()
        data.pop(_notebook_key(), None)
        _save_persisted(data)

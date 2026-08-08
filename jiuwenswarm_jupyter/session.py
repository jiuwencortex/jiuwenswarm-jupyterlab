"""Session ID management and per-notebook JupyterSwarm instance registry."""

from __future__ import annotations

import threading
from uuid import uuid4

_lock = threading.Lock()
_registry: dict[str, "JupyterSwarm"] = {}  # noqa: F821 – forward ref resolved at import time
_default_key = "__notebook_default__"


def make_session_id(name: str | None = None) -> str:
    """Return a session ID in the jupyter_<name|uuid> format."""
    suffix = name if name else uuid4().hex[:12]
    return f"jupyter_{suffix}"


def get_default_swarm(ip=None) -> "JupyterSwarm":  # noqa: F821
    """Return (or create) the per-notebook default JupyterSwarm instance.

    The instance is stored in the IPython namespace so it persists across
    cells and is visible to the user as ``_jiuwen``.
    """
    from .client import JupyterSwarm  # late import to avoid circular

    if ip is not None:
        existing = ip.user_ns.get("_jiuwen")
        if isinstance(existing, JupyterSwarm):
            return existing

    with _lock:
        if _default_key not in _registry:
            _registry[_default_key] = JupyterSwarm()
        swarm = _registry[_default_key]

    if ip is not None:
        ip.user_ns["_jiuwen"] = swarm

    return swarm


def get_named_swarm(name: str) -> "JupyterSwarm":  # noqa: F821
    """Return (or create) a named JupyterSwarm session."""
    from .client import JupyterSwarm  # late import to avoid circular

    with _lock:
        if name not in _registry:
            _registry[name] = JupyterSwarm(session_id=make_session_id(name))
        return _registry[name]


def clear_session(name: str | None = None) -> None:
    """Remove a session from the registry (next call creates a fresh one)."""
    key = name if name else _default_key
    with _lock:
        _registry.pop(key, None)

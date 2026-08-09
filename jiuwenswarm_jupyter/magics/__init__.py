"""IPython magics for JiuwenSwarm, one module per magic.

Each module exposes a ``register(ip)`` function that registers its magic
with the given IPython shell. :func:`register_all` calls them in order.
"""

from __future__ import annotations

from . import (
    chat,
    clear,
    error,
    export,
    jiuwen,
    pin,
    replay,
    unpin,
)

__all__ = [
    "register_all",
    "jiuwen",
    "error",
    "clear",
    "export",
    "replay",
    "pin",
    "unpin",
    "chat",
]


def register_all(ip) -> None:
    """Register all JiuwenSwarm magics with the given IPython shell."""
    jiuwen.register(ip)
    error.register(ip)
    clear.register(ip)
    export.register(ip)
    replay.register(ip)
    pin.register(ip)
    unpin.register(ip)
    chat.register(ip)

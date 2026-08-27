"""Session management magics — conversation lifecycle, context pinning, and memory."""

from __future__ import annotations

from . import clear, export, memory, pin, replay, unpin

__all__ = ["register_all", "clear", "export", "memory", "pin", "replay", "unpin"]


def register_all(ip) -> None:
    """Register all session magics with the given IPython shell."""
    clear.register(ip)
    export.register(ip)
    replay.register(ip)
    pin.register(ip)
    unpin.register(ip)
    memory.register(ip)

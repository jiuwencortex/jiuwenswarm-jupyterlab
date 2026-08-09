"""Experiment lifecycle magics — tracking, reproduction, and model documentation."""

from __future__ import annotations

from . import card, reproduce, track

__all__ = ["register_all", "track", "reproduce", "card"]


def register_all(ip) -> None:
    """Register all workflow magics with the given IPython shell."""
    track.register(ip)
    reproduce.register(ip)
    card.register(ip)

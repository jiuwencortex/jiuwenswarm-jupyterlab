"""Experiment lifecycle magics — tracking, reproduction, model documentation, and next-step suggestions."""

from __future__ import annotations

from . import card, reproduce, suggest, track

__all__ = ["register_all", "track", "reproduce", "card", "suggest"]


def register_all(ip) -> None:
    """Register all workflow magics with the given IPython shell."""
    track.register(ip)
    reproduce.register(ip)
    card.register(ip)
    suggest.register(ip)

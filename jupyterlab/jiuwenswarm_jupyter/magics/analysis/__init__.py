"""Code analysis and intelligence magics — profiling, auditing, safety, and narrative."""

from __future__ import annotations

from . import audit, diff, doc, explain, guard, profile, safe, story

__all__ = [
    "register_all",
    "audit",
    "diff",
    "doc",
    "explain",
    "guard",
    "profile",
    "safe",
    "story",
]


def register_all(ip) -> None:
    """Register all analysis magics with the given IPython shell."""
    explain.register(ip)
    audit.register(ip)
    story.register(ip)
    profile.register(ip)
    guard.register(ip)
    safe.register(ip)
    diff.register(ip)
    doc.register(ip)

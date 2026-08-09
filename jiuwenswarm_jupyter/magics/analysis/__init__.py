"""Code analysis and intelligence magics — profiling, testing, auditing, and safety."""

from __future__ import annotations

from . import audit, diff, explain, guard, profile, safe, story, test_gen, todo

__all__ = [
    "register_all",
    "audit",
    "diff",
    "explain",
    "guard",
    "profile",
    "safe",
    "story",
    "test_gen",
    "todo",
]


def register_all(ip) -> None:
    """Register all analysis magics with the given IPython shell."""
    explain.register(ip)
    test_gen.register(ip)
    audit.register(ip)
    story.register(ip)
    profile.register(ip)
    guard.register(ip)
    safe.register(ip)
    todo.register(ip)
    diff.register(ip)

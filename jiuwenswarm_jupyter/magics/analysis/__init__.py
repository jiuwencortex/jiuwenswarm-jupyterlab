"""Code analysis and intelligence magics — profiling, testing, auditing, and safety."""

from __future__ import annotations

from . import audit, benchmark, diff, doc, explain, fix, guard, optimize, profile, safe, story, test_gen, todo, translate

__all__ = [
    "register_all",
    "audit",
    "benchmark",
    "diff",
    "doc",
    "explain",
    "fix",
    "guard",
    "optimize",
    "profile",
    "safe",
    "story",
    "test_gen",
    "todo",
    "translate",
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
    doc.register(ip)
    benchmark.register(ip)
    fix.register(ip)
    optimize.register(ip)
    translate.register(ip)

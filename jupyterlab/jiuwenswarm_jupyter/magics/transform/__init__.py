"""Code transformation magics — fix errors, optimize, translate, generate tests and docs."""

from __future__ import annotations

from . import benchmark, fix, optimize, test_gen, todo, translate

__all__ = [
    "register_all",
    "benchmark",
    "fix",
    "optimize",
    "test_gen",
    "todo",
    "translate",
]


def register_all(ip) -> None:
    """Register all code transformation magics with the given IPython shell."""
    fix.register(ip)
    optimize.register(ip)
    translate.register(ip)
    test_gen.register(ip)
    todo.register(ip)
    benchmark.register(ip)

"""Shared fixtures for jiuwenswarm_jupyter unit tests."""

from __future__ import annotations

import pytest


class MockHistoryManager:
    """Minimal history_manager stub."""

    def __init__(self, history: list | None = None) -> None:
        # Each entry: (session_no, line_no, source)
        self._history: list = history or []

    def get_tail(self, n: int = 1000, include_latest: bool = False):
        return list(self._history[-n:])


class MockIPython:
    """Minimal IPython shell stub used across all test modules."""

    def __init__(self, history: list | None = None) -> None:
        self.user_ns: dict = {}
        self._magics: dict = {}
        self.history_manager = MockHistoryManager(history)

    # ------------------------------------------------------------------
    # Magic registration helpers
    # ------------------------------------------------------------------

    def register_magic_function(self, func=None, magic_kind: str = "line", magic_name: str | None = None):
        """Supports both ``@ip.register_magic_function`` and direct call forms."""
        if func is None:
            # Should not happen in production code but guard anyway
            def _deco(f):
                self._magics[magic_name or f.__name__] = f
                return f
            return _deco
        name = magic_name or func.__name__
        self._magics[name] = func
        return func

    def call_magic(self, name: str, line: str = "", cell: str | None = None):
        """Invoke a registered magic by name."""
        fn = self._magics[name]
        if cell is not None:
            return fn(line, cell)
        return fn(line)

    def has_magic(self, name: str) -> bool:
        return name in self._magics


@pytest.fixture
def ip():
    """Return a fresh MockIPython shell for each test."""
    return MockIPython()


@pytest.fixture
def ip_with_history():
    """Return a MockIPython with three pre-populated history entries."""
    history = [
        (1, 1, "import pandas as pd"),
        (1, 2, "df = pd.read_csv('data.csv')"),
        (1, 3, "print(df.head())"),
    ]
    shell = MockIPython(history=history)
    shell.user_ns["Out"] = {2: "   col1 col2\n0   1    2"}
    return shell

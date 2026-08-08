"""Unit tests for jiuwenswarm_jupyter.magic."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest

from jiuwenswarm_jupyter.magic import (
    register_magics,
    _make_parser,
    _run_magic,
)
from .conftest import MockIPython


# ── Parser ─────────────────────────────────────────────────────────────────────

class TestParser:
    def setup_method(self):
        self.parser = _make_parser()

    def test_default_mode_is_none(self):
        args = self.parser.parse_args([])
        assert args.mode is None

    def test_set_mode_long(self):
        args = self.parser.parse_args(["--mode", "code"])
        assert args.mode == "code"

    def test_set_mode_short(self):
        args = self.parser.parse_args(["-m", "team"])
        assert args.mode == "team"

    def test_default_timeout(self):
        args = self.parser.parse_args([])
        assert args.timeout == 300.0

    def test_set_timeout(self):
        args = self.parser.parse_args(["--timeout", "600"])
        assert args.timeout == 600.0

    def test_no_context_flag(self):
        args = self.parser.parse_args(["--no-context"])
        assert args.no_context is True

    def test_default_no_context_is_false(self):
        args = self.parser.parse_args([])
        assert args.no_context is False

    def test_session_flag(self):
        args = self.parser.parse_args(["--session", "research"])
        assert args.session == "research"

    def test_session_short_flag(self):
        args = self.parser.parse_args(["-s", "coding"])
        assert args.session == "coding"

    def test_all_modes_are_valid(self):
        for mode in ("agent", "code", "team", "code.team"):
            args = self.parser.parse_args(["--mode", mode])
            assert args.mode == mode


# ── register_magics ────────────────────────────────────────────────────────────

class TestRegisterMagics:
    def setup_method(self):
        self.ip = MockIPython()
        register_magics(self.ip)

    def test_jiuwen_magic_registered(self):
        assert self.ip.has_magic("jiuwen")

    def test_jiuwen_error_magic_registered(self):
        assert self.ip.has_magic("jiuwen_error")

    def test_jiuwen_clear_magic_registered(self):
        assert self.ip.has_magic("jiuwen_clear")

    def test_jiuwen_save_not_registered(self):
        """%jiuwen_save was removed — it must not be registered."""
        assert not self.ip.has_magic("jiuwen_save")


# ── _run_magic (%%jiuwen body) ─────────────────────────────────────────────────

class TestRunMagic:
    def setup_method(self):
        self.ip = MockIPython()

    def _mock_swarm(self):
        swarm = MagicMock()
        swarm.run_sync.return_value = "mock response"
        return swarm

    def test_empty_cell_prints_usage(self, capsys):
        _run_magic(self.ip, "", cell="")
        out = capsys.readouterr().out
        assert "Usage" in out

    def test_empty_cell_does_not_call_run_sync(self):
        with patch("jiuwenswarm_jupyter.magic.get_default_swarm") as mock_get:
            _run_magic(self.ip, "", cell="")
        mock_get.assert_not_called()

    def test_calls_run_sync_with_query(self):
        swarm = self._mock_swarm()
        with patch("jiuwenswarm_jupyter.magic.get_default_swarm", return_value=swarm):
            _run_magic(self.ip, "", cell="What is df?")
        swarm.run_sync.assert_called_once()
        call_kwargs = swarm.run_sync.call_args
        assert "What is df?" in call_kwargs[0] or "What is df?" == call_kwargs[0][0]

    def test_passes_mode_from_args(self):
        swarm = self._mock_swarm()
        with patch("jiuwenswarm_jupyter.magic.get_default_swarm", return_value=swarm):
            _run_magic(self.ip, "--mode code", cell="Write a function.")
        _, kwargs = swarm.run_sync.call_args
        assert kwargs.get("mode") == "code"

    def test_uses_named_swarm_when_session_given(self):
        swarm = self._mock_swarm()
        with patch("jiuwenswarm_jupyter.magic.get_named_swarm", return_value=swarm) as mock_named, \
             patch("jiuwenswarm_jupyter.magic.get_default_swarm") as mock_default:
            _run_magic(self.ip, "--session research", cell="Find papers.")
        mock_named.assert_called_once_with("research")
        mock_default.assert_not_called()

    def test_no_context_flag_passed_to_run_sync(self):
        swarm = self._mock_swarm()
        with patch("jiuwenswarm_jupyter.magic.get_default_swarm", return_value=swarm):
            _run_magic(self.ip, "--no-context", cell="Question.")
        _, kwargs = swarm.run_sync.call_args
        assert kwargs.get("inject_context") is False

    def test_keyboard_interrupt_is_caught(self, capsys):
        swarm = self._mock_swarm()
        swarm.run_sync.side_effect = KeyboardInterrupt()
        with patch("jiuwenswarm_jupyter.magic.get_default_swarm", return_value=swarm):
            # Must not propagate KeyboardInterrupt
            _run_magic(self.ip, "", cell="A query.")
        out = capsys.readouterr().out
        assert "cancelled" in out.lower()

    def test_bad_mode_prints_help(self, capsys):
        _run_magic(self.ip, "--mode invalid_mode", cell="Query.")
        out = capsys.readouterr().out
        # argparse error triggers help print
        assert len(out) > 0


# ── %jiuwen_error ──────────────────────────────────────────────────────────────

class TestJiuwenErrorMagic:
    def setup_method(self):
        self.ip = MockIPython()
        register_magics(self.ip)

    def test_no_exception_prints_message(self, capsys):
        self.ip.call_magic("jiuwen_error", "")
        out = capsys.readouterr().out
        assert "no exception" in out.lower() or "no error" in out.lower()

    def test_with_exception_calls_run_sync(self):
        swarm = MagicMock()
        swarm.run_sync.return_value = ""

        exc = ValueError("test error")
        with patch("sys.last_type", ValueError), \
             patch("sys.last_value", exc), \
             patch("sys.last_traceback", None), \
             patch("jiuwenswarm_jupyter.magic.get_default_swarm", return_value=swarm):
            self.ip.call_magic("jiuwen_error", "")

        swarm.run_sync.assert_called_once()
        query_arg = swarm.run_sync.call_args[0][0]
        assert "ValueError" in query_arg or "test error" in query_arg

    def test_extra_note_appended_to_query(self):
        swarm = MagicMock()
        swarm.run_sync.return_value = ""

        exc = ValueError("boom")
        with patch("sys.last_type", ValueError), \
             patch("sys.last_value", exc), \
             patch("sys.last_traceback", None), \
             patch("jiuwenswarm_jupyter.magic.get_default_swarm", return_value=swarm):
            self.ip.call_magic("jiuwen_error", "also check the dtype")

        query_arg = swarm.run_sync.call_args[0][0]
        assert "also check the dtype" in query_arg

    def test_keyboard_interrupt_is_caught(self):
        swarm = MagicMock()
        swarm.run_sync.side_effect = KeyboardInterrupt()

        exc = ValueError("boom")
        with patch("sys.last_type", ValueError), \
             patch("sys.last_value", exc), \
             patch("sys.last_traceback", None), \
             patch("jiuwenswarm_jupyter.magic.get_default_swarm", return_value=swarm):
            # Must not propagate
            self.ip.call_magic("jiuwen_error", "")


# ── %jiuwen_clear ──────────────────────────────────────────────────────────────

class TestJiuwenClearMagic:
    def setup_method(self):
        self.ip = MockIPython()
        register_magics(self.ip)

    def test_clear_default_prints_new_session_id(self, capsys):
        fresh_swarm = MagicMock()
        fresh_swarm.session_id = "jupyter_fresh123"

        with patch("jiuwenswarm_jupyter.magic.clear_session") as mock_clear, \
             patch("jiuwenswarm_jupyter.magic.get_default_swarm", return_value=fresh_swarm):
            self.ip.call_magic("jiuwen_clear", "")

        mock_clear.assert_called_once_with(None)
        out = capsys.readouterr().out
        assert "jupyter_fresh123" in out

    def test_clear_named_calls_clear_session_with_name(self, capsys):
        with patch("jiuwenswarm_jupyter.magic.clear_session") as mock_clear:
            self.ip.call_magic("jiuwen_clear", "research")

        mock_clear.assert_called_once_with("research")
        out = capsys.readouterr().out
        assert "research" in out

    def test_clear_default_updates_user_ns(self):
        fresh_swarm = MagicMock()
        fresh_swarm.session_id = "jupyter_new"

        with patch("jiuwenswarm_jupyter.magic.clear_session"), \
             patch("jiuwenswarm_jupyter.magic.get_default_swarm", return_value=fresh_swarm):
            self.ip.call_magic("jiuwen_clear", "")

        assert self.ip.user_ns.get("_jiuwen") is fresh_swarm

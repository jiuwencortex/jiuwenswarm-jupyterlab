"""Unit tests for jiuwenswarm_jupyter.session."""

from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from jiuwenswarm_jupyter.session import (
    make_session_id,
    clear_session,
    get_named_swarm,
    save_session_for_restart,
    restore_session_from_restart,
    _load_persisted,
    _save_persisted,
    _registry,
    _lock,
    _default_key,
)


# ── make_session_id ────────────────────────────────────────────────────────────

class TestMakeSessionId:
    def test_default_format(self):
        sid = make_session_id()
        assert sid.startswith("jupyter_")
        assert len(sid) > len("jupyter_")

    def test_named_format(self):
        sid = make_session_id("research")
        assert sid == "jupyter_research"

    def test_unique_without_name(self):
        ids = {make_session_id() for _ in range(20)}
        assert len(ids) == 20  # all unique


# ── get_named_swarm ────────────────────────────────────────────────────────────

class TestGetNamedSwarm:
    def setup_method(self):
        # Clear registry before each test to avoid cross-test contamination.
        with _lock:
            _registry.clear()

    @patch("jiuwenswarm_jupyter.session.JupyterSwarm")
    def test_creates_new_swarm(self, MockSwarm):
        mock_instance = MagicMock()
        mock_instance.session_id = "jupyter_test"
        MockSwarm.return_value = mock_instance

        swarm = get_named_swarm("test")
        MockSwarm.assert_called_once()
        assert swarm is mock_instance

    @patch("jiuwenswarm_jupyter.session.JupyterSwarm")
    def test_returns_same_instance_on_second_call(self, MockSwarm):
        mock_instance = MagicMock()
        mock_instance.session_id = "jupyter_myname"
        MockSwarm.return_value = mock_instance

        s1 = get_named_swarm("myname")
        s2 = get_named_swarm("myname")
        assert s1 is s2
        MockSwarm.assert_called_once()  # only one creation

    @patch("jiuwenswarm_jupyter.session.JupyterSwarm")
    def test_different_names_create_different_swarms(self, MockSwarm):
        def _make_mock(session_id=None, mode="agent"):
            m = MagicMock()
            m.session_id = session_id or "jupyter_x"
            return m

        MockSwarm.side_effect = _make_mock

        s1 = get_named_swarm("alpha")
        s2 = get_named_swarm("beta")
        assert s1 is not s2


# ── clear_session ──────────────────────────────────────────────────────────────

class TestClearSession:
    def setup_method(self):
        with _lock:
            _registry.clear()

    @patch("jiuwenswarm_jupyter.session.JupyterSwarm")
    def test_clear_named_removes_from_registry(self, MockSwarm):
        mock_instance = MagicMock()
        mock_instance.session_id = "jupyter_myname"
        MockSwarm.return_value = mock_instance

        get_named_swarm("myname")
        assert "myname" in _registry

        clear_session("myname")
        assert "myname" not in _registry

    @patch("jiuwenswarm_jupyter.session.JupyterSwarm")
    @patch("jiuwenswarm_jupyter.session._save_persisted")
    def test_clear_default_removes_and_clears_persistence(self, mock_save, MockSwarm):
        mock_instance = MagicMock()
        mock_instance.session_id = "jupyter_abc"
        MockSwarm.return_value = mock_instance

        with _lock:
            _registry[_default_key] = mock_instance

        clear_session()
        assert _default_key not in _registry
        # _save_persisted should have been called to wipe the persisted entry
        mock_save.assert_called_once()

    def test_clear_nonexistent_does_not_raise(self):
        clear_session("nonexistent_session")  # must not raise


# ── Restart persistence ────────────────────────────────────────────────────────

class TestRestartPersistence:
    def test_save_and_restore_roundtrip(self, tmp_path):
        sessions_file = tmp_path / "jupyter_sessions.json"
        with patch("jiuwenswarm_jupyter.session._SESSIONS_FILE", sessions_file), \
             patch("jiuwenswarm_jupyter.session._notebook_key", return_value="/work/nb"):
            save_session_for_restart("jupyter_abc123")
            restored = restore_session_from_restart()
        assert restored == "jupyter_abc123"

    def test_restore_returns_none_when_no_entry(self, tmp_path):
        sessions_file = tmp_path / "jupyter_sessions.json"
        with patch("jiuwenswarm_jupyter.session._SESSIONS_FILE", sessions_file), \
             patch("jiuwenswarm_jupyter.session._notebook_key", return_value="/work/nb"):
            restored = restore_session_from_restart()
        assert restored is None

    def test_restore_returns_none_for_expired_entry(self, tmp_path):
        sessions_file = tmp_path / "jupyter_sessions.json"
        # Write an entry that is older than 30 days
        old_ts = time.time() - (31 * 86400)
        data = {"/work/nb": {"session_id": "jupyter_old", "saved_at": old_ts}}
        sessions_file.write_text(json.dumps(data))

        with patch("jiuwenswarm_jupyter.session._SESSIONS_FILE", sessions_file), \
             patch("jiuwenswarm_jupyter.session._notebook_key", return_value="/work/nb"):
            restored = restore_session_from_restart()
        assert restored is None

    def test_restore_cleans_up_expired_entry(self, tmp_path):
        sessions_file = tmp_path / "jupyter_sessions.json"
        old_ts = time.time() - (31 * 86400)
        data = {"/work/nb": {"session_id": "jupyter_old", "saved_at": old_ts}}
        sessions_file.write_text(json.dumps(data))

        with patch("jiuwenswarm_jupyter.session._SESSIONS_FILE", sessions_file), \
             patch("jiuwenswarm_jupyter.session._notebook_key", return_value="/work/nb"):
            restore_session_from_restart()
            remaining = json.loads(sessions_file.read_text())
        assert "/work/nb" not in remaining

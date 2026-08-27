"""Unit tests for jiuwenswarm_jupyter.config."""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from jiuwenswarm_jupyter.config import JiuwenConfig, get_config, register_config_magic
from .conftest import MockIPython


# ── JiuwenConfig defaults ──────────────────────────────────────────────────────

class TestJiuwenConfigDefaults:
    def test_default_mode(self):
        cfg = JiuwenConfig()
        assert cfg.mode == "agent"

    def test_default_timeout(self):
        cfg = JiuwenConfig()
        assert cfg.timeout == 300

    def test_default_inject_context(self):
        cfg = JiuwenConfig()
        assert cfg.inject_context is True

    def test_default_model_is_none(self):
        cfg = JiuwenConfig()
        assert cfg.model is None


# ── JiuwenConfig.update ────────────────────────────────────────────────────────

class TestJiuwenConfigUpdate:
    def test_set_mode(self):
        cfg = JiuwenConfig()
        errors = cfg.update(mode="code")
        assert errors == []
        assert cfg.mode == "code"

    def test_set_timeout_as_string(self):
        cfg = JiuwenConfig()
        errors = cfg.update(timeout="600")
        assert errors == []
        assert cfg.timeout == 600

    def test_set_inject_context_false(self):
        cfg = JiuwenConfig()
        errors = cfg.update(inject_context="false")
        assert errors == []
        assert cfg.inject_context is False

    def test_set_inject_context_true_variants(self):
        for truthy in ("true", "True", "1", "yes", "on"):
            cfg = JiuwenConfig()
            cfg.update(inject_context="false")  # set to False first
            cfg.update(inject_context=truthy)
            assert cfg.inject_context is True, f"Expected True for {truthy!r}"

    def test_set_inject_context_false_variants(self):
        for falsy in ("false", "False", "0", "no", "off"):
            cfg = JiuwenConfig()
            cfg.update(inject_context=falsy)
            assert cfg.inject_context is False, f"Expected False for {falsy!r}"

    def test_unknown_key_returns_error(self):
        cfg = JiuwenConfig()
        errors = cfg.update(nonexistent_key="value")
        assert len(errors) == 1
        assert "nonexistent_key" in errors[0]

    def test_invalid_timeout_type_returns_error(self):
        cfg = JiuwenConfig()
        errors = cfg.update(timeout="not_a_number")
        assert len(errors) == 1
        assert "timeout" in errors[0]

    def test_multiple_valid_keys(self):
        cfg = JiuwenConfig()
        errors = cfg.update(mode="team", timeout="600")
        assert errors == []
        assert cfg.mode == "team"
        assert cfg.timeout == 600

    def test_partial_failure_does_not_update_good_key(self):
        """If a later key fails, the first key update has still been applied."""
        cfg = JiuwenConfig()
        errors = cfg.update(mode="code", timeout="bad")
        # mode update succeeded, timeout failed
        assert cfg.mode == "code"
        assert cfg.timeout == 300  # unchanged
        assert len(errors) == 1


# ── JiuwenConfig.summary ──────────────────────────────────────────────────────

class TestJiuwenConfigSummary:
    def test_summary_contains_all_fields(self):
        cfg = JiuwenConfig()
        summary = cfg.summary()
        for field in ("mode", "timeout", "inject_context", "model"):
            assert field in summary


# ── get_config ─────────────────────────────────────────────────────────────────

class TestGetConfig:
    def test_creates_default_when_absent(self, ip):
        cfg = get_config(ip)
        assert isinstance(cfg, JiuwenConfig)
        assert "_jiuwen_config" in ip.user_ns

    def test_returns_same_instance_on_second_call(self, ip):
        cfg1 = get_config(ip)
        cfg2 = get_config(ip)
        assert cfg1 is cfg2

    def test_returns_existing_instance(self, ip):
        existing = JiuwenConfig(mode="code")
        ip.user_ns["_jiuwen_config"] = existing
        cfg = get_config(ip)
        assert cfg is existing


# ── %jiuwen_config magic ──────────────────────────────────────────────────────

class TestJiuwenConfigMagic:
    def setup_method(self):
        self.ip = MockIPython()
        register_config_magic(self.ip)

    def _call(self, line: str) -> None:
        self.ip.call_magic("jiuwen_config", line)

    def test_magic_is_registered(self):
        assert self.ip.has_magic("jiuwen_config")

    def test_show_prints_summary(self, capsys):
        self._call("")
        out = capsys.readouterr().out
        assert "mode" in out
        assert "timeout" in out

    def test_set_mode(self):
        self._call("mode=code")
        cfg = get_config(self.ip)
        assert cfg.mode == "code"

    def test_set_timeout(self):
        self._call("timeout=600")
        cfg = get_config(self.ip)
        assert cfg.timeout == 600

    def test_set_inject_context_false(self):
        self._call("inject_context=false")
        cfg = get_config(self.ip)
        assert cfg.inject_context is False

    def test_reset_restores_defaults(self):
        self._call("mode=code")
        self._call("reset")
        cfg = get_config(self.ip)
        assert cfg.mode == "agent"
        assert cfg.timeout == 300

    def test_unknown_key_prints_error(self, capsys):
        self._call("bad_key=value")
        out = capsys.readouterr().out
        assert "bad_key" in out

    def test_missing_equals_prints_error(self, capsys):
        self._call("mode")
        out = capsys.readouterr().out
        assert "key=value" in out

    def test_propagates_mode_to_swarm(self):
        mock_swarm = MagicMock()
        mock_swarm.mode = "agent"
        self.ip.user_ns["_jiuwen"] = mock_swarm
        self._call("mode=code")
        assert mock_swarm.mode == "code"

    def test_propagates_timeout_to_swarm(self):
        mock_swarm = MagicMock()
        mock_swarm.timeout = 300.0
        self.ip.user_ns["_jiuwen"] = mock_swarm
        self._call("timeout=900")
        assert mock_swarm.timeout == 900

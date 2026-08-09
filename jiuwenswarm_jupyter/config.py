"""
Per-notebook configuration for jiuwenswarm_jupyter.

Usage:
    %jiuwen_config                         # show current settings
    %jiuwen_config mode=code               # set agent mode
    %jiuwen_config mode=team timeout=600   # multiple settings at once
    %jiuwen_config inject_context=false    # disable auto context injection
    %jiuwen_config reset                   # restore all defaults
"""
from __future__ import annotations

import shlex
from dataclasses import dataclass, field, fields
from typing import Any


@dataclass
class JiuwenConfig:
    """Per-notebook configuration stored in the IPython namespace as ``_jiuwen_config``."""

    mode: str = "agent"
    """Agent mode: agent | code | team | code.team"""

    timeout: int = 300
    """Request timeout in seconds."""

    inject_context: bool = True
    """Automatically inject notebook variables, DataFrames, and cell history."""

    model: str | None = None
    """Override the default LLM model (None = use JiuwenSwarm default)."""

    pinned_vars: list = field(default_factory=list)
    """Variable names always injected into context regardless of auto-context sweep."""

    def update(self, **kwargs: Any) -> list[str]:
        """Apply ``key=value`` updates. Returns a list of error strings (empty = success)."""
        errors: list[str] = []
        valid = {f.name: f for f in fields(self)}
        for key, raw in kwargs.items():
            if key not in valid:
                errors.append(
                    f"Unknown config key {key!r}. Valid keys: {', '.join(valid)}"
                )
                continue
            f = valid[key]
            try:
                origin = f.type
                if origin in (bool, "bool") or "bool" in str(origin):
                    coerced: Any = raw.lower() not in ("false", "0", "no", "off")
                elif origin in (int, "int") or "int" in str(origin):
                    coerced = int(raw)
                elif "None" in str(origin):  # Optional[str]
                    coerced = None if raw.lower() in ("none", "null", "") else raw
                else:
                    coerced = raw
                setattr(self, key, coerced)
            except (ValueError, TypeError) as exc:
                errors.append(f"Bad value for {key!r}: {exc}")
        return errors

    def summary(self) -> str:
        lines = ["JiuwenSwarm notebook config:"]
        for f in fields(self):
            val = getattr(self, f.name)
            lines.append(f"  {f.name:20s} = {val!r}")
        return "\n".join(lines)


def get_config(ip=None) -> JiuwenConfig:
    """Return the per-notebook :class:`JiuwenConfig`, creating defaults if absent."""
    if ip is None:
        try:
            ip = get_ipython()  # type: ignore[name-defined]  # noqa: F821
        except NameError:
            return JiuwenConfig()
    if "_jiuwen_config" not in ip.user_ns:
        ip.user_ns["_jiuwen_config"] = JiuwenConfig()
    return ip.user_ns["_jiuwen_config"]  # type: ignore[return-value]


def register_config_magic(ip) -> None:
    """Register the ``%jiuwen_config`` line magic on *ip*."""

    def jiuwen_config(line: str) -> None:
        """Configure JiuwenSwarm notebook defaults.

        Usage::

            %jiuwen_config                       # show current config
            %jiuwen_config mode=code             # switch to code agent
            %jiuwen_config mode=team timeout=600 # multi-agent with longer timeout
            %jiuwen_config inject_context=false  # disable context injection
            %jiuwen_config reset                 # restore defaults
        """
        cfg = get_config(ip)
        line = line.strip()

        if not line or line == "show":
            print(cfg.summary())
            return

        if line == "reset":
            ip.user_ns["_jiuwen_config"] = JiuwenConfig()
            # Propagate to default swarm if it exists
            if "_jiuwen" in ip.user_ns:
                swarm = ip.user_ns["_jiuwen"]
                defaults = JiuwenConfig()
                swarm.mode = defaults.mode
                swarm.timeout = defaults.timeout
            print("Config reset to defaults.")
            return

        # Parse key=value tokens
        try:
            tokens = shlex.split(line)
        except ValueError as exc:
            print(f"Parse error: {exc}")
            return

        kwargs: dict[str, str] = {}
        for token in tokens:
            if "=" not in token:
                print(f"Expected key=value, got {token!r}. Try: %jiuwen_config show")
                return
            k, _, v = token.partition("=")
            kwargs[k.strip()] = v.strip()

        errors = cfg.update(**kwargs)
        if errors:
            for err in errors:
                print(err)
            return

        # Propagate relevant settings to the live default swarm
        if "_jiuwen" in ip.user_ns:
            swarm = ip.user_ns["_jiuwen"]
            if "mode" in kwargs:
                swarm.mode = cfg.mode
            if "timeout" in kwargs:
                swarm.timeout = cfg.timeout

        print(cfg.summary())

    ip.register_magic_function(jiuwen_config, magic_kind="line", magic_name="jiuwen_config")

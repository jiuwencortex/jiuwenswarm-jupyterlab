"""IPython cell and line magic for JiuwenSwarm.

Provides:
    %%jiuwen [--mode MODE] [--session NAME] [--no-context] [--timeout SECS]
        Cell magic: send the cell body to the agent, stream response below.

    %jiuwen <query>
        Line magic: send a single-line query to the agent.
"""

from __future__ import annotations

import argparse
import shlex
import textwrap

from IPython.core.magic import register_cell_magic, register_line_magic  # type: ignore[import]
from IPython.core.magic_arguments import magic_arguments, argument, parse_argstring  # type: ignore[import]


_DESCRIPTION = textwrap.dedent("""\
    Send a query to JiuwenSwarm directly from a Jupyter cell.

    Cell body is the user message. Any options go on the %% line.

    Examples
    --------
    %%jiuwen
    Explain the df variable loaded above.

    %%jiuwen --mode code
    Write a train/test split for df using stratified sampling.

    %%jiuwen --mode team --session research
    Research the top 3 XGBoost alternatives and benchmark each.
""")


def _make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="%%jiuwen",
        description=_DESCRIPTION,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False,
    )
    parser.add_argument(
        "--mode", "-m",
        default=None,
        choices=["agent", "code", "team", "code.team"],
        help="Agent mode (default: agent)",
    )
    parser.add_argument(
        "--session", "-s",
        default=None,
        metavar="NAME",
        help="Named session to reuse across cells",
    )
    parser.add_argument(
        "--no-context",
        dest="no_context",
        action="store_true",
        help="Skip automatic notebook context injection",
    )
    parser.add_argument(
        "--timeout", "-t",
        type=float,
        default=300.0,
        metavar="SECS",
        help="Request timeout in seconds (default: 300)",
    )
    return parser


_parser = _make_parser()


def register_magics(ip) -> None:
    """Register %%jiuwen, %jiuwen, %jiuwen_error, and %jiuwen_save with the given IPython shell."""

    @ip.register_magic_function
    def jiuwen(line, cell=None):
        """JiuwenSwarm cell magic — %%jiuwen or %jiuwen."""
        _run_magic(ip, line, cell)

    # Make it available as both line and cell magic
    ip.register_magic_function(jiuwen, magic_kind="cell", magic_name="jiuwen")
    ip.register_magic_function(jiuwen, magic_kind="line", magic_name="jiuwen")

    _register_error_magic(ip)
    _register_save_magic(ip)


def _register_error_magic(ip) -> None:
    """Register %jiuwen_error: forward the last exception to the agent."""

    @ip.register_magic_function
    def jiuwen_error(line: str) -> None:
        """Send the last notebook exception to JiuwenSwarm for debugging.

        Usage::

            %jiuwen_error                  # send last error, ask for a fix
            %jiuwen_error explain why      # add your own question
        """
        import sys
        import traceback as _tb

        exc_type = getattr(sys, "last_type", None)
        exc_value = getattr(sys, "last_value", None) or getattr(sys, "last_exc", None)
        exc_tb = getattr(sys, "last_traceback", None)

        if exc_value is None:
            print("No exception recorded. Run a cell that produces an error first.")
            return

        # Format traceback
        if exc_tb is not None:
            tb_lines = _tb.format_exception(exc_type, exc_value, exc_tb)
        else:
            tb_lines = [f"{exc_type.__name__}: {exc_value}"]
        tb_str = "".join(tb_lines).strip()

        # Last executed cell
        last_source = ""
        try:
            hist = list(ip.history_manager.get_tail(n=1, include_latest=True))
            if hist:
                _, _, last_source = hist[-1]
                last_source = last_source.strip()
        except Exception:
            pass

        extra = line.strip()
        parts: list[str] = ["I got an error in my Jupyter notebook. Please help me fix it.\n"]
        if last_source:
            parts.append(f"**Failing cell:**\n```python\n{last_source}\n```\n")
        parts.append(f"**Error:**\n```\n{tb_str}\n```")
        if extra:
            parts.append(f"\n{extra}")

        from .session import get_default_swarm
        swarm = get_default_swarm(ip)
        swarm.run_sync("\n".join(parts), inject_context=True, ip=ip)


def _register_save_magic(ip) -> None:
    """Register %jiuwen_save: persist or restore the current session ID."""

    @ip.register_magic_function
    def jiuwen_save(line: str) -> None:
        """Save or load the current JiuwenSwarm session so it can be shared or resumed.

        The session ID is the only thing that needs to be stored — the full
        conversation history lives on the JiuwenSwarm server and is looked up
        by session ID automatically.

        Usage::

            %jiuwen_save                      # save to ./jiuwen_session.json
            %jiuwen_save path/to/file.json    # save to a specific path
            %jiuwen_save load                 # load from ./jiuwen_session.json
            %jiuwen_save load path/to/file.json  # load from a specific path
        """
        import json
        import os
        import time

        from .session import get_default_swarm

        parts = line.strip().split(None, 1)
        command = parts[0].lower() if parts else "save"
        arg = parts[1].strip() if len(parts) > 1 else ""

        # Resolve file path
        if command == "load":
            filepath = arg or "jiuwen_session.json"
            _load_session(ip, filepath)
        else:
            # "save" or bare invocation (first token is a path, not a command)
            if command not in ("save",):
                # treat the first token as a path, not a command keyword
                filepath = command if command else "jiuwen_session.json"
                if arg:
                    filepath = f"{command} {arg}".strip()
            else:
                filepath = arg or "jiuwen_session.json"
            _save_session(ip, filepath)


def _save_session(ip, filepath: str) -> None:
    import json, time
    from .session import get_default_swarm

    swarm = get_default_swarm(ip)
    data = {
        "session_id": swarm.session_id,
        "saved_at": time.time(),
        "mode": swarm.mode,
        "note": "Restore with: %jiuwen_save load " + filepath,
    }
    try:
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        print(f"[jiuwenswarm] Session saved to {filepath!r}")
        print(f"  session_id : {swarm.session_id}")
        print(f"  mode       : {swarm.mode}")
    except OSError as exc:
        print(f"[jiuwenswarm] Could not save session: {exc}")


def _load_session(ip, filepath: str) -> None:
    import json
    from .client import JupyterSwarm
    from .session import _lock, _registry, _default_key, save_session_for_restart

    try:
        with open(filepath) as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[jiuwenswarm] Could not load session from {filepath!r}: {exc}")
        return

    session_id = data.get("session_id")
    if not session_id:
        print(f"[jiuwenswarm] File {filepath!r} does not contain a session_id.")
        return

    mode = data.get("mode", "agent")
    swarm = JupyterSwarm(session_id=session_id, mode=mode)

    with _lock:
        _registry[_default_key] = swarm

    ip.user_ns["_jiuwen"] = swarm
    save_session_for_restart(session_id)

    print(f"[jiuwenswarm] Restored session from {filepath!r}")
    print(f"  session_id : {session_id}")
    print(f"  mode       : {mode}")


def _run_magic(ip, line: str, cell: str | None) -> None:
    from .session import get_default_swarm, get_named_swarm

    # Parse the options on the %% line
    try:
        args = _parser.parse_args(shlex.split(line) if line.strip() else [])
    except SystemExit:
        # argparse calls sys.exit on error; catch and show help instead
        print(_DESCRIPTION)
        return

    query = (cell or "").strip()
    if not query:
        print("Usage: %%jiuwen [--mode MODE] [--session NAME] [--no-context] [--timeout SECS]")
        print("Cell body: the question or instruction for the agent.")
        return

    # Resolve session
    if args.session:
        swarm = get_named_swarm(args.session)
    else:
        swarm = get_default_swarm(ip)

    # Run (synchronous wrapper because cell magics cannot be async)
    swarm.run_sync(
        query,
        mode=args.mode,
        inject_context=not args.no_context,
        timeout=args.timeout,
        ip=ip,
    )

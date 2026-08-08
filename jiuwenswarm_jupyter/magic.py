"""IPython cell and line magic for JiuwenSwarm.

Provides:
    %%jiuwen [--mode MODE] [--session NAME] [--no-context] [--timeout SECS]
        Cell magic: send the cell body to the agent, stream response below.

    %jiuwen <query>
        Line magic: send a single-line query to the agent.

    %jiuwen_error [note]
        Forward the last exception to the agent for debugging.

    %jiuwen_clear [session_name]
        Reset the current or named session, starting a fresh conversation.
"""

from __future__ import annotations

import argparse
import shlex
import textwrap

from IPython.core.magic import register_cell_magic, register_line_magic  # type: ignore[import]


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
    """Register %%jiuwen, %jiuwen, %jiuwen_error, and %jiuwen_clear with the given IPython shell."""

    @ip.register_magic_function
    def jiuwen(line, cell=None):
        """JiuwenSwarm cell magic — %%jiuwen or %jiuwen."""
        _run_magic(ip, line, cell)

    # Make it available as both line and cell magic
    ip.register_magic_function(jiuwen, magic_kind="cell", magic_name="jiuwen")
    ip.register_magic_function(jiuwen, magic_kind="line", magic_name="jiuwen")

    _register_error_magic(ip)
    _register_clear_magic(ip)


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
        try:
            swarm.run_sync("\n".join(parts), inject_context=True, ip=ip)
        except KeyboardInterrupt:
            print("\n[JiuwenSwarm] Query cancelled.")


def _register_clear_magic(ip) -> None:
    """Register %jiuwen_clear: reset the current or named session."""

    @ip.register_magic_function
    def jiuwen_clear(line: str) -> None:
        """Clear the current or named JiuwenSwarm session.

        Discards the conversation history and creates a fresh session.
        The new session ID is printed so you can note it if needed.

        Usage::

            %jiuwen_clear                  # clear the default (current notebook) session
            %jiuwen_clear research         # clear a specific named session
        """
        from .session import clear_session, get_default_swarm

        name = line.strip() or None
        clear_session(name)

        if name:
            print(f"[JiuwenSwarm] Session '{name}' cleared. Next use will start fresh.")
        else:
            # Eagerly create the replacement so the user sees the new ID immediately.
            fresh = get_default_swarm(ip)
            ip.user_ns["_jiuwen"] = fresh
            print(f"[JiuwenSwarm] Default session cleared. New session: {fresh.session_id}")


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

    # Run (synchronous wrapper because cell magics cannot be async).
    # KeyboardInterrupt (Ctrl+C / Kernel → Interrupt) is caught here so the
    # magic exits cleanly without a traceback.
    try:
        swarm.run_sync(
            query,
            mode=args.mode,
            inject_context=not args.no_context,
            timeout=args.timeout,
            ip=ip,
        )
    except KeyboardInterrupt:
        print("\n[JiuwenSwarm] Query cancelled.")

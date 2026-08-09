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

    %jiuwen_export [filename]
        Export the current session's conversation history to a markdown file.

    %jiuwen_replay [N]
        Re-send the last N exchanges (default 3) as context to a fresh session.

    %jiuwen_pin var1 [var2 ...]
        Always inject the named variables into context, even with --no-context.

    %jiuwen_unpin [var1 var2 ...] | all
        Remove specific variables (or all) from the pinned list.
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
    """Register all JiuwenSwarm magics with the given IPython shell."""

    @ip.register_magic_function
    def jiuwen(line, cell=None):
        """JiuwenSwarm cell magic — %%jiuwen or %jiuwen."""
        _run_magic(ip, line, cell)

    # Make it available as both line and cell magic
    ip.register_magic_function(jiuwen, magic_kind="cell", magic_name="jiuwen")
    ip.register_magic_function(jiuwen, magic_kind="line", magic_name="jiuwen")

    _register_error_magic(ip)
    _register_clear_magic(ip)
    _register_export_magic(ip)
    _register_replay_magic(ip)
    _register_pin_magic(ip)
    _register_unpin_magic(ip)


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


def _register_export_magic(ip) -> None:
    """Register %jiuwen_export: save session history to a markdown file."""

    @ip.register_magic_function
    def jiuwen_export(line: str) -> None:
        """Export the current session's conversation history to a markdown file.

        Writes one H2 section per exchange with timestamp, mode, user query,
        and agent response.  The file is created in the current working directory.

        Usage::

            %jiuwen_export                          # writes jiuwen_session_<id>.md
            %jiuwen_export my_analysis_notes.md     # explicit filename
            %jiuwen_export --session research notes.md   # named session
        """
        import os
        import shlex as _shlex

        tokens = _shlex.split(line.strip()) if line.strip() else []

        session_name: str | None = None
        filename: str | None = None

        i = 0
        while i < len(tokens):
            if tokens[i] in ("--session", "-s") and i + 1 < len(tokens):
                session_name = tokens[i + 1]
                i += 2
            else:
                filename = tokens[i]
                i += 1

        from .session import get_default_swarm, get_named_swarm
        swarm = get_named_swarm(session_name) if session_name else get_default_swarm(ip)
        history = swarm.get_history()

        if not history:
            print("[JiuwenSwarm] No exchanges recorded in this session yet.")
            return

        if filename is None:
            filename = f"jiuwen_session_{swarm.session_id}.md"

        lines: list[str] = [
            f"# JiuwenSwarm Session Export",
            f"",
            f"**Session ID:** `{swarm.session_id}`  ",
            f"**Exchanges:** {len(history)}",
            f"",
        ]
        for i, entry in enumerate(history, 1):
            lines += [
                f"---",
                f"",
                f"## Exchange {i} — {entry['timestamp']} · mode: {entry['mode']}",
                f"",
                f"**User:**",
                f"",
                entry["query"],
                f"",
                f"**Assistant:**",
                f"",
                entry["response"],
                f"",
            ]

        path = os.path.join(os.getcwd(), filename)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines))

        print(f"[JiuwenSwarm] Exported {len(history)} exchange(s) to {path}")


def _register_replay_magic(ip) -> None:
    """Register %jiuwen_replay: re-send last N exchanges to a fresh session."""

    @ip.register_magic_function
    def jiuwen_replay(line: str) -> None:
        """Re-send the last N conversation exchanges as context to a fresh session.

        Useful when a conversation has gone off-topic: start clean but let the
        agent know what was already discussed.  The original session is unchanged.
        A new default session is created.

        Usage::

            %jiuwen_replay        # replay last 3 exchanges (default)
            %jiuwen_replay 5      # replay last 5 exchanges
        """
        from .session import get_default_swarm, clear_session

        n = 3
        arg = line.strip()
        if arg:
            try:
                n = int(arg)
            except ValueError:
                print(f"[JiuwenSwarm] Expected an integer, got {arg!r}. Using default (3).")

        old_swarm = get_default_swarm(ip)
        history = old_swarm.get_history()

        if not history:
            print("[JiuwenSwarm] No exchanges to replay. Run some %%jiuwen cells first.")
            return

        recent = history[-n:]

        # Build a summary of the exchanges to replay
        summary_parts: list[str] = [
            f"I am continuing a conversation. Here are the last {len(recent)} exchange(s) "
            f"for context. Please acknowledge and wait for my next question.\n"
        ]
        for i, entry in enumerate(recent, 1):
            summary_parts.append(
                f"**Exchange {i} ({entry['timestamp']}, mode={entry['mode']}):**\n"
                f"User: {entry['query']}\n"
                f"Assistant: {entry['response']}"
            )

        context_msg = "\n\n".join(summary_parts)

        # Clear old session and create fresh one
        clear_session()
        new_swarm = get_default_swarm(ip)
        ip.user_ns["_jiuwen"] = new_swarm

        print(f"[JiuwenSwarm] Replaying {len(recent)} exchange(s) into new session {new_swarm.session_id}…")
        try:
            new_swarm.run_sync(context_msg, inject_context=False, ip=ip)
        except KeyboardInterrupt:
            print("\n[JiuwenSwarm] Replay cancelled.")


def _register_pin_magic(ip) -> None:
    """Register %jiuwen_pin: always inject named variables into context."""

    @ip.register_magic_function
    def jiuwen_pin(line: str) -> None:
        """Pin variables so they are always injected into context.

        Pinned variables appear in a dedicated section regardless of whether
        ``--no-context`` is used or the variable would normally be filtered out.

        Usage::

            %jiuwen_pin df_train results_dict model
        """
        from .config import get_config

        names = line.strip().split()
        if not names:
            print("Usage: %jiuwen_pin var1 [var2 ...]")
            return

        cfg = get_config(ip)
        added: list[str] = []
        already: list[str] = []
        for name in names:
            if name in cfg.pinned_vars:
                already.append(name)
            else:
                cfg.pinned_vars.append(name)
                added.append(name)

        if added:
            print(f"[JiuwenSwarm] Pinned: {', '.join(added)}")
        if already:
            print(f"[JiuwenSwarm] Already pinned: {', '.join(already)}")
        print(f"[JiuwenSwarm] All pinned vars: {cfg.pinned_vars or '(none)'}")


def _register_unpin_magic(ip) -> None:
    """Register %jiuwen_unpin: remove variables from the pinned list."""

    @ip.register_magic_function
    def jiuwen_unpin(line: str) -> None:
        """Remove variables from the pinned context list.

        Usage::

            %jiuwen_unpin df_train          # unpin one variable
            %jiuwen_unpin df_train results  # unpin several
            %jiuwen_unpin all               # clear all pinned variables
        """
        from .config import get_config

        cfg = get_config(ip)
        arg = line.strip()

        if not arg:
            print("Usage: %jiuwen_unpin var1 [var2 ...] | all")
            return

        if arg == "all":
            cfg.pinned_vars.clear()
            print("[JiuwenSwarm] All pinned variables cleared.")
            return

        names = arg.split()
        removed: list[str] = []
        not_found: list[str] = []
        for name in names:
            if name in cfg.pinned_vars:
                cfg.pinned_vars.remove(name)
                removed.append(name)
            else:
                not_found.append(name)

        if removed:
            print(f"[JiuwenSwarm] Unpinned: {', '.join(removed)}")
        if not_found:
            print(f"[JiuwenSwarm] Not in pinned list: {', '.join(not_found)}")
        print(f"[JiuwenSwarm] Remaining pinned vars: {cfg.pinned_vars or '(none)'}")


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

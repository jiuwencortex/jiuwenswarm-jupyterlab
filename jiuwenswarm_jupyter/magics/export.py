"""The ``%jiuwen_export`` line magic — save session history to a markdown file."""

from __future__ import annotations


def register(ip) -> None:
    """Register ``%jiuwen_export`` with the given IPython shell."""

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

        from ..session import get_default_swarm, get_named_swarm
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

    ip.register_magic_function(jiuwen_export, magic_kind="line", magic_name="jiuwen_export")

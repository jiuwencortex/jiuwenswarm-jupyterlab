"""The ``%jiuwen_clear`` line magic — reset the current or named session."""

from __future__ import annotations


def register(ip) -> None:
    """Register ``%jiuwen_clear`` with the given IPython shell."""

    def jiuwen_clear(line: str) -> None:
        """Clear the current or named JiuwenSwarm session.

        Discards the conversation history and creates a fresh session.
        The new session ID is printed so you can note it if needed.

        Usage::

            %jiuwen_clear                  # clear the default (current notebook) session
            %jiuwen_clear research         # clear a specific named session
        """
        from ..session import clear_session, get_default_swarm

        name = line.strip() or None
        clear_session(name)

        if name:
            print(f"[JiuwenSwarm] Session '{name}' cleared. Next use will start fresh.")
        else:
            # Eagerly create the replacement so the user sees the new ID immediately.
            fresh = get_default_swarm(ip)
            ip.user_ns["_jiuwen"] = fresh
            print(f"[JiuwenSwarm] Default session cleared. New session: {fresh.session_id}")

    ip.register_magic_function(jiuwen_clear, magic_kind="line", magic_name="jiuwen_clear")

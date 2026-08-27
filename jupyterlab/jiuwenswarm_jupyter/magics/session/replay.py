"""The ``%jiuwen_replay`` line magic — re-send last N exchanges to a fresh session."""

from __future__ import annotations


def register(ip) -> None:
    """Register ``%jiuwen_replay`` with the given IPython shell."""

    def jiuwen_replay(line: str) -> None:
        """Re-send the last N conversation exchanges as context to a fresh session.

        Useful when a conversation has gone off-topic: start clean but let the
        agent know what was already discussed.  The original session is unchanged.
        A new default session is created.

        Usage::

            %jiuwen_replay        # replay last 3 exchanges (default)
            %jiuwen_replay 5      # replay last 5 exchanges
        """
        from ...session import get_default_swarm, clear_session

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

    ip.register_magic_function(jiuwen_replay, magic_kind="line", magic_name="jiuwen_replay")

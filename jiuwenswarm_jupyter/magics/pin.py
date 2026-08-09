"""The ``%jiuwen_pin`` line magic — always inject named variables into context."""

from __future__ import annotations


def register(ip) -> None:
    """Register ``%jiuwen_pin`` with the given IPython shell."""

    def jiuwen_pin(line: str) -> None:
        """Pin variables so they are always injected into context.

        Pinned variables appear in a dedicated section regardless of whether
        ``--no-context`` is used or the variable would normally be filtered out.

        Usage::

            %jiuwen_pin df_train results_dict model
        """
        from ..config import get_config

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

    ip.register_magic_function(jiuwen_pin, magic_kind="line", magic_name="jiuwen_pin")

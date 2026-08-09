"""The ``%jiuwen_unpin`` line magic — remove variables from the pinned list."""

from __future__ import annotations


def register(ip) -> None:
    """Register ``%jiuwen_unpin`` with the given IPython shell."""

    def jiuwen_unpin(line: str) -> None:
        """Remove variables from the pinned context list.

        Usage::

            %jiuwen_unpin df_train          # unpin one variable
            %jiuwen_unpin df_train results  # unpin several
            %jiuwen_unpin all               # clear all pinned variables
        """
        from ..config import get_config

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

    ip.register_magic_function(jiuwen_unpin, magic_kind="line", magic_name="jiuwen_unpin")

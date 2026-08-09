"""The ``%jiuwen_fix`` line magic — rewrite the last failing cell to fix the error."""

from __future__ import annotations

import sys


def register(ip) -> None:
    """Register ``%jiuwen_fix`` with the given IPython shell."""

    def jiuwen_fix(line: str) -> None:
        """Fix the last Python error by rewriting the failing cell in-place.

        Reads the last traceback and the source of the last executed cell,
        sends both to the agent, and replaces the cell with a corrected version.
        The original cell is preserved until the fix is applied.

        Arguments
        ---------
        HINT        Optional free-text hint for the agent.

        Usage::

            %jiuwen_fix
            %jiuwen_fix the column dtype is str not int
            %jiuwen_fix avoid using inplace=True
        """
        hint = line.strip()

        exc = getattr(sys, "last_value", None)
        if exc is None:
            print("[JiuwenSwarm] No recent exception found. Run a failing cell first.")
            return

        exc_type = type(exc).__name__
        exc_msg = str(exc)

        try:
            history = list(ip.history_manager.get_range(output=False))
            last_src = history[-1][2] if history else ""
        except Exception:
            last_src = ""

        if not last_src:
            print("[JiuwenSwarm] Could not retrieve last cell source.")
            return

        hint_note = f"\n\nHint from user: {hint}" if hint else ""

        query = (
            f"Fix the following Python code that raised `{exc_type}: {exc_msg}`.\n\n"
            "Rules:\n"
            "- Return ONLY the corrected Python code, no explanation, no markdown fences.\n"
            "- Preserve the original logic and variable names.\n"
            "- Use `replace_notebook_cell` to replace the failing cell with your fix.\n"
            f"{hint_note}\n\n"
            "**Failing code:**\n"
            f"```python\n{last_src}\n```"
        )

        from ...session import get_default_swarm

        swarm = get_default_swarm(ip)
        print(f"[JiuwenSwarm] Fixing {exc_type}: {exc_msg[:100]}…")
        try:
            swarm.run_sync(query, inject_context=False, ip=ip)
        except KeyboardInterrupt:
            print("\n[JiuwenSwarm] Fix cancelled.")

    ip.register_magic_function(jiuwen_fix, magic_kind="line", magic_name="jiuwen_fix")

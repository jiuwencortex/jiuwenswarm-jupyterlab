"""The ``%jiuwen_audit`` line magic — full notebook health scan by the agent."""

from __future__ import annotations


def register(ip) -> None:
    """Register ``%jiuwen_audit`` with the given IPython shell."""

    def jiuwen_audit(line: str) -> None:
        """Scan the entire notebook for code quality, correctness, and data issues.

        Collects every executed cell and the current variable namespace, then
        sends them to the agent for a structured review.  The agent reports on:

        - Dead or unreachable code
        - Unused imports
        - Data leakage between train and test sets
        - Operations that may silently fail on new data (type mismatches, nulls)
        - Hardcoded paths or magic numbers
        - Out-of-order cell execution dependencies
        - Memory-heavy patterns (iterrows, full-copy operations)
        - Missing error handling at I/O boundaries

        Usage::

            %jiuwen_audit
            %jiuwen_audit --quick   # shortened report, no code snippets
        """
        quick = "--quick" in (line or "")

        # Gather all executed cells from IPython history.
        cells: list[str] = []
        try:
            hist = list(ip.history_manager.get_tail(n=50, include_latest=True))
            cells = [src for _, _, src in hist if src.strip()]
        except Exception:
            pass

        if not cells:
            print("[JiuwenSwarm] No executed cells found. Run some notebook cells first.")
            return

        # Summarise the user namespace (variable names + types only — no values).
        var_summary_lines: list[str] = []
        skip = {"In", "Out", "get_ipython", "exit", "quit", "_", "__", "___"}
        for name, val in ip.user_ns.items():
            if name.startswith("_") or name in skip:
                continue
            type_name = type(val).__name__
            try:
                if hasattr(val, "shape"):
                    extra = f"shape={val.shape}"
                elif hasattr(val, "__len__"):
                    extra = f"len={len(val)}"
                else:
                    extra = ""
            except Exception:
                extra = ""
            var_summary_lines.append(f"  {name}: {type_name}" + (f" ({extra})" if extra else ""))

        cells_block = "\n\n".join(
            f"**Cell {i + 1}:**\n```python\n{src.strip()[:600]}\n```"
            for i, src in enumerate(cells)
        )

        vars_block = (
            "\n".join(var_summary_lines[:60]) if var_summary_lines else "(namespace is empty)"
        )

        detail_instruction = (
            "Provide a brief bullet-point summary only — do not quote code."
            if quick
            else (
                "For each issue found: state the severity (high/medium/low), "
                "quote the relevant line(s), and suggest a concrete fix."
            )
        )

        query = (
            "Please audit the following Jupyter notebook cells for code quality, "
            "correctness, and data science best-practice issues. "
            f"{detail_instruction}\n\n"
            f"**Executed cells ({len(cells)} total):**\n\n{cells_block}\n\n"
            f"**Current namespace variables:**\n{vars_block}"
        )

        from ...session import get_default_swarm

        swarm = get_default_swarm(ip)
        try:
            swarm.run_sync(query, inject_context=False, ip=ip)
        except KeyboardInterrupt:
            print("\n[JiuwenSwarm] Audit cancelled.")

    ip.register_magic_function(jiuwen_audit, magic_kind="line", magic_name="jiuwen_audit")

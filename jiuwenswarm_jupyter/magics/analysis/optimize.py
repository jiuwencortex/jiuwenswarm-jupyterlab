"""The ``%%jiuwen_optimize`` cell magic — rewrite a cell with faster vectorized code."""

from __future__ import annotations


def register(ip) -> None:
    """Register ``%%jiuwen_optimize`` with the given IPython shell."""

    def jiuwen_optimize(line: str, cell: str) -> None:
        """Rewrite the cell body for speed and memory efficiency, replacing it in-place.

        The agent identifies bottlenecks (iterrows, Python loops, redundant copies,
        dtype inefficiencies) and returns a drop-in replacement using vectorized
        pandas/numpy operations. The original cell is replaced automatically.

        Arguments
        ---------
        --profile      Run cProfile on the original cell first; include stats in the prompt.
        --no-replace   Stream the optimized version to output instead of replacing the cell.

        Usage::

            %%jiuwen_optimize
            for idx, row in df.iterrows():
                df.loc[idx, 'score'] = row['a'] * 2 + row['b']

            %%jiuwen_optimize --profile
            result = []
            for i in range(len(df)):
                result.append(transform(df.iloc[i]))
        """
        import shlex

        tokens = shlex.split(line.strip()) if line.strip() else []
        run_profile = "--profile" in tokens
        no_replace = "--no-replace" in tokens

        if not cell.strip():
            print("Usage: %%jiuwen_optimize\n<code to optimize>")
            return

        profile_note = ""
        if run_profile:
            import cProfile
            import io
            import pstats

            pr = cProfile.Profile()
            try:
                pr.enable()
                exec(cell, ip.user_ns)  # noqa: S102
                pr.disable()
                buf = io.StringIO()
                pstats.Stats(pr, stream=buf).sort_stats("cumulative").print_stats(15)
                profile_note = f"\n\n**cProfile output (top 15):**\n```\n{buf.getvalue()}\n```"
            except Exception as exc:
                profile_note = f"\n\n(Profiling failed — {exc})"

        replace_instruction = (
            "Use `replace_notebook_cell` to replace the original cell with the optimized version."
            if not no_replace
            else "Write the optimized code to the output only — do not replace the cell."
        )

        query = (
            "You are a performance engineer. Rewrite the following Python code to be faster "
            "and more memory-efficient.\n\n"
            "Focus on: vectorized pandas/numpy, eliminating iterrows/apply where possible, "
            "reducing DataFrame copies, appropriate dtypes, and built-in aggregations.\n\n"
            "Return ONLY the optimized code with brief inline comments where the approach changed. "
            f"{replace_instruction}"
            f"{profile_note}\n\n"
            "**Original code:**\n"
            f"```python\n{cell.strip()}\n```"
        )

        from ...session import get_default_swarm

        swarm = get_default_swarm(ip)
        print("[JiuwenSwarm] Optimizing cell…")
        try:
            swarm.run_sync(query, inject_context=False, ip=ip)
        except KeyboardInterrupt:
            print("\n[JiuwenSwarm] Optimization cancelled.")

    ip.register_magic_function(jiuwen_optimize, magic_kind="cell", magic_name="jiuwen_optimize")

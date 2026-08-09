"""The ``%%jiuwen_profile`` cell magic — profile a cell and have the agent interpret it."""

from __future__ import annotations


def register(ip) -> None:
    """Register ``%%jiuwen_profile`` with the given IPython shell."""

    def jiuwen_profile(line: str, cell: str) -> None:
        """Profile the cell using cProfile, then stream an agent analysis.

        The cell is executed under cProfile.  The top slowest call sites are
        extracted from the profile stats and sent to the agent, which identifies
        the real bottlenecks and proposes concrete optimizations.

        Options
        -------
        --top N    Number of slowest functions to include (default: 20)

        Usage::

            %%jiuwen_profile
            for row in df.iterrows():
                process(row)

            %%jiuwen_profile --top 30
            result = [expensive(x) for x in large_list]
        """
        import cProfile
        import io
        import pstats
        import shlex

        if not cell or not cell.strip():
            print("Usage: %%jiuwen_profile\\n<code to profile>")
            return

        tokens = shlex.split(line.strip()) if line.strip() else []
        top_n = 20
        i = 0
        while i < len(tokens):
            if tokens[i] == "--top" and i + 1 < len(tokens):
                try:
                    top_n = int(tokens[i + 1])
                except ValueError:
                    pass
                i += 2
            else:
                i += 1

        profiler = cProfile.Profile()
        exec_error: str | None = None

        print(f"[JiuwenSwarm] Profiling cell (top {top_n} calls)…")
        try:
            profiler.enable()
            exec(compile(cell, "<jiuwen_profile>", "exec"), ip.user_ns)  # noqa: S102
        except Exception as exc:
            exec_error = f"{type(exc).__name__}: {exc}"
        finally:
            profiler.disable()

        # Render stats to a string.
        stats_buf = io.StringIO()
        stats = pstats.Stats(profiler, stream=stats_buf)
        stats.sort_stats("cumulative")
        stats.print_stats(top_n)
        profile_output = stats_buf.getvalue()

        # Print the raw stats for the user.
        print(profile_output[:3000])

        query_parts = [
            "I profiled the following Python code in a Jupyter notebook. "
            "Identify the real performance bottlenecks from the profile output below, "
            "explain why each is slow, and propose concrete optimisations with code examples. "
            "Prioritise the highest-impact changes.\n",
            f"**Profiled code:**\n```python\n{cell.strip()}\n```",
            f"**cProfile output (top {top_n} by cumulative time):**\n```\n{profile_output[:2000]}\n```",
        ]
        if exec_error:
            query_parts.append(f"**Error during execution:**\n```\n{exec_error}\n```")

        query = "\n\n".join(query_parts)

        from ...session import get_default_swarm

        swarm = get_default_swarm(ip)
        try:
            swarm.run_sync(query, inject_context=False, ip=ip)
        except KeyboardInterrupt:
            print("\n[JiuwenSwarm] Profile analysis cancelled.")

    ip.register_magic_function(jiuwen_profile, magic_kind="cell", magic_name="jiuwen_profile")

"""The ``%%jiuwen_benchmark`` cell magic — compare multiple implementations with timeit."""

from __future__ import annotations


def register(ip) -> None:
    """Register ``%%jiuwen_benchmark`` with the given IPython shell."""

    def jiuwen_benchmark(line: str, cell: str) -> None:
        """Benchmark multiple implementations separated by ``---`` and compare them.

        Each section is run under ``timeit``, the results are printed as a table,
        and the agent explains which implementation is fastest and why.

        Options
        -------
        --n N      Number of timeit repetitions per implementation (default: 100).
        --setup S  Setup code to run before each implementation (e.g. imports).

        Usage::

            %%jiuwen_benchmark
            # iterrows
            [process(row) for _, row in df.iterrows()]
            ---
            # apply
            df.apply(lambda row: process(row), axis=1)
            ---
            # vectorised
            process_vec(df["col"].values)

            %%jiuwen_benchmark --n 50
            # list comprehension
            [x * 2 for x in data]
            ---
            # numpy
            np.array(data) * 2
        """
        import timeit

        if not cell or not cell.strip():
            print("Usage: %%jiuwen_benchmark [--n N]\\n<impl1>\\n---\\n<impl2>\\n---\\n...")
            return

        import shlex

        tokens = shlex.split(line.strip()) if line.strip() else []
        n_reps = 100
        setup_code = ""

        i = 0
        while i < len(tokens):
            if tokens[i] == "--n" and i + 1 < len(tokens):
                try:
                    n_reps = int(tokens[i + 1])
                except ValueError:
                    pass
                i += 2
            elif tokens[i] == "--setup" and i + 1 < len(tokens):
                setup_code = tokens[i + 1]
                i += 2
            else:
                i += 1

        # Split on --- separator.
        sections = [s.strip() for s in cell.split("\n---\n") if s.strip()]
        if len(sections) < 2:
            # Also try "---" alone on a line.
            import re
            sections = [s.strip() for s in re.split(r"^\s*---\s*$", cell, flags=re.MULTILINE) if s.strip()]

        if len(sections) < 2:
            print("[JiuwenSwarm] Separate implementations with --- on its own line. "
                  "Need at least 2 implementations.")
            return

        # Extract labels from first comment line of each section.
        def _label(code: str) -> str:
            for line_ in code.splitlines():
                s = line_.strip()
                if s.startswith("#"):
                    return s.lstrip("# ").strip()
            return code.splitlines()[0][:40]

        results: list[dict] = []
        print(f"[JiuwenSwarm] Benchmarking {len(sections)} implementations (n={n_reps})…\n")

        # Build namespace for exec: user namespace + optional setup code.
        bench_ns = dict(ip.user_ns)
        if setup_code:
            exec(compile(setup_code, "<benchmark_setup>", "exec"), bench_ns)  # noqa: S102

        for idx, code in enumerate(sections):
            label = _label(code)
            print(f"  [{idx + 1}/{len(sections)}] {label}…", end=" ", flush=True)
            try:
                timer = timeit.Timer(
                    stmt=compile(code, "<benchmark>", "exec"),
                    globals=bench_ns,
                )
                times = timer.repeat(repeat=5, number=n_reps)
                mean_ms = min(times) / n_reps * 1000  # best-of-5, per iteration
                results.append({"label": label, "mean_ms": mean_ms, "code": code})
                print(f"{mean_ms:.3f} ms")
            except Exception as exc:
                results.append({"label": label, "mean_ms": None, "error": str(exc), "code": code})
                print(f"ERROR: {exc}")

        # Print comparison table.
        valid = [r for r in results if r["mean_ms"] is not None]
        if valid:
            fastest = min(valid, key=lambda r: r["mean_ms"])
            print(f"\n{'Label':<30}  {'Mean (ms)':<12}  {'vs fastest'}")
            print("-" * 55)
            for r in results:
                if r["mean_ms"] is None:
                    print(f"  {r['label']:<28}  {'ERROR':<12}")
                else:
                    ratio = r["mean_ms"] / fastest["mean_ms"]
                    print(f"  {r['label']:<28}  {r['mean_ms']:<12.3f}  {ratio:.1f}x")

        # Ask the agent to interpret the results.
        results_text = "\n".join(
            f"- {r['label']}: {r['mean_ms']:.3f} ms" if r.get("mean_ms") is not None
            else f"- {r['label']}: ERROR — {r.get('error', '?')}"
            for r in results
        )
        impls_text = "\n\n".join(
            f"**{r['label']}:**\n```python\n{r['code']}\n```"
            for r in results
        )

        query = (
            f"I benchmarked {len(results)} Python implementations with timeit (n={n_reps} reps). "
            "Please explain: which is fastest, WHY it is faster (memory layout, vectorisation, "
            "Python overhead, etc.), and what the trade-offs are. "
            "Recommend which to use in production and when each alternative might be preferred.\n\n"
            f"**Results:**\n{results_text}\n\n"
            f"**Implementations:**\n{impls_text}"
        )

        from ...session import get_default_swarm

        swarm = get_default_swarm(ip)
        try:
            swarm.run_sync(query, inject_context=False, ip=ip)
        except KeyboardInterrupt:
            print("\n[JiuwenSwarm] Benchmark analysis cancelled.")

    ip.register_magic_function(jiuwen_benchmark, magic_kind="cell", magic_name="jiuwen_benchmark")

"""The ``%jiuwen_hypothesis`` line magic — agent-generated insight seeds from live data."""

from __future__ import annotations


def register(ip) -> None:
    """Register ``%jiuwen_hypothesis`` with the given IPython shell."""

    def jiuwen_hypothesis(line: str) -> None:
        """Scan the current DataFrames and generate testable hypotheses.

        The agent looks for non-obvious patterns — skewed distributions,
        suspicious correlations, class imbalance, date gaps, outlier clusters —
        and produces prioritised hypotheses worth investigating, each with the
        exact code to test it inserted as a notebook cell.

        Arguments
        ---------
        DF_NAME        Specific DataFrame to focus on (optional).
        --target COL   Label/target column for supervised-learning context.
        --n N          Number of hypotheses to generate (default: 8).

        Usage::

            %jiuwen_hypothesis
            %jiuwen_hypothesis df_train --target churn
            %jiuwen_hypothesis df --n 12
        """
        import shlex

        tokens = shlex.split(line.strip()) if line.strip() else []

        df_name: str | None = None
        target_col: str | None = None
        n_hyp = 8

        i = 0
        while i < len(tokens):
            if tokens[i] == "--target" and i + 1 < len(tokens):
                target_col = tokens[i + 1]
                i += 2
            elif tokens[i] == "--n" and i + 1 < len(tokens):
                try:
                    n_hyp = int(tokens[i + 1])
                except ValueError:
                    pass
                i += 2
            elif not tokens[i].startswith("--"):
                df_name = tokens[i]
                i += 1
            else:
                i += 1

        # Collect DataFrames to profile.
        try:
            import pandas as pd
            if df_name:
                df_map = {df_name: ip.user_ns.get(df_name)}
            else:
                df_map = {
                    k: v for k, v in ip.user_ns.items()
                    if not k.startswith("_") and isinstance(v, pd.DataFrame)
                }
        except ImportError:
            df_map = {}

        if not df_map or all(v is None for v in df_map.values()):
            print("[JiuwenSwarm] No DataFrames found. Run %jiuwen_hypothesis df_name.")
            return

        summaries: list[str] = []
        for name, df in df_map.items():
            if df is None:
                continue
            cols = list(df.columns) if hasattr(df, "columns") else []
            shape = getattr(df, "shape", "?")
            try:
                desc = df.describe(include="all").to_string()[:1200]
            except Exception:
                desc = ""
            try:
                null_rates = {
                    col: f"{100 * df[col].isnull().mean():.1f}%"
                    for col in cols[:40]
                }
            except Exception:
                null_rates = {}
            summaries.append(
                f"**`{name}`** shape={shape}, columns={cols[:40]}\n"
                f"Null rates: {null_rates}\n"
                f"describe:\n```\n{desc}\n```"
            )

        target_note = (
            f"\nTarget column: `{target_col}`. Frame hypotheses in terms of what "
            f"predicts `{target_col}` and what might cause model issues."
            if target_col else ""
        )

        query = (
            f"You are a senior data scientist reviewing a Jupyter notebook dataset cold. "
            f"Generate exactly {n_hyp} prioritised, testable hypotheses based on the "
            "data profile below. For each hypothesis:\n"
            "1. State the hypothesis clearly (one sentence).\n"
            "2. Explain what pattern in the data suggested it.\n"
            "3. Provide Python code to test it.\n"
            "Insert each hypothesis + code as a separate cell using `insert_notebook_cell`. "
            "Use only the actual column names listed. Do not invent data.\n"
            f"{target_note}\n\n"
            + "\n\n".join(summaries)
        )

        from ...session import get_default_swarm

        swarm = get_default_swarm(ip)
        print(f"[JiuwenSwarm] Generating {n_hyp} hypotheses…")
        try:
            swarm.run_sync(query, inject_context=False, ip=ip)
        except KeyboardInterrupt:
            print("\n[JiuwenSwarm] Hypothesis generation cancelled.")

    ip.register_magic_function(jiuwen_hypothesis, magic_kind="line", magic_name="jiuwen_hypothesis")

"""The ``%jiuwen_eda`` line magic — one-shot exploratory data analysis on a DataFrame."""

from __future__ import annotations


def register(ip) -> None:
    """Register ``%jiuwen_eda`` with the given IPython shell."""

    def jiuwen_eda(line: str) -> None:
        """Generate a complete EDA for a DataFrame and insert it as notebook cells.

        The agent produces the full standard EDA suite — shape, dtypes, null rates,
        cardinality, distributions, correlation matrix, outlier flags, and class
        balance when a target column is specified — and inserts each section as a
        ready-to-run code or markdown cell.

        Arguments
        ---------
        DF_NAME        Variable name of the DataFrame to analyse (required).
        --target COL   Name of the target/label column for class balance and
                       feature-target correlation analysis.
        --quick        Short summary only (shape, nulls, dtypes). No plots.

        Usage::

            %jiuwen_eda df
            %jiuwen_eda df_train --target churn
            %jiuwen_eda df --target price --quick
        """
        import shlex

        tokens = shlex.split(line.strip()) if line.strip() else []
        if not tokens:
            print("Usage: %jiuwen_eda <df_name> [--target COL] [--quick]")
            return

        df_name = None
        target_col: str | None = None
        quick = False

        i = 0
        while i < len(tokens):
            if tokens[i] == "--target" and i + 1 < len(tokens):
                target_col = tokens[i + 1]
                i += 2
            elif tokens[i] == "--quick":
                quick = True
                i += 1
            elif not tokens[i].startswith("--"):
                df_name = tokens[i]
                i += 1
            else:
                i += 1

        if df_name is None:
            print("Usage: %jiuwen_eda <df_name> [--target COL] [--quick]")
            return

        df = ip.user_ns.get(df_name)
        if df is None:
            print(f"[JiuwenSwarm] Variable '{df_name}' not found in the notebook namespace.")
            return

        # Build a schema summary to give the agent full column awareness.
        try:
            import io
            buf = io.StringIO()
            df.info(buf=buf)
            info_str = buf.getvalue()
        except Exception:
            info_str = f"shape={getattr(df, 'shape', '?')}"

        try:
            desc_str = str(df.describe(include="all").to_string())[:1500]
        except Exception:
            desc_str = ""

        try:
            null_str = str(df.isnull().sum().to_string())[:600]
        except Exception:
            null_str = ""

        cols = list(df.columns) if hasattr(df, "columns") else []
        shape = getattr(df, "shape", "?")

        target_note = (
            f"\nTarget column: `{target_col}`. Include class balance analysis and "
            "feature-target correlation/importance."
            if target_col
            else ""
        )
        depth_note = (
            "Produce a SHORT summary only: shape, dtypes table, and null counts. No plots."
            if quick
            else (
                "Produce a COMPLETE EDA with: "
                "(1) shape and dtypes table, "
                "(2) null / missing value counts and percentages, "
                "(3) numeric distribution plots (histograms + boxplots), "
                "(4) cardinality check for categoricals, "
                "(5) correlation heatmap, "
                "(6) outlier detection (IQR method), "
                "(7) first 5 rows preview."
            )
        )

        query = (
            f"Please generate an exploratory data analysis for the DataFrame `{df_name}`. "
            f"{depth_note}{target_note}\n\n"
            "Use `insert_notebook_cell` to insert each section as a separate code or "
            "markdown cell so the user can run them individually. "
            "Use the actual column names below — do not invent any.\n\n"
            f"**DataFrame:** `{df_name}`  shape={shape}\n"
            f"**Columns ({len(cols)}):** {', '.join(str(c) for c in cols[:60])}\n\n"
            f"**df.info():**\n```\n{info_str[:800]}\n```\n\n"
            f"**df.describe():**\n```\n{desc_str}\n```\n\n"
            f"**Null counts:**\n```\n{null_str}\n```"
        )

        from ...session import get_default_swarm

        swarm = get_default_swarm(ip)
        print(f"[JiuwenSwarm] Generating EDA for `{df_name}` ({shape})…")
        try:
            swarm.run_sync(query, inject_context=False, ip=ip)
        except KeyboardInterrupt:
            print("\n[JiuwenSwarm] EDA cancelled.")

    ip.register_magic_function(jiuwen_eda, magic_kind="line", magic_name="jiuwen_eda")

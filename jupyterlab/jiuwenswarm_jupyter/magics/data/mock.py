"""The ``%jiuwen_mock`` line magic — generate synthetic data matching a DataFrame schema."""

from __future__ import annotations


def register(ip) -> None:
    """Register ``%jiuwen_mock`` with the given IPython shell."""

    def jiuwen_mock(line: str) -> None:
        """Generate a synthetic DataFrame that mirrors the schema of an existing one.

        Reads column names, dtypes, value ranges, cardinalities, and null rates
        from the template DataFrame, then inserts a complete code cell that creates
        a realistic mock dataset. Useful for unit tests, demos, and sharing notebooks
        without exposing real data.

        Arguments
        ---------
        DF_NAME        Template DataFrame variable name (required).
        --n N          Number of rows to generate (default: 100).
        --var NAME     Variable name for the output DataFrame (default: df_mock).
        --seed N       Random seed for reproducibility (default: 42).

        Usage::

            %jiuwen_mock df
            %jiuwen_mock df_train --n 500 --var df_synthetic
            %jiuwen_mock transactions --n 1000 --seed 0
        """
        import shlex

        tokens = shlex.split(line.strip()) if line.strip() else []
        if not tokens:
            print("Usage: %jiuwen_mock <df_name> [--n N] [--var NAME] [--seed N]")
            return

        df_name: str | None = None
        n_rows = 100
        var_name = "df_mock"
        seed = 42

        i = 0
        while i < len(tokens):
            if tokens[i] == "--n" and i + 1 < len(tokens):
                try:
                    n_rows = int(tokens[i + 1])
                except ValueError:
                    pass
                i += 2
            elif tokens[i] == "--var" and i + 1 < len(tokens):
                var_name = tokens[i + 1]
                i += 2
            elif tokens[i] == "--seed" and i + 1 < len(tokens):
                try:
                    seed = int(tokens[i + 1])
                except ValueError:
                    pass
                i += 2
            elif not tokens[i].startswith("--"):
                df_name = tokens[i]
                i += 1
            else:
                i += 1

        if df_name is None:
            print("Usage: %jiuwen_mock <df_name> [--n N] [--var NAME] [--seed N]")
            return

        df = ip.user_ns.get(df_name)
        if df is None:
            print(f"[JiuwenSwarm] '{df_name}' not found in the namespace.")
            return

        cols = list(df.columns) if hasattr(df, "columns") else []
        shape = getattr(df, "shape", "?")

        col_profiles: list[str] = []
        for col in cols[:60]:
            try:
                series = df[col]
                dtype = str(series.dtype)
                null_pct = round(series.isna().mean() * 100, 1)
                if series.dtype.kind in ("i", "f"):
                    lo, hi = float(series.min()), float(series.max())
                    col_profiles.append(
                        f"  {col} ({dtype}): range=[{lo:.4g}, {hi:.4g}], nulls={null_pct}%"
                    )
                elif series.dtype.kind == "M":
                    lo = str(series.min())[:10]
                    hi = str(series.max())[:10]
                    col_profiles.append(f"  {col} (datetime): range=[{lo}, {hi}], nulls={null_pct}%")
                else:
                    n_unique = series.nunique()
                    top_vals = series.dropna().value_counts().head(8).index.tolist()
                    col_profiles.append(
                        f"  {col} ({dtype}, {n_unique} unique, nulls={null_pct}%): top={top_vals}"
                    )
            except Exception:
                col_profiles.append(f"  {col}: ?")

        query = (
            f"Generate a synthetic pandas DataFrame `{var_name}` with {n_rows} rows "
            f"that mirrors the schema of `{df_name}` (original shape: {shape}).\n\n"
            f"Use `numpy.random.default_rng(seed={seed})` for reproducibility.\n"
            "Requirements:\n"
            "- Match every column's dtype exactly.\n"
            "- For numerics: draw from the observed range (use uniform or normal distribution).\n"
            "- For categoricals/strings: sample from the observed top values with realistic frequencies.\n"
            "- For datetimes: generate random dates within the observed date range.\n"
            "- Reproduce null rates by randomly setting values to NaN.\n"
            "- Use `insert_notebook_cell` to insert the complete code as a runnable cell.\n\n"
            "**Schema profile:**\n" + "\n".join(col_profiles)
        )

        from ...session import get_default_swarm

        swarm = get_default_swarm(ip)
        print(f"[JiuwenSwarm] Generating {n_rows}-row mock DataFrame for `{df_name}`…")
        try:
            swarm.run_sync(query, inject_context=False, ip=ip)
        except KeyboardInterrupt:
            print("\n[JiuwenSwarm] Mock generation cancelled.")

    ip.register_magic_function(jiuwen_mock, magic_kind="line", magic_name="jiuwen_mock")

"""The ``%jiuwen_features`` line magic — domain-aware feature engineering suggestions."""

from __future__ import annotations


def register(ip) -> None:
    """Register ``%jiuwen_features`` with the given IPython shell."""

    def jiuwen_features(line: str) -> None:
        """Generate feature engineering ideas for a DataFrame and insert them as cells.

        The agent reads the schema, infers column semantics (dates, IDs, categoricals,
        text, numerics), and proposes engineered features with full pandas code.
        Each feature lands as a separate runnable code cell.

        Arguments
        ---------
        DF_NAME        DataFrame variable name (required).
        --target COL   Label column — agent focuses on features likely predictive of it.
        --domain TEXT  Domain context e.g. "telecom churn", "e-commerce", "credit risk".
        --n N          Number of feature ideas to produce (default: 12).

        Usage::

            %jiuwen_features df --target churn
            %jiuwen_features df_train --target price --domain "real estate"
            %jiuwen_features transactions --n 20 --domain "fraud detection"
        """
        import shlex

        tokens = shlex.split(line.strip()) if line.strip() else []
        if not tokens:
            print("Usage: %jiuwen_features <df_name> [--target COL] [--domain TEXT] [--n N]")
            return

        df_name: str | None = None
        target_col: str | None = None
        domain: str | None = None
        n_features = 12

        i = 0
        while i < len(tokens):
            if tokens[i] == "--target" and i + 1 < len(tokens):
                target_col = tokens[i + 1]
                i += 2
            elif tokens[i] == "--domain" and i + 1 < len(tokens):
                domain = tokens[i + 1]
                i += 2
            elif tokens[i] == "--n" and i + 1 < len(tokens):
                try:
                    n_features = int(tokens[i + 1])
                except ValueError:
                    pass
                i += 2
            elif not tokens[i].startswith("--"):
                df_name = tokens[i]
                i += 1
            else:
                i += 1

        if df_name is None:
            print("Usage: %jiuwen_features <df_name> [--target COL]")
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
                n_unique = series.nunique()
                sample = series.dropna().head(3).tolist()
                col_profiles.append(f"  {col} ({dtype}, {n_unique} unique): {sample}")
            except Exception:
                col_profiles.append(f"  {col}: ?")

        target_note = f"\nTarget: `{target_col}`." if target_col else ""
        domain_note = f"\nDomain: {domain}." if domain else ""

        query = (
            f"You are a senior ML engineer doing feature engineering on `{df_name}`. "
            f"Propose exactly {n_features} new engineered features.{target_note}{domain_note}\n\n"
            "For each feature:\n"
            "- Name and one-sentence rationale.\n"
            "- Complete pandas code that creates the feature column in the existing DataFrame.\n"
            "Insert each feature as its own code cell using `insert_notebook_cell`.\n"
            "Prioritise: date/time decomposition, interaction terms, ratio features, "
            "count encodings, cyclic encodings, lag features if timestamps present, "
            "text length/word count for string columns.\n"
            "Use ONLY the actual column names listed below.\n\n"
            f"**`{df_name}`** shape={shape}\n"
            + "\n".join(col_profiles)
        )

        from ...session import get_default_swarm

        swarm = get_default_swarm(ip)
        print(f"[JiuwenSwarm] Generating {n_features} feature ideas for `{df_name}`…")
        try:
            swarm.run_sync(query, inject_context=False, ip=ip)
        except KeyboardInterrupt:
            print("\n[JiuwenSwarm] Feature generation cancelled.")

    ip.register_magic_function(jiuwen_features, magic_kind="line", magic_name="jiuwen_features")

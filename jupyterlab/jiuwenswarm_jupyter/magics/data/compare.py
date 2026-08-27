"""The ``%jiuwen_compare`` line magic — statistical comparison of two DataFrames."""

from __future__ import annotations


def register(ip) -> None:
    """Register ``%jiuwen_compare`` with the given IPython shell."""

    def jiuwen_compare(line: str) -> None:
        """Compare two DataFrames and get a structured agent-written diff report.

        Computes schema differences, shape changes, column-level statistical drift
        (mean, std, null rate, cardinality), and optional target distribution shift.
        Useful for train/test drift detection, before/after cleaning comparisons,
        and dataset version validation.

        Arguments
        ---------
        DF1  DF2       Two DataFrame variable names (required, positional).
        --target COL   Focus drift analysis on this label column.

        Usage::

            %jiuwen_compare df_train df_test
            %jiuwen_compare df_v1 df_v2 --target churn
            %jiuwen_compare raw_df cleaned_df
        """
        import shlex

        tokens = shlex.split(line.strip()) if line.strip() else []

        positional = [t for t in tokens if not t.startswith("--")]
        if len(positional) < 2:
            print("Usage: %jiuwen_compare <df1> <df2> [--target COL]")
            return

        df1_name, df2_name = positional[0], positional[1]

        target_col: str | None = None
        i = 0
        while i < len(tokens):
            if tokens[i] == "--target" and i + 1 < len(tokens):
                target_col = tokens[i + 1]
                i += 2
            else:
                i += 1

        df1 = ip.user_ns.get(df1_name)
        df2 = ip.user_ns.get(df2_name)

        if df1 is None:
            print(f"[JiuwenSwarm] '{df1_name}' not found in the namespace.")
            return
        if df2 is None:
            print(f"[JiuwenSwarm] '{df2_name}' not found in the namespace.")
            return

        cols1 = set(df1.columns) if hasattr(df1, "columns") else set()
        cols2 = set(df2.columns) if hasattr(df2, "columns") else set()
        only_in_1 = sorted(cols1 - cols2)
        only_in_2 = sorted(cols2 - cols1)
        common = sorted(cols1 & cols2)

        # Dtype changes
        dtype_changes: list[str] = []
        for col in common:
            d1 = str(df1[col].dtype)
            d2 = str(df2[col].dtype)
            if d1 != d2:
                dtype_changes.append(f"  {col}: {d1} → {d2}")

        # Per-column statistical diff
        col_stats: list[str] = []
        for col in common[:50]:
            try:
                s1, s2 = df1[col], df2[col]
                null1 = round(s1.isna().mean() * 100, 1)
                null2 = round(s2.isna().mean() * 100, 1)
                if s1.dtype.kind in ("i", "f"):
                    col_stats.append(
                        f"  {col}: mean {s1.mean():.4g}→{s2.mean():.4g}, "
                        f"std {s1.std():.4g}→{s2.std():.4g}, "
                        f"nulls {null1}%→{null2}%"
                    )
                else:
                    u1, u2 = s1.nunique(), s2.nunique()
                    col_stats.append(
                        f"  {col}: unique {u1}→{u2}, nulls {null1}%→{null2}%"
                    )
            except Exception:
                col_stats.append(f"  {col}: ?")

        target_note = f"\nFocus on drift in target column `{target_col}`." if target_col else ""

        query = (
            f"Compare `{df1_name}` (shape={df1.shape}) vs `{df2_name}` (shape={df2.shape}).\n"
            f"{target_note}\n\n"
            "Write a structured comparison report with these sections:\n"
            "1. **Schema changes** — added/removed/type-changed columns\n"
            "2. **Size** — row/column count differences\n"
            "3. **Statistical drift** — flag numeric columns with large mean/std shifts (>10%)\n"
            "4. **Categorical drift** — cardinality changes, new or missing categories\n"
            "5. **Null rates** — columns with meaningful null rate changes\n"
            "6. **Verdict** — overall assessment: safe to use as train/test split? Any concerns?\n\n"
            f"Columns only in `{df1_name}`: {only_in_1 or ['none']}\n"
            f"Columns only in `{df2_name}`: {only_in_2 or ['none']}\n"
            f"Dtype changes: {dtype_changes or ['none']}\n\n"
            "**Per-column stats (A→B):**\n" + "\n".join(col_stats)
        )

        from ...session import get_default_swarm

        swarm = get_default_swarm(ip)
        print(f"[JiuwenSwarm] Comparing `{df1_name}` vs `{df2_name}`…")
        try:
            swarm.run_sync(query, inject_context=False, ip=ip)
        except KeyboardInterrupt:
            print("\n[JiuwenSwarm] Comparison cancelled.")

    ip.register_magic_function(jiuwen_compare, magic_kind="line", magic_name="jiuwen_compare")

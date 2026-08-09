"""The ``%%jiuwen_df`` cell magic — natural language to DataFrame operation."""

from __future__ import annotations


def register(ip) -> None:
    """Register ``%%jiuwen_df`` with the given IPython shell."""

    def jiuwen_df(line: str, cell: str) -> None:
        """Translate a plain-English description into a pandas DataFrame operation.

        Write what you want to do with the data in natural language.  The agent
        reads the actual column names and dtypes from the DataFrames currently in
        the namespace, generates the correct pandas code, inserts it as a new cell,
        and executes it.

        Options
        -------
        --df DF_NAME   DataFrame to operate on (auto-detected if only one is present).
        --no-run       Insert the cell but do not execute it.

        Usage::

            %%jiuwen_df
            Show customers who churned in Q3 2024, grouped by product tier,
            sorted by average monthly spend descending.

            %%jiuwen_df --df transactions
            Find all orders above $500 placed on weekends in the last 90 days,
            keeping only customer_id, amount, and product_category.

            %%jiuwen_df --no-run
            Pivot the sales table so each row is a customer and each column is a month.
        """
        if not cell or not cell.strip():
            print("Usage: %%jiuwen_df\\n<plain English description of the operation>")
            return

        import shlex

        tokens = shlex.split(line.strip()) if line.strip() else []
        df_name: str | None = None
        auto_run = True

        i = 0
        while i < len(tokens):
            if tokens[i] == "--df" and i + 1 < len(tokens):
                df_name = tokens[i + 1]
                i += 2
            elif tokens[i] == "--no-run":
                auto_run = False
                i += 1
            else:
                i += 1

        # Collect all DataFrames for schema context.
        try:
            import pandas as pd
            if df_name:
                dfs = {df_name: ip.user_ns.get(df_name)}
            else:
                dfs = {
                    k: v for k, v in ip.user_ns.items()
                    if not k.startswith("_") and isinstance(v, pd.DataFrame)
                }
        except ImportError:
            dfs = {}

        schema_parts: list[str] = []
        for name, df in dfs.items():
            if df is None:
                continue
            cols = list(df.columns) if hasattr(df, "columns") else []
            shape = getattr(df, "shape", "?")
            try:
                dtypes_str = ", ".join(f"{c}:{df[c].dtype}" for c in cols[:40])
            except Exception:
                dtypes_str = ", ".join(str(c) for c in cols[:40])
            schema_parts.append(f"`{name}` shape={shape}: {dtypes_str}")

        schema_block = "\n".join(schema_parts) if schema_parts else "(no DataFrames found)"
        run_instruction = (
            "Insert it as a code cell using `insert_notebook_cell` with `execute=True`."
            if auto_run
            else "Insert it as a code cell using `insert_notebook_cell` with `execute=False`."
        )

        query = (
            "Translate the following natural-language data request into correct pandas code. "
            f"{run_instruction} "
            "Use ONLY the column names that appear in the schema below — never invent columns. "
            "Prefer vectorised operations over loops.\n\n"
            f"**Request:**\n{cell.strip()}\n\n"
            f"**Available DataFrames:**\n{schema_block}"
        )

        from ...session import get_default_swarm

        swarm = get_default_swarm(ip)
        try:
            swarm.run_sync(query, inject_context=False, ip=ip)
        except KeyboardInterrupt:
            print("\n[JiuwenSwarm] DataFrame query cancelled.")

    ip.register_magic_function(jiuwen_df, magic_kind="cell", magic_name="jiuwen_df")

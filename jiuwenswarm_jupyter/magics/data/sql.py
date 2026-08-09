"""The ``%%jiuwen_sql`` cell magic — natural language to SQL, executed via DuckDB."""

from __future__ import annotations


def register(ip) -> None:
    """Register ``%%jiuwen_sql`` with the given IPython shell."""

    def jiuwen_sql(line: str, cell: str) -> None:
        """Translate a plain-English SQL request and run it via DuckDB over DataFrames.

        Write your query in natural language.  The agent generates a DuckDB SQL
        query (DataFrames are accessible by their variable names as table names),
        inserts it as a code cell, and executes it.  No database connection needed —
        DuckDB queries pandas DataFrames in-process with zero setup.

        Options
        -------
        --no-run   Insert the cell but do not execute it immediately.

        Usage::

            %%jiuwen_sql
            Find the top 10 customers by total spend who have not placed an order
            in the last 60 days.

            %%jiuwen_sql
            Show monthly revenue by region for 2024, with month-over-month growth rate.

            %%jiuwen_sql --no-run
            Calculate the 90th percentile of order value for each product category,
            only for customers who signed up before 2023.
        """
        if not cell or not cell.strip():
            print("Usage: %%jiuwen_sql\\n<plain English description of the query>")
            return

        no_run = "--no-run" in (line or "")

        # Collect DataFrame schemas — DuckDB uses df variable names as table names.
        try:
            import pandas as pd
            dfs = {
                k: v for k, v in ip.user_ns.items()
                if not k.startswith("_") and isinstance(v, pd.DataFrame)
            }
        except ImportError:
            dfs = {}

        schema_parts: list[str] = []
        for name, df in dfs.items():
            cols = list(df.columns) if hasattr(df, "columns") else []
            try:
                col_types = ", ".join(f"{c} ({df[c].dtype})" for c in cols[:40])
            except Exception:
                col_types = ", ".join(str(c) for c in cols[:40])
            schema_parts.append(f"Table `{name}` — {col_types}")

        schema_block = "\n".join(schema_parts) if schema_parts else "(no DataFrames found)"
        run_instruction = (
            "Insert as a code cell using `insert_notebook_cell` with `execute=False`."
            if no_run
            else "Insert as a code cell using `insert_notebook_cell` with `execute=True`."
        )

        query = (
            "Generate a DuckDB SQL query for the following request. "
            "In DuckDB, pandas DataFrames can be queried directly by their variable name "
            "as if they were SQL tables (e.g. `duckdb.query('SELECT * FROM df').df()`). "
            "Import duckdb at the top of the cell. "
            f"{run_instruction} "
            "Use ONLY the column names from the schema below.\n\n"
            f"**Request:**\n{cell.strip()}\n\n"
            f"**Available tables (pandas DataFrames):**\n{schema_block}"
        )

        from ...session import get_default_swarm

        swarm = get_default_swarm(ip)
        try:
            swarm.run_sync(query, inject_context=False, ip=ip)
        except KeyboardInterrupt:
            print("\n[JiuwenSwarm] SQL generation cancelled.")

    ip.register_magic_function(jiuwen_sql, magic_kind="cell", magic_name="jiuwen_sql")

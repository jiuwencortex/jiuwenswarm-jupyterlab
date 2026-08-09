"""The ``%%jiuwen_viz`` cell magic — natural language to data visualisation."""

from __future__ import annotations


def register(ip) -> None:
    """Register ``%%jiuwen_viz`` with the given IPython shell."""

    def jiuwen_viz(line: str, cell: str) -> None:
        """Describe a chart in plain English; get runnable visualisation code.

        The agent reads the actual column names and dtypes from the DataFrames in
        your namespace, picks the best library (matplotlib, seaborn, or plotly),
        generates complete chart code, inserts it as a cell, and runs it.

        Options
        -------
        --lib LIBRARY  Force a specific library: matplotlib | seaborn | plotly.
        --no-run       Insert the cell but do not execute it.

        Usage::

            %%jiuwen_viz
            Plot monthly revenue by region as a stacked bar chart with a rolling
            3-month average line overlay.

            %%jiuwen_viz --lib plotly
            Interactive scatter plot of customer lifetime value vs churn probability,
            coloured by product tier, sized by number of orders.

            %%jiuwen_viz --no-run
            Heatmap of the correlation matrix for all numeric features,
            masking the upper triangle.
        """
        if not cell or not cell.strip():
            print("Usage: %%jiuwen_viz\\n<plain English description of the chart>")
            return

        import shlex

        tokens = shlex.split(line.strip()) if line.strip() else []
        lib: str | None = None
        no_run = False

        i = 0
        while i < len(tokens):
            if tokens[i] == "--lib" and i + 1 < len(tokens):
                lib = tokens[i + 1].lower()
                i += 2
            elif tokens[i] == "--no-run":
                no_run = True
                i += 1
            else:
                i += 1

        # Collect DataFrames for column awareness.
        try:
            import pandas as pd
            dfs = {
                k: v for k, v in ip.user_ns.items()
                if not k.startswith("_") and isinstance(v, pd.DataFrame)
            }
        except ImportError:
            dfs = {}

        # Detect which plotting libraries are installed.
        available_libs: list[str] = []
        for lib_name in ("plotly.express", "seaborn", "matplotlib.pyplot"):
            try:
                __import__(lib_name)
                available_libs.append(lib_name.split(".")[0])
            except ImportError:
                pass

        schema_parts: list[str] = []
        for name, df in dfs.items():
            cols = list(df.columns) if hasattr(df, "columns") else []
            try:
                col_types = ", ".join(f"{c} ({df[c].dtype})" for c in cols[:40])
            except Exception:
                col_types = ", ".join(str(c) for c in cols[:40])
            schema_parts.append(f"`{name}`: {col_types}")

        schema_block = "\n".join(schema_parts) if schema_parts else "(no DataFrames found)"
        lib_instruction = (
            f"Use {lib} for the chart."
            if lib
            else (
                f"Choose the most appropriate library from those available: "
                f"{available_libs or ['matplotlib']}. Prefer plotly for interactive charts, "
                "seaborn for statistical charts, matplotlib for everything else."
            )
        )
        run_instruction = (
            "Insert as a code cell using `insert_notebook_cell` with `execute=False`."
            if no_run
            else "Insert as a code cell using `insert_notebook_cell` with `execute=True`."
        )

        query = (
            "Generate Python visualisation code for the following chart description. "
            f"{lib_instruction} "
            f"{run_instruction} "
            "Use ONLY the column names that appear in the schema below. "
            "Include axis labels, a title, and a legend where appropriate. "
            "The code must be self-contained (import the library at the top of the cell).\n\n"
            f"**Chart description:**\n{cell.strip()}\n\n"
            f"**Available DataFrames:**\n{schema_block}"
        )

        from ...session import get_default_swarm

        swarm = get_default_swarm(ip)
        try:
            swarm.run_sync(query, inject_context=False, ip=ip)
        except KeyboardInterrupt:
            print("\n[JiuwenSwarm] Visualisation generation cancelled.")

    ip.register_magic_function(jiuwen_viz, magic_kind="cell", magic_name="jiuwen_viz")

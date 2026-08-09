"""The ``%%jiuwen_translate`` cell magic — translate code between data-processing libraries."""

from __future__ import annotations

_KNOWN_LIBS: dict[str, str] = {
    "polars": "Polars",
    "dask": "Dask",
    "spark": "PySpark",
    "pyspark": "PySpark",
    "torch": "PyTorch",
    "pytorch": "PyTorch",
    "jax": "JAX",
    "cudf": "cuDF (GPU pandas)",
    "modin": "Modin",
    "vaex": "Vaex",
    "sql": "SQL (via DuckDB)",
    "pandas": "pandas",
    "numpy": "NumPy",
}


def register(ip) -> None:
    """Register ``%%jiuwen_translate`` with the given IPython shell."""

    def jiuwen_translate(line: str, cell: str) -> None:
        """Translate the cell body to a different data-processing library.

        The agent produces a complete, runnable equivalent in the target library
        and inserts it as a new cell immediately below. The original cell is kept.

        Arguments
        ---------
        --to LIBRARY   Target library (required).
                       Supported: polars, dask, spark, torch, sql, modin, jax, cudf, vaex, numpy

        Usage::

            %%jiuwen_translate --to polars
            df_agg = df.groupby("region").agg({"revenue": "sum", "orders": "count"})

            %%jiuwen_translate --to sql
            result = df[df["age"] > 30].sort_values("revenue", ascending=False).head(20)

            %%jiuwen_translate --to dask
            result = df.merge(other, on="id").groupby("category")["amount"].sum()
        """
        import shlex

        tokens = shlex.split(line.strip()) if line.strip() else []

        target_lib: str | None = None
        i = 0
        while i < len(tokens):
            if tokens[i] == "--to" and i + 1 < len(tokens):
                target_lib = tokens[i + 1].lower()
                i += 2
            else:
                i += 1

        if target_lib is None:
            known = ", ".join(sorted(_KNOWN_LIBS))
            print(f"Usage: %%jiuwen_translate --to <library>\nKnown targets: {known}")
            return

        if not cell.strip():
            print("Usage: %%jiuwen_translate --to <library>\n<code to translate>")
            return

        lib_label = _KNOWN_LIBS.get(target_lib, target_lib)

        query = (
            f"Translate the following Python code to {lib_label}.\n\n"
            "Rules:\n"
            "- Produce a complete, runnable equivalent — no placeholders.\n"
            "- Preserve all logic, column names, and output variable names.\n"
            "- Add brief inline comments where the API differs meaningfully.\n"
            "- If the translation requires additional imports, include them at the top.\n"
            "- Use `insert_notebook_cell` to insert the translated code as a new cell.\n\n"
            "**Original code:**\n"
            f"```python\n{cell.strip()}\n```"
        )

        from ...session import get_default_swarm

        swarm = get_default_swarm(ip)
        print(f"[JiuwenSwarm] Translating to {lib_label}…")
        try:
            swarm.run_sync(query, inject_context=False, ip=ip)
        except KeyboardInterrupt:
            print("\n[JiuwenSwarm] Translation cancelled.")

    ip.register_magic_function(jiuwen_translate, magic_kind="cell", magic_name="jiuwen_translate")

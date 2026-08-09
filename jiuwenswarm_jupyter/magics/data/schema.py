"""The ``%jiuwen_schema`` line magic — auto-generate a data dictionary for DataFrames."""

from __future__ import annotations


def register(ip) -> None:
    """Register ``%jiuwen_schema`` with the given IPython shell."""

    def jiuwen_schema(line: str) -> None:
        """Infer and document a human-readable data dictionary for DataFrames.

        For each column the agent infers a plain-English description from the
        column name, sample values, and distribution, then writes a markdown
        data dictionary.  Output is inserted as a markdown cell and optionally
        written to a file.

        Arguments
        ---------
        DF_NAME ...    One or more DataFrame variable names.
                       Omit to document all DataFrames currently in the namespace.
        --output PATH  Write the dictionary to this markdown file as well.

        Usage::

            %jiuwen_schema                          # all DataFrames in scope
            %jiuwen_schema df_train                 # one specific DataFrame
            %jiuwen_schema df_train df_test         # multiple DataFrames
            %jiuwen_schema df --output data_dict.md
        """
        import shlex

        tokens = shlex.split(line.strip()) if line.strip() else []

        df_names: list[str] = []
        output_file: str | None = None

        i = 0
        while i < len(tokens):
            if tokens[i] == "--output" and i + 1 < len(tokens):
                output_file = tokens[i + 1]
                i += 2
            elif not tokens[i].startswith("--"):
                df_names.append(tokens[i])
                i += 1
            else:
                i += 1

        # If no names given, find all DataFrames in the namespace.
        if not df_names:
            try:
                import pandas as pd
                df_names = [
                    name for name, val in ip.user_ns.items()
                    if not name.startswith("_") and isinstance(val, pd.DataFrame)
                ]
            except ImportError:
                df_names = []
            if not df_names:
                print("[JiuwenSwarm] No DataFrames found in the namespace. "
                      "Specify one: %jiuwen_schema df")
                return

        parts: list[str] = []
        for name in df_names:
            df = ip.user_ns.get(name)
            if df is None:
                print(f"[JiuwenSwarm] '{name}' not found — skipping.")
                continue

            cols = list(df.columns) if hasattr(df, "columns") else []
            shape = getattr(df, "shape", "?")

            col_summaries: list[str] = []
            for col in cols[:80]:
                try:
                    series = df[col]
                    dtype = str(series.dtype)
                    n_null = int(series.isnull().sum())
                    pct_null = f"{100 * n_null / len(series):.1f}%" if len(series) else "?"
                    n_unique = series.nunique()
                    sample = series.dropna().head(5).tolist()
                    col_summaries.append(
                        f"  - `{col}` ({dtype}): {n_null} nulls ({pct_null}), "
                        f"{n_unique} unique, sample={sample}"
                    )
                except Exception:
                    col_summaries.append(f"  - `{col}`: (could not profile)")

            parts.append(
                f"**DataFrame `{name}`** — shape={shape}\n"
                + "\n".join(col_summaries)
            )

        if not parts:
            return

        file_note = (
            f" Then save the full dictionary to `{output_file}` using a file write."
            if output_file
            else ""
        )

        query = (
            "Generate a markdown data dictionary for the following DataFrame(s). "
            "For each column write: a one-sentence plain-English description inferred "
            "from the column name and sample values, the data type, null rate, and "
            "any data quality observations (e.g. high cardinality, suspicious constant "
            "values, ID-like pattern). "
            "Insert the result as a markdown cell using `insert_notebook_cell`."
            f"{file_note}\n\n"
            + "\n\n".join(parts)
        )

        from ...session import get_default_swarm

        swarm = get_default_swarm(ip)
        print(f"[JiuwenSwarm] Generating schema for: {', '.join(df_names)}")
        try:
            swarm.run_sync(query, inject_context=False, ip=ip)
        except KeyboardInterrupt:
            print("\n[JiuwenSwarm] Schema generation cancelled.")

    ip.register_magic_function(jiuwen_schema, magic_kind="line", magic_name="jiuwen_schema")

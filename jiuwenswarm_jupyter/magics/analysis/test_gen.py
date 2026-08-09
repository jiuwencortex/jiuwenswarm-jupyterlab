"""The ``%%jiuwen_test`` cell magic — generate pytest unit tests for the cell's code."""

from __future__ import annotations


def register(ip) -> None:
    """Register ``%%jiuwen_test`` with the given IPython shell."""

    def jiuwen_test(line: str, cell: str) -> None:
        """Ask the agent to generate pytest unit tests for the code in the cell body.

        The agent writes complete, runnable tests and inserts them as a new
        code cell.  The cell itself is NOT executed — it is read and sent
        to the agent as source only.

        Options
        -------
        --file PATH   Write tests to this file instead of inserting a cell.
                      Appends if the file already exists.

        Usage::

            %%jiuwen_test
            def normalize(df, cols):
                return (df[cols] - df[cols].mean()) / df[cols].std()

            %%jiuwen_test --file tests/test_preprocessing.py
            class FeatureEncoder:
                ...
        """
        import shlex

        if not cell or not cell.strip():
            print("Usage: %%jiuwen_test\\n<function or class to test>")
            return

        tokens = shlex.split(line.strip()) if line.strip() else []
        output_file: str | None = None
        i = 0
        while i < len(tokens):
            if tokens[i] == "--file" and i + 1 < len(tokens):
                output_file = tokens[i + 1]
                i += 2
            else:
                i += 1

        file_instruction = (
            f"Write the tests to `{output_file}` using the `insert_notebook_cell` tool "
            f"with cell_type='code'.  Use a comment at the top: `# tests for {output_file}`."
            if output_file
            else "Insert the tests as a new code cell using the `insert_notebook_cell` tool."
        )

        query = (
            "Generate a complete set of pytest unit tests for the following Python code. "
            "Cover normal cases, edge cases, and known failure modes. "
            "Use plain pytest — no external fixtures beyond what is standard. "
            f"{file_instruction}\n\n"
            f"**Code to test:**\n```python\n{cell.strip()}\n```"
        )

        from ...session import get_default_swarm

        swarm = get_default_swarm(ip)
        try:
            swarm.run_sync(query, inject_context=False, ip=ip)
        except KeyboardInterrupt:
            print("\n[JiuwenSwarm] Test generation cancelled.")

    ip.register_magic_function(jiuwen_test, magic_kind="cell", magic_name="jiuwen_test")

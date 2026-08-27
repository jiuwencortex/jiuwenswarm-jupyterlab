"""The ``%%jiuwen_doc`` cell magic — auto-generate docstrings for functions and classes."""

from __future__ import annotations


def register(ip) -> None:
    """Register ``%%jiuwen_doc`` with the given IPython shell."""

    def jiuwen_doc(line: str, cell: str) -> None:
        """Generate a complete docstring for the function or class in the cell.

        The agent reads the signature and body, writes a NumPy or Google-style
        docstring (parameters, returns, raises, examples), and uses
        ``replace_notebook_cell`` to rewrite the cell with the docstring inserted.
        The original logic is untouched — only the docstring is added.

        Options
        -------
        --style STYLE   Docstring style: numpy (default) | google | sphinx.
        --no-replace    Stream the docstring as output instead of updating the cell.

        Usage::

            %%jiuwen_doc
            def normalize(df, cols, clip=None):
                result = (df[cols] - df[cols].mean()) / df[cols].std()
                if clip:
                    result = result.clip(-clip, clip)
                return result

            %%jiuwen_doc --style google
            class FeatureEncoder:
                def fit(self, df): ...
                def transform(self, df): ...
        """
        import shlex

        if not cell or not cell.strip():
            print("Usage: %%jiuwen_doc [--style numpy|google|sphinx]\\n<function or class>")
            return

        tokens = shlex.split(line.strip()) if line.strip() else []
        style = "numpy"
        no_replace = False

        i = 0
        while i < len(tokens):
            if tokens[i] == "--style" and i + 1 < len(tokens):
                style = tokens[i + 1].lower()
                i += 2
            elif tokens[i] == "--no-replace":
                no_replace = True
                i += 1
            else:
                i += 1

        replace_instruction = (
            "Stream the result as output text only — do not call insert_notebook_cell "
            "or replace_notebook_cell."
            if no_replace
            else
            "Use `replace_notebook_cell` to rewrite the current cell with the docstring "
            "inserted immediately after the function/class definition line. "
            "Preserve all original code exactly — only add the docstring."
        )

        query = (
            f"Add a complete {style}-style docstring to the following Python code. "
            "Cover: purpose, all parameters (name, type, description), return value(s), "
            "exceptions raised, and one concise usage example. "
            f"{replace_instruction}\n\n"
            f"**Code:**\n```python\n{cell.strip()}\n```"
        )

        from ...session import get_default_swarm

        swarm = get_default_swarm(ip)
        try:
            swarm.run_sync(query, inject_context=False, ip=ip)
        except KeyboardInterrupt:
            print("\n[JiuwenSwarm] Docstring generation cancelled.")

    ip.register_magic_function(jiuwen_doc, magic_kind="cell", magic_name="jiuwen_doc")

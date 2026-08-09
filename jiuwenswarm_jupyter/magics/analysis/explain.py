"""The ``%%jiuwen_explain`` cell magic — run a cell then have the agent narrate what it did."""

from __future__ import annotations


def register(ip) -> None:
    """Register ``%%jiuwen_explain`` with the given IPython shell."""

    def jiuwen_explain(line: str, cell: str) -> None:
        """Execute the cell normally, then stream an agent explanation into the output.

        The cell body runs first in the notebook namespace.  The agent then
        receives the source code and any captured stdout and writes a markdown
        explanation suitable for inserting as a narrative cell.

        Usage::

            %%jiuwen_explain
            model.fit(X_train, y_train)
            print(model.score(X_test, y_test))
        """
        if not cell or not cell.strip():
            print("Usage: %%jiuwen_explain\\n<code to execute and explain>")
            return

        # Execute the cell in the user namespace via IPython so that cell
        # outputs (rich display, stdout) appear normally before the explanation.
        result = ip.run_cell(cell)

        # Collect stdout captured by IPython, if any.
        stdout_text = ""
        if result.error_before_exec or result.error_in_exec:
            error_str = str(result.error_in_exec or result.error_before_exec)
        else:
            error_str = ""

        parts = [
            "I just ran the following Python cell in my Jupyter notebook. "
            "Write a concise markdown explanation of what the code does, "
            "what the output shows, and any caveats a reader should know. "
            "Address a technical but non-expert audience. "
            "Write it as a self-contained paragraph or two — suitable as a "
            "markdown cell inserted directly below the code.\n",
            f"**Cell code:**\n```python\n{cell.strip()}\n```",
        ]
        if stdout_text:
            parts.append(f"**Captured output:**\n```\n{stdout_text[:800]}\n```")
        if error_str:
            parts.append(f"**Error encountered:**\n```\n{error_str[:400]}\n```")

        query = "\n\n".join(parts)

        from ...session import get_default_swarm

        swarm = get_default_swarm(ip)
        try:
            swarm.run_sync(query, inject_context=False, ip=ip)
        except KeyboardInterrupt:
            print("\n[JiuwenSwarm] Explanation cancelled.")

    ip.register_magic_function(jiuwen_explain, magic_kind="cell", magic_name="jiuwen_explain")

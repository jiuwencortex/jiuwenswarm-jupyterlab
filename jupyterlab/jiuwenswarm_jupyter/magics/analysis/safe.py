"""The ``%%jiuwen_safe`` cell magic — static analysis before execution."""

from __future__ import annotations


def register(ip) -> None:
    """Register ``%%jiuwen_safe`` with the given IPython shell."""

    def jiuwen_safe(line: str, cell: str) -> None:
        """Have the agent analyse the cell for side effects before you run it.

        The cell is NOT executed.  The agent receives the code and reports on:

        - Files written, moved, or deleted
        - Network calls (HTTP requests, database writes)
        - In-place mutations of shared variables
        - Non-reversible operations (``DROP TABLE``, ``os.remove``, etc.)
        - Potential exceptions and data loss paths

        After the analysis is streamed, the cell body is printed so you can
        copy it into a fresh cell and run it manually when you are ready.

        Options
        -------
        --run   Execute the cell immediately after the agent finishes the analysis.
                Use only when you are confident the code is safe.

        Usage::

            %%jiuwen_safe
            os.remove("data/raw/sensitive.csv")
            shutil.rmtree("output/")

            %%jiuwen_safe --run
            df.to_sql("results", engine, if_exists="replace")
        """
        if not cell or not cell.strip():
            print("Usage: %%jiuwen_safe\\n<code to analyse before running>")
            return

        run_after = "--run" in (line or "")

        query = (
            "Before I execute the following Python code in my Jupyter notebook, "
            "please analyse it for side effects and risks. Report:\n"
            "1. Any files that will be created, overwritten, or deleted.\n"
            "2. Any network requests or database writes.\n"
            "3. Any in-place mutations of large shared variables.\n"
            "4. Any non-reversible operations.\n"
            "5. Any paths that could raise an exception and leave state inconsistent.\n"
            "Conclude with a one-line verdict: SAFE / CAUTION / HIGH RISK.\n\n"
            f"**Code:**\n```python\n{cell.strip()}\n```"
        )

        from ...session import get_default_swarm

        swarm = get_default_swarm(ip)
        try:
            swarm.run_sync(query, inject_context=True, ip=ip)
        except KeyboardInterrupt:
            print("\n[JiuwenSwarm] Analysis cancelled.")
            return

        if run_after:
            print("\n[JiuwenSwarm] --run flag set — executing cell now.\n")
            ip.run_cell(cell)
        else:
            print(
                "\n[JiuwenSwarm] Cell was NOT executed. "
                "Copy the code into a new cell to run it, or re-run with --run."
            )

    ip.register_magic_function(jiuwen_safe, magic_kind="cell", magic_name="jiuwen_safe")

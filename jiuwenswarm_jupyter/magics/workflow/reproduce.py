"""The ``%jiuwen_reproduce`` line magic — convert a notebook into a production script."""

from __future__ import annotations


def register(ip) -> None:
    """Register ``%jiuwen_reproduce`` with the given IPython shell."""

    def jiuwen_reproduce(line: str) -> None:
        """Convert all executed notebook cells into a clean, standalone Python script.

        The agent extracts imports, wraps logic into functions, adds argparse for
        configurable file paths, strips or adapts cell magic commands, and writes
        a ``if __name__ == '__main__'`` entry point.  The result is a script that
        can be run in CI/CD or a production environment without Jupyter.

        Options
        -------
        --output PATH   Write the script here (default: reproduce.py).
        --no-argparse   Skip argparse — produce a plain procedural script.

        Usage::

            %jiuwen_reproduce
            %jiuwen_reproduce --output src/pipeline.py
            %jiuwen_reproduce --output train.py --no-argparse
        """
        import os
        import shlex

        tokens = shlex.split(line.strip()) if line.strip() else []
        output_file = "reproduce.py"
        use_argparse = True

        i = 0
        while i < len(tokens):
            if tokens[i] == "--output" and i + 1 < len(tokens):
                output_file = tokens[i + 1]
                i += 2
            elif tokens[i] == "--no-argparse":
                use_argparse = False
                i += 1
            else:
                i += 1

        # Gather executed cells.
        cells: list[str] = []
        try:
            hist = list(ip.history_manager.get_tail(n=80, include_latest=True))
            cells = [src for _, _, src in hist if src.strip()]
        except Exception:
            pass

        if not cells:
            print("[JiuwenSwarm] No executed cells found.")
            return

        cells_block = "\n\n".join(
            f"# --- Cell {i + 1} ---\n{src.strip()}"
            for i, src in enumerate(cells)
        )

        dest = os.path.join(os.getcwd(), output_file)
        argparse_note = (
            "Include argparse to make file paths and key parameters configurable "
            "from the command line."
            if use_argparse
            else "Do not use argparse — produce a plain procedural script."
        )

        query = (
            "Convert the following Jupyter notebook cells into a clean, standalone "
            "Python script suitable for production or CI/CD execution.\n\n"
            "Rules:\n"
            "1. Consolidate all imports at the top.\n"
            "2. Wrap each logical stage (load data, preprocess, train, evaluate, save) "
            "into a clearly named function.\n"
            f"3. {argparse_note}\n"
            "4. Remove or replace any IPython magic commands (lines starting with "
            "% or %%) with equivalent Python code.\n"
            "5. Add a `if __name__ == '__main__':` block that calls the functions in order.\n"
            "6. Add brief inline comments explaining each stage.\n"
            f"After generating the script, save it to `{dest}` and print the path.\n\n"
            f"**Notebook cells ({len(cells)} total):**\n\n```python\n{cells_block}\n```"
        )

        from ...session import get_default_swarm

        swarm = get_default_swarm(ip)
        print(f"[JiuwenSwarm] Converting notebook → {dest}")
        try:
            response = swarm.run_sync(query, inject_context=False, ip=ip)
            # If the agent did not write the file, extract and save code blocks.
            if response and not os.path.exists(dest):
                import re
                blocks = re.findall(r"```python\n(.*?)```", response, re.DOTALL)
                if blocks:
                    with open(dest, "w", encoding="utf-8") as fh:
                        fh.write(blocks[-1])
                    print(f"[JiuwenSwarm] Script saved to {dest}")
        except KeyboardInterrupt:
            print("\n[JiuwenSwarm] Reproduce cancelled.")

    ip.register_magic_function(jiuwen_reproduce, magic_kind="line", magic_name="jiuwen_reproduce")

"""The ``%jiuwen_story`` line magic — convert the notebook into a narrated document."""

from __future__ import annotations


def register(ip) -> None:
    """Register ``%jiuwen_story`` with the given IPython shell."""

    def jiuwen_story(line: str) -> None:
        """Convert the executed notebook cells into a narrated blog post or paper draft.

        The agent receives every executed cell and writes a flowing document with
        an executive summary, section headings, and explanatory prose between
        code blocks.  Output is written to a markdown file and also streamed to
        the cell output so you can preview it immediately.

        Options
        -------
        --output PATH     Destination file (default: jiuwen_story.md)
        --style STYLE     Writing style: blog (default), paper, tutorial, report

        Usage::

            %jiuwen_story
            %jiuwen_story --output analysis.md --style report
            %jiuwen_story --style tutorial
        """
        import os
        import shlex

        tokens = shlex.split(line.strip()) if line.strip() else []
        output_file = "jiuwen_story.md"
        style = "blog"

        i = 0
        while i < len(tokens):
            if tokens[i] == "--output" and i + 1 < len(tokens):
                output_file = tokens[i + 1]
                i += 2
            elif tokens[i] == "--style" and i + 1 < len(tokens):
                style = tokens[i + 1]
                i += 2
            else:
                i += 1

        # Gather executed cells.
        cells: list[str] = []
        try:
            hist = list(ip.history_manager.get_tail(n=60, include_latest=True))
            cells = [src for _, _, src in hist if src.strip()]
        except Exception:
            pass

        if not cells:
            print("[JiuwenSwarm] No executed cells found. Run some notebook cells first.")
            return

        style_instructions = {
            "blog": (
                "Write in an engaging, conversational technical blog style. "
                "Use first person where natural. Include an intro and a conclusion."
            ),
            "paper": (
                "Write in a formal academic style with an abstract, introduction, "
                "methodology, results, and conclusion sections."
            ),
            "tutorial": (
                "Write as a step-by-step tutorial for someone learning the topic. "
                "Explain each step before showing the code, then interpret the result."
            ),
            "report": (
                "Write as a professional analytical report with an executive summary, "
                "findings, and recommendations."
            ),
        }.get(style, "Write in a clear, structured technical style.")

        cells_block = "\n\n".join(
            f"```python\n{src.strip()[:800]}\n```" for src in cells
        )

        dest = os.path.join(os.getcwd(), output_file)

        query = (
            f"{style_instructions}\n\n"
            "Below are all the code cells from a Jupyter notebook, in execution order. "
            "Produce a complete, self-contained document that narrates what is happening "
            "at each stage.  Include the code blocks verbatim using fenced markdown. "
            "Do NOT add fictional results or invent data you cannot see. "
            f"After writing the document, save it to `{dest}` using `insert_notebook_cell` "
            f"with cell_type='markdown' so the user can also see it inline, and print "
            f"the path `{dest}` so the user knows where the file is.\n\n"
            f"**Notebook cells ({len(cells)} total):**\n\n{cells_block}"
        )

        from ...session import get_default_swarm

        swarm = get_default_swarm(ip)
        print(f"[JiuwenSwarm] Generating {style} document → {dest}")
        try:
            response = swarm.run_sync(query, inject_context=False, ip=ip)
            # If agent did not write the file itself, save the response.
            if response and not os.path.exists(dest):
                with open(dest, "w", encoding="utf-8") as fh:
                    fh.write(response)
                print(f"[JiuwenSwarm] Saved to {dest}")
        except KeyboardInterrupt:
            print("\n[JiuwenSwarm] Story generation cancelled.")

    ip.register_magic_function(jiuwen_story, magic_kind="line", magic_name="jiuwen_story")

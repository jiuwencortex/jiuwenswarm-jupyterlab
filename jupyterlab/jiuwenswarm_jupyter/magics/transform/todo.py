"""The ``%jiuwen_todo`` line magic — find TODOs in executed cells and draft implementations."""

from __future__ import annotations

import re


_TODO_PATTERN = re.compile(
    r"(?:#\s*(TODO|FIXME|HACK|XXX|NOTE)[:\s].+|raise\s+NotImplementedError.*|pass\s*$)",
    re.IGNORECASE | re.MULTILINE,
)


def register(ip) -> None:
    """Register ``%jiuwen_todo`` with the given IPython shell."""

    def jiuwen_todo(line: str) -> None:
        """Scan executed cells for TODO/FIXME/HACK comments and unimplemented stubs.

        Collects every flagged location across the notebook's execution history,
        prints a numbered list, and sends them to the agent which drafts
        concrete implementations and inserts them as runnable cells.

        Options
        -------
        --list   Print found items only — do not call the agent.

        Usage::

            %jiuwen_todo
            %jiuwen_todo --list
        """
        list_only = "--list" in (line or "")

        # Gather executed cells.
        cells_with_src: list[tuple[int, str]] = []
        try:
            hist = list(ip.history_manager.get_tail(n=60, include_latest=True))
            cells_with_src = [(idx + 1, src) for idx, (_, _, src) in enumerate(hist) if src.strip()]
        except Exception:
            pass

        if not cells_with_src:
            print("[JiuwenSwarm] No executed cells found.")
            return

        # Find all TODO-like lines.
        findings: list[dict] = []
        for cell_num, src in cells_with_src:
            for line_num, src_line in enumerate(src.splitlines(), 1):
                stripped = src_line.strip()
                if _TODO_PATTERN.search(stripped):
                    findings.append({
                        "cell": cell_num,
                        "line": line_num,
                        "text": stripped,
                        "cell_src": src,
                    })

        if not findings:
            print("[JiuwenSwarm] No TODO / FIXME / unimplemented stubs found.")
            return

        print(f"[JiuwenSwarm] Found {len(findings)} item(s):")
        for i, f in enumerate(findings, 1):
            print(f"  {i}. Cell {f['cell']}, line {f['line']}: {f['text']}")

        if list_only:
            return

        # Build agent query grouping items by cell.
        cells_seen: dict[int, str] = {}
        for f in findings:
            cells_seen[f["cell"]] = f["cell_src"]

        cells_block = "\n\n".join(
            f"**Cell {num}:**\n```python\n{src.strip()[:800]}\n```"
            for num, src in cells_seen.items()
        )

        items_list = "\n".join(
            f"{i}. Cell {f['cell']}, line {f['line']}: `{f['text']}`"
            for i, f in enumerate(findings, 1)
        )

        query = (
            f"I have {len(findings)} unfinished items in my Jupyter notebook. "
            "For each one, draft a concrete implementation and insert it as a code cell "
            "using `insert_notebook_cell`. Keep each implementation minimal and correct.\n\n"
            f"**Items to implement:**\n{items_list}\n\n"
            f"**Relevant cells:**\n\n{cells_block}"
        )

        from ...session import get_default_swarm

        swarm = get_default_swarm(ip)
        try:
            swarm.run_sync(query, inject_context=True, ip=ip)
        except KeyboardInterrupt:
            print("\n[JiuwenSwarm] TODO drafting cancelled.")

    ip.register_magic_function(jiuwen_todo, magic_kind="line", magic_name="jiuwen_todo")

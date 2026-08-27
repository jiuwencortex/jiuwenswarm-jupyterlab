"""The ``%jiuwen_diff`` line magic — compare notebook state to a git ref with agent commentary."""

from __future__ import annotations


def register(ip) -> None:
    """Register ``%jiuwen_diff`` with the given IPython shell."""

    def jiuwen_diff(line: str) -> None:
        """Diff the current working directory against a git commit and get agent commentary.

        Runs ``git diff <ref>`` in the current directory, displays the raw diff,
        and sends it to the agent for a structured review of what changed and why
        it matters.

        Arguments
        ---------
        REF         Git reference to diff against (default: HEAD).
                    Accepts: HEAD~1, HEAD~3, a commit hash, a branch name.
        --stat      Show only ``git diff --stat`` summary (no full patch).
        --file PATH Limit the diff to a specific file.

        Usage::

            %jiuwen_diff                   # diff current state vs HEAD
            %jiuwen_diff HEAD~3            # last 3 commits
            %jiuwen_diff main              # compare against main branch
            %jiuwen_diff HEAD~1 --stat     # summary only
            %jiuwen_diff HEAD~2 --file src/model.py
        """
        import shlex
        import subprocess

        tokens = shlex.split(line.strip()) if line.strip() else []

        ref = "HEAD"
        stat_only = False
        file_path: str | None = None

        i = 0
        while i < len(tokens):
            if tokens[i] == "--stat":
                stat_only = True
                i += 1
            elif tokens[i] == "--file" and i + 1 < len(tokens):
                file_path = tokens[i + 1]
                i += 2
            elif not tokens[i].startswith("--"):
                ref = tokens[i]
                i += 1
            else:
                i += 1

        # Build git command.
        cmd = ["git", "diff", ref]
        if stat_only:
            cmd.append("--stat")
        if file_path:
            cmd += ["--", file_path]

        try:
            result = subprocess.run(  # noqa: S603
                cmd,
                capture_output=True,
                text=True,
                cwd=str(__import__("pathlib").Path.cwd()),
            )
        except FileNotFoundError:
            print("[JiuwenSwarm] git not found. Make sure git is installed and on PATH.")
            return

        if result.returncode != 0:
            print(f"[JiuwenSwarm] git diff failed:\n{result.stderr.strip()}")
            return

        diff_text = result.stdout.strip()
        if not diff_text:
            print(f"[JiuwenSwarm] No differences found between working tree and {ref!r}.")
            return

        # Print a truncated preview.
        preview = diff_text[:3000]
        print(preview)
        if len(diff_text) > 3000:
            print(f"\n… (truncated — {len(diff_text)} chars total)")

        query = (
            f"I ran `git diff {ref}` in my project. "
            "Please review these changes: describe what was changed and why it might matter, "
            "flag anything that looks risky or unintentional, and note any improvements "
            "or issues you observe in the new code.\n\n"
            f"**Diff ({ref}):**\n```diff\n{diff_text[:4000]}\n```"
        )

        from ...session import get_default_swarm

        swarm = get_default_swarm(ip)
        try:
            swarm.run_sync(query, inject_context=False, ip=ip)
        except KeyboardInterrupt:
            print("\n[JiuwenSwarm] Diff review cancelled.")

    ip.register_magic_function(jiuwen_diff, magic_kind="line", magic_name="jiuwen_diff")

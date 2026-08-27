"""The ``%jiuwen_memory`` line magic — persistent cross-notebook knowledge base."""

from __future__ import annotations

import json
import time
from pathlib import Path

_MEMORY_FILE = Path.home() / ".jiuwenswarm" / "memory.json"


def _load() -> list[dict]:
    try:
        if _MEMORY_FILE.exists():
            return json.loads(_MEMORY_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return []


def _save(entries: list[dict]) -> None:
    _MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    _MEMORY_FILE.write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")


def register(ip) -> None:
    """Register ``%jiuwen_memory`` with the given IPython shell."""

    def jiuwen_memory(line: str) -> None:
        """Save and retrieve notes across notebooks in a persistent knowledge base.

        Notes are stored in ``~/.jiuwenswarm/memory.json`` and survive kernel
        restarts and notebook closures.  The ``search`` command also sends
        matching notes to the agent so it can reason over them in context.

        Commands
        --------
        save "NOTE"     Save a plain-text note (use quotes for multi-word notes).
        search "QUERY"  Find notes matching QUERY and send them to the agent.
        list            Print all saved notes with their timestamps and IDs.
        delete ID       Remove a note by its numeric ID.
        clear           Delete all saved notes (asks for confirmation first).

        Usage::

            %jiuwen_memory save "Validation AUC plateaus after 200 XGBoost trees"
            %jiuwen_memory search "XGBoost performance"
            %jiuwen_memory list
            %jiuwen_memory delete 3
            %jiuwen_memory clear
        """
        import shlex

        tokens = shlex.split(line.strip()) if line.strip() else []
        if not tokens:
            print(
                "Commands: save <note>  |  search <query>  |  list  |  delete <id>  |  clear"
            )
            return

        cmd = tokens[0].lower()

        # ── save ──────────────────────────────────────────────────────────────
        if cmd == "save":
            note = " ".join(tokens[1:]).strip().strip('"\'')
            if not note:
                print("Usage: %jiuwen_memory save \"Your note text here\"")
                return
            entries = _load()
            entry = {
                "id": len(entries) + 1,
                "note": note,
                "saved_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "notebook": str(Path.cwd()),
            }
            entries.append(entry)
            _save(entries)
            print(f"[JiuwenSwarm] Memory #{entry['id']} saved.")

        # ── search ────────────────────────────────────────────────────────────
        elif cmd == "search":
            query_text = " ".join(tokens[1:]).strip().strip('"\'')
            if not query_text:
                print("Usage: %jiuwen_memory search \"your query\"")
                return
            entries = _load()
            terms = query_text.lower().split()
            hits = [e for e in entries if any(t in e["note"].lower() for t in terms)]
            if not hits:
                print(f"[JiuwenSwarm] No memories matching {query_text!r}.")
                return
            print(f"[JiuwenSwarm] Found {len(hits)} matching note(s).")
            for e in hits:
                print(f"  #{e['id']} [{e['saved_at']}] {e['note']}")

            notes_block = "\n".join(f"- (#{e['id']}, {e['saved_at']}) {e['note']}" for e in hits)
            agent_query = (
                f"I searched my personal knowledge base for {query_text!r} and found "
                f"these notes from past notebook sessions. Please help me reason about "
                f"them in the context of my current work.\n\n"
                f"**Matching notes:**\n{notes_block}"
            )

            from ...session import get_default_swarm

            swarm = get_default_swarm(ip)
            try:
                swarm.run_sync(agent_query, inject_context=True, ip=ip)
            except KeyboardInterrupt:
                print("\n[JiuwenSwarm] Memory search cancelled.")

        # ── list ──────────────────────────────────────────────────────────────
        elif cmd == "list":
            entries = _load()
            if not entries:
                print("[JiuwenSwarm] Memory is empty. Use: %jiuwen_memory save \"note\"")
                return
            print(f"[JiuwenSwarm] {len(entries)} saved note(s):")
            for e in entries:
                nb = Path(e.get("notebook", "")).name or "unknown"
                print(f"  #{e['id']} [{e['saved_at']}] ({nb}) {e['note']}")

        # ── delete ────────────────────────────────────────────────────────────
        elif cmd == "delete":
            if len(tokens) < 2:
                print("Usage: %jiuwen_memory delete <id>")
                return
            try:
                target_id = int(tokens[1])
            except ValueError:
                print(f"Expected a numeric ID, got {tokens[1]!r}")
                return
            entries = _load()
            before = len(entries)
            entries = [e for e in entries if e["id"] != target_id]
            if len(entries) == before:
                print(f"[JiuwenSwarm] No note with ID {target_id}.")
            else:
                _save(entries)
                print(f"[JiuwenSwarm] Memory #{target_id} deleted.")

        # ── clear ─────────────────────────────────────────────────────────────
        elif cmd == "clear":
            entries = _load()
            if not entries:
                print("[JiuwenSwarm] Memory is already empty.")
                return
            _save([])
            print(f"[JiuwenSwarm] Cleared {len(entries)} note(s).")

        else:
            print(f"[JiuwenSwarm] Unknown command {cmd!r}. Commands: save | search | list | delete | clear")

    ip.register_magic_function(jiuwen_memory, magic_kind="line", magic_name="jiuwen_memory")

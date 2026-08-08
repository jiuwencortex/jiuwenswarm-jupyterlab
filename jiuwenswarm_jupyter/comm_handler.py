"""Phase 2: Python kernel side of the Jupyter comm bridge.

When the JupyterLab frontend extension connects (TypeScript ChatPanel opens a
comm to the 'jiuwenswarm' target), this module handles all incoming messages,
routes them to JiuWenSwarm, and streams events back via comm.send().

The event schema is identical to the IDE WebSocket protocol, so the shared
chat.html requires no changes to understand the events.

Registration happens in __init__.py via load_ipython_extension → register_comm_target().
"""

from __future__ import annotations

import asyncio
import traceback
from typing import Any


# Session ID → running asyncio.Task; used for cancellation.
_active_tasks: dict[str, "asyncio.Task[None]"] = {}


# ── Public entry point ────────────────────────────────────────────────────────

def register_comm_target(ip=None) -> bool:
    """Register the 'jiuwenswarm' comm target with the running kernel.

    Tries the modern ``comm`` package first (Jupyter 7+ / JupyterLab 4+),
    then falls back to ``ipykernel`` for older environments.

    Returns True on success, False if registration could not be completed
    (e.g. not running inside a kernel).
    """
    # Modern path: jupyter_client 7+ / JupyterLab 4+
    try:
        import comm as _comm_pkg
        _comm_pkg.get_comm_manager().register_target("jiuwenswarm", _comm_target)
        return True
    except Exception:
        pass

    # Legacy path: ipykernel < 6 / classic Notebook
    try:
        import ipykernel.comm as _ik_comm
        kernel = _get_kernel()
        if kernel is not None:
            kernel.comm_manager.register_target("jiuwenswarm", _comm_target)
            return True
    except Exception:
        pass

    return False


# ── Comm target callback ──────────────────────────────────────────────────────

def _comm_target(comm, open_msg: dict) -> None:
    """Called once per frontend connection (comm open)."""

    @comm.on_msg
    def _on_message(msg: dict) -> None:
        data: dict = msg.get("content", {}).get("data", {})
        if not data:
            return

        msg_type: str = data.get("type", "")

        if msg_type == "send_message":
            _schedule(_handle_send_message(comm, data))
        elif msg_type == "cancel":
            _cancel(data.get("session_id", ""))
        elif msg_type == "get_sessions":
            comm.send({"type": "sessions", "sessions": []})

    # Immediately inform the frontend that the bridge is ready.
    comm.send({
        "type": "connected",
        "server_version": "1.0",
        "available_modes": ["agent", "code", "team", "code.team"],
    })


# ── Message handlers ──────────────────────────────────────────────────────────

async def _handle_send_message(comm, data: dict) -> None:
    """Run the agent stream and forward every chunk to the frontend."""
    session_id: str = data.get("session_id") or f"jupyter_comm_{id(comm)}"
    query: str = data.get("query", "").strip()
    mode: str = data.get("mode", "agent")
    inject_context: bool = data.get("inject_context", True)
    turn_id: str = f"turn_{id(data)}"

    if not query:
        return

    # Cancel any running stream on the same session.
    _cancel(session_id)
    _active_tasks[session_id] = asyncio.current_task()  # type: ignore[assignment]

    try:
        from .client import JupyterSwarm
        from .context import build_context_block

        # Inject notebook context into the query if requested.
        full_query = query
        if inject_context:
            try:
                import IPython
                ip = IPython.get_ipython()
                if ip is not None:
                    ctx = build_context_block(ip)
                    if ctx:
                        full_query = f"{ctx}\n\n---\n\n{query}"
            except Exception:
                pass

        backend = JupyterSwarm(mode=mode, session_id=session_id)._get_swarm()

        async for chunk in backend.process_message_stream(
            session_id=session_id,
            message=full_query,
            mode=mode,
            channel_id="jupyter",
        ):
            event = _chunk_to_event(chunk, session_id, turn_id)
            if event:
                comm.send(event)

    except asyncio.CancelledError:
        comm.send({
            "type": "chat.error",
            "session_id": session_id,
            "turn_id": turn_id,
            "error": "Cancelled by user.",
        })
    except Exception:
        comm.send({
            "type": "chat.error",
            "session_id": session_id,
            "turn_id": turn_id,
            "error": traceback.format_exc(limit=5),
        })
    finally:
        _active_tasks.pop(session_id, None)


# ── Event conversion ──────────────────────────────────────────────────────────

def _chunk_to_event(chunk: Any, session_id: str, turn_id: str) -> dict | None:
    """Convert an AgentResponseChunk (object or dict) to a frontend event dict."""

    def _get(attr: str, default: Any = "") -> Any:
        if isinstance(chunk, dict):
            return chunk.get(attr, default)
        return getattr(chunk, attr, default)

    event_type: str = _get("type", "")

    if event_type in ("chat.delta", "delta"):
        return {"type": "chat.delta", "session_id": session_id, "turn_id": turn_id, "delta": _get("delta")}

    if event_type in ("chat.final", "final"):
        return {"type": "chat.final", "session_id": session_id, "turn_id": turn_id, "text": _get("text")}

    if event_type in ("chat.error", "error"):
        return {"type": "chat.error", "session_id": session_id, "turn_id": turn_id, "error": _get("error")}

    if event_type in ("tool.call", "tool_call"):
        return {
            "type": "tool.call",
            "session_id": session_id,
            "turn_id": turn_id,
            "tool_id": _get("tool_id", turn_id),
            "name": _get("name"),
            "args": _get("args", {}),
        }

    if event_type in ("tool.result", "tool_result"):
        result = str(_get("result", ""))
        return {
            "type": "tool.result",
            "session_id": session_id,
            "turn_id": turn_id,
            "tool_id": _get("tool_id", turn_id),
            "name": _get("name"),
            "result": result[:2000] + ("…" if len(result) > 2000 else ""),
            "is_error": _get("is_error", False),
        }

    # Pass team.* events through unchanged so the swarm map updates.
    if event_type.startswith("team."):
        if isinstance(chunk, dict):
            return {**chunk, "session_id": session_id}
        return {"type": event_type, "session_id": session_id}

    return None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _schedule(coro) -> None:
    """Schedule a coroutine on the running event loop (ipykernel uses asyncio)."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(coro)
        else:
            loop.run_until_complete(coro)
    except RuntimeError:
        asyncio.run(coro)


def _cancel(session_id: str) -> None:
    task = _active_tasks.pop(session_id, None)
    if task and not task.done():
        task.cancel()


def _get_kernel():
    try:
        import ipykernel.ipkernel
        return ipykernel.ipkernel.IPythonKernel.instance()
    except Exception:
        return None

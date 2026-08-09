"""Thin wrapper around JiuWenSwarm facade with Jupyter-specific defaults."""

from __future__ import annotations

import asyncio
import os
import sys
from typing import TYPE_CHECKING, AsyncIterator, Any

from .session import make_session_id

if TYPE_CHECKING:
    pass

_VALID_MODES = {"agent", "code", "team", "code.team"}


def _ensure_jiuwenswarm() -> None:
    """Make ``jiuwenswarm`` importable from the running kernel.

    The kernel that executes ``%%jiuwen`` may be a different Python than the
    one the JiuWenSwarm server was launched from. Fall back to the source
    checkout (via ``JIWENSWARM_SOURCE`` or the default workspace path) when
    the package is not already installed in the kernel.
    """
    try:
        import jiuwenswarm  # noqa: F401
        if getattr(jiuwenswarm, "__file__", None):
            return
    except ImportError:
        pass

    sys.modules.pop("jiuwenswarm", None)

    candidates = [
        os.environ.get("JIWENSWARM_SOURCE"),
        "C:\\Workspace\\openjiuwen\\jiuwenswarm",
    ]
    for candidate in candidates:
        if not candidate:
            continue
        package_dir = os.path.join(candidate, "jiuwenswarm")
        if os.path.isdir(os.path.join(package_dir, "common")) and candidate not in sys.path:
            sys.path.insert(0, candidate)
            try:
                import jiuwenswarm  # noqa: F401
                if getattr(jiuwenswarm, "__file__", None):
                    return
            except ImportError:
                continue
    raise ImportError(
        "jiuwenswarm is not importable from this kernel. "
        "Point JIWENSWARM_SOURCE at the checkout (parent of the "
        "'jiuwenswarm' package dir) or install it into the kernel."
    )


class JupyterSwarm:
    """In-process JiuwenSwarm client for Jupyter notebooks.

    Wraps ``JiuWenSwarm.process_message_stream()`` with notebook-specific
    session handling, context injection, and IPython output rendering.

    Usage::

        swarm = JupyterSwarm(mode="code")
        result = await swarm.run("Write a preprocessing pipeline for df")
    """

    def __init__(
        self,
        mode: str = "agent",
        session_id: str | None = None,
    ) -> None:
        if mode not in _VALID_MODES:
            raise ValueError(f"mode must be one of {_VALID_MODES}, got {mode!r}")

        self._mode = mode
        self._session_id = session_id or make_session_id()
        self._swarm = None  # lazy — imported on first use to avoid hard dep at load time
        self.timeout: float = 300.0  # default; overridable via %jiuwen_config or run() kwarg
        self._history: list[dict] = []  # in-memory exchange log for %jiuwen_export / %jiuwen_replay

    # ── Public ──────────────────────────────────────────────────────────────

    @property
    def session_id(self) -> str:
        return self._session_id

    @property
    def mode(self) -> str:
        return self._mode

    @mode.setter
    def mode(self, value: str) -> None:
        if value not in _VALID_MODES:
            raise ValueError(f"mode must be one of {_VALID_MODES}, got {value!r}")
        self._mode = value

    async def run(
        self,
        query: str,
        *,
        mode: str | None = None,
        inject_context: bool = True,
        timeout: float | None = None,
        ip=None,
    ) -> str:
        """Send *query* to the agent and stream output into the current cell.

        Parameters
        ----------
        query:
            The user message to send.
        mode:
            Override the instance-level mode for this call only.
        inject_context:
            When ``True`` (default), notebook variable and cell history context
            is prepended to the query before sending to the agent.
        timeout:
            Seconds before the stream is forcibly cancelled.
        ip:
            IPython shell instance used for context extraction.  If *None*,
            the running shell is located automatically.

        Returns
        -------
        str
            The final complete assistant response text.
        """
        from .context import build_context_block
        from .display import StreamRenderer

        effective_mode = mode or self._mode
        if effective_mode not in _VALID_MODES:
            raise ValueError(f"mode must be one of {_VALID_MODES}, got {effective_mode!r}")

        if ip is None:
            try:
                import IPython
                ip = IPython.get_ipython()
            except Exception:
                ip = None

        full_query = query
        if ip is not None:
            from .config import get_config
            cfg = get_config(ip)
            pinned = cfg.pinned_vars if cfg.pinned_vars else None
            if inject_context:
                ctx = build_context_block(ip, pinned_vars=pinned)
            elif pinned:
                # inject_context=False but user has pinned vars — include only those
                from .context import _extract_pinned_variables
                pin_section = _extract_pinned_variables(ip, pinned)
                ctx = pin_section if pin_section else ""
            else:
                ctx = ""
            if ctx:
                full_query = f"{ctx}\n\n---\n\n{query}"

        effective_timeout = timeout if timeout is not None else self.timeout
        renderer = StreamRenderer()

        import time as _time

        final_text = ""
        try:
            async with asyncio.timeout(effective_timeout):
                final_text = await renderer.render(
                    self._stream_request(
                        query=full_query,
                        mode=effective_mode,
                    )
                )
        except TimeoutError:
            renderer.finalize_error(f"Request timed out after {effective_timeout:.0f}s.")

        # Record exchange for %jiuwen_export / %jiuwen_replay
        if query.strip() and final_text:
            self._history.append({
                "timestamp": _time.strftime("%Y-%m-%dT%H:%M:%S"),
                "mode": effective_mode,
                "query": query.strip(),
                "response": final_text.strip(),
            })

        return final_text

    def get_history(self) -> list[dict]:
        """Return the list of recorded exchanges for this session."""
        return list(self._history)

    def clear_history(self) -> None:
        """Clear the in-memory exchange log (does not affect the session on the server)."""
        self._history.clear()

    def run_sync(self, query: str, **kwargs) -> str:
        """Synchronous wrapper around :meth:`run` for use in cell magics."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We are inside an existing event loop (e.g. ipykernel).
                import nest_asyncio  # type: ignore[import]
                nest_asyncio.apply()
                return loop.run_until_complete(self.run(query, **kwargs))
            else:
                return loop.run_until_complete(self.run(query, **kwargs))
        except ImportError:
            # nest_asyncio not available — create a new loop in a thread
            result: list[str] = []

            def _run() -> None:
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    result.append(new_loop.run_until_complete(self.run(query, **kwargs)))
                finally:
                    new_loop.close()

            import threading
            t = threading.Thread(target=_run, daemon=True)
            t.start()
            t.join()
            return result[0] if result else ""

    # ── Internal ─────────────────────────────────────────────────────────────

    def _get_swarm(self):
        if self._swarm is None:
            try:
                _ensure_jiuwenswarm()
                from jiuwenswarm.server.runtime.agent_adapter.interface import JiuWenSwarm
                self._swarm = JiuWenSwarm()
            except ImportError as exc:
                raise ImportError(
                    "jiuwenswarm is not installed. "
                    "Install it with: pip install jiuwenswarm"
                ) from exc
        return self._swarm

    async def _stream_request(self, query: str, mode: str) -> AsyncIterator[Any]:
        """Build an ``AgentRequest`` and stream chunks from the JiuWenSwarm facade.

        The ``JiuWenSwarm.process_message_stream`` API expects a single
        ``AgentRequest`` carrying ``params`` with ``query`` and ``mode``.
        """
        import time as _time
        from uuid import uuid4

        _ensure_jiuwenswarm()
        from jiuwenswarm.common.schema.agent import AgentRequest
        from jiuwenswarm.common.schema.message import ReqMethod

        request = AgentRequest(
            request_id=f"jupyter_{uuid4().hex[:12]}",
            channel_id="jupyter",
            session_id=self._session_id,
            req_method=ReqMethod.CHAT_SEND,
            params={"query": query, "mode": mode},
            is_stream=True,
            timestamp=_time.time(),
        )
        async for chunk in self._get_swarm().process_message_stream(request):
            yield chunk

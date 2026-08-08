"""Thin wrapper around JiuWenSwarm facade with Jupyter-specific defaults."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from .session import make_session_id

if TYPE_CHECKING:
    pass

_VALID_MODES = {"agent", "code", "team", "code.team"}


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
        if inject_context and ip is not None:
            ctx = build_context_block(ip)
            if ctx:
                full_query = f"{ctx}\n\n---\n\n{query}"

        effective_timeout = timeout if timeout is not None else self.timeout
        swarm = self._get_swarm()
        renderer = StreamRenderer()

        try:
            async with asyncio.timeout(effective_timeout):
                final_text = await renderer.render(
                    swarm.process_message_stream(
                        session_id=self._session_id,
                        message=full_query,
                        mode=effective_mode,
                        channel_id="jupyter",
                    )
                )
        except TimeoutError:
            renderer.finalize_error(f"Request timed out after {effective_timeout:.0f}s.")
            final_text = ""

        return final_text

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
                from jiuwenswarm.server.runtime.agent_adapter.interface import JiuWenSwarm
                self._swarm = JiuWenSwarm()
            except ImportError as exc:
                raise ImportError(
                    "jiuwenswarm is not installed. "
                    "Install it with: pip install jiuwenswarm"
                ) from exc
        return self._swarm

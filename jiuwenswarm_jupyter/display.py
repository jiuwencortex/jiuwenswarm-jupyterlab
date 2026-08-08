"""IPython output rendering for streamed agent responses.

Uses ``display()`` with ``display_id`` and ``update_display()`` to stream
``chat.delta`` events into a single output widget that updates in place,
rather than printing chunks as separate lines.

Tool call events (``tool.call``, ``tool.result``) render as compact
collapsible HTML blocks so the user can see agent activity without it
dominating the output.
"""

from __future__ import annotations

import html
import time
from typing import AsyncIterator, Any


class StreamRenderer:
    """Renders a stream of ``AgentResponseChunk`` objects into IPython output."""

    def __init__(self) -> None:
        self._text_buf: list[str] = []
        self._tool_calls: list[dict] = []
        self._display_handle = None
        self._start_time = time.monotonic()

    async def render(self, stream: AsyncIterator[Any]) -> str:
        """Consume *stream* and render to the current cell output.

        Returns the final accumulated text.
        """
        from IPython.display import display, HTML, update_display  # type: ignore[import]

        # Create initial placeholder so the output area appears immediately.
        display_id = f"jiuwen_{id(self)}"
        display(HTML("<em style='color: var(--jp-content-font-color2, #888)'>Thinking…</em>"),
                display_id=display_id)

        async for chunk in stream:
            self._handle_chunk(chunk)
            update_display(
                HTML(self._render_html()),
                display_id=display_id,
            )

        # Final render with completion marker.
        elapsed = time.monotonic() - self._start_time
        update_display(
            HTML(self._render_html(done=True, elapsed=elapsed)),
            display_id=display_id,
        )

        return "".join(self._text_buf)

    def finalize_error(self, message: str) -> None:
        """Render an error message into the current cell."""
        from IPython.display import display, HTML  # type: ignore[import]
        display(HTML(
            f"<div style='color: #f14c4c; padding: 4px 0;'>"
            f"&#9888; {html.escape(message)}</div>"
        ))

    # ── Internal ─────────────────────────────────────────────────────────────

    def _handle_chunk(self, chunk: Any) -> None:
        event_type = getattr(chunk, "type", None) or chunk.get("type", "") if isinstance(chunk, dict) else ""

        if event_type in ("chat.delta", "delta"):
            delta = (
                chunk.get("delta", "") if isinstance(chunk, dict)
                else getattr(chunk, "delta", "")
            )
            if delta:
                self._text_buf.append(delta)

        elif event_type in ("tool.call", "tool_call"):
            name = (
                chunk.get("name", "tool") if isinstance(chunk, dict)
                else getattr(chunk, "name", "tool")
            )
            args = (
                chunk.get("args", {}) if isinstance(chunk, dict)
                else getattr(chunk, "args", {})
            )
            self._tool_calls.append({"type": "call", "name": name, "args": args})

        elif event_type in ("tool.result", "tool_result"):
            name = (
                chunk.get("name", "") if isinstance(chunk, dict)
                else getattr(chunk, "name", "")
            )
            result = (
                chunk.get("result", "") if isinstance(chunk, dict)
                else getattr(chunk, "result", "")
            )
            self._tool_calls.append({"type": "result", "name": name, "result": result})

        elif event_type in ("chat.final", "final"):
            text = (
                chunk.get("text", "") if isinstance(chunk, dict)
                else getattr(chunk, "text", "")
            )
            if text:
                self._text_buf = [text]

    def _render_html(self, done: bool = False, elapsed: float | None = None) -> str:
        parts: list[str] = []

        # Tool call summary (collapsible blocks)
        if self._tool_calls:
            parts.append('<div style="margin-bottom:8px">')
            for item in self._tool_calls:
                if item["type"] == "call":
                    args_str = html.escape(str(item.get("args", "")))
                    label = html.escape(f"{item['name']}({args_str[:120]}{'…' if len(args_str) > 120 else ''})")
                    parts.append(
                        f"<details style='margin:2px 0; font-size:12px; "
                        f"color: var(--jp-content-font-color2, #888)'>"
                        f"<summary>&#9656; tool: {label}</summary></details>"
                    )
            parts.append("</div>")

        # Main response text (rendered as preformatted, markdown-like)
        text = "".join(self._text_buf)
        if text:
            escaped = html.escape(text)
            # Very basic markdown: wrap code blocks in <pre>
            parts.append(
                f"<div style='font-family: inherit; white-space: pre-wrap; "
                f"word-break: break-word; line-height: 1.5'>{escaped}</div>"
            )

        # Footer
        if done and elapsed is not None:
            parts.append(
                f"<div style='font-size:11px; color: var(--jp-content-font-color3, #aaa); "
                f"margin-top:6px'>"
                f"&#10003; done &nbsp;&middot;&nbsp; {elapsed:.1f}s</div>"
            )

        return "".join(parts) if parts else "<em>…</em>"

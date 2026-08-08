"""Notebook context extractor.

Builds a concise summary of the notebook state (variables, DataFrames,
recent cell history) to inject into the agent's system prompt so it
understands what already exists in the notebook without the user having
to explain it.
"""

from __future__ import annotations

import sys
import traceback
from typing import Any

# Maximum number of recent cells included in the context block.
_MAX_CELLS = 5
# Maximum characters per cell output before truncation.
_MAX_OUTPUT_CHARS = 800
# Maximum characters per DataFrame head() representation.
_MAX_DF_CHARS = 600


def build_context_block(ip) -> str:
    """Return a markdown-formatted context block for the current notebook state.

    Parameters
    ----------
    ip:
        The running ``IPython.InteractiveShell`` instance.

    Returns
    -------
    str
        A context block suitable for prepending to the user query, or an
        empty string if no meaningful context could be extracted.
    """
    parts: list[str] = []

    var_section = _extract_variables(ip)
    if var_section:
        parts.append(var_section)

    cell_section = _extract_recent_cells(ip)
    if cell_section:
        parts.append(cell_section)

    if not parts:
        return ""

    header = "<!-- jiuwenswarm notebook context -->"
    footer = "<!-- end context -->"
    return f"{header}\n" + "\n\n".join(parts) + f"\n{footer}"


# ── Variable extraction ───────────────────────────────────────────────────────

def _extract_variables(ip) -> str:
    ns: dict[str, Any] = ip.user_ns
    lines: list[str] = []

    for name, value in sorted(ns.items()):
        if name.startswith("_") or name in ("In", "Out", "exit", "quit", "get_ipython"):
            continue
        if callable(value) and not _is_interesting_callable(value):
            continue

        type_name = type(value).__name__
        summary = _summarize_value(name, value)
        lines.append(f"- `{name}` ({type_name}): {summary}")

    if not lines:
        return ""
    return "**Notebook variables:**\n" + "\n".join(lines)


def _is_interesting_callable(value: Any) -> bool:
    """Return True for class instances that happen to be callable."""
    return hasattr(value, "__class__") and value.__class__.__name__ not in (
        "function", "builtin_function_or_method", "method", "type"
    )


def _summarize_value(name: str, value: Any) -> str:
    try:
        # pandas DataFrame
        if _is_dataframe(value):
            return _summarize_dataframe(value)
        # numpy array
        if _is_ndarray(value):
            shape = getattr(value, "shape", None)
            dtype = getattr(value, "dtype", None)
            return f"shape={shape}, dtype={dtype}"
        # list / tuple / set
        if isinstance(value, (list, tuple, set)):
            return f"len={len(value)}, first={repr(next(iter(value), None))}"  # type: ignore[call-overload]
        # dict
        if isinstance(value, dict):
            keys_preview = list(value.keys())[:5]
            return f"len={len(value)}, keys_preview={keys_preview}"
        # scalar / short repr
        r = repr(value)
        return r if len(r) <= 120 else r[:120] + "…"
    except Exception:
        return "<error summarizing>"


def _is_dataframe(value: Any) -> bool:
    try:
        return type(value).__name__ == "DataFrame" and "pandas" in type(value).__module__
    except Exception:
        return False


def _is_ndarray(value: Any) -> bool:
    try:
        return type(value).__name__ == "ndarray" and "numpy" in type(value).__module__
    except Exception:
        return False


def _summarize_dataframe(df: Any) -> str:
    try:
        shape = df.shape
        dtypes = dict(df.dtypes.astype(str))
        try:
            head_str = df.head(3).to_string(max_cols=10)
        except Exception:
            head_str = "<unable to render>"
        if len(head_str) > _MAX_DF_CHARS:
            head_str = head_str[:_MAX_DF_CHARS] + "…"
        dtype_summary = ", ".join(f"{c}:{t}" for c, t in list(dtypes.items())[:8])
        if len(dtypes) > 8:
            dtype_summary += f", … (+{len(dtypes) - 8} more)"
        return f"shape={shape}, dtypes=[{dtype_summary}]\n```\n{head_str}\n```"
    except Exception:
        return "<DataFrame — error summarizing>"


# ── Cell history extraction ───────────────────────────────────────────────────

def _extract_recent_cells(ip) -> str:
    try:
        history_manager = getattr(ip, "history_manager", None)
        if history_manager is None:
            return ""

        # get_tail returns list of (session, line_number, input) tuples
        raw = list(history_manager.get_tail(_MAX_CELLS, include_latest=False))
        if not raw:
            return ""

        cell_lines: list[str] = []
        for _session, _lineno, cell_input in raw:
            if not cell_input or not cell_input.strip():
                continue
            snippet = cell_input.strip()
            if len(snippet) > _MAX_OUTPUT_CHARS:
                snippet = snippet[:_MAX_OUTPUT_CHARS] + "\n…"
            cell_lines.append(f"```python\n{snippet}\n```")

        if not cell_lines:
            return ""

        return f"**Recent cell inputs (last {len(cell_lines)}):**\n" + "\n".join(cell_lines)
    except Exception:
        return ""

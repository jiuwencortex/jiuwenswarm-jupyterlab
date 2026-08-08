"""Phase 3: Notebook-native agent tools.

Three tools the agent can invoke when running inside a Jupyter notebook:

    read_notebook_cell(cell_index)
        Read the source and output of any previously-run cell.
        Lets the agent reference earlier analysis without the user
        having to copy-paste anything into the prompt.

    read_variable(name)
        Inspect any Python variable currently in the notebook namespace.
        Works with DataFrames, numpy arrays, dicts, models — anything.

    insert_notebook_cell(source, cell_type)
        Propose a new code or markdown cell.  In Phase 2 (sidebar panel
        active) the cell is inserted directly into the notebook via comm.
        In Phase 1 (magic-only) it is displayed in the output area so the
        user can copy it.

    replace_notebook_cell(cell_index, new_source)
        Rewrite an existing cell identified by its execution history index.
        Shows a before/after diff.  In Phase 2 the user sees an Apply/Cancel
        dialog in JupyterLab; in Phase 1 the diff is rendered in the output.

Usage — direct call from a cell:

    from jiuwenswarm_jupyter import read_variable, read_notebook_cell
    print(read_variable("df"))
    print(read_notebook_cell(2))

Usage — agent calls these automatically when enabled:

    %%jiuwen --tools notebook
    Look at cell 3 and the model variable, then write an evaluation function.
"""

from __future__ import annotations

import json
from typing import Any


# ── read_notebook_cell ────────────────────────────────────────────────────────

def read_notebook_cell(cell_index: int, ip=None) -> dict:
    """Return the source code and output of a previously executed cell.

    Parameters
    ----------
    cell_index:
        Zero-based position in execution history (0 = oldest executed cell).
    ip:
        IPython shell.  Auto-detected if None.

    Returns
    -------
    dict with keys: cell_index, line_number, source, output (or error).
    """
    ip = _get_ip(ip)
    if ip is None:
        return {"error": "No active IPython shell found."}

    try:
        history = list(ip.history_manager.get_tail(1000, include_latest=True))

        if not history:
            return {"error": "No cell history available yet. Execute some cells first."}

        if cell_index < 0 or cell_index >= len(history):
            return {
                "error": f"Cell index {cell_index} is out of range.",
                "total_executed_cells": len(history),
                "valid_range": f"0 to {len(history) - 1}",
            }

        _session, line_no, source = history[cell_index]

        # Retrieve output from the Out dict
        output: str | None = None
        out_dict: dict = ip.user_ns.get("Out", {})
        if line_no in out_dict:
            raw = repr(out_dict[line_no])
            output = raw[:2000] + ("…" if len(raw) > 2000 else "")

        return {
            "cell_index": cell_index,
            "line_number": line_no,
            "source": source,
            "output": output,
        }

    except Exception as exc:
        return {"error": str(exc)}


# ── read_variable ─────────────────────────────────────────────────────────────

def read_variable(name: str, ip=None) -> str:
    """Return a human-readable description of a variable in the notebook namespace.

    Parameters
    ----------
    name:
        Variable name to inspect.
    ip:
        IPython shell.  Auto-detected if None.

    Returns
    -------
    Formatted string describing the variable's type, shape/size, and content.
    """
    ip = _get_ip(ip)
    if ip is None:
        return "Error: No active IPython shell found."

    if name not in ip.user_ns:
        available = sorted(k for k in ip.user_ns if not k.startswith("_") and k not in
                          ("In", "Out", "exit", "quit", "get_ipython"))[:30]
        return f"Variable '{name}' not found.\nAvailable variables: {available}"

    value = ip.user_ns[name]

    try:
        if _is_dataframe(value):
            return _format_dataframe(name, value)
        if _is_ndarray(value):
            return _format_ndarray(name, value)
        if isinstance(value, (list, tuple)):
            return _format_sequence(name, value)
        if isinstance(value, dict):
            return _format_dict(name, value)
        r = repr(value)
        return f"{name} ({type(value).__name__}): " + (r[:2000] + "…" if len(r) > 2000 else r)
    except Exception as exc:
        return f"Error reading '{name}': {exc}"


# ── insert_notebook_cell ──────────────────────────────────────────────────────

def insert_notebook_cell(
    source: str,
    cell_type: str = "code",
    execute: bool = False,
    confirm_execute: bool = False,
    ip=None,
) -> str:
    """Insert a new cell into the current notebook.

    Phase 2 (JupyterLab sidebar active): inserts via Jupyter comm → the
    TypeScript frontend uses the JupyterLab notebook API to create the cell.
    When *confirm_execute* is True, a JupyterLab dialog is shown before
    running; in Phase 1 the user is prompted via ``input()``.

    Phase 1 (magic only): renders the proposed cell in the output area.

    Parameters
    ----------
    source:
        Source code or markdown content.
    cell_type:
        ``"code"`` or ``"markdown"``.
    execute:
        If True, execute the cell immediately after insertion.
    confirm_execute:
        If True (and *execute* is True), ask the user before running.  In
        Phase 2 this shows a JupyterLab dialog; in Phase 1 uses ``input()``.
    ip:
        IPython shell.  Auto-detected if None.

    Returns
    -------
    Status message string.
    """
    if cell_type not in ("code", "markdown"):
        return f'Error: cell_type must be "code" or "markdown", got {cell_type!r}'

    if not source.strip():
        return "Error: source is empty."

    # Phase 2 path: confirmation and execution are handled by the TypeScript frontend
    if _comm_insert(source, cell_type, execute, confirm_execute):
        action = " and queued for execution" if execute else ""
        return f"Cell inserted{action} into notebook."

    # Phase 1 fallback: display proposed cell in output area
    _display_proposed_cell(source, cell_type)

    if execute and cell_type == "code" and confirm_execute:
        answer = ""
        try:
            answer = input("Run this cell? [y/N]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            pass
        if answer not in ("y", "yes"):
            return "Cell displayed. Execution skipped (not confirmed)."

    return "Cell displayed in output area. Copy it into a new cell to run it."


# ── replace_notebook_cell ─────────────────────────────────────────────────────

def replace_notebook_cell(cell_index: int, new_source: str, ip=None) -> str:
    """Rewrite an existing notebook cell, showing a diff before applying.

    Identifies the cell by its execution history index — the same index
    returned by :func:`read_notebook_cell`.

    In Phase 2 (JupyterLab sidebar active): sends the old and new source to
    the TypeScript frontend, which shows a diff dialog with Apply/Cancel.

    In Phase 1 (magic only): renders a coloured unified diff in the cell
    output area so the user can review and apply the change manually.

    Parameters
    ----------
    cell_index:
        Zero-based position in execution history (same scale as
        ``read_notebook_cell``).
    new_source:
        The replacement source code.
    ip:
        IPython shell.  Auto-detected if None.

    Returns
    -------
    Status message string.
    """
    ip = _get_ip(ip)
    if ip is None:
        return "Error: No active IPython shell found."

    if not new_source.strip():
        return "Error: new_source is empty."

    try:
        history = list(ip.history_manager.get_tail(1000, include_latest=True))
    except Exception as exc:
        return f"Error reading cell history: {exc}"

    if not history:
        return "Error: No cell history available yet. Execute some cells first."

    if cell_index < 0 or cell_index >= len(history):
        return (
            f"Error: cell_index {cell_index} is out of range. "
            f"Valid range: 0 to {len(history) - 1}."
        )

    _session, line_no, old_source = history[cell_index]

    if old_source.strip() == new_source.strip():
        return "No changes: new_source is identical to the current cell."

    # Phase 2 path: interactive diff dialog in JupyterLab
    if _comm_replace(old_source, new_source, line_no):
        return "Diff dialog opened in JupyterLab. Click Apply to replace the cell."

    # Phase 1 fallback: render diff in the output area
    _display_diff(old_source, new_source)
    return "Diff displayed above. Update the cell source manually to apply the change."


# ── Tool schema (for agent registration) ─────────────────────────────────────

TOOL_DEFINITIONS: list[dict] = [
    {
        "name": "read_notebook_cell",
        "description": (
            "Read the source code and output of a specific cell in the current Jupyter notebook. "
            "Useful for referencing earlier analysis or data that the user already ran. "
            "Use total_executed_cells from an error response to know the valid range."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "cell_index": {
                    "type": "integer",
                    "description": "Zero-based index into execution history. 0 is the oldest cell.",
                },
            },
            "required": ["cell_index"],
        },
    },
    {
        "name": "read_variable",
        "description": (
            "Read the current value of any Python variable from the notebook namespace. "
            "Returns a formatted description including type, shape, and content preview. "
            "Works with pandas DataFrames, numpy arrays, lists, dicts, and other objects."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name of the Python variable to inspect.",
                },
            },
            "required": ["name"],
        },
    },
    {
        "name": "insert_notebook_cell",
        "description": (
            "Insert a new code or markdown cell into the current notebook. "
            "Prefer this over showing code in the chat response when the user will need to execute it. "
            "In JupyterLab the cell appears immediately in the notebook. "
            "In other environments it is shown as a formatted block in the output area."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "source": {
                    "type": "string",
                    "description": "Source code or markdown to put in the new cell.",
                },
                "cell_type": {
                    "type": "string",
                    "enum": ["code", "markdown"],
                    "description": "Cell type. Defaults to code.",
                },
                "execute": {
                    "type": "boolean",
                    "description": "If true, execute the cell immediately after inserting.",
                },
                "confirm_execute": {
                    "type": "boolean",
                    "description": (
                        "If true (and execute is true), ask the user for confirmation before "
                        "running the cell. Use this when auto-running could be destructive."
                    ),
                },
            },
            "required": ["source"],
        },
    },
    {
        "name": "replace_notebook_cell",
        "description": (
            "Rewrite an existing notebook cell with new source code, showing a diff before applying. "
            "Use this instead of insert_notebook_cell when you want to fix or improve code the user "
            "already has in a cell. The user must approve the change via a dialog (Phase 2) or "
            "review the diff in the output area (Phase 1)."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "cell_index": {
                    "type": "integer",
                    "description": (
                        "Zero-based index into execution history — the same value "
                        "returned by read_notebook_cell."
                    ),
                },
                "new_source": {
                    "type": "string",
                    "description": "The complete replacement source code for the cell.",
                },
            },
            "required": ["cell_index", "new_source"],
        },
    },
]


def get_dispatcher(ip=None) -> dict[str, Any]:
    """Return a mapping of tool name → callable for use with JiuWenSwarm.

    Example::

        from jiuwenswarm_jupyter.notebook_tools import get_dispatcher
        dispatcher = get_dispatcher()
        result = dispatcher["read_variable"]("df")
    """
    _ip = ip or _get_ip()
    return {
        "read_notebook_cell": lambda cell_index: read_notebook_cell(cell_index, ip=_ip),
        "read_variable": lambda name: read_variable(name, ip=_ip),
        "insert_notebook_cell": lambda source, cell_type="code", execute=False, confirm_execute=False: insert_notebook_cell(
            source, cell_type=cell_type, execute=execute, confirm_execute=confirm_execute, ip=_ip
        ),
        "replace_notebook_cell": lambda cell_index, new_source: replace_notebook_cell(
            cell_index, new_source, ip=_ip
        ),
    }


# ── Internal helpers ──────────────────────────────────────────────────────────

def _get_ip(ip=None):
    if ip is not None:
        return ip
    try:
        import IPython
        return IPython.get_ipython()
    except Exception:
        return None


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


def _format_dataframe(name: str, df: Any) -> str:
    try:
        rows, cols = df.shape
        dtypes = {str(c): str(t) for c, t in df.dtypes.items()}
        dtype_str = ", ".join(f"{c}:{t}" for c, t in list(dtypes.items())[:8])
        if len(dtypes) > 8:
            dtype_str += f", … (+{len(dtypes) - 8} more)"

        missing = int(df.isnull().sum().sum())
        head_str = df.head(5).to_string(max_cols=12)

        try:
            desc_str = df.describe().to_string()
        except Exception:
            desc_str = "(describe unavailable)"

        return (
            f"{name}: DataFrame  rows={rows:,}  cols={cols}\n"
            f"dtypes: {dtype_str}\n"
            f"missing values: {missing:,}\n\n"
            f"First 5 rows:\n{head_str}\n\n"
            f"Numeric summary:\n{desc_str}"
        )[:4000]
    except Exception as exc:
        return f"{name}: DataFrame (error formatting: {exc})"


def _format_ndarray(name: str, arr: Any) -> str:
    try:
        preview = repr(arr.flat[:20].tolist())
        return (
            f"{name}: ndarray  shape={arr.shape}  dtype={arr.dtype}\n"
            f"min={arr.min():.4g}  max={arr.max():.4g}  mean={arr.mean():.4g}\n"
            f"First values: {preview}"
        )
    except Exception as exc:
        return f"{name}: ndarray (error formatting: {exc})"


def _format_sequence(name: str, seq: Any) -> str:
    type_name = type(seq).__name__
    preview = repr(seq[:10])
    suffix = f"  … ({len(seq) - 10} more)" if len(seq) > 10 else ""
    return f"{name}: {type_name}  len={len(seq)}\n{preview}{suffix}"


def _format_dict(name: str, d: dict) -> str:
    keys_preview = list(d.keys())[:15]
    try:
        sample = json.dumps({k: d[k] for k in keys_preview}, indent=2, default=str)
        sample = sample[:1500] + ("…" if len(sample) > 1500 else "")
    except Exception:
        sample = repr(dict(list(d.items())[:5]))
    suffix = f"\n… ({len(d) - 15} more keys)" if len(d) > 15 else ""
    return f"{name}: dict  len={len(d)}\n{sample}{suffix}"


def _comm_insert(source: str, cell_type: str, execute: bool, confirm_execute: bool = False) -> bool:
    """Try to insert via Jupyter comm (Phase 2 path). Returns True on success.

    Sends ``jiuwen_generated: true`` so the frontend can tag the inserted cell
    with ``cell.metadata.jiuwen_generated = true``.  When ``confirm_execute``
    is True the TypeScript frontend shows a dialog before running.
    """
    try:
        import comm as _comm_pkg
        c = _comm_pkg.create_comm(target_name="jiuwenswarm_cell_insert")
        c.open({
            "type": "insert_cell",
            "source": source,
            "cell_type": cell_type,
            "execute": execute,
            "confirm_execute": confirm_execute,
            "jiuwen_generated": True,
        })
        return True
    except Exception:
        return False


def _display_proposed_cell(source: str, cell_type: str) -> None:
    """Render the proposed cell as formatted HTML in the output area.

    A ``# [jiuwen]`` tag is prepended to code cells so agent-generated code
    is identifiable even without the Phase 2 comm path.
    """
    import html as _html
    # Tag code cells so the source is identifiable
    tagged_source = f"# [jiuwen] Generated by JiuwenSwarm\n{source}" if cell_type == "code" else source
    try:
        from IPython.display import display, HTML
        escaped = _html.escape(tagged_source)
        display(HTML(
            f"<div style='border:1px solid #555; border-radius:4px; padding:10px; "
            f"margin:6px 0; background:#1a1a2e'>"
            f"<div style='font-size:11px; color:#888; margin-bottom:6px; font-weight:600'>"
            f"&#9655; Proposed {cell_type} cell (generated by JiuwenSwarm) — copy into a new cell to run</div>"
            f"<pre style='margin:0; color:#d4d4d4; font-size:12.5px; "
            f"white-space:pre-wrap; line-height:1.5'>{escaped}</pre>"
            f"</div>"
        ))
    except Exception:
        print(f"\n--- Generated {cell_type} cell (JiuwenSwarm) ---\n{tagged_source}\n--- end ---\n")


def _comm_replace(old_source: str, new_source: str, line_no: int) -> bool:
    """Try to send a cell-replace request via Jupyter comm (Phase 2 path). Returns True on success.

    Sends ``{type, old_source, new_source, line_no}`` to the
    ``jiuwenswarm_cell_replace`` comm target registered in TypeScript.
    The frontend finds the matching cell by ``old_source`` content, shows
    a diff dialog, and applies ``new_source`` on Apply.
    """
    try:
        import comm as _comm_pkg
        c = _comm_pkg.create_comm(target_name="jiuwenswarm_cell_replace")
        c.open({
            "type": "replace_cell",
            "old_source": old_source,
            "new_source": new_source,
            "line_no": line_no,
        })
        return True
    except Exception:
        return False


def _display_diff(old_source: str, new_source: str) -> None:
    """Render a coloured unified diff in the output area (Phase 1 fallback)."""
    import difflib
    import html as _html

    old_lines = old_source.splitlines(keepends=True)
    new_lines = new_source.splitlines(keepends=True)
    diff_lines = list(difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile="current cell",
        tofile="proposed replacement",
        lineterm="",
    ))

    if not diff_lines:
        return

    def _line_html(line: str) -> str:
        escaped = _html.escape(line.rstrip("\n"))
        if line.startswith("+") and not line.startswith("+++"):
            bg, fg = "#1a4a1a", "#a8d8a8"
        elif line.startswith("-") and not line.startswith("---"):
            bg, fg = "#4a1a1a", "#d8a8a8"
        elif line.startswith("@@"):
            bg, fg = "#1a2a4a", "#a8c8f8"
        else:
            bg, fg = "#1e1e1e", "#c8c8c8"
        return (
            f"<div style='background:{bg}; color:{fg}; padding:1px 8px; "
            f"font-family:monospace; font-size:12.5px; white-space:pre'>{escaped}</div>"
        )

    body_html = "".join(_line_html(ln) for ln in diff_lines)
    try:
        from IPython.display import display, HTML
        display(HTML(
            f"<div style='border:1px solid #555; border-radius:4px; margin:6px 0; overflow:auto'>"
            f"<div style='font-size:11px; color:#888; padding:6px 8px; font-weight:600; background:#111'>"
            f"&#9651; JiuwenSwarm — proposed cell rewrite (Phase 1: apply manually)</div>"
            f"{body_html}"
            f"</div>"
        ))
    except Exception:
        print("".join(diff_lines))

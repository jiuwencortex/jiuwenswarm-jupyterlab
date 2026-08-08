"""Optional ipywidgets control panel for JiuwenSwarm.

Provides ``show_jiuwen_panel()`` — an interactive UI that replaces typing
``%%jiuwen`` flags manually.  Requires ``ipywidgets`` (not installed by
default; install with ``pip install ipywidgets``).

Load with:
    from jiuwenswarm_jupyter import show_jiuwen_panel
    show_jiuwen_panel()

Or via the magic registered on extension load:
    %jiuwen_panel
"""

from __future__ import annotations


def show_jiuwen_panel(ip=None) -> None:
    """Display an interactive ipywidgets panel for JiuwenSwarm.

    The panel provides dropdowns and sliders for all ``%%jiuwen`` options so
    the user does not need to remember flag syntax.  Output is streamed into
    the panel's output area, identical to a ``%%jiuwen`` cell.

    Parameters
    ----------
    ip:
        IPython shell.  Auto-detected if None.

    Raises
    ------
    ImportError
        If ``ipywidgets`` is not installed.
    """
    try:
        import ipywidgets as W
        from IPython.display import display
    except ImportError:
        print(
            "ipywidgets is not installed.\n"
            "Install it with:  pip install ipywidgets\n"
            "Then restart the kernel and try again."
        )
        return

    from .config import get_config
    from .session import get_default_swarm, get_named_swarm

    if ip is None:
        try:
            import IPython
            ip = IPython.get_ipython()
        except Exception:
            ip = None

    cfg = get_config(ip)

    # ── Widgets ───────────────────────────────────────────────────────────────
    mode_dd = W.Dropdown(
        options=["agent", "code", "team", "code.team"],
        value=cfg.mode,
        description="Mode:",
        layout=W.Layout(width="160px"),
    )

    timeout_slider = W.IntSlider(
        value=int(cfg.timeout),
        min=30,
        max=3600,
        step=30,
        description="Timeout (s):",
        style={"description_width": "initial"},
        layout=W.Layout(width="300px"),
    )

    context_chk = W.Checkbox(
        value=cfg.inject_context,
        description="Inject notebook context",
        indent=False,
        layout=W.Layout(width="220px"),
    )

    session_txt = W.Text(
        placeholder="(default session)",
        description="Session:",
        layout=W.Layout(width="260px"),
    )

    query_area = W.Textarea(
        placeholder="Ask JiuwenSwarm anything…",
        layout=W.Layout(width="100%", height="90px"),
    )

    send_btn = W.Button(
        description="Send",
        button_style="primary",
        icon="paper-plane",
        layout=W.Layout(width="90px"),
    )

    clear_btn = W.Button(
        description="Clear",
        button_style="",
        layout=W.Layout(width="80px"),
    )

    status_lbl = W.Label(value="")

    output_area = W.Output(
        layout=W.Layout(
            border="1px solid #d0d0d0",
            border_radius="4px",
            padding="8px",
            min_height="60px",
            max_height="600px",
            overflow_y="auto",
        )
    )

    # ── Layout ────────────────────────────────────────────────────────────────
    controls_row = W.HBox(
        [mode_dd, timeout_slider, context_chk, session_txt],
        layout=W.Layout(flex_flow="row wrap", gap="12px", margin="0 0 8px 0"),
    )
    btn_row = W.HBox([send_btn, clear_btn, status_lbl], layout=W.Layout(gap="8px", align_items="center"))
    panel = W.VBox(
        [controls_row, query_area, btn_row, output_area],
        layout=W.Layout(padding="12px", border="1px solid #bbb", border_radius="6px", width="100%"),
    )

    # ── Handlers ─────────────────────────────────────────────────────────────
    def _on_send(_b) -> None:
        q = query_area.value.strip()
        if not q:
            status_lbl.value = "⚠ Empty query."
            return

        send_btn.disabled = True
        status_lbl.value = "⏳ Waiting…"

        session_name = session_txt.value.strip()
        swarm = get_named_swarm(session_name) if session_name else get_default_swarm(ip)

        with output_area:
            swarm.run_sync(
                q,
                mode=mode_dd.value,
                inject_context=context_chk.value,
                timeout=float(timeout_slider.value),
                ip=ip,
            )

        status_lbl.value = "✓ Done."
        send_btn.disabled = False

    def _on_clear(_b) -> None:
        output_area.clear_output()
        status_lbl.value = ""

    send_btn.on_click(_on_send)
    clear_btn.on_click(_on_clear)

    display(panel)


def register_panel_magic(ip) -> None:
    """Register the ``%jiuwen_panel`` line magic on *ip*."""

    @ip.register_magic_function
    def jiuwen_panel(line: str) -> None:  # noqa: ARG001
        """Open the JiuwenSwarm ipywidgets control panel.

        Usage::

            %jiuwen_panel
        """
        show_jiuwen_panel(ip=ip)

"""The ``%jiuwen_chat`` line magic — embed the full chat UI in the cell output."""

from __future__ import annotations


def register(ip) -> None:
    """Register ``%jiuwen_chat`` with the given IPython shell."""

    def jiuwen_chat(line: str) -> None:
        """Embed the JiuwenSwarm chat UI directly in the cell output.

        Displays the full themed chat interface — the same one used by the
        JupyterLab sidebar panel — as an embedded iframe inside the cell output
        area.  A JavaScript bridge connects the iframe to the running kernel via
        the Jupyter comm API.

        Most useful in environments that do not have the JupyterLab sidebar:
        Google Colab, Kaggle Notebooks, and classic Jupyter Notebook.
        In JupyterLab the sidebar panel is the preferred interface, but
        ``%jiuwen_chat`` works there too.

        Usage::

            %jiuwen_chat               # default height (520 px)
            %jiuwen_chat --height 700  # taller panel
        """
        import html as _html
        import pathlib
        import uuid

        from IPython.display import display, HTML

        # Parse --height option
        height = 520
        arg = line.strip()
        if arg:
            tokens = arg.split()
            if "--height" in tokens:
                idx = tokens.index("--height")
                try:
                    height = int(tokens[idx + 1])
                except (IndexError, ValueError):
                    pass

        # Locate chat.html — installed wheel path first, source tree fallback for dev.
        chat_html_path = pathlib.Path(__file__).resolve().parent.parent / "static" / "chat.html"
        if not chat_html_path.exists():
            # Development mode (pip install -e .): hatchling force-include does not
            # copy the file, so fall back to the canonical source location.
            chat_html_path = (
                pathlib.Path(__file__).resolve().parent.parent.parent
                / "packages" / "shared-webview" / "chat.html"
            )
        if not chat_html_path.exists():
            print(
                "[JiuwenSwarm] chat.html not found. "
                "Run 'pip install jiuwenswarm-jupyter' or check that "
                "packages/shared-webview/chat.html exists in the source tree."
            )
            return

        chat_html = chat_html_path.read_text(encoding="utf-8")

        # Unique ID so multiple %jiuwen_chat cells coexist in the same notebook
        uid = f"jw-chat-{uuid.uuid4().hex[:12]}"

        # HTML-escape the full chat.html for use as the iframe srcdoc value
        srcdoc_value = _html.escape(chat_html, quote=True)

        bridge_js = f"""<script>
(function() {{
  var iframe = document.getElementById('{uid}');
  if (!iframe) {{ console.warn('[jiuwenswarm] iframe #{uid} not found'); return; }}
  var comm = null;

  // Install __jupyter_send bridge on the iframe window so chat.html can
  // call it when the user submits a message.
  function _bridgeReady(win) {{
    try {{
      win.__jupyter_send = function(jsonStr) {{
        if (comm) {{ comm.send(JSON.parse(jsonStr)); }}
      }};
    }} catch(e) {{
      console.warn('[jiuwenswarm] __jupyter_send install failed', e);
    }}
    // Announce connection to chat.html so it leaves the disconnected state.
    win.postMessage({{
      type: 'connected',
      server_version: '1.0',
      available_modes: ['agent', 'code', 'team', 'code.team']
    }}, '*');
  }}

  // Open the 'jiuwenswarm' comm target registered by comm_handler.py.
  function _openComm() {{
    var kernel = null;
    if (typeof Jupyter !== 'undefined' && Jupyter.notebook && Jupyter.notebook.kernel) {{
      kernel = Jupyter.notebook.kernel;
    }}
    if (!kernel) {{
      console.warn('[jiuwenswarm] %jiuwen_chat: Jupyter kernel API not available. '
        + 'In JupyterLab use the sidebar panel instead.');
      if (iframe.contentWindow) {{
        iframe.contentWindow.postMessage({{
          type: 'chat.error',
          session_id: 'none',
          turn_id: 'setup',
          error: 'Kernel comm not available. In JupyterLab, open the sidebar panel '
               + '(Cmd/Ctrl+Shift+J) for the full chat interface.'
        }}, '*');
      }}
      return;
    }}
    comm = kernel.comm_manager.new_comm('jiuwenswarm', {{}});
    comm.on_msg(function(msg) {{
      if (iframe && iframe.contentWindow) {{
        iframe.contentWindow.postMessage(msg.content.data, '*');
      }}
    }});
    comm.open();
  }}

  // Forward messages from the iframe to the kernel via comm.
  window.addEventListener('message', function(e) {{
    if (!iframe || e.source !== iframe.contentWindow) return;
    if (comm && e.data && e.data.type) {{ comm.send(e.data); }}
  }});

  // Wire iframe load → bridge setup → comm open.
  function _onLoad() {{
    _bridgeReady(iframe.contentWindow);
    _openComm();
  }}

  if (iframe.contentDocument && iframe.contentDocument.readyState === 'complete') {{
    _onLoad();
  }} else {{
    iframe.addEventListener('load', _onLoad);
  }}
}})();
</script>"""

        output_html = (
            f'<div style="width:100%;height:{height}px;border:1px solid #3c3c3c;'
            f'border-radius:6px;overflow:hidden;margin:4px 0;">'
            f'<iframe id="{uid}" srcdoc="{srcdoc_value}"'
            f' style="width:100%;height:100%;border:none;"'
            f' allow="clipboard-read; clipboard-write"></iframe>'
            f"</div>"
            f"{bridge_js}"
        )

        display(HTML(output_html))

    ip.register_magic_function(jiuwen_chat, magic_kind="line", magic_name="jiuwen_chat")

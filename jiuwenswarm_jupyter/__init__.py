"""
jiuwenswarm_jupyter — JiuwenSwarm integration for Jupyter notebooks.

Load with:
    %load_ext jiuwenswarm_jupyter

Or add to ipython_config.py:
    c.InteractiveShellApp.extensions = ["jiuwenswarm_jupyter"]

Public API:
    JupyterSwarm          — programmatic Python client
    get_default_swarm     — per-notebook shared instance
    JiuwenConfig          — per-notebook config dataclass
    get_config            — return or create current notebook config
    read_variable         — inspect any notebook variable
    read_notebook_cell    — read source + output of any cell
    insert_notebook_cell  — insert a new cell into the notebook
    replace_notebook_cell — rewrite an existing cell with a diff dialog
    show_jiuwen_panel     — ipywidgets interactive control panel (requires ipywidgets)

Magics registered on load:
    %%jiuwen / %jiuwen    — send query to agent, stream response
    %jiuwen_config        — view or change per-notebook settings
    %jiuwen_error         — forward last exception to agent for debugging
    %jiuwen_clear         — reset current or named session context
    %jiuwen_export        — export conversation history to a markdown file
    %jiuwen_replay        — continue in a fresh session with recent context
    %jiuwen_pin           — always inject named variables into context
    %jiuwen_unpin         — remove variables from the pinned list
    %jiuwen_panel         — open the ipywidgets control panel
    %jiuwen_chat          — embed the full chat UI (chat.html) in the cell output
"""

from .client import JupyterSwarm
from .config import JiuwenConfig, get_config
from .session import get_default_swarm
from .notebook_tools import read_variable, read_notebook_cell, insert_notebook_cell, replace_notebook_cell
from .widgets import show_jiuwen_panel

__all__ = [
    "JupyterSwarm",
    "JiuwenConfig",
    "get_config",
    "get_default_swarm",
    "read_variable",
    "read_notebook_cell",
    "insert_notebook_cell",
    "replace_notebook_cell",
    "show_jiuwen_panel",
]
__version__ = "0.1.0"


def load_ipython_extension(ip):
    """Called by %load_ext jiuwenswarm_jupyter."""
    from .magic import register_magics
    register_magics(ip)

    from .config import register_config_magic
    register_config_magic(ip)

    try:
        from .widgets import register_panel_magic
        register_panel_magic(ip)
    except Exception:
        pass

    # Register comm target so the JupyterLab sidebar panel can connect.
    # Print a one-line status so users know which mode is active.
    try:
        from .comm_handler import register_comm_target
        if register_comm_target(ip):
            print("[JiuwenSwarm] Sidebar connected — JupyterLab comm active.")
        else:
            print(
                "[JiuwenSwarm] Running without sidebar — cell insertion will use display blocks."
            )
    except Exception:
        print(
            "[JiuwenSwarm] Running without sidebar — cell insertion will use display blocks."
        )

    # Expose default session as _jiuwen and config as _jiuwen_config
    ip.user_ns.setdefault("_jiuwen", get_default_swarm(ip))
    ip.user_ns.setdefault("_jiuwen_config", get_config(ip))


def unload_ipython_extension(ip):
    """Called by %unload_ext jiuwenswarm_jupyter."""
    pass

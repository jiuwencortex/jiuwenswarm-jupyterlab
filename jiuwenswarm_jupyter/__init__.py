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
    read_variable         — inspect any notebook variable (Phase 3)
    read_notebook_cell    — read source + output of any cell (Phase 3)
    insert_notebook_cell  — insert a new cell into the notebook (Phase 3)
    show_jiuwen_panel     — ipywidgets interactive control panel (requires ipywidgets)

Magics registered on load:
    %%jiuwen / %jiuwen    — send query to agent (Phase 1)
    %jiuwen_config        — view or change per-notebook settings
    %jiuwen_error         — forward last exception to agent for debugging
    %jiuwen_panel         — open the ipywidgets control panel
    %jiuwen_save          — save the current conversation to a JSON file
"""

from .client import JupyterSwarm
from .config import JiuwenConfig, get_config
from .session import get_default_swarm
from .notebook_tools import read_variable, read_notebook_cell, insert_notebook_cell
from .widgets import show_jiuwen_panel

__all__ = [
    "JupyterSwarm",
    "JiuwenConfig",
    "get_config",
    "get_default_swarm",
    "read_variable",
    "read_notebook_cell",
    "insert_notebook_cell",
    "show_jiuwen_panel",
]
__version__ = "0.1.0"


def load_ipython_extension(ip):
    """Called by %load_ext jiuwenswarm_jupyter."""
    # Phase 1: %%jiuwen / %jiuwen / %jiuwen_error
    from .magic import register_magics
    register_magics(ip)

    # Per-notebook configuration magic: %jiuwen_config
    from .config import register_config_magic
    register_config_magic(ip)

    # ipywidgets panel: %jiuwen_panel
    try:
        from .widgets import register_panel_magic
        register_panel_magic(ip)
    except Exception:
        pass

    # Phase 2: register comm target so the JupyterLab sidebar panel can connect
    try:
        from .comm_handler import register_comm_target
        register_comm_target(ip)
    except Exception:
        # Not running inside a kernel that supports comm — fine for Phase 1.
        pass

    # Expose default session as _jiuwen and config as _jiuwen_config
    ip.user_ns.setdefault("_jiuwen", get_default_swarm(ip))
    ip.user_ns.setdefault("_jiuwen_config", get_config(ip))


def unload_ipython_extension(ip):
    """Called by %unload_ext jiuwenswarm_jupyter."""
    pass

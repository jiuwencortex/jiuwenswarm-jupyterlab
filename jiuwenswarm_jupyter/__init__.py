"""
jiuwenswarm_jupyter — JiuwenSwarm integration for Jupyter notebooks.

Load with:
    %load_ext jiuwenswarm_jupyter

Or add to ipython_config.py:
    c.InteractiveShellApp.extensions = ["jiuwenswarm_jupyter"]

Public API:
    JupyterSwarm          — programmatic Python client
    get_default_swarm     — per-notebook shared instance
    read_variable         — inspect any notebook variable (Phase 3)
    read_notebook_cell    — read source + output of any cell (Phase 3)
    insert_notebook_cell  — insert a new cell into the notebook (Phase 3)
"""

from .client import JupyterSwarm
from .session import get_default_swarm
from .notebook_tools import read_variable, read_notebook_cell, insert_notebook_cell

__all__ = [
    "JupyterSwarm",
    "get_default_swarm",
    "read_variable",
    "read_notebook_cell",
    "insert_notebook_cell",
]
__version__ = "0.1.0"


def load_ipython_extension(ip):
    """Called by %load_ext jiuwenswarm_jupyter."""
    # Phase 1: cell magic
    from .magic import register_magics
    register_magics(ip)

    # Phase 2: register comm target so the JupyterLab sidebar panel can connect
    try:
        from .comm_handler import register_comm_target
        register_comm_target(ip)
    except Exception:
        # Not running inside a kernel that supports comm — fine for Phase 1.
        pass

    # Expose the default session as _jiuwen in the user namespace
    ip.user_ns.setdefault("_jiuwen", get_default_swarm(ip))


def unload_ipython_extension(ip):
    """Called by %unload_ext jiuwenswarm_jupyter."""
    pass

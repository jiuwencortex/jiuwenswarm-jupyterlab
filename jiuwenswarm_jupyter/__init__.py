"""
jiuwenswarm_jupyter — JiuwenSwarm integration for Jupyter notebooks.

Load with:
    %load_ext jiuwenswarm_jupyter

Or add to ipython_config.py:
    c.InteractiveShellApp.extensions = ["jiuwenswarm_jupyter"]
"""

from .client import JupyterSwarm
from .session import get_default_swarm

__all__ = ["JupyterSwarm", "get_default_swarm"]
__version__ = "0.1.0"


def load_ipython_extension(ip):
    """Called by %load_ext jiuwenswarm_jupyter."""
    from .magic import register_magics
    register_magics(ip)


def unload_ipython_extension(ip):
    """Called by %unload_ext jiuwenswarm_jupyter."""
    pass

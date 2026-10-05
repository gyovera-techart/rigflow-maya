"""RigFlow Toolkit for Autodesk Maya.

Character Technical Art utilities for rig validation, skin audits and animation export.
"""

from .version import __version__


def show():
    """Open the RigFlow UI inside Maya."""
    from .ui import show_window
    return show_window()

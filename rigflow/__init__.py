"""RigFlow Toolkit for Autodesk Maya.

Character Technical Art utilities for rig validation, skin audits and animation export.
"""

__version__ = "0.1.0"


def show():
    """Open the RigFlow UI inside Maya."""
    from .ui import show_window
    return show_window()

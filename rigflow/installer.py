from __future__ import annotations

import os
from typing import Optional

from .version import __version__


def repository_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))


def write_module_file(modules_dir: Optional[str] = None) -> str:
    """Write a Maya .mod file pointing at this RigFlow checkout."""
    import maya.cmds as cmds

    if modules_dir is None:
        modules_dir = os.path.join(cmds.internalVar(userAppDir=True), "modules")
    os.makedirs(modules_dir, exist_ok=True)
    path = os.path.join(modules_dir, "RigFlow.mod")
    root = repository_root().replace("\\", "/")
    content = "+ RigFlow %s %s\nPYTHONPATH +:= .\n" % (__version__, root)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(content)
    return path


def install_shelf_button(label: str = "RigFlow") -> str:
    """Create/update a RigFlow shelf button in the current Maya shelf."""
    import maya.cmds as cmds
    import maya.mel as mel

    shelf_top = mel.eval("$tmp=$gShelfTopLevel")
    current_shelf = cmds.tabLayout(shelf_top, query=True, selectTab=True)
    children = cmds.shelfLayout(current_shelf, query=True, childArray=True) or []
    for child in children:
        try:
            if cmds.shelfButton(child, query=True, label=True) == label:
                cmds.deleteUI(child)
        except Exception:
            pass

    root = repository_root().replace("\\", "/")
    command = (
        "import sys\n"
        "p = r'%s'\n"
        "if p not in sys.path: sys.path.insert(0, p)\n"
        "import rigflow\n"
        "rigflow.show()"
    ) % root.replace("'", "\\'")
    button = cmds.shelfButton(
        parent=current_shelf,
        label=label,
        annotation="Open RigFlow Toolkit v%s" % __version__,
        command=command,
        sourceType="python",
        image1="pythonFamily.png",
    )
    return button

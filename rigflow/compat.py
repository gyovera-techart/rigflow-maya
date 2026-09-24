"""Compatibility helpers for PySide2/PySide6 across Maya releases."""
from __future__ import annotations

import maya.OpenMayaUI as omui

try:
    from PySide6 import QtCore, QtGui, QtWidgets
    from shiboken6 import wrapInstance
    PYSIDE_VERSION = 6
except ImportError:  # Maya versions shipping PySide2
    from PySide2 import QtCore, QtGui, QtWidgets
    from shiboken2 import wrapInstance
    PYSIDE_VERSION = 2


def maya_main_window():
    ptr = omui.MQtUtil.mainWindow()
    if ptr is None:
        return None
    return wrapInstance(int(ptr), QtWidgets.QWidget)


def exec_dialog(dialog):
    """Compatibility wrapper for Qt5/Qt6 dialog execution."""
    if hasattr(dialog, "exec"):
        return dialog.exec()
    return dialog.exec_()

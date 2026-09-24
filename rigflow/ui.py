from __future__ import annotations

import os
from typing import List, Optional

import maya.cmds as cmds

from .compat import QtCore, QtWidgets, maya_main_window
from .config import load_config
from .result import CheckResult, Severity
from .validators import run_scene_validation
from .rig_audit import run_rig_audit, apply_fix
from .clip_exporter import AnimationClip, export_clip
from .report import build_report, save_json, save_txt

WINDOW_OBJECT_NAME = "RigFlowToolkitWindow"


class ResultsTable(QtWidgets.QTableWidget):
    def __init__(self, parent=None):
        super().__init__(0, 4, parent)
        self.setHorizontalHeaderLabels(["Status", "Check", "Message", "Nodes"])
        select_rows = getattr(getattr(QtWidgets.QAbstractItemView, "SelectionBehavior", QtWidgets.QAbstractItemView), "SelectRows")
        no_edit = getattr(getattr(QtWidgets.QAbstractItemView, "EditTrigger", QtWidgets.QAbstractItemView), "NoEditTriggers")
        self.setSelectionBehavior(select_rows)
        self.setEditTriggers(no_edit)
        self.horizontalHeader().setStretchLastSection(True)
        self._results: List[CheckResult] = []
        self.cellDoubleClicked.connect(self.select_problem)

    def set_results(self, results: List[CheckResult]):
        self._results = results
        self.setRowCount(len(results))
        for row, result in enumerate(results):
            status = QtWidgets.QTableWidgetItem(result.severity.label)
            title = QtWidgets.QTableWidgetItem(result.title)
            message = QtWidgets.QTableWidgetItem(result.message)
            nodes = QtWidgets.QTableWidgetItem(", ".join(result.nodes[:4]) + (" …" if len(result.nodes) > 4 else ""))
            self.setItem(row, 0, status)
            self.setItem(row, 1, title)
            self.setItem(row, 2, message)
            self.setItem(row, 3, nodes)
        self.resizeColumnsToContents()

    def current_result(self) -> Optional[CheckResult]:
        row = self.currentRow()
        if 0 <= row < len(self._results):
            return self._results[row]
        return None

    def select_problem(self, *_):
        result = self.current_result()
        if not result or not result.nodes:
            return
        existing = [n for n in result.nodes if cmds.objExists(n)]
        if existing:
            cmds.select(existing, replace=True)


class RigFlowWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=maya_main_window()):
        super().__init__(parent)
        self.setObjectName(WINDOW_OBJECT_NAME)
        self.setWindowTitle("RigFlow Toolkit for Maya")
        self.resize(1040, 680)
        self.config = load_config()
        self.last_results: List[CheckResult] = []
        self.export_results = []
        self._build_ui()

    def _build_ui(self):
        central = QtWidgets.QWidget()
        root_layout = QtWidgets.QVBoxLayout(central)

        header = QtWidgets.QHBoxLayout()
        title = QtWidgets.QLabel("RigFlow Toolkit")
        title.setStyleSheet("font-size: 20px; font-weight: 600;")
        header.addWidget(title)
        header.addStretch()
        report_json = QtWidgets.QPushButton("Save JSON Report")
        report_txt = QtWidgets.QPushButton("Save TXT Report")
        report_json.clicked.connect(lambda: self.save_report("json"))
        report_txt.clicked.connect(lambda: self.save_report("txt"))
        header.addWidget(report_json)
        header.addWidget(report_txt)
        root_layout.addLayout(header)

        self.tabs = QtWidgets.QTabWidget()
        root_layout.addWidget(self.tabs)
        self.tabs.addTab(self._build_validate_tab(), "Validate")
        self.tabs.addTab(self._build_rig_audit_tab(), "Rig Audit")
        self.tabs.addTab(self._build_export_tab(), "Export")
        self.setCentralWidget(central)

    def _result_tab(self, run_callback):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        controls = QtWidgets.QHBoxLayout()
        run_btn = QtWidgets.QPushButton("Run")
        select_btn = QtWidgets.QPushButton("Select Problem")
        fix_btn = QtWidgets.QPushButton("Fix Selected (safe fixes only)")
        controls.addWidget(run_btn)
        controls.addWidget(select_btn)
        controls.addWidget(fix_btn)
        controls.addStretch()
        table = ResultsTable()
        layout.addLayout(controls)
        layout.addWidget(table)
        run_btn.clicked.connect(lambda: run_callback(table))
        select_btn.clicked.connect(table.select_problem)
        fix_btn.clicked.connect(lambda: self.fix_selected(table))
        return widget, table

    def _build_validate_tab(self):
        widget, self.validate_table = self._result_tab(self.run_validation)
        return widget

    def _build_rig_audit_tab(self):
        widget, self.audit_table = self._result_tab(self.run_audit)
        return widget

    def _build_export_tab(self):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QFormLayout(widget)

        root_row = QtWidgets.QHBoxLayout()
        self.root_joint = QtWidgets.QLineEdit()
        pick_root = QtWidgets.QPushButton("Use Selected Joint")
        pick_root.clicked.connect(self.use_selected_joint)
        root_row.addWidget(self.root_joint)
        root_row.addWidget(pick_root)
        layout.addRow("Root joint", root_row)

        self.clip_name = QtWidgets.QLineEdit("idle")
        layout.addRow("Clip name", self.clip_name)

        range_row = QtWidgets.QHBoxLayout()
        self.start = QtWidgets.QDoubleSpinBox()
        self.end = QtWidgets.QDoubleSpinBox()
        for box in (self.start, self.end):
            box.setRange(-100000, 100000)
            box.setDecimals(2)
        self.start.setValue(cmds.playbackOptions(query=True, minTime=True))
        self.end.setValue(cmds.playbackOptions(query=True, maxTime=True))
        range_row.addWidget(QtWidgets.QLabel("Start"))
        range_row.addWidget(self.start)
        range_row.addWidget(QtWidgets.QLabel("End"))
        range_row.addWidget(self.end)
        layout.addRow("Frame range", range_row)

        out_row = QtWidgets.QHBoxLayout()
        self.output_dir = QtWidgets.QLineEdit(cmds.workspace(query=True, rootDirectory=True))
        browse = QtWidgets.QPushButton("Browse")
        browse.clicked.connect(self.browse_output)
        out_row.addWidget(self.output_dir)
        out_row.addWidget(browse)
        layout.addRow("Output folder", out_row)

        self.bake = QtWidgets.QCheckBox("Bake to non-destructive export skeleton copy")
        self.bake.setChecked(True)
        layout.addRow("Bake", self.bake)

        self.export_status = QtWidgets.QPlainTextEdit()
        self.export_status.setReadOnly(True)
        export_btn = QtWidgets.QPushButton("Export FBX Clip")
        export_btn.clicked.connect(self.export_current_clip)
        layout.addRow(export_btn)
        layout.addRow("Result", self.export_status)
        return widget

    def run_validation(self, table: ResultsTable):
        results = run_scene_validation(self.config)
        table.set_results(results)
        self.last_results = results

    def run_audit(self, table: ResultsTable):
        results = run_rig_audit(self.config)
        table.set_results(results)
        self.last_results = results

    def fix_selected(self, table: ResultsTable):
        result = table.current_result()
        if not result:
            self._info("Select a result row first.")
            return
        if not result.fix_id:
            self._info("This result has no automatic fix. RigFlow only exposes explicitly safe fixes.")
            return
        try:
            message = apply_fix(result.fix_id, result.nodes)
            self._info(message)
        except Exception as exc:
            self._error(str(exc))

    def use_selected_joint(self):
        selection = cmds.ls(selection=True, long=True, type="joint") or []
        if not selection:
            self._info("Select a root joint in Maya first.")
            return
        self.root_joint.setText(selection[0])

    def browse_output(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Choose FBX output folder", self.output_dir.text())
        if folder:
            self.output_dir.setText(folder)

    def export_current_clip(self):
        clip = AnimationClip(
            name=self.clip_name.text(),
            start=self.start.value(),
            end=self.end.value(),
            output_dir=self.output_dir.text(),
            bake=self.bake.isChecked(),
        )
        try:
            result = export_clip(self.root_joint.text(), clip, self.config)
            self.export_results.append(result)
            self.export_status.appendPlainText(f"Exported: {result['output']} | success={result['success']}")
        except Exception as exc:
            self.export_status.appendPlainText(f"ERROR: {exc}")
            self._error(str(exc))

    def save_report(self, kind: str):
        report = build_report(self.last_results, self.export_results)
        suffix = ".json" if kind == "json" else ".txt"
        default = os.path.join(cmds.workspace(query=True, rootDirectory=True), "rigflow_report" + suffix)
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save RigFlow report", default, f"*{suffix}")
        if not path:
            return
        if kind == "json":
            save_json(path, report)
        else:
            save_txt(path, report)
        self._info(f"Saved report:\n{path}")

    def _info(self, message: str):
        QtWidgets.QMessageBox.information(self, "RigFlow", message)

    def _error(self, message: str):
        QtWidgets.QMessageBox.critical(self, "RigFlow", message)


def show_window():
    for widget in QtWidgets.QApplication.topLevelWidgets():
        if widget.objectName() == WINDOW_OBJECT_NAME:
            widget.close()
            widget.deleteLater()
    window = RigFlowWindow()
    window.show()
    return window

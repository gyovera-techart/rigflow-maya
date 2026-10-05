from __future__ import annotations

import json
import os
from typing import List, Optional, Tuple

import maya.cmds as cmds

from .compat import QtCore, QtWidgets, maya_main_window
from .config import load_config
from .result import CheckResult
from .registry import build_default_registry
from .rig_audit import apply_fix
from .clip_exporter import AnimationClip, batch_export_clips
from .presets import apply_preset, list_presets, load_preset
from .preflight import evaluate_preflight, BLOCKED, NOT_RUN
from .report import build_session_report, save_json, save_txt
from .safe_fix import execute_safe_fix
from .session import RigFlowSession, summarize_results
from .version import __version__

WINDOW_OBJECT_NAME = "RigFlowToolkitWindow"


def _enum(root, group_name: str, value_name: str):
    group = getattr(root, group_name, root)
    return getattr(group, value_name)


class ResultsTable(QtWidgets.QTableWidget):
    def __init__(self, parent=None):
        super().__init__(0, 4, parent)
        self.setHorizontalHeaderLabels(["Status", "Check", "Message", "Nodes"])
        self.setSelectionBehavior(_enum(QtWidgets.QAbstractItemView, "SelectionBehavior", "SelectRows"))
        self.setEditTriggers(_enum(QtWidgets.QAbstractItemView, "EditTrigger", "NoEditTriggers"))
        self.horizontalHeader().setStretchLastSection(True)
        self._results: List[CheckResult] = []
        self.cellDoubleClicked.connect(self.select_problem)

    def set_results(self, results: List[CheckResult]):
        self._results = list(results)
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
        self.setWindowTitle("RigFlow Toolkit for Maya v%s" % __version__)
        self.resize(1180, 760)
        self.config = load_config()
        self.registry = build_default_registry()
        self.session = RigFlowSession(self.config)
        # Backward-compatible convenience attributes from v0.1.
        self.last_results: List[CheckResult] = []
        self.export_results = self.session.exports
        self._build_ui()
        self._refresh_preflight()

    def _build_ui(self):
        central = QtWidgets.QWidget()
        root_layout = QtWidgets.QVBoxLayout(central)

        header = QtWidgets.QHBoxLayout()
        title = QtWidgets.QLabel("RigFlow Toolkit")
        title.setStyleSheet("font-size: 20px; font-weight: 600;")
        version = QtWidgets.QLabel("v%s" % __version__)
        version.setStyleSheet("font-weight: 600;")
        header.addWidget(title)
        header.addWidget(version)
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
        self.tabs.addTab(self._build_preflight_tab(), "Preflight")
        self.tabs.addTab(self._build_validate_tab(), "Validate")
        self.tabs.addTab(self._build_rig_audit_tab(), "Rig Audit")
        self.tabs.addTab(self._build_export_tab(), "Export")
        self.setCentralWidget(central)

    def _build_preflight_tab(self):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)

        top = QtWidgets.QHBoxLayout()
        run_all = QtWidgets.QPushButton("Run All")
        run_all.setMinimumHeight(38)
        run_all.clicked.connect(self.run_all)
        top.addWidget(run_all)
        top.addStretch()
        layout.addLayout(top)

        summary = QtWidgets.QGroupBox("Session Preflight")
        form = QtWidgets.QFormLayout(summary)
        self.preflight_status = QtWidgets.QLabel(NOT_RUN)
        self.preflight_status.setStyleSheet("font-size: 18px; font-weight: 700;")
        self.preflight_pass = QtWidgets.QLabel("0")
        self.preflight_warn = QtWidgets.QLabel("0")
        self.preflight_error = QtWidgets.QLabel("0")
        self.preflight_blocking = QtWidgets.QLabel("0")
        form.addRow("Status", self.preflight_status)
        form.addRow("PASS", self.preflight_pass)
        form.addRow("WARN", self.preflight_warn)
        form.addRow("ERROR", self.preflight_error)
        form.addRow("Blocking errors", self.preflight_blocking)
        layout.addWidget(summary)

        note = QtWidgets.QLabel(
            "Run All executes Scene Validation + Rig Audit. ERROR results block export; WARN results keep the asset exportable with warnings."
        )
        note.setWordWrap(True)
        layout.addWidget(note)
        layout.addStretch()
        return widget

    def _result_tab(self, run_callback, fix_callback):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        controls = QtWidgets.QHBoxLayout()
        run_btn = QtWidgets.QPushButton("Run")
        select_btn = QtWidgets.QPushButton("Select Problem")
        fix_btn = QtWidgets.QPushButton("Fix Selected (safe fixes only)")
        copy_btn = QtWidgets.QPushButton("Copy Details")
        controls.addWidget(run_btn)
        controls.addWidget(select_btn)
        controls.addWidget(fix_btn)
        controls.addWidget(copy_btn)
        controls.addStretch()
        table = ResultsTable()
        details = QtWidgets.QPlainTextEdit()
        details.setReadOnly(True)
        details.setMaximumHeight(170)
        details.setPlaceholderText("Select a result to inspect full nodes and metadata.")
        layout.addLayout(controls)
        layout.addWidget(table)
        layout.addWidget(details)
        run_btn.clicked.connect(lambda: run_callback(table))
        select_btn.clicked.connect(table.select_problem)
        fix_btn.clicked.connect(lambda: fix_callback(table))
        table.itemSelectionChanged.connect(lambda: self._show_result_details(table, details))
        copy_btn.clicked.connect(lambda: self._copy_details(details))
        return widget, table

    def _build_validate_tab(self):
        widget, self.validate_table = self._result_tab(self.run_validation, self.fix_selected)
        return widget

    def _build_rig_audit_tab(self):
        widget, self.audit_table = self._result_tab(self.run_audit, self.fix_selected)
        return widget

    def _build_export_tab(self):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)

        settings = QtWidgets.QGroupBox("Export Settings")
        form = QtWidgets.QFormLayout(settings)

        root_row = QtWidgets.QHBoxLayout()
        self.root_joint = QtWidgets.QLineEdit()
        pick_root = QtWidgets.QPushButton("Use Selected Joint")
        pick_root.clicked.connect(self.use_selected_joint)
        root_row.addWidget(self.root_joint)
        root_row.addWidget(pick_root)
        form.addRow("Root joint", root_row)

        out_row = QtWidgets.QHBoxLayout()
        self.output_dir = QtWidgets.QLineEdit(cmds.workspace(query=True, rootDirectory=True))
        browse = QtWidgets.QPushButton("Browse")
        browse.clicked.connect(self.browse_output)
        out_row.addWidget(self.output_dir)
        out_row.addWidget(browse)
        form.addRow("Output folder", out_row)

        self.preset_combo = QtWidgets.QComboBox()
        preset_names = list_presets()
        for preset_name in preset_names:
            try:
                preset = load_preset(preset_name)
                self.preset_combo.addItem(preset.get("label", preset_name), preset.get("id", preset_name))
            except Exception:
                self.preset_combo.addItem(preset_name, preset_name)
        form.addRow("Target preset", self.preset_combo)

        self.bake = QtWidgets.QCheckBox("Bake to non-destructive export skeleton copy")
        self.bake.setChecked(True)
        form.addRow("Bake", self.bake)
        layout.addWidget(settings)

        clip_box = QtWidgets.QGroupBox("Clip Queue")
        clip_layout = QtWidgets.QVBoxLayout(clip_box)
        editor = QtWidgets.QHBoxLayout()
        self.clip_name = QtWidgets.QLineEdit("idle")
        self.start = QtWidgets.QDoubleSpinBox()
        self.end = QtWidgets.QDoubleSpinBox()
        for box in (self.start, self.end):
            box.setRange(-100000, 100000)
            box.setDecimals(2)
        self.start.setValue(cmds.playbackOptions(query=True, minTime=True))
        self.end.setValue(cmds.playbackOptions(query=True, maxTime=True))
        add_btn = QtWidgets.QPushButton("Add Clip")
        add_btn.clicked.connect(self.add_clip)
        editor.addWidget(QtWidgets.QLabel("Name"))
        editor.addWidget(self.clip_name, 2)
        editor.addWidget(QtWidgets.QLabel("Start"))
        editor.addWidget(self.start)
        editor.addWidget(QtWidgets.QLabel("End"))
        editor.addWidget(self.end)
        editor.addWidget(add_btn)
        clip_layout.addLayout(editor)

        self.clip_table = QtWidgets.QTableWidget(0, 5)
        self.clip_table.setHorizontalHeaderLabels(["Enabled", "Name", "Start", "End", "Status"])
        self.clip_table.setSelectionBehavior(_enum(QtWidgets.QAbstractItemView, "SelectionBehavior", "SelectRows"))
        self.clip_table.horizontalHeader().setStretchLastSection(True)
        clip_layout.addWidget(self.clip_table)

        queue_buttons = QtWidgets.QHBoxLayout()
        remove_btn = QtWidgets.QPushButton("Remove Selected")
        export_selected_btn = QtWidgets.QPushButton("Export Selected")
        export_enabled_btn = QtWidgets.QPushButton("Export Enabled")
        remove_btn.clicked.connect(self.remove_selected_clip)
        export_selected_btn.clicked.connect(self.export_selected_clip)
        export_enabled_btn.clicked.connect(self.export_enabled_clips)
        queue_buttons.addWidget(remove_btn)
        queue_buttons.addStretch()
        queue_buttons.addWidget(export_selected_btn)
        queue_buttons.addWidget(export_enabled_btn)
        clip_layout.addLayout(queue_buttons)
        layout.addWidget(clip_box)

        status_box = QtWidgets.QGroupBox("Export Status / Session Log")
        status_layout = QtWidgets.QVBoxLayout(status_box)
        self.export_current_status = QtWidgets.QLabel("Idle")
        self.export_current_status.setStyleSheet("font-weight: 600;")
        self.export_status = QtWidgets.QPlainTextEdit()
        self.export_status.setReadOnly(True)
        self.export_status.setMaximumHeight(150)
        status_layout.addWidget(self.export_current_status)
        status_layout.addWidget(self.export_status)
        layout.addWidget(status_box)
        return widget

    def _show_result_details(self, table: ResultsTable, details: QtWidgets.QPlainTextEdit):
        result = table.current_result()
        details.setPlainText(json.dumps(result.to_dict(), indent=2, ensure_ascii=False) if result else "")

    def _copy_details(self, details: QtWidgets.QPlainTextEdit):
        QtWidgets.QApplication.clipboard().setText(details.toPlainText())

    def run_validation(self, table: Optional[ResultsTable] = None):
        results = self.registry.run_category("scene_validation", self.config)
        self.session.set_scene_validation(results)
        self.last_results = list(results)
        (table or self.validate_table).set_results(results)
        self._refresh_preflight()
        return results

    def run_audit(self, table: Optional[ResultsTable] = None):
        results = self.registry.run_category("rig_audit", self.config)
        self.session.set_rig_audit(results)
        self.last_results = list(results)
        (table or self.audit_table).set_results(results)
        self._refresh_preflight()
        return results

    def run_all(self, checked=False, silent: bool = False):
        scene_results = self.registry.run_category("scene_validation", self.config)
        audit_results = self.registry.run_category("rig_audit", self.config)
        self.session.set_scene_validation(scene_results)
        self.session.set_rig_audit(audit_results)
        self.last_results = list(audit_results)
        self.validate_table.set_results(scene_results)
        self.audit_table.set_results(audit_results)
        self._refresh_preflight(force=True)
        if not silent:
            self.tabs.setCurrentIndex(0)
        return self.session.preflight

    def _refresh_preflight(self, force: bool = False):
        if force or (self.session.scene_validation and self.session.rig_audit):
            data = evaluate_preflight(self.session.scene_validation, self.session.rig_audit)
        else:
            combined = self.session.all_results()
            summary = summarize_results(combined)
            data = {
                "status": NOT_RUN,
                "ready_for_export": False,
                "blocking_errors": summary.get("error", 0),
                "warnings": summary.get("warn", 0),
                "summary": summary,
                "blocking_codes": [],
            }
        self.session.set_preflight(data)
        self.preflight_status.setText(data.get("status", NOT_RUN))
        summary = data.get("summary", {})
        self.preflight_pass.setText(str(summary.get("pass", 0)))
        self.preflight_warn.setText(str(summary.get("warn", 0)))
        self.preflight_error.setText(str(summary.get("error", 0)))
        self.preflight_blocking.setText(str(data.get("blocking_errors", 0)))

    def fix_selected(self, table: ResultsTable):
        result = table.current_result()
        if not result:
            self._info("Select a result row first.")
            return
        if not result.fix_id:
            self._info("This result has no automatic fix. RigFlow only exposes explicitly safe fixes.")
            return
        if not self._confirm(
            "Apply safe fix '%s' and immediately revalidate?\n\nThe change will be grouped as one Maya Undo step." % result.fix_id
        ):
            return

        if table is self.audit_table:
            category = "rig_audit"
        else:
            category = "scene_validation"

        outcome = execute_safe_fix(
            result.fix_id,
            result.code,
            result.nodes,
            apply_fix,
            lambda: self.registry.run_category(category, self.config),
        )
        self.session.add_fix(outcome.to_dict())

        if category == "rig_audit":
            refreshed = self.registry.run_category(category, self.config)
            self.session.set_rig_audit(refreshed)
            self.audit_table.set_results(refreshed)
        else:
            refreshed = self.registry.run_category(category, self.config)
            self.session.set_scene_validation(refreshed)
            self.validate_table.set_results(refreshed)
        self._refresh_preflight()

        if outcome.success:
            self._info(outcome.message + "\nRevalidation passed. The change is grouped as one Maya Undo step.")
        else:
            self._error(outcome.message)

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

    def add_clip(self):
        try:
            clip = AnimationClip(
                self.clip_name.text(), self.start.value(), self.end.value(), self.output_dir.text(), self.bake.isChecked()
            ).validated()
        except Exception as exc:
            self._error(str(exc))
            return
        row = self.clip_table.rowCount()
        self.clip_table.insertRow(row)
        enabled = QtWidgets.QTableWidgetItem("")
        enabled.setCheckState(_enum(QtCore.Qt, "CheckState", "Checked"))
        self.clip_table.setItem(row, 0, enabled)
        self.clip_table.setItem(row, 1, QtWidgets.QTableWidgetItem(clip.name))
        self.clip_table.setItem(row, 2, QtWidgets.QTableWidgetItem(str(clip.start)))
        self.clip_table.setItem(row, 3, QtWidgets.QTableWidgetItem(str(clip.end)))
        self.clip_table.setItem(row, 4, QtWidgets.QTableWidgetItem("READY"))
        self.clip_table.resizeColumnsToContents()

    def remove_selected_clip(self):
        rows = sorted({index.row() for index in self.clip_table.selectedIndexes()}, reverse=True)
        for row in rows:
            self.clip_table.removeRow(row)

    def _row_enabled(self, row: int) -> bool:
        item = self.clip_table.item(row, 0)
        return bool(item and item.checkState() == _enum(QtCore.Qt, "CheckState", "Checked"))

    def _clip_from_row(self, row: int) -> AnimationClip:
        return AnimationClip(
            name=self.clip_table.item(row, 1).text(),
            start=float(self.clip_table.item(row, 2).text()),
            end=float(self.clip_table.item(row, 3).text()),
            output_dir=self.output_dir.text(),
            bake=self.bake.isChecked(),
        ).validated()

    def _active_export_config(self):
        preset_id = self.preset_combo.currentData() or self.preset_combo.currentText()
        preset = load_preset(str(preset_id))
        return apply_preset(self.config, preset)

    def export_selected_clip(self):
        row = self.clip_table.currentRow()
        if row < 0:
            self._info("Select a clip row first.")
            return
        self._export_rows([row])

    def export_enabled_clips(self):
        rows = [row for row in range(self.clip_table.rowCount()) if self._row_enabled(row)]
        if not rows:
            self._info("No enabled clips are in the queue.")
            return
        self._export_rows(rows)

    def _export_rows(self, rows: List[int]):
        # Always refresh preflight immediately before export so stale validation
        # state cannot silently permit a blocked scene.
        preflight = self.run_all(silent=True)
        if preflight.get("status") == BLOCKED:
            self._error("Export blocked by Preflight. Resolve ERROR checks before exporting.")
            self.tabs.setCurrentIndex(0)
            return

        root = self.root_joint.text().strip()
        if not root:
            self._error("A root joint is required.")
            return
        try:
            config = self._active_export_config()
            pairs: List[Tuple[int, AnimationClip]] = [(row, self._clip_from_row(row)) for row in rows]
        except Exception as exc:
            self._error(str(exc))
            return

        for row, _ in pairs:
            self.clip_table.item(row, 4).setText("RUNNING")
        self.export_current_status.setText("Exporting %d clip(s)…" % len(pairs))
        QtWidgets.QApplication.processEvents()

        results = batch_export_clips(root, [clip for _, clip in pairs], config)
        success_count = 0
        for (row, _), result in zip(pairs, results):
            self.clip_table.item(row, 4).setText(result.get("status", "FAILED"))
            self.session.add_export(result)
            if result.get("success"):
                success_count += 1
                self.export_status.appendPlainText("SUCCESS: %s" % result.get("output"))
            else:
                self.export_status.appendPlainText("FAILED: %s" % result.get("error", result.get("output")))

        self.export_current_status.setText("Completed: %d/%d successful" % (success_count, len(results)))

    def save_report(self, kind: str):
        report = build_session_report(self.session)
        suffix = ".json" if kind == "json" else ".txt"
        default = os.path.join(cmds.workspace(query=True, rootDirectory=True), "rigflow_report_v0.2" + suffix)
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save RigFlow report", default, f"*{suffix}")
        if not path:
            return
        if kind == "json":
            save_json(path, report)
        else:
            save_txt(path, report)
        self._info("Saved report:\n%s" % path)

    def _confirm(self, message: str) -> bool:
        yes = _enum(QtWidgets.QMessageBox, "StandardButton", "Yes")
        no = _enum(QtWidgets.QMessageBox, "StandardButton", "No")
        answer = QtWidgets.QMessageBox.question(self, "RigFlow Safe Fix", message, yes | no, no)
        return answer == yes

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

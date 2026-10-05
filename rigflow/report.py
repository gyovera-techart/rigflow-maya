from __future__ import annotations

import json
import os
import platform
from copy import deepcopy
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional

import maya.cmds as cmds

from .result import CheckResult
from .session import RigFlowSession, summarize_results
from .version import __version__


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _environment() -> Dict:
    try:
        api_version = cmds.about(apiVersion=True)
    except Exception:
        api_version = None
    try:
        os_name = cmds.about(operatingSystem=True)
    except Exception:
        os_name = platform.platform()
    try:
        fbx_loaded = bool(cmds.pluginInfo("fbxmaya", query=True, loaded=True))
    except Exception:
        fbx_loaded = False
    try:
        fbx_version = cmds.pluginInfo("fbxmaya", query=True, version=True) if fbx_loaded else None
    except Exception:
        fbx_version = None
    return {
        "maya_version": cmds.about(version=True),
        "maya_api_version": api_version,
        "os": os_name,
        "python": platform.python_version(),
        "fbx_plugin_loaded": fbx_loaded,
        "fbx_plugin_version": fbx_version,
    }


def build_session_report(session: RigFlowSession) -> Dict:
    scene = cmds.file(query=True, sceneName=True) or "<untitled>"
    payload = session.to_dict()
    return {
        "tool": {
            "name": "RigFlow Toolkit for Maya",
            "version": __version__,
        },
        "environment": _environment(),
        "scene": {
            "path": scene,
            "name": os.path.basename(scene) if scene != "<untitled>" else scene,
        },
        "session": {
            "started_at": payload["started_at"],
            "updated_at": payload["updated_at"],
        },
        "scene_validation": payload["scene_validation"],
        "rig_audit": payload["rig_audit"],
        "safe_fixes": payload["safe_fixes"],
        "exports": payload["exports"],
        "preflight": payload["preflight"],
        "config_snapshot": payload["config_snapshot"],
    }


def build_report(results: Iterable[CheckResult], export_results: Optional[List[Dict]] = None) -> Dict:
    """Backward-compatible v0.1-style report builder for external scripts."""
    scene = cmds.file(query=True, sceneName=True) or "<untitled>"
    items = list(results)
    return {
        "tool": "RigFlow Toolkit for Maya",
        "tool_version": __version__,
        "timestamp_utc": _utc_now(),
        "maya_version": cmds.about(version=True),
        "scene": scene,
        "summary": summarize_results(items),
        "checks": [r.to_dict() for r in items],
        "exports": export_results or [],
    }


def save_json(path: str, report: Dict) -> str:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    return path


def _txt_lines_v2(report: Dict) -> List[str]:
    tool = report.get("tool", {})
    env = report.get("environment", {})
    scene = report.get("scene", {})
    session = report.get("session", {})
    preflight = report.get("preflight", {})
    lines = [
        "%s v%s" % (tool.get("name", "RigFlow Toolkit for Maya"), tool.get("version", "?")),
        "Session start: %s" % session.get("started_at", ""),
        "Session update: %s" % session.get("updated_at", ""),
        "Maya: %s | API: %s" % (env.get("maya_version", ""), env.get("maya_api_version", "")),
        "OS: %s" % env.get("os", ""),
        "Scene: %s" % scene.get("path", ""),
        "Preflight: %s | blocking=%s | warnings=%s" % (
            preflight.get("status", "NOT_RUN"),
            preflight.get("blocking_errors", 0),
            preflight.get("warnings", 0),
        ),
        "",
    ]
    for section_key, heading in (("scene_validation", "SCENE VALIDATION"), ("rig_audit", "RIG AUDIT")):
        section = report.get(section_key, {})
        lines.extend([heading, "-" * len(heading)])
        for item in section.get("checks", []):
            lines.append("[%s] %s: %s" % (item.get("severity"), item.get("title"), item.get("message")))
            if item.get("nodes"):
                lines.append("  Nodes: " + ", ".join(item["nodes"]))
        lines.append("")

    lines.extend(["SAFE FIXES", "----------"])
    for item in report.get("safe_fixes", []):
        lines.append("[%s] %s: %s" % (
            "OK" if item.get("success") else "FAIL",
            item.get("fix_id", ""),
            item.get("message", ""),
        ))
    lines.extend(["", "EXPORTS", "-------"])
    for item in report.get("exports", []):
        clip = item.get("clip", {})
        lines.append("[%s] %s -> %s" % (
            item.get("status", "SUCCESS" if item.get("success") else "FAILED"),
            clip.get("name", "<clip>"),
            item.get("output") or item.get("error", ""),
        ))
    return lines


def save_txt(path: str, report: Dict) -> str:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    if isinstance(report.get("tool"), dict):
        lines = _txt_lines_v2(report)
    else:
        lines = [
            report.get("tool", "RigFlow Toolkit for Maya"),
            f"Timestamp: {report.get('timestamp_utc', '')}",
            f"Maya: {report.get('maya_version', '')}",
            f"Scene: {report.get('scene', '')}",
            "",
            "CHECKS",
            "------",
        ]
        for item in report.get("checks", []):
            lines.append(f"[{item['severity']}] {item['title']}: {item['message']}")
            if item.get("nodes"):
                lines.append("  Nodes: " + ", ".join(item["nodes"]))
        if report.get("exports"):
            lines.extend(["", "EXPORTS", "-------"])
            for item in report["exports"]:
                lines.append(f"[{'OK' if item.get('success') else 'FAIL'}] {item.get('output')}")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines))
    return path

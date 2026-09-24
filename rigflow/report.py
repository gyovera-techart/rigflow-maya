from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional

import maya.cmds as cmds

from .result import CheckResult


def build_report(results: Iterable[CheckResult], export_results: Optional[List[Dict]] = None) -> Dict:
    scene = cmds.file(query=True, sceneName=True) or "<untitled>"
    return {
        "tool": "RigFlow Toolkit for Maya",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "maya_version": cmds.about(version=True),
        "scene": scene,
        "checks": [r.to_dict() for r in results],
        "exports": export_results or [],
    }


def save_json(path: str, report: Dict) -> str:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    return path


def save_txt(path: str, report: Dict) -> str:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    lines = [
        report["tool"],
        f"Timestamp: {report['timestamp_utc']}",
        f"Maya: {report['maya_version']}",
        f"Scene: {report['scene']}",
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
            lines.append(f"[{ 'OK' if item.get('success') else 'FAIL' }] {item.get('output')}")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines))
    return path

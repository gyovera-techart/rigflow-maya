from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Callable, Dict, List

import maya.cmds as cmds

from .result import CheckResult, Severity


@dataclass
class FixOutcome:
    fix_id: str
    result_code: str
    success: bool
    rolled_back: bool
    message: str

    def to_dict(self) -> Dict:
        return asdict(self)


def execute_safe_fix(
    fix_id: str,
    result_code: str,
    nodes: List[str],
    apply_callable: Callable[[str, List[str]], str],
    revalidate_callable: Callable[[], List[CheckResult]],
) -> FixOutcome:
    """Execute one approved fix as a single undo chunk, then revalidate.

    If the target check remains ERROR or execution raises, the complete chunk is
    undone to avoid leaving the scene partially modified.
    """
    chunk_open = False
    try:
        cmds.undoInfo(openChunk=True, chunkName="RigFlow Safe Fix: %s" % fix_id)
        chunk_open = True
        message = apply_callable(fix_id, nodes)
        cmds.undoInfo(closeChunk=True)
        chunk_open = False

        rerun = revalidate_callable()
        target = next((item for item in rerun if item.code == result_code), None)
        if target is None or target.severity == Severity.ERROR:
            cmds.undo()
            return FixOutcome(
                fix_id, result_code, False, True,
                "Fix was rolled back because revalidation did not clear the target error.",
            )
        return FixOutcome(fix_id, result_code, True, False, message)
    except Exception as exc:
        if chunk_open:
            try:
                cmds.undoInfo(closeChunk=True)
            except Exception:
                pass
        try:
            cmds.undo()
            rolled_back = True
        except Exception:
            rolled_back = False
        return FixOutcome(
            fix_id, result_code, False, rolled_back,
            "Safe Fix failed: %s" % exc,
        )

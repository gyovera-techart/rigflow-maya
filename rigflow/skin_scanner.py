from __future__ import annotations

from typing import Dict, List


def scan_skin_weights(mesh: str, skin: str, limit: int) -> Dict:
    """Read skin weights in bulk with Maya API 2.0.

    The caller may fall back to cmds.skinPercent if this API path is unavailable
    for a particular scene/geometry combination.
    """
    import maya.api.OpenMaya as om
    import maya.api.OpenMayaAnim as oma

    sel = om.MSelectionList()
    sel.add(mesh)
    dag = sel.getDagPath(0)
    if dag.node().hasFn(om.MFn.kTransform):
        dag.extendToShape()

    mesh_fn = om.MFnMesh(dag)
    count = min(int(mesh_fn.numVertices), int(limit))
    indices = list(range(count))

    comp_fn = om.MFnSingleIndexedComponent()
    component = comp_fn.create(om.MFn.kMeshVertComponent)
    comp_fn.addElements(indices)

    skin_sel = om.MSelectionList()
    skin_sel.add(skin)
    skin_obj = skin_sel.getDependNode(0)
    skin_fn = oma.MFnSkinCluster(skin_obj)
    weights, influence_count = skin_fn.getWeights(dag, component)

    rows: List[List[float]] = []
    influence_count = int(influence_count)
    for vertex_index in range(count):
        offset = vertex_index * influence_count
        rows.append([float(weights[offset + i]) for i in range(influence_count)])
    return {
        "weights": rows,
        "vertex_count": count,
        "influence_count": influence_count,
        "backend": "OpenMayaAnim.MFnSkinCluster",
    }

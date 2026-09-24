"""Create a tiny Maya scene with intentional RigFlow validation issues.

Run inside Maya Script Editor (Python) after adding the repo root to sys.path.
The scene intentionally contains:
1) one badly named joint,
2) one non-unit joint scale,
3) one unskinned mesh.
"""
import maya.cmds as cmds


def build():
    cmds.file(new=True, force=True)

    cmds.select(clear=True)
    root = cmds.joint(name="root_demo", position=(0, 0, 0))
    spine = cmds.joint(name="jnt_spine", position=(0, 5, 0))
    bad = cmds.joint(name="Bad Joint Name", position=(0, 10, 0))
    cmds.setAttr(spine + ".scaleX", 1.15)

    skinned = cmds.polyCylinder(name="body_geo", height=10, radius=1.5, subdivisionsY=8)[0]
    cmds.skinCluster([root, spine, bad], skinned, toSelectedBones=True, maximumInfluences=4, normalizeWeights=1)

    cmds.polyCube(name="prop_unskinned_geo", width=2, height=2, depth=2)
    cmds.move(4, 1, 0)

    cmds.select(root, replace=True)
    print("RigFlow demo scene created with intentional issues.")


build()

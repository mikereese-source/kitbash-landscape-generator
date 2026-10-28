# SPDX-License-Identifier: GPL-3.0-or-later
"""Cliff and cave features (M5): the local volume patch (D91).

Only the grid faces under a feature are touched. They are closed into a solid block, the feature's
cutter (a closed mesh built from SDF shapes) is subtracted from that block with the Manifold boolean, and
the block's walls and floor are thrown away again. The rim of the piece never moves, so it welds back
onto the rest of the grid exactly: the landscape stays one watertight surface (D91, bake as one mesh).
"""

import bpy

CUT_GROUP = "KB Landscape Cut"
CUT_VERSION = 1


def cut_group():
    """Geometry, Cutter (closed mesh), Margin (m) -> the landscape with the cutter carved out.
    Faces left from the cutter are marked lg_cave (face domain)."""
    ng = bpy.data.node_groups.get(CUT_GROUP)
    if ng is not None and ng.get("kb_version") == CUT_VERSION:
        return ng
    if ng is None:
        ng = bpy.data.node_groups.new(CUT_GROUP, 'GeometryNodeTree')
    ng.interface.clear()
    ng.nodes.clear()
    ng.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket("Cutter", in_out='INPUT', socket_type='NodeSocketGeometry')
    s = ng.interface.new_socket("Margin", in_out='INPUT', socket_type='NodeSocketFloat')
    s.default_value = 2.0
    N, L = ng.nodes, ng.links
    gin, gout = N.new('NodeGroupInput'), N.new('NodeGroupOutput')

    def node(kind, **inputs):
        n = N.new(kind)
        for k, v in inputs.items():
            if isinstance(v, bpy.types.NodeSocket):
                L.new(v, n.inputs[k])
            else:
                n.inputs[k].default_value = v
        return n

    def math(op, a, b=None):
        n = N.new('ShaderNodeMath')
        n.operation = op
        for sock, v in zip(n.inputs, (a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                sock.default_value = v
            else:
                L.new(v, sock)
        return n.outputs[0]

    def store(geo, name, value, domain='FACE'):
        n = N.new('GeometryNodeStoreNamedAttribute')
        n.data_type = 'BOOLEAN'
        n.domain = domain
        n.inputs["Name"].default_value = name
        L.new(geo, n.inputs["Geometry"])
        if isinstance(value, bool):
            n.inputs["Value"].default_value = value
        else:
            L.new(value, n.inputs["Value"])
        return n.outputs[0]

    def named(name):
        n = N.new('GeometryNodeInputNamedAttribute')
        n.data_type = 'BOOLEAN'
        n.inputs["Name"].default_value = name
        return n.outputs["Attribute"]

    # The piece: faces whose centre lies over the cutter's footprint plus the margin.
    bb = node('GeometryNodeBoundBox', Geometry=gin.outputs["Cutter"])
    pos = N.new('ShaderNodeSeparateXYZ')
    L.new(N.new('GeometryNodeInputPosition').outputs[0], pos.inputs[0])
    lo, hi = N.new('ShaderNodeSeparateXYZ'), N.new('ShaderNodeSeparateXYZ')
    L.new(bb.outputs["Min"], lo.inputs[0])
    L.new(bb.outputs["Max"], hi.inputs[0])
    m = gin.outputs["Margin"]
    inside = math('MULTIPLY',
                  math('MULTIPLY', math('GREATER_THAN', pos.outputs["X"], math('SUBTRACT', lo.outputs["X"], m)),
                       math('LESS_THAN', pos.outputs["X"], math('ADD', hi.outputs["X"], m))),
                  math('MULTIPLY', math('GREATER_THAN', pos.outputs["Y"], math('SUBTRACT', lo.outputs["Y"], m)),
                       math('LESS_THAN', pos.outputs["Y"], math('ADD', hi.outputs["Y"], m))))
    sep = N.new('GeometryNodeSeparateGeometry')
    sep.domain = 'FACE'
    L.new(gin.outputs["Geometry"], sep.inputs["Geometry"])
    L.new(inside, sep.inputs["Selection"])
    piece = store(sep.outputs["Selection"], "lg_top", True)

    # Close the piece into a block: extrude it down, flatten the moved copy below the cutter, flip that
    # shell (extruding down turns it inside out), and weld it to the untouched top.
    p_stats = N.new('GeometryNodeAttributeStatistic')
    p_stats.data_type = 'FLOAT'
    p_stats.domain = 'POINT'
    L.new(piece, p_stats.inputs["Geometry"])
    L.new(pos.outputs["Z"], p_stats.inputs["Attribute"])
    floor_z = math('SUBTRACT', math('MINIMUM', p_stats.outputs["Min"], lo.outputs["Z"]), math('ADD', m, 1.0))
    ext = N.new('GeometryNodeExtrudeMesh')
    ext.mode = 'FACES'
    L.new(piece, ext.inputs["Mesh"])
    ext.inputs["Offset"].default_value = (0.0, 0.0, -1.0)
    ext.inputs["Individual"].default_value = False
    flat = N.new('ShaderNodeCombineXYZ')
    L.new(pos.outputs["X"], flat.inputs["X"])
    L.new(pos.outputs["Y"], flat.inputs["Y"])
    L.new(floor_z, flat.inputs["Z"])
    drop = node('GeometryNodeSetPosition', Geometry=ext.outputs["Mesh"], Selection=ext.outputs["Top"], Position=flat.outputs[0])
    shell = store(drop.outputs[0], "lg_top", False)
    flip = node('GeometryNodeFlipFaces', Mesh=shell)
    join = N.new('GeometryNodeJoinGeometry')
    L.new(flip.outputs[0], join.inputs[0])
    L.new(piece, join.inputs[0])
    block = node('GeometryNodeMergeByDistance', Geometry=join.outputs[0], Distance=1e-4)

    cutter = store(gin.outputs["Cutter"], "lg_cave", True)
    boolean = N.new('GeometryNodeMeshBoolean')
    boolean.operation = 'DIFFERENCE'
    boolean.solver = 'MANIFOLD'
    L.new(block.outputs[0], boolean.inputs["Mesh 1"])
    L.new(cutter, boolean.inputs["Mesh 2"])
    # Keep the top and the carved faces; the block's walls and floor go.
    keep = math('MAXIMUM', named("lg_top"), named("lg_cave"))
    trim = N.new('GeometryNodeDeleteGeometry')
    trim.domain = 'FACE'
    L.new(boolean.outputs["Mesh"], trim.inputs["Geometry"])
    L.new(math('LESS_THAN', keep, 0.5), trim.inputs["Selection"])

    back = N.new('GeometryNodeJoinGeometry')
    L.new(trim.outputs[0], back.inputs[0])
    L.new(sep.outputs["Inverted"], back.inputs[0])
    # Weld only the open rim (boundary points), not millions of grid points.
    rim = math('LESS_THAN', N.new('GeometryNodeInputMeshVertexNeighbors').outputs["Face Count"], 4.0)
    weld = node('GeometryNodeMergeByDistance', Geometry=back.outputs[0], Selection=rim, Distance=1e-3)
    out = N.new('GeometryNodeSwitch')  # no cutter: the landscape untouched
    out.input_type = 'GEOMETRY'
    has = node('GeometryNodeAttributeDomainSize', Geometry=gin.outputs["Cutter"])
    L.new(math('GREATER_THAN', has.outputs["Face Count"], 0.5), out.inputs["Switch"])
    L.new(gin.outputs["Geometry"], out.inputs["False"])
    L.new(weld.outputs[0], out.inputs["True"])
    L.new(out.outputs[0], gout.inputs["Geometry"])
    ng["kb_version"] = CUT_VERSION
    return ng

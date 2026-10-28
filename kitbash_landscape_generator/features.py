# SPDX-License-Identifier: GPL-3.0-or-later
"""Cliff and cave features (M5): the local volume patch (D91).

Only the grid faces under a feature are touched. They are closed into a solid block, the feature's
cutter (a closed mesh built from SDF shapes) is subtracted from that block with the Manifold boolean, and
the block's walls and floor are thrown away again. The rim of the piece never moves, so it welds back
onto the rest of the grid exactly: the landscape stays one watertight surface (D91, bake as one mesh).
"""

import bpy

CUT_GROUP = "KB Landscape Cut"
CUT_VERSION = 9


def cut_group():
    """Geometry, Cutter (closed mesh), Adder (closed mesh, optional), Margin (m) -> the landscape with the
    adder joined on (rock a feature needs, like the hood over a cave mouth) and the cutter carved out.
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
    ng.interface.new_socket("Adder", in_out='INPUT', socket_type='NodeSocketGeometry')
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
    both = N.new('GeometryNodeJoinGeometry')
    L.new(gin.outputs["Adder"], both.inputs[0])
    L.new(gin.outputs["Cutter"], both.inputs[0])
    bb = node('GeometryNodeBoundBox', Geometry=both.outputs[0])
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

    adder = store(gin.outputs["Adder"], "lg_top", True)  # the added rock is new ground surface
    grow = N.new('GeometryNodeMeshBoolean')
    grow.operation = 'UNION'
    grow.solver = 'MANIFOLD'
    L.new(block.outputs[0], grow.inputs["Mesh 2"])
    L.new(adder, grow.inputs["Mesh 2"])
    cutter = store(gin.outputs["Cutter"], "lg_cave", True)
    boolean = N.new('GeometryNodeMeshBoolean')
    boolean.operation = 'DIFFERENCE'
    boolean.solver = 'EXACT'
    L.new(grow.outputs["Mesh"], boolean.inputs["Mesh 1"])
    L.new(cutter, boolean.inputs["Mesh 2"])
    # Keep the top and the carved faces; the block's walls and floor go.
    keep = math('MAXIMUM', named("lg_top"), named("lg_cave"))
    trim = N.new('GeometryNodeDeleteGeometry')
    trim.domain = 'FACE'
    L.new(boolean.outputs["Mesh"], trim.inputs["Geometry"])
    L.new(math('LESS_THAN', keep, 0.5), trim.inputs["Selection"])

    # The boolean merges flat runs of ground into long n-gons that shade as streaks: back to triangles.
    tri = N.new('GeometryNodeTriangulate')
    L.new(trim.outputs[0], tri.inputs["Mesh"])
    corners = N.new('GeometryNodeInputMeshFaceNeighbors')  # "Vertex Count": corners per face
    L.new(math('GREATER_THAN', corners.outputs["Vertex Count"], 4.5), tri.inputs["Selection"])
    back = N.new('GeometryNodeJoinGeometry')
    L.new(tri.outputs[0], back.inputs[0])
    L.new(sep.outputs["Inverted"], back.inputs[0])
    # Weld only the open rim (boundary points), not millions of grid points.
    # A point is on the rim if one of its edges has a single face (fewer than 4 faces also caught points
    # inside the cave mesh, and welding two of those broke the surface).
    open_edge = math('LESS_THAN', N.new('GeometryNodeInputMeshEdgeNeighbors').outputs["Face Count"], 1.5)
    on_edges = N.new('GeometryNodeFieldOnDomain')
    on_edges.domain = 'EDGE'
    on_edges.data_type = 'FLOAT'
    L.new(open_edge, on_edges.inputs[0])
    rim = math('GREATER_THAN', on_edges.outputs[0], 0.0)
    weld = node('GeometryNodeMergeByDistance', Geometry=back.outputs[0], Selection=rim, Distance=1e-5)  # rim copies are exact
    # Drop flaps: a stray triangle hanging off an edge (both solvers left one where the cave's floor or front
    # nearly touched the ground on Mesa). More than 60% of its edges open; a landscape corner has 50%.
    flap_open = math('LESS_THAN', N.new('GeometryNodeInputMeshEdgeNeighbors').outputs["Face Count"], 1.5)
    per_face = N.new('GeometryNodeFieldOnDomain')
    per_face.domain = 'EDGE'
    per_face.data_type = 'FLOAT'
    L.new(flap_open, per_face.inputs[0])
    unflap = N.new('GeometryNodeDeleteGeometry')
    unflap.domain = 'FACE'
    L.new(weld.outputs[0], unflap.inputs["Geometry"])
    L.new(math('GREATER_THAN', per_face.outputs[0], 0.6), unflap.inputs["Selection"])
    weld = unflap
    out = N.new('GeometryNodeSwitch')  # no cutter: the landscape untouched
    out.input_type = 'GEOMETRY'
    has = node('GeometryNodeAttributeDomainSize', Geometry=gin.outputs["Cutter"])
    L.new(math('GREATER_THAN', has.outputs["Face Count"], 0.5), out.inputs["Switch"])
    L.new(gin.outputs["Geometry"], out.inputs["False"])
    L.new(weld.outputs[0], out.inputs["True"])
    L.new(out.outputs[0], gout.inputs["Geometry"])
    ng["kb_version"] = CUT_VERSION
    return ng


ENTRANCE_GROUP = "KB Cave Entrance"
ENTRANCE_VERSION = 7


class _Tree:
    """Small node-building helpers for the feature groups."""

    def __init__(self, ng):
        self.N, self.L = ng.nodes, ng.links

    def _set(self, sock, v):
        if v is None:
            return
        if isinstance(v, bpy.types.NodeSocket):
            self.L.new(v, sock)
        else:
            sock.default_value = v

    def node(self, kind, outputs=None, **inputs):
        n = self.N.new(kind)
        for k, v in inputs.items():
            self._set(n.inputs[k.replace("_", " ")], v)
        return n

    def math(self, op, a, b=None):
        n = self.N.new('ShaderNodeMath')
        n.operation = op
        self._set(n.inputs[0], a)
        self._set(n.inputs[1], b)
        return n.outputs[0]

    def vmath(self, op, a, b=None, scale=None):
        n = self.N.new('ShaderNodeVectorMath')
        n.operation = op
        self._set(n.inputs[0], a)
        self._set(n.inputs[1], b)
        if scale is not None:
            self._set(n.inputs["Scale"], scale)
        return n.outputs["Vector"] if op not in ('LENGTH', 'DOT_PRODUCT', 'DISTANCE') else n.outputs["Value"]

    def xyz(self, v):
        n = self.N.new('ShaderNodeSeparateXYZ')
        self._set(n.inputs[0], v)
        return n.outputs

    def vec(self, x, y, z):
        n = self.N.new('ShaderNodeCombineXYZ')
        for sock, v in zip(n.inputs, (x, y, z)):
            self._set(sock, v)
        return n.outputs[0]

    def smooth(self, x, e0, e1):
        n = self.N.new('ShaderNodeMapRange')
        n.interpolation_type = 'SMOOTHSTEP'
        self._set(n.inputs["Value"], x)
        self._set(n.inputs["From Min"], e0)
        self._set(n.inputs["From Max"], e1)
        return n.outputs["Result"]

    def store(self, geo, name, value, data_type='FLOAT', domain='POINT'):
        n = self.N.new('GeometryNodeStoreNamedAttribute')
        n.data_type, n.domain = data_type, domain
        n.inputs["Name"].default_value = name
        self._set(n.inputs["Geometry"], geo)
        self._set(n.inputs["Value"], value)
        return n.outputs[0]

    def named(self, name, data_type='FLOAT'):
        n = self.N.new('GeometryNodeInputNamedAttribute')
        n.data_type = data_type
        n.inputs["Name"].default_value = name
        return n.outputs["Attribute"]

    def position(self):
        return self.N.new('GeometryNodeInputPosition').outputs[0]


def entrance_group():
    """A walk-in cave entrance cutter (M5 step 5.2, RESEARCH-caves.md): Terrain, Target (where to look),
    Width, Height, Depth (m), Flat Roof (0 round, 1 flat), Search (m), Spacing (m), Fine -> Cutter, and the
    Terrain with the face over the mouth raised where the slope is too low for a roof.

    The mouth snaps to the foot of the steepest rock face near Target: gentle ground at the spot, with ground
    rising at least the entrance height plus a roof just behind it. The cutter is a low arch driven straight
    into that face, with a flat floor at the mouth's ground height, so the cave floor carries on from the
    ground outside (Mike: you walk in at ground level)."""
    ng = bpy.data.node_groups.get(ENTRANCE_GROUP)
    if ng is not None and ng.get("kb_version") == ENTRANCE_VERSION:
        return ng
    if ng is None:
        ng = bpy.data.node_groups.new(ENTRANCE_GROUP, 'GeometryNodeTree')
    ng.interface.clear()
    ng.nodes.clear()
    ng.interface.new_socket("Cutter", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket("Terrain", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket("Terrain", in_out='INPUT', socket_type='NodeSocketGeometry')
    for name, stype, default in (("Target", 'NodeSocketVector', (0.0, 0.0, 0.0)), ("Width", 'NodeSocketFloat', 12.0),
                                 ("Height", 'NodeSocketFloat', 6.0), ("Depth", 'NodeSocketFloat', 18.0),
                                 ("Flat Roof", 'NodeSocketFloat', 0.0), ("Search", 'NodeSocketFloat', 40.0),
                                 ("Spacing", 'NodeSocketFloat', 0.5), ("Fine", 'NodeSocketBool', False),
                                 ("Seed", 'NodeSocketInt', 0)):
        ng.interface.new_socket(name, in_out='INPUT', socket_type=stype).default_value = default
    t = _Tree(ng)
    gin = t.node('NodeGroupInput').outputs
    gout = t.node('NodeGroupOutput')
    W, H, D = gin["Width"], gin["Height"], gin["Depth"]
    tgt = t.xyz(gin["Target"])
    pos = t.xyz(t.position())

    # Candidates: the terrain near Target, with a ring around it so the look-uphill probes stay on it.
    reach = t.math('MULTIPLY', H, 4.0)
    d_xy = t.vmath('LENGTH', t.vec(t.math('SUBTRACT', pos["X"], tgt["X"]), t.math('SUBTRACT', pos["Y"], tgt["Y"]), 0.0))
    near = t.node('GeometryNodeSeparateGeometry', Geometry=gin["Terrain"],
                  Selection=t.math('LESS_THAN', d_xy, t.math('ADD', gin["Search"], t.math('MULTIPLY', reach, 1.5))))
    near.domain = 'FACE'
    near_geo = near.outputs["Selection"]
    # Which way is uphill: the normal blurred over about one entrance width, so a flat foot still knows
    # which face it sits under. Ground normals lean downhill, so uphill is minus their flat part.
    blur = t.N.new('GeometryNodeBlurAttribute')
    blur.data_type = 'FLOAT_VECTOR'  # before linking: the type swaps the sockets
    t._set(blur.inputs["Value"], t.node('GeometryNodeInputNormal').outputs[0])
    t._set(blur.inputs["Iterations"], t.node('FunctionNodeFloatToInt', Float=t.math('MINIMUM', t.math('MAXIMUM', t.math('DIVIDE', W, gin["Spacing"]), 4.0), 40.0)).outputs[0])
    nb = t.xyz(blur.outputs["Value"])
    uphill = t.vmath('NORMALIZE', t.vec(t.math('MULTIPLY', nb["X"], -1.0), t.math('MULTIPLY', nb["Y"], -1.0), 0.0))

    def ground_ahead(dist):
        """Ground height `dist` meters uphill (negative: downhill) of each candidate, minus its own."""
        src = t.vmath('ADD', t.vmath('ADD', t.position(), t.vmath('SCALE', uphill, scale=dist)), t.vec(0.0, 0.0, 1.0e5))
        ray = t.node('GeometryNodeRaycast', Target_Geometry=near_geo, Source_Position=src,
                     Ray_Direction=(0.0, 0.0, -1.0), Ray_Length=2.0e5)
        return t.math('SUBTRACT', t.xyz(ray.outputs["Hit Position"])["Z"], pos["Z"])

    # The face must rise at least the entrance plus a roof (about 1.8x the height) within a few heights
    # uphill: the highest of three looks, so a cliff behind a talus slope still counts.
    rise = t.math('MAXIMUM', t.math('MAXIMUM', ground_ahead(H), ground_ahead(t.math('MULTIPLY', H, 2.5))),
                  t.math('MULTIPLY', ground_ahead(reach), 0.85))
    # ...and the face has to start right at the mouth (half the height up within 0.6 of it), or the mouth sat
    # out on flat ground up to 24 m in front of the cliff and the swell built a block out to meet it.
    starts = t.math('MINIMUM', t.math('DIVIDE', ground_ahead(t.math('MULTIPLY', H, 0.6)), t.math('MULTIPLY', H, 0.5)), 1.0)
    here_n = t.xyz(t.node('GeometryNodeInputNormal').outputs[0])
    gentle = t.smooth(here_n["Z"], 0.82, 0.95)  # 35 to 18 degrees
    # The ground in front must fall away (or stay level), or the opening cuts a trench into it: the foot
    # of a face, not the bottom of a hollow.
    gentle = t.math('MULTIPLY', gentle, t.smooth(ground_ahead(t.math('MULTIPLY', H, -1.6)), t.math('MULTIPLY', H, 0.25), 0.0))
    inside = t.math('LESS_THAN', d_xy, gin["Search"])
    score = t.math('SUBTRACT',
                   t.math('MULTIPLY', t.math('MULTIPLY', t.math('MULTIPLY', t.math('MINIMUM', t.math('DIVIDE', rise, t.math('MULTIPLY', H, 1.8)), 1.0),
                                                       t.math('MAXIMUM', starts, 0.0)), gentle), inside),
                   t.math('MULTIPLY', t.math('DIVIDE', d_xy, gin["Search"]), 0.15))
    cand = t.store(t.store(near_geo, "c_up", uphill, 'FLOAT_VECTOR'), "c_score", score)
    pts = t.node('GeometryNodeMeshToPoints', Mesh=cand).outputs[0]
    best = t.node('GeometryNodeSortElements', Geometry=pts, Sort_Weight=t.math('MULTIPLY', t.named("c_score"), -1.0))
    best.domain = 'POINT'

    def pick(field, data_type='FLOAT_VECTOR'):
        n = t.N.new('GeometryNodeSampleIndex')
        n.data_type, n.domain = data_type, 'POINT'
        t._set(n.inputs["Geometry"], best.outputs[0])
        t._set(n.inputs["Value"], field)
        return n.outputs[0]

    mouth = pick(t.position())
    mz = t.xyz(mouth)["Z"]
    up = t.xyz(pick(t.named("c_up", 'FLOAT_VECTOR')))
    angle = t.N.new('ShaderNodeMath')  # heading of the face, for turning local shapes to face out of it
    angle.operation = 'ARCTAN2'
    t._set(angle.inputs[0], up["Y"])
    t._set(angle.inputs[1], up["X"])

    def rock(p, scale, amount):
        """Rock noise in real meters at p: (Fac - 0.5) * amount."""
        n = t.node('ShaderNodeTexNoise', Vector=t.vmath('DIVIDE', p, t.vec(scale, scale, scale)), Scale=1.6, Detail=3.0, Roughness=0.6)
        n.noise_dimensions = '3D'
        return t.math('MULTIPLY', t.math('SUBTRACT', n.outputs["Fac"], 0.5), amount)

    r = t.math('MULTIPLY', W, 0.5)
    roof = t.math('MAXIMUM', t.math('MULTIPLY', H, 0.8), 1.5)

    # The face over the mouth (Mammoth: a rock ledge stands out of the hillside). The ground itself swells
    # into a steep face just behind the mouth, high enough for the entrance plus a roof, and eases back into
    # the slope behind and to the sides. Only ever raised (a smooth maximum), so a tall cliff is left alone.
    rel = t.vmath('SUBTRACT', t.position(), mouth)
    back = t.node('ShaderNodeVectorRotate', Vector=rel, Angle=t.math('MULTIPLY', angle.outputs[0], -1.0))
    back.rotation_type = 'Z_AXIS'
    q = t.xyz(back.outputs[0])  # local: X into the face, Y across
    # A rounded knob, not a block: a face rising over about one radius at the mouth, the top falling away
    # over a few heights behind it and to the sides (a flat-topped swell read as a building).
    width_in = t.math('MULTIPLY', r, 1.5)
    across = t.smooth(t.math('ABSOLUTE', q["Y"]), t.math('MULTIPLY', width_in, 2.2), t.math('MULTIPLY', width_in, 0.8))
    face = t.smooth(q["X"], t.math('MULTIPLY', r, -0.6), t.math('MULTIPLY', r, 0.4))
    fade = t.smooth(q["X"], t.math('ADD', t.math('MULTIPLY', r, 0.4), t.math('MULTIPLY', H, 3.0)), t.math('MULTIPLY', r, 0.4))
    lift = t.math('ADD', t.math('ADD', H, roof), rock(t.position(), t.math('MULTIPLY', r, 0.7), t.math('MULTIPLY', r, 0.6)))
    w = t.math('MULTIPLY', t.math('MULTIPLY', across, face), fade)
    # Outside the swell it drops far below ground, so the smooth maximum leaves the rest of the land alone.
    swell_z = t.math('SUBTRACT', t.math('ADD', mz, t.math('MULTIPLY', lift, w)), t.math('MULTIPLY', t.math('SUBTRACT', 1.0, w), t.math('MULTIPLY', H, 20.0)))
    gz = pos["Z"]
    k = t.math('MULTIPLY', H, 0.3)  # smooth maximum: no crease where the swell meets the slope
    hmx = t.math('MAXIMUM', t.math('SUBTRACT', k, t.math('ABSOLUTE', t.math('SUBTRACT', gz, swell_z))), 0.0)
    smax = t.math('ADD', t.math('MAXIMUM', gz, swell_z), t.math('DIVIDE', t.math('MULTIPLY', hmx, hmx), t.math('MULTIPLY', k, 4.0)))
    raised = t.node('GeometryNodeSetPosition', Geometry=gin["Terrain"],
                    Position=t.vec(pos["X"], pos["Y"], smax)).outputs[0]
    t.L.new(raised, gout.inputs["Terrain"])

    # The opening in local space (+X into the face, Z up, floor at 0): a row of spheres along X, narrowing
    # toward the back, stretched to Height, then cut by a box to a flat floor at 0, a level roof on layered
    # rock, and a flat front at the face (a clean Manifold cut; squashing points there left debris).
    voxel = t.math('MAXIMUM', t.math('DIVIDE', r, t.math('ADD', 8.0, t.math('MULTIPLY', gin["Fine"], 8.0))), 0.1)
    count = 24
    x0 = t.math('MULTIPLY', r, -0.6)
    line = t.node('GeometryNodeMeshLine', Count=count, Start_Location=t.vec(x0, 0.0, 0.0),
                  Offset=t.vec(t.math('DIVIDE', t.math('SUBTRACT', D, x0), count - 1), 0.0, 0.0))
    along = t.math('DIVIDE', t.node('GeometryNodeInputIndex').outputs[0], count - 1)
    radius = t.math('MULTIPLY', r, t.math('SUBTRACT', 1.0, t.math('MULTIPLY', t.math('POWER', along, 1.5), 0.45)))
    spheres = t.node('GeometryNodeMeshToPoints', Mesh=line.outputs[0], Radius=radius).outputs[0]
    sdf = t.node('GeometryNodePointsToSDFGrid', Points=spheres, Radius=t.node('GeometryNodeInputRadius').outputs[0], Voxel_Size=voxel)
    tube = t.node('GeometryNodeGridToMesh', Grid=sdf.outputs[0]).outputs[0]
    lp = t.xyz(t.position())
    stretch = t.math('DIVIDE', H, t.math('MULTIPLY', r, t.math('SUBTRACT', 1.0, t.math('MULTIPLY', gin["Flat Roof"], 0.35))))
    # Rough rock on walls and roof (none low down, so the floor stays flat after the cut).
    wall = t.smooth(lp["Z"], t.math('MULTIPLY', r, 0.1), t.math('MULTIPLY', r, 0.4))
    bump = t.math('MULTIPLY', rock(t.position(), r, t.math('MULTIPLY', r, 0.3)), wall)
    tall = t.node('GeometryNodeSetPosition', Geometry=tube,
                  Position=t.vec(lp["X"], t.math('ADD', lp["Y"], t.math('MULTIPLY', bump, t.math('DIVIDE', lp["Y"], t.math('MAXIMUM', r, 1e-3)))),
                                 t.math('ADD', t.math('MULTIPLY', lp["Z"], stretch), bump))).outputs[0]
    front_x = t.math('MULTIPLY', r, -0.3)
    span = t.math('ADD', t.math('SUBTRACT', D, front_x), r)
    box = t.node('GeometryNodeMeshCube', Size=t.vec(span, t.math('MULTIPLY', r, 4.0), H))
    for sock in ("Vertices X", "Vertices Y", "Vertices Z"):
        box.inputs[sock].default_value = 2
    box_at = t.node('GeometryNodeTransform', Geometry=box.outputs["Mesh"],
                    Translation=t.vec(t.math('ADD', front_x, t.math('MULTIPLY', span, 0.5)), 0.0, t.math('MULTIPLY', H, 0.5)))
    trimmed = t.N.new('GeometryNodeMeshBoolean')
    trimmed.operation = 'INTERSECT'
    trimmed.solver = 'MANIFOLD'
    t.L.new(tall, trimmed.inputs["Mesh 2"])
    t.L.new(box_at.outputs[0], trimmed.inputs["Mesh 2"])

    # Into the world: turn +X to face uphill, floor a hair under the mouth's ground so it opens cleanly.
    rot = t.node('ShaderNodeVectorRotate', Vector=t.position(), Angle=angle.outputs[0])
    rot.rotation_type = 'Z_AXIS'
    world = t.vmath('ADD', rot.outputs[0], t.vmath('SUBTRACT', mouth, t.vec(0.0, 0.0, t.math('MULTIPLY', H, 0.03))))
    placed = t.node('GeometryNodeSetPosition', Geometry=trimmed.outputs["Mesh"], Position=world).outputs[0]
    t.L.new(placed, gout.inputs["Cutter"])
    ng["kb_version"] = ENTRANCE_VERSION
    return ng

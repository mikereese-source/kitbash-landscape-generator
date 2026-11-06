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


CAVE_GROUP = "KB Cave"
CAVE_VERSION = 187
# (name, socket type, default) for the cave object's controls; sizes in real meters (D91).
CAVE_INPUTS = (
    ("Entrance Width", 'NodeSocketFloat', 12.0), ("Entrance Height", 'NodeSocketFloat', 6.0),
    ("Depth", 'NodeSocketFloat', 30.0), ("Wiggle", 'NodeSocketFloat', 0.3), ("Turn", 'NodeSocketFloat', 0.0),
    ("Drop", 'NodeSocketFloat', 0.0),
    ("Narrowing", 'NodeSocketFloat', 0.4), ("Chamber Size", 'NodeSocketFloat', 0.0),
    ("Ceiling Height", 'NodeSocketFloat', 10.0), ("Chamber Drop", 'NodeSocketFloat', 0.0),
    ("Ramp", 'NodeSocketBool', False), ("Rubble", 'NodeSocketFloat', 0.5), ("Wall Shape", 'NodeSocketFloat', 0.5), ("Roughness", 'NodeSocketFloat', 0.5),
    # How the rocks are spread (Mike): their size, how long they are, how far they tip, how far they strew.
    ("Rock Size", 'NodeSocketFloat', 1.0), ("Stretch", 'NodeSocketFloat', 0.3), ("Tilt", 'NodeSocketFloat', 0.5),
    ("Spread", 'NodeSocketFloat', 0.5),
    ("Rock", 'NodeSocketInt', 0),  # the walls: 0 Limestone, 1 Jointed, 2 Lava tube
    ("Seed", 'NodeSocketInt', 0), ("Detail", 'NodeSocketInt', 0),  # 0 Preview, 1 High, 2 Ultra
    ("Show Mask", 'NodeSocketInt', 0), ("Mask Heatmap", 'NodeSocketBool', False),  # the map viewer, as on the landscapes
    # Rock kits (rocks.py), each in three sizes: the rubble at the wall foot and the scree on the ramp.
    ("Rubble Big", 'NodeSocketCollection', None), ("Rubble Medium", 'NodeSocketCollection', None), ("Rubble Small", 'NodeSocketCollection', None),
    ("Scree Big", 'NodeSocketCollection', None), ("Scree Medium", 'NodeSocketCollection', None), ("Scree Small", 'NodeSocketCollection', None),
    # Formations (5.4, formations.py): how many, and each family's kit in three sizes.
    ("Formations", 'NodeSocketFloat', 0.5), ("Formation Size", 'NodeSocketFloat', 1.0), ("Formation Stretch", 'NodeSocketFloat', 0.5),
    ("Clusters", 'NodeSocketFloat', 0.85), ("Puddles", 'NodeSocketFloat', 0.5),  # mostly clusters, a few standing alone (Mike)
    # Each family's own amount, under Formations (Mike, D189): 0 none of it, 1 all its spots.
    # Water (D193): 0 none, 1 puddles, 2 the chamber flooded to Water Level (0 the chamber floor, 1 the passage floor).
    ("Water", 'NodeSocketInt', 1), ("Water Level", 'NodeSocketFloat', 0.6),
    ("Stalactite Amount", 'NodeSocketFloat', 1.0), ("Stalagmite Amount", 'NodeSocketFloat', 1.0), ("Column Amount", 'NodeSocketFloat', 1.0),
    # Drapes drawn by the artist (D185): a curve on the roof, and how long, how full and how folded the curtains are.
    ("Drape Lines", 'NodeSocketObject', None), ("Drape Length", 'NodeSocketFloat', 0.5), ("Drape Fullness", 'NodeSocketFloat', 0.8),
    ("Drape Fold", 'NodeSocketFloat', 0.5),
) + tuple((f"{fam} {size}", 'NodeSocketCollection', None) for fam in ("Stalactites", "Stalagmites", "Columns", "Lava Drips", "Stalactite Clusters", "Stalagmite Clusters", "Drapes")
          for size in ("Big", "Medium"))
CAVE_DETAIL = (6.0, 8.0, 8.0)  # voxels across the smaller of the entrance's half width and height (shape only;
# Mike: Preview's bolder forms looked best, finer voxels broke the masses into thin stretched strips)
CAVE_FACES = (150_000, 4_000_000, 16_000_000)  # shell faces aimed for per Detail Level, by subdividing (D105)
CAVE_SUBDIV = (2, 4, 5)  # but never fewer smoothing steps than these (each x4 faces; D121)


def cave_group():
    """The cave object (M5 step 5.2, D93): one closed mesh of the cave's space, the "sausage". The mouth is
    at the object's origin with a flat walk-in floor at Z 0, and the cave runs back along +Y. Place it so
    the mouth sits in a face, then carve it into a landscape or use it as a Boolean cutter on any mesh.

    A row of spheres along a wandering path (Wiggle), narrowing toward the back (Narrowing) and opening into
    a chamber at the end (Chamber Size, Ceiling Height, Chamber Drop). Each section is a dome of its own width
    and height on its own floor (which falls by Drop), with rubble rocks along the foot of the walls, all
    merged as one volume. Rock noise on the walls and roof, a gently uneven floor."""
    ng = bpy.data.node_groups.get(CAVE_GROUP)
    if ng is not None and ng.get("kb_version") == CAVE_VERSION:
        return ng
    if ng is None:
        ng = bpy.data.node_groups.new(CAVE_GROUP, 'GeometryNodeTree')
    ng.interface.clear()
    ng.nodes.clear()
    ng.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    for name, stype, default in CAVE_INPUTS:
        ng.interface.new_socket(name, in_out='INPUT', socket_type=stype).default_value = default
    t = _Tree(ng)
    gin = t.node('NodeGroupInput').outputs
    gout = t.node('NodeGroupOutput')
    W, H, D = gin["Entrance Width"], gin["Entrance Height"], gin["Depth"]
    r = t.math('MULTIPLY', W, 0.5)
    rc = t.math('MAXIMUM', t.math('MULTIPLY', gin["Chamber Size"], 0.5), 1e-3)
    has_chamber = t.math('GREATER_THAN', gin["Chamber Size"], 0.0)
    seed = t.math('MULTIPLY', gin["Seed"], 17.13)
    # Flooded chamber (D193, refs docs/m5/c151): one flat water level, from the chamber floor (Water Level 0) up to
    # the passage floor where the chamber opens (1), so you walk out onto the shore. Without a Chamber Drop the
    # range is a third of the entrance height, and the water never reaches the mouth.
    flood_on = t.math('COMPARE', gin["Water"], 2.0)
    w_bottom = t.math('SUBTRACT', t.math('MULTIPLY', gin["Drop"], -1.0), t.math('MULTIPLY', gin["Chamber Drop"], has_chamber))
    w_top = t.math('MINIMUM', t.math('MAXIMUM', t.math('MULTIPLY', gin["Drop"], -0.6), t.math('ADD', w_bottom, t.math('MULTIPLY', H, 0.3))),
                   t.math('MULTIPLY', H, -0.05))
    w_z = t.math('ADD', w_bottom, t.math('MULTIPLY', gin["Water Level"], t.math('SUBTRACT', w_top, w_bottom)))

    # The path: from just in front of the mouth (so the front pokes out through the face) to Depth.
    y0 = t.math('MULTIPLY', W, -0.3)
    count = t.node('FunctionNodeFloatToInt', Float=t.math('MINIMUM', t.math('MAXIMUM', t.math('DIVIDE', t.math('SUBTRACT', D, y0), t.math('MULTIPLY', r, 0.25)), 8.0), 600.0)).outputs[0]
    line = t.node('GeometryNodeMeshLine', Count=count, Start_Location=t.vec(0.0, y0, 0.0),
                  Offset=t.vec(0.0, t.math('DIVIDE', t.math('SUBTRACT', D, y0), t.math('SUBTRACT', count, 1.0)), 0.0))
    idx = t.node('GeometryNodeInputIndex').outputs[0]
    s = t.math('DIVIDE', idx, t.math('MAXIMUM', t.math('SUBTRACT', count, 1.0), 1.0))  # 0 mouth .. 1 back
    # A swing every 3.5 entrance widths (Mike likes the zigzag), each no wider than keeps the bend at least as
    # round as the passage (at full Wiggle the inner corner pinched): radius = wave^2 / (4 pi^2 amp) >= 0.9 r,
    # with 1.6 for the noise that varies each swing. Right first for Wiggle > 0, left first for < 0; the
    # passage leaves the mouth straight. Turn bends the whole passage left (-1) or right (+1).
    wave = t.math('MULTIPLY', W, 3.5)
    amp = t.math('MINIMUM', t.math('MULTIPLY', t.math('MULTIPLY', t.math('ABSOLUTE', gin["Wiggle"]), W), 1.2),
                 t.math('DIVIDE', t.math('MULTIPLY', wave, wave), t.math('MULTIPLY', r, 39.48 * 0.9 * 1.6)))
    swing = t.math('SINE', t.math('DIVIDE', t.math('MULTIPLY', t.math('MULTIPLY', s, D), 6.2832), wave))
    wn = t.node('ShaderNodeTexNoise', Vector=t.vec(t.math('DIVIDE', t.math('MULTIPLY', s, D), wave), seed, 0.0), Scale=1.0, Detail=1.0)
    wn.noise_dimensions = '2D'
    sway = t.math('MULTIPLY', t.math('MULTIPLY', t.math('MULTIPLY', swing, t.math('ADD', 0.4, t.math('MULTIPLY', wn.outputs["Fac"], 1.2))), amp),
                  t.math('SIGN', gin["Wiggle"]))
    sway = t.math('MULTIPLY', sway, t.smooth(s, 0.0, 0.2))
    bend = t.math('MULTIPLY', t.math('MULTIPLY', gin["Turn"], t.math('MULTIPLY', D, 0.35)), t.math('MULTIPLY', s, s))
    chamber = t.math('MULTIPLY', t.smooth(s, 0.6, 0.9), has_chamber)
    # The floor falls by Drop toward the back; the chamber's floor sinks a further Chamber Drop (Mike: so it
    # opens out into a massive space).
    floor_at = t.math('SUBTRACT', t.math('MULTIPLY', t.math('MULTIPLY', gin["Drop"], -1.0), t.math('MAXIMUM', s, 0.0)),
                      t.math('MULTIPLY', gin["Chamber Drop"], chamber))
    # Narrowing never closes the passage: at least a third of the entrance and 0.8 m (it could pinch shut).
    narrow = t.math('MAXIMUM', t.math('MULTIPLY', r, t.math('SUBTRACT', 1.0, t.math('MULTIPLY', t.math('POWER', s, 1.5), gin["Narrowing"]))),
                    t.math('MAXIMUM', t.math('MULTIPLY', r, 0.35), 0.8))
    radius = t.math('ADD', t.math('MULTIPLY', narrow, t.math('SUBTRACT', 1.0, chamber)), t.math('MULTIPLY', rc, chamber))
    # Each section's height, floor to roof: the entrance's Height, growing to the chamber's Ceiling Height.
    tall = t.math('ADD', t.math('MULTIPLY', H, t.math('SUBTRACT', 1.0, chamber)), t.math('MULTIPLY', gin["Ceiling Height"], chamber))
    path = t.node('GeometryNodeSetPosition', Geometry=line.outputs[0], Offset=t.vec(t.math('ADD', sway, bend), 0.0, floor_at)).outputs[0]
    path = t.store(t.store(t.store(t.store(path, "c_s", s), "c_narrow", narrow), "c_tall", tall), "c_ch", chamber)

    # Each section is built at its true size before meshing: a dome as wide as the passage and as tall as the
    # section, standing on its own floor height; all of them merged as one volume. (Stretching one tube after
    # meshing read each point's height and floor off the nearest bit of path; on a big chamber that was the
    # passage for some points and the chamber for their neighbours, and the mesh tore: Mike's curtains.)
    sphere = t.node('GeometryNodeMeshUVSphere', Segments=24, Rings=12, Radius=1.0).outputs["Mesh"]
    sp = t.xyz(t.position())
    dome = t.node('GeometryNodeSetPosition', Geometry=sphere, Position=t.vec(sp["X"], sp["Y"], t.math('MAXIMUM', sp["Z"], 0.0))).outputs[0]
    domes = t.node('GeometryNodeInstanceOnPoints', Points=path, Instance=dome, Scale=t.vec(radius, radius, tall)).outputs[0]

    per = t.node('GeometryNodeIndexSwitch')  # Detail Level: voxels across the entrance
    per.data_type = 'FLOAT'
    while len(per.index_switch_items) < len(CAVE_DETAIL):
        per.index_switch_items.new()
    t._set(per.inputs["Index"], gin["Detail"])
    for i, v in enumerate(CAVE_DETAIL):
        per.inputs[i + 1].default_value = v
    voxel = t.math('MAXIMUM', t.math('DIVIDE', t.math('MINIMUM', r, t.math('MAXIMUM', H, 0.5)), per.outputs[0]), 0.04)

    def level_set(parts, voxel=voxel):
        """Overlapping closed parts -> one signed-distance field. Through a fog volume first, which merges overlaps
        cleanly: a level set made straight from overlapping meshes kept their inner faces, and taking rubble out of
        it left holes, loose pieces and pinches (Mike). Returns (grid, merged mesh)."""
        fog = t.node('GeometryNodeMeshToVolume', Mesh=t.node('GeometryNodeRealizeInstances', Geometry=parts).outputs[0],
                     Density=1.0, Voxel_Size=voxel, Interior_Band_Width=t.math('MULTIPLY', voxel, 2.0))
        fog.inputs["Resolution Mode"].default_value = 'Size'
        skin = t.node('GeometryNodeVolumeToMesh', Volume=fog.outputs[0], Threshold=0.1).outputs[0]
        return t.node('GeometryNodeMeshToSDFGrid', Mesh=skin, Voxel_Size=voxel, Band_Width=3).outputs[0], skin

    space, space_mesh = level_set(domes)
    # The rocks are placed and kept against the cave's space built at Preview's grid, whatever the Detail Level
    # (Mike: the number and placement of rocks must not change between Preview, High and Ultra; tested against
    # each level's own shape, a few came and went). Only their height settles onto the finished shell.
    rock_voxel = t.math('MAXIMUM', t.math('DIVIDE', t.math('MINIMUM', r, t.math('MAXIMUM', H, 0.5)), CAVE_DETAIL[0]), 0.04)
    _rock_grid, rock_space = level_set(domes, rock_voxel)

    # Rubble at the foot of the walls (Mike: rocks, a blend like Mesa's talus), taken out of the same space:
    # two rows of rock lumps along the passage, one each side, of varied size. Rubble sets how many and how
    # big (0 none); Roughness is only the rock surface, as on the landscapes (Mike).
    def rand(lo, hi, offset, ident=None):
        n = t.N.new('FunctionNodeRandomValue')
        n.data_type = 'FLOAT'
        n.inputs["Min"].default_value, n.inputs["Max"].default_value = lo, hi
        t._set(n.inputs["Seed"], t.math('ADD', gin["Seed"], offset))
        if ident is not None:  # a stored id, so a point keeps its value when others are deleted before it
            t._set(n.inputs["ID"], ident)
        return n.outputs["Value"]

    ahead = t.N.new('GeometryNodeSampleIndex')  # the path's direction, from its neighbours
    ahead.data_type, ahead.domain = 'FLOAT_VECTOR', 'POINT'
    t._set(ahead.inputs["Geometry"], path)
    t._set(ahead.inputs["Value"], t.position())
    t._set(ahead.inputs["Index"], t.math('ADD', idx, 1.0))
    behind = t.N.new('GeometryNodeSampleIndex')
    behind.data_type, behind.domain = 'FLOAT_VECTOR', 'POINT'
    t._set(behind.inputs["Geometry"], path)
    t._set(behind.inputs["Value"], t.position())
    t._set(behind.inputs["Index"], t.math('MAXIMUM', t.math('SUBTRACT', idx, 1.0), 0.0))
    dirn = t.xyz(t.vmath('NORMALIZE', t.vmath('SUBTRACT', ahead.outputs[0], behind.outputs[0])))
    across = t.vec(dirn["Y"], t.math('MULTIPLY', dirn["X"], -1.0), 0.0)  # flat, at right angles to the path
    path = t.store(t.store(path, "c_across", across, 'FLOAT_VECTOR'), "c_radius", radius)
    # Distance along the path from its start, for the tube coordinates (below).
    run = t.N.new('GeometryNodeAccumulateField')
    run.data_type, run.domain = 'FLOAT', 'POINT'
    t._set(run.inputs["Value"], t.vmath('DISTANCE', t.position(), behind.outputs[0]))
    path = t.store(path, "c_len", run.outputs["Leading"])
    both = t.node('GeometryNodeDuplicateElements', Geometry=path, Amount=1)
    both.domain = 'POINT'
    rows = t.node('GeometryNodeJoinGeometry')
    t.L.new(path, rows.inputs[0])
    t.L.new(t.store(both.outputs["Geometry"], "c_side", 1.0), rows.inputs[0])
    sidev = t.math('SUBTRACT', t.math('MULTIPLY', t.named("c_side"), 2.0), 1.0)  # -1 one side, +1 the other
    # Rocks are sized to the passage up to a 25 m passage radius, no further (Mike: in a big chamber they grew to
    # 20-30 m and pushed out through the walls). Each row is pulled in off the wall by about a rock's half
    # width, so the rocks sit on the floor, not in the wall.
    rock_r = t.math('MINIMUM', t.named("c_radius"), 25.0)
    reach_out = t.math('SUBTRACT', t.math('MULTIPLY', t.named("c_radius"), t.math('SUBTRACT', 0.92, t.math('MULTIPLY', rand(0.0, 0.4, 11), gin["Spread"]))),
                       t.math('MULTIPLY', rock_r, t.math('MULTIPLY', gin["Rock Size"], 0.2)))
    # Rubble is how much rock, never how big (Mike: 0 none, 1 a lot; size is Rock Size): up to three more
    # rocks per foot point, spread along the passage.
    more = t.node('GeometryNodeDuplicateElements', Geometry=rows.outputs[0], Amount=t.node('FunctionNodeFloatToInt', Float=t.math('MULTIPLY', gin["Rubble"], 3.0)).outputs[0])
    more.domain = 'POINT'
    m_across = t.xyz(t.named("c_across", 'FLOAT_VECTOR'))
    more_at = t.node('GeometryNodeSetPosition', Geometry=more.outputs["Geometry"],
                     Offset=t.vmath('SCALE', t.vec(t.math('MULTIPLY', m_across["Y"], -1.0), m_across["X"], 0.0), scale=t.math('MULTIPLY', t.named("c_radius"), rand(-0.7, 0.7, 17)))).outputs[0]
    all_rows = t.node('GeometryNodeJoinGeometry')
    t.L.new(rows.outputs[0], all_rows.inputs[0])
    t.L.new(more_at, all_rows.inputs[0])
    foot = t.node('GeometryNodeSetPosition', Geometry=all_rows.outputs[0],
                  Offset=t.vmath('SCALE', t.named("c_across", 'FLOAT_VECTOR'), scale=t.math('MULTIPLY', sidev, reach_out))).outputs[0]
    # Each rock drops onto the floor below it (where the passage meets a sunk chamber, the floor is lower
    # than the path, and rocks floated).
    drop_ray = t.node('GeometryNodeRaycast', Target_Geometry=rock_space,
                      Source_Position=t.vmath('ADD', t.position(), t.vec(0.0, 0.0, t.math('MULTIPLY', H, 0.3))),
                      Ray_Direction=(0.0, 0.0, -1.0), Ray_Length=t.math('ADD', t.math('MULTIPLY', gin["Chamber Drop"], 2.0), t.math('MULTIPLY', H, 2.0)))
    foot = t.node('GeometryNodeSetPosition', Geometry=foot, Selection=drop_ray.outputs["Is Hit"], Position=drop_ray.outputs["Hit Position"]).outputs[0]
    # A kit of three sizes (Mike): the odd big block leaning on the wall, the everyday rocks, and pebbles strewn
    # out across the floor to break it up. A rock is big or medium, never both on one spot.
    not_jointed = t.math('SUBTRACT', 1.0, t.math('COMPARE', gin["Rock"], 1.0))  # jointed rock's fallen blocks lie in heaps instead (D178)
    big_keep = t.math('MULTIPLY', t.math('LESS_THAN', rand(0.0, 1.0, 29), t.math('MULTIPLY', gin["Rubble"], t.math('ADD', 0.15, t.math('MULTIPLY', t.math('COMPARE', gin["Rock"], 2.0), 0.15)))), not_jointed)  # lava: its big rocks are the fallen roof slabs, twice as many
    keep = t.math('MULTIPLY', t.math('MULTIPLY', t.math('LESS_THAN', rand(0.0, 1.0, 23), gin["Rubble"]), t.math('SUBTRACT', 1.0, big_keep)), not_jointed)
    # Pebbles: three for each foot point, thrown out from the wall onto the floor and along the passage.
    strewn = t.node('GeometryNodeDuplicateElements', Geometry=rows.outputs[0], Amount=t.node('FunctionNodeFloatToInt', Float=t.math('ADD', 2.0, t.math('MULTIPLY', gin["Rubble"], 6.0))).outputs[0])
    strewn.domain = 'POINT'
    across_v = t.named("c_across", 'FLOAT_VECTOR')
    along_v = t.vec(t.math('MULTIPLY', t.xyz(across_v)["Y"], -1.0), t.xyz(across_v)["X"], 0.0)
    pebble_at = t.node('GeometryNodeSetPosition', Geometry=strewn.outputs["Geometry"],
                       Offset=t.vmath('ADD', t.vmath('SCALE', across_v, scale=t.math('MULTIPLY', sidev, t.math('SUBTRACT', t.math('MULTIPLY', t.named("c_radius"), t.math('SUBTRACT', 0.95, t.math('MULTIPLY', rand(0.0, 1.5, 131), gin["Spread"]))), t.math('MULTIPLY', rock_r, 0.1)))),
                                      t.vmath('SCALE', along_v, scale=t.math('MULTIPLY', t.named("c_radius"), t.math('MULTIPLY', rand(-1.2, 1.2, 137), gin["Spread"]))))).outputs[0]
    pebble_ray = t.node('GeometryNodeRaycast', Target_Geometry=rock_space,
                        Source_Position=t.vmath('ADD', t.position(), t.vec(0.0, 0.0, t.math('MULTIPLY', H, 0.3))),
                        Ray_Direction=(0.0, 0.0, -1.0), Ray_Length=t.math('ADD', t.math('MULTIPLY', gin["Chamber Drop"], 2.0), t.math('MULTIPLY', H, 2.0)))
    pebbles_at = t.node('GeometryNodeSetPosition', Geometry=pebble_at, Selection=pebble_ray.outputs["Is Hit"], Position=pebble_ray.outputs["Hit Position"]).outputs[0]
    pebble_keep = t.math('MULTIPLY', t.math('MULTIPLY', t.math('LESS_THAN', rand(0.0, 1.0, 139), gin["Rubble"]), pebble_ray.outputs["Is Hit"]), not_jointed)
    # The rocks come from a collection of separate rock meshes (D105, rocks.py; any collection can be swapped
    # in), one picked at random per rock. Each fits -1..1 with its pivot 45% up, so it sits partly buried.
    def library(name):
        info = t.node('GeometryNodeCollectionInfo', Collection=gin[name], Separate_Children=True, Reset_Children=True)
        info.transform_space = 'ORIGINAL'
        return info.outputs[0]

    pick = lambda offset: t.node('FunctionNodeFloatToInt', Float=rand(0.0, 9999.0, offset)).outputs[0]  # wraps per collection

    def scatter(points, selection, kit, size, seed, across):
        """One size of a kit on its points: each rock picked at random, turned about the vertical with a small
        tilt (the buried side stays down) and stretched a little. Big and small rocks carry their own size."""
        size = t.math('MULTIPLY', size, gin["Rock Size"])
        tip = lambda k: t.math('MULTIPLY', rand(-0.35, 0.35, seed + k), gin["Tilt"])
        long = t.math('ADD', 1.0, t.math('MULTIPLY', rand(0.0, 1.5, seed + 6), gin["Stretch"]))  # drawn out along its length
        placed = t.node('GeometryNodeInstanceOnPoints', Points=points, Selection=selection, Instance=library(kit), Pick_Instance=True,
                        Instance_Index=pick(seed), Rotation=t.vec(tip(1), tip(2), rand(0.0, 6.28, seed + 3)),
                        Scale=t.vec(t.math('MULTIPLY', size, long), t.math('MULTIPLY', size, rand(0.7, 1.3, seed + 4)), t.math('MULTIPLY', size, rand(0.5, 0.9, seed + 5)))).outputs[0]
        return t.store(placed, "lg_rock_r", across, 'FLOAT', 'INSTANCE')  # the kit's half width at scale 1 (big rocks are wider)

    # Sized to the passage up to the cap above; instances, so no lower limit from the rock-detail grid.
    size = t.math('MULTIPLY', t.math('MULTIPLY', rock_r, rand(0.12, 0.32, 37)), 0.8)
    rubble_sets = [scatter(foot, keep, "Rubble Medium", size, 97, 1.0), scatter(foot, big_keep, "Rubble Big", size, 151, 3.0),
                   scatter(pebbles_at, pebble_keep, "Rubble Small", size, 161, 0.5)]

    # Ramp into Chamber (Mike, for players): an embankment of rock along the path, from the passage floor down
    # into the sunk chamber, so it can be walked down instead of jumped, with scree on its slopes.
    # (Without it the merged domes' floors leave steps where the floor drops.)
    ramp_on = t.math('MULTIPLY', t.math('MULTIPLY', gin["Ramp"], has_chamber), t.math('GREATER_THAN', gin["Chamber Drop"], 0.0))
    walk = t.node('GeometryNodeResampleCurve', Curve=t.node('GeometryNodeMeshToCurve', Mesh=path).outputs[0], Length=0.5)
    walk.inputs["Mode"].default_value = 'Length'
    walk_c = walk.outputs[0]
    tan = t.xyz(t.node('GeometryNodeInputTangent').outputs[0])
    walk_c = t.store(walk_c, "c_heading", t.math('ARCTAN2', t.math('MULTIPLY', tan["X"], -1.0), tan["Y"]))
    walk_c = t.store(walk_c, "c_mid", t.position(), 'FLOAT_VECTOR')
    walk_pts = t.node('GeometryNodeCurveToPoints', Curve=walk_c)
    walk_pts.mode = 'EVALUATED'
    # Walkable: from where the chamber begins (s 0.6) the ramp falls at most 1 in 2 (about 27 degrees) until it
    # meets the chamber floor, running out into the chamber as a causeway if it must (following the floor's own
    # curve was over 50 degrees in a short cave).
    wp = t.xyz(t.position())
    # Start where the chamber begins, or earlier if the slope needs more room to reach the chamber floor by the
    # end of the path (a short cave ran out of path and ended the ramp in a drop).
    y06 = t.math('MINIMUM', t.math('ADD', y0, t.math('MULTIPLY', t.math('SUBTRACT', D, y0), 0.6)),
                 t.math('SUBTRACT', D, t.math('ADD', t.math('MULTIPLY', gin["Chamber Drop"], 2.0), 1.0)))
    graded = t.math('SUBTRACT', t.math('MULTIPLY', t.math('MULTIPLY', gin["Drop"], -1.0), t.named("c_s")),
                    t.math('MULTIPLY', t.math('MAXIMUM', t.math('SUBTRACT', wp["Y"], y06), 0.0), 0.5))
    # Straight down the grade to the chamber floor, not along the floor's own S-curve (steeper mid-way).
    bottom = t.math('SUBTRACT', t.math('MULTIPLY', t.math('MULTIPLY', gin["Drop"], -1.0), t.named("c_s")), gin["Chamber Drop"])
    walk_top = t.node('GeometryNodeSetPosition', Geometry=walk_pts.outputs["Points"],
                      Position=t.vec(wp["X"], wp["Y"], t.math('MAXIMUM', graded, bottom))).outputs[0]
    # Only while the ramp still stands above the chamber floor (past that its edge rocks ran on across the
    # chamber in a line; Mike).
    walk_top = t.store(walk_top, "c_above", t.math('SUBTRACT', t.math('MAXIMUM', graded, bottom), bottom))
    # Scree from about where the floor starts to fall, not along the whole level start of the ramp.
    on_ramp = t.math('MULTIPLY', ramp_on, t.math('MULTIPLY', t.math('GREATER_THAN', wp["Y"], t.math('SUBTRACT', y06, t.math('MULTIPLY', rc, 0.5))),
                                                 t.math('GREATER_THAN', t.named("c_above"), 0.3)))
    # The ramp's width wanders (0.6 to 1.1 of the passage), so its edges aren't ruler-straight.
    rw = t.node('ShaderNodeTexNoise', Vector=t.vmath('DIVIDE', t.position(), t.vec(W, W, W)), Scale=1.5, Detail=2.0)
    rw.noise_dimensions = '3D'
    ramp_w = t.math('MULTIPLY', t.named("c_narrow"), t.math('ADD', 1.2, t.math('MULTIPLY', rw.outputs["Fac"], 1.0)))
    walk_top = t.store(walk_top, "c_ramp_w", ramp_w)
    # The ramp's body, one continuous shape swept along the path (Mike: at Preview the half-metre slabs and
    # wedges came out as saw-teeth and holes, smaller than a step of rock detail): a walkway on top, sides
    # sloping out about 35 degrees down to just into the chamber floor, ends closed.
    ramp_c = t.store(walk_c, "c_raw", t.math('SUBTRACT', graded, bottom))  # below 0 past the ramp's foot
    ramp_c = t.store(t.store(t.store(ramp_c, "c_rtop", t.math('MAXIMUM', graded, bottom)),
                             "c_above", t.math('SUBTRACT', t.math('MAXIMUM', graded, bottom), bottom)), "c_ramp_w", ramp_w)
    # From as far back as the chamber's space reaches over the passage (a wide chamber reaches back past where
    # the slope begins, and the floor dropped away before the ramp picked up: a gap; Mike), level with the
    # passage floor until the slope starts.
    reach_back = t.math('SUBTRACT', t.math('SUBTRACT', y06, rc), W)
    on_curve = t.math('MULTIPLY', ramp_on, t.math('MULTIPLY', t.math('GREATER_THAN', t.xyz(t.position())["Y"], reach_back),
                                                  t.math('GREATER_THAN', t.named("c_raw"), t.math('MULTIPLY', voxel, -2.0))))
    trim_c = t.node('GeometryNodeDeleteGeometry', Geometry=ramp_c, Selection=t.math('LESS_THAN', on_curve, 0.5))
    trim_c.domain = 'POINT'
    square = t.node('GeometryNodeCurvePrimitiveQuadrilateral', Width=2.0, Height=2.0).outputs[0]
    sq = t.xyz(t.position())
    square = t.store(t.store(square, "p_side", sq["X"]), "p_top", t.math('GREATER_THAN', sq["Y"], 0.0))
    swept = t.node('GeometryNodeCurveToMesh', Curve=trim_c.outputs[0], Profile_Curve=square, Fill_Caps=True).outputs[0]
    # Each corner goes where it belongs, from the path point it was swept from (profile and path attributes
    # both carry onto the mesh): top corners at the walkway's edges, bottom corners out at the slopes' feet.
    top = t.named("p_top")
    low = t.math('SUBTRACT', 1.0, top)
    # Buried at least a voxel and a half, and run on past its foot level with the floor (Mike: holes along the
    # ramp's foot; thinner than the shape's voxels, its edge and end opened pits and saw-teeth into the floor).
    h_r = t.math('ADD', t.named("c_above"), t.math('MAXIMUM', t.math('MULTIPLY', voxel, 1.5), 1.0))
    reach = t.math('ADD', t.math('MULTIPLY', t.named("c_ramp_w"), 0.5), t.math('MULTIPLY', low, t.math('MULTIPLY', h_r, 1.4)))
    across_r = t.vec(t.math('COSINE', t.named("c_heading")), t.math('SINE', t.named("c_heading")), 0.0)
    rp = t.xyz(t.named("c_mid", 'FLOAT_VECTOR'))
    corner_at = t.vmath('ADD', t.vec(rp["X"], rp["Y"], t.math('SUBTRACT', t.named("c_rtop"), t.math('MULTIPLY', low, h_r))),
                        t.vmath('SCALE', across_r, scale=t.math('MULTIPLY', t.math('SIGN', t.named("p_side")), reach)))
    ramp_mesh = t.node('GeometryNodeSetPosition', Geometry=swept, Position=corner_at).outputs[0]

    edge = t.node('GeometryNodeDuplicateElements', Geometry=walk_top, Amount=1)
    edge.domain = 'POINT'
    edges = t.node('GeometryNodeJoinGeometry')
    t.L.new(walk_top, edges.inputs[0])
    t.L.new(t.store(edge.outputs["Geometry"], "c_side", 1.0), edges.inputs[0])
    out_dir = t.vec(t.math('COSINE', t.named("c_heading")), t.math('SINE', t.named("c_heading")), 0.0)  # the slab's local X
    # Edge rocks scattered, not a row (Mike: it looked man-made): sparse, pushed in or out from the edge and
    # along it at random, mostly small with the odd boulder.
    heading_v = t.vec(t.math('MULTIPLY', t.math('SINE', t.named("c_heading")), -1.0), t.math('COSINE', t.named("c_heading")), 0.0)
    # On the side slopes, anywhere from the walkway's edge to their foot, dropped onto the slope below.
    out_k = rand(0.0, 1.0, 83)
    sideways = t.math('MULTIPLY', t.math('SUBTRACT', t.math('MULTIPLY', t.named("c_side"), 2.0), 1.0),
                      t.math('ADD', t.math('MULTIPLY', t.named("c_ramp_w"), 0.45),
                             t.math('MULTIPLY', t.math('MULTIPLY', out_k, out_k), t.math('MULTIPLY', t.named("c_above"), 1.3))))
    edge_pts = t.node('GeometryNodeSetPosition', Geometry=edges.outputs[0],
                      Offset=t.vmath('ADD', t.vmath('ADD', t.vmath('SCALE', out_dir, scale=sideways),
                                                    t.vmath('SCALE', heading_v, scale=rand(-1.5, 1.5, 89))),
                                     t.vec(0.0, 0.0, t.math('MULTIPLY', t.math('MULTIPLY', out_k, out_k), t.math('MULTIPLY', t.named("c_above"), -0.93))))).outputs[0]
    onto = t.node('GeometryNodeRaycast', Target_Geometry=ramp_mesh,
                  Source_Position=t.vmath('ADD', t.position(), t.vec(0.0, 0.0, t.math('MULTIPLY', H, 0.5))),
                  Ray_Direction=(0.0, 0.0, -1.0), Ray_Length=t.math('ADD', t.math('MULTIPLY', gin["Chamber Drop"], 2.0), t.math('MULTIPLY', H, 2.0)))
    edge_pts = t.node('GeometryNodeSetPosition', Geometry=edge_pts, Selection=onto.outputs["Is Hit"], Position=onto.outputs["Hit Position"]).outputs[0]
    edge_keep = t.math('MULTIPLY', on_ramp, t.math('LESS_THAN', rand(0.0, 1.0, 61), t.math('MULTIPLY', gin["Rubble"], 0.33)))  # Rubble 0: none
    edge_size = t.math('MULTIPLY', t.named("c_narrow"), t.math('ADD', 0.05, t.math('MULTIPLY', t.math('POWER', rand(0.0, 1.0, 67), 2.5), 0.35)))
    # Scree in three sizes too: the odd big slab, the everyday scree, and plenty of small chips.
    edge_big = t.math('MULTIPLY', on_ramp, t.math('LESS_THAN', rand(0.0, 1.0, 171), t.math('MULTIPLY', gin["Rubble"], 0.04)))
    edge_small = t.math('MULTIPLY', on_ramp, t.math('LESS_THAN', rand(0.0, 1.0, 173), t.math('MULTIPLY', gin["Rubble"], 0.6)))
    edge_sets = [scatter(edge_pts, t.math('MULTIPLY', edge_keep, t.math('SUBTRACT', 1.0, edge_big)), "Scree Medium", edge_size, 101, 1.0),
                 scatter(edge_pts, edge_big, "Scree Big", edge_size, 181, 3.0), scatter(edge_pts, edge_small, "Scree Small", edge_size, 191, 0.5)]
    solids = t.node('GeometryNodeJoinGeometry')
    t.L.new(ramp_mesh, solids.inputs[0])
    # Jointed rock, primary shapes (from the rockfall reference, docs/m5/ref_jointed_shapes.jpg): big slabs of
    # rock set into the walls as the cave's shape is built, each cutting a face into the passage. Like the
    # Resident Evil Village caves Mike shared, they stand nearly upright and lean in at the top, so the passage
    # is a tall keyhole of big masses, overlapping into creased edges, never reaching the walkway (at most 40%
    # of the way in at their foot). Displacing the finished tube could only make ramps, which
    # wrapped the passage in rings.
    jointed_on = t.math('MULTIPLY', t.math('COMPARE', gin["Rock"], 1.0), t.math('GREATER_THAN', gin["Wall Shape"], 0.0))
    # None at the mouth (it keeps its size) or where the passage opens into a chamber (a slab sized for the
    # passage stuck out into the bigger space).
    opening = t.math('MULTIPLY', has_chamber, t.math('MULTIPLY', t.math('GREATER_THAN', t.named("c_s"), 0.64), t.math('LESS_THAN', t.named("c_s"), 0.8)))
    slab_keep = t.math('MULTIPLY', t.math('MULTIPLY', jointed_on, t.math('LESS_THAN', rand(0.0, 1.0, 211), 0.5)),
                       t.math('MULTIPLY', t.math('GREATER_THAN', t.named("c_s"), 0.3), t.math('LESS_THAN', t.math('MULTIPLY', t.named("c_s"), has_chamber), 0.58)))
    # right up to the opening (Mike: melted without them) but not past its lip: over a sunk chamber they hung
    # out over the drop; the chamber's ring of masses is its wall
    intrude = t.math('MULTIPLY', t.named("c_radius"), t.math('MULTIPLY', rand(0.08, 0.2, 213), t.math('MINIMUM', t.math('MULTIPLY', gin["Wall Shape"], 1.6), 1.0)))
    thick = t.math('MULTIPLY', W, 2.0)
    across_s = t.named("c_across", 'FLOAT_VECTOR')
    # Each mass finds the real wall beside it (a ray out sideways onto the cave's space), so through the opening
    # into a chamber, where the chamber reaches back over the passage, it sits in the chamber's wall instead of
    # standing out in the open space as an overhang.
    side_ray = t.node('GeometryNodeRaycast', Target_Geometry=space_mesh,
                      Source_Position=t.vmath('ADD', t.position(), t.vec(0.0, 0.0, t.math('MULTIPLY', t.named("c_tall"), 0.4))),
                      Ray_Direction=t.vmath('SCALE', across_s, scale=sidev), Ray_Length=t.math('ADD', t.math('MULTIPLY', rc, 2.0), W))
    wall_d = t.N.new('GeometryNodeSwitch')
    wall_d.input_type = 'FLOAT'
    t._set(wall_d.inputs['Switch'], side_ray.outputs["Is Hit"])
    t._set(wall_d.inputs['False'], t.named("c_radius"))
    t._set(wall_d.inputs['True'], side_ray.outputs["Hit Distance"])
    out_by = t.math('ADD', t.math('SUBTRACT', wall_d.outputs[0], intrude), t.math('MULTIPLY', thick, 0.5))
    slab_at = t.node('GeometryNodeSetPosition', Geometry=rows.outputs[0],
                     Offset=t.vmath('ADD', t.vmath('SCALE', across_s, scale=t.math('MULTIPLY', sidev, out_by)),
                                    t.vec(0.0, 0.0, t.math('MULTIPLY', t.named("c_tall"), 0.5)))).outputs[0]  # low enough to reach the floor, not spread across it
    yaw = t.math('ARCTAN2', t.xyz(across_s)["Y"], t.xyz(across_s)["X"])
    # Upright blocks with flat faces (Mike: the rock-kit masses came out round and bulbous, not like jointed
    # rock; he wants boxy, square, vertical columns lined up with the joints on the walls): boxes standing
    # nearly upright, narrow along the passage so several sit side by side, each set in or out its own amount.
    # Every column runs from below the floor up into the roof, plumb, like a support (Mike: short or leaning
    # ones floated, read as stalactites); they come in only a little, so the passage stays open.
    cube = library("Rubble Medium")  # each rock fits -1..1, so scales below are halved (limestone's plates)
    column = t.node('GeometryNodeMeshCube', Size=(2.0, 2.0, 2.0)).outputs["Mesh"]  # -1..1 like the rocks
    # The jointed masses (columns, steps, teardrops, roof blocks) together, made as separate pieces set into the
    # walls, floor and roof (below), not cut into the cave's shape (Mike, D141: cut in left too many nodules).
    cols = t.node('GeometryNodeJoinGeometry')
    # Carved, not boxes (Mike: no straight lines, no straight verticals; they need to be jagged, carved more):
    # each block steps in and out in horizontal bands, a flat plane per band, its own pattern per block, so its
    # faces stay flat and layered but no edge runs straight up (smooth noise melted them; patches tore them).
    col_id = t.node('GeometryNodeStoreNamedAttribute', Geometry=cols.outputs[0], Name="lg_cid", Value=rand(0.0, 1000.0, 361))
    col_id.data_type, col_id.domain = 'FLOAT', 'INSTANCE'
    carved = t.node('GeometryNodeSubdivideMesh', Mesh=t.node('GeometryNodeRealizeInstances', Geometry=col_id.outputs[0]).outputs[0], Level=4).outputs[0]
    cid = t.named("lg_cid")
    band = t.math('FLOOR', t.math('ADD', t.math('DIVIDE', t.xyz(t.position())["Z"], t.math('MULTIPLY', W, 0.6)), t.math('FRACT', cid)))
    band_r = t.node('ShaderNodeTexWhiteNoise', Vector=t.vec(band, cid, 0.0)).outputs["Value"]
    carve_d = t.math('MULTIPLY', band_r, t.math('MULTIPLY', W, -0.15))  # cut in only (pushing out closed the passage)
    carved = t.node('GeometryNodeSetPosition', Geometry=carved, Offset=t.vmath('SCALE', t.node('GeometryNodeInputNormal').outputs[0], scale=carve_d)).outputs[0]
    # Every column reaches down past the floor by the chamber's drop as well (Mike: by the opening into a sunk
    # chamber, whose roof reaches back over the passage, a column's foot came out into the open and hung there
    # like a drip). Below a floor it stays buried in rock; over the chamber it runs on down to its floor.
    reach = t.math('MULTIPLY', t.named("c_tall"), 1.14)  # half the column's height, before the extra
    half = t.math('ADD', reach, t.math('MULTIPLY', t.math('ADD', gin["Chamber Drop"], 2.0), 0.5))  # past a ramp too (they hung over its slope)
    slabs = t.node('GeometryNodeInstanceOnPoints', Points=slab_at, Selection=slab_keep, Instance=column,
                   Rotation=t.vec(rand(-0.03, 0.03, 217), t.math('MULTIPLY', t.math('MULTIPLY', sidev, -1.0), rand(0.0, 0.04, 219)), t.math('ADD', yaw, rand(-0.12, 0.12, 221))),
                   Scale=t.vec(t.math('MULTIPLY', thick, 0.5), t.math('MULTIPLY', W, rand(0.22, 0.45, 223)), half)).outputs[0]
    # Moved down so its top stays where it was.
    slabs = t.node('GeometryNodeTranslateInstances', Instances=slabs, Translation=t.vec(0.0, 0.0, t.math('SUBTRACT', reach, half)), Local_Space=False).outputs[0]
    t.L.new(slabs, cols.inputs[0])
    # The chamber's own columns (Mike: columns in the chamber, without blocking its entrance): points spread
    # over the chamber's standing walls, each a carved column from below its floor up into its roof, standing
    # out a little. Rays from the end of the path missed the walls of a big chamber, and one aimed at the
    # opening stood a column across the passage. Only walls facing out from the chamber's middle count (not
    # the passage's), and none near where the passage opens into it.
    def path_mean(sel):
        st = t.node('GeometryNodeAttributeStatistic', Geometry=path, Selection=sel, Attribute=t.position())
        st.data_type, st.domain = 'FLOAT_VECTOR', 'POINT'
        return st.outputs["Mean"]
    ch_mid = path_mean(t.math('GREATER_THAN', t.named("c_s"), 0.95))
    flat = lambda v: t.vec(t.xyz(v)["X"], t.xyz(v)["Y"], 0.0)
    # the opening: where the path crosses the chamber's edge, a chamber's radius from its middle
    ch_door = path_mean(t.math('LESS_THAN', t.math('ABSOLUTE', t.math('SUBTRACT', t.vmath('LENGTH', flat(t.vmath('SUBTRACT', t.position(), ch_mid))), rc)), W))
    # 24 rays out from the chamber's middle, a third of the way up; none within 35 degrees of the opening.
    ring_n = t.node('GeometryNodePoints', Count=24, Position=t.vmath('ADD', ch_mid, t.vec(0.0, 0.0, t.math('MULTIPLY', gin["Ceiling Height"], 0.35)))).outputs[0]
    ang = t.math('ADD', t.math('MULTIPLY', t.node('GeometryNodeInputIndex').outputs[0], 0.2618), rand(-0.1, 0.1, 231))
    ring_dir = t.vec(t.math('COSINE', ang), t.math('SINE', ang), 0.0)
    to_door = t.vmath('NORMALIZE', flat(t.vmath('SUBTRACT', ch_door, ch_mid)))
    ring_ray = t.node('GeometryNodeRaycast', Target_Geometry=space_mesh, Source_Position=t.position(), Ray_Direction=ring_dir,
                      Ray_Length=t.math('MULTIPLY', rc, 3.0))
    ring_keep = t.math('MULTIPLY', t.math('MULTIPLY', jointed_on, has_chamber), t.math('LESS_THAN', rand(0.0, 1.0, 235), 0.75))
    ring_keep = t.math('MULTIPLY', ring_keep, t.math('MULTIPLY', ring_ray.outputs["Is Hit"],
                       t.math('LESS_THAN', t.vmath('DOT_PRODUCT', ring_dir, to_door), 0.82)))  # the entrance stays clear
    ring_depth = t.math('MULTIPLY', thick, 0.3)  # half the column's depth
    wn = ring_dir
    # Leaning in with the dome (straight up, a column left the chamber's space halfway up and was cut off there,
    # a stub): a second ray, higher up, finds how far the wall has come in, and the column tips to follow it.
    up_ray = t.node('GeometryNodeRaycast', Target_Geometry=space_mesh,
                    Source_Position=t.vmath('ADD', t.position(), t.vec(0.0, 0.0, t.math('MULTIPLY', gin["Ceiling Height"], 0.4))),
                    Ray_Direction=ring_dir, Ray_Length=t.math('MULTIPLY', rc, 3.0))
    lean = t.math('ARCTAN2', t.math('SUBTRACT', ring_ray.outputs["Hit Distance"], up_ray.outputs["Hit Distance"]), t.math('MULTIPLY', gin["Ceiling Height"], 0.4))
    lean = t.math('MULTIPLY', up_ray.outputs["Is Hit"], t.math('MINIMUM', t.math('MAXIMUM', lean, 0.0), 0.7))
    ring_n = t.store(ring_n, "lg_lean", lean)
    ring_n = t.store(ring_n, "lg_rk", ring_keep)  # kept before the points move (the ray is cast from where they start)
    # Leaning from its foot (leaning about its middle lifted the foot off the floor): its axis passes through
    # the wall where the ray met it and runs down to below the chamber's floor.
    ring_half = t.math('MULTIPLY', gin["Ceiling Height"], 1.3)
    axis = t.vec(t.math('MULTIPLY', t.xyz(ring_dir)["X"], t.math('MULTIPLY', t.math('SINE', lean), -1.0)),
                 t.math('MULTIPLY', t.xyz(ring_dir)["Y"], t.math('MULTIPLY', t.math('SINE', lean), -1.0)), t.math('COSINE', lean))
    to_foot = t.math('DIVIDE', t.math('ADD', t.math('ADD', t.xyz(ring_ray.outputs["Hit Position"])["Z"], t.math('ADD', gin["Drop"], gin["Chamber Drop"])), 4.0), t.math('COSINE', lean))
    ring_at = t.node('GeometryNodeSetPosition', Geometry=ring_n, Position=t.vmath('ADD', t.vmath('ADD', ring_ray.outputs["Hit Position"],
                     t.vmath('SCALE', ring_dir, scale=t.math('SUBTRACT', ring_depth, t.math('MULTIPLY', rc, rand(0.02, 0.07, 233))))),
                     t.vmath('SCALE', axis, scale=t.math('SUBTRACT', ring_half, to_foot)))).outputs[0]
    ring = t.node('GeometryNodeInstanceOnPoints', Points=ring_at, Selection=t.named("lg_rk"), Instance=column,
                  Rotation=t.vec(rand(-0.03, 0.03, 237), t.math('MULTIPLY', t.named("lg_lean"), -1.0), t.math('ADD', t.math('ARCTAN2', t.xyz(wn)["Y"], t.xyz(wn)["X"]), rand(-0.12, 0.12, 241))),  # top tips in
                  Scale=t.vec(ring_depth, t.math('MULTIPLY', rc, rand(0.06, 0.12, 243)), ring_half)).outputs[0]  # floor to roof and past both
    t.L.new(ring, cols.inputs[0])
    # Second pass against the jointed references (sea-cave interior, rockfall cave): the roof hangs in big
    # angular blocks with inclined undersides along the joints, and the columns break into blocks that step
    # in and out, where ours were a smooth vault and clean single boxes.
    # Roof blocks: off to either side of the passage, their undersides at 72 to 90% of the height, tilted
    # their own way, so the roof is broken planes meeting at angles.
    block = t.node('GeometryNodeMeshCube', Size=(1.0, 1.0, 1.0)).outputs["Mesh"]
    hang_h = t.math('MULTIPLY', t.named("c_tall"), rand(0.72, 0.9, 301))
    hang_d = t.math('MULTIPLY', t.named("c_tall"), 0.6)  # the block's depth, mostly up in the rock
    hang_at = t.node('GeometryNodeSetPosition', Geometry=rows.outputs[0],
                     Offset=t.vmath('ADD', t.vmath('SCALE', across_s, scale=t.math('MULTIPLY', sidev, t.math('MULTIPLY', t.named("c_radius"), rand(0.1, 0.5, 303)))),
                                    t.vec(0.0, 0.0, t.math('ADD', hang_h, t.math('MULTIPLY', hang_d, 0.5))))).outputs[0]
    hang_keep = t.math('MULTIPLY', t.math('MULTIPLY', jointed_on, t.math('LESS_THAN', rand(0.0, 1.0, 305), 0.4)),
                       t.math('MULTIPLY', t.math('GREATER_THAN', t.named("c_s"), 0.25), t.math('LESS_THAN', t.math('MULTIPLY', t.named("c_s"), has_chamber), 0.58)))  # the passage only: sized by a chamber's radius they filled its dome (Mike)
    hangs = t.node('GeometryNodeInstanceOnPoints', Points=hang_at, Selection=hang_keep, Instance=block,
                   Rotation=t.vec(rand(-0.45, 0.45, 307), rand(-0.45, 0.45, 309), t.math('ADD', yaw, rand(-0.4, 0.4, 311))),
                   Scale=t.vec(t.math('MULTIPLY', t.named("c_radius"), rand(0.5, 1.1, 313)), t.math('MULTIPLY', W, rand(0.4, 0.9, 315)), hang_d)).outputs[0]
    t.L.new(hangs, cols.inputs[0])
    # Steps on the columns: a shorter block over part of some columns, set out a little further and turned a
    # little, so a column's face steps out and back like stacked blocks.
    step_keep = t.math('MULTIPLY', slab_keep, t.math('LESS_THAN', rand(0.0, 1.0, 321), 0.6))
    step_at = t.node('GeometryNodeSetPosition', Geometry=slab_at,
                     Offset=t.vmath('ADD', t.vmath('SCALE', across_s, scale=t.math('MULTIPLY', sidev, t.math('MULTIPLY', t.named("c_radius"), rand(-0.1, -0.05, 323)))),
                                    t.vec(0.0, 0.0, t.math('MULTIPLY', t.named("c_tall"), rand(-0.35, 0.35, 325))))).outputs[0]
    steps = t.node('GeometryNodeInstanceOnPoints', Points=step_at, Selection=step_keep, Instance=column,
                   Rotation=t.vec(rand(-0.04, 0.04, 327), rand(-0.04, 0.04, 329), t.math('ADD', yaw, rand(-0.2, 0.2, 331))),
                   Scale=t.vec(t.math('MULTIPLY', thick, 0.5), t.math('MULTIPLY', W, rand(0.15, 0.35, 333)), t.math('MULTIPLY', t.named("c_tall"), rand(0.12, 0.3, 335)))).outputs[0]
    t.L.new(steps, cols.inputs[0])
    # Teardrops (Mike, from the rockfall cave: big flat-faced slabs wide at the top that narrow down the wall
    # to a rounded point partway down): now and then a four-sided wedge on the passage wall, wide near the
    # roof, tapering to a small blunt foot a sixth to a third of the way up, standing out about as far as the
    # columns.
    # A box whose lower face is pinched to 15% of its width: a flat front face the same depth all the way
    # down, narrowing to a blunt foot (a cone narrowed in depth too and sank back into the wall).
    drop_box = t.node('GeometryNodeMeshCube', Size=(2.0, 2.0, 2.0)).outputs["Mesh"]
    bp = t.xyz(t.position())
    drop_cone = t.node('GeometryNodeSetPosition', Geometry=drop_box, Selection=t.math('LESS_THAN', bp["Z"], 0.0),
                       Position=t.vec(bp["X"], t.math('MULTIPLY', bp["Y"], 0.15), bp["Z"])).outputs[0]
    drop_h = t.math('MULTIPLY', t.named("c_tall"), rand(0.25, 0.4, 341))  # half its height
    drop_at = t.node('GeometryNodeSetPosition', Geometry=slab_at,
                     Offset=t.vmath('ADD', t.vmath('SCALE', across_s, scale=t.math('MULTIPLY', sidev, t.math('MULTIPLY', t.named("c_radius"), rand(-0.06, 0.0, 343)))),
                                    t.vec(0.0, 0.0, t.math('MULTIPLY', t.named("c_tall"), 0.05)))).outputs[0]  # centred at 55% of the height
    drop_keep = t.math('MULTIPLY', t.math('MULTIPLY', jointed_on, t.math('LESS_THAN', rand(0.0, 1.0, 345), 0.5)),
                      t.math('MULTIPLY', t.math('GREATER_THAN', t.named("c_s"), 0.3), t.math('LESS_THAN', t.math('MULTIPLY', t.named("c_s"), has_chamber), 0.58)))  # standing passage wall (behind a chamber's dome they were buried)
    drops = t.node('GeometryNodeInstanceOnPoints', Points=drop_at, Selection=drop_keep, Instance=drop_cone,
                   Rotation=t.vec(rand(-0.05, 0.05, 347), rand(-0.05, 0.05, 349), t.math('ADD', yaw, rand(-0.15, 0.15, 351))),
                   Scale=t.vec(t.math('MULTIPLY', thick, 0.5), t.math('MULTIPLY', W, rand(0.4, 0.8, 353)), drop_h)).outputs[0]
    t.L.new(drops, cols.inputs[0])
    # Limestone, primary shapes (from the Mammoth passage reference, docs/m5/ref_limestone_shapes.jpg): the
    # walls are stacks of thick beds, each standing out or set back from the one below like stacked plates, and
    # the roof is broad flat planes stepping between beds. Flat rock plates set into both walls at three bed
    # levels, and flat blocks under the roof that cut it level, as the cave's shape is built.
    lime_on = t.math('MULTIPLY', t.math('LESS_THAN', gin["Rock"], 0.5), t.math('GREATER_THAN', gin["Wall Shape"], 0.0))
    beds = t.node('GeometryNodeDuplicateElements', Geometry=rows.outputs[0], Amount=2)
    beds.domain = 'POINT'
    level = beds.outputs["Duplicate Index"]  # 0, 1, 2 up the wall
    bed_h = t.math('MULTIPLY', t.named("c_tall"), t.math('ADD', 0.22, t.math('MULTIPLY', level, 0.22)))  # lowest above the floor (it hung onto it)
    bed_in = t.math('MULTIPLY', t.named("c_radius"), t.math('MULTIPLY', rand(0.03, 0.28, 261), t.math('MINIMUM', t.math('MULTIPLY', gin["Wall Shape"], 1.6), 1.0)))
    bed_out = t.math('ADD', t.math('SUBTRACT', wall_d.outputs[0], bed_in), t.math('MULTIPLY', thick, 0.4))
    bed_at = t.node('GeometryNodeSetPosition', Geometry=beds.outputs["Geometry"],
                    Offset=t.vmath('ADD', t.vmath('SCALE', across_s, scale=t.math('MULTIPLY', sidev, bed_out)), t.vec(0.0, 0.0, bed_h))).outputs[0]
    bed_keep = t.math('MULTIPLY', t.math('MULTIPLY', lime_on, t.math('LESS_THAN', rand(0.0, 1.0, 263), 0.55)),
                      t.math('MULTIPLY', t.math('GREATER_THAN', t.named("c_s"), 0.2), t.math('LESS_THAN', t.math('MULTIPLY', t.named("c_s"), has_chamber), 0.58)))
    plates = t.node('GeometryNodeInstanceOnPoints', Points=bed_at, Selection=bed_keep, Instance=cube, Pick_Instance=True, Instance_Index=pick(265),
                    Rotation=t.vec(rand(-0.05, 0.05, 267), rand(-0.05, 0.05, 269), t.math('ADD', yaw, rand(-0.15, 0.15, 271))),
                    Scale=t.vec(t.math('MULTIPLY', thick, 0.48), t.math('MULTIPLY', W, rand(0.72, 1.56, 273)), t.math('MULTIPLY', t.named("c_tall"), 0.16))).outputs[0]  # +20% (Mike: more slab-like)
    t.L.new(plates, solids.inputs[0])
    # The roof: flat blocks whose undersides sit at 72 to 88% of the section's height, a few per passage, so the
    # roof is level planes stepping between beds.
    roof_keep = t.math('MULTIPLY', t.math('MULTIPLY', lime_on, t.math('LESS_THAN', rand(0.0, 1.0, 281), 0.25)),
                       t.math('MULTIPLY', t.math('GREATER_THAN', t.named("c_s"), 0.15), t.math('LESS_THAN', t.math('MULTIPLY', t.named("c_s"), has_chamber), 0.58)))
    roof_h = t.math('MULTIPLY', t.named("c_tall"), rand(0.74, 0.9, 283))
    roof_at = t.node('GeometryNodeSetPosition', Geometry=path, Offset=t.vec(0.0, 0.0, t.math('ADD', roof_h, t.named("c_tall")))).outputs[0]
    slab = t.node('GeometryNodeMeshCube', Size=(1.0, 1.0, 1.0)).outputs["Mesh"]
    roofs = t.node('GeometryNodeInstanceOnPoints', Points=roof_at, Selection=roof_keep, Instance=slab,
                   Rotation=t.vec(0.0, 0.0, t.math('ADD', yaw, rand(-0.3, 0.3, 285))),
                   Scale=t.vec(t.math('MULTIPLY', t.named("c_radius"), 2.6), t.math('MULTIPLY', W, rand(0.96, 1.92, 287)), t.math('MULTIPLY', t.named("c_tall"), 2.0))).outputs[0]
    t.L.new(roofs, solids.inputs[0])
    boulders = t.node('GeometryNodeJoinGeometry')
    for g in rubble_sets:  # the ramp's scree is off while the walls are dialled in (Mike: rocks on the ground only)
        t.L.new(g, boulders.inputs[0])

    # Space minus rock: the domes' space as one signed-distance field, the rubble and ramp taken out of it
    # (merging the rocks into the space carved hollows into the walls instead of piling rock at their foot).
    rubble_all, _ramp_skin = level_set(solids.outputs[0])
    # A walkway no mass may fill, whatever the rock and settings: a tube along the path from the floor to just
    # over head height (2.2 m, or 60% of a small passage's half width) (a long limestone plate on a tight bend once cut right across the
    # passage and the cave ended there).
    # It stops where a ramp starts down (it would cut a step into the ramp's slope).
    clear_pts = t.node('GeometryNodeDeleteGeometry', Geometry=path,
                       Selection=t.math('MULTIPLY', ramp_on, t.math('GREATER_THAN', t.xyz(t.position())["Y"],
                       t.math('MAXIMUM', y06, t.math('ADD', y0, W)))))  # never the whole tube: an empty one wipes the cave
    clear_pts.domain = 'POINT'
    clear_c = t.node('GeometryNodeMeshToCurve', Mesh=clear_pts.outputs[0]).outputs[0]
    # A person, about 2.2 m clear, but never under a voxel and a fifth: thinner, the tube vanished as the shape
    # was built and roof blocks sealed the passage, so the cave's front was dropped as a loose piece.
    walk_r = t.math('MAXIMUM', t.math('MINIMUM', t.math('MULTIPLY', t.named("c_narrow"), 0.3), 1.1), t.math('MULTIPLY', voxel, 1.2))
    clear_c = t.node('GeometryNodeSetPosition', Geometry=clear_c, Offset=t.vec(0.0, 0.0, walk_r)).outputs[0]
    clear_c = t.node('GeometryNodeSetCurveRadius', Curve=clear_c, Radius=walk_r).outputs[0]
    clear_tube = t.node('GeometryNodeCurveToMesh', Curve=clear_c, Profile_Curve=t.node('GeometryNodeCurvePrimitiveCircle', Resolution=12, Radius=1.0).outputs["Curve"],
                        Fill_Caps=True).outputs[0]
    # And down the ramp, along its top (Mike: past where the first tube stops, roof blocks sealed the passage
    # and the cave's front was dropped as a loose piece): the same tube, resting on the ramp's walkway.
    ramp_walk = t.node('GeometryNodeDeleteGeometry', Geometry=ramp_c,
                       Selection=t.math('LESS_THAN', t.math('MULTIPLY', ramp_on, t.math('GREATER_THAN', t.xyz(t.position())["Y"], t.math('SUBTRACT', y06, W))), 0.5))
    ramp_walk.domain = 'POINT'
    ramp_walk = t.node('GeometryNodeSetPosition', Geometry=ramp_walk.outputs[0],
                       Position=t.vec(t.xyz(t.position())["X"], t.xyz(t.position())["Y"], t.math('ADD', t.named("c_rtop"), walk_r))).outputs[0]
    ramp_walk = t.node('GeometryNodeSetCurveRadius', Curve=ramp_walk, Radius=walk_r).outputs[0]
    ramp_tube = t.node('GeometryNodeCurveToMesh', Curve=ramp_walk, Profile_Curve=t.node('GeometryNodeCurvePrimitiveCircle', Resolution=12, Radius=1.0).outputs["Curve"],
                       Fill_Caps=True).outputs[0]
    tubes = t.node('GeometryNodeJoinGeometry')
    t.L.new(clear_tube, tubes.inputs[0])
    t.L.new(ramp_tube, tubes.inputs[0])
    clear_grid, _tubes_skin = level_set(tubes.outputs[0])
    # Jointed pieces (Mike: separate pieces for better AO and a better jointed look, but looking like the rest
    # of the cave, not plain cubes, and reaching only a little past it): the masses as one shape of their own,
    # trimmed to the cave's space grown by a voxel (so they sink just into the walls, floor and roof) and kept
    # out of the walkway. Joined to the shell below, they go through the same snapping, smoothing and rock
    # detail as the walls, but stay their own pieces.
    all_pieces = t.node('GeometryNodeJoinGeometry')
    t.L.new(carved, all_pieces.inputs[0])
    pieces_all, _pieces_skin = level_set(all_pieces.outputs[0])
    room = t.node('GeometryNodeSDFGridOffset', Grid=space, Distance=t.math('MULTIPLY', voxel, 3.0)).outputs[0]  # grown into the rock (positive grows; at 1.5 the feet stopped at the floor)
    in_room = t.N.new('GeometryNodeSDFGridBoolean')
    in_room.operation = 'INTERSECT'
    t.L.new(room, in_room.inputs["Grid"])
    t.L.new(pieces_all, in_room.inputs["Grid"])
    clear_pieces = t.N.new('GeometryNodeSDFGridBoolean')
    clear_pieces.operation = 'DIFFERENCE'
    t.L.new(in_room.outputs[0], clear_pieces.inputs["Grid 1"])
    t.L.new(clear_grid, clear_pieces.inputs["Grid 2"])
    pieces_mesh = t.node('GeometryNodeGridToMesh', Grid=clear_pieces.outputs[0]).outputs[0]
    pieces_mesh = t.node('GeometryNodeDeleteGeometry', Geometry=pieces_mesh, Selection=t.math('LESS_THAN', jointed_on, 0.5)).outputs[0]
    # Slivers where a box's corner only just reaches into the margin are dropped (under 5% of the biggest piece).
    p_island = t.node('GeometryNodeInputMeshIsland').outputs["Island Index"]
    p_count = t.node('GeometryNodeAccumulateField', Value=1.0, Group_ID=p_island)
    p_count.domain = 'POINT'
    p_big = t.node('GeometryNodeAttributeStatistic', Geometry=pieces_mesh, Attribute=p_count.outputs["Total"])
    p_big.domain = 'POINT'
    pieces_mesh = t.node('GeometryNodeDeleteGeometry', Geometry=pieces_mesh,
                         Selection=t.math('LESS_THAN', p_count.outputs["Total"], t.math('MULTIPLY', p_big.outputs["Max"], 0.05))).outputs[0]
    pieces_mesh = t.store(pieces_mesh, "lg_piece", True, 'BOOLEAN', 'POINT')
    keep_clear = t.N.new('GeometryNodeSDFGridBoolean')
    keep_clear.operation = 'DIFFERENCE'
    t.L.new(rubble_all, keep_clear.inputs["Grid 1"])
    t.L.new(clear_grid, keep_clear.inputs["Grid 2"])
    rubble = keep_clear.outputs[0]
    carve = t.N.new('GeometryNodeSDFGridBoolean')
    carve.operation = 'DIFFERENCE'
    t.L.new(space, carve.inputs["Grid 1"])
    t.L.new(rubble, carve.inputs["Grid 2"])
    rounded = t.node('GeometryNodeSDFGridFillet', Grid=carve.outputs[0], Iterations=1)  # closes thin slits (pinches)
    # No ramp: nothing to take out (taking out an empty grid wiped the whole cave).
    plain = t.node('GeometryNodeGridToMesh', Grid=t.node('GeometryNodeSDFGridFillet', Grid=space, Iterations=1).outputs[0]).outputs[0]
    with_ramp = t.node('GeometryNodeGridToMesh', Grid=rounded.outputs[0]).outputs[0]
    pick_mesh = t.N.new('GeometryNodeSwitch')
    pick_mesh.input_type = 'GEOMETRY'
    t._set(pick_mesh.inputs['Switch'], t.math('GREATER_THAN', t.math('ADD', ramp_on, lime_on), 0.5))  # nothing cut in: plain
    t.L.new(plain, pick_mesh.inputs['False'])
    t.L.new(with_ramp, pick_mesh.inputs['True'])
    merged = pick_mesh.outputs[0]

    # One piece: drop any loose bits (on the coarse shape, before it is subdivided).
    island = t.node('GeometryNodeInputMeshIsland').outputs["Island Index"]
    acc = t.node('GeometryNodeAccumulateField', Value=1.0, Group_ID=island)
    acc.domain = 'POINT'
    biggest = t.node('GeometryNodeAttributeStatistic', Geometry=merged, Attribute=acc.outputs["Total"])
    biggest.domain = 'POINT'
    loose = t.node('GeometryNodeDeleteGeometry', Geometry=merged,
                   Selection=t.math('LESS_THAN', acc.outputs["Total"], t.math('SUBTRACT', biggest.outputs["Max"], 0.5)))
    loose.domain = 'POINT'
    # Shell density (D105, Mike: the walls were too few faces to hold rock detail): the voxels only set the
    # cave's shape; the shell is then smoothly subdivided (each step x4 faces) toward about 150k / 4M / 16M faces
    # (Preview / High / Ultra), but never fewer than 2 / 4 / 5 steps: a big cave rounded to High's steps at
    # Ultra and lost its detail (Mike), a small one needs more steps to reach the target.
    def per_level(values):
        n = t.N.new('GeometryNodeIndexSwitch')
        n.data_type = 'FLOAT'
        while len(n.index_switch_items) < len(values):
            n.index_switch_items.new()
        t._set(n.inputs["Index"], gin["Detail"])
        for i, v in enumerate(values):
            n.inputs[i + 1].default_value = float(v)
        return n.outputs[0]

    # Jointed columns keep flat faces and crisp edges (Mike: they came out round; the shape's voxels, metres
    # across, bevel every corner): points of the shell within a voxel of a column's face are put back onto it.
    near_col = t.node('GeometryNodeProximity', Geometry=carved,
                      Source_Position=t.position())
    near_col.target_element = 'FACES'
    # Only points that move mostly in or out to the face: one pulled sideways onto a column's edge spiked.
    to_col = t.vmath('NORMALIZE', t.vmath('SUBTRACT', near_col.outputs["Position"], t.position()))
    straight = t.math('GREATER_THAN', t.math('ABSOLUTE', t.vmath('DOT_PRODUCT', to_col, t.node('GeometryNodeInputNormal').outputs[0])), 0.55)
    on_col = t.math('MULTIPLY', t.math('MULTIPLY', t.math('MULTIPLY', t.named("lg_piece", 'BOOLEAN'), jointed_on), straight),  # only jointed blocks to snap to (with none, all went to the origin)
                    t.math('LESS_THAN', near_col.outputs["Distance"], t.math('MULTIPLY', voxel, 0.9)))
    shell_pieces = t.node('GeometryNodeJoinGeometry')
    t.L.new(loose.outputs[0], shell_pieces.inputs[0])
    t.L.new(pieces_mesh, shell_pieces.inputs[0])
    before = t.store(t.store(shell_pieces.outputs[0], "lg_p0", t.position(), 'FLOAT_VECTOR'), "lg_n0", t.node('GeometryNodeInputNormal').outputs[0], 'FLOAT_VECTOR')
    snapped = t.node('GeometryNodeSetPosition', Geometry=before, Selection=on_col, Position=near_col.outputs["Position"]).outputs[0]
    # Any face the snap turned over (where columns crowd together) has its points put back where they were.
    flipped = t.N.new('GeometryNodeFieldOnDomain')
    flipped.domain, flipped.data_type = 'FACE', 'FLOAT'
    t._set(flipped.inputs[0], t.math('LESS_THAN', t.vmath('DOT_PRODUCT', t.node('GeometryNodeInputNormal').outputs[0], t.named("lg_n0", 'FLOAT_VECTOR')), 0.2))
    squared = t.node('GeometryNodeSetPosition', Geometry=snapped, Selection=t.math('GREATER_THAN', flipped.outputs[0], 0.0),
                     Position=t.named("lg_p0", 'FLOAT_VECTOR')).outputs[0]
    squared = t.node('GeometryNodeRemoveAttribute', Geometry=t.node('GeometryNodeRemoveAttribute', Geometry=squared, Name="lg_p0").outputs[0], Name="lg_n0").outputs[0]
    faces = t.node('GeometryNodeAttributeDomainSize', Geometry=squared).outputs["Face Count"]
    aim = t.math('ROUND', t.math('LOGARITHM', t.math('DIVIDE', per_level(CAVE_FACES), t.math('MAXIMUM', faces, 1.0)), 4.0))
    levels = t.math('MINIMUM', t.math('MAXIMUM', aim, per_level(CAVE_SUBDIV)), 6.0)
    # Sharp edges stay sharp (Mike: the jointed masses came out soft): edges where the faces meet at a real
    # angle are creased before smoothing, so broad flat faces keep crisp ridges between them.
    bend = t.node('GeometryNodeInputMeshEdgeAngle').outputs["Unsigned Angle"]
    # A lava tube is one smooth bore (Thurston, Lava River Cave): the shape's domes left rings at their joins,
    # which the wall noise drew out into ribs, so for lava the coarse shell is smoothed a few passes first.
    bore = t.N.new('GeometryNodeBlurAttribute')
    bore.data_type = 'FLOAT_VECTOR'  # before linking: the type swaps the sockets
    t._set(bore.inputs["Value"], t.position())
    bore.inputs["Iterations"].default_value = 12  # Mike: at 6, the grid's steps showed as faint rings on the walls at Ultra
    squared = t.node('GeometryNodeSetPosition', Geometry=squared, Selection=t.math('MULTIPLY', t.math('GREATER_THAN', gin["Rock"], 1.5), t.math('LESS_THAN', t.named("lg_piece", 'BOOLEAN'), 0.5)), Position=bore.outputs["Value"]).outputs[0]
    # Tube coordinates (Mike: the noise and the texture maps read the cave like a UV unwrap, the floor as one
    # piece and the walls as strips along the tube; 3D noise sliced by the curved wall left rings): for each point
    # of the coarse shell, how far along the tube, out to the side of its centre line and up over its floor,
    # measured from the nearest point on the path's line (between its points: from the nearest point itself, the
    # measures stepped wherever the nearest point changed, which ribbed the walls every few metres, Mike), with
    # that section's radius and height. Blurred over the shell, so wherever the nearest bit of the line jumps (a
    # bend, the chamber) they ease instead of stepping; the subdivision carries them onto the fine faces.
    t_near = t.node('GeometryNodeSampleNearest', Geometry=path, Sample_Position=t.position()).outputs[0]

    def t_at(value, k, data_type='FLOAT'):
        n = t.N.new('GeometryNodeSampleIndex')
        n.data_type, n.domain = data_type, 'POINT'
        t._set(n.inputs["Geometry"], path)
        t._set(n.inputs["Value"], value)
        t._set(n.inputs["Index"], t.math('MINIMUM', t.math('MAXIMUM', t.math('ADD', t_near, k), 0.0), t.math('SUBTRACT', count, 1.0)))
        return n.outputs[0]

    def t_seg(k):
        """The nearest point on the path's segment from point k to k + 1: (how far along it 0..1, distance)."""
        a, b = t_at(t.position(), k, 'FLOAT_VECTOR'), t_at(t.position(), k + 1.0, 'FLOAT_VECTOR')
        ab = t.vmath('SUBTRACT', b, a)
        f = t.math('DIVIDE', t.vmath('DOT_PRODUCT', t.vmath('SUBTRACT', t.position(), a), ab), t.math('MAXIMUM', t.vmath('DOT_PRODUCT', ab, ab), 1e-6))
        f = t.math('MINIMUM', t.math('MAXIMUM', f, 0.0), 1.0)
        return f, t.vmath('DISTANCE', t.position(), t.vmath('ADD', a, t.vmath('SCALE', ab, scale=f)))

    f_back, d_back = t_seg(-1.0)
    f_on, d_on = t_seg(0.0)
    behind_seg = t.math('LESS_THAN', d_back, d_on)

    def t_path(value, data_type='FLOAT'):
        """value along the path's line at the nearest point on it."""
        a0, a1, a2 = (t_at(value, k, data_type) for k in (-1.0, 0.0, 1.0))
        if data_type == 'FLOAT':
            back = t.math('ADD', a0, t.math('MULTIPLY', t.math('SUBTRACT', a1, a0), f_back))
            on = t.math('ADD', a1, t.math('MULTIPLY', t.math('SUBTRACT', a2, a1), f_on))
        else:
            back = t.vmath('ADD', a0, t.vmath('SCALE', t.vmath('SUBTRACT', a1, a0), scale=f_back))
            on = t.vmath('ADD', a1, t.vmath('SCALE', t.vmath('SUBTRACT', a2, a1), scale=f_on))
        n = t.N.new('GeometryNodeSwitch')
        n.input_type = data_type if data_type == 'FLOAT' else 'VECTOR'
        t._set(n.inputs["Switch"], behind_seg)
        t._set(n.inputs["False"], on)
        t._set(n.inputs["True"], back)
        return n.outputs[0]

    t_off = t.vmath('SUBTRACT', t.position(), t_path(t.position(), 'FLOAT_VECTOR'))
    t_ac = t.vmath('NORMALIZE', t_path(t.named("c_across", 'FLOAT_VECTOR'), 'FLOAT_VECTOR'))
    t_acx = t.xyz(t_ac)
    t_along = t.math('ADD', t_path(t.named("c_len")), t.vmath('DOT_PRODUCT', t_off, t.vec(t.math('MULTIPLY', t_acx["Y"], -1.0), t_acx["X"], 0.0)))
    tube = t.vec(t_along, t.vmath('DOT_PRODUCT', t_off, t_ac), t.xyz(t_off)["Z"])
    tube_r = t.vec(t_path(t.named("c_radius")), t_path(t.named("c_tall")), t_path(t.named("c_ch")))  # and how far into the chamber
    for t_name, t_val in (("lg_tube", tube), ("lg_tube_r", tube_r)):
        t_blur = t.N.new('GeometryNodeBlurAttribute')
        t_blur.data_type = 'FLOAT_VECTOR'  # before linking: the type swaps the sockets
        t._set(t_blur.inputs["Value"], t_val)
        t_blur.inputs["Iterations"].default_value = 16
        squared = t.store(squared, t_name, t_blur.outputs["Value"], 'FLOAT_VECTOR')
    # Where the passage runs into a chamber, the merged domes left a sharp inside corner from floor to roof (Mike:
    # a pinched crease): the shell is smoothed hard there only, between the passage and the chamber (by how far into
    # the chamber, from the tube coordinates), so the join rounds into a broad curve like a mouth carved wider.
    j_ch = t.xyz(t.named("lg_tube_r", 'FLOAT_VECTOR'))["Z"]
    join = t.math('MULTIPLY', t.smooth(j_ch, 0.05, 0.3), t.math('SUBTRACT', 1.0, t.smooth(j_ch, 0.97, 0.995)))  # the crease sits where the passage flares into the dome, 80-98% in
    # Spread over the shell: by the chamber measure alone its far edge fell within a few metres (it saturates in the
    # chamber), and the hand-over there stood up as a rib.
    j_spread = t.N.new('GeometryNodeBlurAttribute')
    j_spread.data_type = 'FLOAT'
    t._set(j_spread.inputs["Value"], join)
    t._set(j_spread.inputs["Iterations"], t.node('FunctionNodeFloatToInt', Float=t.math('MULTIPLY', 60.0, t.math('POWER', t.math('DIVIDE', per.outputs[0], CAVE_DETAIL[0]), 2.0))).outputs[0])
    squared = t.store(squared, "lg_join", t.math('MINIMUM', t.math('MULTIPLY', j_spread.outputs["Value"], 1.5), 1.0))
    join = t.named("lg_join")
    j_blur = t.N.new('GeometryNodeBlurAttribute')
    j_blur.data_type = 'FLOAT_VECTOR'  # before linking: the type swaps the sockets
    t._set(j_blur.inputs["Value"], t.position())
    # The same reach at every Detail Level: finer grids take more passes (by the square of the cells across).
    t._set(j_blur.inputs["Iterations"], t.node('FunctionNodeFloatToInt', Float=t.math('MULTIPLY', 40.0, t.math('POWER', t.math('DIVIDE', per.outputs[0], CAVE_DETAIL[0]), 2.0))).outputs[0])
    squared = t.node('GeometryNodeSetPosition', Geometry=squared, Selection=t.math('LESS_THAN', t.named("lg_piece", 'BOOLEAN'), 0.5),
                     Offset=t.vmath('SCALE', t.vmath('SUBTRACT', j_blur.outputs["Value"], t.position()), scale=join)).outputs[0]

    # The UV map (Mike: square, no stretching; split only where the cave splits naturally, never into lots of small
    # islands): unwrapped on the coarse shell, the subdivision carries it onto the fine faces. Islands: the mouth's
    # end, the passage floor, the passage walls and roof as one strip, the back end, and in a chamber its floor, its
    # roof and its walls in two halves (a ring of wall needs a cut; the halves meet front and back). Loose pieces
    # (jointed blocks) split by which way each face looks, like a box.
    def face_of(value):
        n = t.N.new('GeometryNodeFieldOnDomain')
        n.domain, n.data_type = 'FACE', 'FLOAT'
        t._set(n.inputs[0], value)
        return n.outputs[0]

    def pick(cond, yes, no):
        n = t.N.new('GeometryNodeSwitch')
        n.input_type = 'FLOAT'
        t._set(n.inputs["Switch"], t.math('GREATER_THAN', cond, 0.5))
        t._set(n.inputs["False"], no)
        t._set(n.inputs["True"], yes)
        return n.outputs[0]

    ft, fr = t.xyz(t.named("lg_tube", 'FLOAT_VECTOR')), t.xyz(t.named("lg_tube_r", 'FLOAT_VECTOR'))
    f_along, f_side, f_up = face_of(ft["X"]), face_of(ft["Y"]), face_of(ft["Z"])
    f_tall, f_ch = face_of(fr["Y"]), face_of(fr["Z"])
    p_end = t.node('GeometryNodeAttributeStatistic', Geometry=path, Attribute=t.named("c_len"))
    p_end.data_type, p_end.domain = 'FLOAT', 'POINT'
    is_floor = t.math('LESS_THAN', f_up, t.math('MULTIPLY', f_tall, 0.08))  # the floor is flat on the coarse shell
    in_chamber = pick(is_floor, 2.0, pick(t.math('GREATER_THAN', f_up, t.math('MULTIPLY', f_tall, 0.7)), 3.0,
                                         pick(t.math('GREATER_THAN', f_side, 0.0), 4.0, 5.0)))
    in_passage = pick(t.math('GREATER_THAN', f_along, p_end.outputs["Max"]), 6.0, pick(is_floor, 7.0, 8.0))
    shell_part = pick(t.math('LESS_THAN', f_along, 0.0), 1.0, pick(t.math('GREATER_THAN', f_ch, 0.5), in_chamber, in_passage))
    fn = t.xyz(t.node('GeometryNodeInputNormal').outputs[0])
    box = t.math('ADD', t.math('ADD', t.math('ROUND', fn["X"]), t.math('MULTIPLY', t.math('ROUND', fn["Y"]), 3.0)),
                 t.math('MULTIPLY', t.math('ROUND', fn["Z"]), 9.0))
    part = pick(t.named("lg_piece", 'BOOLEAN'), t.math('ADD', box, 30.0), shell_part)
    # A seam on every edge between two faces of different parts (the parts' mean and mean square disagree there).
    e_mean = t.N.new('GeometryNodeFieldOnDomain')
    e_mean.domain, e_mean.data_type = 'EDGE', 'FLOAT'
    e_sq = t.N.new('GeometryNodeFieldOnDomain')
    e_sq.domain, e_sq.data_type = 'EDGE', 'FLOAT'
    f_part = t.N.new('GeometryNodeFieldOnDomain')
    f_part.domain, f_part.data_type = 'FACE', 'FLOAT'
    t._set(f_part.inputs[0], part)
    t._set(e_mean.inputs[0], f_part.outputs[0])
    t._set(e_sq.inputs[0], face_of(t.math('MULTIPLY', part, part)))  # squared on the faces, then averaged
    seam = t.math('GREATER_THAN', t.math('SUBTRACT', e_sq.outputs[0], t.math('MULTIPLY', e_mean.outputs[0], e_mean.outputs[0])), 0.01)
    unwrap = t.node('GeometryNodeUVUnwrap', Seam=seam, Margin=0.005)
    unwrap.inputs["Method"].default_value = 'Minimum Stretch'
    squared = t.store(squared, "UVMap", unwrap.outputs["UV"], 'FLOAT2', 'CORNER')
    squared = t.store(squared, "lg_uv_part", part, 'FLOAT', 'FACE')
    # How sharp the coarse shape is at each point (the bed plates' creased edges), spread a little, so the rock
    # detail can ease off there: pushed over a crease the surface folded into lips and the block scars zippered (Mike).
    sharp_b = t.N.new('GeometryNodeBlurAttribute')
    sharp_b.data_type = 'FLOAT'
    t._set(sharp_b.inputs["Value"], t.smooth(bend, 0.35, 0.8))
    sharp_b.inputs["Iterations"].default_value = 3
    squared = t.store(squared, "lg_sharp", sharp_b.outputs["Value"])
    dense = t.node('GeometryNodeSubdivisionSurface', Mesh=squared, Edge_Crease=t.math('MULTIPLY', t.smooth(bend, 0.35, 0.8), t.math('COMPARE', gin["Rock"], 1.0)),  # jointed rock only: a lava tube stays smooth (creases ringed it at the domes' joins), and on limestone the creases ending mid-wall pinched the bed plates' edges into lips (D161)
                   Level=t.node('FunctionNodeFloatToInt', Float=levels).outputs[0]).outputs[0]

    # Wall volume by Rock (D115, Mike: primary and secondary volume in the mesh; ledges, bands and fine lines
    # go to the textures). The floor (faces looking down, out of the cave's space) stays a walkable, gently
    # uneven floor. On the walls and roof:
    #   primary: the big forms, bulges, recesses and alcoves at the passage's scale (Wall Shape),
    #   secondary: the broken rock on them, a metre or so (Roughness),
    # each shaped by the rock: limestone long and horizontal with a flat roof, jointed rock in flat-faced blocks
    # between straight fractures, a lava tube smooth and drawn out along the tube.
    nrm = t.node('GeometryNodeInputNormal').outputs[0]
    nz = t.xyz(nrm)["Z"]
    # The wall is pushed out along the normal blurred over a few faces, not the raw one (Mike's folded seam):
    # at a sharp inside corner the raw normals on its two sides cross, so pushing along them folded the
    # surface through itself. Blurred, they turn the corner together; the creases stay sharp.
    push_blur = t.N.new('GeometryNodeBlurAttribute')
    push_blur.data_type = 'FLOAT_VECTOR'  # before linking: the type swaps the sockets
    t._set(push_blur.inputs["Value"], nrm)
    t._set(push_blur.inputs["Iterations"], t.node('FunctionNodeFloatToInt', Float=t.math('POWER', 2.0, t.math('ADD', levels, 2.0))).outputs[0])
    push = t.vmath('NORMALIZE', push_blur.outputs["Value"])
    # A rock piece's normals point out of it, into the cave (the shell's point into the rock), so for a piece the
    # floor test is flipped: read as the shell's, every piece's underside counted as floor and got no rock detail,
    # a smooth pillow (Mike).
    nz_rock = t.math('MULTIPLY', nz, t.math('SUBTRACT', 1.0, t.math('MULTIPLY', t.named("lg_piece", 'BOOLEAN'), 2.0)))
    wall = t.smooth(nz_rock, -0.93, -0.7)  # not the floor; down to near-flat ground (Mike: the wall foot looked melted)
    upright = t.math('SUBTRACT', 1.0, t.smooth(t.math('ABSOLUTE', nz), 0.55, 0.9))  # standing walls only
    R, F = gin["Roughness"], gin["Wall Shape"]
    # Seeded by at most 100 m: by the whole seed (hundreds of thousands) the noise lost precision, and every sharp
    # ridge read off it (the jointed folds) jittered into zipper stitches (Mike's pinching, D164).
    sp = t.vmath('ADD', t.position(), t.vec(t.math('FLOORED_MODULO', seed, 100.0), t.math('MULTIPLY', t.math('FLOORED_MODULO', seed, 100.0), 0.7), 0.0))
    pz = t.xyz(t.position())

    # Lava tube benches, cut into the shell (Mike: as separate pieces they broke into floating bits and flat
    # slabs in a big cave): along both walls the floor rises into a broad, rounded curb where the flowing lava
    # cooled at its edges, swelling and narrowing along the tube. Raised, not pushed out from the wall: pushed
    # sideways, the curved wall foot folded into stripes. Measured from the nearest point of the path: how far
    # out from it (the wall is about its radius out) and how high over its floor.
    near = t.node('GeometryNodeSampleNearest', Geometry=path, Sample_Position=t.position()).outputs[0]

    def on_path(value, data_type='FLOAT'):
        n = t.N.new('GeometryNodeSampleIndex')
        n.data_type, n.domain = data_type, 'POINT'
        t._set(n.inputs["Geometry"], path)
        t._set(n.inputs["Value"], value)
        t._set(n.inputs["Index"], near)
        return n.outputs[0]

    p_s = on_path(t.named("c_s"))
    # Height over the floor, from the tube coordinates (a ray cast straight down jumped between surfaces by the
    # bulging wall foot, and the lift folded the wall into slits there, Mike; before that, the path's own floor
    # jumped 31 m at a sunk chamber).
    up_floor = t.xyz(t.named("lg_tube", 'FLOAT_VECTOR'))["Z"]
    over_floor = t.math('MAXIMUM', up_floor, 0.0)
    bench_in = t.math('MULTIPLY', t.math('MULTIPLY', t.smooth(p_s, 0.1, 0.25), t.math('SUBTRACT', 1.0, t.smooth(p_s, 0.84, 0.9))),  # eased in over ~15% of the path (Mike: it stood up from the floor in a step by the mouth)
                      t.math('SUBTRACT', 1.0, t.math('MULTIPLY', has_chamber, t.smooth(p_s, 0.5, 0.56))))  # eased out before the chamber and the ends
    b_swell = t.node('ShaderNodeTexNoise', Vector=t.vmath('DIVIDE', sp, t.vec(W, W, W)), Scale=0.8, Detail=1.0)
    b_swell.noise_dimensions = '3D'
    # Sized to the entrance (the passage's own radius jumps to the chamber's between two path points, and that
    # tore a seam down the wall).
    b_wide = t.math('MULTIPLY', t.math('MULTIPLY', r, t.math('ADD', 0.144, t.math('MULTIPLY', F, 0.192))),  # Wall Shape: a slim curb (0) to a broad bench (1)
                    t.math('ADD', 0.35, t.math('MULTIPLY', t.smooth(b_swell.outputs["Fac"], 0.3, 0.6), 0.65)))
    b_top = t.math('MULTIPLY', b_wide, 0.6)
    # How near the wall: the cave space's distance to its nearest side from a point a bench-width up (the floor
    # is that far below it, so only a nearer wall counts).
    w_probe = t.N.new('GeometryNodeSampleGrid')
    w_probe.data_type = 'FLOAT'
    t._set(w_probe.inputs["Grid"], space)
    t._set(w_probe.inputs["Position"], t.vmath('ADD', t.position(), t.vec(0.0, 0.0, t.math('MULTIPLY', b_wide, 1.5))))
    to_wall = t.math('ABSOLUTE', w_probe.outputs[0])
    # Up to full height over the curb's rounded edge, then the wall foot rides up with it; faded out well up the
    # wall, slowly enough that no point is lifted past one above it (no folds).
    b_rise = t.math('SUBTRACT', 1.0, t.smooth(to_wall, t.math('MULTIPLY', b_wide, 0.4), t.math('MULTIPLY', b_wide, 1.2)))
    b_low = t.math('SUBTRACT', 1.0, t.smooth(over_floor, t.math('MULTIPLY', b_top, 1.5), t.math('MULTIPLY', b_top, 4.5)))
    # Not below the floor (a pocket under the wall foot, lifted whole, folded through itself into a slit, Mike).
    b_low = t.math('MULTIPLY', b_low, t.smooth(up_floor, t.math('MULTIPLY', b_top, -2.0), 0.0))
    # Spread over the surface, so wherever a measure jumps the lift eases instead of stepping.
    b_blur = t.N.new('GeometryNodeBlurAttribute')
    b_blur.data_type = 'FLOAT'
    t._set(b_blur.inputs["Value"], t.math('MULTIPLY', t.math('MULTIPLY', t.math('MULTIPLY', b_top, b_rise), t.math('MULTIPLY', b_low, bench_in)),
                                          t.math('COMPARE', gin["Rock"], 2.0)))
    t._set(b_blur.inputs["Iterations"], t.node('FunctionNodeFloatToInt', Float=t.math('POWER', 2.0, t.math('ADD', levels, 2.0))).outputs[0])
    bench = t.vec(0.0, 0.0, b_blur.outputs["Value"])

    def noise(sx, sy, sz, detail, amp):
        """Rock noise -0.5..0.5 times amp, stretched: sx, sy, sz are its size along X, Y (the cave) and Z."""
        n = t.node('ShaderNodeTexNoise', Vector=t.vmath('DIVIDE', sp, t.vec(sx, sy, sz)), Scale=1.0, Detail=detail, Roughness=0.6)
        n.noise_dimensions = '3D'
        return t.math('MULTIPLY', t.math('SUBTRACT', n.outputs["Fac"], 0.5), amp)

    rr = lambda k: t.math('MULTIPLY', r, k)
    grain = noise(rr(0.25), rr(0.25), rr(0.25), 3.0, rr(0.05))  # the smallest the shell shows, every rock
    floor_bump = t.math('MULTIPLY', noise(r, r, r, 4.0, 1.0), t.math('MULTIPLY', t.math('MULTIPLY', H, 0.06), R))
    floor_bump = t.math('MULTIPLY', floor_bump, t.math('SUBTRACT', 1.0, t.math('MULTIPLY', t.math('LESS_THAN', gin["Rock"], 0.5), 0.75)))  # limestone: a level silt floor (D180)

    # Lava and limestone are read in tube space (D148, Mike: 3D noise sliced by the curved wall made round shapes
    # that don't exist in lava tubes): along the tube, out to the side and up over the floor, so every form runs with the
    # tube, round its bends too. Round the arc from the roof's centre line for the walls' lines.
    tb, tr = t.xyz(t.named("lg_tube", 'FLOAT_VECTOR')), t.xyz(t.named("lg_tube_r", 'FLOAT_VECTOR'))
    # The seed moves the noise by at most 100 of its cells: by the whole seed (up to hundreds of thousands) the
    # noise was read so far out that its float steps ribbed the walls (Mike's shots).
    t_seed = t.math('FLOORED_MODULO', seed, 100.0)
    t_hn = t.math('DIVIDE', tb["Z"], t.math('MAXIMUM', tr["Y"], 1e-3))  # 0 floor .. 1 roof
    t_arc = t.math('MULTIPLY', t.math('ARCTAN2', t.math('DIVIDE', tb["Y"], t.math('MAXIMUM', tr["X"], 1e-3)), t_hn),
                   t.math('SQRT', t.math('MULTIPLY', t.math('ADD', t.math('MULTIPLY', tr["X"], tr["X"]), t.math('MULTIPLY', tr["Y"], tr["Y"])), 0.5)))

    def t_noise(sa, ss, su, detail, amp, across=None):
        """noise() in tube space: sa, ss, su its size along the tube, across it (side, or round the arc) and up."""
        q = t.vec(t.math('DIVIDE', tb["X"], sa), t.math('DIVIDE', tb["Y"] if across is None else across, ss), t.math('DIVIDE', tb["Z"], su))
        n = t.node('ShaderNodeTexNoise', Vector=t.vmath('ADD', q, t.vec(t_seed, t.math('MULTIPLY', t_seed, 0.7), 0.0)), Scale=1.0, Detail=detail, Roughness=0.6)
        n.noise_dimensions = '3D'
        return t.math('MULTIPLY', t.math('SUBTRACT', n.outputs["Fac"], 0.5), amp)

    # Limestone: long horizontal forms (the beds show in the shape, not as lines): wide shallow recesses and
    # bulges, broken rock in flat-lying slabs, and a flat roof.
    # Read in tube space (Mike: the limestone walls pinched; 3D noise sliced by the curved walls ran across the beds
    # and folded them, D158), so the beds stay level along the tube, round its bends too.
    # 40% of before: the bed plates built into the shape carry the beds now, and pushed this far on top of them
    # their edges folded into flaps (D158).
    lime_primary = t.math('ADD', t_noise(rr(3.0), rr(3.0), rr(0.8), 2.0, rr(0.28)), t_noise(rr(1.2), rr(1.2), rr(0.4), 2.0, rr(0.12)))
    roof = t.math('MULTIPLY', t.smooth(nz, 0.55, 0.85), F)  # faces looking up: the roof
    # The flat roof is the flat blocks built into the cave's shape (above); cut into height bands here as well, the
    # bands ringed a chamber's dome like a contour map and folded at their steps (Mike: pinching, D158).
    lime_off = t.math('SUBTRACT', 1.0, t.math('MULTIPLY', roof, 0.7))  # keeps the flat roof flat

    # Jointed rock (sea caves, cliffs; Mike: straight joint planes across the whole cave looked man-made): the
    # rock breaks into irregular blocks, taller than wide as the joints split it, each with its own flat face
    # tilted its own way and standing in or out, blended only along the seams so no line runs on.
    J = t.math('MINIMUM', t.math('MAXIMUM', t.math('MULTIPLY', W, 0.6), 2.0), 12.0)  # big block size

    # Primary (from the rockfall reference, docs/m5/ref_jointed_shapes.jpg): a few huge masses, long in the
    # direction they lean and all leaning the same steep way (about 70 degrees, one strike per cave), meeting at
    # long creased edges like the buttresses there.
    strike = t.math('MULTIPLY', seed, 0.61)
    lean = t.vec(t.math('MULTIPLY', t.math('COSINE', strike), 0.34), t.math('MULTIPLY', t.math('SINE', strike), 0.34), -0.94)

    def blocks(size, depth, offset, drawn=3.0, seam=0.45):
        # Seeded by at most 100 m (by the whole seed, hundreds of thousands, the cells' positions lost precision and
        # their seams sawtoothed into zippers, Mike's pinching).
        bp = t.vmath('ADD', t.position(), t.vec(t_seed, t.math('MULTIPLY', t_seed, 0.7), 0.0))
        along = t.vmath('DOT_PRODUCT', bp, lean)
        across = t.vmath('SUBTRACT', bp, t.vmath('SCALE', lean, scale=along))
        q = t.vmath('DIVIDE', t.vmath('ADD', across, t.vmath('SCALE', lean, scale=t.math('DIVIDE', along, drawn))), t.vec(size, size, size))
        # Warped, so the blocks come in all shapes and sizes (even cells read as a honeycomb).
        warp = t.node('ShaderNodeTexNoise', Vector=q, Scale=0.6, Detail=1.0)
        warp.noise_dimensions = '3D'
        q = t.vmath('ADD', q, t.vmath('SCALE', t.vmath('SUBTRACT', warp.outputs["Color"], t.vec(0.5, 0.5, 0.5)), scale=0.5))
        faces = []
        for feature in ('F1', 'F2'):
            v = t.node('ShaderNodeTexVoronoi', Vector=t.vmath('ADD', q, t.vec(offset, 0.0, 0.0)), Scale=1.0, Randomness=0.9)
            v.voronoi_dimensions, v.feature = '3D', feature
            c = v.outputs["Position"]
            # Neighbouring blocks mostly line up, with a step at only some joints (every block stepping on
            # its own read as paving or a turtle shell): depth and tilt follow a broad noise across the blocks,
            # plus a little of each block's own.
            broad = t.node('ShaderNodeTexNoise', Vector=c, Scale=0.35, Detail=1.0)
            broad.noise_dimensions = '3D'
            own = t.node('ShaderNodeTexWhiteNoise', Vector=c).outputs["Value"]
            height = t.math('ADD', t.math('MULTIPLY', broad.outputs["Fac"], 0.75), t.math('MULTIPLY', own, 0.25))
            tilt = t.vmath('SCALE', t.vmath('ADD', t.vmath('SUBTRACT', broad.outputs["Color"], t.vec(0.5, 0.5, 0.5)),
                                             t.vmath('SCALE', t.vmath('SUBTRACT', v.outputs["Color"], t.vec(0.5, 0.5, 0.5)), scale=0.4)), scale=1.4)
            off = t.vmath('SUBTRACT', t.vmath('ADD', q, t.vec(offset, 0.0, 0.0)), c)
            face = t.math('ADD', t.math('MULTIPLY', t.math('SUBTRACT', height, 0.5), depth),
                          t.math('MULTIPLY', t.vmath('DOT_PRODUCT', off, tilt), t.math('MULTIPLY', size, 0.45)))
            faces.append((face, v.outputs["Distance"]))
        (f1, d1), (f2, d2) = faces
        w = t.smooth(t.math('SUBTRACT', d2, d1), 0.0, seam)  # wide, so a step rolls over (steep ones ribbed the mesh)  # 1 inside a block, 0 on its seam
        return t.math('ADD', t.math('MULTIPLY', f1, w), t.math('MULTIPLY', t.math('MULTIPLY', t.math('ADD', f1, f2), 0.5), t.math('SUBTRACT', 1.0, w)))

    joint_primary = t.math('MULTIPLY', grain, 0.0)  # the primary shapes are the masses cut into the cave's shape (above)
    # Secondary: crumpled facets over the masses (the Village mine wall): flat faces about a third of the
    # passage's half width across, meeting at crisp ridges, shallow, following the masses; drawn out a
    # little along the lean (3x ran as long thin arcs at High, even cells read as a honeycomb).
    # Folds, not cells (closed facet outlines read as a network of cracks): where a smooth rock noise crosses
    # zero the wall folds to a crisp ridge, broad faces between, the ridges branching and fading like crumpled
    # rock. Two sizes, the big folds about two thirds of the passage's half width, small ones a quarter.
    # Each fold rises fast from its ridge then flattens out (|n| to the power 0.7; 0.4 cut worm-like grooves), so the faces between read flat
    # and angular rather than as soft, melted bulges.
    # The ridge itself is rounded over a few centimetres of the fold (a true |n| peaks to a knife edge, which at
    # high Roughness stood up as thin fins that looked like geometry folding through itself, Mike).
    def fold(size, amp):
        n = noise(rr(size), rr(size), rr(size * 1.6), 1.0, 2.0)
        # Ridge rounded over a wider band (0.04; at 0.01 it was narrower than the mesh and zippered, D164).
        return t.math('MULTIPLY', t.math('POWER', t.math('SQRT', t.math('ADD', t.math('MULTIPLY', n, n), 0.04)), 0.7), rr(amp))
    # The folds alone (D179, Mike): the facets that went with them drew their cell seams on the walls as dark
    # zigzag lines with beads at the corners, a network of cracks that read as noise, not rock.
    joint_secondary = t.math('ADD', t.math('ADD', fold(0.65, 0.06), fold(0.25, 0.03)), t.math('MULTIPLY', grain, 0.5))
    jointed = t.math('ADD', t.math('MULTIPLY', joint_primary, F), t.math('MULTIPLY', joint_secondary, R))

    # Limestone secondary, each part from the Mammoth reference (docs/m5/ref_limestone_shapes.jpg; its thin bed
    # lines are the M7 material, D158/D159):
    #   S1 thick beds step out: on the standing walls, beds about a tenth of the radius thick, each set a little in
    #     or out from the next with a lip where it steps, in stretches along the tube;
    #   S2 block scars: high on the walls, angular broken blocks with flat faces (as the jointed rock's facets);
    #   S3 roof-fall scars: on the flat roof, shallow patches each at its own height where slabs fell away;
    #   S4 undercut foot: the foot of the walls worn back into a shallow notch.
    # Beds as in the reference (Mike: even, clean grooves read as artificial): many, of varied thickness (the
    # height is warped so some beds are thin and some thick), their lips wandering and breaking off along the tube
    # (where a lip breaks the bed slopes into the next instead of stepping), their faces rough.
    s_band = t.math('ADD', t.math('DIVIDE', t.math('ADD', tb["Z"], t_noise(rr(4.0), rr(3.0), rr(3.0), 1.0, rr(0.15))), rr(0.07)),
                    t.math('ADD', t_noise(rr(3.0), rr(3.0), rr(0.25), 1.0, 1.2), t_noise(rr(0.3), rr(0.3), rr(0.3), 2.0, 0.25)))
    s_idx, s_f = t.math('FLOOR', s_band), t.math('FRACT', s_band)

    def s_bed(k):
        n = t.node('ShaderNodeTexNoise', Vector=t.vec(t.math('DIVIDE', tb["X"], rr(2.0)), t.math('MULTIPLY', t.math('ADD', s_idx, k), 3.17), t_seed),
                   Scale=1.0, Detail=0.0)
        n.noise_dimensions = '3D'
        return t.math('MULTIPLY', t.math('SUBTRACT', n.outputs["Fac"], 0.5), rr(0.08))  # each bed in or out up to 4% of the radius (at 8% the lips became deep dark slashes, D162)
    s_brk = t.node('ShaderNodeTexNoise', Vector=t.vec(t.math('DIVIDE', tb["X"], rr(0.8)), t.math('MULTIPLY', s_idx, 5.1), t.math('ADD', t_seed, 7.0)), Scale=1.0, Detail=1.0)
    s_brk.noise_dimensions = '3D'
    s_lip = t.math('ADD', t.smooth(s_f, 0.7, 1.0), t.math('MULTIPLY', t.math('SUBTRACT', s_f, t.smooth(s_f, 0.7, 1.0)), t.smooth(s_brk.outputs["Fac"], 0.45, 0.6)))
    s_beds = t.math('ADD', t.math('ADD', s_bed(0.0), t.math('MULTIPLY', t.math('SUBTRACT', s_bed(1.0), s_bed(0.0)), s_lip)),
                    t_noise(rr(0.2), rr(0.2), rr(0.08), 3.0, rr(0.025)))
    s_beds = t.math('MULTIPLY', s_beds, t.math('MULTIPLY', t.math('MULTIPLY', upright, t.smooth(t_noise(rr(4.0), rr(1.0), rr(1.0), 1.0, 1.0), -0.05, 0.08)),
                                               t.math('MULTIPLY', t.smooth(t_hn, 0.1, 0.18), t.math('SUBTRACT', 1.0, t.smooth(t_hn, 0.6, 0.75)))))
    # Seams blended over a narrow band (D164: wider, the second-nearest cell's flips beaded the seams).
    s_scars = t.math('MULTIPLY', blocks(rr(0.6), rr(0.07), 17.3, 1.0, 0.12), t.math('MULTIPLY', t.math('SUBTRACT', 1.0, t.smooth(t.math('ABSOLUTE', nz), 0.3, 0.6)), t.smooth(t_hn, 0.4, 0.6)))  # upright wall only: on the turn into the roof the steep cells cut through at a grazing angle and zippered
    # Smooth cells, each patch blending into the next (eased to nothing at their edges, neighbouring patches met in
    # a sharp V that zippered across a chamber's roof; stepped straight, the edges tore).
    s_cells = t.node('ShaderNodeTexVoronoi', Vector=t.vec(t.math('DIVIDE', tb["X"], rr(0.9)), t.math('DIVIDE', tb["Y"], rr(0.9)), t_seed),
                     Scale=1.0, Randomness=0.9)
    s_cells.voronoi_dimensions, s_cells.feature = '3D', 'SMOOTH_F1'
    s_cells.inputs[[i.name for i in s_cells.inputs].index("Smoothness")].default_value = 0.6
    s_roof = t.math('MULTIPLY', t.math('MULTIPLY', t.math('SUBTRACT', t.xyz(s_cells.outputs["Color"])["X"], 0.5), rr(0.08)), t.smooth(nz, 0.55, 0.85))
    s_foot = t.math('MULTIPLY', t.math('ADD', 0.5, t_noise(rr(3.0), rr(1.0), rr(1.0), 1.0, 1.0)),
                    t.math('MULTIPLY', rr(0.06), t.math('MULTIPLY', t.smooth(t_hn, 0.0, 0.04), t.math('SUBTRACT', 1.0, t.smooth(t_hn, 0.08, 0.16)))))
    lime_secondary = t.math('ADD', t.math('ADD', s_beds, s_scars), t.math('ADD', s_foot, t.math('MULTIPLY', grain, 0.5)))
    # Secondary 15% fuller (Mike: the reference's shapes read stronger); eased off over the plates' creased edges.
    lime_secondary = t.math('MULTIPLY', lime_secondary, 1.15)
    s_roof = t.math('MULTIPLY', s_roof, 1.15)
    lime_off = t.math('MULTIPLY', lime_off, t.math('SUBTRACT', 1.0, t.smooth(t.named("lg_sharp"), 0.02, 0.25)))
    limestone = t.math('ADD', t.math('MULTIPLY', t.math('ADD', t.math('MULTIPLY', lime_primary, F), t.math('MULTIPLY', lime_secondary, R)), lime_off),
                       t.math('MULTIPLY', s_roof, R))  # the roof's patches past the flat-roof damping

    # Lava tube: a smooth round tube that swells and narrows along its length, ropey ripples drawn out along
    # the flow, little broken rock.
    lava_primary = t_noise(rr(6.0), rr(2.0), rr(2.0), 1.0, rr(1.32))  # Mike: Wall Shape did little at 0.45
    # Where the passage flares into a chamber the tube's lines bend round the flare, and read along them the big
    # forms wrapped it in curved lips (Mike's shot of the join): there they blend back to the world-space forms
    # (D146), which made none.
    t_join = t.named("lg_join")
    lava_primary = t.math('ADD', t.math('MULTIPLY', lava_primary, t.math('SUBTRACT', 1.0, t_join)),
                          t.math('MULTIPLY', noise(rr(2.0), rr(6.0), rr(2.0), 1.0, rr(1.32)), t_join))
    # Secondary, each part from a reference (docs/m5/c105; cracks and colour bands are the M7 textures, not the
    # mesh: carved arching cracks traced to no reference and Mike called them out, D151):
    #   skins (Lava River Cave): the roof and walls lined in thin streaky layers that arch over from wall to wall,
    #     shallow; noise drawn out round the arch;
    #   (the ledges at the reference's wall foot are sharp shelves: as noise they read as gentle steps or folded
    #   into spikes, so they are left for the shell, built like the benches; D153)
    #   rough surface (Thurston): a faint lumpy grain all over.
    # The fallen roof slabs are the Big rocks.
    # Skins: noise drawn out round the arch (short along the tube, long round it), several octaves so the layers
    # come in all widths and break off (a single-frequency Gabor stripe read as an even washboard).
    skins = t.math('MULTIPLY', t_noise(rr(0.2), rr(1.5), rr(1.5), 4.0, rr(0.07), t_arc),  # Mike: 40% fewer and 40% deeper, more pronounced
                   t.math('MULTIPLY', t.math('ADD', 0.5, t.math('MULTIPLY', t.smooth(t_hn, 0.2, 0.6), 0.5)),
                          t.smooth(t_hn, 0.2, 0.4)))  # not down at the wall foot or on the bench's curb, where the streaks ended in points
    # Not on walls that face down the tube (a chamber's far end, the mouth's): there the tube's lines close up
    # into rings round the end.
    t_ac = t.xyz(on_path(t.named("c_across", 'FLOAT_VECTOR'), 'FLOAT_VECTOR'))
    facing = t.math('ABSOLUTE', t.vmath('DOT_PRODUCT', push, t.vec(t.math('MULTIPLY', t_ac["Y"], -1.0), t_ac["X"], 0.0)))
    side_on = t.math('SUBTRACT', 1.0, t.smooth(facing, 0.45, 0.8))
    # Nor where the passage flares into a chamber: the tube's lines bend round the flare there, and the streaks
    # wrapped it in curved lips that tore at High (Mike's shot of the join).
    skins = t.math('MULTIPLY', skins, t.math('SUBTRACT', 1.0, t_join))
    lava_secondary = t.math('ADD', t.math('MULTIPLY', skins, side_on),
                            t.math('ADD', t_noise(rr(1.4), rr(0.35), rr(0.35), 2.0, rr(0.02)), t.math('MULTIPLY', grain, 0.3)))
    # The swell fades out down the wall foot, and narrows the tube only high on the walls and roof (Mike: pushed
    # in low on the wall it stood out over the floor as a flat, striped lip).
    # Outward, the swell grows up the wall from the floor's edge (added below, D155).
    lava_out = t.math('MULTIPLY', t.math('MAXIMUM', lava_primary, 0.0), t.math('COMPARE', gin["Rock"], 2.0))
    # High on the walls by height over the floor too: by the face's slope alone it still pushed the low wall in
    # over the bench's top, an overhanging lip with a dark slot and teeth under it (Mike's shot).
    lava_in = t.math('MULTIPLY', t.math('MINIMUM', lava_primary, 0.0), t.math('MULTIPLY', t.smooth(nz, -0.1, 0.5), t.smooth(t_hn, 0.3, 0.6)))
    lava = t.math('ADD', t.math('MULTIPLY', lava_in, F), t.math('MULTIPLY', lava_secondary, R))

    # Lava floor flow lobes (5.4b, D175; the Stefanshellir floor on docs/m5/c131): the floor rises in rounded
    # pahoehoe tongues drawn out along the tube, flat-topped with rounded edges, overlapping, 4-10% of the
    # entrance high (Wall Shape scales them; softer and lower they read as nothing), with a lower channel down the middle where the last lava drained.
    # Lifted straight up like the bench, on the floor only, eased in and out as the bench is, and spread over
    # the surface so nothing steps or folds. The cauliflower grain is roughness / M7 (Mike).
    # About 2.5 times as long as wide: drawn out further they ran as thin ridges, the gaps between pinched into
    # creases like folded cloth. Kept to the middle of the floor, clear of the bench along the walls.
    tongue = t.smooth(t.math('ADD', t_noise(rr(0.9), rr(0.36), rr(4.0), 2.0, 1.0), t.math('MULTIPLY', t_noise(rr(0.45), rr(0.18), rr(4.0), 1.0, 1.0), 0.4)), -0.05, 0.086)  # edges 15% sharper (Mike)
    channel = t.math('MULTIPLY', t.smooth(t.math('ABSOLUTE', tb["Y"]), rr(0.08), rr(0.26)), t.math('SUBTRACT', 1.0, t.smooth(t.math('ABSOLUTE', tb["Y"]), rr(0.5), rr(0.75))))
    lobe_lift = t.math('MULTIPLY', t.math('MULTIPLY', t.math('MULTIPLY', tongue, channel), t.math('MULTIPLY', H, t.math('ADD', 0.04, t.math('MULTIPLY', F, 0.06)))),
                       t.math('MULTIPLY', t.math('MULTIPLY', t.math('SUBTRACT', 1.0, wall), bench_in), t.math('COMPARE', gin["Rock"], 2.0)))
    l_blur = t.N.new('GeometryNodeBlurAttribute')
    l_blur.data_type = 'FLOAT'
    t._set(l_blur.inputs["Value"], lobe_lift)
    t._set(l_blur.inputs["Iterations"], t.node('FunctionNodeFloatToInt', Float=t.math('MULTIPLY', t.math('POWER', 2.0, levels), 0.85)).outputs[0])  # lighter than the bench's: the tongues kept their edges
    # No broken crust on the lobes (D184): as a displacement it drew seam lines at Preview and cloth-like ripples
    # at High; real broken floors are loose flat slabs (Lava River Cave). The crust comes back as an M7
    # displacement map (Mike); slab pieces are parked.
    # Limestone silt floor (5.4b, D175, D180; the Mammoth passages): level flats (the floor's bumps cut to a
    # quarter, above), banked gently up against the walls, about 3% of the entrance high, and puddle hollows in
    # the flats (the Ayyalon pool, the Marble Arch gours): shallow dips up to 2% of the entrance deep, off the
    # walls and past the cave's front, soft-edged. Puddles sets how many (0 none). Each holds a water plane
    # (below) and fills lg_depth for the M7 water.
    lime_rock_f = t.math('LESS_THAN', gin["Rock"], 0.5)
    bank = t.math('MULTIPLY', t.math('MULTIPLY', t.math('MULTIPLY', H, 0.03), t.math('SUBTRACT', 1.0, t.smooth(to_wall, rr(0.05), rr(0.35)))),
                  t.math('MULTIPLY', t.math('SUBTRACT', 1.0, t.smooth(over_floor, t.math('MULTIPLY', H, 0.04), t.math('MULTIPLY', H, 0.12))), lime_rock_f))
    pool_n = t_noise(rr(0.55), rr(0.45), rr(4.0), 1.0, 1.0)
    pool = t.smooth(pool_n, t.math('SUBTRACT', 0.16, t.math('MULTIPLY', gin["Puddles"], 0.24)), t.math('SUBTRACT', 0.24, t.math('MULTIPLY', gin["Puddles"], 0.24)))  # Puddles 0.5: about a quarter of the open floor
    pool = t.math('MULTIPLY', t.math('MULTIPLY', pool, t.math('MULTIPLY', t.smooth(to_wall, rr(0.25), rr(0.45)), t.math('SUBTRACT', 1.0, wall))),
                  t.math('MULTIPLY', t.math('MULTIPLY', t.smooth(p_s, 0.2, 0.3), lime_rock_f), t.math('GREATER_THAN', gin["Puddles"], 0.0)))
    # Only down at floor level and never on a rock piece (a roof block's underside faces down like floor).
    pool = t.math('MULTIPLY', pool, t.math('MULTIPLY', t.math('SUBTRACT', 1.0, t.smooth(over_floor, t.math('MULTIPLY', H, 0.05), t.math('MULTIPLY', H, 0.1))),
                                          t.math('SUBTRACT', 1.0, t.named("lg_piece", 'BOOLEAN'))))
    pool_d = t.math('MULTIPLY', pool, t.math('MULTIPLY', H, 0.02))
    bench = t.vec(0.0, 0.0, t.math('ADD', t.math('ADD', b_blur.outputs["Value"], l_blur.outputs["Value"]), t.math('SUBTRACT', bank, pool_d)))

    style = t.N.new('GeometryNodeIndexSwitch')
    style.data_type = 'FLOAT'
    while len(style.index_switch_items) < 3:
        style.index_switch_items.new()
    t._set(style.inputs["Index"], gin["Rock"])
    for i, g in enumerate((limestone, jointed, lava)):
        t._set(style.inputs[i + 1], g)
    # The swell grows up the wall from the floor's edge, which stays put, and the floor stays flat (Mike: moved
    # with the swell the floor dropped metres and from outside the drops stood out under the chamber as fins; held
    # still under a moving wall foot the turn folded into grooves round the rim; slid sideways it overlapped as a flap).
    bump = t.math('ADD', t.math('ADD', t.math('MULTIPLY', style.outputs[0], wall), floor_bump),
                  t.math('MULTIPLY', t.math('MULTIPLY', t.math('MULTIPLY', lava_out, F), wall), t.smooth(t_hn, 0.02, 0.3)))
    # The shell is only the cave's shape; rocks never touch it (Mike, D107).
    pushes = t.store(t.store(t.store(dense, "lg_pool", pool_d), "lg_push", t.vmath('ADD', t.vmath('SCALE', push, scale=bump), bench), 'FLOAT_VECTOR'), "lg_n0", push, 'FLOAT_VECTOR')
    pushed = t.node('GeometryNodeSetPosition', Geometry=pushes,
                    Offset=t.named("lg_push", 'FLOAT_VECTOR')).outputs[0]
    # Where the push still folds the wall through itself (a face turned to look away from where it looked
    # before), it is taken back out over a few faces round the fold, so the wall eases to its smooth shape there.
    turned = t.N.new('GeometryNodeFieldOnDomain')
    turned.domain, turned.data_type = 'FACE', 'FLOAT'
    t._set(turned.inputs[0], t.math('LESS_THAN', t.vmath('DOT_PRODUCT', t.node('GeometryNodeInputNormal').outputs[0], t.named("lg_n0", 'FLOAT_VECTOR')), 0.2))
    spread_fold = t.N.new('GeometryNodeBlurAttribute')
    spread_fold.data_type = 'FLOAT'
    t._set(spread_fold.inputs["Value"], turned.outputs[0])
    t._set(spread_fold.inputs["Iterations"], t.node('FunctionNodeFloatToInt', Float=t.math('POWER', 2.0, t.math('SUBTRACT', levels, 1.0))).outputs[0])
    eased = t.node('GeometryNodeSetPosition', Geometry=pushed,
                   Offset=t.vmath('SCALE', t.named("lg_push", 'FLOAT_VECTOR'), scale=t.math('MULTIPLY', t.smooth(spread_fold.outputs[0], 0.0, 0.05), -1.0))).outputs[0]
    rough = t.node('GeometryNodeRemoveAttribute', Geometry=t.node('GeometryNodeRemoveAttribute', Geometry=eased, Name="lg_push").outputs[0], Name="lg_n0").outputs[0]
    # Lava at the finest levels gets a last light smoothing (Mike: at Ultra the coarse shape's edge flow showed
    # through the fine faces as a moire of faint lines).
    finish = t.N.new('GeometryNodeBlurAttribute')
    finish.data_type = 'FLOAT_VECTOR'  # before linking: the type swaps the sockets
    t._set(finish.inputs["Value"], t.position())
    t._set(finish.inputs["Iterations"], t.node('FunctionNodeFloatToInt', Float=t.math('MULTIPLY', t.math('MAXIMUM', t.math('SUBTRACT', levels, 3.0), 0.0), 2.0)).outputs[0])
    rough = t.node('GeometryNodeSetPosition', Geometry=rough, Selection=t.math('MULTIPLY', t.math('COMPARE', gin["Rock"], 2.0), t.math('LESS_THAN', t.named("lg_piece", 'BOOLEAN'), 0.5)),
                   Position=finish.outputs["Value"]).outputs[0]
    # Lava at the finest levels gets a last light smoothing (Mike: at Ultra the coarse shape's edge flow showed
    # through the fine faces as a moire of faint lines).
    finish = t.N.new('GeometryNodeBlurAttribute')
    finish.data_type = 'FLOAT_VECTOR'  # before linking: the type swaps the sockets
    t._set(finish.inputs["Value"], t.position())
    t._set(finish.inputs["Iterations"], t.node('FunctionNodeFloatToInt', Float=t.math('MULTIPLY', t.math('MAXIMUM', t.math('SUBTRACT', levels, 3.0), 0.0), 2.0)).outputs[0])
    rough = t.node('GeometryNodeSetPosition', Geometry=rough, Selection=t.math('MULTIPLY', t.math('COMPARE', gin["Rock"], 2.0), t.math('LESS_THAN', t.named("lg_piece", 'BOOLEAN'), 0.5)),
                   Position=finish.outputs["Value"]).outputs[0]
    # Jointed pieces stay inside (PARKING 2026-11-04, D188): they are trimmed to the cave grown by 3 voxels so
    # they sink into the walls, metres past the shell, and from outside they hung under the chamber as spikes.
    # Any part of a piece outside the shell is pulled back to a thin margin over it; that part is in the rock,
    # so nothing changes from inside.
    shell_only = t.N.new('GeometryNodeDeleteGeometry')
    shell_only.domain = 'POINT'
    t._set(shell_only.inputs["Geometry"], rough)
    t._set(shell_only.inputs["Selection"], t.named("lg_piece", 'BOOLEAN'))
    p_near = t.node('GeometryNodeProximity', Geometry=shell_only.outputs[0], Source_Position=t.position())
    p_near.target_element = 'FACES'
    p_n = t.N.new('GeometryNodeSampleNearestSurface')
    p_n.data_type = 'FLOAT_VECTOR'
    t._set(p_n.inputs["Mesh"], shell_only.outputs[0])
    t._set(p_n.inputs["Value"], t.node('GeometryNodeInputNormal').outputs[0])
    t._set(p_n.inputs["Sample Position"], t.position())
    p_out = t.vmath('DOT_PRODUCT', t.vmath('SUBTRACT', t.position(), p_near.outputs["Position"]), p_n.outputs["Value"])  # normals point into the rock: > 0 is outside
    p_margin = t.math('MINIMUM', t.math('MULTIPLY', voxel, 0.1), 0.5)
    rough = t.node('GeometryNodeSetPosition', Geometry=rough,
                   Selection=t.math('MULTIPLY', t.math('MULTIPLY', t.named("lg_piece", 'BOOLEAN'), jointed_on), t.math('GREATER_THAN', p_out, p_margin)),
                   Position=t.vmath('ADD', p_near.outputs["Position"], t.vmath('SCALE', t.vmath('NORMALIZE', p_n.outputs["Value"]), scale=p_margin))).outputs[0]
    marked = t.store(rough, "lg_cave", True, 'BOOLEAN', 'FACE')
    smooth = t.node('GeometryNodeSetShadeSmooth', Geometry=marked).outputs[0]
    # Rubble is separate pieces laid over the shell, wall foot and ramp alike (Mike, D107): instances, not
    # cut in, so Rubble 0 leaves no rock at all and Ramp off takes the ramp's rocks with it.
    # Data maps (Mike: every map the landscapes have, for export): the same 0..1 named attributes on the shell
    # and pieces, read for a cave. lg_height and lg_slope as on the landscapes; lg_curvature from the true 3D
    # surface, bright in crevices and hollows, dark on ridges; lg_flow the floor's hollows, where water runs and
    # pools; lg_wear the ridges and edges; lg_deposit the flat floor and its hollows, where silt settles;
    # lg_depth 0 until caves get water. Normals point into the rock, so the floor's look down.
    nrm_f = t.node('GeometryNodeInputNormal').outputs[0]
    nzf = t.xyz(nrm_f)["Z"]
    m_st = t.node('GeometryNodeAttributeStatistic', Geometry=smooth, Selection=t.math('LESS_THAN', t.named("lg_piece", 'BOOLEAN'), 0.5),
                  Attribute=t.xyz(t.position())["Z"])  # the shell's range (pieces reach past it)
    m_st.data_type, m_st.domain = 'FLOAT', 'POINT'
    m_height = t.math('DIVIDE', t.math('SUBTRACT', t.xyz(t.position())["Z"], m_st.outputs["Min"]),
                      t.math('MAXIMUM', t.math('SUBTRACT', m_st.outputs["Max"], m_st.outputs["Min"]), 1e-6))
    m_slope = t.math('DIVIDE', t.math('ARCCOSINE', t.math('MINIMUM', t.math('ABSOLUTE', nzf), 1.0)), 1.5707963)
    m_blur = t.N.new('GeometryNodeBlurAttribute')
    m_blur.data_type = 'FLOAT_VECTOR'  # before linking: the type swaps the sockets
    t._set(m_blur.inputs["Value"], t.position())
    m_blur.inputs["Iterations"].default_value = 3
    m_spacing = t.math('MAXIMUM', t.math('DIVIDE', voxel, t.math('POWER', 2.0, levels)), 1e-4)  # about an edge
    m_curv = t.math('ADD', 0.5, t.math('MULTIPLY', t.math('DIVIDE', t.vmath('DOT_PRODUCT', t.vmath('SUBTRACT', m_blur.outputs["Value"], t.position()),
                                                                          t.vmath('SCALE', nrm_f, scale=-1.0)), m_spacing), 0.5))
    m_curv = t.math('MINIMUM', t.math('MAXIMUM', m_curv, 0.0), 1.0)
    m_floor = t.smooth(nzf, -0.7, -0.9)
    m_flow = t.math('MULTIPLY', m_floor, t.smooth(m_curv, 0.5, 0.62))
    m_wear = t.math('SUBTRACT', 1.0, t.smooth(m_curv, 0.2, 0.5))
    m_dep = t.math('MULTIPLY', t.math('MULTIPLY', m_floor, t.math('SUBTRACT', 1.0, m_slope)), t.smooth(m_curv, 0.3, 0.6))
    maps = (("lg_height", m_height), ("lg_slope", m_slope), ("lg_curvature", m_curv), ("lg_flow", m_flow),
            ("lg_wear", m_wear), ("lg_deposit", m_dep),
            ("lg_depth", t.math('MAXIMUM', t.math('MINIMUM', t.math('DIVIDE', t.named("lg_pool"), t.math('MAXIMUM', t.math('MULTIPLY', H, 0.02), 1e-3)), 1.0),
                                # flooded: 0 at the shore, 1 a quarter of the entrance height down
                                t.math('MULTIPLY', flood_on, t.math('MINIMUM', t.math('MAXIMUM', t.math('DIVIDE', t.math('SUBTRACT', w_z, t.xyz(t.position())["Z"]),
                                                                                                          t.math('MULTIPLY', H, 0.25)), 0.0), 1.0)))))
    for m_name, m_val in maps:
        smooth = t.store(smooth, m_name, m_val)
    # The viewer: the picked map as a colour the viewport shows in Solid mode, grey or heatmap (as nodes.py).
    m_pick = t.N.new('GeometryNodeIndexSwitch')
    m_pick.data_type = 'FLOAT'
    while len(m_pick.index_switch_items) < 8:
        m_pick.index_switch_items.new()
    t._set(m_pick.inputs["Index"], gin["Show Mask"])
    for i, (m_name, _v) in enumerate(maps):
        t._set(m_pick.inputs[i + 2], t.named(m_name))
    m_ramp = t.N.new('ShaderNodeValToRGB')
    els = m_ramp.color_ramp.elements
    els[0].color, els[1].color = (0.05, 0.03, 0.25, 1.0), (0.99, 0.91, 0.14, 1.0)
    els.new(0.5).color = (0.13, 0.57, 0.55, 1.0)
    t._set(m_ramp.inputs["Fac"], m_pick.outputs[0])
    gray_v = t.math('POWER', t.math('MAXIMUM', m_pick.outputs[0], 0.0), 2.2)  # shown as the map's own value
    m_gray = t.node('FunctionNodeCombineColor', Red=gray_v, Green=gray_v, Blue=gray_v).outputs[0]
    m_col = t.N.new('GeometryNodeSwitch')
    m_col.input_type = 'RGBA'
    t._set(m_col.inputs["Switch"], gin["Mask Heatmap"])
    t._set(m_col.inputs["False"], m_gray)
    t._set(m_col.inputs["True"], m_ramp.outputs["Color"])
    m_view = t.node('GeometryNodeStoreNamedAttribute', Geometry=smooth, Selection=t.math('GREATER_THAN', gin["Show Mask"], 0.5), Name="lg_view")
    m_view.data_type, m_view.domain = 'FLOAT_COLOR', 'POINT'
    t._set(m_view.inputs["Value"], m_col.outputs[0])
    smooth = m_view.outputs[0]
    with_rocks = t.node('GeometryNodeJoinGeometry')
    t.L.new(smooth, with_rocks.inputs[0])
    # Which rocks stay is decided on the Preview-grid space (rock_space, above), before any rock moves, so it is
    # the same at every Detail Level.
    # Rocks only on the ground for now (Mike, while the wall shapes are dialled in): any rock not resting on
    # floor (a face looking down, out of the cave's space) is dropped, so none sit on walls, slabs or in the air.
    under = t.node('GeometryNodeRaycast', Target_Geometry=rock_space,
                   Source_Position=t.vmath('ADD', t.position(), t.vec(0.0, 0.0, t.math('MULTIPLY', H, 0.25))),
                   Ray_Direction=(0.0, 0.0, -1.0), Ray_Length=t.math('ADD', t.math('MULTIPLY', H, 2.0), t.math('MULTIPLY', gin["Chamber Drop"], 2.0)))
    on_floor = t.math('MULTIPLY', under.outputs["Is Hit"], t.math('LESS_THAN', t.xyz(under.outputs["Hit Normal"])["Z"], -0.9))  # near-flat ground
    grounded = t.node('GeometryNodeDeleteGeometry', Geometry=boulders.outputs[0], Selection=t.math('LESS_THAN', on_floor, 0.5))
    grounded.domain = 'INSTANCE'
    # No rock may poke out through the walls or roof (Mike: rocks showed on the outside of the cave): from each
    # rock's middle (a little over its pivot, which sits at the ground), a ray up and four level rays must not
    # meet the cave's side inside the rock's own reach. (From the pivot itself the level rays met the floor's rise.)
    i_scale = t.xyz(t.node('GeometryNodeInputInstanceScale').outputs[0])
    reach_xy = t.math('MULTIPLY', t.math('MULTIPLY', t.math('MAXIMUM', i_scale["X"], i_scale["Y"]), t.named("lg_rock_r")), 0.85)
    pokes = None
    for d, reach in (((0.0, 0.0, 1.0), t.math('MULTIPLY', i_scale["Z"], 0.3)), ((1.0, 0.0, 0.0), reach_xy), ((-1.0, 0.0, 0.0), reach_xy),
                     ((0.0, 1.0, 0.0), reach_xy), ((0.0, -1.0, 0.0), reach_xy)):
        ray = t.node('GeometryNodeRaycast', Target_Geometry=rock_space, Source_Position=t.vmath('ADD', t.position(), t.vec(0.0, 0.0, t.math('MULTIPLY', i_scale["Z"], 0.35))),
                     Ray_Direction=d, Ray_Length=reach)
        pokes = ray.outputs["Is Hit"] if pokes is None else t.math('MAXIMUM', pokes, ray.outputs["Is Hit"])
    clear = t.node('GeometryNodeDeleteGeometry', Geometry=grounded.outputs[0], Selection=pokes)
    clear.domain = 'INSTANCE'
    # Every kept rock then settles onto the finished shell below it: they were dropped onto the coarse shape
    # (and the ramp's own mesh), which smoothing and wall detail move a little, so some floated (Mike's ramp slab).
    settle = t.node('GeometryNodeRaycast', Target_Geometry=smooth,
                    Source_Position=t.vmath('ADD', t.position(), t.vec(0.0, 0.0, t.math('MULTIPLY', H, 0.25))),
                    Ray_Direction=(0.0, 0.0, -1.0), Ray_Length=t.math('ADD', t.math('MULTIPLY', H, 2.0), t.math('MULTIPLY', gin["Chamber Drop"], 2.0)))
    settled = t.node('GeometryNodeSetPosition', Geometry=clear.outputs[0], Selection=settle.outputs["Is Hit"],
                     Position=settle.outputs["Hit Position"]).outputs[0]
    # Each rock tipped to the ground under it (Mike: whole rocks, set into the ground; a little rock showing
    # under the floor outside the cave is fine, as in games and film, but no floating).
    lay = t.N.new('FunctionNodeAlignRotationToVector')
    lay.axis = 'Z'
    t._set(lay.inputs["Vector"], t.vmath('SCALE', settle.outputs["Hit Normal"], scale=-1.0))
    tipped = t.N.new('GeometryNodeRotateInstances')
    t._set(tipped.inputs["Instances"], settled)
    t._set(tipped.inputs["Selection"], settle.outputs["Is Hit"])
    t._set(tipped.inputs["Rotation"], lay.outputs[0])
    t._set(tipped.inputs["Pivot Point"], t.position())
    tipped.inputs["Local Space"].default_value = False
    t.L.new(tipped.outputs[0], with_rocks.inputs[0])

    # Breakdown heaps (5.4b, D175, D178; the sea-cave rockfall and Giant's Coffin blocks on docs/m5/c131): in
    # jointed rock the fallen roof lies in a few big heaps, the rest of the floor clear. Each heap a cone of
    # tumbled blocks at about 30 degrees (rockfall's angle of rest), the biggest round its foot, smaller ones up
    # its sides, a thin apron round the base. Heap spots are picked on the Preview-grid space like the rocks
    # (the same heaps at every level), apart along the cave and past its front; Rubble sets how many, Rock Size
    # how big the blocks. Every block drops onto the finished floor under it and sits partly in its heap (a
    # rock's pivot is 45% up from its middle); any that would poke through a wall is left out.
    jointed = t.math('COMPARE', gin["Rock"], 1.0)
    h_near = t.node('GeometryNodeSampleNearest', Geometry=path, Sample_Position=t.position()).outputs[0]
    h_s = t.N.new('GeometryNodeSampleIndex')
    h_s.data_type, h_s.domain = 'FLOAT', 'POINT'
    t._set(h_s.inputs["Geometry"], path)
    t._set(h_s.inputs["Value"], t.named("c_s"))
    t._set(h_s.inputs["Index"], h_near)
    h_floor = t.math('LESS_THAN', t.xyz(t.node('GeometryNodeInputNormal').outputs[0])["Z"], -0.9)
    spots = t.N.new('GeometryNodeDistributePointsOnFaces')
    spots.distribute_method = 'POISSON'  # before the inputs: its spacing input only shows in this mode
    t._set(spots.inputs["Mesh"], rock_space)
    t._set(spots.inputs["Selection"], t.math('MULTIPLY', t.math('MULTIPLY', h_floor, jointed), t.math('GREATER_THAN', h_s.outputs[0], 0.3)))
    t._set(spots.inputs["Distance Min"], t.math('MULTIPLY', W, 0.5))
    t._set(spots.inputs["Density Max"], 1.0)
    t._set(spots.inputs["Seed"], gin["Seed"])
    spots = t.node('GeometryNodeDeleteGeometry', Geometry=spots.outputs["Points"], Selection=t.math('GREATER_THAN', rand(0.0, 1.0, 501), t.math('ADD', 0.08, t.math('MULTIPLY', gin["Rubble"], 0.3)))).outputs[0]  # a few: about 5 in a big cave at Rubble 0.5
    h_rad = t.math('MULTIPLY', t.math('MINIMUM', r, 30.0), rand(0.5, 0.8, 503))  # each heap's radius (Mike: large heaps)
    spots = t.store(spots, "h_rad", h_rad)
    spots = t.store(spots, "h_mid", t.position(), 'FLOAT_VECTOR')
    # 90 blocks cover the cone at Rock Size 1; smaller blocks need more (by area), or they spread thin over a
    # cone that isn't there: scattered rocks, some on nothing (Mike, Rock Size 0.5).
    # shortcut: capped at 800 (Rock Size about 0.34); smaller still thins out, shrink the cone then if wanted.
    per = t.node('FunctionNodeFloatToInt', Float=t.math('MINIMUM', t.math('DIVIDE', 90.0, t.math('POWER', t.math('MAXIMUM', gin["Rock Size"], 0.1), 2.0)), 800.0)).outputs[0]
    heap = t.node('GeometryNodeDuplicateElements', Geometry=spots, Amount=per)
    heap.domain = 'POINT'
    hr = t.named("h_rad")
    # Out from the heap's middle: most blocks on the cone, some on the apron just past its foot.
    d = t.math('MULTIPLY', hr, t.math('ADD', t.math('SQRT', rand(0.0, 1.0, 505)), t.math('MULTIPLY', t.math('GREATER_THAN', rand(0.0, 1.0, 507), 0.8), rand(0.0, 0.35, 509))))
    a = rand(0.0, 6.2832, 511)
    h_xy = t.node('GeometryNodeSetPosition', Geometry=heap.outputs["Geometry"],
                  Position=t.vmath('ADD', t.named("h_mid", 'FLOAT_VECTOR'), t.vec(t.math('MULTIPLY', d, t.math('COSINE', a)), t.math('MULTIPLY', d, t.math('SINE', a)), 0.0))).outputs[0]
    h_xy = t.store(h_xy, "h_d", t.math('DIVIDE', d, t.math('MAXIMUM', hr, 1e-3)))
    h_down = t.node('GeometryNodeRaycast', Target_Geometry=smooth, Source_Position=t.vmath('ADD', t.position(), t.vec(0.0, 0.0, t.math('MULTIPLY', H, 0.6))),
                    Ray_Direction=(0.0, 0.0, -1.0), Ray_Length=t.math('ADD', t.math('MULTIPLY', H, 3.0), t.math('MULTIPLY', gin["Chamber Drop"], 2.0)))
    h_xy = t.store(h_xy, "h_hit", t.math('MULTIPLY', h_down.outputs["Is Hit"], t.math('LESS_THAN', t.xyz(h_down.outputs["Hit Normal"])["Z"], -0.7)))
    h_xy = t.store(h_xy, "h_ground", h_down.outputs["Hit Position"], 'FLOAT_VECTOR')
    h_xy = t.node('GeometryNodeDeleteGeometry', Geometry=h_xy, Selection=t.math('LESS_THAN', t.named("h_hit"), 0.5)).outputs[0]
    hd = t.named("h_d")
    # Blocks shrink up the heap: about Rock Size x 28% of the heap's radius across at its foot, half that at the top.
    h_size = t.math('MULTIPLY', t.math('MULTIPLY', t.math('MULTIPLY', hr, 0.14), gin["Rock Size"]),
                    t.math('MULTIPLY', t.math('ADD', 0.5, t.math('MULTIPLY', t.math('MINIMUM', hd, 1.0), 0.6)), rand(0.7, 1.3, 513)))
    cone = t.math('MULTIPLY', t.math('MULTIPLY', hr, 0.65), t.math('POWER', t.math('MAXIMUM', t.math('SUBTRACT', 1.0, hd), 0.0), 0.8))
    h_at = t.node('GeometryNodeSetPosition', Geometry=h_xy,
                  Position=t.vmath('ADD', t.named("h_ground", 'FLOAT_VECTOR'), t.vec(0.0, 0.0, t.math('SUBTRACT', cone, t.math('MULTIPLY', h_size, 0.5))))).outputs[0]
    h_pokes = None
    for dvec in ((1.0, 0.0, 0.0), (-1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, -1.0, 0.0), (0.0, 0.0, 1.0)):
        ray = t.node('GeometryNodeRaycast', Target_Geometry=smooth, Source_Position=t.vmath('ADD', t.named("h_ground", 'FLOAT_VECTOR'), t.vec(0.0, 0.0, t.math('MAXIMUM', cone, t.math('MULTIPLY', h_size, 0.6)))),
                     Ray_Direction=dvec, Ray_Length=t.math('MULTIPLY', h_size, 1.6))  # from just over the floor: from the pivot, under it at the heap's foot, every ray met the floor
        h_pokes = ray.outputs["Is Hit"] if h_pokes is None else t.math('MAXIMUM', h_pokes, ray.outputs["Is Hit"])
    big = t.math('MULTIPLY', t.math('GREATER_THAN', hd, 0.55), t.math('LESS_THAN', rand(0.0, 1.0, 515), 0.35))  # big blocks round the foot
    tumble = t.vec(rand(-0.7, 0.7, 517), rand(-0.7, 0.7, 519), rand(0.0, 6.28, 521))
    for name, sel, k, seed in (("Rubble Big", big, 0.4, 523), ("Rubble Medium", t.math('SUBTRACT', 1.0, big), 1.0, 527)):
        blocks_at = t.node('GeometryNodeInstanceOnPoints', Points=h_at, Selection=t.math('MULTIPLY', sel, t.math('SUBTRACT', 1.0, h_pokes)), Instance=library(name),
                           Pick_Instance=True, Instance_Index=t.node('FunctionNodeFloatToInt', Float=rand(0.0, 9999.0, seed)).outputs[0], Rotation=tumble,
                           Scale=t.math('MULTIPLY', h_size, k)).outputs[0]
        t.L.new(blocks_at, with_rocks.inputs[0])

    # Formations (5.4, D168-D171; rules L1-L5 on docs/m5/c128_formation_refs.png). What grows follows the rock:
    # limestone grows stalactites, stalagmites under them and columns where a pair meets; lava and jointed rock
    # none (lava drips are a few cm, under the 2 ft least size, D171). Secondary and sometimes primary details
    # (Mike): Medium and Big pieces only, none under 2 ft, so they read over the rocks on the floor.
    # Where (L2, L3): along the roof's cracks and ledge lines, most of the roof bare, none in the daylit front of
    # the cave. Points are picked on the Preview-grid space like the rocks, so the same formations at every level.
    f_amount = t.math('MULTIPLY', t.math('LESS_THAN', gin["Rock"], 0.5), gin["Formations"])
    f_near = t.node('GeometryNodeSampleNearest', Geometry=path, Sample_Position=t.position()).outputs[0]
    f_s = t.N.new('GeometryNodeSampleIndex')
    f_s.data_type, f_s.domain = 'FLOAT', 'POINT'
    t._set(f_s.inputs["Geometry"], path)
    t._set(f_s.inputs["Value"], t.named("c_s"))
    t._set(f_s.inputs["Index"], f_near)
    # The cracks: cell edges about 0.6 entrance widths apart, seen from below.
    f_seed = t.math('MULTIPLY', t.math('FLOORED_MODULO', gin["Seed"], 100.0), 13.7)
    f_cell = t.math('MAXIMUM', t.math('MULTIPLY', W, 0.6), 1.0)
    crack = t.N.new('ShaderNodeTexVoronoi')
    crack.voronoi_dimensions, crack.feature = '2D', 'DISTANCE_TO_EDGE'
    crack.inputs["Scale"].default_value = 1.0
    t._set(crack.inputs["Vector"], t.vmath('DIVIDE', t.vmath('ADD', t.position(), t.vec(f_seed, t.math('MULTIPLY', f_seed, 0.7), 0.0)), t.vec(f_cell, f_cell, f_cell)))
    on_crack = t.math('LESS_THAN', crack.outputs["Distance"], 0.025)
    f_roof = t.math('GREATER_THAN', t.xyz(t.node('GeometryNodeInputNormal').outputs[0])["Z"], 0.85)
    f_sel = t.math('MULTIPLY', t.math('MULTIPLY', f_roof, on_crack), t.math('MULTIPLY', t.math('GREATER_THAN', f_s.outputs[0], 0.3), t.math('GREATER_THAN', f_amount, 0.0)))
    drips = t.node('GeometryNodeDistributePointsOnFaces', Mesh=rock_space, Selection=f_sel, Seed=gin["Seed"],
                   Density=t.math('MULTIPLY', f_amount, 0.4)).outputs["Points"]
    # Each drip point keeps the id it was born with: the keep tests below use the finished shell, which differs by
    # Detail Level, so plain indices shifted and the same spot got another piece at High (review S1, c130).
    drips = t.store(drips, "f_id", t.node('GeometryNodeInputIndex').outputs[0], 'INT')
    frand = lambda lo, hi, offset: rand(lo, hi, offset, t.named("f_id", 'INT'))
    # Every keep test (roof slope, gap, flat floor, walls in reach) reads the Preview-grid space, like the rocks,
    # so Preview, High and Ultra keep exactly the same formations at the same sizes (Mike, D189: the finished
    # roof differs by level and High kept about 7% more). Only where each piece sits comes from the finished shell.
    f_reach = t.math('ADD', t.math('MULTIPLY', H, 3.0), t.math('MULTIPLY', t.math('ADD', gin["Ceiling Height"], gin["Chamber Drop"]), 2.0))
    c_up = t.node('GeometryNodeRaycast', Target_Geometry=rock_space, Source_Position=t.vmath('SUBTRACT', t.position(), t.vec(0.0, 0.0, t.math('MULTIPLY', H, 0.25))),
                  Ray_Direction=(0.0, 0.0, 1.0), Ray_Length=t.math('MULTIPLY', H, 0.5))
    drips = t.store(drips, "f_rz", t.math('MULTIPLY', c_up.outputs["Is Hit"], t.xyz(c_up.outputs["Hit Normal"])["Z"]))
    c_down = t.node('GeometryNodeRaycast', Target_Geometry=rock_space, Source_Position=t.vmath('SUBTRACT', c_up.outputs["Hit Position"], t.vec(0.0, 0.0, 0.05)),
                    Ray_Direction=(0.0, 0.0, -1.0), Ray_Length=f_reach)
    drips = t.store(drips, "f_gap", t.math('MULTIPLY', c_down.outputs["Is Hit"], c_down.outputs["Hit Distance"]))
    # Stalagmites and columns stand only on near-flat floor (they grow straight up; on a slope the skirt lifted off).
    drips = t.store(drips, "f_flat", t.math('MULTIPLY', c_down.outputs["Is Hit"], t.math('LESS_THAN', t.xyz(c_down.outputs["Hit Normal"])["Z"], -0.97)))
    drips = t.store(drips, "f_cfloor", c_down.outputs["Hit Position"], 'FLOAT_VECTOR')
    drips = t.store(drips, "f_croof", t.xyz(c_up.outputs["Hit Position"])["Z"])
    # Up onto the finished roof; then down to the finished floor below. Ray results are stored before moving.
    # Reaching twice as far as the test above: the finished roof can sit well off the Preview-grid one, and a miss left the piece floating.
    f_up = t.node('GeometryNodeRaycast', Target_Geometry=smooth, Source_Position=t.vmath('SUBTRACT', t.position(), t.vec(0.0, 0.0, t.math('MULTIPLY', H, 0.5))),
                  Ray_Direction=(0.0, 0.0, 1.0), Ray_Length=H)
    # Missed, or met a floor: the finished roof is cut well under the Preview-grid one (limestone's level roof
    # blocks, up to ~20 m in a big chamber), so look down to it from inside the rock instead.
    f_upok = t.math('MULTIPLY', f_up.outputs["Is Hit"], t.math('GREATER_THAN', t.xyz(f_up.outputs["Hit Normal"])["Z"], 0.2))
    f_dn = t.node('GeometryNodeRaycast', Target_Geometry=smooth, Source_Position=t.vmath('ADD', t.position(), t.vec(0.0, 0.0, t.math('MULTIPLY', H, 0.1))),
                  Ray_Direction=(0.0, 0.0, -1.0), Ray_Length=t.math('MULTIPLY', H, 1.5))
    f_dnok = t.math('MULTIPLY', f_dn.outputs["Is Hit"], t.math('GREATER_THAN', t.xyz(f_dn.outputs["Hit Normal"])["Z"], 0.2))
    f_rp = t.N.new('GeometryNodeSwitch')
    f_rp.input_type = 'VECTOR'
    t._set(f_rp.inputs["Switch"], f_upok)
    t._set(f_rp.inputs["False"], f_dn.outputs["Hit Position"])
    t._set(f_rp.inputs["True"], f_up.outputs["Hit Position"])
    drips = t.store(drips, "f_roof", f_rp.outputs[0], 'FLOAT_VECTOR')
    drips = t.store(drips, "f_hit", t.math('MAXIMUM', f_upok, f_dnok), 'BOOLEAN')
    drips = t.node('GeometryNodeDeleteGeometry', Geometry=drips, Selection=t.math('LESS_THAN', t.named("f_rz"), 0.9)).outputs[0]  # 26 degrees: a fat root's 12% plug still covers the slope under it
    drips = t.node('GeometryNodeSetPosition', Geometry=drips, Selection=t.named("f_hit", 'BOOLEAN'), Position=t.named("f_roof", 'FLOAT_VECTOR')).outputs[0]
    f_down = t.node('GeometryNodeRaycast', Target_Geometry=smooth, Source_Position=t.vmath('SUBTRACT', t.position(), t.vec(0.0, 0.0, 0.05)), Ray_Direction=(0.0, 0.0, -1.0),
                    Ray_Length=f_reach)
    # Missed (rare): the floor point on the Preview-grid space, so the piece is kept either way.
    f_fl = t.N.new('GeometryNodeSwitch')
    f_fl.input_type = 'VECTOR'
    t._set(f_fl.inputs["Switch"], f_down.outputs["Is Hit"])
    t._set(f_fl.inputs["False"], t.named("f_cfloor", 'FLOAT_VECTOR'))
    t._set(f_fl.inputs["True"], f_down.outputs["Hit Position"])
    drips = t.store(drips, "f_floor", f_fl.outputs[0], 'FLOAT_VECTOR')
    # The finished gap, floor to roof, for columns: they must meet both finished surfaces (the keep tests use the Preview-grid gap).
    drips = t.store(drips, "f_fgap", t.math('SUBTRACT', t.xyz(t.position())["Z"], t.xyz(f_fl.outputs[0])["Z"]))
    gap = t.named("f_gap")
    lime = t.math('MULTIPLY', t.math('LESS_THAN', gin["Rock"], 0.5), t.math('GREATER_THAN', gap, 0.0))
    # A column where the gap is low enough for a pair to have met (L5), standing floor to roof.
    col_spot = t.math('MULTIPLY', t.math('MULTIPLY', lime, t.named("f_flat")), t.math('MULTIPLY', t.math('LESS_THAN', gap, t.math('MULTIPLY', H, 0.3)),
                      t.math('MULTIPLY', t.math('GREATER_THAN', t.named("f_rz"), 0.95), t.math('LESS_THAN', frand(0.0, 1.0, 411), 0.6))))
    # Each amount slider thins only its own family: a column's spot left empty grows no pair in its place.
    col_keep = t.math('MULTIPLY', col_spot, t.math('LESS_THAN', frand(0.0, 1.0, 489), gin["Column Amount"]))
    # Lengths follow the room: about 8% of the gap for a medium stalactite, at most 4 m; big pieces are 2-3x that
    # (L1's spread in a cluster). Stalagmites about 5% of the gap, at most 3 m. The smallest fifth is left out
    # and the rest made 17.5% bigger (Mike: bigger shapes, fewer very small ones); Formation Size scales them
    # all, and none is ever under 2 ft (0.61 m, Mike). Stretch draws them out longer and thinner (1) or
    # shorter and stubbier (0); 0.5 is the pieces as built.
    r_len, r_high = frand(0.6, 1.3, 401), frand(0.5, 1.2, 421)
    f_size = t.math('MULTIPLY', gin["Formation Size"], 1.175)
    f_len = t.math('MAXIMUM', t.math('MULTIPLY', t.math('MULTIPLY', t.math('MINIMUM', t.math('MULTIPLY', gap, 0.08), 4.0), r_len), f_size), 0.61)
    f_high = t.math('MAXIMUM', t.math('MULTIPLY', t.math('MULTIPLY', t.math('MINIMUM', t.math('MULTIPLY', gap, 0.05), 3.0), r_high), f_size), 0.61)
    f_along = t.math('ADD', 0.7, t.math('MULTIPLY', gin["Formation Stretch"], 0.6))
    f_round = t.math('SUBTRACT', 1.15, t.math('MULTIPLY', gin["Formation Stretch"], 0.3))
    shaped = lambda s: t.vec(t.math('MULTIPLY', s, f_round), t.math('MULTIPLY', s, f_round), t.math('MULTIPLY', s, f_along))

    f_pick = lambda offset: t.node('FunctionNodeFloatToInt', Float=frand(0.0, 9999.0, offset)).outputs[0]  # pick above is redefined below

    def grow(points, selection, fam, scale, seed, medium_keep, fits=None):
        """One family on its points: Big or Medium by chance (no Small: too small to read, Mike), each piece
        picked at random and turned about the vertical only (they grow plumb). medium_keep drops the shortest
        Mediums: three in ten of them are the smallest fifth of all."""
        u = frand(0.0, 1.0, seed)
        for size, keep in (("Big", t.math('LESS_THAN', u, 0.25)), ("Medium", t.math('MULTIPLY', t.math('GREATER_THAN', u, 0.25), medium_keep))):
            if fits is not None:  # flooded chamber: only what clears the water (a Big piece is 2-3x a Medium's length)
                keep = t.math('MULTIPLY', keep, fits(3.0 if size == "Big" else 1.0, 2.0 if size == "Big" else 1.0))
            placed = t.node('GeometryNodeInstanceOnPoints', Points=points, Selection=t.math('MULTIPLY', selection, keep), Instance=library(f"{fam} {size}"),
                            Pick_Instance=True, Instance_Index=f_pick(seed + 1), Rotation=t.vec(0.0, 0.0, frand(0.0, 6.28, seed + 2)), Scale=scale).outputs[0]
            t.L.new(placed, with_rocks.inputs[0])

    # A single piece or a cluster grown as one (Mike: close ones become one asset; L1).
    # None shorter than a tenth of the entrance height (Mike, D185: in a big chamber the 2-3 m ones read as rows
    # of tiny spikes, noise; against the cave's own size so a small cave keeps its stalactites).
    tite_room = t.math('MULTIPLY', t.math('MULTIPLY', t.math('MINIMUM', t.math('MULTIPLY', gap, 0.08), 4.0), r_len), f_size)
    tite = t.math('MULTIPLY', t.math('MULTIPLY', lime, t.math('SUBTRACT', 1.0, col_spot)), t.math('GREATER_THAN', tite_room, t.math('MULTIPLY', H, 0.1)))
    tite = t.math('MULTIPLY', tite, t.math('LESS_THAN', frand(0.0, 1.0, 437), gin["Stalactite Amount"]))
    # Stalactites 15% bigger, Big and Medium alike (Mike, D189: more substantial); which ones grow is unchanged.
    tite_len = t.math('MULTIPLY', f_len, 1.15)
    tite_cl = t.math('LESS_THAN', frand(0.0, 1.0, 433), gin["Clusters"])
    tite_big = t.math('GREATER_THAN', r_len, 0.81)
    # Flooded: no stalactite tip in the water (they don't grow under it; refs c151), measured at its longest.
    w_clear = t.math('ADD', w_z, 0.3)
    tite_fits = lambda longest, _shortest: t.math('MAXIMUM', t.math('SUBTRACT', 1.0, flood_on), t.math('GREATER_THAN', t.math('SUBTRACT', t.named("f_croof"),
                                                     t.math('MULTIPLY', t.math('MULTIPLY', tite_len, f_along), longest)), w_clear))
    grow(drips, t.math('MULTIPLY', tite, t.math('SUBTRACT', 1.0, tite_cl)), "Stalactites", shaped(tite_len), 431, tite_big, tite_fits)
    grow(drips, t.math('MULTIPLY', tite, tite_cl), "Stalactite Clusters", shaped(tite_len), 435, tite_big, tite_fits)
    # Stalagmites under most drips (L4), on the floor straight below, sunk a little.
    floor_at = t.node('GeometryNodeSetPosition', Geometry=drips, Position=t.vmath('SUBTRACT', t.named("f_floor", 'FLOAT_VECTOR'), t.vec(0.0, 0.0, t.math('MULTIPLY', f_high, 0.04)))).outputs[0]
    # None poking through a wall: four level rays from a third of the way up must not meet the shell inside
    # the piece's reach.
    f_pokes = None
    for d in ((1.0, 0.0, 0.0), (-1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, -1.0, 0.0)):
        ray = t.node('GeometryNodeRaycast', Target_Geometry=rock_space, Source_Position=t.vmath('ADD', t.named("f_cfloor", 'FLOAT_VECTOR'), t.vec(0.0, 0.0, t.math('MULTIPLY', f_high, 0.3))),
                     Ray_Direction=d, Ray_Length=f_high)  # a cluster's footprint reaches about its height
        f_pokes = ray.outputs["Is Hit"] if f_pokes is None else t.math('MAXIMUM', f_pokes, ray.outputs["Is Hit"])
    mite_keep = t.math('MULTIPLY', t.math('MULTIPLY', lime, t.named("f_flat")), t.math('MULTIPLY', t.math('SUBTRACT', 1.0, col_spot),
                       t.math('MULTIPLY', t.math('LESS_THAN', frand(0.0, 1.0, 461), 0.7), t.math('SUBTRACT', 1.0, f_pokes))))
    mite_keep = t.math('MULTIPLY', mite_keep, t.math('LESS_THAN', frand(0.0, 1.0, 477), gin["Stalagmite Amount"]))
    mite_cl = t.math('LESS_THAN', frand(0.0, 1.0, 473), gin["Clusters"])
    mite_big = t.math('GREATER_THAN', r_high, 0.71)
    # Flooded: none wholly under the water; those that rise out of it stay (Drac), measured at their shortest.
    mite_fits = lambda _longest, shortest: t.math('MAXIMUM', t.math('SUBTRACT', 1.0, flood_on), t.math('GREATER_THAN', t.math('ADD', t.xyz(t.named("f_cfloor", 'FLOAT_VECTOR'))["Z"],
                                                     t.math('MULTIPLY', t.math('MULTIPLY', f_high, f_along), shortest)), w_clear))
    grow(floor_at, t.math('MULTIPLY', mite_keep, t.math('SUBTRACT', 1.0, mite_cl)), "Stalagmites", shaped(f_high), 471, mite_big, mite_fits)
    grow(floor_at, t.math('MULTIPLY', mite_keep, mite_cl), "Stalagmite Clusters", shaped(f_high), 475, mite_big, mite_fits)
    col_gap = t.named("f_fgap")
    col_w = t.math('MULTIPLY', col_gap, frand(0.45, 0.8, 481))
    columns = t.node('GeometryNodeInstanceOnPoints', Points=floor_at, Selection=col_keep, Instance=library("Columns Medium"), Pick_Instance=True,
                     Instance_Index=f_pick(483), Rotation=t.vec(0.0, 0.0, frand(0.0, 6.28, 485)), Scale=t.vec(col_w, col_w, col_gap)).outputs[0]
    t.L.new(columns, with_rocks.inputs[0])
    # Drapes, drawn (5.4b, L6, D185; references c142, pieces c143): the artist draws lines on the roof (a curve
    # object picked as Drape Lines); each line hangs a curtain of drape pieces laid end to end along it, half a
    # piece apart so they overlap into one (Te Ananui, Boyden), each piece turned to run along the line, settled
    # up onto the finished roof (the line was drawn on whatever Detail Level was showing) and hanging plumb.
    # Limestone only. Drape Length: 10-50% of the entrance height, never past a third of the gap to the floor;
    # Fullness keeps 30-100% of the pieces; Fold deepens the folds (the pieces' depth, 0.4x to 1.6x).
    dl_info = t.node('GeometryNodeObjectInfo', Object=gin["Drape Lines"])
    dl_info.transform_space = 'RELATIVE'
    dl_len = t.math('MULTIPLY', H, t.math('ADD', 0.1, t.math('MULTIPLY', gin["Drape Length"], 0.4)))
    dl_pts = t.N.new('GeometryNodeCurveToPoints')
    dl_pts.mode = 'LENGTH'  # before linking: the mode adds the Length input
    t._set(dl_pts.inputs["Curve"], dl_info.outputs["Geometry"])
    t._set(dl_pts.inputs["Length"], t.math('MAXIMUM', t.math('MULTIPLY', dl_len, 0.5), 0.3))
    dl = t.store(dl_pts.outputs["Points"], "dl_t", dl_pts.outputs["Tangent"], 'FLOAT_VECTOR')
    dl = t.store(dl, "dl_id", t.node('GeometryNodeInputIndex').outputs[0], 'INT')
    dlrand = lambda lo, hi, offset: rand(lo, hi, offset, t.named("dl_id", 'INT'))
    dl_up = t.node('GeometryNodeRaycast', Target_Geometry=smooth, Source_Position=t.vmath('SUBTRACT', t.position(), t.vec(0.0, 0.0, t.math('MULTIPLY', H, 0.25))),
                   Ray_Direction=(0.0, 0.0, 1.0), Ray_Length=t.math('MULTIPLY', H, 0.5))
    dl = t.store(dl, "dl_hit", t.math('MULTIPLY', dl_up.outputs["Is Hit"], t.math('GREATER_THAN', t.xyz(dl_up.outputs["Hit Normal"])["Z"], 0.2)))
    dl = t.store(dl, "dl_roof", dl_up.outputs["Hit Position"], 'FLOAT_VECTOR')
    dl = t.node('GeometryNodeDeleteGeometry', Geometry=dl, Selection=t.math('LESS_THAN', t.named("dl_hit"), 0.5)).outputs[0]
    dl = t.node('GeometryNodeSetPosition', Geometry=dl, Position=t.named("dl_roof", 'FLOAT_VECTOR')).outputs[0]
    dl_down = t.node('GeometryNodeRaycast', Target_Geometry=smooth, Source_Position=t.vmath('SUBTRACT', t.position(), t.vec(0.0, 0.0, 0.05)), Ray_Direction=(0.0, 0.0, -1.0),
                     Ray_Length=t.math('ADD', t.math('MULTIPLY', H, 3.0), t.math('MULTIPLY', t.math('ADD', gin["Ceiling Height"], gin["Chamber Drop"]), 2.0)))
    dl = t.store(dl, "dl_gap", t.math('MULTIPLY', dl_down.outputs["Is Hit"], dl_down.outputs["Hit Distance"]))
    dl_tan = t.named("dl_t", 'FLOAT_VECTOR')
    dl_yaw = t.math('ARCTAN2', t.xyz(dl_tan)["Y"], t.xyz(dl_tan)["X"])
    dl_l = t.math('MAXIMUM', t.math('MINIMUM', t.math('MULTIPLY', dl_len, dlrand(0.8, 1.2, 601)), t.math('MULTIPLY', t.named("dl_gap"), 0.33)), 0.61)
    dl_fold = t.math('ADD', 0.4, t.math('MULTIPLY', gin["Drape Fold"], 1.2))
    dl_keep = t.math('MULTIPLY', t.math('MULTIPLY', t.math('LESS_THAN', gin["Rock"], 0.5), t.math('GREATER_THAN', t.named("dl_gap"), 3.0)),
                     t.math('LESS_THAN', dlrand(0.0, 1.0, 603), t.math('ADD', 0.3, t.math('MULTIPLY', gin["Drape Fullness"], 0.7))))
    dl_big = t.math('LESS_THAN', dlrand(0.0, 1.0, 605), 0.3)
    for size, keep, k in (("Big", dl_big, 0.4), ("Medium", t.math('SUBTRACT', 1.0, dl_big), 1.0)):  # a Big piece is 2-3x a Medium: scaled to the same length
        s = t.math('MULTIPLY', dl_l, k)
        placed = t.node('GeometryNodeInstanceOnPoints', Points=dl, Selection=t.math('MULTIPLY', dl_keep, keep), Instance=library(f"Drapes {size}"),
                        Pick_Instance=True, Instance_Index=t.node('FunctionNodeFloatToInt', Float=dlrand(0.0, 9999.0, 607)).outputs[0],
                        Rotation=t.vec(0.0, 0.0, dl_yaw), Scale=t.vec(s, t.math('MULTIPLY', s, dl_fold), s)).outputs[0]
        t.L.new(placed, with_rocks.inputs[0])
    # Puddle water (5.4b, D180; as the landscapes' water level, Mike: to see how things shape up): a flat sheet
    # a quarter of the deepest dip under the silt's own level, cut a little wider than the pool so the floor
    # hides its edge (cut where the water showed, its stepped face edge stood over the floor); the waterline is
    # where the hollow's smooth slope meets it. The landscapes' plain water material, marked lg_water.
    from .nodes import water_material
    p_full = t.math('MULTIPLY', H, 0.02)
    w_faces = t.N.new('GeometryNodeSeparateGeometry')
    w_faces.domain = 'FACE'
    t._set(w_faces.inputs["Geometry"], smooth)
    t._set(w_faces.inputs["Selection"], t.math('GREATER_THAN', t.named("lg_pool"), t.math('MULTIPLY', p_full, 0.1)))
    w_up = t.node('GeometryNodeSetPosition', Geometry=w_faces.outputs["Selection"],
                  Offset=t.vec(0.0, 0.0, t.math('SUBTRACT', t.named("lg_pool"), t.math('MULTIPLY', p_full, 0.25)))).outputs[0]
    w_level = t.N.new('GeometryNodeBlurAttribute')
    w_level.data_type = 'FLOAT'
    t._set(w_level.inputs["Value"], t.xyz(t.position())["Z"])
    w_level.inputs["Iterations"].default_value = 8
    w_up = t.node('GeometryNodeSetPosition', Geometry=w_up, Position=t.vec(t.xyz(t.position())["X"], t.xyz(t.position())["Y"], w_level.outputs["Value"])).outputs[0]
    w_up = t.store(t.node('GeometryNodeSetShadeSmooth', Geometry=w_up).outputs[0], "lg_water", True, 'BOOLEAN', 'POINT')
    w_mat = t.N.new('GeometryNodeSetMaterial')
    w_mat.inputs["Material"].default_value = water_material()
    t._set(w_mat.inputs["Geometry"], w_up)
    t.L.new(w_mat.outputs[0], with_rocks.inputs[0])
    # Flooded chamber water (D193): a flat sheet at the water level over the whole cave, kept where it lies in the
    # cave's space (straight up from it is roof, not a floor seen from under it or a rock piece from inside), one
    # row of faces past that, and those outer corners pulled onto the wall so the shore sits exactly on it.
    w_bb = t.node('GeometryNodeBoundBox', Geometry=rock_space)
    w_lo, w_hi = t.xyz(w_bb.outputs["Min"]), t.xyz(w_bb.outputs["Max"])
    w_sx, w_sy = t.math('SUBTRACT', w_hi["X"], w_lo["X"]), t.math('SUBTRACT', w_hi["Y"], w_lo["Y"])
    w_step = t.math('MAXIMUM', t.math('MULTIPLY', voxel, 0.5), t.math('DIVIDE', t.math('MAXIMUM', w_sx, w_sy), 1000.0))
    w_n = lambda size: t.node('FunctionNodeFloatToInt', Float=t.math('ADD', t.math('DIVIDE', size, w_step), 2.0)).outputs[0]
    w_grid = t.node('GeometryNodeMeshGrid', Size_X=w_sx, Size_Y=w_sy, Vertices_X=w_n(w_sx), Vertices_Y=w_n(w_sy)).outputs[0]
    w_grid = t.node('GeometryNodeSetPosition', Geometry=w_grid, Offset=t.vec(t.math('MULTIPLY', t.math('ADD', w_lo["X"], w_hi["X"]), 0.5),
                                                                              t.math('MULTIPLY', t.math('ADD', w_lo["Y"], w_hi["Y"]), 0.5), w_z)).outputs[0]
    w_ray = t.node('GeometryNodeRaycast', Target_Geometry=smooth, Source_Position=t.position(), Ray_Direction=(0.0, 0.0, 1.0),
                   Ray_Length=t.math('ADD', t.math('MULTIPLY', H, 3.0), t.math('MULTIPLY', t.math('ADD', gin["Ceiling Height"], gin["Chamber Drop"]), 2.0)))
    w_grid = t.store(w_grid, "w_in", t.math('MULTIPLY', w_ray.outputs["Is Hit"], t.math('GREATER_THAN', t.xyz(w_ray.outputs["Hit Normal"])["Z"], 0.0)))
    w_any = t.N.new('GeometryNodeFieldOnDomain')
    w_any.data_type, w_any.domain = 'FLOAT', 'FACE'
    t._set(w_any.inputs["Value"], t.named("w_in"))
    w_del = t.N.new('GeometryNodeDeleteGeometry')
    w_del.domain = 'FACE'
    t._set(w_del.inputs["Geometry"], w_grid)
    t._set(w_del.inputs["Selection"], t.math('MAXIMUM', t.math('LESS_THAN', w_any.outputs[0], 0.01), t.math('SUBTRACT', 1.0, flood_on)))
    w_near = t.node('GeometryNodeProximity', Geometry=smooth, Source_Position=t.position())
    w_shore = t.node('GeometryNodeSetPosition', Geometry=w_del.outputs[0], Selection=t.math('LESS_THAN', t.named("w_in"), 0.5),
                     Position=t.vec(t.xyz(w_near.outputs["Position"])["X"], t.xyz(w_near.outputs["Position"])["Y"], w_z)).outputs[0]
    w_shore = t.store(t.node('GeometryNodeSetShadeSmooth', Geometry=w_shore).outputs[0], "lg_water", True, 'BOOLEAN', 'POINT')
    w_fmat = t.N.new('GeometryNodeSetMaterial')
    w_fmat.inputs["Material"].default_value = water_material()
    t._set(w_fmat.inputs["Geometry"], w_shore)
    t.L.new(w_fmat.outputs[0], with_rocks.inputs[0])
    t.L.new(with_rocks.outputs[0], gout.inputs["Geometry"])
    ng["kb_version"] = CAVE_VERSION
    return ng

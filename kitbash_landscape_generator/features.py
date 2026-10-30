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
CAVE_VERSION = 92
# (name, socket type, default) for the cave object's controls; sizes in real meters (D91).
CAVE_INPUTS = (
    ("Entrance Width", 'NodeSocketFloat', 12.0), ("Entrance Height", 'NodeSocketFloat', 6.0),
    ("Depth", 'NodeSocketFloat', 30.0), ("Wiggle", 'NodeSocketFloat', 0.3), ("Turn", 'NodeSocketFloat', 0.0),
    ("Drop", 'NodeSocketFloat', 0.0),
    ("Narrowing", 'NodeSocketFloat', 0.4), ("Chamber Size", 'NodeSocketFloat', 0.0),
    ("Ceiling Height", 'NodeSocketFloat', 10.0), ("Chamber Drop", 'NodeSocketFloat', 0.0),
    ("Ramp", 'NodeSocketBool', False), ("Separate Pieces", 'NodeSocketBool', False), ("Rubble", 'NodeSocketFloat', 0.5), ("Wall Shape", 'NodeSocketFloat', 0.5), ("Roughness", 'NodeSocketFloat', 0.5),
    # How the rocks are spread (Mike): their size, how long they are, how far they tip, how far they strew.
    ("Rock Size", 'NodeSocketFloat', 1.0), ("Stretch", 'NodeSocketFloat', 0.3), ("Tilt", 'NodeSocketFloat', 0.5),
    ("Spread", 'NodeSocketFloat', 0.5),
    ("Rock", 'NodeSocketInt', 0),  # the walls: 0 Limestone, 1 Jointed, 2 Lava tube
    ("Seed", 'NodeSocketInt', 0), ("Detail", 'NodeSocketInt', 0),  # 0 Preview, 1 High, 2 Ultra
    # Rock kits (rocks.py), each in three sizes: the rubble at the wall foot and the scree on the ramp.
    ("Rubble Big", 'NodeSocketCollection', None), ("Rubble Medium", 'NodeSocketCollection', None), ("Rubble Small", 'NodeSocketCollection', None),
    ("Scree Big", 'NodeSocketCollection', None), ("Scree Medium", 'NodeSocketCollection', None), ("Scree Small", 'NodeSocketCollection', None),
)
CAVE_DETAIL = (6.0, 7.0, 8.0)  # voxels across the smaller of the entrance's half width and height (shape only;
# Mike: Preview's bolder forms looked best, finer voxels broke the masses into thin stretched strips)
CAVE_FACES = (150_000, 1_000_000, 4_000_000)  # shell faces aimed for per Detail Level, by subdividing (D105)
CAVE_SUBDIV = (2, 3, 4)  # but never fewer smoothing steps than these (each x4 faces; D121)


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
    path = t.store(t.store(t.store(path, "c_s", s), "c_narrow", narrow), "c_tall", tall)

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

    def level_set(parts):
        """Overlapping closed parts -> one signed-distance field. Through a fog volume first, which merges overlaps
        cleanly: a level set made straight from overlapping meshes kept their inner faces, and taking rubble out of
        it left holes, loose pieces and pinches (Mike). Returns (grid, merged mesh)."""
        fog = t.node('GeometryNodeMeshToVolume', Mesh=t.node('GeometryNodeRealizeInstances', Geometry=parts).outputs[0],
                     Density=1.0, Voxel_Size=voxel, Interior_Band_Width=t.math('MULTIPLY', voxel, 2.0))
        fog.inputs["Resolution Mode"].default_value = 'Size'
        skin = t.node('GeometryNodeVolumeToMesh', Volume=fog.outputs[0], Threshold=0.1).outputs[0]
        return t.node('GeometryNodeMeshToSDFGrid', Mesh=skin, Voxel_Size=voxel, Band_Width=3).outputs[0], skin

    space, space_mesh = level_set(domes)

    # Rubble at the foot of the walls (Mike: rocks, a blend like Mesa's talus), taken out of the same space:
    # two rows of rock lumps along the passage, one each side, of varied size. Rubble sets how many and how
    # big (0 none); Roughness is only the rock surface, as on the landscapes (Mike).
    def rand(lo, hi, offset):
        n = t.N.new('FunctionNodeRandomValue')
        n.data_type = 'FLOAT'
        n.inputs["Min"].default_value, n.inputs["Max"].default_value = lo, hi
        t._set(n.inputs["Seed"], t.math('ADD', gin["Seed"], offset))
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
    both = t.node('GeometryNodeDuplicateElements', Geometry=path, Amount=1)
    both.domain = 'POINT'
    rows = t.node('GeometryNodeJoinGeometry')
    t.L.new(path, rows.inputs[0])
    t.L.new(t.store(both.outputs["Geometry"], "c_side", 1.0), rows.inputs[0])
    sidev = t.math('SUBTRACT', t.math('MULTIPLY', t.named("c_side"), 2.0), 1.0)  # -1 one side, +1 the other
    reach_out = t.math('MULTIPLY', t.named("c_radius"), t.math('SUBTRACT', 0.92, t.math('MULTIPLY', rand(0.0, 0.4, 11), gin["Spread"])))
    foot = t.node('GeometryNodeSetPosition', Geometry=rows.outputs[0],
                  Offset=t.vmath('SCALE', t.named("c_across", 'FLOAT_VECTOR'), scale=t.math('MULTIPLY', sidev, reach_out))).outputs[0]
    # Each rock drops onto the floor below it (where the passage meets a sunk chamber, the floor is lower
    # than the path, and rocks floated).
    drop_ray = t.node('GeometryNodeRaycast', Target_Geometry=space_mesh,
                      Source_Position=t.vmath('ADD', t.position(), t.vec(0.0, 0.0, t.math('MULTIPLY', H, 0.3))),
                      Ray_Direction=(0.0, 0.0, -1.0), Ray_Length=t.math('ADD', t.math('MULTIPLY', gin["Chamber Drop"], 2.0), t.math('MULTIPLY', H, 2.0)))
    foot = t.node('GeometryNodeSetPosition', Geometry=foot, Selection=drop_ray.outputs["Is Hit"], Position=drop_ray.outputs["Hit Position"]).outputs[0]
    # A kit of three sizes (Mike): the odd big block leaning on the wall, the everyday rocks, and pebbles strewn
    # out across the floor to break it up. A rock is big or medium, never both on one spot.
    big_keep = t.math('LESS_THAN', rand(0.0, 1.0, 29), t.math('MULTIPLY', gin["Rubble"], 0.12))
    keep = t.math('MULTIPLY', t.math('LESS_THAN', rand(0.0, 1.0, 23), t.math('MULTIPLY', gin["Rubble"], 0.9)), t.math('SUBTRACT', 1.0, big_keep))
    # Pebbles: three for each foot point, thrown out from the wall onto the floor and along the passage.
    strewn = t.node('GeometryNodeDuplicateElements', Geometry=rows.outputs[0], Amount=3)
    strewn.domain = 'POINT'
    across_v = t.named("c_across", 'FLOAT_VECTOR')
    along_v = t.vec(t.math('MULTIPLY', t.xyz(across_v)["Y"], -1.0), t.xyz(across_v)["X"], 0.0)
    pebble_at = t.node('GeometryNodeSetPosition', Geometry=strewn.outputs["Geometry"],
                       Offset=t.vmath('ADD', t.vmath('SCALE', across_v, scale=t.math('MULTIPLY', sidev, t.math('MULTIPLY', t.named("c_radius"), t.math('SUBTRACT', 0.95, t.math('MULTIPLY', rand(0.0, 1.5, 131), gin["Spread"]))))),
                                      t.vmath('SCALE', along_v, scale=t.math('MULTIPLY', t.named("c_radius"), t.math('MULTIPLY', rand(-1.2, 1.2, 137), gin["Spread"]))))).outputs[0]
    pebble_ray = t.node('GeometryNodeRaycast', Target_Geometry=space_mesh,
                        Source_Position=t.vmath('ADD', t.position(), t.vec(0.0, 0.0, t.math('MULTIPLY', H, 0.3))),
                        Ray_Direction=(0.0, 0.0, -1.0), Ray_Length=t.math('ADD', t.math('MULTIPLY', gin["Chamber Drop"], 2.0), t.math('MULTIPLY', H, 2.0)))
    pebbles_at = t.node('GeometryNodeSetPosition', Geometry=pebble_at, Selection=pebble_ray.outputs["Is Hit"], Position=pebble_ray.outputs["Hit Position"]).outputs[0]
    pebble_keep = t.math('MULTIPLY', t.math('LESS_THAN', rand(0.0, 1.0, 139), t.math('MULTIPLY', gin["Rubble"], 0.8)), pebble_ray.outputs["Is Hit"])
    # The rocks come from a collection of separate rock meshes (D105, rocks.py; any collection can be swapped
    # in), one picked at random per rock. Each fits -1..1 with its pivot 45% up, so it sits partly buried.
    def library(name):
        info = t.node('GeometryNodeCollectionInfo', Collection=gin[name], Separate_Children=True, Reset_Children=True)
        info.transform_space = 'ORIGINAL'
        return info.outputs[0]

    pick = lambda offset: t.node('FunctionNodeFloatToInt', Float=rand(0.0, 9999.0, offset)).outputs[0]  # wraps per collection

    def scatter(points, selection, kit, size, seed):
        """One size of a kit on its points: each rock picked at random, turned about the vertical with a small
        tilt (the buried side stays down) and stretched a little. Big and small rocks carry their own size."""
        size = t.math('MULTIPLY', size, gin["Rock Size"])
        tip = lambda k: t.math('MULTIPLY', rand(-0.7, 0.7, seed + k), gin["Tilt"])
        long = t.math('ADD', 1.0, t.math('MULTIPLY', rand(0.0, 1.5, seed + 6), gin["Stretch"]))  # drawn out along its length
        return t.node('GeometryNodeInstanceOnPoints', Points=points, Selection=selection, Instance=library(kit), Pick_Instance=True,
                      Instance_Index=pick(seed), Rotation=t.vec(tip(1), tip(2), rand(0.0, 6.28, seed + 3)),
                      Scale=t.vec(t.math('MULTIPLY', size, long), t.math('MULTIPLY', size, rand(0.7, 1.3, seed + 4)), t.math('MULTIPLY', size, rand(0.5, 0.9, seed + 5)))).outputs[0]

    # Sized to the passage (boulders in a chamber); instances, so no lower limit from the rock-detail grid.
    size = t.math('MULTIPLY', t.math('MULTIPLY', t.named("c_radius"), rand(0.12, 0.32, 37)), t.math('ADD', 0.5, t.math('MULTIPLY', gin["Rubble"], 0.6)))
    rubble_sets = [scatter(foot, keep, "Rubble Medium", size, 97), scatter(foot, big_keep, "Rubble Big", size, 151),
                   scatter(pebbles_at, pebble_keep, "Rubble Small", size, 161)]

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
    edge_sets = [scatter(edge_pts, t.math('MULTIPLY', edge_keep, t.math('SUBTRACT', 1.0, edge_big)), "Scree Medium", edge_size, 101),
                 scatter(edge_pts, edge_big, "Scree Big", edge_size, 181), scatter(edge_pts, edge_small, "Scree Small", edge_size, 191)]
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
    # The jointed masses (columns, steps, teardrops, roof blocks) together: cut into the cave's shape, or with
    # Separate Pieces on (Mike's test) left out of it and joined to the shell as separate pieces set into the
    # walls, floor and roof, so their flat faces and edges stay exactly as made.
    sep = gin["Separate Pieces"]
    cols = t.node('GeometryNodeJoinGeometry')
    cut_cols = t.node('GeometryNodeDeleteGeometry', Geometry=cols.outputs[0], Selection=sep)
    cut_cols.domain = 'INSTANCE'
    t.L.new(cut_cols.outputs[0], solids.inputs[0])
    # Every column reaches down past the floor by the chamber's drop as well (Mike: by the opening into a sunk
    # chamber, whose roof reaches back over the passage, a column's foot came out into the open and hung there
    # like a drip). Below a floor it stays buried in rock; over the chamber it runs on down to its floor.
    reach = t.math('MULTIPLY', t.named("c_tall"), 1.14)  # half the column's height, before the extra
    half = t.math('ADD', reach, t.math('MULTIPLY', t.math('MULTIPLY', t.math('ADD', gin["Chamber Drop"], 2.0), 0.5),
                                          t.math('SUBTRACT', 1.0, ramp_on)))  # not with a ramp: it fills to the chamber floor, and the feet came up through it (Mike's holes)
    slabs = t.node('GeometryNodeInstanceOnPoints', Points=slab_at, Selection=slab_keep, Instance=column,
                   Rotation=t.vec(rand(-0.03, 0.03, 217), t.math('MULTIPLY', t.math('MULTIPLY', sidev, -1.0), rand(0.0, 0.04, 219)), t.math('ADD', yaw, rand(-0.12, 0.12, 221))),
                   Scale=t.vec(t.math('MULTIPLY', thick, 0.5), t.math('MULTIPLY', W, rand(0.22, 0.45, 223)), half)).outputs[0]
    # Moved down so its top stays where it was.
    slabs = t.node('GeometryNodeTranslateInstances', Instances=slabs, Translation=t.vec(0.0, 0.0, t.math('SUBTRACT', reach, half)), Local_Space=False).outputs[0]
    t.L.new(slabs, cols.inputs[0])
    # The chamber's own wall, all the way round: a ring of slabs at a few points in the chamber.
    ring_pts = t.node('GeometryNodeDuplicateElements', Geometry=path, Amount=15)
    ring_pts.domain = 'POINT'
    ang = t.math('ADD', t.math('MULTIPLY', ring_pts.outputs["Duplicate Index"], 0.393), rand(-0.15, 0.15, 231))
    ring_dir = t.vec(t.math('COSINE', ang), t.math('SINE', ang), 0.0)
    # Each finds the chamber's real wall along its direction (placed at a set distance from a point near the
    # chamber's far end, the near side's masses stood out in the open: Mike's blob).
    ring_ray = t.node('GeometryNodeRaycast', Target_Geometry=space_mesh,
                      Source_Position=t.vmath('ADD', t.position(), t.vec(0.0, 0.0, t.math('MULTIPLY', t.named("c_tall"), 0.4))),
                      Ray_Direction=ring_dir, Ray_Length=t.math('ADD', t.math('MULTIPLY', rc, 3.0), W))
    ring_d = t.N.new('GeometryNodeSwitch')
    ring_d.input_type = 'FLOAT'
    t._set(ring_d.inputs['Switch'], ring_ray.outputs["Is Hit"])
    t._set(ring_d.inputs['False'], rc)
    t._set(ring_d.inputs['True'], ring_ray.outputs["Hit Distance"])
    ring_out = t.math('ADD', t.math('SUBTRACT', ring_d.outputs[0], t.math('MULTIPLY', t.math('MINIMUM', rc, ring_d.outputs[0]),
                      t.math('MULTIPLY', rand(0.08, 0.2, 233), t.math('MINIMUM', t.math('MULTIPLY', gin["Wall Shape"], 1.6), 1.0)))),
                      t.math('MULTIPLY', thick, 0.3))  # half the mass's depth into the rock (it is scaled thick x 0.3)
    ring_at = t.node('GeometryNodeSetPosition', Geometry=ring_pts.outputs["Geometry"],
                     Offset=t.vmath('ADD', t.vmath('SCALE', ring_dir, scale=ring_out), t.vec(0.0, 0.0, t.math('MULTIPLY', t.named("c_tall"), 0.5)))).outputs[0]
    ring_keep = t.math('MULTIPLY', t.math('MULTIPLY', jointed_on, has_chamber),
                       t.math('MULTIPLY', t.math('GREATER_THAN', t.named("c_s"), 0.9), t.math('LESS_THAN', rand(0.0, 1.0, 235), 0.5)))
    # Only where the ray finds the chamber's own wall: one aimed at the opening ran back down the passage and
    # stood a column right across it near the mouth, sealing the cave (Mike's cave lost its front).
    ring_keep = t.math('MULTIPLY', ring_keep, t.math('MULTIPLY', ring_ray.outputs["Is Hit"], t.math('LESS_THAN', ring_ray.outputs["Hit Distance"], t.math('MULTIPLY', rc, 1.3))))
    ring_keep = t.math('MULTIPLY', ring_keep, t.math('GREATER_THAN', t.xyz(ring_ray.outputs["Hit Position"])["Y"], t.math('SUBTRACT', y06, W)))  # and past where the chamber begins (a big one reaches back over the passage)
    ring = t.node('GeometryNodeInstanceOnPoints', Points=ring_at, Selection=ring_keep, Instance=column,
                  Rotation=t.vec(rand(-0.03, 0.03, 237), t.math('MULTIPLY', rand(0.0, 0.04, 239), -1.0), t.math('ADD', ang, rand(-0.12, 0.12, 241))),
                  Scale=t.vec(t.math('MULTIPLY', thick, 0.3), t.math('MULTIPLY', rc, rand(0.08, 0.16, 243)), half)).outputs[0]  # narrow, many (Mike: big ones read blobby); floor to roof
    ring = t.node('GeometryNodeTranslateInstances', Instances=ring, Translation=t.vec(0.0, 0.0, t.math('SUBTRACT', reach, half)), Local_Space=False).outputs[0]  # down to the floor too
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
    # Pieces Separate (Mike: separate pieces for better AO and a better jointed look, but looking like the rest
    # of the cave, not plain cubes, and reaching only a little past it): the masses as one shape of their own,
    # trimmed to the cave's space grown by a voxel (so they sink just into the walls, floor and roof) and kept
    # out of the walkway. Joined to the shell below, they go through the same snapping, smoothing and rock
    # detail as the walls, but stay their own pieces.
    pieces_all, _pieces_skin = level_set(cols.outputs[0])
    room = t.node('GeometryNodeSDFGridOffset', Grid=space, Distance=t.math('MULTIPLY', voxel, 1.5)).outputs[0]  # grown into the rock (positive grows)
    in_room = t.N.new('GeometryNodeSDFGridBoolean')
    in_room.operation = 'INTERSECT'
    t.L.new(room, in_room.inputs["Grid"])
    t.L.new(pieces_all, in_room.inputs["Grid"])
    clear_pieces = t.N.new('GeometryNodeSDFGridBoolean')
    clear_pieces.operation = 'DIFFERENCE'
    t.L.new(in_room.outputs[0], clear_pieces.inputs["Grid 1"])
    t.L.new(clear_grid, clear_pieces.inputs["Grid 2"])
    pieces_mesh = t.node('GeometryNodeGridToMesh', Grid=clear_pieces.outputs[0]).outputs[0]
    pieces_mesh = t.node('GeometryNodeDeleteGeometry', Geometry=pieces_mesh, Selection=t.math('LESS_THAN', t.math('MULTIPLY', sep, jointed_on), 0.5)).outputs[0]
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
    t._set(pick_mesh.inputs['Switch'], t.math('GREATER_THAN', t.math('ADD', t.math('ADD', ramp_on, t.math('MULTIPLY', jointed_on, t.math('SUBTRACT', 1.0, sep))), lime_on), 0.5))  # nothing cut in: plain
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
    # cave's shape; the shell is then smoothly subdivided (each step x4 faces) toward about 150k / 1M / 4M faces
    # (Preview / High / Ultra), but never fewer than 2 / 3 / 4 steps: a big cave rounded to High's steps at
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
    near_col = t.node('GeometryNodeProximity', Geometry=t.node('GeometryNodeRealizeInstances', Geometry=cols.outputs[0]).outputs[0],
                      Source_Position=t.position())
    near_col.target_element = 'FACES'
    # Only points that move mostly in or out to the face: one pulled sideways onto a column's edge spiked.
    to_col = t.vmath('NORMALIZE', t.vmath('SUBTRACT', near_col.outputs["Position"], t.position()))
    straight = t.math('GREATER_THAN', t.math('ABSOLUTE', t.vmath('DOT_PRODUCT', to_col, t.node('GeometryNodeInputNormal').outputs[0])), 0.55)
    # Not the floor: points where the wall turns into floor, snapped onto a column's foot, folded the shell there.
    upright_pt = t.math('GREATER_THAN', t.xyz(t.node('GeometryNodeInputNormal').outputs[0])["Z"], -0.35)  # wall and roof (normals point into the rock)
    cut_in = t.math('MULTIPLY', t.math('MULTIPLY', jointed_on, t.math('SUBTRACT', 1.0, sep)), upright_pt)
    on_col = t.math('MULTIPLY', t.math('MULTIPLY', t.math('MAXIMUM', cut_in, t.named("lg_piece", 'BOOLEAN')), straight),
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
    levels = t.math('MINIMUM', t.math('MAXIMUM', aim, per_level(CAVE_SUBDIV)), 5.0)
    # Sharp edges stay sharp (Mike: the jointed masses came out soft): edges where the faces meet at a real
    # angle are creased before smoothing, so broad flat faces keep crisp ridges between them.
    bend = t.node('GeometryNodeInputMeshEdgeAngle').outputs["Unsigned Angle"]
    dense = t.node('GeometryNodeSubdivisionSurface', Mesh=squared, Edge_Crease=t.smooth(bend, 0.35, 0.8),
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
    wall = t.smooth(nz, -0.93, -0.7)  # not the floor; down to near-flat ground (Mike: the wall foot looked melted)
    upright = t.math('SUBTRACT', 1.0, t.smooth(t.math('ABSOLUTE', nz), 0.55, 0.9))  # standing walls only
    R, F = gin["Roughness"], gin["Wall Shape"]
    sp = t.vmath('ADD', t.position(), t.vec(seed, t.math('MULTIPLY', seed, 0.7), 0.0))
    pz = t.xyz(t.position())

    def noise(sx, sy, sz, detail, amp):
        """Rock noise -0.5..0.5 times amp, stretched: sx, sy, sz are its size along X, Y (the cave) and Z."""
        n = t.node('ShaderNodeTexNoise', Vector=t.vmath('DIVIDE', sp, t.vec(sx, sy, sz)), Scale=1.0, Detail=detail, Roughness=0.6)
        n.noise_dimensions = '3D'
        return t.math('MULTIPLY', t.math('SUBTRACT', n.outputs["Fac"], 0.5), amp)

    rr = lambda k: t.math('MULTIPLY', r, k)
    grain = noise(rr(0.25), rr(0.25), rr(0.25), 3.0, rr(0.05))  # the smallest the shell shows, every rock
    floor_bump = t.math('MULTIPLY', noise(r, r, r, 4.0, 1.0), t.math('MULTIPLY', t.math('MULTIPLY', H, 0.06), R))

    # Limestone: long horizontal forms (the beds show in the shape, not as lines): wide shallow recesses and
    # bulges, broken rock in flat-lying slabs, and a flat roof.
    lime_primary = t.math('ADD', noise(rr(3.0), rr(3.0), rr(0.8), 2.0, rr(0.7)), noise(rr(1.2), rr(1.2), rr(0.4), 2.0, rr(0.3)))
    lime_secondary = t.math('ADD', noise(rr(0.7), rr(0.7), rr(0.18), 3.0, rr(0.22)), grain)
    roof = t.math('MULTIPLY', t.smooth(nz, 0.55, 0.85), F)  # faces looking up: the roof
    flat = t.math('MAXIMUM', t.math('MULTIPLY', H, 0.3), 1.0)  # one flat roof plane per this much height
    fr = t.math('FRACT', t.math('DIVIDE', t.math('ADD', pz["Z"], t.math('MULTIPLY', noise(rr(4.0), rr(4.0), rr(4.0), 1.0, 1.0), flat)), flat))
    lift = t.math('MULTIPLY', t.math('MULTIPLY', t.math('MULTIPLY', t.math('SUBTRACT', 1.0, fr), flat), t.smooth(fr, 0.0, 0.3)), roof)
    lime_off = t.math('SUBTRACT', 1.0, t.math('MULTIPLY', roof, 0.7))  # keeps the flat roof flat
    limestone = t.math('MULTIPLY', t.math('ADD', t.math('MULTIPLY', lime_primary, F), t.math('MULTIPLY', lime_secondary, R)), lime_off)

    # Jointed rock (sea caves, cliffs; Mike: straight joint planes across the whole cave looked man-made): the
    # rock breaks into irregular blocks, taller than wide as the joints split it, each with its own flat face
    # tilted its own way and standing in or out, blended only along the seams so no line runs on.
    J = t.math('MINIMUM', t.math('MAXIMUM', t.math('MULTIPLY', W, 0.6), 2.0), 12.0)  # big block size

    # Primary (from the rockfall reference, docs/m5/ref_jointed_shapes.jpg): a few huge masses, long in the
    # direction they lean and all leaning the same steep way (about 70 degrees, one strike per cave), meeting at
    # long creased edges like the buttresses there.
    strike = t.math('MULTIPLY', seed, 0.61)
    lean = t.vec(t.math('MULTIPLY', t.math('COSINE', strike), 0.34), t.math('MULTIPLY', t.math('SINE', strike), 0.34), -0.94)

    def blocks(size, depth, offset, drawn=3.0):
        along = t.vmath('DOT_PRODUCT', sp, lean)
        across = t.vmath('SUBTRACT', sp, t.vmath('SCALE', lean, scale=along))
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
        w = t.smooth(t.math('SUBTRACT', d2, d1), 0.0, 0.45)  # wide, so a step rolls over (steep ones ribbed the mesh)  # 1 inside a block, 0 on its seam
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
        return t.math('MULTIPLY', t.math('POWER', t.math('SQRT', t.math('ADD', t.math('MULTIPLY', n, n), 0.01)), 0.7), rr(amp))
    # Facets and folds together (Mike: the facets keep the look of layered rock; the folds, lighter, break up
    # their outlines so they don't read as a network of cracks).
    facets = blocks(rr(0.35), rr(0.06), 41.7, 1.8)
    joint_secondary = t.math('ADD', t.math('ADD', facets, t.math('ADD', fold(0.65, 0.06), fold(0.25, 0.03))), t.math('MULTIPLY', grain, 0.5))
    jointed = t.math('ADD', t.math('MULTIPLY', joint_primary, F), t.math('MULTIPLY', joint_secondary, R))

    # Lava tube: a smooth round tube that swells and narrows along its length, ropey ripples drawn out along
    # the flow, little broken rock.
    lava_primary = noise(rr(2.0), rr(6.0), rr(2.0), 1.0, rr(0.45))
    lava_secondary = t.math('ADD', noise(rr(0.35), rr(1.4), rr(0.35), 2.0, rr(0.07)), t.math('MULTIPLY', grain, 0.3))
    lava = t.math('ADD', t.math('MULTIPLY', lava_primary, F), t.math('MULTIPLY', lava_secondary, R))

    style = t.N.new('GeometryNodeIndexSwitch')
    style.data_type = 'FLOAT'
    while len(style.index_switch_items) < 3:
        style.index_switch_items.new()
    t._set(style.inputs["Index"], gin["Rock"])
    for i, g in enumerate((limestone, jointed, lava)):
        t._set(style.inputs[i + 1], g)
    bump = t.math('ADD', t.math('MULTIPLY', style.outputs[0], wall), floor_bump)
    lift = t.math('MULTIPLY', lift, t.math('LESS_THAN', gin["Rock"], 0.5))  # flat roofs: limestone only
    # The shell is only the cave's shape; rocks never touch it (Mike, D107).
    pushes = t.store(t.store(dense, "lg_push", t.vmath('SCALE', push, scale=bump), 'FLOAT_VECTOR'), "lg_n0", push, 'FLOAT_VECTOR')
    pushed = t.node('GeometryNodeSetPosition', Geometry=pushes,
                    Offset=t.vmath('ADD', t.named("lg_push", 'FLOAT_VECTOR'), t.vec(0.0, 0.0, lift))).outputs[0]
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
    marked = t.store(rough, "lg_cave", True, 'BOOLEAN', 'FACE')
    smooth = t.node('GeometryNodeSetShadeSmooth', Geometry=marked).outputs[0]
    # Rubble is separate pieces laid over the shell, wall foot and ramp alike (Mike, D107): instances, not
    # cut in, so Rubble 0 leaves no rock at all and Ramp off takes the ramp's rocks with it.
    with_rocks = t.node('GeometryNodeJoinGeometry')
    t.L.new(smooth, with_rocks.inputs[0])
    # Every rock settles onto the finished shell below it: they were dropped onto the coarse shape (and the
    # ramp's own mesh), which smoothing and wall detail move a little, so some floated (Mike's ramp slab).
    settle = t.node('GeometryNodeRaycast', Target_Geometry=smooth,
                    Source_Position=t.vmath('ADD', t.position(), t.vec(0.0, 0.0, t.math('MULTIPLY', H, 0.25))),
                    Ray_Direction=(0.0, 0.0, -1.0), Ray_Length=t.math('ADD', t.math('MULTIPLY', H, 2.0), t.math('MULTIPLY', gin["Chamber Drop"], 2.0)))
    settled = t.node('GeometryNodeSetPosition', Geometry=boulders.outputs[0], Selection=settle.outputs["Is Hit"],
                     Position=settle.outputs["Hit Position"]).outputs[0]
    # Rocks only on the ground for now (Mike, while the wall shapes are dialled in): any rock not resting on
    # floor (a face looking down, out of the cave's space) is dropped, so none sit on walls, slabs or in the air.
    on_floor = t.math('MULTIPLY', settle.outputs["Is Hit"], t.math('LESS_THAN', t.xyz(settle.outputs["Hit Normal"])["Z"], -0.9))  # near-flat ground
    grounded = t.node('GeometryNodeDeleteGeometry', Geometry=settled, Selection=t.math('LESS_THAN', on_floor, 0.5))
    grounded.domain = 'INSTANCE'
    t.L.new(grounded.outputs[0], with_rocks.inputs[0])
    t.L.new(with_rocks.outputs[0], gout.inputs["Geometry"])
    ng["kb_version"] = CAVE_VERSION
    return ng

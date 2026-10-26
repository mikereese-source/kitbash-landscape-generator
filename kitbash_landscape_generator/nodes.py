# SPDX-License-Identifier: GPL-3.0-or-later
"""Builds the shared Geometry Nodes group that every landscape uses."""

import os

import bpy

GROUP_NAME = "KB Landscape Core"
GROUP_VERSION = 120  # bump when the tree changes so old files rebuild it

# (name, socket type, default, min, max, description)
INPUTS = (
    ("Size X", 'NodeSocketFloat', 200.0, 1.0, 100000.0, "Width of the landscape in meters"),
    ("Size Y", 'NodeSocketFloat', 200.0, 1.0, 100000.0, "Depth of the landscape in meters"),
    ("Final", 'NodeSocketBool', False, None, None, "Use the Final detail level instead of Preview"),
    ("Preview Resolution", 'NodeSocketInt', 512, 8, 8192, "Points along the longer side while editing"),
    ("Final Resolution", 'NodeSocketInt', 2048, 8, 8192, "Points along the longer side for the finished landscape"),
    ("Ultra", 'NodeSocketBool', False, None, None, "Hero detail: Ultra Resolution instead of Final"),
    ("Ultra Resolution", 'NodeSocketInt', 4096, 8, 16384, "Points along the longer side for hero shots"),
    ("Recipe", 'NodeSocketInt', 1, 0, 12, "Base shape: see types.json notes"),
    ("Height", 'NodeSocketFloat', 0.15, 0.0, 2.0, "Height range as a fraction of the landscape's size"),
    ("Feature Scale", 'NodeSocketFloat', 3.0, 0.1, 50.0, "How many main shapes fit across the landscape"),
    ("Detail", 'NodeSocketFloat', 6.0, 0.0, 15.0, "Layers of smaller detail on top of the main shapes"),
    ("Rock", 'NodeSocketFloat', 0.5, 0.0, 2.0, "How much real-size rock grain steep and high ground gets (per type)"),
    ("Erosion", 'NodeSocketFloat', 0.0, 0.0, 1.0, "How much of the erosion map is applied (set by the add-on)"),
    ("Erosion Map", 'NodeSocketImage', None, None, None, "Eroded heights from the erosion engine, in units of Height (set by the add-on)"),
    ("Primary", 'NodeSocketFloat', 0.0, 0.0, 1.0, "Use the drained primary shape that erosion builds on (set by the add-on)"),
    ("Pad Cells", 'NodeSocketFloat', 0.0, 0.0, 4096.0, "Extra rings of points around the edge, for the erosion engine (set by the add-on)"),
    ("Detail Floor", 'NodeSocketFloat', 0.25, 0.01, 1000.0, "Smallest shape wavelength in meters; with erosion on, the erosion grid's (set by the add-on)"),
    ("Grain Roughness", 'NodeSocketFloat', 0.5, 0.3, 0.8, "How fast rock grain fades with size: higher = rubblier at 1 m (per type, from lidar)"),
    ("Roughness", 'NodeSocketFloat', 0.5, 0.0, 1.0, "Smooth and soft, or bumpy with small detail"),
    ("Warp", 'NodeSocketFloat', 0.2, 0.0, 2.0, "Bends shapes so they look less regular"),
    ("Sharpness", 'NodeSocketFloat', 1.0, 0.2, 4.0, "Above 1: pointier tops and flatter lows"),
    ("Seed", 'NodeSocketInt', 0, -100000, 100000, "Same seed, same landscape"),
    # Per-type style and controls; what each means is set per type in types.json.
    ("Style", 'NodeSocketInt', 0, 0, 15, "Per-type style (e.g. volcano: strato, shield, cinder, caldera)"),
    ("P1", 'NodeSocketFloat', 0.5, -100.0, 100.0, "Per-type control 1"),
    ("P2", 'NodeSocketFloat', 0.5, -100.0, 100.0, "Per-type control 2"),
    ("P3", 'NodeSocketFloat', 0.5, -100.0, 100.0, "Per-type control 3"),
    ("P4", 'NodeSocketFloat', 0.0, -100.0, 100.0, "Per-type control 4"),
    ("P5", 'NodeSocketFloat', 0.5, -100.0, 100.0, "Per-type control 5"),
    ("P6", 'NodeSocketFloat', 0.5, -100.0, 100.0, "Per-type control 6"),
    ("P7", 'NodeSocketFloat', 0.0, -100.0, 100.0, "Per-type control 7"),
)


def _build(ng, recipe):
    ng.interface.clear()
    ng.nodes.clear()
    ng.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    for name, stype, default, lo, hi, desc in INPUTS:
        s = ng.interface.new_socket(name, in_out='INPUT', socket_type=stype)
        if default is not None:
            s.default_value = default
        s.description = desc
        if lo is not None:
            s.min_value, s.max_value = lo, hi

    N, L = ng.nodes, ng.links
    gin = N.new('NodeGroupInput')
    gout = N.new('NodeGroupOutput')
    inp = gin.outputs

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

    def noise(vector, kind, scale, detail, roughness, distortion=None):
        n = N.new('ShaderNodeTexNoise')
        n.noise_dimensions = '3D'
        n.noise_type = kind
        for sock, v in (("Vector", vector), ("Scale", scale), ("Detail", detail),
                        ("Roughness", roughness), ("Distortion", distortion)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[sock].default_value = v
            else:
                L.new(v, n.inputs[sock])
        return n

    def smooth(x, edge0, edge1):
        """0 below edge0, 1 above edge1, smooth in between."""
        n = N.new('ShaderNodeMapRange')
        n.interpolation_type = 'SMOOTHSTEP'
        for sock, v in (("Value", x), ("From Min", edge0), ("From Max", edge1)):
            if isinstance(v, (int, float)):
                n.inputs[sock].default_value = v
            else:
                L.new(v, n.inputs[sock])
        return n.outputs["Result"]

    def vec(x, y, z):
        n = N.new('ShaderNodeCombineXYZ')
        for sock, v in zip(n.inputs, (x, y, z)):
            if isinstance(v, (int, float)):
                sock.default_value = v
            else:
                L.new(v, sock)
        return n.outputs[0]

    def soft_ridge(n, width):
        """1 - |2n - 1| with a rounded crest: `width` 0 = knife edge, 1 = broad and round."""
        d = math('SUBTRACT', math('MULTIPLY', n, 2.0), 1.0)
        k = math('ADD', 0.02, math('MULTIPLY', width, 0.45))
        soft = math('SUBTRACT', math('SQRT', math('ADD', math('MULTIPLY', d, d), math('MULTIPLY', k, k))), k)
        span = math('SUBTRACT', math('SQRT', math('ADD', 1.0, math('MULTIPLY', k, k))), k)
        return math('SUBTRACT', 1.0, math('DIVIDE', soft, span))

    size_x, size_y = inp["Size X"], inp["Size Y"]
    # Reference size: shapes are sampled on position / ref, so they keep their form at any size.
    ref = math('MAXIMUM', size_x, size_y)

    res = N.new('GeometryNodeSwitch')
    res.input_type = 'INT'
    L.new(inp["Final"], res.inputs["Switch"])
    L.new(inp["Preview Resolution"], res.inputs["False"])
    L.new(inp["Final Resolution"], res.inputs["True"])
    ultra = N.new('GeometryNodeSwitch')
    ultra.input_type = 'INT'
    L.new(inp["Ultra"], ultra.inputs["Switch"])
    L.new(res.outputs[0], ultra.inputs["False"])
    L.new(inp["Ultra Resolution"], ultra.inputs["True"])
    res = ultra
    spacing = math('DIVIDE', ref, res.outputs[0])
    # Shape layers stop at a real size (~0.25 m wavelength); below that the rock grain takes over (R2).
    # With erosion on, the floor is the erosion grid, so every shape layer gets eroded (D54).
    detail = math('MINIMUM', inp["Detail"], math('MAXIMUM', math('LOGARITHM', math('DIVIDE', ref,
                  math('MULTIPLY', inp["Feature Scale"], inp["Detail Floor"])), 2.0), 0.0))

    # Erosion runs on a padded grid (Pad Cells extra rings on the same spacing) and crops back, so the
    # edges don't act as river mouths (Pass 3). Pad 0 is the landscape itself.
    pad = math('MULTIPLY', inp["Pad Cells"], spacing)
    grid = N.new('GeometryNodeMeshGrid')
    L.new(math('ADD', size_x, math('MULTIPLY', pad, 2.0)), grid.inputs["Size X"])
    L.new(math('ADD', size_y, math('MULTIPLY', pad, 2.0)), grid.inputs["Size Y"])
    for axis, size in (("X", size_x), ("Y", size_y)):
        to_int = N.new('FunctionNodeFloatToInt')
        to_int.rounding_mode = 'ROUND'
        L.new(math('ADD', math('ADD', math('DIVIDE', size, spacing), 1.0), math('MULTIPLY', inp["Pad Cells"], 2.0)), to_int.inputs[0])
        L.new(to_int.outputs[0], grid.inputs["Vertices " + axis])
    inner_at = N.new('ShaderNodeSeparateXYZ')
    L.new(N.new('GeometryNodeInputPosition').outputs[0], inner_at.inputs[0])
    inner = math('MULTIPLY',
                 math('LESS_THAN', math('ABSOLUTE', inner_at.outputs["X"]), math('ADD', math('MULTIPLY', size_x, 0.5), math('MULTIPLY', spacing, 0.01))),
                 math('LESS_THAN', math('ABSOLUTE', inner_at.outputs["Y"]), math('ADD', math('MULTIPLY', size_y, 0.5), math('MULTIPLY', spacing, 0.01))))

    # Normalized position, shifted by the seed so each seed is a different slice of the noise.
    pos = N.new('GeometryNodeInputPosition')
    ref_vec = N.new('ShaderNodeCombineXYZ')
    for i in range(3):
        L.new(ref, ref_vec.inputs[i])
    norm = N.new('ShaderNodeVectorMath')
    norm.operation = 'DIVIDE'
    L.new(pos.outputs[0], norm.inputs[0])
    L.new(ref_vec.outputs[0], norm.inputs[1])
    # Seed offsets stay small (wrapped): an offset in the hundreds of thousands leaves 32-bit floats
    # only ~0.03-0.06 units of precision, which snapped noise and Voronoi into blocks and rings.
    seed_val = math('FLOORED_MODULO', math('MULTIPLY', inp["Seed"], 7.31), 89.7)
    seed_z = N.new('ShaderNodeCombineXYZ')
    L.new(seed_val, seed_z.inputs["Z"])
    p = N.new('ShaderNodeVectorMath')
    p.operation = 'ADD'
    L.new(norm.outputs[0], p.inputs[0])
    L.new(seed_z.outputs[0], p.inputs[1])
    p_unbent = p.outputs[0]
    p = p.outputs[0]
    bend_n = N.new('ShaderNodeTexNoise')
    bend_n.noise_dimensions = '3D'
    L.new(p, bend_n.inputs["Vector"])
    bend_n.inputs["Scale"].default_value = 1.3
    bend_n.inputs["Detail"].default_value = 1.0
    centred = N.new('ShaderNodeVectorMath')
    centred.operation = 'SUBTRACT'
    L.new(bend_n.outputs["Color"], centred.inputs[0])
    centred.inputs[1].default_value = (0.5, 0.5, 0.5)
    push = N.new('ShaderNodeVectorMath')
    push.operation = 'SCALE'
    L.new(centred.outputs[0], push.inputs[0])
    L.new(math('MULTIPLY', inp["Warp"], 0.35), push.inputs["Scale"])
    flat = N.new('ShaderNodeVectorMath')  # keep the warp in the ground plane
    flat.operation = 'MULTIPLY'
    L.new(push.outputs[0], flat.inputs[0])
    flat.inputs[1].default_value = (1.0, 1.0, 0.0)
    warped = N.new('ShaderNodeVectorMath')
    warped.operation = 'ADD'
    L.new(p, warped.inputs[0])
    L.new(flat.outputs[0], warped.inputs[1])
    p = warped.outputs[0]
    warp_amount = 0.0  # no noise Distortion anywhere (it streaks)
    # Voronoi patterns are 2D: a flat slice through 3D cells mostly misses their sites, which made
    # craters, rocks and cones sparse. The seed shifts them sideways instead.
    seed_xy = N.new('ShaderNodeVectorMath')
    seed_xy.operation = 'ADD'
    L.new(p_unbent, seed_xy.inputs[0])
    seed_shift = N.new('ShaderNodeCombineXYZ')
    L.new(math('FLOORED_MODULO', math('MULTIPLY', inp["Seed"], 3.17), 61.3), seed_shift.inputs["X"])
    L.new(math('FLOORED_MODULO', math('MULTIPLY', inp["Seed"], 5.29), 73.1), seed_shift.inputs["Y"])
    L.new(seed_shift.outputs[0], seed_xy.inputs[1])
    p2 = seed_xy.outputs[0]

    # Recipe 0, hills: soft fBM.
    hills = noise(p, 'FBM', inp["Feature Scale"], detail, inp["Roughness"], warp_amount).outputs["Fac"]

    # Recipe 1, mountains: fold fBM into ridges (1 - |2n - 1|), square it for knife edges,
    # and let a broad noise decide which ridges grow into peaks. (Blender's own ridged
    # multifractal mostly reads as one soft blob once stretched to 0..1.)
    # Only the big shapes are folded; folding every detail layer turns it into spiky noise.
    ridge_n = noise(p, 'FBM', inp["Feature Scale"], 1.5, 0.5, warp_amount).outputs["Fac"]
    # P1 ridge width: rounds the crest (thickness) and eases the falloff.
    rd = math('SUBTRACT', math('MULTIPLY', ridge_n, 2.0), 1.0)
    rk = math('ADD', 0.02, math('MULTIPLY', inp["P1"], 0.45))
    rsoft = math('SUBTRACT', math('SQRT', math('ADD', math('MULTIPLY', rd, rd), math('MULTIPLY', rk, rk))), rk)
    rspan = math('SUBTRACT', math('SQRT', math('ADD', 1.0, math('MULTIPLY', rk, rk))), rk)
    ridge = math('SUBTRACT', 1.0, math('DIVIDE', rsoft, rspan))
    ridge = math('POWER', ridge, math('SUBTRACT', 2.5, math('MULTIPLY', inp["P1"], 1.5)))
    peaks = noise(p, 'FBM', math('MULTIPLY', inp["Feature Scale"], 0.5), 2.0, 0.5).outputs["Fac"]
    rock = noise(p, 'FBM', math('MULTIPLY', inp["Feature Scale"], 4.0), detail, inp["Roughness"]).outputs["Fac"]
    mountains = math('ADD', math('MULTIPLY', ridge, math('ADD', 0.15, peaks)),
                     math('MULTIPLY', math('SUBTRACT', rock, 0.5), 0.12))
    # Primary shape for erosion (D55): long ridge spines with valleys between that tilt to one end,
    # so every valley drains out (a fold of noise makes closed bowls erosion can't fix). Spacing and
    # path wander, each spine rises and falls along its length; erosion then carves the secondary
    # forms (tributaries, spurs, scree) and the rock grain the tertiary.
    pm = N.new('ShaderNodeSeparateXYZ')
    L.new(p, pm.inputs[0])
    wander = math('MULTIPLY', math('SUBTRACT', noise(p, 'FBM', 1.1, 3.0, 0.55).outputs["Fac"], 0.5), 1.8)
    # Spines turn (a slow direction field, up to about +-85 deg) and their spacing varies, so they curve,
    # fan and pinch instead of running as parallel rows (Pass 2: Sierra lidar has ridges at all angles).
    turn = math('MULTIPLY', math('SUBTRACT', noise(p, 'FBM', 0.7, 1.0, 0.5).outputs["Fac"], 0.5), 3.0)
    across_m = math('ADD', math('MULTIPLY', pm.outputs["Y"], math('COSINE', turn)), math('MULTIPLY', pm.outputs["X"], math('SINE', turn)))
    spread_m = math('ADD', 0.7, math('MULTIPLY', noise(p, 'FBM', 0.9, 1.0, 0.5).outputs["Fac"], 0.6))
    phase = math('ADD', math('MULTIPLY', across_m, math('MULTIPLY', inp["Feature Scale"], spread_m)), wander)
    spine_i = math('FLOOR', phase)
    crest = soft_ridge(math('FRACT', phase), inp["P1"])  # P1 ridge width
    along = noise(vec(math('MULTIPLY', pm.outputs["X"], math('MULTIPLY', inp["Feature Scale"], 1.3)),
                      math('MULTIPLY', spine_i, 7.13), seed_val), 'FBM', 1.0, 2.0, 0.5).outputs["Fac"]
    spine_h = math('ADD', 0.35, math('MULTIPLY', along, 1.1))  # peaks and saddles along each spine
    # Each spine its own strength and profile: some fade to low hills, some stand as main ridges,
    # broad or knife-edged. Identical spines read as parallel bands (Pass 2 sheet).
    spine_k = noise(vec(math('MULTIPLY', spine_i, 3.71), seed_val, 9.1), 'FBM', 1.0, 0.0, 0.5).outputs["Fac"]
    spine_k = math('MINIMUM', math('MAXIMUM', math('MULTIPLY', math('SUBTRACT', spine_k, 0.3), 2.5), 0.0), 1.0)
    spine_h = math('MULTIPLY', spine_h, math('ADD', 0.3, math('MULTIPLY', spine_k, 1.1)))
    tilt = math('MULTIPLY', math('ADD', pm.outputs["X"], 0.5), 0.12)  # valley floors fall to one end
    # Side spurs: bumps on the flanks that fade out toward the valley floor, so tributaries branch
    # around them instead of running down the flank in parallel (valley floors stay drained).
    # Two sizes of spur, so flanks are lumpy at more than one scale and gullies join (one size made a comb).
    spur_big = math('SUBTRACT', noise(p, 'FBM', math('MULTIPLY', inp["Feature Scale"], 1.7), 2.0, 0.5).outputs["Fac"], 0.5)
    spur_small = math('SUBTRACT', noise(p, 'FBM', math('MULTIPLY', inp["Feature Scale"], 4.5), 3.0, 0.55).outputs["Fac"], 0.5)
    spurs = math('MULTIPLY', math('ADD', math('MULTIPLY', spur_big, 0.9), math('MULTIPLY', spur_small, 0.5)),
                 math('MULTIPLY', crest, 0.8))
    primary = math('ADD', math('ADD', math('MULTIPLY', math('POWER', crest, math('ADD', 0.8, math('MULTIPLY', spine_k, 1.2))), spine_h), spurs), tilt)
    # Blend in the folded-noise ridges: spines alone read as parallel bands at 2 km (Pass 2 sheet);
    # the engine drains the noise's basins now (D58).
    mix_r = 0.4  # 0.7 left one big basin the engine filled flat
    primary = math('ADD', math('MULTIPLY', primary, 1.0 - mix_r), math('MULTIPLY', math('ADD', math('MULTIPLY', mountains, 1.2), tilt), mix_r))
    mountains = math('ADD', mountains, math('MULTIPLY', math('SUBTRACT', primary, mountains), inp["Primary"]))
    # Primary shapes for the other eroded types (D55, Pass 1): each keeps its own forms but every
    # low drains: floors tilt to one end (the same tilt as the Mountains valleys).
    hills_p = math('ADD', math('ADD', math('MULTIPLY', math('POWER', crest, 1.6), math('ADD', 0.35, math('MULTIPLY', along, 0.6))),
                                   math('MULTIPLY', tilt, 0.6)), math('MULTIPLY', math('SUBTRACT', hills, 0.5), 0.2))
    hills = math('ADD', hills, math('MULTIPLY', math('SUBTRACT', hills_p, hills), inp["Primary"]))

    # Recipe 2, dunes: an asymmetric sawtooth across the wind (+X), bent into crescents by low noise.
    sep = N.new('ShaderNodeSeparateXYZ')
    L.new(p, sep.inputs[0])
    bend = noise(p, 'FBM', 1.5, 2.0, 0.5).outputs["Fac"]

    spacing_jitter = math('MULTIPLY', math('SUBTRACT', noise(p, 'FBM', math('MULTIPLY', inp["Feature Scale"], 0.7), 1.0, 0.5)
                                             .outputs["Fac"], 0.5), 0.9)

    def dune_field(angle, windward_share, bend_amount):
        """Sawtooth crests across the wind at `angle` (radians): a long gentle windward rise,
        then a steep slip face. Returns (crest 0..1, phase along the wind)."""
        along = math('ADD', math('MULTIPLY', sep.outputs["X"], math('COSINE', angle)),
                     math('MULTIPLY', sep.outputs["Y"], math('SINE', angle)))
        phase = math('MULTIPLY', math('ADD', along, math('MULTIPLY', math('SUBTRACT', bend, 0.5),
                                                         math('MULTIPLY', inp["Warp"], bend_amount))),
                     inp["Feature Scale"])
        phase = math('ADD', phase, spacing_jitter)  # real dune spacing is uneven (R3 lidar)
        f = math('FRACT', phase)
        rise = math('DIVIDE', f, windward_share)
        slip = math('DIVIDE', math('SUBTRACT', 1.0, f), 1.0 - windward_share)
        return math('MINIMUM', rise, slip), phase

    def pick_field(index, fields):
        n = N.new('GeometryNodeIndexSwitch')
        n.data_type = 'FLOAT'
        while len(n.index_switch_items) < len(fields):
            n.index_switch_items.new()
        L.new(index, n.inputs["Index"])
        for i, fld in enumerate(fields):
            L.new(fld, n.inputs[i + 1])
        return n.outputs[0]

    wind = inp["P1"]
    envelope = math('ADD', 0.4, noise(p, 'FBM', 1.2, 2.0, 0.5).outputs["Fac"])
    crescent, wind_phase = dune_field(wind, 0.78, 1.0)
    # Break crests into separate dunes of about one spacing across, with open sand between
    # (White Sands lidar, docs/REALISM.md R3).
    # One smooth octave, wide ramp: crests taper out along their length instead of being cut off.
    pieces = noise(p, 'FBM', math('MULTIPLY', inp["Feature Scale"], 1.3), 0.0, 0.5).outputs["Fac"]
    crescent = math('MULTIPLY', crescent, smooth(pieces, 0.3, 0.62))
    # Linear (seif) dunes run along the wind: symmetric ridges, barely bent.
    linear, _ = dune_field(math('ADD', wind, 1.5708), 0.5, 0.3)
    star_a, _ = dune_field(math('ADD', wind, 1.0472), 0.6, 0.6)
    star_b, _ = dune_field(math('ADD', wind, 2.0944), 0.6, 0.6)
    # Star dunes are tall peaks over low sand (Erg Chebbi), so the meeting points are raised to a power.
    star = math('POWER', math('MAXIMUM', math('MAXIMUM', crescent, star_a), star_b), 2.2)
    # Wind ripples at real size (~0.3 m apart, ~1.5 cm high), only where the mesh can draw them.
    ripple_m = 0.3
    ripples = math('SINE', math('MULTIPLY', math('DIVIDE', wind_phase, inp["Feature Scale"]),
                                math('DIVIDE', math('MULTIPLY', ref, 6.2832), ripple_m)))
    # 1.5 cm high, but never more than 2% of the dunes (a 10 m landscape has 20 cm dunes).
    ripples = math('MULTIPLY', ripples, math('MINIMUM', math('DIVIDE', 0.015, math('MAXIMUM', math('MULTIPLY', inp["Height"], ref), 1e-3)), 0.02))
    ripples = math('MULTIPLY', ripples, smooth(math('DIVIDE', ripple_m, spacing), 2.5, 4.0))
    dune_shape = pick_field(inp["Style"], (math('MULTIPLY', crescent, envelope),
                                           math('MULTIPLY', linear, math('ADD', 0.6, math('MULTIPLY', envelope, 0.4))),
                                           math('MULTIPLY', star, envelope)))
    # Roughness: small secondary dunes and wind-scoured lumps on the big ones (sand had no use for it;
    # Mike). Crossing the main crests at an angle, a fraction of the spacing, kept off the slip faces' tops.
    sec_ph = math('MULTIPLY', math('ADD', math('MULTIPLY', sep.outputs["X"], math('COSINE', math('ADD', wind, 0.5))),
                                   math('MULTIPLY', sep.outputs["Y"], math('SINE', math('ADD', wind, 0.5)))),
                  math('MULTIPLY', inp["Feature Scale"], 2.2))
    sec_ph = math('ADD', sec_ph, math('MULTIPLY', math('SUBTRACT', noise(p, 'FBM', math('MULTIPLY', inp["Feature Scale"], 2.0), 1.0, 0.5).outputs["Fac"], 0.5), 2.0))
    sec_f = math('FRACT', sec_ph)
    secondary = math('MINIMUM', math('DIVIDE', sec_f, 0.75), math('DIVIDE', math('SUBTRACT', 1.0, sec_f), 0.25))
    lumps = math('SUBTRACT', noise(p, 'FBM', math('MULTIPLY', inp["Feature Scale"], 3.5), 3.0, 0.55).outputs["Fac"], 0.5)
    rough_d = math('MULTIPLY', math('ADD', math('MULTIPLY', secondary, 0.22), math('MULTIPLY', lumps, 0.3)),
                   math('MULTIPLY', inp["Roughness"], math('ADD', 0.3, math('MULTIPLY', envelope, 0.7))))
    dunes = math('ADD', math('ADD', dune_shape, ripples), rough_d)

    base = noise(p, 'FBM', inp["Feature Scale"], detail, inp["Roughness"], warp_amount).outputs["Fac"]

    # Recipe 3, seabed: a gently rolling shelf of smooth sand with patches of fractured rocky reef
    # (NOAA 3 m seafloor off Point Lobos, docs/REALISM.md). Reefs stand a few meters proud with
    # crisp edges and lined, broken tops; sand fills between. Ripples are real-size (~0.6 m).
    # The shelf tilts gently offshore and rolls; reefs are only a few percent of its relief.
    shelf = math('ADD', math('MULTIPLY', noise(p, 'FBM', math('MULTIPLY', inp["Feature Scale"], 0.5), 2.0, 0.5).outputs["Fac"], 0.5),
                 math('MULTIPLY', sep.outputs["Y"], 0.3))
    reef_n = noise(p, 'FBM', math('MULTIPLY', inp["Feature Scale"], 1.2), 3.0, 0.55).outputs["Fac"]
    reef = smooth(reef_n, 0.46, 0.54)  # about half the floor, ledgy edges a few meters tall
    bedding = N.new('ShaderNodeVectorMath')  # rock layers make lined, ledgy reef tops
    bedding.operation = 'MULTIPLY'
    L.new(p, bedding.inputs[0])
    bedding.inputs[1].default_value = (1.0, 0.3, 1.0)
    ledges = soft_ridge(noise(bedding.outputs[0], 'FBM', math('MULTIPLY', inp["Feature Scale"], 10.0), detail, 0.6)
                        .outputs["Fac"], 0.15)
    # Roughness: how ledgy and broken the reefs are (it did nothing on Seabed before; Mike, Pass 4 review).
    broken = noise(p, 'FBM', math('MULTIPLY', inp["Feature Scale"], 5.0), detail, math('ADD', 0.35, math('MULTIPLY', inp["Roughness"], 0.5))).outputs["Fac"]
    rough_s = math('ADD', 0.2, math('MULTIPLY', inp["Roughness"], 1.6))
    reef_h = math('MULTIPLY', reef, math('ADD', 0.012, math('MULTIPLY', math('ADD', math('MULTIPLY', ledges, 0.012), math('MULTIPLY', broken, 0.02)), rough_s)))
    sea_ripple_m = 0.6
    s_rip = math('SINE', math('MULTIPLY', math('ADD', sep.outputs["X"], math('MULTIPLY', bend, inp["Warp"])),
                               math('DIVIDE', math('MULTIPLY', ref, 6.2832), sea_ripple_m)))
    s_rip = math('MULTIPLY', math('MULTIPLY', s_rip, math('MINIMUM', math('DIVIDE', 0.03, math('MAXIMUM', math('MULTIPLY', inp["Height"], ref), 1e-3)), 0.01)),
                 math('MULTIPLY', smooth(math('DIVIDE', sea_ripple_m, spacing), 2.5, 4.0), math('SUBTRACT', 1.0, reef)))
    seabed = math('ADD', math('ADD', shelf, reef_h), math('MULTIPLY', s_rip, math('ADD', 0.4, math('MULTIPLY', inp["Roughness"], 1.2))))

    # Recipe 4, coastal cliffs: rolling land cut by gullies that deepen toward the edge, a steep
    # bluff band and a low wave-cut platform (Torrey Pines 1 m lidar, docs/REALISM.md).
    shore = noise(p, 'FBM', inp["Feature Scale"], 2.0, 0.5).outputs["Fac"]  # headlands and coves
    # Stretched across the coast, so ravine lines run inland from the edge instead of closing into loops.
    run_inland = N.new('ShaderNodeVectorMath')
    run_inland.operation = 'MULTIPLY'
    L.new(p, run_inland.inputs[0])
    run_inland.inputs[1].default_value = (1.0, 0.18, 1.0)
    gully_n = noise(run_inland.outputs[0], 'FBM', math('MULTIPLY', inp["Feature Scale"], 6.0), 1.5, 0.5).outputs["Fac"]  # few layers: folding the top one made a 25 m repeat
    ravine = math('POWER', soft_ridge(gully_n, 0.2), 2.5)  # V ravines of varied width: 1 along each line, 0 between
    coast = math('ADD', sep.outputs["Y"], math('MULTIPLY', math('SUBTRACT', shore, 0.5), math('MULTIPLY', inp["Warp"], 0.8)))
    coast = math('SUBTRACT', coast, math('MULTIPLY', ravine, 0.03))  # ravines notch the edge
    land = smooth(coast, -0.012, math('ADD', 0.012, math('MULTIPLY', inp["Primary"], 0.018)))  # eroded: a wider bluff zone to dissect (0.045 laid it back: 1 m slope90 12 vs 27 real)
    near_edge = smooth(coast, 0.35, 0.0)  # gullies are deepest at the edge, gone well inland
    plateau = math('ADD', math('ADD', 0.7, math('MULTIPLY', bend, 0.2)), math('MULTIPLY', math('SUBTRACT', base, 0.5), 0.5))
    # With erosion on (Primary) the stretched-noise ravines are shallow and erosion carves its own,
    # branching ones: at full depth they read as a comb along the bluff (Pass 2 sheet).
    plateau = math('SUBTRACT', plateau, math('MULTIPLY', math('MULTIPLY', ravine, near_edge), math('SUBTRACT', 0.85, math('MULTIPLY', inp["Primary"], 0.85))))
    platform = math('MULTIPLY', noise(p, 'FBM', math('MULTIPLY', inp["Feature Scale"], 3.0), 3.0, 0.5).outputs["Fac"], 0.04)
    # A sand beach at the foot (photo review, Torrey Pines): a smooth ramp from the waterline up to the bluff.
    beach = math('MULTIPLY', smooth(coast, -0.07, -0.012), 0.07)
    cliffs = math('ADD', math('ADD', platform, math('MULTIPLY', beach, math('SUBTRACT', 1.0, land))), math('MULTIPLY', land, math('MAXIMUM', plateau, 0.08)))
    # Primary: the land rises gently inland, so it drains to the sea
    cliffs = math('ADD', cliffs, math('MULTIPLY', math('SUBTRACT', math('ADD', cliffs, math('MULTIPLY', land, math('MULTIPLY', math('MINIMUM', math('MAXIMUM', coast, 0.0), 0.5), 0.3))), cliffs), inp["Primary"]))
    # The bluff's caprock in patches: hard headlands hold, soft stretches gather the ravines into a few big
    # ones (an even caprock let erosion cut an even comb; Pass 3 sheet).
    cap_patch = smooth(noise(p, 'FBM', math('MULTIPLY', inp["Feature Scale"], 2.5), 2.0, 0.5).outputs["Fac"], 0.42, 0.58)
    hard_cliffs = math('MULTIPLY', land, math('MULTIPLY', cap_patch, 0.9))

    # Recipe 5, canyon: a flat plateau cut by a branching network of channels (where the noise
    # crosses 0.5), stepped into rock layers down the walls.
    # Channels follow a low-detail noise so they stay long and continuous; detail only roughens the rim.
    course = noise(p, 'FBM', inp["Feature Scale"], 1.5, 0.5, warp_amount).outputs["Fac"]
    channel = math('ABSOLUTE', math('SUBTRACT', math('MULTIPLY', course, 2.0), 1.0))
    rim = math('MULTIPLY', math('SUBTRACT', base, 0.5), 0.08)
    width = math('ADD', 0.04, math('MULTIPLY', inp["P1"], 0.3))  # P1 channel width
    # Walls spread wide: real canyon walls are long talus slopes between cliff bands (lidar, 30 m and 1 m).
    cut = smooth(math('ADD', channel, rim), 0.0, math('MULTIPLY', width, 1.8))
    cut = math('POWER', cut, math('SUBTRACT', 2.0, math('MULTIPLY', inp["P2"], 1.7)))  # P2 plateau
    wobble = math('MULTIPLY', math('SUBTRACT', noise(p, 'FBM', math('MULTIPLY', inp["Feature Scale"], 3.0), 2.0,
                                                     0.5).outputs["Fac"], 0.5), 0.9)
    layers = 5.0
    # Uneven strata: a slow 1D noise over height stretches some layers and squeezes others.
    strata = math('MULTIPLY', math('SUBTRACT', noise(vec(math('MULTIPLY', cut, 2.3), seed_val, 0.0), 'FBM', 1.0, 2.0, 0.5)
                                   .outputs["Fac"], 0.5), 2.4)
    lu = math('ADD', math('ADD', math('MULTIPLY', cut, layers), wobble), strata)
    # Each layer's hardness: hard rock makes a short cliff over a long slope, soft rock an even ramp.
    hard = noise(vec(math('MULTIPLY', math('FLOOR', lu), 3.7), seed_val, 5.0), 'FBM', 1.0, 0.0, 0.5).outputs["Fac"]
    bench = math('DIVIDE', math('ADD', math('FLOOR', lu), math('POWER', math('FRACT', lu),
                                                                 math('ADD', 1.2, math('MULTIPLY', hard, 1.3)))), layers)
    bench = math('SUBTRACT', bench, math('DIVIDE', math('ADD', wobble, strata), layers))  # keep plateau and floor level
    wall = math('MULTIPLY', smooth(cut, 0.02, 0.12), smooth(cut, 0.98, 0.88))
    canyon = math('ADD', math('MULTIPLY', bench, wall), math('MULTIPLY', cut, math('SUBTRACT', 1.0, wall)))
    # Side gullies and ledges break up the walls at 20-200 m (Grand Canyon 1 m lidar: walls were too smooth).
    side = math('SUBTRACT', soft_ridge(noise(p, 'FBM', math('MULTIPLY', inp["Feature Scale"], 9.0), 2.0, 0.5).outputs["Fac"], 0.3), 0.5)
    canyon = math('ADD', canyon, math('MULTIPLY', side, math('MULTIPLY', wall, 0.12)))
    # Primary: plateau and channel floors tilt to one end, so the channel network drains
    canyon = math('ADD', canyon, math('MULTIPLY', math('SUBTRACT', math('ADD', canyon, math('MULTIPLY', tilt, 0.8)), canyon), inp["Primary"]))
    hard_canyon = math('MAXIMUM', math('MULTIPLY', wall, smooth(hard, 0.35, 0.65)), math('MULTIPLY', smooth(cut, 0.9, 0.98), 0.9))  # cliff bands, rim caprock

    # Recipe 6, mesa (Pass 5, from Monument Valley / Lake Powell photos, Mike's review): blocky outlines
    # where rock breaks along two joint directions, every top at one caprock level, a vertical cliff
    # with fluted faces (a crenulated outline reads as vertical grooves from the side), a stepped talus
    # apron of ledge bands below, the odd second tier, then a rough desert floor. P1 coverage runs from
    # wide plateau to scattered buttes; Style 1 (Hero) is one butte in the middle.
    mx, my = sep.outputs["X"], sep.outputs["Y"]
    j_ang = math('MULTIPLY', seed_val, 0.37)
    jx = math('SUBTRACT', math('MULTIPLY', mx, math('COSINE', j_ang)), math('MULTIPLY', my, math('SINE', j_ang)))
    jy = math('ADD', math('MULTIPLY', mx, math('SINE', j_ang)), math('MULTIPLY', my, math('COSINE', j_ang)))
    pj = vec(jx, jy, seed_val)
    # Fluted cliffs: the joint pattern is read at a slightly jiggled position, so block edges crinkle
    # (vertical grooves from the side) without breaking blocks into speckle. Roughness sets how deep.
    fl = N.new('ShaderNodeTexNoise')
    fl.noise_dimensions = '3D'
    L.new(pj, fl.inputs["Vector"])
    L.new(math('MULTIPLY', inp["Feature Scale"], 25.0), fl.inputs["Scale"])
    fl.inputs["Detail"].default_value = 2.0
    fl_c = N.new('ShaderNodeVectorMath')
    fl_c.operation = 'SUBTRACT'
    L.new(fl.outputs["Color"], fl_c.inputs[0])
    fl_c.inputs[1].default_value = (0.5, 0.5, 0.5)
    fl_s = N.new('ShaderNodeVectorMath')
    fl_s.operation = 'SCALE'
    L.new(fl_c.outputs[0], fl_s.inputs[0])
    L.new(math('DIVIDE', math('ADD', 0.02, math('MULTIPLY', inp["Roughness"], 0.06)), inp["Feature Scale"]), fl_s.inputs["Scale"])
    pj_f = N.new('ShaderNodeVectorMath')
    pj_f.operation = 'ADD'
    L.new(pj, pj_f.inputs[0])
    L.new(fl_s.outputs[0], pj_f.inputs[1])
    def joint_cells(feature):
        n = N.new('ShaderNodeTexVoronoi')  # straight-sided blocks on a rotated grid (0.35 randomness read as tiles)
        n.voronoi_dimensions = '2D'
        n.feature = feature
        n.inputs["Randomness"].default_value = 0.8  # 0.6 left a regular block spacing (9 dB spectrum spike, Pass 5)
        L.new(pj_f.outputs[0], n.inputs["Vector"])
        L.new(math('MULTIPLY', inp["Feature Scale"], 3.5), n.inputs["Scale"])
        return n
    blob = noise(pj, 'FBM', inp["Feature Scale"], 2.0, 0.45).outputs["Fac"]
    edge = math('SUBTRACT', 0.7, math('MULTIPLY', inp["P1"], 0.2))  # P1 plateau coverage (0.62 covered most of the tile)

    def block_value(site):
        """The broad field at a block's centre decides whether the whole block stands (straight edges,
        corners). Hero: one butte in the middle, still built from whole blocks."""
        sv = N.new('ShaderNodeSeparateXYZ')
        L.new(site, sv.inputs[0])
        field = noise(vec(sv.outputs["X"], sv.outputs["Y"], seed_val), 'FBM', inp["Feature Scale"], 2.0, 0.45).outputs["Fac"]
        r = math('SQRT', math('ADD', math('MULTIPLY', sv.outputs["X"], sv.outputs["X"]), math('MULTIPLY', sv.outputs["Y"], sv.outputs["Y"])))
        hero = math('ADD', math('SUBTRACT', 0.95, math('MULTIPLY', r, 1.6)), math('MULTIPLY', math('SUBTRACT', field, 0.5), 0.4))
        return pick_field(inp["Style"], (field, hero))
    v = block_value(joint_cells('F1').outputs["Position"])
    v2 = block_value(joint_cells('F2').outputs["Position"])  # the neighbouring block across the nearest edge
    d_edge = joint_cells('DISTANCE_TO_EDGE').outputs["Distance"]  # in blocks (~1 across)
    top = smooth(v, edge, math('ADD', edge, 0.002))  # sheer caprock edge
    nb_top = smooth(v2, edge, math('ADD', edge, 0.002))
    # Caprock rims are broken back a little, not machined: a short rounded bevel where a block meets open ground.
    rim = math('MULTIPLY', math('SUBTRACT', 1.0, nb_top), math('POWER', math('MAXIMUM', math('SUBTRACT', 1.0, math('DIVIDE', d_edge, 0.05)), 0.0), 2.0))
    top = math('MULTIPLY', top, math('SUBTRACT', 1.0, math('MULTIPLY', rim, 0.08)))
    # Talus apron (Monument Valley 1 m lidar, Pass 6): the cliff stands on a wide concave slope of shale
    # and rubble that reaches about half the cliff height and runs ~0.6 block out, stepped by ledges.
    # Built from the distance to the block's edge, so it always hugs the blocks (Pass 5 used a separate
    # noise field and left orphan lumps on the floor and bare cliff feet).
    # P2 Talus Spread: 0.2 to 1 block out (the erosion apron's reach scales with it too, types.json);
    # 1.6x with Floor off, so the cut-out piece keeps its full apron down to the ground.
    t = math('MULTIPLY', math('MAXIMUM', math('SUBTRACT', 1.0, math('DIVIDE', d_edge, math('MULTIPLY', math('ADD', 0.2, math('MULTIPLY', inp["P2"], 0.8)),
                                                                                  math('SUBTRACT', 1.6, math('MULTIPLY', inp["P4"], 0.6))))), 0.0),
             math('MULTIPLY', nb_top, math('SUBTRACT', 1.0, top)))
    # Floor off keeps a short ring of flat floor past the apron's toe (Mike: a little floor, so the piece
    # blends into the ground it is placed on): beyond this the floor is cut away (lg_cut, below).
    # Measured on the smooth field the blocks are picked from (read here, not at block centres): the
    # distance to a block edge stops at the middle of each open block, too short for apron and ring.
    keep_floor = math('GREATER_THAN', block_value(pj), math('SUBTRACT', edge, 0.2))  # Hero only (types.json): the Field's broad field doesn't follow its blocks
    lu = math('MULTIPLY', t, 3.0)
    ledge = math('DIVIDE', math('ADD', math('FLOOR', lu), math('POWER', math('FRACT', lu), 2.5)), 3.0)
    talus = math('MULTIPLY', math('POWER', math('ADD', math('MULTIPLY', ledge, 0.6), math('MULTIPLY', t, 0.4)), 1.6), 0.5)
    tier = math('MULTIPLY', smooth(v, math('ADD', edge, 0.07), math('ADD', edge, 0.074)), math('MULTIPLY', inp["P3"], 0.44))  # P3 Caprock Tiers
    # The floor between the blocks is rough, dissected ground (real slope50 ~10 deg at 1 m, ours was 1 deg
    # on flat desert): rolling swells plus folded ridgelets that erosion turns into dense gullies.
    swell = noise(p, 'FBM', math('MULTIPLY', inp["Feature Scale"], 3.0), detail, 0.6).outputs["Fac"]
    ridgelets = soft_ridge(noise(p, 'FBM', math('MULTIPLY', inp["Feature Scale"], 6.0), 3.0, 0.55).outputs["Fac"], 0.3)
    # P4 Floor off (Mike, 2026-10-26): no floor relief or tilt, and the flat floor is cut away at the end,
    # leaving the mesas and their aprons as a standalone piece to place on other ground.
    desert = math('MULTIPLY', math('MULTIPLY', math('ADD', math('MULTIPLY', swell, 0.06), math('MULTIPLY', ridgelets, math('MULTIPLY', inp["Roughness"], 0.14))),
                  math('SUBTRACT', 1.0, top)), inp["P4"])
    mesa = math('ADD', math('ADD', math('MAXIMUM', talus, top), tier), desert)  # all caps at one level (flat strata)
    # Primary: the desert floor between the blocks drains to one end
    mesa = math('ADD', mesa, math('MULTIPLY', math('SUBTRACT', math('ADD', mesa, math('MULTIPLY', math('MULTIPLY', tilt, 0.6), inp["P4"])), mesa), inp["Primary"]))
    hard_mesa = math('MULTIPLY', math('MAXIMUM', top, smooth(t, 0.92, 1.0)), 0.95)  # caprock and cliff band; talus soft

    def pick_float(index, values):
        n = N.new('GeometryNodeIndexSwitch')
        n.data_type = 'FLOAT'
        while len(n.index_switch_items) < len(values):
            n.index_switch_items.new()
        L.new(index, n.inputs["Index"])
        for i, v in enumerate(values):
            n.inputs[i + 1].default_value = v
        return n.outputs[0]

    x, y = sep.outputs["X"], sep.outputs["Y"]

    # Recipe 7, badlands: dense small knife-edged spurs over a soft base, with many thin soft
    # bands (the colored strata).
    density = math('ADD', 0.5, math('MULTIPLY', inp["P1"], 1.5))  # P1 gully density
    # Only the big spurs are folded; folding the finest layer made an 18 m repeating texture (R3 lidar).
    spur_n = noise(p, 'FBM', math('MULTIPLY', inp["Feature Scale"], density), math('MINIMUM', detail, 2.0), inp["Roughness"],
                   warp_amount).outputs["Fac"]
    spur = soft_ridge(spur_n, inp["P2"])  # P2 ridge width
    spur = math('POWER', spur, math('SUBTRACT', 3.0, math('MULTIPLY', inp["P2"], 1.8)))
    spur_fine = noise(p, 'FBM', math('MULTIPLY', inp["Feature Scale"], math('MULTIPLY', density, 4.0)), detail,
                      inp["Roughness"]).outputs["Fac"]
    # Broad benches carry more of the relief than the spurs (Badlands NP 1 m lidar).
    bad = math('ADD', math('ADD', math('MULTIPLY', bend, 0.9), math('MULTIPLY', spur, 0.35)),
               math('MULTIPLY', math('SUBTRACT', spur_fine, 0.5), math('MULTIPLY', spur, 0.12)))
    badlands = bad
    # Primary (Pass 5, from Badlands NP and Petrified Forest photos, Mike's review). Style 0, Wall: a
    # meandering escarpment between a flat grass table and the lower floor, with remnant buttes out on
    # the floor and a gentle concave apron at the foot; erosion cuts the dense fluted gullies into the
    # face, and thin hard caps and beds (hard map) leave a sawtooth of pinnacles and small ledges.
    # Style 1, Mounds: rounded banded haystacks (Yellow Mounds, Petrified Forest). P1 how dissected the
    # wall line is, P2 how sharp the spurs erosion starts from.
    bx, by = sep.outputs["X"], sep.outputs["Y"]
    meander = math('MULTIPLY', math('SUBTRACT', noise(vec(math('MULTIPLY', bx, 1.6), seed_val, 3.3), 'FBM', 1.0, 2.0, 0.5).outputs["Fac"], 0.5), 0.7)
    scallop = math('MULTIPLY', math('SUBTRACT', noise(p, 'FBM', math('MULTIPLY', inp["Feature Scale"], math('MULTIPLY', density, 0.35)), 2.0, 0.5)
                                    .outputs["Fac"], 0.5), 0.25)
    wall_line = math('ADD', math('ADD', math('ADD', by, meander), scallop), math('MULTIPLY', math('SUBTRACT', spur, 0.5), 0.05))
    table = smooth(wall_line, -0.02, 0.02)
    remnant = smooth(noise(p, 'FBM', math('MULTIPLY', inp["Feature Scale"], 0.45), 2.0, 0.5).outputs["Fac"], 0.66, 0.68)
    remnant = math('MULTIPLY', remnant, smooth(wall_line, -0.12, -0.2))  # out on the floor, not crowding the wall
    # The table rises gently away from the wall, so it drains to the rim: a dead-flat table let tiny
    # differences decide where water ran, and the gullies came out different at each size (T1).
    table = math('MULTIPLY', table, math('ADD', 1.0, math('MULTIPLY', math('MINIMUM', math('MAXIMUM', wall_line, 0.0), 0.6), 0.12)))
    upper = math('MAXIMUM', table, remnant)
    apron = math('MULTIPLY', math('POWER', smooth(wall_line, -0.3, -0.01), 2.0), 0.12)  # concave rise to the wall foot
    wall_style = math('ADD', math('ADD', math('MAXIMUM', upper, apron), math('MULTIPLY', tilt, 0.15)),
                      math('MULTIPLY', math('SUBTRACT', bend, 0.5), 0.05))
    # Mounds: separate haystacks (Mike, Pass 5: they read as lumpy hills). Each is a bell, round-topped
    # with a flaring foot, about the spacing across, so neighbours meet only in low saddles and narrow
    # flats; heights vary. The two nearest mounds are both drawn (max), so cells meet without seams.
    def haystack(feature):
        vn = N.new('ShaderNodeTexVoronoi')
        vn.voronoi_dimensions = '2D'
        vn.feature = feature
        vn.inputs["Randomness"].default_value = 0.9
        L.new(p2, vn.inputs["Vector"])
        L.new(math('MULTIPLY', inp["Feature Scale"], 1.2), vn.inputs["Scale"])  # 0.7: wide low swells, ~1:3 (real haystacks ~1:1.5)
        rnd = N.new('FunctionNodeSeparateColor')
        L.new(vn.outputs["Color"], rnd.inputs[0])
        size = math('ADD', 0.42, math('MULTIPLY', rnd.outputs[1], 0.13))  # foot radius in spacings: 0.42-0.55 (bigger let a third mound cut seams)
        # Bell profile: round top, steepest part of the flank about halfway out, flaring concave foot
        # (a sheer-sided dome cut a moat around every base once eroded).
        bell = math('POWER', smooth(math('DIVIDE', vn.outputs["Distance"], size), 1.0, 0.0), 0.55)  # fuller, rounder shoulders
        return math('MULTIPLY', bell, math('ADD', 0.7, math('MULTIPLY', rnd.outputs[0], 0.6)))
    dome = math('MAXIMUM', haystack('F1'), haystack('F2'))
    mound_style = math('ADD', dome, math('ADD', math('MULTIPLY', tilt, 0.15), math('MULTIPLY', math('SUBTRACT', spur, 0.5), 0.03)))
    bad_p = pick_field(inp["Style"], (wall_style, mound_style))
    badlands = math('ADD', badlands, math('MULTIPLY', math('SUBTRACT', bad_p, badlands), inp["Primary"]))
    # Hard: thin beds every so often up the wall (ledges) and a thin cap at the top (pinnacle tips).
    beds = smooth(math('ADD', math('MULTIPLY', math('SINE', math('MULTIPLY', bad_p, 44.0)), 0.5), 0.5), 0.86, 0.95)
    hard_bad = math('MAXIMUM', math('MULTIPLY', beds, 0.6), math('MULTIPLY', smooth(bad_p, 0.85, 0.95), 0.5))

    # Recipe 8, volcanic: overlapping lava-flow lobes on a broad gently sloping plain, a few cinder
    # cones (Craters of the Moon 1 m lidar, Pass 2: real relief is broad, ours was dotted cones on flat).
    # Each lobe is a tongue stretched down the plain's slope (+X): a low dome with a steep front a few
    # meters high and pressure ridges across its top; younger lobes lie over older ones.
    flow_v = N.new('ShaderNodeVectorMath')
    flow_v.operation = 'MULTIPLY'
    L.new(p, flow_v.inputs[0])
    flow_v.inputs[1].default_value = (0.6, 1.0, 1.0)  # 0.35 streaked the whole field one way (lidar streaks 5 vs 1.1)
    plain = math('ADD', math('MULTIPLY', noise(p, 'FBM', math('MULTIPLY', inp["Feature Scale"], 0.3), 4.0, 0.6).outputs["Fac"], 2.2),  # 1.4, 2 octaves: too little broad relief (s64 2x real)
                 math('MULTIPLY', sep.outputs["X"], -0.3))  # a gentle regional slope; lobes and cones carry the relief (Mike: "I don't see anything")
    lobes = plain
    for sc, cut_at, tall in ((0.8, 0.52, 0.2), (1.3, 0.55, 0.14), (2.1, 0.57, 0.1), (3.4, 0.6, 0.07)):  # lower fronts: 64 m relief was 2x real
        ln = noise(flow_v.outputs[0], 'FBM', math('MULTIPLY', inp["Feature Scale"], sc), 3.0, 0.5).outputs["Fac"]
        front = smooth(ln, cut_at, cut_at + 0.03)  # flow front (0.012 stood too sharp: 1 m slope90 40 vs 25 real)
        dome = smooth(ln, cut_at, cut_at + 0.12)     # low rounded top behind it
        lobes = math('ADD', lobes, math('MULTIPLY', math('ADD', math('MULTIPLY', front, 0.6), math('MULTIPLY', dome, 0.4)), tall))
        # each lobe gets its own slice of the noise
        flow_shift = N.new('ShaderNodeVectorMath')
        flow_shift.operation = 'ADD'
        L.new(flow_v.outputs[0], flow_shift.inputs[0])
        flow_shift.inputs[1].default_value = (3.1, 7.7, 1.9)
        flow_v = flow_shift
    ridge_v = N.new('ShaderNodeVectorMath')  # pressure ridges run across the flow
    ridge_v.operation = 'MULTIPLY'
    L.new(p, ridge_v.inputs[0])
    ridge_v.inputs[1].default_value = (1.0, 0.3, 1.0)
    pressure = math('MULTIPLY', soft_ridge(noise(ridge_v.outputs[0], 'FBM', math('MULTIPLY', inp["Feature Scale"], 14.0), 2.0, 0.5)
                                           .outputs["Fac"], 0.2), 0.012)
    cells = N.new('ShaderNodeTexVoronoi')
    cells.voronoi_dimensions = '2D'
    cells.inputs["Randomness"].default_value = 0.6  # 1.0 put sites near cell edges and sliced cones into flat faces
    L.new(p2, cells.inputs["Vector"])
    L.new(math('MULTIPLY', inp["Feature Scale"], 2.5), cells.inputs["Scale"])
    cell_rand = N.new('FunctionNodeSeparateColor')
    L.new(cells.outputs["Color"], cell_rand.inputs[0])
    cone_here = smooth(cell_rand.outputs[0], 0.9, 0.92)  # a few cones, not a field of dots
    cone_r = math('ADD', 0.16, math('MULTIPLY', cell_rand.outputs[1], 0.12))  # each cone its own size; stays inside its cell (0.45 hit the edges)
    # Cinder cone (Mike, Pass 8: a smooth flat-topped stump): straight scoria flanks at the angle of repose,
    # a wide summit crater with a sharp rim, and radial rills and gullies down every flank (SP Crater,
    # Sunset Crater).
    u_c = math('DIVIDE', cells.outputs["Distance"], cone_r)  # 0 at the centre, 1 at the foot
    flank = math('MINIMUM', math('MULTIPLY', math('MAXIMUM', math('SUBTRACT', 1.0, u_c), 0.0), 1.55), 1.0)  # straight sides
    flank = math('MULTIPLY', flank, smooth(u_c, 1.0, 0.85))  # a short concave foot, no hard crease at the base
    cone = math('MULTIPLY', flank, math('DIVIDE', cone_r, 0.4))  # small cones are low; ~1:5 tall to wide
    cone_crater = math('MULTIPLY', smooth(u_c, 0.4, 0.15), math('MULTIPLY', math('DIVIDE', cone_r, 0.4), 0.45))  # wide, deep bowl
    site = N.new('ShaderNodeSeparateXYZ')
    L.new(cells.outputs["Position"], site.inputs[0])
    here2 = N.new('ShaderNodeSeparateXYZ')
    L.new(p2, here2.inputs[0])
    c_ang = math('ARCTAN2', math('SUBTRACT', here2.outputs["Y"], site.outputs["Y"]), math('SUBTRACT', here2.outputs["X"], site.outputs["X"]))
    rill_n = noise(vec(math('MULTIPLY', math('COSINE', c_ang), 3.0), math('MULTIPLY', math('SINE', c_ang), 3.0),
                       math('ADD', math('MULTIPLY', u_c, 0.8), math('MULTIPLY', cell_rand.outputs[2], 40.0))), 'FBM', 4.0, 3.0, 0.55).outputs["Fac"]
    rills = math('MULTIPLY', math('SUBTRACT', soft_ridge(rill_n, 0.25), 0.6),
                 math('MULTIPLY', math('MULTIPLY', smooth(u_c, 0.4, 0.55), smooth(u_c, 1.0, 0.8)), math('MULTIPLY', math('DIVIDE', cone_r, 0.4), 0.2)))
    cinder = math('MULTIPLY', math('ADD', math('SUBTRACT', cone, cone_crater), rills), cone_here)
    volcanic = math('ADD', math('ADD', lobes, pressure),
                    math('ADD', math('MULTIPLY', cinder, 0.45), math('MULTIPLY', noise(p, 'FBM', math('MULTIPLY', inp["Feature Scale"], 30.0), 4.0, 0.6).outputs["Fac"], 0.012)))  # rough lava surface
    # Broken aa rubble on every flow (photo review, Craters of the Moon 1 m lidar: slope50 10 deg, ours 3.6 on
    # smooth flow tops): folded noise reads as jagged blocks and ridges down to a meter or two. Rock grain
    # can't do it here: it only starts below the shape's own detail, and this type isn't eroded.
    rubble = math('MULTIPLY', math('ADD', soft_ridge(noise(p, 'FBM', math('MULTIPLY', inp["Feature Scale"], 40.0), 8.0, 0.72).outputs["Fac"], 0.1),
                                       soft_ridge(noise(p, 'FBM', math('MULTIPLY', inp["Feature Scale"], 97.0), 7.0, 0.72).outputs["Fac"], 0.1)), 0.5)  # two scales: one made a spectrum spike
    volcanic = math('ADD', volcanic, math('MULTIPLY', math('SUBTRACT', rubble, 0.5), math('ADD', 0.03, math('MULTIPLY', inp["Roughness"], 0.12))))

    # Recipe 9, glacial valley (Pass 7, from Yosemite photos): a flat floor between sheer granite walls
    # that stand straight up from it and round over at an even rim (El Capitan, Half Dome); above the rim,
    # mountains with ridges every way; side valleys run down to the trough but stop at the rim, so they
    # hang high on the wall (Bridalveil, Yosemite Falls). Pass 4's walls borrowed the Mountains spines,
    # which ran parallel to the trough and pinched a second valley in beside it.
    axis = math('MULTIPLY', math('SUBTRACT', noise(vec(x, 0.0, seed_val), 'FBM', 2.2, 1.0, 0.5).outputs["Fac"], 0.5),
                math('ADD', math('MULTIPLY', inp["Warp"], 2.0), 0.9))  # the trough bends; Warp at its default ran it straight across (Pass 3 sheet)
    across = math('DIVIDE', math('ABSOLUTE', math('SUBTRACT', y, axis)),
                  math('ADD', 0.08, math('MULTIPLY', inp["P1"], 0.3)))  # P1 valley width; floor is across < 1
    # Wall: steepest at its foot, rounding over at the rim (1 - (1 - s)^2 over 0.35 of the half-width).
    ws = math('MINIMUM', math('MAXIMUM', math('DIVIDE', math('SUBTRACT', across, 1.0), 0.35), 0.0), 1.0)
    rim_h = math('ADD', 0.62, math('MULTIPLY', math('SUBTRACT', noise(vec(math('MULTIPLY', x, 3.0), seed_val, 5.1), 'FBM', 1.0, 1.0, 0.5).outputs["Fac"], 0.5), 0.15))
    wall = math('MULTIPLY', math('SUBTRACT', 1.0, math('POWER', math('SUBTRACT', 1.0, ws), 2.0)), rim_h)
    # Uplands: drained mountains beyond the rim, rising away from it.
    up = smooth(across, 1.35, 2.6)
    upland = math('MULTIPLY', math('MULTIPLY', mountains, up), 1.5)
    # Hanging valleys: side valleys at intervals along the trough, cut into the uplands but never below
    # the rim, so their floors end high on the wall.
    t_phase = math('ADD', math('MULTIPLY', x, math('MULTIPLY', inp["Feature Scale"], 1.6)),
                   math('MULTIPLY', math('SUBTRACT', noise(vec(x, y, seed_val), 'FBM', 3.0, 2.0, 0.5).outputs["Fac"], 0.5), 2.0))
    trib = math('POWER', math('SUBTRACT', 1.0, math('ABSOLUTE', math('SUBTRACT', math('MULTIPLY', math('FRACT', t_phase), 2.0), 1.0))), 3.0)
    upland = math('MULTIPLY', upland, math('SUBTRACT', 1.0, math('MULTIPLY', trib, math('MULTIPLY', smooth(across, 4.0, 1.4), 0.6))))
    glacial = math('ADD', math('ADD', wall, upland), math('MULTIPLY', base, 0.03))
    # Primary: the trough floor falls along the valley
    glacial = math('ADD', glacial, math('MULTIPLY', math('SUBTRACT', math('ADD', glacial, math('MULTIPLY', tilt, 0.8)), glacial), inp["Primary"]))
    hard_glacial = math('MAXIMUM', math('MULTIPLY', math('MULTIPLY', smooth(across, 0.98, 1.05), smooth(across, 1.5, 1.3)), 0.95),
                        math('MULTIPLY', smooth(across, 1.3, 1.6), 0.35))  # sheer granite walls; domes and uplands firm

    # Recipe 10, riverbed: a wide nearly flat gravel floor with braided channels running along X
    # (noise stretched along the flow), and banks rising at the sides.
    flow = N.new('ShaderNodeVectorMath')
    flow.operation = 'MULTIPLY'
    L.new(p, flow.inputs[0])
    flow.inputs[1].default_value = (0.25, 1.0, 1.0)
    braids = math('ADD', 0.8, math('MULTIPLY', inp["P1"], 3.2))  # P1 channel count
    braid_n = noise(flow.outputs[0], 'FBM', math('MULTIPLY', inp["Feature Scale"], braids), 3.0, 0.5,
                    warp_amount).outputs["Fac"]
    braid = smooth(math('ABSOLUTE', math('SUBTRACT', math('MULTIPLY', braid_n, 2.0), 1.0)), 0.0, 0.1)
    # Braids split and rejoin (photo review): a second, offset channel field; the bed is the lower of the
    # two, so channels cross, part around bars and merge again.
    flow2 = N.new('ShaderNodeVectorMath')
    flow2.operation = 'ADD'
    L.new(flow.outputs[0], flow2.inputs[0])
    flow2.inputs[1].default_value = (5.3, 2.1, 7.7)
    braid_n2 = noise(flow2.outputs[0], 'FBM', math('MULTIPLY', inp["Feature Scale"], math('MULTIPLY', braids, 1.4)), 3.0, 0.5).outputs["Fac"]
    braid2 = smooth(math('ABSOLUTE', math('SUBTRACT', math('MULTIPLY', braid_n2, 2.0), 1.0)), 0.0, 0.08)
    braid = math('MINIMUM', braid, math('ADD', braid2, 0.15))
    bank = smooth(math('ABSOLUTE', y), 0.32, 0.48)
    # Roughness: cobble and gravel texture on the bars and how ragged the channel edges are (it did little).
    gravel = math('MULTIPLY', math('SUBTRACT', noise(p, 'FBM', math('MULTIPLY', inp["Feature Scale"], 12.0), detail, 0.6).outputs["Fac"], 0.5),
                  math('ADD', 0.01, math('MULTIPLY', inp["Roughness"], 0.35)))
    ragged = math('MULTIPLY', math('SUBTRACT', noise(flow.outputs[0], 'FBM', math('MULTIPLY', inp["Feature Scale"], math('MULTIPLY', braids, 6.0)), 2.0, 0.5)
                                   .outputs["Fac"], 0.5), math('MULTIPLY', inp["Roughness"], 0.5))
    riverbed = math('ADD', math('ADD', math('MULTIPLY', math('ADD', braid, ragged), 0.25), math('MULTIPLY', bank, 0.7)), gravel)
    # Primary: the whole bed falls down-valley
    riverbed = math('ADD', riverbed, math('MULTIPLY', math('SUBTRACT', math('ADD', riverbed, math('MULTIPLY', tilt, 0.4)), riverbed), inp["Primary"]))

    # Recipe 11, volcano: one hero volcano at the centre. Style picks the profile
    # (0 stratovolcano, 1 shield, 2 cinder cone, 3 caldera, 4 collapsed). P1 crater size, P2 steepness,
    # P3 gullies, P4 breach, P5 crater depth, P6 rim thickness. r runs 0 (centre) .. 1 (foot).
    style = inp["Style"]
    radius = math('DIVIDE', pick_float(style, (0.48, 0.5, 0.42, 0.5, 0.5)),
                  math('DIVIDE', inp["Feature Scale"], 1.5))
    # No real volcano is round (Mike, Pass 3): the summit sits off centre and the outline is lopsided,
    # both set by the seed, so flanks differ in length and steepness.
    lop_amt = pick_float(style, (0.6, 0.5, 0.12, 0.45, 0.6))  # cinder cones are nearly round
    off_x = math('MULTIPLY', math('SUBTRACT', noise(vec(seed_val, 1.3, 0.0), 'FBM', 1.0, 0.0, 0.5).outputs["Fac"], 0.5), math('MULTIPLY', radius, math('MULTIPLY', lop_amt, 0.7)))
    off_y = math('MULTIPLY', math('SUBTRACT', noise(vec(seed_val, 4.7, 0.0), 'FBM', 1.0, 0.0, 0.5).outputs["Fac"], 0.5), math('MULTIPLY', radius, math('MULTIPLY', lop_amt, 0.7)))
    xo, yo = math('SUBTRACT', x, off_x), math('SUBTRACT', y, off_y)
    theta = math('ARCTAN2', yo, xo)
    lop = noise(vec(math('MULTIPLY', math('COSINE', theta), 1.1), math('MULTIPLY', math('SINE', theta), 1.1), math('ADD', seed_val, 2.2)),
                'FBM', 1.0, 0.0, 0.5).outputs["Fac"]  # one smooth octave: more made a scalloped flower outline
    d_round = math('DIVIDE', math('SQRT', math('ADD', math('MULTIPLY', xo, xo), math('MULTIPLY', yo, yo))), radius)
    # Lopsided at the foot, round at the summit (a wobbling crater rim looked scalloped).
    radius_t = math('MULTIPLY', radius, math('ADD', 1.0, math('MULTIPLY', math('MULTIPLY', math('SUBTRACT', lop, 0.5), lop_amt),
                                                                     smooth(d_round, 0.25, 0.85))))
    # Always inside the landscape (Mike, Pass 8: a lopsided foot ran off the edge): in each direction the foot
    # stops short of the border, measured from the off-centre summit, with a margin for the warp.
    dist_o = math('MAXIMUM', math('SQRT', math('ADD', math('MULTIPLY', xo, xo), math('MULTIPLY', yo, yo))), 1e-6)
    dir_c, dir_s = math('DIVIDE', xo, dist_o), math('DIVIDE', yo, dist_o)
    margin = math('ADD', 0.03, math('MULTIPLY', inp["Warp"], 0.08))
    half_x = math('SUBTRACT', math('DIVIDE', size_x, math('MULTIPLY', ref, 2.0)), margin)
    half_y = math('SUBTRACT', math('DIVIDE', size_y, math('MULTIPLY', ref, 2.0)), margin)
    to_x = math('DIVIDE', math('SUBTRACT', half_x, math('MULTIPLY', off_x, math('SIGN', dir_c))), math('MAXIMUM', math('ABSOLUTE', dir_c), 1e-4))
    to_y = math('DIVIDE', math('SUBTRACT', half_y, math('MULTIPLY', off_y, math('SIGN', dir_s))), math('MAXIMUM', math('ABSOLUTE', dir_s), 1e-4))
    radius_t = math('MINIMUM', radius_t, math('MAXIMUM', math('MINIMUM', to_x, to_y), 0.05))
    r = math('DIVIDE', math('SQRT', math('ADD', math('MULTIPLY', xo, xo), math('MULTIPLY', yo, yo))), radius_t)
    collapsed = pick_float(style, (0.0, 0.0, 0.0, 0.0, 1.0))
    exponent = math('ADD', pick_float(style, (0.6, 0.3, 0.7, 1.1, 0.6)),
                    math('MULTIPLY', inp["P2"], pick_float(style, (2.0, 0.6, 0.6, 1.0, 2.0))))
    crater_r = math('MULTIPLY', inp["P1"], pick_float(style, (0.4, 0.22, 0.6, 0.85, 0.9)))
    # No perfect circles (Mike): the crater edge wanders in and out, the rim rises and dips around it.
    rim_n = noise(vec(math('MULTIPLY', math('COSINE', theta), 1.6), math('MULTIPLY', math('SINE', theta), 1.6), math('ADD', seed_val, 7.7)),
                  'FBM', 1.0, 2.0, 0.55).outputs["Fac"]
    rim_h = noise(vec(math('MULTIPLY', math('COSINE', theta), 2.6), math('MULTIPLY', math('SINE', theta), 2.6), math('ADD', seed_val, 4.1)),
                  'FBM', 1.0, 2.0, 0.55).outputs["Fac"]
    crater_r = math('MULTIPLY', crater_r, math('ADD', 1.0, math('MULTIPLY', math('SUBTRACT', rim_n, 0.5), 0.4)))
    rim_w = math('ADD', 0.015, math('MULTIPLY', inp["P6"], 0.2))   # flat band of rim that always stays
    rim_out = math('MINIMUM', math('ADD', crater_r, rim_w), 0.95)
    # Flank starts at the outer edge of the rim, so the summit keeps its thickness.
    t = math('DIVIDE', math('MAXIMUM', math('SUBTRACT', r, rim_out), 0.0),
             math('MAXIMUM', math('SUBTRACT', 1.0, rim_out), 1e-3))
    flank = math('POWER', math('MAXIMUM', math('SUBTRACT', 1.0, t), 0.0), exponent)
    flank = math('MULTIPLY', flank, smooth(r, 1.05, 0.9))
    # Gullies: broad channels down the flank, fading out before the rim and at the foot.
    ring = noise(vec(math('MULTIPLY', math('COSINE', theta), 2.0), math('MULTIPLY', math('SINE', theta), 2.0),
                     math('ADD', math('MULTIPLY', r, 1.2), seed_val)), 'FBM', 2.0, 1.0, 0.5).outputs["Fac"]
    channel = math('SUBTRACT', 1.0, soft_ridge(ring, 0.15))
    on_flank = math('MULTIPLY', smooth(t, 0.0, 0.25), smooth(t, 1.0, 0.75))
    gully = math('MULTIPLY', math('MULTIPLY', channel, inp["P3"]),
                 math('MULTIPLY', on_flank, math('MULTIPLY', 0.18, pick_float(style, (1.0, 1.0, 0.3, 1.0, 1.0)))))
    cone_h = math('SUBTRACT', flank, gully)
    # Crater: steep walls down to a rough floor; P5 sets how deep.
    depth = math('MULTIPLY', inp["P5"], pick_float(style, (0.6, 0.35, 0.8, 0.85, 0.9)))
    u = math('DIVIDE', r, math('MAXIMUM', crater_r, 1e-3))
    bowl = math('SUBTRACT', 1.0, math('POWER', math('MINIMUM', u, 1.0), 4.0))
    floor_rough = math('MULTIPLY', math('SUBTRACT', noise(p, 'FBM', math('MULTIPLY', inp["Feature Scale"], 12.0),
                                                          4.0, 0.6).outputs["Fac"], 0.5), 0.08)
    inside = math('SUBTRACT', 1.0, math('MULTIPLY', depth, math('ADD', bowl, math('MULTIPLY', floor_rough, bowl))))
    # Chutes and ribs down the inner walls, so the wall doesn't read as smooth concentric bands.
    chute = noise(vec(math('MULTIPLY', math('COSINE', theta), 9.0), math('MULTIPLY', math('SINE', theta), 9.0),
                      math('ADD', math('MULTIPLY', u, 1.5), seed_val)), 'FBM', 1.0, 3.0, 0.6).outputs["Fac"]
    in_wall = math('MULTIPLY', smooth(u, 0.45, 0.8), smooth(u, 1.02, 0.95))
    inside = math('SUBTRACT', inside, math('MULTIPLY', math('SUBTRACT', chute, 0.5), math('MULTIPLY', in_wall, math('MULTIPLY', depth, 0.35))))
    in_crater = smooth(r, crater_r, math('MULTIPLY', crater_r, 0.9))
    lip_c = math('ADD', crater_r, math('MULTIPLY', rim_w, 0.45))
    lip_w = math('ADD', math('MULTIPLY', rim_w, 0.6), 0.01)
    lip = math('MULTIPLY', math('EXPONENT', math('MULTIPLY', math('POWER', math('DIVIDE', math('SUBTRACT', r, lip_c), lip_w),
                                                                      2.0), -1.0)), math('MULTIPLY', 0.06, math('ADD', 0.2, math('MULTIPLY', rim_h, 1.6))))
    cone_h = math('ADD', cone_h, lip)
    shaped_cone = math('ADD', math('MULTIPLY', cone_h, math('SUBTRACT', 1.0, in_crater)),
                       math('MULTIPLY', inside, in_crater))
    # P7 Inner Cone (photo review): Caldera gets an island cinder cone off to one side of the floor, with
    # its own small summit crater (Wizard Island, Crater Lake); Strato a rounded, rubbly lava dome near the
    # middle (Mount St Helens). Other styles have none.
    in_off = pick_float(style, (0.12, 0.0, 0.0, 0.42, 0.0))
    in_size = pick_float(style, (0.38, 0.0, 0.0, 0.3, 0.0))
    in_tall = pick_float(style, (0.85, 0.0, 0.0, 1.0, 0.0))  # at P7 0.6: Wizard Island stands ~0.4-0.6 of the caldera depth
    in_ang = math('MULTIPLY', seed_val, 2.39)
    ix = math('SUBTRACT', math('DIVIDE', xo, radius_t), math('MULTIPLY', math('COSINE', in_ang), math('MULTIPLY', crater_r, in_off)))
    iy = math('SUBTRACT', math('DIVIDE', yo, radius_t), math('MULTIPLY', math('SINE', in_ang), math('MULTIPLY', crater_r, in_off)))
    ri = math('DIVIDE', math('SQRT', math('ADD', math('MULTIPLY', ix, ix), math('MULTIPLY', iy, iy))),
              math('MAXIMUM', math('MULTIPLY', crater_r, in_size), 1e-3))
    is_cal = pick_float(style, (0.0, 0.0, 0.0, 1.0, 0.0))
    cone_in = math('SUBTRACT', smooth(ri, 1.0, 0.0), math('MULTIPLY', smooth(ri, 0.3, 0.05), 0.3))  # cinder cone, small crater
    dome_in = math('POWER', math('MAXIMUM', math('SUBTRACT', 1.0, math('MULTIPLY', ri, ri)), 0.0), 0.6)  # round-shouldered dome
    in_shape = math('ADD', math('MULTIPLY', cone_in, is_cal), math('MULTIPLY', dome_in, math('SUBTRACT', 1.0, is_cal)))
    in_shape = math('ADD', in_shape, math('MULTIPLY', math('SUBTRACT', noise(p, 'FBM', math('MULTIPLY', inp["Feature Scale"], 30.0), 4.0, 0.6).outputs["Fac"], 0.5),
                                    math('MULTIPLY', smooth(ri, 1.0, 0.6), 0.25)))  # rubble
    inner_top = math('ADD', math('SUBTRACT', 1.0, depth), math('MULTIPLY', math('MULTIPLY', in_shape, math('MULTIPLY', depth, in_tall)), inp["P7"]))
    shaped_cone = math('ADD', shaped_cone, math('MULTIPLY', in_crater, math('MAXIMUM', math('SUBTRACT', inner_top, shaped_cone), 0.0)))
    # Breach (+X): a lava outflow. Inside a smooth-edged sector the volcano is capped by a ramp
    # that runs from the crater floor down to the foot, so the rim opens and the slope below drops.
    facing = math('DIVIDE', xo, math('MAXIMUM', math('MULTIPLY', r, radius_t), 1e-5))
    # Collapsed: the breach is a wide horseshoe amphitheater (St Helens 1980) whatever the Breach slider.
    breach_amt = math('MAXIMUM', inp["P4"], math('MULTIPLY', collapsed, 0.9))
    open_at = math('SUBTRACT', 1.0, math('MULTIPLY', breach_amt, 0.6))
    # The breach walls wander as they run downhill instead of two straight wedge edges (Mike).
    edge_w = math('MULTIPLY', math('SUBTRACT', noise(vec(math('MULTIPLY', r, 3.5), math('MULTIPLY', yo, 4.0), math('ADD', seed_val, 2.9)),
                                                     'FBM', 1.0, 2.0, 0.55).outputs["Fac"], 0.5), 0.45)
    open_at = math('ADD', open_at, edge_w)
    sector = math('MULTIPLY', smooth(facing, open_at, math('ADD', open_at, 0.18)), smooth(breach_amt, 0.0, 0.05))
    floor_top = math('SUBTRACT', 1.0, depth)
    ramp = math('MULTIPLY', floor_top, math('POWER', math('MAXIMUM', math('SUBTRACT', 1.0,
                                       math('DIVIDE', math('MAXIMUM', math('SUBTRACT', r, crater_r), 0.0),
                                            math('MAXIMUM', math('SUBTRACT', 1.0, crater_r), 1e-3))), 0.0), 1.3))
    # Meandering lava/debris channels down the breach floor, plus rubble, so it isn't a clean ramp.
    wander_b = math('MULTIPLY', math('SUBTRACT', noise(vec(math('MULTIPLY', r, 4.0), seed_val, 1.3), 'FBM', 1.0, 2.0, 0.5).outputs["Fac"], 0.5), 0.5)
    b_chan = noise(vec(math('MULTIPLY', math('ADD', math('DIVIDE', yo, math('MAXIMUM', radius, 1e-3)), wander_b), 5.0),
                       math('MULTIPLY', r, 1.5), math('ADD', seed_val, 6.1)), 'FBM', 1.0, 1.0, 0.5).outputs["Fac"]
    b_cut = math('MULTIPLY', smooth(soft_ridge(b_chan, 0.15), 0.75, 1.0), math('MULTIPLY', floor_top, 0.07))
    b_rub = math('MULTIPLY', math('SUBTRACT', noise(p, 'FBM', math('MULTIPLY', inp["Feature Scale"], 10.0), 4.0, 0.6).outputs["Fac"], 0.5),
                 math('MULTIPLY', floor_top, 0.08))
    ramp = math('ADD', math('SUBTRACT', ramp, math('MULTIPLY', b_cut, smooth(r, crater_r, math('ADD', crater_r, 0.1)))), b_rub)
    capped = math('MINIMUM', shaped_cone, ramp)
    breached = math('ADD', math('MULTIPLY', shaped_cone, math('SUBTRACT', 1.0, sector)), math('MULTIPLY', capped, sector))
    crag = soft_ridge(noise(p, 'FBM', math('MULTIPLY', inp["Feature Scale"], 9.0), 5.0, 0.6).outputs["Fac"], 0.3)
    near_top = math('MULTIPLY', smooth(t, 0.45, 0.0), smooth(r, math('MULTIPLY', crater_r, 0.85), crater_r))
    rocky = math('MULTIPLY', math('SUBTRACT', crag, 0.5), math('MULTIPLY', near_top, 0.07))
    # Collapsed: hummocky avalanche debris spreads out below the breach.
    hummocks = noise(p, 'FBM', math('MULTIPLY', inp["Feature Scale"], 7.0), 2.0, 0.5).outputs["Fac"]
    debris = math('MULTIPLY', math('MULTIPLY', smooth(facing, 0.3, 0.7), math('MULTIPLY', smooth(r, 0.55, 0.85), smooth(r, 1.6, 1.15))),
                  math('MULTIPLY', math('ADD', 0.04, math('MULTIPLY', smooth(hummocks, 0.45, 0.7), 0.08)), collapsed))
    # Roughness: crags near the summit and rubbly flanks (it only moved a faint 4% noise before; Mike).
    v_rough = math('ADD', 0.2, math('MULTIPLY', inp["Roughness"], 2.2))
    rubble = math('MULTIPLY', math('SUBTRACT', noise(p, 'FBM', math('MULTIPLY', inp["Feature Scale"], 4.0), 5.0, 0.62).outputs["Fac"], 0.5),
                  math('MULTIPLY', math('MULTIPLY', smooth(r, 1.15, 0.9), smooth(r, 0.0, 0.2)), 0.13))
    ground = math('MULTIPLY', base, math('MULTIPLY', 0.04, v_rough))
    above = math('ADD', math('ADD', breached, math('MULTIPLY', math('ADD', rocky, rubble), v_rough)), debris)
    # Never below the surrounding ground (Mike, Pass 8: deep gullies and rubble at the foot dug under the
    # plain, and a low Peak Sharpness stretched those dips into long needles hanging under the base).
    above = math('MAXIMUM', above, 0.0)
    # And always inside the landscape: whatever reaches past the foot (collapse debris) fades out before
    # the border, as the foot itself does (radius cap above).
    room = math('MINIMUM', math('SUBTRACT', half_x, math('ABSOLUTE', x)), math('SUBTRACT', half_y, math('ABSOLUTE', y)))
    above = math('MULTIPLY', above, smooth(room, 0.0, margin))
    volcano = math('ADD', above, ground)

    # Recipe 12, craters: an impact-cratered surface, tuned against LROC 2 m elevation of the Moon
    # (Linne, Apollo 14 and 16; docs/REALISM.md). P1 count, P2 size, P3 surface age, P4 variety.
    # Heights are built in true proportion (normalised-position units), so depth/diameter holds:
    # fresh craters 0.2 deep, rim 0.035 D, worn ones 0.03. Each crater has its own age; Age shifts the
    # mix, so an old surface is mostly soft "ghost" craters with a few fresh ones, as on the Moon.
    # Each point sees its two nearest crater sites (Voronoi F1, F2); the nearest cuts into the other.
    density = math('ADD', 0.03, math('MULTIPLY', inp["P1"], 0.97))  # share of sites that get a crater
    # Wear spread: fresh-crater share ~70% at Age 0, ~5% at 0.6 (the Apollo fields), ~1% at 1.
    age_k = math('MULTIPLY', 0.36, math('EXPONENT', math('MULTIPLY', inp["P3"], 4.9)))
    regolith = noise(p, 'FBM', math('MULTIPLY', inp["Feature Scale"], 12.0), detail,
                     math('ADD', 0.4, math('MULTIPLY', inp["Roughness"], 0.25))).outputs["Fac"]
    rolling = noise(p, 'FBM', math('MULTIPLY', inp["Feature Scale"], 0.6), 3.0, 0.5).outputs["Fac"]
    rolling = math('MULTIPLY', math('SUBTRACT', rolling, 0.5), 0.08)
    # Crater relief builds up on its own and the rolling ground is added last: erasing toward zero
    # then only removes older crater relief, never cuts a step into the slope.
    surface = math('MULTIPLY', math('SUBTRACT', regolith, 0.5), math('ADD', 0.0005, math('MULTIPLY', inp["Roughness"], 0.002)))

    def crater_layer(h, scale, old_bias, detailed):
        prev = None  # the second-nearest crater's relief, which the nearest one cuts into
        for feature in ('F2', 'F1'):  # nearest site last, so it sits on top
            cells = N.new('ShaderNodeTexVoronoi')
            cells.voronoi_dimensions = '2D'
            cells.feature = feature
            cells.inputs["Randomness"].default_value = 0.8
            L.new(p2, cells.inputs["Vector"])
            L.new(scale, cells.inputs["Scale"])
            rnd = N.new('FunctionNodeSeparateColor')
            L.new(cells.outputs["Color"], rnd.inputs[0])
            r_size, r_keep, r_shape = rnd.outputs[0], rnd.outputs[1], rnd.outputs[2]
            exists = smooth(r_keep, math('ADD', density, 0.02), density)
            # This crater's wear: 0 fresh .. 1 a ghost. Older layers (bigger craters) lean old.
            u = math('FRACT', math('MULTIPLY', math('ADD', r_size, r_shape), 31.7))
            wear = math('SUBTRACT', 1.0, math('POWER', math('SUBTRACT', 1.0, u), age_k))
            bias = math('MULTIPLY', old_bias, math('ADD', 0.3, math('MULTIPLY', inp["P3"], 0.7)))
            wear = math('ADD', bias, math('MULTIPLY', wear, math('SUBTRACT', 1.0, bias)))
            fresh = math('SUBTRACT', 1.0, wear)
            # Vector from the crater centre. Voronoi "Position" is in input space, so measure there.
            rel = N.new('ShaderNodeVectorMath')
            rel.operation = 'SUBTRACT'
            L.new(p2, rel.inputs[0])
            L.new(cells.outputs["Position"], rel.inputs[1])
            here = N.new('ShaderNodeVectorMath')
            here.operation = 'SCALE'
            L.new(rel.outputs[0], here.inputs[0])
            L.new(scale, here.inputs["Scale"])
            rs = N.new('ShaderNodeSeparateXYZ')
            L.new(here.outputs[0], rs.inputs[0])
            ang = math('MULTIPLY', r_shape, 6.2832)
            ca, sa = math('COSINE', ang), math('SINE', ang)
            lx = math('ADD', math('MULTIPLY', rs.outputs[0], ca), math('MULTIPLY', rs.outputs[1], sa))
            ly = math('SUBTRACT', math('MULTIPLY', rs.outputs[1], ca), math('MULTIPLY', rs.outputs[0], sa))
            # Nearly all craters are round; a rare low-angle impact makes a clear oval.
            f1 = math('FRACT', math('MULTIPLY', r_shape, 3.7))
            ly = math('MULTIPLY', ly, math('ADD', math('ADD', 1.0, math('MULTIPLY', f1, 0.06)),
                                          math('MULTIPLY', smooth(f1, 0.94, 0.98), 0.5)))
            dist = math('SQRT', math('ADD', math('MULTIPLY', lx, lx), math('MULTIPLY', ly, ly)))
            size = math('MULTIPLY', math('ADD', 0.14, math('MULTIPLY', inp["P2"], 0.14)),
                        math('ADD', 0.45, math('MULTIPLY', r_size, 0.55)))
            d = math('DIVIDE', dist, size)
            radius = math('DIVIDE', size, scale)  # crater radius in normalised units
            # Real-size diameter decides simple bowl vs complex crater (Moon: over ~15 km).
            complex_ = smooth(math('MULTIPLY', math('MULTIPLY', radius, ref), 2.0), 12000.0, 20000.0)
            # depth/diameter: 0.2 fresh (Linne 0.205), complex craters shallower, worn ones ~0.03.
            dd = math('MULTIPLY', math('SUBTRACT', 0.2, math('MULTIPLY', complex_, 0.11)),
                      math('SUBTRACT', 1.0, math('MULTIPLY', wear, 0.85)))
            dd = math('MULTIPLY', dd, math('ADD', 0.85, math('MULTIPLY', math('FRACT', math('MULTIPLY', r_size, 7.3)), 0.3)))
            rim_h = math('MULTIPLY', 0.035, math('POWER', fresh, 1.5))
            # Fresh: small flat floor, straight ~32 deg walls, rounded crest, ejecta falling off as d^-4.
            fresh_in = math('SUBTRACT', rim_h, math('MULTIPLY', math('ADD', dd, rim_h),
                                                    math('SUBTRACT', 1.0, smooth(d, 0.12, 1.0))))
            # Complex: flat floor out to half the radius and a central peak.
            floor_cut = math('ADD', math('MULTIPLY', dd, -1.0), math('MULTIPLY', smooth(d, 0.45, 1.0), math('ADD', dd, rim_h)))
            peak = math('MULTIPLY', math('EXPONENT', math('MULTIPLY', math('POWER', math('DIVIDE', d, 0.15), 2.0), -1.0)),
                        math('MULTIPLY', dd, 0.45))
            complex_in = math('ADD', floor_cut, peak)
            fresh_in = math('ADD', fresh_in, math('MULTIPLY', complex_, math('SUBTRACT', complex_in, fresh_in)))
            apron = math('MULTIPLY', math('MULTIPLY', rim_h, math('POWER', math('MAXIMUM', d, 1.0), -4.0)), smooth(d, 2.2, 1.6))
            if detailed:
                theta = math('ARCTAN2', ly, lx)
                # Hummocky ejecta and a slightly uneven rim on fresh craters; faint talus streaks on walls.
                ring_v = vec(math('MULTIPLY', math('COSINE', theta), 2.5), math('MULTIPLY', math('SINE', theta), 2.5),
                             math('ADD', math('MULTIPLY', d, 2.0), math('MULTIPLY', r_size, 53.0)))
                lumps = math('SUBTRACT', noise(ring_v, 'FBM', 1.0, 3.0, 0.55).outputs["Fac"], 0.5)
                apron = math('MULTIPLY', apron, math('ADD', 1.0, math('MULTIPLY', lumps, 1.2)))
                streak_v = vec(math('MULTIPLY', math('COSINE', theta), 7.0), math('MULTIPLY', math('SINE', theta), 7.0),
                               math('MULTIPLY', r_size, 41.0))
                streaks = math('SUBTRACT', noise(streak_v, 'FBM', 1.0, 2.0, 0.5).outputs["Fac"], 0.5)
                wall = math('MULTIPLY', smooth(d, 0.3, 0.6), smooth(d, 1.0, 0.85))
                fresh_in = math('ADD', fresh_in, math('MULTIPLY', math('MULTIPLY', streaks, wall), math('MULTIPLY', dd, math('MULTIPLY', fresh, 0.12))))
            fresh_prof = math('ADD', fresh_in, math('MULTIPLY', math('SUBTRACT', apron, fresh_in), smooth(d, 0.98, 1.02)))
            # Worn: diffusion leaves a wide, soft dish with no rim.
            worn_prof = math('MULTIPLY', math('MULTIPLY', dd, -1.0), math('SUBTRACT', 1.0, smooth(d, 0.0, 1.35)))
            prof = math('ADD', fresh_prof, math('MULTIPLY', wear, math('SUBTRACT', worn_prof, fresh_prof)))
            profile = math('MULTIPLY', math('MULTIPLY', prof, math('MULTIPLY', radius, 2.0)), exists)
            if prev is None:
                prev = profile
                continue
            # Overprint within the layer only: a smaller crater landing on a bigger one is carved into
            # its floor or wall (added), it doesn't flatten a disc into it.
            erase = math('MULTIPLY', smooth(d, 1.05, 0.75), math('MULTIPLY', exists, math('SUBTRACT', 0.9, math('MULTIPLY', wear, 0.6))))
            h = math('ADD', h, math('ADD', math('MULTIPLY', prev, math('SUBTRACT', 1.0, erase)), profile))
        return h

    # Variety spreads the layers apart in size: 0 = all similar, 1 = basins down to pinpricks.
    # Equal site density per layer gives the Moon's size spread, N(>D) ~ D^-2.
    spread = math('ADD', 0.15, math('MULTIPLY', inp["P4"], 0.85))
    count = math('MULTIPLY', inp["Feature Scale"], 1.25)
    craters = surface
    for mult, old_bias, detailed in ((0.35, 0.35, True), (1.0, 0.15, True), (3.0, 0.0, False), (9.0, 0.0, False),
                                     (27.0, 0.0, False), (81.0, 0.0, False)):
        craters = crater_layer(craters, math('MULTIPLY', count, math('POWER', mult, spread)), old_bias, detailed)
    craters = math('ADD', craters, rolling)

    recipes = (hills, mountains, dunes, seabed, cliffs, canyon, mesa, badlands, volcanic, glacial, riverbed, volcano,
               craters)
    # One group per recipe: only the chosen recipe is wired to the output, so Blender never
    # evaluates the other twelve (an Index Switch over fields evaluated them all, ~35% slower).
    chosen = recipes[min(max(recipe, 0), len(recipes) - 1)]
    # Universal anti-alias: blur the heights over 2 neighbouring points before stretching to Height,
    # so no feature is sharper than the mesh can draw and Height stays the exact relief.
    aa = N.new('GeometryNodeBlurAttribute')
    aa.data_type = 'FLOAT'
    L.new(chosen, aa.inputs["Value"])
    # Edge rounding is a real width, the same at every detail level: Preview's 2-point bevel
    # (2 x size / 512), capped at 2 m, never under 2 points. A fixed 2 points shrank the bevel 4x
    # at Final, so steep canyon benches folded into pinched creases (Mike, 2026-10-23).
    bevel_m = math('MINIMUM', math('DIVIDE', math('MULTIPLY', ref, 2.0), 512.0), 2.0)
    aa_iter = N.new('FunctionNodeFloatToInt')
    aa_iter.rounding_mode = 'ROUND'
    L.new(math('MINIMUM', math('MAXIMUM', math('DIVIDE', bevel_m, spacing), 2.0), 16.0), aa_iter.inputs[0])
    L.new(aa_iter.outputs[0], aa.inputs["Iterations"])
    raw = aa.outputs[0]

    # Stretch to 0..1 across this landscape, so Height is the true relief whatever the recipe.
    stats = N.new('GeometryNodeAttributeStatistic')
    stats.data_type = 'FLOAT'
    stats.domain = 'POINT'
    L.new(grid.outputs["Mesh"], stats.inputs["Geometry"])
    L.new(raw, stats.inputs["Attribute"])
    L.new(inner, stats.inputs["Selection"])  # Height is the relief of the landscape, not of its padding
    lo, hi = stats.outputs["Min"], stats.outputs["Max"]
    unit = math('DIVIDE', math('SUBTRACT', raw, lo), math('MAXIMUM', math('SUBTRACT', hi, lo), 1e-6))
    # Peak Sharpness: above 1, unit^s (pointy tops, flatter lows). Below 1, 1 - (1 - unit)^(1/s) (rounded tops,
    # full lows): unit^s has an infinite slope at 0, so at s 0.25 a 1% dip in the ground became ~30% of
    # the Height and hung under the landscape as needles (Mike, Pass 8). Both are plain unit at s = 1.
    sharp_hi = math('POWER', unit, inp["Sharpness"])
    sharp_lo = math('SUBTRACT', 1.0, math('POWER', math('MAXIMUM', math('SUBTRACT', 1.0, unit), 0.0), math('DIVIDE', 1.0, math('MAXIMUM', inp["Sharpness"], 0.05))))
    lo_side = math('LESS_THAN', inp["Sharpness"], 1.0)
    shaped = math('ADD', math('MULTIPLY', sharp_lo, lo_side), math('MULTIPLY', sharp_hi, math('SUBTRACT', 1.0, lo_side)))
    z = math('MULTIPLY', shaped, math('MULTIPLY', inp["Height"], ref))
    # Erosion (R6): the engine's eroded heights, stored per landscape as an image across the
    # landscape (in units of Height), blended in here so rock grain stays live on top (D54).
    # Absolute, not a change: adding a change to a separately sampled shape left pits.
    at = N.new('ShaderNodeSeparateXYZ')
    L.new(N.new('GeometryNodeInputPosition').outputs[0], at.inputs[0])
    # Vertex i of n lands on texel centre (i + 0.5) / n, so the map is read exactly where it was
    # computed (resampling it in Python broke 1-cell diagonal channels into chains of pits).
    info = N.new('GeometryNodeImageInfo')
    L.new(inp["Erosion Map"], info.inputs["Image"])
    tex_w = math('MAXIMUM', info.outputs["Width"], 2.0)
    tex_h = math('MAXIMUM', info.outputs["Height"], 2.0)

    def texel(coord, size, count):
        frac = math('ADD', math('DIVIDE', coord, size), 0.5)
        return math('DIVIDE', math('ADD', math('MULTIPLY', frac, math('SUBTRACT', count, 1.0)), 0.5), count)

    uv = vec(texel(at.outputs["X"], size_x, tex_w), texel(at.outputs["Y"], size_y, tex_h), 0.0)
    er_tex = N.new('GeometryNodeImageTexture')
    er_tex.interpolation = 'Cubic'  # no crease at every texel (5.7 m spectral spike, Pass 2); floors are wide enough now not to fill into pits
    er_tex.extension = 'EXTEND'
    L.new(inp["Erosion Map"], er_tex.inputs["Image"])
    L.new(uv, er_tex.inputs["Vector"])
    er_r = N.new('FunctionNodeSeparateColor')
    L.new(er_tex.outputs["Color"], er_r.inputs[0])
    eroded_z = math('MULTIPLY', er_r.outputs[0], math('MULTIPLY', inp["Height"], ref))
    z = math('ADD', z, math('MULTIPLY', math('SUBTRACT', eroded_z, z), inp["Erosion"]))

    offset = N.new('ShaderNodeCombineXYZ')
    L.new(z, offset.inputs["Z"])
    # Hard rock (0..1) for the erosion engine, stored on the flat grid so it samples the same points as
    # the shape: cliff bands, caprock and crests erode slower and stand steeper (Pass 3).
    hard_by_recipe = {4: hard_cliffs, 5: hard_canyon, 6: hard_mesa, 7: hard_bad, 9: hard_glacial}
    store = N.new('GeometryNodeStoreNamedAttribute')
    store.data_type = 'FLOAT'
    store.domain = 'POINT'
    store.inputs["Name"].default_value = "lg_hard"
    L.new(grid.outputs["Mesh"], store.inputs["Geometry"])
    if recipe in hard_by_recipe:
        L.new(hard_by_recipe[recipe], store.inputs["Value"])
    else:
        store.inputs["Value"].default_value = 0.0
    setpos = N.new('GeometryNodeSetPosition')
    L.new(store.outputs[0], setpos.inputs["Geometry"])
    if recipe == 6:
        # Mesa Floor off: the floor is exactly 0 in the shape, so mark it here, before erosion (which digs
        # small channels below it) moves anything; never while the erosion engine samples the full grid.
        cut = N.new('GeometryNodeStoreNamedAttribute')
        cut.data_type = 'BOOLEAN'
        cut.domain = 'POINT'
        cut.inputs["Name"].default_value = "lg_cut"
        L.new(store.outputs[0], cut.inputs["Geometry"])
        low = math('MULTIPLY', math('LESS_THAN', unit, 0.004), math('SUBTRACT', 1.0, keep_floor))
        floor_off = math('MULTIPLY', math('LESS_THAN', inp["P4"], 0.5), math('LESS_THAN', inp["Pad Cells"], 0.5))
        L.new(math('MULTIPLY', low, floor_off), cut.inputs["Value"])
        L.new(cut.outputs[0], setpos.inputs["Geometry"])
    L.new(offset.outputs[0], setpos.inputs["Offset"])
    shape = setpos.outputs[0]

    # R2, rock grain in real meters: rough where real land is bare rock (steep or high), nearly
    # smooth on flats and valley floors. Wavelengths from min(30 m, size/16) down to 0.5 m or 2.5 points.
    normal = N.new('GeometryNodeInputNormal').outputs[0]
    nrm = N.new('ShaderNodeSeparateXYZ')
    L.new(normal, nrm.inputs[0])
    # Rough from ~22 deg up, some texture everywhere, smooth only on flats. Starting at 35 deg (above
    # scree) lost the texture once erosion laid slopes back to their ~38 deg rest (Mike, Pass 3).
    steep = smooth(nrm.outputs["Z"], 0.93, 0.77)  # 22 to 40 degrees
    high = smooth(shaped, 0.35, 0.85)
    # Lava fields are bare rock everywhere: rough aa flows, flat or not (Craters of the Moon lidar, Pass 2).
    floor = 1.0 if recipe == 8 else 0.2
    bare = math('ADD', floor, math('MULTIPLY', math('MAXIMUM', steep, math('MULTIPLY', high, 0.35)), 1.0 - floor))
    # Grain starts where the shape's own detail stops (Detail Floor): starting at 30 m over a shape that
    # stops at 16 m made a lone bump at ~30 m, a stripe on smooth types (Hills, Riverbed; Pass 4).
    l_max = math('MINIMUM', math('MINIMUM', 30.0, math('DIVIDE', ref, 16.0)), math('MAXIMUM', inp["Detail Floor"], 1.0))
    l_min = math('MAXIMUM', 0.5, math('MULTIPLY', spacing, 2.5))
    octaves = math('MAXIMUM', math('LOGARITHM', math('DIVIDE', l_max, l_min), 2.0), 0.0)
    here = N.new('GeometryNodeInputPosition')
    rock_p = N.new('ShaderNodeVectorMath')
    rock_p.operation = 'ADD'
    L.new(here.outputs[0], rock_p.inputs[0])
    L.new(vec(math('MULTIPLY', seed_val, 13.0), math('MULTIPLY', seed_val, 7.9), 0.0), rock_p.inputs[1])
    grain = noise(rock_p.outputs[0], 'FBM', math('DIVIDE', 1.0, l_max), octaves, inp["Grain Roughness"]).outputs["Fac"]
    amount = math('MULTIPLY', math('MULTIPLY', inp["Rock"], bare),
                  math('MULTIPLY', math('ADD', 0.4, math('MULTIPLY', inp["Roughness"], 1.2)), math('MULTIPLY', l_max, 0.06)))  # top layer weak: stronger made a 20-35 m bump (lidar)
    amount = math('MULTIPLY', amount, smooth(math('DIVIDE', l_max, l_min), 1.0, 1.5))  # none if the mesh can't draw it
    hz = N.new('ShaderNodeSeparateXYZ')
    L.new(here.outputs[0], hz.inputs[0])
    # Push along the surface normal, so steep walls get rough sideways, not just up and down.
    push = math('MULTIPLY', math('SUBTRACT', grain, 0.5), math('MULTIPLY', amount, 2.0))
    total = math('ADD', hz.outputs["Z"], math('MULTIPLY', nrm.outputs["Z"], push))
    # Stretch again so Height stays the exact relief.
    stats2 = N.new('GeometryNodeAttributeStatistic')
    stats2.data_type = 'FLOAT'
    stats2.domain = 'POINT'
    L.new(shape, stats2.inputs["Geometry"])
    L.new(total, stats2.inputs["Attribute"])
    L.new(inner, stats2.inputs["Selection"])
    lo2, hi2 = stats2.outputs["Min"], stats2.outputs["Max"]
    final_z = math('MULTIPLY', math('DIVIDE', math('SUBTRACT', total, lo2), math('MAXIMUM', math('SUBTRACT', hi2, lo2), 1e-6)),
                   math('MULTIPLY', inp["Height"], ref))
    offset2 = N.new('ShaderNodeCombineXYZ')
    L.new(math('MULTIPLY', nrm.outputs["X"], push), offset2.inputs["X"])
    L.new(math('MULTIPLY', nrm.outputs["Y"], push), offset2.inputs["Y"])
    L.new(math('SUBTRACT', final_z, hz.outputs["Z"]), offset2.inputs["Z"])
    setpos2 = N.new('GeometryNodeSetPosition')
    L.new(shape, setpos2.inputs["Geometry"])
    L.new(offset2.outputs[0], setpos2.inputs["Offset"])
    out_geo = setpos2.outputs[0]
    if recipe == 6:  # Mesa with Floor off: drop the floor, marked on the flat grid from the shape (lg_cut)
        cut_at = N.new('GeometryNodeInputNamedAttribute')
        cut_at.data_type = 'BOOLEAN'
        cut_at.inputs["Name"].default_value = "lg_cut"
        drop = N.new('GeometryNodeDeleteGeometry')
        drop.domain = 'POINT'
        L.new(setpos2.outputs[0], drop.inputs["Geometry"])
        L.new(cut_at.outputs["Attribute"], drop.inputs["Selection"])
        out_geo = drop.outputs[0]
    shade = N.new('GeometryNodeSetShadeSmooth')
    L.new(out_geo, shade.inputs["Geometry"])
    L.new(shade.outputs[0], gout.inputs["Geometry"])
    _prune(ng, gout)
    ng["kb_version"] = GROUP_VERSION


def _prune(ng, out):
    """Drop nodes that don't feed the output: every group is built with all thirteen recipes' nodes,
    but only one is wired (a smaller tree saves and loads faster)."""
    feeds = {}
    for link in ng.links:
        feeds.setdefault(link.to_node.name, []).append(link.from_node)
    keep, todo = set(), [out]
    while todo:
        n = todo.pop()
        if n.name in keep:
            continue
        keep.add(n.name)
        todo.extend(feeds.get(n.name, ()))
    for n in [n for n in ng.nodes if n.name not in keep and n.bl_idname != 'NodeGroupInput']:
        ng.nodes.remove(n)


LIBRARY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "node_groups.blend")


def ensure_group(recipe=1):
    """Return the node group for one recipe. Missing or outdated: append the prebuilt one shipped with
    the add-on (well under a second), or build it from Python if that file is missing or older (~40 s;
    switching types took that long; Mike, Pass 5). Rebuild the file with tests/build_library.py."""
    name = f"{GROUP_NAME} {recipe:02d}"
    ng = bpy.data.node_groups.get(name)
    if ng is not None and ng.get("kb_version") == GROUP_VERSION:
        return ng
    lib = _append_prebuilt(name)
    if lib is not None:
        if ng is not None:  # outdated copy in this file: point its users at the new one
            ng.user_remap(lib)
            bpy.data.node_groups.remove(ng)
        lib.name = name
        return lib
    if ng is None:
        ng = bpy.data.node_groups.new(name, 'GeometryNodeTree')
    _build(ng, recipe)
    return ng


def _append_prebuilt(name):
    if not os.path.exists(LIBRARY):
        return None
    try:
        with bpy.data.libraries.load(LIBRARY, link=False) as (src, dst):
            if name not in src.node_groups:
                return None
            dst.node_groups = [name]
    except (OSError, RuntimeError):
        return None
    ng = dst.node_groups[0] if dst.node_groups else None
    if ng is None or ng.get("kb_version") != GROUP_VERSION:
        if ng is not None:
            bpy.data.node_groups.remove(ng)
        return None
    ng.use_fake_user = False
    return ng


def input_socket(mod, name):
    """The modifier's value holder for a group input, by its display name (Blender 5.2 API)."""
    for item in mod.node_group.interface.items_tree:
        if item.item_type == 'SOCKET' and item.in_out == 'INPUT' and item.name == name:
            return getattr(mod.properties.inputs, item.identifier)
    raise KeyError(name)

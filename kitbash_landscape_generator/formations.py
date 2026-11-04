# SPDX-License-Identifier: GPL-3.0-or-later
"""The cave formation library (M5 step 5.4, D105, D168): stalactites, stalagmites, columns and lava drips as
separate meshes, built from the references on docs/m5/c128_formation_refs.png (rules L1-L6, V1 in
docs/RESEARCH-caves.md), kept in a hidden "KB Cave Formations" collection like the rock library, so any
family can be swapped for any collection or made into a Kit. Which families a cave grows follows its rock
type (D168): Limestone stalactites, stalagmites and columns; Lava the lava drips (High and Ultra only, D169);
Jointed none."""

import math
import random

import bmesh
import bpy
from mathutils import Vector, noise

from .rocks import LEVELS, SIZES as ROCK_SIZES, at_level, sizes  # noqa: F401  (at_level, sizes: the same kit layout as the rocks)

LIBRARY = "KB Cave Formations"
LIBRARY_VERSION = 10
LEVEL_LIBRARY = f"{LIBRARY} Levels"
# Big and Medium only (Mike: the small ones are too small to read in a cave, and compete with the rocks).
SIZES = ROCK_SIZES[:2]
# Faces per piece at each Detail Level, a single or a whole cluster alike (Mike: about 300 / 3,000-5,000 /
# 10,000, bold pieces with real detail): the cube-sphere's grid per side, 6 x n x n faces.
LEVEL_GRID = {"Preview": 7, "High": 26, "Ultra": 41}
# A medium piece is 1 long (a column 1 tall); big and small ones are that times their size (rocks.SIZES).
# Hanging pieces have their pivot on the roof and hang down -Z; standing pieces stand up +Z from the floor.
# Each runs on past its pivot into the rock (EMBED of its length), so it sits set in, never on top.
EMBED = 0.12
FAMILIES = {
    "Stalactites": 51,  # L1: carrots, long thin taper to a sharp tip, flared root
    "Stalagmites": 53,  # L4: blunt round top, knobby stacked lobes, flared skirt
    "Columns": 59,      # L5: a stalactite and stalagmite grown together, fluted, narrowest near the join
    "Lava Drips": 61,   # V1: stubby shark teeth off a glazed lava-tube roof
    # Clusters: one asset each, a few laid-out designs (Mike: our own clusters, built once, spread around;
    # cleaner and fewer polygons than random ones unioned, which left odd bits sticking out).
    "Stalactite Clusters": 67,
    "Stalagmite Clusters": 71,
    "Drapes": 73,  # L6: thin folded sheets off a sloping roof, alone or a row of pointed ribbons (board c142)
}
# Each design: (size against the lead, x, y) per member, the lead first; units of the lead's length. No member
# under 70% of the lead (smaller ones only poked out of the others), and far enough apart that the bodies
# never pass through each other: stalactites meet only at the flared roots by the roof (L1), stalagmites
# only where their skirts run together on the floor. No Boolean: each member stays whole, all quads.
CLUSTERS = {
    "Stalactite Clusters": ("Stalactites", (
        ((1.0, 0.0, 0.0), (0.8, 0.28, 0.02)),                                         # pair
        ((1.0, 0.0, 0.0), (0.85, 0.28, 0.04), (0.75, -0.27, -0.03)),                  # trio in a row
        ((1.0, 0.0, 0.0), (0.8, 0.24, 0.17), (0.8, -0.06, -0.29)),                    # trio in a knot
        ((0.75, -0.56, 0.0), (0.9, -0.28, 0.03), (1.0, 0.0, 0.0), (0.85, 0.28, -0.02), (0.75, 0.56, 0.02)),  # fringe along a crack (L2)
        ((1.0, 0.0, 0.0), (0.9, 0.28, 0.0), (0.85, 0.0, 0.28), (0.8, 0.29, 0.29)),     # block of four
        ((1.0, 0.0, 0.0), (0.7, 0.27, 0.12), (0.7, -0.27, 0.12)),                     # lead and two flanks
    )),
    "Stalagmite Clusters": ("Stalagmites", (
        ((1.0, 0.0, 0.0), (0.8, 0.46, 0.0)),                                          # pair
        ((1.0, 0.0, 0.0), (0.95, 0.44, 0.06)),                                        # twins
        ((1.0, 0.0, 0.0), (0.85, 0.46, 0.06), (0.75, -0.44, -0.02)),                  # trio in a row
        ((1.0, 0.0, 0.0), (0.8, 0.4, 0.26), (0.8, -0.08, -0.46)),                     # trio in a knot
        ((1.0, 0.0, 0.0), (0.9, 0.46, 0.0), (0.8, 0.0, 0.46), (0.75, 0.46, 0.46)),     # block of four
        ((1.0, 0.0, 0.0), (0.7, 0.44, -0.1), (0.7, -0.22, 0.4)),                      # lead and two smaller
    )),
}
HANGING = {"Stalactites", "Lava Drips", "Stalactite Clusters", "Drapes"}


def _lathe(grid, radius, z0, z1, top=0.0, bottom=0.0, sway=None):
    """A closed all-quad shape turned round the Z axis (Mike: all quads): the rocks' cube-sphere, each point
    moved onto the shape. The side faces carry the body from z0 to z1, its radius(u, phi) for u 0..1 along it;
    an end with a height (top, bottom) is a round cap on the cube's end face, the end without one runs on to a
    point (a sharp tip: the body's radius must reach 0 at u = 1). A cap the length of EMBED buried in the rock
    is the plug that sets a piece in (on a coarse mesh the end face held so little of the length that the
    root came out a flat disc at the roof line)."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=2.0)
    cuts = max(grid - 1, 1)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=cuts, use_grid_fill=True)
    lo, hi = (0.25 if top else 0.0), (0.75 if bottom else 1.0)
    away = 1.0 if z0 > z1 else -1.0  # the top end's way out of the body
    for v in bm.verts:
        p = v.co.normalized()
        t = math.acos(max(-1.0, min(1.0, p.z))) / math.pi  # 0 at the top pole, 1 at the bottom
        phi = math.atan2(p.y, p.x)
        u = min(max((t - lo) / (hi - lo), 0.0), 1.0)
        r, z = radius(u, phi), z0 + (z1 - z0) * u
        if t < lo or t > hi:  # a cap: a quarter circle from the body's end in to the pole
            a = (1.0 - t / lo if t < lo else (t - hi) / (1.0 - hi)) * math.pi * 0.5
            r *= math.cos(a)
            z += (top * away if t < lo else -bottom * away) * math.sin(a)
        flat = Vector((p.x, p.y))
        out = flat.normalized() * r if flat.length > 1e-9 else Vector((0.0, 0.0))
        dx, dy = sway(u) if sway else (0.0, 0.0)
        v.co = Vector((out.x + dx, out.y + dy, z))
    return bm


def _sheet(nu, nv, at):
    """A thin closed all-quad sheet: a front and a back grid (nu across, nv down) joined round their edge by one
    rim of quads. at(s, v, side) gives a point for s, v in 0..1 and side -1 (back) or 1 (front)."""
    bm = bmesh.new()
    grid = {side: [[bm.verts.new(at(i / nu, j / nv, side)) for j in range(nv + 1)] for i in range(nu + 1)] for side in (-1, 1)}
    F, B = grid[1], grid[-1]
    for i in range(nu):
        for j in range(nv):
            bm.faces.new((F[i][j], F[i + 1][j], F[i + 1][j + 1], F[i][j + 1]))
            bm.faces.new((B[i][j + 1], B[i + 1][j + 1], B[i + 1][j], B[i][j]))
    edge = [(i, 0) for i in range(nu)] + [(nu, j) for j in range(nv)] + [(i, nv) for i in range(nu, 0, -1)] + [(0, j) for j in range(nv, 0, -1)]
    for k, (i, j) in enumerate(edge):
        i2, j2 = edge[(k + 1) % len(edge)]
        bm.faces.new((F[i2][j2], F[i][j], B[i][j], B[i2][j2]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return bm


def _drape(rng, scale, grid):
    """L6 (board c142): a thin sheet hanging plumb from a level top line along the roof (X), its pivot on the roof
    and a plug of EMBED up into the rock. Either one wavy sheet (Ruakuri) or a row of 3-8 ribbons on a shared
    band, each tapering to a point, so the lower edge is a fringe (Boyden, Te Ananui); folded in plan, more
    lower down (Crystal Grottoes). About 5% as thick as long at the top, thinner at the tips. A medium piece is
    1 long; the faces as the other pieces (about 300 / 4,000 / 10,000)."""
    # Ribbons 5-10x as long as wide (Te Ananui, Crystal Grottoes; wider ones read as a row of teeth), joined most
    # of their length, V notches between their pointed tips; each ribbon a fold about as deep as it is wide.
    row = rng.random() < 0.7
    ribbons = rng.randrange(3, 9) if row else 1
    rib_w = rng.uniform(0.1, 0.2)
    width = rib_w * ribbons if row else rng.uniform(0.35, 0.55)
    lens = [rng.uniform(0.5, 1.0) for _ in range(ribbons)]
    notch = rng.uniform(0.25, 0.45)  # how far up the V between two tips reaches
    folds, fold_at = (ribbons if row else rng.uniform(1.0, 2.0)), rng.uniform(0.0, 1.0)
    fold_amp = rib_w * rng.uniform(0.4, 0.6) if row else width * rng.uniform(0.12, 0.2)
    off = Vector((rng.uniform(-50, 50), rng.uniform(-50, 50), rng.uniform(-50, 50)))
    thick = 0.05

    def length(s):
        k = min(int(s * ribbons), ribbons - 1)
        c = (s * ribbons - k) * 2.0 - 1.0  # -1..1 across this ribbon
        return lens[k] * (1.0 - notch * abs(c) ** 1.5) if row else lens[k] * (1.0 - 0.5 * abs(c) ** 2.0)

    def at(s, v, side):
        # the top tenth of the grid is the plug, rising EMBED into the rock; the rest hangs down the sheet
        w = max((v - 0.1) / 0.9, 0.0)
        z = EMBED * (1.0 - v / 0.1) if v < 0.1 else -length(s) * w
        fold = fold_amp * math.sin(2.0 * math.pi * (folds * s + fold_at)) * (0.5 + 0.5 * w)
        fold += 0.04 * noise.noise(Vector((s * width * 3.0, w * 3.0, 0.0)) + off)
        t = thick * (1.0 - 0.6 * w) * 0.5
        return Vector(((s - 0.5) * width, fold + side * t, z))
    # whole columns per ribbon (at least two), so each tip comes to a point even at Preview
    return _sheet(ribbons * max(2, round(2 * grid / ribbons)), max(round(1.5 * grid), 3), at)


def _piece(family, rng, scale, grid, slim=False):
    if family == "Drapes":
        bm = _drape(rng, scale, grid)
        for v in bm.verts:
            v.co *= scale
        return bm
    off = Vector((rng.uniform(-50, 50), rng.uniform(-50, 50), rng.uniform(-50, 50)))
    lump = lambda u, phi, f: noise.noise(Vector((math.cos(phi) * f * 0.3, math.sin(phi) * f * 0.3, u * f)) + off)
    if family == "Stalactites":
        # L1: 8-20x as long as wide; the root flares where it merges with the roof and its neighbours; faint
        # ribs along the length; a little drift off straight. Hangs from the roof (z 0) to its tip (z -1).
        R = 0.5 / rng.uniform(5.0, 10.0)  # 8-20x as long as wide measured down the body, the root flare on top
        taper, flare, fall = rng.uniform(0.9, 1.3), rng.uniform(0.4, 0.8), rng.uniform(5.0, 9.0)
        drift = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1))).normalized() * rng.uniform(0.0, 0.03)
        radius = lambda u, phi: R * ((1.0 - u) ** taper + flare * math.exp(-u * fall)) * (1.0 + 0.06 * lump(u, phi, 18.0))
        bm = _lathe(grid, radius, 0.0, -1.0, top=EMBED, sway=lambda u: (drift.x * u * u, drift.y * u * u))
    elif family == "Lava Drips":
        # V1: stubby, 1-3x as long as wide, swollen like a drop that set, the root spread into the glaze.
        R = 0.5 / rng.uniform(1.0, 3.0)
        taper, spread = rng.uniform(0.55, 0.85), rng.uniform(0.2, 0.4)
        bend = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1))).normalized() * rng.uniform(0.0, 0.1)
        radius = lambda u, phi: R * ((1.0 - u) ** taper + spread * math.exp(-u * 4.0)) * (1.0 + 0.12 * lump(u, phi, 6.0))
        bm = _lathe(grid, radius, 0.0, -1.0, top=EMBED, sway=lambda u: (bend.x * u * u, bend.y * u * u))
    elif family == "Stalagmites":
        # L4: 1.5-3x as tall as wide, a round blunt top, stacked lobes up the side, a skirt flared into the floor.
        # Stands from the floor (z 0) to its top (z 1); u runs down from the top.
        # Review S3 against six photos (docs/m5/c139): tapered cones, stacked tiers, deep knobs, some slender spires.
        R = 0.5 / (rng.uniform(2.6, 4.0) if slim else rng.uniform(1.5, 5.0))  # slim in a cluster, so neighbours stand clear (and spires show, most are clusters); up to Choranche's 5x
        cap = 0.5 * R  # the top is narrower now, so a lower round cap
        skirt = rng.uniform(0.4, 0.69)  # 15% wider (review S3)
        tiers, tier_at = rng.uniform(2.0, 4.0), rng.uniform(0.0, 1.0)

        def radius(u, phi):
            # knobs of every size, not rings (rings read as a screw against the Vrelo photo); deep as Vrelo and Aranui
            lobes = 1.0 + 0.2 * lump(u, phi, 5.0) + 0.12 * lump(u, phi, 14.0)
            # 2-4 stacked tiers (Birthday Candle, Choranche), lopsided round the piece so they never close into rings
            # (noise at f 5, x3: at f 2 it barely changed round the piece, so half the pieces stacked even pagoda
            # rings, review pass 2); faded out over the top quarter so no bulb head sits on a neck
            tier = 1.0 + 0.15 * min(u * 4.0, 1.0) * math.sin(2.0 * math.pi * (tiers * u + tier_at) + 3.0 * lump(u, phi, 5.0))
            # top about 55% of the base (Vrelo, Sophienhoehle: cones, not thumbs)
            return R * (0.55 + 0.45 * u + skirt * math.exp(-(1.0 - u) * 5.0)) * lobes * tier
        bm = _lathe(grid, radius, 1.0 - cap, 0.0, top=cap, bottom=EMBED)
    else:  # Columns
        # L5: a stalactite from the roof and a stalagmite from the floor grown together; narrowest near where they
        # met, flared at both ends, fluted round and banded along. From the floor (z 0) to the roof (z 1).
        R = 0.5 / rng.uniform(2.0, 4.0)  # fat: the Timpanogos column is about half as wide as tall
        join, flutes = rng.uniform(0.35, 0.6), rng.randrange(6, 11)
        twist = rng.uniform(0.0, 6.28)

        def radius(u, phi):
            r = R * (0.8 + 0.4 * abs(u - join) + 0.5 * math.exp(-u * 5.0) + 0.6 * math.exp(-(1.0 - u) * 5.0))
            return r * (1.0 + 0.09 * math.cos(flutes * phi + twist + 3.0 * u) + 0.05 * lump(u, phi, 8.0)) * (1.0 + 0.04 * math.sin(u * 40.0))
        bm = _lathe(grid, radius, 1.0, 0.0, top=EMBED, bottom=EMBED)
    for v in bm.verts:
        v.co *= scale
    return bm


def _cluster(family, rng, design, scale, grid):
    """One laid-out cluster: its members, each whole and closed, in one mesh, sharing one piece's faces."""
    member, _designs = CLUSTERS[family]
    bm = bmesh.new()
    for size, x, y in design:
        piece = _piece(member, rng, size, max(round(grid / len(design) ** 0.5), 4), slim=True)
        piece.verts.index_update()
        verts = [bm.verts.new((v.co + Vector((x, y, 0.0))) * scale) for v in piece.verts]
        for f in piece.faces:
            bm.faces.new([verts[v.index] for v in f.verts])
        piece.free()
    return bm


def ensure_library():
    """Build (or rebuild, when this code changes) the formation library. Returns the top collection."""
    top = bpy.data.collections.get(LIBRARY)
    # Its pieces deleted (a scene cleared of every object) counts as missing too: kits left empty grew nothing.
    if top is not None and top.get("kb_version") == LIBRARY_VERSION and len(top.children) == len(FAMILIES) and top.all_objects:
        return top
    if top is None:
        top = bpy.data.collections.new(LIBRARY)
    levels = bpy.data.collections.get(LEVEL_LIBRARY) or bpy.data.collections.new(LEVEL_LIBRARY)
    for coll in (top, levels):
        for ob in list(coll.all_objects):
            me = ob.data
            bpy.data.objects.remove(ob)
            if me is not None and me.users == 0:
                bpy.data.meshes.remove(me)
        for child in list(coll.children_recursive):
            bpy.data.collections.remove(child)
    for family, seed in FAMILIES.items():
        rng = random.Random(seed)
        kit = bpy.data.collections.new(f"{LIBRARY} {family}")
        top.children.link(kit)
        for size, count, (lo, hi), _subdivisions in SIZES:
            name = f"{LIBRARY} {family} {size}"
            colls = {}
            for level, _step in LEVELS:
                colls[level] = bpy.data.collections.new(name if level == "High" else f"{name} {level}")
                (kit if level == "High" else levels).children.link(colls[level])
            designs = CLUSTERS[family][1] if family in CLUSTERS else None
            for i in range(len(designs) if designs else count):  # a cluster family: each design once per size
                state = rng.getstate()
                for level, _step in LEVELS:  # the same draws at every level: the same piece, finer or coarser
                    rng.setstate(state)
                    if designs:
                        bm = _cluster(family, rng, designs[i], rng.uniform(lo, hi), LEVEL_GRID[level])
                    else:
                        bm = _piece(family, rng, rng.uniform(lo, hi), LEVEL_GRID[level])
                    me = bpy.data.meshes.new(f"KB Formation {family} {size} {i + 1}" + ("" if level == "High" else f" {level}"))
                    bm.to_mesh(me)
                    bm.free()
                    me.shade_smooth()
                    colls[level].objects.link(bpy.data.objects.new(me.name, me))
    levels.use_fake_user = True
    top.use_fake_user = True  # kept in the file though no scene shows it
    top["kb_version"] = LIBRARY_VERSION
    return top


def family(name):
    """One family's kit (its Big, Medium and Small collections), building the library if it isn't there."""
    ensure_library()
    return bpy.data.collections.get(f"{LIBRARY} {name}")

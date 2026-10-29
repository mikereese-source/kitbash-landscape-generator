# SPDX-License-Identifier: GPL-3.0-or-later
"""The cave rock library (M5 step 5.2c, D105-D107): our own rock meshes in four families, built from the
references in docs/RESEARCH-caves.md, kept in a hidden "KB Cave Rocks" collection that caves pick from.
Rocks are separate pieces, instanced over the cave's shell, so a family can be swapped for any collection of
rocks (Mike: swappable later)."""

import random

import bmesh
import bpy
from mathutils import Vector, noise

LIBRARY = "KB Cave Rocks"
LIBRARY_VERSION = 4
# Each family is a kit of three sizes (Mike): a few big ones, the everyday ones, and pebbles to break up the
# floor. Size -> (how many, size range against a medium rock, detail of the mesh at High).
SIZES = (("Big", 4, (2.0, 3.0), 5), ("Medium", 8, (1.0, 1.0), 4), ("Small", 8, (0.33, 0.5), 3))
# Each rock at every Detail Level (Mike), the same shape finer or coarser: the High rocks are the kit itself;
# Preview and Ultra copies sit in collections named "<size collection> Preview" / "Ultra" in a hidden
# KB Cave Rocks Levels collection. Level -> mesh detail against High.
LEVELS = (("Preview", -1), ("High", 0), ("Ultra", 1))
LEVEL_LIBRARY = f"{LIBRARY} Levels"
# Family -> seed. A medium rock fits -1..1 across, big and small ones are that times their size; every pivot
# is 45% of the way up from the centre, so it sits partly buried in what it rests on (resting on top left thin
# slits; Mike).
FAMILIES = {
    "Blocks": 11,    # breakdown blocks: roof fall, blocky with flat broken faces (limestone)
    "Scree": 23,     # slabby scree: thin plates split along the bedding
    "Boulders": 37,  # water-worn boulders and cobbles: rounded, flattened (sea caves, streams)
    "Lava": 41,      # lava rubble: rough, pitted, irregular clinker
}


def _clip(verts, normal, dist):
    """Flatten everything past a plane onto it: a broken face."""
    for v in verts:
        over = v.co.dot(normal) - dist
        if over > 0.0:
            v.co -= normal * over


def _plane(rng, up_bias=0.0):
    n = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1) + up_bias)).normalized()
    return n, rng.uniform(0.55, 0.85)


def _rock(family, rng, scale=1.0, subdivisions=4):
    # All quads (Mike: easier to work on later): a cube cut into a grid on each side and pushed out to a
    # sphere, about as many faces as an icosphere of this detail had triangles halved.
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=2.0)
    cuts = max(round(1.25 * 2 ** subdivisions) - 1, 1)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=cuts, use_grid_fill=True)
    for v in bm.verts:
        v.co.normalize()
    verts = bm.verts
    off = Vector((rng.uniform(-50, 50), rng.uniform(-50, 50), rng.uniform(-50, 50)))
    if family == "Blocks":
        stretch = Vector((1.0, rng.uniform(0.45, 1.0), rng.uniform(0.45, 0.85)))  # some long blocks
        for v in verts:
            v.co = v.co * stretch
        for axis in (Vector((1, 0, 0)), Vector((-1, 0, 0)), Vector((0, 1, 0)), Vector((0, -1, 0)), Vector((0, 0, 1)), Vector((0, 0, -1))):
            jitter = Vector((rng.uniform(-0.3, 0.3), rng.uniform(-0.3, 0.3), rng.uniform(-0.3, 0.3)))
            _clip(verts, (axis + jitter).normalized(), rng.uniform(0.5, 0.7))
        for _ in range(rng.randint(2, 4)):  # the odd corner knocked off
            _clip(verts, *_plane(rng))
        grain = 0.03
    elif family == "Scree":
        stretch = Vector((1.0, rng.uniform(0.3, 0.8), rng.uniform(0.15, 0.3)))  # long, thin, slate-like
        for v in verts:
            v.co = v.co * stretch
        tilt = Vector((rng.uniform(-0.15, 0.15), rng.uniform(-0.15, 0.15), 1.0)).normalized()
        _clip(verts, tilt, stretch.z * 0.8)  # flat bedding faces top and bottom
        _clip(verts, -tilt, stretch.z * 0.8)
        for _ in range(rng.randint(4, 6)):  # sharp broken edges round the plate
            n = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-0.2, 0.2))).normalized()
            _clip(verts, n, rng.uniform(0.45, 0.8))
        grain = 0.015
    elif family == "Boulders":
        stretch = Vector((1.0, rng.uniform(0.5, 0.95), rng.uniform(0.45, 0.75)))
        for v in verts:
            d = noise.noise(v.co * 1.2 + off) * 0.12
            v.co = v.co * stretch * (1.0 + d)
        _clip(verts, Vector((0, 0, -1)), stretch.z * 0.75)  # a flattened underside, as it settled
        grain = 0.008
    else:  # Lava
        stretch = Vector((1.0, rng.uniform(0.5, 1.0), rng.uniform(0.5, 0.85)))
        for v in verts:
            lumps = noise.fractal(v.co * 1.4 + off, 0.6, 2.0, 3) * 0.14
            pits = max(noise.noise(v.co * 3.0 + off) - 0.3, 0.0) * 0.2  # gas pockets
            v.co = v.co * stretch * (1.0 + lumps - pits)
        for _ in range(rng.randint(2, 4)):  # broken faces, so it reads as rubble, not a sponge
            _clip(verts, *_plane(rng))
        grain = 0.02
    bm.normal_update()
    for v in verts:  # a fine surface grain over every family
        v.co += v.normal * noise.noise(v.co * 9.0 + off) * grain
    # Fit -1..1 across, keep the proportions, pivot 45% up from the centre.
    lo = Vector((min(v.co[i] for v in verts) for i in range(3)))
    hi = Vector((max(v.co[i] for v in verts) for i in range(3)))
    centre, half = (lo + hi) * 0.5, max(hi - lo) * 0.5
    for v in verts:
        v.co = (v.co - centre) / half
    zhalf = (hi.z - lo.z) * 0.5 / half
    for v in verts:
        v.co.z -= 0.45 * zhalf
        v.co *= scale
    return bm


def ensure_library():
    """Build (or rebuild, when this code changes) the rock library. Returns the top collection."""
    top = bpy.data.collections.get(LIBRARY)
    if top is not None and top.get("kb_version") == LIBRARY_VERSION and len(top.children) == len(FAMILIES):
        return top
    if top is None:
        top = bpy.data.collections.new(LIBRARY)
    for ob in list(top.all_objects):
        me = ob.data
        bpy.data.objects.remove(ob)
        if me is not None and me.users == 0:
            bpy.data.meshes.remove(me)
    for child in list(top.children_recursive):
        bpy.data.collections.remove(child)
    levels = bpy.data.collections.get(LEVEL_LIBRARY) or bpy.data.collections.new(LEVEL_LIBRARY)
    for ob in list(levels.all_objects):
        me = ob.data
        bpy.data.objects.remove(ob)
        if me is not None and me.users == 0:
            bpy.data.meshes.remove(me)
    for child in list(levels.children_recursive):
        bpy.data.collections.remove(child)
    for family, seed in FAMILIES.items():
        rng = random.Random(seed)
        kit = bpy.data.collections.new(f"{LIBRARY} {family}")
        top.children.link(kit)
        for size, count, (lo, hi), subdivisions in SIZES:
            name = f"{LIBRARY} {family} {size}"
            colls = {}
            for level, _step in LEVELS:
                colls[level] = bpy.data.collections.new(name if level == "High" else f"{name} {level}")
                (kit if level == "High" else levels).children.link(colls[level])
            for i in range(count):
                state = rng.getstate()
                for level, step in LEVELS:  # the same draws at every level: the same rock, finer or coarser
                    rng.setstate(state)
                    bm = _rock(family, rng, rng.uniform(lo, hi), subdivisions + step)
                    me = bpy.data.meshes.new(f"KB Rock {family} {size} {i + 1}" + ("" if level == "High" else f" {level}"))
                    bm.to_mesh(me)
                    bm.free()
                    me.shade_smooth()
                    me.set_sharp_from_angle(angle=0.7 if family != "Boulders" else 3.14)
                    colls[level].objects.link(bpy.data.objects.new(me.name, me))
    levels.use_fake_user = True
    top.use_fake_user = True  # kept in the file though no scene shows it
    top["kb_version"] = LIBRARY_VERSION
    return top


def family(name):
    """One family's kit (its Big, Medium and Small collections), building the library if it isn't there."""
    ensure_library()
    return bpy.data.collections.get(f"{LIBRARY} {name}")


def sizes(kit):
    """A kit's (big, medium, small) collections: its child collections ending Big / Medium / Small. A plain
    collection of rocks with no such children is used as the medium rocks (any collection can be swapped in)."""
    if kit is None:
        return None, None, None
    found = {size: next((c for c in kit.children if c.name.lower().endswith(size.lower())), None) for size, *_ in SIZES}
    if not any(found.values()):
        return None, kit, None
    return found["Big"], found["Medium"], found["Small"]


def at_level(coll, level):
    """A rock collection's copy at a Detail Level ("<name> Preview" / "Ultra"), or the collection itself when
    it has none (an artist's own rocks)."""
    if coll is None or level == "High":
        return coll
    return bpy.data.collections.get(f"{coll.name} {level}") or coll


def layout_review(scene, name="Rock Review"):
    """Every library rock laid out for review in its own collection: a block of rows per kit (big, medium,
    small), beside whatever is in the scene. Shares each rock's mesh, so it shows the library as it is."""
    old = bpy.data.collections.get(name)
    if old is not None:
        for ob in list(old.objects):
            bpy.data.objects.remove(ob)
        bpy.data.collections.remove(old)
    review = bpy.data.collections.new(name)
    scene.collection.children.link(review)
    xs = [(ob.matrix_world @ Vector(c)).x for ob in scene.objects if ob.type == 'MESH' for c in ob.bound_box]
    x0, y = (max(xs) + 12.0) if xs else 0.0, 0.0
    ensure_library()
    for family_name in FAMILIES:
        kit = family(family_name)
        for coll in sizes(kit):
            rocks = sorted(coll.objects, key=lambda ob: ob.name)
            gap = max(max(ob.dimensions.x, ob.dimensions.y) for ob in rocks) + 1.0
            label = bpy.data.objects.new(f"{coll.name} label", bpy.data.curves.new(f"{coll.name} label", 'FONT'))
            label.data.body, label.data.size = coll.name.replace(f"{LIBRARY} ", ""), 1.0
            label.location = (x0 - 14.0, y - 0.4, 0.0)
            review.objects.link(label)
            x = x0
            for src in rocks:
                ob = bpy.data.objects.new(f"{src.name} review", src.data)
                ob.location = (x, y, -min(v.co.z for v in src.data.vertices))  # standing on the ground
                review.objects.link(ob)
                x += gap
            y -= gap
        y -= 4.0  # a gap between kits
    return review

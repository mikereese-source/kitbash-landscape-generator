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
LIBRARY_VERSION = 1
PER_FAMILY = 8
# Family -> (seed, how it is shaped). Every rock fits -1..1 across, its pivot 45% of the way up from its
# centre, so it sits partly buried in what it rests on (resting on top left thin slits; Mike).
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


def _rock(family, rng):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=4, radius=1.0)
    verts = bm.verts
    off = Vector((rng.uniform(-50, 50), rng.uniform(-50, 50), rng.uniform(-50, 50)))
    if family == "Blocks":
        stretch = Vector((1.0, rng.uniform(0.75, 1.0), rng.uniform(0.6, 0.85)))
        for v in verts:
            v.co = v.co * stretch
        for axis in (Vector((1, 0, 0)), Vector((-1, 0, 0)), Vector((0, 1, 0)), Vector((0, -1, 0)), Vector((0, 0, 1)), Vector((0, 0, -1))):
            jitter = Vector((rng.uniform(-0.3, 0.3), rng.uniform(-0.3, 0.3), rng.uniform(-0.3, 0.3)))
            _clip(verts, (axis + jitter).normalized(), rng.uniform(0.5, 0.7))
        for _ in range(rng.randint(2, 4)):  # the odd corner knocked off
            _clip(verts, *_plane(rng))
        grain = 0.03
    elif family == "Scree":
        stretch = Vector((1.0, rng.uniform(0.6, 0.9), rng.uniform(0.22, 0.35)))
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
        stretch = Vector((1.0, rng.uniform(0.75, 0.95), rng.uniform(0.5, 0.75)))
        for v in verts:
            d = noise.noise(v.co * 1.2 + off) * 0.12
            v.co = v.co * stretch * (1.0 + d)
        _clip(verts, Vector((0, 0, -1)), stretch.z * 0.75)  # a flattened underside, as it settled
        grain = 0.008
    else:  # Lava
        stretch = Vector((1.0, rng.uniform(0.7, 1.0), rng.uniform(0.6, 0.9)))
        for v in verts:
            lumps = noise.fractal(v.co * 1.6 + off, 0.7, 2.2, 4) * 0.22
            pits = max(noise.noise(v.co * 5.0 + off) - 0.25, 0.0) * 0.35  # gas pockets
            v.co = v.co * stretch * (1.0 + lumps - pits)
        for _ in range(rng.randint(1, 3)):
            _clip(verts, *_plane(rng))
        grain = 0.04
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
    return bm


def ensure_library():
    """Build (or rebuild, when this code changes) the rock library. Returns the top collection."""
    top = bpy.data.collections.get(LIBRARY)
    if top is not None and top.get("kb_version") == LIBRARY_VERSION and len(top.children) == len(FAMILIES):
        return top
    if top is None:
        top = bpy.data.collections.new(LIBRARY)
    for child in list(top.children):
        for ob in list(child.objects):
            me = ob.data
            bpy.data.objects.remove(ob)
            if me is not None and me.users == 0:
                bpy.data.meshes.remove(me)
        bpy.data.collections.remove(child)
    for family, seed in FAMILIES.items():
        rng = random.Random(seed)
        coll = bpy.data.collections.new(f"{LIBRARY} {family}")
        top.children.link(coll)
        for i in range(PER_FAMILY):
            bm = _rock(family, rng)
            me = bpy.data.meshes.new(f"KB Rock {family} {i + 1}")
            bm.to_mesh(me)
            bm.free()
            me.shade_smooth()
            me.set_sharp_from_angle(angle=0.7 if family != "Boulders" else 3.14)
            coll.objects.link(bpy.data.objects.new(me.name, me))
    top.use_fake_user = True  # kept in the file though no scene shows it
    top["kb_version"] = LIBRARY_VERSION
    return top


def family(name):
    """One family's collection, building the library if it isn't there."""
    ensure_library()
    return bpy.data.collections.get(f"{LIBRARY} {name}")

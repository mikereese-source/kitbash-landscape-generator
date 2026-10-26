"""Headless tests for the KitBash Landscape Generator.

Run:  blender -b --factory-startup --python tests/run_tests.py
Exits 1 if any test fails. Tests drive the panel's own properties (ob.lg.*), never the
node inputs directly, so they catch the Blender 5.2 "value set but not rebuilt" trap (D19).
"""

import math
import os
import sys
import traceback

import bpy
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kitbash_landscape_generator as lg  # noqa: E402

RESULTS = []


def test(tid, name):
    def wrap(fn):
        try:
            detail = fn()
            RESULTS.append((tid, name, True, detail or ""))
        except Exception as e:  # report and keep going
            RESULTS.append((tid, name, False, f"{type(e).__name__}: {e}"))
            traceback.print_exc()
        return fn
    return wrap


def check(cond, msg):
    if not cond:
        raise AssertionError(msg)


def fresh_scene():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    bpy.context.scene.cursor.location = (0, 0, 0)


def add(kind="mountains", at=(0, 0, 0)):
    scene = bpy.context.scene
    scene.cursor.location = at
    scene.lg_type = kind
    check(bpy.ops.landscape.add() == {'FINISHED'}, "Add Landscape did not finish")
    return bpy.context.view_layer.objects.active


def evaluated_points(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    ev.to_mesh_clear()
    return co.reshape(-1, 3)


def set_size(ob, x, y=None):
    ob.lg.size_x = x
    ob.lg.size_y = x if y is None else y


lg.register()
lg._refresh_all()


@test("T1", "Scale keeps the big shapes")
def _t1():
    out, worst = [], 0.0

    def broad(z):
        n = int(round(math.sqrt(z.size)))
        k = max(n // 24, 1)
        c = np.pad(np.cumsum(np.cumsum(np.pad(z.reshape(n, n), k, mode="edge"), 0), 1), ((1, 0), (1, 0)))
        m = 2 * k + 1
        return (c[m:, m:] - c[:-m, m:] - c[m:, :-m] + c[:-m, :-m]) / (m * m)

    for kind in lg.TYPES:
        fresh_scene()
        ob = add(kind)
        ref = None
        for size in (10.0, 100.0, 1000.0):
            set_size(ob, size)
            z = evaluated_points(ob)[:, 2] / size
            check(np.isfinite(z).all(), f"{kind} at {size} m has broken heights")
            if ref is None:
                ref, span = z, z.max() - z.min()
                check(span > 0, f"{kind} is flat")
                continue
            # Big shapes must match; fine grain is real-size on purpose (R2: shape layers stop at ~2 m,
            # rock grain is in meters), so compare after removing detail under 1/12 of the width.
            diff = np.abs(broad(z) - broad(ref)).max() / span * 100
            check(diff < 3.0, f"{kind} at {size} m: big shapes differ {diff:.2f}% from 10 m")
            worst = max(worst, diff)
        out.append(kind)
    return f"big shapes within {worst:.2f}% at 10 m / 100 m / 1 km for " + ", ".join(out)


@test("T2", "Detail spacing = size / resolution")
def _t2():
    fresh_scene()
    ob = add()
    for final, res in ((False, 512), (True, 2048)):
        ob.lg.final = final
        for size in (10.0, 200.0, 1000.0):
            set_size(ob, size)
            # Points per side from the count: rock grain pushes points sideways, so x values aren't a grid.
            spacing = size / (math.sqrt(len(evaluated_points(ob))) - 1)
            want = size / res
            check(abs(spacing - want) / want < 0.05, f"spacing {spacing:.4f} m, want {want:.4f} m")
    return "within 5% for Preview 512 and Final 2048 at 10 m, 200 m, 1 km"


@test("T3", "Fit to selection covers the objects")
def _t3():
    fresh_scene()
    ob = add(at=(5, -5, 0))
    cubes = []
    for loc in ((150, 20, 5), (-40, -90, 5)):
        bpy.ops.mesh.primitive_cube_add(size=10, location=loc)
        cubes.append(bpy.context.view_layer.objects.active)
    for c in cubes:
        c.select_set(True)
    check(bpy.ops.landscape.fit_selection() == {'FINISHED'}, "Fit did not finish")
    pts = evaluated_points(ob)[:, :2] + np.array(ob.location[:2])
    lo, hi = pts.min(0), pts.max(0)
    for c in cubes:
        for corner in c.bound_box:
            x, y, _ = c.matrix_world @ lg.Vector(corner)
            check(lo[0] <= x <= hi[0] and lo[1] <= y <= hi[1], f"corner ({x:.0f}, {y:.0f}) not covered")
    check(tuple(ob.location) == (5, -5, 0), "Fit moved the landscape")
    # 10% margin: half-size = 1.1 x the farthest corner from the landscape's centre.
    reach = np.zeros(2)
    for c in cubes:
        for corner in c.bound_box:
            w = c.matrix_world @ lg.Vector(corner)
            reach = np.maximum(reach, np.abs(np.array(w[:2]) - np.array(ob.location[:2])))
    want = 2 * reach * 1.1
    got = np.array((ob.lg.size_x, ob.lg.size_y))
    check(np.allclose(got, want, rtol=0.01), f"size {got.round(1)}, want {want.round(1)} (10% margin)")
    for o in bpy.context.selected_objects:
        o.select_set(False)
    check(not bpy.ops.landscape.fit_selection.poll(), "Fit should be greyed out with nothing selected")
    return f"covers both cubes; landscape stayed at the cursor; size {ob.lg.size_x:.0f} x {ob.lg.size_y:.0f} m"


@test("T4", "Preview vs Final point counts")
def _t4():
    fresh_scene()
    ob = add()
    set_size(ob, 200.0)
    n_prev = len(evaluated_points(ob))
    ob.lg.final = True
    n_final = len(evaluated_points(ob))
    check(n_prev == 513 * 513, f"Preview has {n_prev} points, want {513 * 513}")
    check(n_final == 2049 * 2049, f"Final has {n_final} points, want {2049 * 2049}")
    ob.lg.ultra = True
    n_ultra = len(evaluated_points(ob))
    check(n_ultra == 4097 * 4097, f"Ultra has {n_ultra} points, want {4097 * 4097}")
    ob.lg.ultra = False
    return f"Preview {n_prev:,} / Final {n_final:,} / Ultra {n_ultra:,} points"


@test("T18", "Landscape tab and Add Landscape")
def _t18():
    fresh_scene()
    panel = bpy.types.LG_PT_main
    check(panel.bl_space_type == 'VIEW_3D' and panel.bl_region_type == 'UI', "panel is not in the sidebar")
    check(panel.bl_category == "Landscape", f"tab is '{panel.bl_category}'")
    check(panel.bl_label == "KitBash Landscape Generator", f"header is '{panel.bl_label}'")
    ob = add(at=(12, 34, 0))
    check(tuple(ob.location) == (12, 34, 0), "not placed at the 3D cursor")
    check(ob.lg.is_landscape and lg.landscape_modifier(ob), "not a live landscape")
    return "sidebar tab 'Landscape'; Add places a live landscape at the 3D cursor (button position: manual check)"


@test("T19", "Landscape list")
def _t19():
    fresh_scene()
    a = add("hills", (0, 0, 0))
    b = add("dunes", (300, 0, 0))
    bpy.ops.mesh.primitive_cube_add()
    scene = bpy.context.scene
    # UILists can't be built outside a UI draw, so call the filter with a stand-in self.
    stand_in = type("UL", (), {"bitflag_filter_item": 1 << 30})()
    flags, _ = lg.LG_UL_landscapes.filter_items(stand_in, bpy.context, scene, "objects")
    listed = {ob.name for ob, f in zip(scene.objects, flags) if f}
    check(listed == {a.name, b.name}, f"list shows {sorted(listed)}")
    scene.lg_index = list(scene.objects).index(a)
    check(bpy.context.view_layer.objects.active == a, "picking a row did not make it active")
    return f"lists only the 2 landscapes; picking a row makes it active"


@test("T7a", "Type is saved by key")
def _t7a():
    fresh_scene()
    ob = add("dunes")
    check(ob.lg.type_key == "dunes", f"type_key is '{ob.lg.type_key}'")
    # A user-typed name survives a type change; a generated one follows the type.
    ob.name = "MyBackdrop"
    bpy.context.scene.lg_type = "hills"
    check(ob.name == "MyBackdrop", f"user name was replaced with {ob.name}")
    check(ob.lg.type_key == "hills", "type did not change")
    other = add("mountains")
    bpy.context.scene.lg_type = "dunes"
    check(other.name.startswith("Landscape_SandDunes"), f"generated name is {other.name}")
    # An M1 file stored the type as a list position; it must still load as the right type.
    other.lg.type_key = ""
    other.lg["land_type"] = 2
    check(lg._object_type_key(other.lg) == "dunes", "M1 type position not migrated")
    return "saved by key; user names kept; M1 files migrate"


@test("T20", "Shape controls, Randomize, Reset")
def _t20():
    fresh_scene()
    ob = add("mountains")
    props = ob.lg
    look = lg.TYPES["mountains"]
    check(abs(props.height_m - look["height"] * 200) < 1e-3, f"starts at {props.height_m} m, not the type's look")
    relief = lambda: np.ptp(evaluated_points(ob)[:, 2])
    check(abs(relief() - props.height_m) < 0.01, "Height (m) is not the real relief")
    props.height_m = 25.0
    check(abs(relief() - 25.0) < 0.01, f"relief {relief():.2f} m after setting 25 m")
    set_size(ob, 400.0)
    check(abs(props.height_m - 50.0) < 0.01, "Height did not grow with the size")
    before = evaluated_points(ob)[:, 2].copy()
    for prop, value in (("feature_m", 80.0), ("roughness_pct", 90.0), ("sharpness_pct", 10.0)):
        setattr(props, prop, value)
        check(abs(getattr(props, prop) - value) < 0.01, f"{prop} reads {getattr(props, prop)}")
        after = evaluated_points(ob)[:, 2]
        check(not np.allclose(after, before), f"{prop} did not change the landscape")
        before = after.copy()
    seed = props.seed
    bpy.ops.landscape.randomize()
    check(props.seed != seed, "Randomize kept the seed")
    check(not np.allclose(evaluated_points(ob)[:, 2], before), "new seed, same landscape")
    bpy.ops.landscape.reset_look()
    check(abs(props.height - look["height"]) < 1e-6 and abs(props.sharpness - look["sharpness"]) < 1e-6,
          "Reset did not restore the type's look")
    return "each control changes the landscape; Height = real relief and grows with size; Randomize; Reset"


@test("T21", "Volcano styles and controls")
def _t21():
    fresh_scene()
    ob = add("volcano")
    props = ob.lg
    check(props.style == "strato", f"starts as {props.style}")
    shapes = {}
    for st in lg.TYPES["volcano"]["styles"]:
        props.style = st["key"]
        check(abs(props.height - st["look"]["height"]) < 1e-6, f"{st['key']} did not load its height")
        shapes[st["key"]] = evaluated_points(ob)[:, 2] / props.height_m
    keys = list(shapes)
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            check(not np.allclose(shapes[keys[i]], shapes[keys[j]], atol=1e-3), f"{keys[i]} looks like {keys[j]}")
    props.style = "strato"
    before = evaluated_points(ob)[:, 2].copy()
    for prop, value in (("crater_size", 0.9), ("steepness", 0.1), ("gullies", 1.0), ("breach", 0.8),
                        ("crater_depth", 1.0), ("rim_thickness", 1.0)):
        setattr(props, prop, value)
        after = evaluated_points(ob)[:, 2]
        check(not np.allclose(after, before), f"{prop} did not change the volcano")
        before = after.copy()
    bpy.ops.landscape.reset_look()
    check(props.breach == 0.0 and props.style == "strato", "Reset did not restore the volcano defaults")
    return "4 distinct styles; all 6 volcano sliders change it; Reset restores"


@test("T22", "Per-type sliders and dune styles")
def _t22():
    done = []
    for key, rec in lg.TYPES.items():
        if key == "volcano" or not rec.get("controls"):
            continue
        fresh_scene()
        ob = add(key)
        for ctl in rec["controls"]:
            if "styles" in ctl:  # a style-only control (Mesa Floor: Hero Butte)
                ob.lg.style = ctl["styles"][0]
            before = evaluated_points(ob)[:, 2].copy()
            if isinstance(ctl["default"], bool):  # a toggle (Mesa Floor)
                value = not ctl["default"]
            else:
                value = 1.2 if ctl["prop"] == "wind_direction" else (0.1 if ctl["default"] > 0.5 else 0.9)
            setattr(ob.lg, ctl["prop"], value)
            after = evaluated_points(ob)[:, 2]
            check(after.shape != before.shape or not np.allclose(after, before), f"{key}: {ctl['prop']} did nothing")
            done.append(f"{key}.{ctl['prop']}")
    fresh_scene()
    ob = add("dunes")
    shapes = []
    for st in lg.TYPES["dunes"]["styles"]:
        ob.lg.style = st["key"]
        shapes.append(evaluated_points(ob)[:, 2].copy())
    check(not np.allclose(shapes[0], shapes[1]) and not np.allclose(shapes[1], shapes[2]), "dune styles look alike")
    return f"{len(done)} sliders each change their type; 3 distinct dune styles"


@test("T24", "Prebuilt node groups are current (fast type switching)")
def _t24():
    from kitbash_landscape_generator import nodes
    check(os.path.exists(nodes.LIBRARY), "node_groups.blend missing: run tests/build_library.py")
    with bpy.data.libraries.load(nodes.LIBRARY, link=False) as (src, dst):
        names = list(src.node_groups)
        dst.node_groups = list(names)  # a copy: Blender swaps the names for the loaded groups in place
    stale = [ng.name for ng in dst.node_groups if ng.get("kb_version") != nodes.GROUP_VERSION]
    for ng in dst.node_groups:
        bpy.data.node_groups.remove(ng)
    want = {f"{nodes.GROUP_NAME} {t['recipe']:02d}" for t in lg.TYPES.values()}
    check(want <= set(names), f"node_groups.blend lacks {sorted(want - set(names))}: run tests/build_library.py")
    check(not stale, f"node_groups.blend is out of date ({len(stale)} groups): run tests/build_library.py")
    return f"{len(names)} groups at version {nodes.GROUP_VERSION}"


@test("T25", "Presets save, load, rename, delete")
def _t25():
    import tempfile
    from kitbash_landscape_generator import presets
    tmp = os.path.join(tempfile.mkdtemp(), "presets.json")
    real = presets.path
    presets.path = lambda: tmp  # never touch the artist's own presets
    try:
        fresh_scene()
        ob = add("volcano")
        ob.lg.style = "caldera"
        ob.lg.seed, ob.lg.roughness_pct, ob.lg.crater_size = 4242, 80.0, 0.7
        bpy.ops.landscape.preset_save(name="Test Volcano")
        check("Test Volcano" in presets.load_all(), "preset was not saved")
        fresh_scene()
        other = add("hills")
        bpy.context.scene.lg_preset = "Test Volcano"
        bpy.ops.landscape.preset_load()
        check(other.lg.type_key == "volcano" and other.lg.style_key == "caldera", "type/style not restored")
        check(other.lg.seed == 4242 and abs(other.lg.crater_size - 0.7) < 1e-6, "sliders not restored")
        presets.rename("Test Volcano", "Renamed")
        check("Renamed" in presets.load_all(), "rename failed")
        presets.delete("Renamed")
        check(not presets.load_all(), "delete failed")
    finally:
        presets.path = real
    return "volcano caldera look saved, loaded onto a Hills landscape, renamed, deleted"


MASKS = ("lg_height", "lg_slope", "lg_curvature", "lg_flow", "lg_wear", "lg_deposit")


def masks_of(ob):
    lg.sync_object(ob)  # Add's first sync runs before the mesh exists; erosion runs on the next one
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    out = {}
    for name in MASKS:
        if name in me.attributes:
            a = np.empty(len(me.vertices))
            me.attributes[name].data.foreach_get("value", a)
            out[name] = a
    ev.to_mesh_clear()
    return out


@test("T9", "Masks exist and are 0-1")
def _t9():
    eroded = 0
    for key, rec in lg.TYPES.items():
        fresh_scene()
        ob = add(key)
        m = masks_of(ob)
        missing = [n for n in MASKS if n not in m]
        check(not missing, f"{key}: missing {missing}")
        for n, a in m.items():
            check(np.isfinite(a).all() and a.min() >= -1e-6 and a.max() <= 1 + 1e-6, f"{key}: {n} outside 0-1 ({a.min():.3f}..{a.max():.3f})")
        check(np.ptp(m["lg_height"]) > 0.99 and np.ptp(m["lg_slope"]) > 0.05, f"{key}: height/slope masks flat")
        if rec.get("erosion") and ob.lg.erosion_amount > 0:
            eroded += 1
            check(m["lg_flow"].max() > 0.5, f"{key}: no channels in the flow mask")
            check(m["lg_wear"].max() > 0.05 or m["lg_deposit"].max() > 0.05, f"{key}: erosion left no wear or deposit")
    fresh_scene()
    ob = add("mountains")
    m = masks_of(ob)
    wet = m["lg_flow"] > 0.6
    check(m["lg_curvature"][wet].mean() > m["lg_curvature"].mean(), "flow should run in hollows (high curvature)")
    fresh_scene()
    ob = add("mesa")
    check((masks_of(ob)["lg_slope"] > 0.6).mean() > 0.01, "Mesa cliffs should be steep in the slope mask")
    return f"6 masks on all {len(lg.TYPES)} types, in 0-1; flow in hollows; {eroded} eroded types have flow and wear/deposit"


@test("T28", "Mask viewer colours the landscape by the picked mask")
def _t28():
    fresh_scene()
    ob = add("mountains")
    lg.sync_object(ob)

    def view_colors():
        dg = bpy.context.evaluated_depsgraph_get()
        dg.update()
        ev = ob.evaluated_get(dg)
        me = ev.to_mesh()
        check("lg_view" in me.attributes, "no lg_view colour attribute")
        c = np.empty(len(me.vertices) * 4)
        me.attributes["lg_view"].data.foreach_get("color", c)
        ev.to_mesh_clear()
        return c.reshape(-1, 4)
    seen = {}
    for key in ("HEIGHT", "SLOPE", "FLOW"):
        ob.lg.show_mask = key
        c = view_colors()
        check(np.ptp(c[:, 0]) > 0.3, f"{key}: viewer colours don't vary")
        seen[key] = c[:, 0].copy()
    check(not np.allclose(seen["HEIGHT"], seen["SLOPE"]), "Height and Slope show the same colours")
    check(ob.data.color_attributes.active_color_name == "lg_view", "lg_view is not the shown colour attribute")
    ob.lg.show_mask = 'NONE'
    check(np.allclose(view_colors()[:, :3], 0.0), "None should leave no mask colours")
    return "Height, Slope, Flow colour the landscape differently; None clears it"


@test("T26", "Proportional Feature Scaling: any size change keeps feature size")
def _t26():
    fresh_scene()
    ob = add("hills")
    set_size(ob, 400.0)
    fs, h_m = ob.lg.feature_scale, ob.lg.height_m
    ob.lg.proportional = True
    bpy.ops.landscape.scale_size(factor=2.0)
    check(abs(ob.lg.feature_scale - fs * 2) < 1e-3, f"features across {ob.lg.feature_scale} != {fs * 2}")
    check(abs(ob.lg.height_m - h_m) < 0.01 * h_m, "height in meters changed")
    ob.lg.size_x = ob.lg.size_y = 1600.0  # a typed size follows the toggle too, not just 2X/4X
    check(abs(ob.lg.feature_scale - fs * 4) < 1e-3, f"typed size: features across {ob.lg.feature_scale} != {fs * 4}")
    ob.lg.proportional = False
    fs2 = ob.lg.feature_scale
    bpy.ops.landscape.scale_size(factor=2.0)
    check(abs(ob.lg.feature_scale - fs2) < 1e-6, "off: shapes should just grow")
    return f"on: {fs:.1f} -> {fs * 2:.1f} (2X) -> {fs * 4:.1f} (typed size) features across, height kept; off: unchanged"


@test("T23", "Big seeds stay smooth; Add keeps size")
def _t23():
    fresh_scene()
    ob = add("craters")
    ob.lg.size_x = ob.lg.size_y = 800.0
    for seed in (0, 71830, 99999):
        ob.lg.seed = seed
        z = evaluated_points(ob)[:, 2]
        flat = np.mean(np.abs(np.diff(z)) < 1e-6)
        check(flat < 0.05, f"seed {seed}: {flat:.0%} of steps are flat (blocky)")
        # A crater field is bowls in rolling ground: what's left after removing the broad shapes
        # skews low (pits). Plain noise with no craters (the old big-seed bug) has no skew.
        n = int(round(math.sqrt(z.size)))
        g = z.reshape(n, n)
        k = 4
        c = np.pad(np.cumsum(np.cumsum(np.pad(g, k, mode="edge"), 0), 1), ((1, 0), (1, 0)))
        m = 2 * k + 1
        fine = g - (c[m:, m:] - c[:-m, m:] - c[m:, :-m] + c[:-m, :-m]) / (m * m)
        skew = float((fine ** 3).mean() / max(fine.std(), 1e-12) ** 3)
        check(skew < -0.5, f"seed {seed}: no crater field (pit skew {skew:.2f})")
    ob.lg.detail = 'FINAL'
    b = add("cliffs")
    check((b.lg.size_x, b.lg.size_y, b.lg.detail) == (800.0, 800.0, 'FINAL'), "Add did not keep size/detail")
    return "seeds 0 / 71830 / 99999 smooth; new landscape keeps 800 m and Final"


@test("T5", "All types build")
def _t5():
    built = 0
    for kind in lg.TYPES:
        styles = [st["key"] for st in lg.TYPES[kind].get("styles", ())] or [None]
        for st in styles:
            fresh_scene()
            ob = add(kind)
            if st:
                ob.lg.style = st
            z = evaluated_points(ob)[:, 2]
            check(z.size > 1000 and np.isfinite(z).all(), f"{kind}/{st}: broken mesh")
            # The stretch makes relief = Height by construction, so check the surface really varies:
            # not one spike or step with everything else flat.
            spread = np.percentile(z, 95) - np.percentile(z, 5)
            check(spread > 0.05 * np.ptp(z), f"{kind}/{st}: flat apart from a few points")
            built += 1
    return f"{len(lg.TYPES)} types, {built} type/style combinations build, finite and not flat"


@test("T7", "Same seed, same result")
def _t7():
    for kind in ("mountains", "dunes", "craters", "volcano"):
        fresh_scene()
        a = add(kind)
        a.lg.seed = 7
        first = evaluated_points(a)[:, 2].copy()
        b = add(kind)
        b.lg.seed = 7
        check(np.array_equal(first, evaluated_points(b)[:, 2]), f"{kind}: two builds with seed 7 differ")
        b.lg.seed = 8
        check(not np.allclose(first, evaluated_points(b)[:, 2]), f"{kind}: seeds 7 and 8 match")
        b.lg.seed = 7
        check(np.array_equal(first, evaluated_points(b)[:, 2]), f"{kind}: seed 7 changed after a round trip")
    return "mountains, dunes, craters, volcano: same seed matches exactly, a new seed differs"


@test("T8", "Controls are plain (auto part)")
def _t8():
    # Not drawn in the panel: bookkeeping, or the raw values behind the meter/percent sliders.
    internal = {"rna_type", "name", "is_landscape", "type_key", "look_set", "style_key", "final", "ultra",
                "height", "feature_scale", "roughness", "sharpness"}
    props = [p for p in bpy.types.Object.bl_rna.properties["lg"].fixed_type.properties if p.identifier not in internal]
    missing = [p.identifier for p in props if len((p.description or "").strip()) < 10]
    check(not missing, f"controls without a tooltip: {missing}")
    ops = [c for c in vars(lg).values() if isinstance(c, type) and issubclass(c, bpy.types.Operator) and c is not bpy.types.Operator]
    no_desc = [o.bl_idname for o in ops if len((getattr(o, "bl_description", "") or "").strip()) < 10]
    check(ops and not no_desc, f"buttons without a tooltip: {no_desc}")
    return f"{len(props)} controls and {len(ops)} buttons all have tooltips (plain-language review: manual)"


print("\n=== KitBash Landscape Generator tests ===")
for tid, name, ok, detail in RESULTS:
    print(f"{'PASS' if ok else 'FAIL'}  {tid:4} {name}: {detail}")
failed = [r for r in RESULTS if not r[2]]
print(f"{len(RESULTS) - len(failed)}/{len(RESULTS)} passed")
sys.exit(1 if failed else 0)

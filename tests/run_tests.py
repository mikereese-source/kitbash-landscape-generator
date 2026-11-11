"""Headless tests for the KitBash Landscape Generator.

Run:  blender -b --factory-startup --python tests/run_tests.py
Exits 1 if any test fails. Tests drive the panel's own properties (ob.lg.*), never the
node inputs directly, so they catch the Blender 5.2 "value set but not rebuilt" trap (D19).
"""

import math
import os
import sys
import time
import traceback

import bpy
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kitbash_landscape_generator as lg  # noqa: E402

RESULTS = []


def test(tid, name):
    def wrap(fn):
        only = os.environ.get("LG_ONLY")  # e.g. LG_ONLY=T30,T29 runs just those
        if only and tid not in only.split(","):
            return fn
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


def add(kind="mountains", at=(0, 0, 0), keep_water=False):
    scene = bpy.context.scene
    scene.cursor.location = at
    scene.lg_type = kind
    check(bpy.ops.landscape.add() == {'FINISHED'}, "Add Landscape did not finish")
    ob = bpy.context.view_layer.objects.active
    if not keep_water:
        ob.lg.water = False  # terrain tests read the mesh as a grid; the water sheet's 4 points aren't on it
    return ob


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
    stale = [ng.name for ng in dst.node_groups if ng.name.startswith(nodes.GROUP_NAME) and ng.get("kb_version") != nodes.GROUP_VERSION]  # sub-groups (KB Landscape Cut) have their own version
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
        # A folder picked per .blend holds the presets; the list shows the 5 most recently saved (Mike, LG-007).
        import time
        folder = tempfile.mkdtemp()
        presets.path = real
        bpy.context.scene.lg_preset_dir = folder
        for i in range(6):
            bpy.ops.landscape.preset_save(name=f"P{i}")
            time.sleep(0.02)
        check(os.path.exists(os.path.join(folder, "kitbash_landscape_presets.json")), "presets were not saved in the picked folder")
        shown = [it[0] for it in lg._preset_enum(None, bpy.context)]
        check(shown == ["P5", "P4", "P3", "P2", "P1"], f"the list should show the 5 most recent, newest first: {shown}")
        bpy.context.scene.lg_preset_all = True
        shown = [it[0] for it in lg._preset_enum(None, bpy.context)]
        bpy.context.scene.lg_preset_all = False
        check(len(shown) == 6 and shown[-1] == "P0", f"Show All should list all 6: {shown}")
    finally:
        presets.path = real
        bpy.context.scene.lg_preset_dir = ""
    return "volcano caldera look saved, loaded onto a Hills landscape, renamed, deleted; saved in a picked folder, 5 most recent listed"


MASKS = ("lg_height", "lg_slope", "lg_curvature", "lg_flow", "lg_wear", "lg_deposit", "lg_depth")


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
    return f"7 masks on all {len(lg.TYPES)} types, in 0-1; flow in hollows; {eroded} eroded types have flow and wear/deposit"


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
    ob.lg.show_mask = 'HEIGHT'
    g = view_colors()
    check(np.allclose(g[:, 0], g[:, 1]) and np.allclose(g[:, 1], g[:, 2]), "Grayscale should be gray (R = G = B)")
    ob.lg.mask_colors = 'HEAT'
    h = view_colors()
    check(not np.allclose(h[:, 0], h[:, 2]), "Heatmap should be coloured")
    ob.lg.mask_colors = 'GRAY'
    ob.lg.show_mask = 'NONE'
    check(np.allclose(view_colors()[:, :3], 0.0), "None should leave no mask colours")
    return "Height, Slope, Flow differ; Grayscale is gray, Heatmap coloured; None clears it"


@test("T10", "Terraces")
def _t10():
    done = []
    for key in ("mesa", "canyon", "badlands", "cliffs", "mountains"):
        fresh_scene()
        ob = add(key)
        ob.lg.erosion_amount = 0.0  # the plain shape, so the steps aren't eroded away
        plain = evaluated_points(ob)[:, 2].copy()
        ob.lg.terrace_strength = 0.0
        check(np.allclose(evaluated_points(ob)[:, 2], plain), f"{key}: Strength 0 changed the shape")
        ob.lg.terraces, ob.lg.terrace_strength, ob.lg.terrace_tilt = 6, 1.0, 0.0
        z = evaluated_points(ob)[:, 2]
        check(not np.allclose(z, plain), f"{key}: terraces did nothing")
        if key == "mountains":  # steady relief: count the benches in the height histogram
            zn = (z - z.min()) / np.ptp(z)
            hist = np.histogram(zn, bins=120)[0].astype(float)
            peaks = [i for i in range(1, 119) if hist[i] > hist[i - 1] and hist[i] >= hist[i + 1] and hist[i] > 1.8 * np.median(hist)]
            merged = [p for j, p in enumerate(peaks) if j == 0 or p - peaks[j - 1] > 4]
            check(4 <= len(merged) <= 8, f"mountains: {len(merged)} benches for 6 terraces")
            done.append(f"mountains {len(merged)} benches for 6")
        done.append(key)
    return "Strength 0 leaves the shape; terraces change " + ", ".join(done)


@test("T27", "Water level")
def _t27():
    fresh_scene()
    ob = add("mountains")

    def water_z():
        dg = bpy.context.evaluated_depsgraph_get()
        dg.update()
        ev = ob.evaluated_get(dg)
        me = ev.to_mesh()
        co = np.empty(len(me.vertices) * 3)
        me.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3)
        wet = np.zeros(len(me.vertices), bool)
        if "lg_water" in me.attributes:
            me.attributes["lg_water"].data.foreach_get("value", wet)
        ev.to_mesh_clear()
        return co[wet], co[~wet]
    check(not ob.lg.water, "Mountains should start without water")
    w, land = water_z()
    check(len(w) == 0, "water off should add no water")
    lg.sync_object(ob)
    key = ob.get("lg_erosion_key")
    ob.lg.water, ob.lg.water_level = True, 0.4
    w, land = water_z()
    check(ob.get("lg_erosion_key") == key, "turning water on re-ran erosion")
    lo, hi = land[:, 2].min(), land[:, 2].max()
    check(len(w) == 4 and np.ptp(w[:, 2]) < 1e-4, "water should be one flat sheet")
    check(abs(w[0, 2] - (lo + 0.4 * (hi - lo))) < 0.01 * (hi - lo), "water not at 40% of the relief")
    check(abs(np.abs(w[:, 0]).max() - ob.lg.size_x / 2) < 1e-3, "water should cover the landscape exactly")
    below = np.mean(land[:, 2] < w[0, 2])
    check(0.05 < below < 0.95, f"{below:.0%} of the ground under water: should be partly flooded")
    d = masks_of(ob)["lg_depth"]
    check(d.max() > 0.3 and (d > 0).mean() < 0.95 and (d == 0).mean() > 0.05, "water depth mask should be 0 on land, growing under water")
    z_before = w[0, 2]
    ob.lg.height_m = ob.lg.height_m * 2
    w, land = water_z()
    check(abs(w[0, 2] / z_before - 2.0) < 0.05, "water should follow Height")
    fresh_scene()
    ob = add("cliffs", keep_water=True)
    check(ob.lg.water, "Coastal Cliffs should start with the sea on")
    return f"off: none; on: flat sheet at 40% covering the landscape, {below:.0%} flooded; follows Height; Cliffs sea on"


@test("T29", "Bake to mesh keeps the shape and masks; Restore rebuilds it")
def _t29():
    fresh_scene()
    ob = add("mountains")
    ob.lg.water, ob.lg.water_level = True, 0.3
    lg.sync_object(ob)
    before = evaluated_points(ob)
    arr = ob.modifiers.new("Artist array", 'ARRAY')  # the artist's own modifier must not be baked in twice
    arr.count = 2
    with bpy.context.temp_override(active_object=ob, object=ob):
        check(bpy.ops.landscape.bake(save_preset=False) == {'FINISHED'}, "Bake did not finish")
    check(list(ob.modifiers) == [arr] and not ob.lg.is_landscape, "baked object should keep only the artist's modifiers")
    check(not any(m is not None and m.name.startswith(lg.nodes.WATER_MATERIAL) for m in ob.data.materials), "water material left on the ground")
    me = ob.data
    for name in ("lg_height", "lg_slope", "lg_flow", "lg_depth"):
        check(name in me.attributes, f"bake lost the {name} mask")
    check(len(me.vertices) == len(before) - 4, "water should leave the landscape mesh")
    water = bpy.data.objects.get(f"{ob.name}_Water")
    check(water is not None and len(water.data.vertices) == 4, "water should be its own 4-point object")
    check(water.data.materials and water.data.materials[0].name.startswith(lg.nodes.WATER_MATERIAL), "water lost its material")
    zb = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", zb)
    check(lg.RECIPE_KEY in ob.keys(), "settings not kept on the baked mesh")
    with bpy.context.temp_override(active_object=ob, object=ob):
        check(bpy.ops.landscape.restore() == {'FINISHED'}, "Restore did not finish")
    live = bpy.context.view_layer.objects.active
    check(water.hide_get(), "Restore should hide the baked water with the baked mesh")
    check(live is not ob and lg.landscape_modifier(live) and live.lg.water, "Restore should add a live landscape with the same settings")
    lg.sync_object(live)
    after = evaluated_points(live)
    land = after[:-4] if live.lg.water else after
    check(np.allclose(np.sort(land[:, 2]), np.sort(zb.reshape(-1, 3)[:, 2]), atol=1e-3 * np.ptp(zb)), "restored landscape doesn't match the baked mesh")
    ob[lg.RECIPE_KEY] = '{"type": "no_such_type"}'
    with bpy.context.temp_override(active_object=ob, object=ob):
        check(bpy.ops.landscape.restore() == {'CANCELLED'}, "Restore should refuse an unknown type")
    return "plain mesh with masks, water its own object, artist modifiers untouched; Restore rebuilds the same heights, refuses unknown types"


def mesh_report(ob):
    """Evaluated mesh: points, open (boundary) edges, non-manifold edges, cave faces and their bounds."""
    import bmesh
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    bm = bmesh.new()
    bm.from_mesh(me)
    open_edges = sum(1 for e in bm.edges if e.is_boundary)
    bad = sum(1 for e in bm.edges if not e.is_manifold and not e.is_boundary)
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    cave = me.attributes.get("lg_cave")
    cave_pts = np.zeros((0, 3))
    if cave is not None:
        flags = [d.value for d in cave.data]
        idx = sorted({i for f, flag in zip(me.polygons, flags) if flag for i in f.vertices})
        cave_pts = co.reshape(-1, 3)[idx]
    slope = me.attributes.get("lg_slope")
    slope_ok = slope is not None and all(math.isfinite(d.value) for d in slope.data)
    bm.free()
    ev.to_mesh_clear()
    return co.reshape(-1, 3), open_edges, bad, cave_pts, slope_ok


@test("T30", "Cave patch: watertight, local, real size")
def _t30():
    fresh_scene()
    ob = add("mountains")
    base, base_open, _bad, _c, _s = mesh_report(ob)
    ob.lg.cave_layout = 'ENTRANCE'
    check(abs(ob.lg.cave_size - 12.0) < 1e-6, f"a 200 m landscape's first cave should start 12 m wide, got {ob.lg.cave_size}")
    t0 = time.time()
    pts, open_edges, bad, cave, slope_ok = mesh_report(ob)
    dt = time.time() - t0
    check(len(cave) > 50, "no cave carved")
    check(open_edges == base_open and bad == 0, f"seam not watertight: {open_edges} open edges (landscape border {base_open}), {bad} non-manifold")
    check(slope_ok, "cave walls are missing the masks")
    c = cave.mean(axis=0)
    reach = ob.lg.cave_size * 3 + 1.5 * max(ob.lg.cave_size, 2 * ob.lg.cave_height) + 4.0  # the cave plus the face raised over its mouth
    far = lambda p: p[np.hypot(p[:, 0] - c[0], p[:, 1] - c[1]) > reach]
    a, b = far(base), far(pts)
    check(len(a) == len(b) and np.allclose(np.sort(a[:, 2]), np.sort(b[:, 2])), "the cave changed the landscape away from it")
    w1 = float(np.linalg.norm(np.ptp(cave, axis=0)))  # its 3D extent: the mouth may face another way at a new size
    set_size(ob, 400.0)
    _p, open2, bad2, cave2, _s = mesh_report(ob)
    check(open2 > 0 and bad2 == 0 and len(cave2) > 50, "cave lost on a bigger landscape")
    w2 = float(np.linalg.norm(np.ptp(cave2, axis=0)))
    check(abs(w2 / w1 - 1.0) < 0.2, f"cave should keep its real size when the landscape doubles: {w1:.1f} m -> {w2:.1f} m")
    return f"12 m entrance, {len(cave)} cave points, only the border open, rest untouched, {dt:.2f} s; {w1:.1f} m -> {w2:.1f} m at 2x size"


def cave_mesh(ob):
    """The cave object's evaluated mesh: (points, closed, floor-face centres, faces)."""
    import bmesh
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    bm = bmesh.new()
    bm.from_mesh(me)
    lw = bm.verts.layers.bool.get("lg_water")  # puddle water is its own open sheet, split off at bake like the landscapes' (D180)
    if lw is not None:
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if v[lw]], context='VERTS')
    closed = all(e.is_manifold for e in bm.edges) and len(bm.edges) > 0
    # One piece: loose bits floating off the cave (Mike) count as a second island.
    seen, islands = set(), 0
    for v0 in bm.verts:
        if v0.index in seen:
            continue
        islands += 1
        todo = [v0]
        seen.add(v0.index)
        while todo:
            v = todo.pop()
            for e in v.link_edges:
                o = e.other_vert(v)
                if o.index not in seen:
                    seen.add(o.index)
                    todo.append(o)
    closed = closed and islands == 1
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    # The inside only (D196): the cave is a hollow rock body now, and its outside (lg_outer) is not the cave's
    # shape (the hull's top faces down into the rock like a floor).
    outer = np.zeros(len(me.vertices), bool)
    if me.attributes.get("lg_outer") is not None:
        me.attributes["lg_outer"].data.foreach_get("value", outer)
    floor = np.array([f.center[:] for f in me.polygons if f.normal.z < -0.95 and not any(outer[i] for i in f.vertices)])
    n = len(me.polygons)
    bm.free()
    ev.to_mesh_clear()
    return co.reshape(-1, 3)[~outer], closed, floor, n


def cave_hits(ob, origin, direction, most=4):
    """Distances along a ray to each surface of the cave's evaluated mesh it crosses, nearest first."""
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    tree = BVHTree.FromPolygons([v.co.copy() for v in me.vertices], [tuple(p.vertices) for p in me.polygons])
    ev.to_mesh_clear()
    o, d, out, gone = Vector(origin), Vector(direction).normalized(), [], 0.0
    for _ in range(most):
        hit = tree.ray_cast(o, d)
        if hit[0] is None:
            break
        gone += hit[3]
        out.append(gone)
        o = hit[0] + d * 1e-3
        gone += 1e-3
    return out


@test("T14", "Cave object: closed rock body, open mouth, Lip, walk-in floor, real-size mouth")
def _t14():
    fresh_scene()
    check(bpy.ops.landscape.add_cave() == {'FINISHED'}, "Add Cave did not finish")
    ob = bpy.context.view_layer.objects.active
    c = ob.lg_cave
    check(c.is_cave and lg.caves.cave_modifier(ob), "Add Cave should make a cave object")
    c.wiggle = 0.0  # straight, so the walkway is the middle strip (talus rises at the sides)
    t0 = time.time()
    pts, closed, floor, n = cave_mesh(ob)
    dt = time.time() - t0
    check(closed, "the cave mesh should be one closed solid (the rock body round the cave, D196)")
    near = floor[(floor[:, 1] > 0.0) & (floor[:, 1] < c.depth * 0.5) & (np.abs(floor[:, 0]) < c.width * 0.2)]  # the walkway behind the mouth (the rounded front pokes out of the face and is cut away); talus rises at the sides
    check(len(near) > 0 and np.abs(near[:, 2]).max() < 0.12 * c.height, f"the floor by the mouth should be flat at 0 (off by {np.abs(near[:, 2]).max():.2f} m)")
    sec = pts[np.abs(pts[:, 1] - c.width * 0.5) < c.width * 0.08]
    w, h = np.ptp(sec[:, 0]), sec[:, 2].max()
    check(abs(w / c.width - 1) < 0.3 and abs(h / c.height - 1) < 0.3, f"mouth {w:.1f} x {h:.1f} m, set {c.width:.0f} x {c.height:.0f} m")
    check(c.depth < pts[:, 1].max() < c.depth + c.width, f"cave should run back about {c.depth:.0f} m, reaches {pts[:, 1].max():.1f} m")
    check(pts[:, 1].min() < 0, "the front should poke out in front of the mouth, through the face")
    # The open mouth (5.3a, D196): from mid-passage, looking out at head height, nothing in the way; the floor
    # runs out in front. Sideways through the mouth's wall: the inside, then the rock's outside, a wall the Lip
    # slider sets apart (at least 1.5 Preview voxels, the narrower of the half width and the height over 6).
    out_hits = cave_hits(ob, (0.0, c.depth * 0.3, c.height * 0.5), (0.0, -1.0, 0.0))
    check(not out_hits, f"the mouth should be open: looking out from inside hit rock {out_hits[0]:.1f} m away" if out_hits else "")
    check(cave_hits(ob, (0.0, -c.width * 0.1, 2.0), (0.0, 0.0, -1.0)), "the floor should run out of the mouth")

    def wall(lip):
        c.lip = lip
        # Sideways through the wall just behind the face cut, under the roof's ledges: the mouth's rock, the only
        # wall Lip thins (behind the mouth it stays at least 3 Preview voxels, D197).
        up = cave_hits(ob, (0.0, c.width * 0.4, c.height * 0.3), (1.0, 0.0, 0.0))
        return (up[1] - up[0]) if len(up) >= 2 else 0.0, max(c.width * lg.caves.lip_thickness(lip), 1.5 * min(c.width * 0.5, c.height) / 6.0)
    thin, want_thin = wall(0.1)
    mid, want_mid = wall(0.55)
    thick, want_thick = wall(1.0)
    # Every step of the slider counts, the default included (first-pass review: under 0.25 it did nothing).
    check(all(0.6 < a / b < 1.6 for a, b in ((thin, want_thin), (mid, want_mid), (thick, want_thick))) and thin < mid < thick,
          f"the rock over the mouth should be as thick as Lip sets: {thin:.1f} / {mid:.1f} / {thick:.1f} m at Lip 0.1 / 0.55 / 1 (want {want_thin:.1f} / {want_mid:.1f} / {want_thick:.1f})")
    c.lip = 0.1
    c.chamber, c.ceiling = 30.0, 15.0
    pc, closed2, _f, _n = cave_mesh(ob)
    back = pc[pc[:, 1] > c.depth * 0.8]
    check(closed2 and np.ptp(back[:, 0]) > 20 and back[:, 2].max() > 11, f"chamber should be about 30 m wide, 15 m tall: {np.ptp(back[:, 0]):.1f} x {back[:, 2].max():.1f} m")
    c.chamber, c.drop = 0.0, 5.0
    pd, closed3, _f, _n = cave_mesh(ob)
    low = pd[pd[:, 1] > c.depth * 0.85, 2].min()
    check(closed3 and -6.0 < low < -4.0, f"Drop 5 m: the floor at the back should be about 5 m down, got {low:.1f} m")
    c.drop = 0.0
    c.chamber, c.chamber_drop = 30.0, 8.0
    pk, closed4, _f, _n = cave_mesh(ob)
    sunk = pk[pk[:, 1] > c.depth * 0.85, 2].min()
    check(closed4 and sunk < -6.0, f"Chamber Drop 8 m: the chamber floor should sink about 8 m, got {sunk:.1f} m")
    c.ramp, c.wiggle = True, 0.0  # Ramp into Chamber: a walkable slope down the middle, not a drop
    pr, closed_r, _f, _n = cave_mesh(ob)
    mid = pr[(np.abs(pr[:, 0]) < c.width * 0.15) & (pr[:, 1] > c.depth * 0.45) & (pr[:, 1] < c.depth + c.chamber * 0.4)]
    bins = {}
    for x, y, z in mid:
        bins.setdefault(int(y), []).append(z)
    walk = [min(v) for _k, v in sorted(bins.items())]
    worst = max(abs(a - b) for a, b in zip(walk, walk[1:]))
    check(closed_r and worst < 1.0 and walk[0] - walk[-1] > 5.0, f"ramp should walk down about 8 m at a walkable slope: drops {walk[0] - walk[-1]:.1f} m, worst step {worst:.2f} m")
    c.rubble, c.roughness = 1.0, 1.0  # the worst case for loose pieces and holes: lots of rock, ramp on
    _p, one_piece, _f, _n = cave_mesh(ob)
    check(one_piece, "with Rubble and the ramp on the cave should still be one closed piece (no holes or loose bits)")
    c.rubble, c.roughness, c.ramp = 0.5, 0.5, False
    c.chamber, c.chamber_drop, c.wiggle, c.depth = 0.0, 0.0, 1.0, 60.0  # room for a swing each way
    pw, _c, _f, _n = cave_mesh(ob)
    mid = pw[(pw[:, 1] > c.width) & (pw[:, 2] > c.height * 0.3)]
    check(mid[:, 0].min() < -c.width * 0.3 and mid[:, 0].max() > c.width * 0.3, "Wiggle should swing both left and right")
    c.wiggle, c.depth = 0.3, 30.0
    c.detail = 'HIGH'
    _p, closed5, _f, n_high = cave_mesh(ob)
    check(closed5 and n_high > n * 2, f"High detail should build a finer cave: {n:,} -> {n_high:,} faces")
    c.detail = 'PREVIEW'
    # Rubble is separate rock pieces over the shell (D107): none at Rubble 0, many at 1; never cut into the shell.
    def rocks_in(o):
        dg = bpy.context.evaluated_depsgraph_get()
        dg.update()
        return sum(1 for i in dg.object_instances if i.is_instance and i.parent and i.parent.original == o and "KB Rock" in i.object.name)
    c.rubble = 0.0
    p0, _c0, _f0, n0 = cave_mesh(ob)
    r0 = rocks_in(ob)
    c.rubble = 1.0
    p1, _c1, _f1, n1 = cave_mesh(ob)
    r1 = rocks_in(ob)
    check(r0 == 0 and r1 > 10, f"Rubble 0 should have no rocks and Rubble 1 many: {r0} vs {r1}")
    check(n0 == n1, f"rocks should never change the cave shell: {n0:,} vs {n1:,} faces")
    c.chamber, c.chamber_drop, c.ramp = 30.0, 8.0, True
    with_ramp = rocks_in(ob)
    c.ramp = False
    no_ramp = rocks_in(ob)
    # The ramp carries no rocks while the walls are dialled in (Mike, D116), so it may only cover floor rocks.
    check(with_ramp <= no_ramp, f"the ramp should add no rocks of its own: {with_ramp} vs {no_ramp}")
    c.chamber, c.chamber_drop = 0.0, 0.0
    c.rubble, c.seed = 0.5, 7
    p7, _c, _f, _n = cave_mesh(ob)
    check(len(p7) != len(pts) or not np.allclose(p7, pts), "a new seed should change the cave")
    seed = c.seed
    check(bpy.ops.landscape.randomize_cave() == {'FINISHED'} and c.seed != seed, "Randomize should pick a new seed")
    # Reset puts the shape back, keeping the seed (as on the landscapes).
    c.width, c.depth, c.rubble = 30.0, 90.0, 0.9
    seed = c.seed
    check(bpy.ops.landscape.reset_cave() == {'FINISHED'} and c.width == 12.0 and c.depth == 30.0 and c.rubble == 0.5 and c.seed == seed,
          "Reset should put the cave's sizes back and keep its seed")
    # Presets: a cave saves to the same list as the landscapes and loads back onto a cave.
    import tempfile
    from kitbash_landscape_generator import presets
    tmp = os.path.join(tempfile.mkdtemp(), "presets.json")
    real = presets.path
    presets.path = lambda: tmp  # never touch the artist's own presets
    try:
        c.width, c.chamber = 21.0, 40.0
        check(bpy.ops.landscape.preset_save(name="Test Cave") == {'FINISHED'}, "Save Preset should save a cave")
        check(presets.load_all()["Test Cave"].get("kind") == "cave", "a cave preset should be marked as a cave")
        bpy.ops.landscape.reset_cave()
        bpy.context.scene.lg_preset = "Test Cave"
        check(bpy.ops.landscape.preset_load() == {'FINISHED'} and c.width == 21.0 and c.chamber == 40.0, "loading a cave preset should restore the cave")
    finally:
        presets.path = real
    return f"closed, {n:,} faces in {dt:.2f} s; mouth {w:.1f} x {h:.1f} m (set 12 x 6), flat floor, {pts[:, 1].max():.0f} m deep; chamber, drop, ramp, rubble, seed, Reset, presets work"


@test("T11", "Erosion lowers steep slopes")
def _t11():
    fresh_scene()
    ob = add("mountains")
    out = []
    for amount in (0.0, 0.5, 1.0):
        ob.lg.erosion_amount = amount
        lg.sync_object(ob)
        p = evaluated_points(ob)
        check(np.isfinite(p).all(), f"Erosion {amount}: NaN in the landscape")
        n = int(round(np.sqrt(len(p))))
        z = p[:n * n, 2].reshape(n, n)
        gy, gx = np.gradient(z, ob.lg.size_x / (n - 1))
        out.append(float(np.percentile(np.degrees(np.arctan(np.hypot(gx, gy))), 99)))
    check(out[1] < out[0] and out[2] <= out[1] + 0.5, f"steepest slopes should drop as erosion rises: {[round(v, 1) for v in out]}")
    return "99th-percentile slope " + " -> ".join(f"{v:.1f}" for v in out) + " deg at Erosion 0 / 0.5 / 1"


@test("T12", "Final build time")
def _t12():
    fresh_scene()
    t0 = time.time()
    ob = add("mountains")
    ob.lg.size_x = ob.lg.size_y = 1000.0
    ob.lg.final = True
    lg.sync_object(ob)
    evaluated_points(ob)
    dt = time.time() - t0
    check(dt <= 60.0, f"1 km at High took {dt:.0f} s (limit 60 s)")
    return f"1 km Mountains at High with erosion: {dt:.1f} s (limit 60 s)"


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
                "height", "feature_scale", "roughness", "sharpness", "cave_size_set"}
    props = [p for p in bpy.types.Object.bl_rna.properties["lg"].fixed_type.properties if p.identifier not in internal]
    missing = [p.identifier for p in props if len((p.description or "").strip()) < 10]
    check(not missing, f"controls without a tooltip: {missing}")
    ops = [c for c in vars(lg).values() if isinstance(c, type) and issubclass(c, bpy.types.Operator) and c is not bpy.types.Operator]
    no_desc = [o.bl_idname for o in ops if len((getattr(o, "bl_description", "") or "").strip()) < 10]
    check(ops and not no_desc, f"buttons without a tooltip: {no_desc}")
    return f"{len(props)} controls and {len(ops)} buttons all have tooltips (plain-language review: manual)"


@test("T31", "Cave UVs: a few natural islands, square, even")
def _t31():
    # Mike (D149): the UV map splits only where the cave does (floor, walls, chamber), never into lots of small
    # islands; squares stay square and the texel density even.
    fresh_scene()
    bpy.ops.landscape.add_cave()
    ob = bpy.context.view_layer.objects.active
    c = ob.lg_cave
    c.rock, c.chamber, c.ceiling = 'LAVA', 30.0, 16.0
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    check(me.uv_layers.get("UVMap") is not None, "the cave should have a UVMap")
    me.calc_loop_triangles()
    nt = len(me.loop_triangles)
    li = np.zeros(nt * 3, np.int32); me.loop_triangles.foreach_get('loops', li); li = li.reshape(-1, 3)
    vi = np.zeros(nt * 3, np.int32); me.loop_triangles.foreach_get('vertices', vi); vi = vi.reshape(-1, 3)
    co = np.zeros(len(me.vertices) * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    uv = np.zeros(len(me.loops) * 2); me.uv_layers["UVMap"].data.foreach_get('uv', uv); uv = uv.reshape(-1, 2)
    e1, e2 = co[vi[:, 1]] - co[vi[:, 0]], co[vi[:, 2]] - co[vi[:, 0]]
    f1, f2 = uv[li[:, 1]] - uv[li[:, 0]], uv[li[:, 2]] - uv[li[:, 0]]
    a3 = np.linalg.norm(np.cross(e1, e2), axis=1) / 2
    a2 = np.abs(f1[:, 0] * f2[:, 1] - f1[:, 1] * f2[:, 0]) / 2
    ok = a3 > 1e-9
    r = (a2[ok] / a3[ok]) / (a2[ok].sum() / a3[ok].sum())
    even = float(((r > 0.5) & (r < 2.0)) @ (a3[ok] / a3[ok].sum()))
    # How square: the longest over the shortest stretch of each triangle's UVs.
    nrm = np.cross(e1, e2); nrm /= np.linalg.norm(nrm, axis=1)[:, None] + 1e-12
    ax = e1 / (np.linalg.norm(e1, axis=1)[:, None] + 1e-12); ay = np.cross(nrm, ax)
    pm = np.stack([np.stack([(e1 * ax).sum(1), (e1 * ay).sum(1)], 1), np.stack([(e2 * ax).sum(1), (e2 * ay).sum(1)], 1)], 2)
    good = ok & (np.abs(np.linalg.det(pm)) > 1e-12)
    sv = np.linalg.svd(np.stack([f1, f2], 2)[good] @ np.linalg.inv(pm[good]), compute_uv=False)
    square = float((sv[:, 0] / np.maximum(sv[:, 1], 1e-12) < 1.5) @ (a3[good] / a3[good].sum()))
    # Islands: faces joined across edges whose corners share UVs.
    lv = np.zeros(len(me.loops), np.int32); me.loops.foreach_get('vertex_index', lv)
    parent = list(range(len(me.polygons)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    seen = {}
    for poly in me.polygons:
        ls = list(poly.loop_indices)
        for j in range(len(ls)):
            la, lb = ls[j], ls[(j + 1) % len(ls)]
            va, vb = lv[la], lv[lb]
            ua, ub = tuple(np.round(uv[la], 5)), tuple(np.round(uv[lb], 5))
            key, sig = (min(va, vb), max(va, vb)), ((ua, ub) if va < vb else (ub, ua))
            if key in seen:
                if seen[key][1] == sig:
                    parent[find(seen[key][0])] = find(poly.index)
            else:
                seen[key] = (poly.index, sig)
    sizes = {}
    for i in range(len(me.polygons)):
        sizes[find(i)] = sizes.get(find(i), 0) + 1
    # The inside's islands (D196): the rock body's outside (lg_outer) gets its own few, which are not counted.
    outer = np.zeros(len(me.vertices), bool)
    if me.attributes.get("lg_outer") is not None:
        me.attributes["lg_outer"].data.foreach_get("value", outer)
    # Puddle water is its own sheet, split off at bake (D180), and now on every rock (LG-062): not the rock's UVs.
    wet_any = np.zeros(len(me.vertices), bool)
    if me.attributes.get("lg_water") is not None:
        me.attributes["lg_water"].data.foreach_get("value", wet_any); outer |= wet_any
    inside = {find(p.index) for p in me.polygons if not outer[list(p.vertices)].any()}
    # Square and even measured on the inside too; the outside is reported (its UVs come with M7, D196).
    t_in = ~outer[vi].any(1)

    w_good = a3[good] * t_in[good]
    square_out = square
    square = float((sv[:, 0] / np.maximum(sv[:, 1], 1e-12) < 1.5) @ (w_good / w_good.sum()))
    w_ok = a3[ok] * t_in[ok]
    even = float(((r > 0.5) & (r < 2.0)) @ (w_ok / w_ok.sum()))
    wet_isl = {find(p.index) for p in me.polygons if wet_any[list(p.vertices)].all()}
    ev.to_mesh_clear()
    small = sum(1 for k, v in sizes.items() if v < 50 and k not in wet_isl)  # puddle sheets are small by nature
    check(len(inside) <= 12 and small == 0, f"{len(inside)} UV islands inside ({len(sizes)} in all), {small} under 50 faces (want at most 12 inside, none small)")
    check(square > 0.9, f"{square:.0%} of the area has square UVs (under 1.5 to 1); want over 90%")
    check(even > 0.9, f"{even:.0%} of the area is within 0.5x to 2x of the average texel density; want over 90%")
    return f"{len(inside)} islands inside, {len(sizes)} in all, {square:.0%} square, {even:.0%} even inside ({square_out:.0%} square with the outside)"


@test("T15", "Stalactites hang, stalagmites stand")
def _t15():
    # 5.4 (D168-D173): formations only in limestone; stalactites hang plumb from the roof with their pivot on it,
    # stalagmites stand on the floor sunk a little, none floats, none under 2 ft (Mike); none in jointed or lava.
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    fresh_scene()
    bpy.ops.landscape.add_cave()
    ob = bpy.context.view_layer.objects.active
    c = ob.lg_cave
    c.chamber, c.ceiling, c.formations = 30.0, 16.0, 1.0

    def pieces():
        dg = bpy.context.evaluated_depsgraph_get()
        dg.update()
        ev = ob.evaluated_get(dg)
        me = ev.to_mesh()
        bvh = BVHTree.FromPolygons([v.co.copy() for v in me.vertices], [tuple(f.vertices) for f in me.polygons])
        ev.to_mesh_clear()
        out = [(i.object.name, i.matrix_world.copy(), np.ptp([v.co.z for v in i.object.data.vertices])) for i in dg.object_instances
               if i.is_instance and i.parent and i.parent.original == ob and "KB Formation" in i.object.name]
        return out, bvh
    found, bvh = pieces()
    hang = [f for f in found if "Stalactite" in f[0]]
    stand = [f for f in found if "Stalagmite" in f[0]]
    # More than 3 (was 5): since D189 the keep tests read the Preview-grid roof; this tiny cave went 6 -> 4, a big one 571 -> 599.
    check(len(hang) > 3 and len(stand) > 2, f"limestone should grow stalactites and stalagmites: {len(hang)} and {len(stand)}")
    for name, m, tall in found:
        up = (m.to_3x3() @ Vector((0, 0, 1))).normalized()
        check(up.z > 0.999, f"{name} is tipped ({up.z:.3f}); formations grow plumb")
        check(tall * m.to_scale().z > 0.6, f"{name} is {tall * m.to_scale().z:.2f} m; none under 2 ft")
    for name, m, _tall in hang:
        p = m.translation
        hit = bvh.ray_cast(p - Vector((0, 0, 1.0)), Vector((0, 0, 1)), 3.0)
        check(hit[0] is not None and abs(hit[3] - 1.0) < 0.05, f"{name} pivot is off the roof by {None if hit[0] is None else round(hit[3] - 1.0, 3)} m")
    for name, m, _tall in stand:
        p = m.translation
        hit = bvh.ray_cast(p + Vector((0, 0, 1.0)), Vector((0, 0, -1)), 3.0)
        sunk = None if hit[0] is None else hit[3] - 1.0
        check(sunk is not None and -0.02 < -sunk < 0.2, f"{name} should sit sunk 0-0.2 m into the floor: {sunk}")
    n_lime = len(found)
    rest = {}
    for rock in ('JOINTED', 'LAVA'):
        c.rock = rock
        rest[rock] = len(pieces()[0])
    check(not any(rest.values()), f"jointed and lava grow no formations: {rest}")
    c.rock, c.formations = 'LIMESTONE', 0.0
    check(not pieces()[0], "Formations 0 should grow none")
    return f"{len(hang)} stalactites on the roof, {len(stand)} stalagmites set in the floor, all plumb and over 2 ft; none in jointed or lava, none at 0 ({n_lime} at 1)"


@test("T32", "Same formations at every Detail Level")
def _t32():
    # D189 (Mike): Preview, High and Ultra grow exactly the same formations, same count, same spots, so the
    # level is predictable; at every level each stalactite's pivot sits on the finished roof (none floats).
    # Also: an old cave catches up to this add-on, and the formation pickers show the library kits.
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    from kitbash_landscape_generator import caves, features
    fresh_scene()
    bpy.ops.landscape.add_cave()
    ob = bpy.context.view_layer.objects.active
    c = ob.lg_cave
    check(all(getattr(c, p) is not None for p in caves.FORMATION_KITS.values()), "a new cave's formation pickers should show the library kits")
    c.chamber, c.ceiling, c.formations = 30.0, 16.0, 1.0
    seen, floating = {}, {}
    for level in ('PREVIEW', 'HIGH', 'ULTRA'):
        c.detail = level
        dg = bpy.context.evaluated_depsgraph_get()
        dg.update()
        ev = ob.evaluated_get(dg)
        me = ev.to_mesh()
        bvh = BVHTree.FromPolygons([v.co.copy() for v in me.vertices], [tuple(f.vertices) for f in me.polygons])
        ev.to_mesh_clear()
        found = [(i.object.name.rsplit(" ", 1)[0], i.matrix_world.copy())
                 for i in dg.object_instances if i.is_instance and i.parent and i.parent.original == ob and "KB Formation" in i.object.name]
        seen[level] = sorted((round(m.translation.x, 1), round(m.translation.y, 1)) for _n, m in found)
        off = 0
        for n, m in found:
            if "Stalactite" in n:
                hit = bvh.ray_cast(m.translation - Vector((0, 0, 1.0)), Vector((0, 0, 1)), 3.0)
                off += hit[0] is None or abs(hit[3] - 1.0) > 0.05
        floating[level] = off
    counts = {k: len(v) for k, v in seen.items()}
    check(len(set(counts.values())) == 1, f"formation counts differ by level: {counts}")
    check(seen['PREVIEW'] == seen['HIGH'] == seen['ULTRA'], "the same formations should stand in the same spots at every level")
    check(not any(floating.values()), f"stalactites off the roof by level: {floating}")
    # Each amount slider thins only its own family (Mike, D189).
    def fams():
        dg = bpy.context.evaluated_depsgraph_get(); dg.update()
        names = [i.object.name for i in dg.object_instances if i.is_instance and i.parent and i.parent.original == ob and "KB Formation" in i.object.name]
        return {f: sum(f in n for n in names) for f in ("Stalactite", "Stalagmite", "Column")}
    c.detail = 'PREVIEW'
    full = fams()
    c.stalactite_amount = 0.0
    no_tite = fams()
    check(no_tite["Stalactite"] == 0 and no_tite["Stalagmite"] == full["Stalagmite"] and no_tite["Column"] == full["Column"], f"Stalactites 0 should take only the stalactites: {full} -> {no_tite}")
    c.stalactite_amount, c.stalagmite_amount = 1.0, 0.0
    no_mite = fams()
    check(no_mite["Stalagmite"] == 0 and no_mite["Stalactite"] == full["Stalactite"], f"Stalagmites 0 should take only the stalagmites: {full} -> {no_mite}")
    c.stalagmite_amount, c.column_amount = 1.0, 0.0
    no_col = fams()
    check(no_col["Column"] == 0 and no_col["Stalactite"] == full["Stalactite"] and no_col["Stalagmite"] == full["Stalagmite"], f"Columns 0 should take only the columns: {full} -> {no_col}")
    c.column_amount = 1.0
    mod = caves.cave_modifier(ob)
    mod.node_group["kb_version"] = -1
    c.formations = 0.9
    check(mod.node_group.get("kb_version") == features.CAVE_VERSION, "an old cave should catch up to this add-on on its next change")
    return f"{counts['PREVIEW']} formations at Preview, High and Ultra, same spots, none off the roof; amount sliders each take only their own family; old caves upgrade; pickers filled"


@test("T36", "Face counts per Detail Level shown before switching")
def _t36():
    # Mike (LG-055): High gave 15M faces with no warning. The panel estimates every level from the current one.
    fresh_scene()
    bpy.ops.landscape.add_cave()
    ob = bpy.context.view_layer.objects.active
    c = ob.lg_cave
    got = {}
    for lvl in ("PREVIEW", "HIGH"):
        c.detail = lvl
        dg = bpy.context.evaluated_depsgraph_get()
        dg.update()
        got[lvl] = (lg.caves.face_estimates(ob, bpy.context, lg.caves.DETAIL_INDEX[lvl]), len(ob.evaluated_get(dg).data.polygons))
    (est_p, real_p), (est_h, real_h) = got["PREVIEW"], got["HIGH"]
    check(est_p is not None and est_h is not None, "the cave should carry lg_basis so the panel can estimate")
    check(est_p is not None and abs(est_p[1] / real_h - 1) < 0.2 and abs(est_h[0] / real_p - 1) < 0.2,
          f"estimates should be within 20%: High from Preview {est_p[1]:,.0f} vs {real_h:,}; Preview from High {est_h[0]:,.0f} vs {real_p:,}")
    return f"High from Preview {est_p[1] / 1e6:.2f}M (real {real_h / 1e6:.2f}M), Preview from High {est_h[0] / 1e6:.2f}M (real {real_p / 1e6:.2f}M), Ultra about {est_p[2] / 1e6:.1f}M"


@test("T38", "List keeps its landscape; Fit to Selection on a turned landscape; quick scale keeps the ratio")
def _t38():
    # Old checker notes (LG-043).
    import math as _m
    fresh_scene()
    scene = bpy.context.scene
    bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
    spare = bpy.context.active_object
    a = add("hills")
    scene.lg_index = list(scene.objects).index(a)
    bpy.data.objects.remove(spare)  # every list position after it shifts
    bpy.context.view_layer.objects.active = None
    check(lg.current_landscape(bpy.context) == a, "the picked landscape should stay picked when another object is removed")
    bpy.context.view_layer.objects.active = a
    a.lg.size_x, a.lg.size_y = 10.0, 5.0
    bpy.ops.landscape.scale_size(factor=0.05)
    check(abs(a.lg.size_x / a.lg.size_y - 2.0) < 1e-6 and a.lg.size_y >= 1.0, f"quick scale should keep 2:1 at the 1 m limit: {a.lg.size_x:.2f} x {a.lg.size_y:.2f}")
    scaled = (a.lg.size_x, a.lg.size_y)
    a.rotation_euler.z = _m.radians(45)
    a.scale = (2.0, 2.0, 1.0)  # sizes are in the landscape's own units: half the world reach
    bpy.ops.mesh.primitive_cube_add(size=2.0, location=(30.0, 0.0, 0.0))
    cube = bpy.context.active_object
    for o in bpy.context.view_layer.objects:
        o.select_set(o == cube)
    bpy.context.view_layer.objects.active = a
    bpy.context.view_layer.update()
    check(bpy.ops.landscape.fit_selection() == {"FINISHED"}, "Fit to Selection did not run")
    check(abs(a.lg.size_x - (31.0 * _m.cos(_m.radians(45)) + 1.0 * _m.sin(_m.radians(45))) * lg.FIT_MARGIN) < 0.5, f"Fit on a turned, 2x-scaled landscape: width {a.lg.size_x:.1f}")
    return f"picked landscape kept by reference; 0.05x gives {scaled[0]:.0f} x {scaled[1]:.0f} m (2:1 kept); fit on a 45 degree, 2x landscape {a.lg.size_x:.1f} x {a.lg.size_y:.1f} m"


@test("T39", "Export package: recipe, 16-bit heightmap, masks, Unity RAW; base left out")
def _t39():
    # LG-023 / docs/PACKAGE.md: the files every other app reads.
    import json, tempfile
    from kitbash_landscape_generator import export
    fresh_scene()
    ob = add("hills")
    ob.lg.base, ob.lg.base_depth = True, 15.0  # the base must not reach the heightmap
    folder = tempfile.mkdtemp()
    out = export.write_package(ob, folder, lg.presets.capture(ob.lg, lg.CONTROL_PROPS), 1009, raw16=True)
    check(os.path.basename(out) == f"{ob.name}.kblandscape", f"folder should be named after the landscape: {out}")
    with open(os.path.join(out, "recipe.json"), encoding="utf-8") as fh:
        rec = json.load(fh)
    check(rec["format"] == "kblandscape" and len(rec["tiles"]) == 1 and rec["tiles"][0]["type"] == "hills" and "controls" in rec["tiles"][0] and rec["base"]["on"], "recipe.json should hold one hills tile with its controls, and the base")
    dg = bpy.context.evaluated_depsgraph_get()
    me = ob.evaluated_get(dg).to_mesh()
    h, masks = export.top_grid(me, ob.lg.size_x, ob.lg.size_y)
    ob.evaluated_get(dg).to_mesh_clear()
    lo, hi = rec["height_range"]
    bottom = min(v.co.z for v in ob.evaluated_get(dg).data.vertices)
    check(lo > bottom + 10.0, f"the base should be left out: heightmap starts at {lo:.2f} m, the base bottom is {bottom:.2f} m")
    img = bpy.data.images.load(os.path.join(out, "height.png"))
    img.colorspace_settings.is_data = True
    px = np.array(img.pixels[:]).reshape(img.size[1], img.size[0], -1)[:, :, 0]
    check(img.size[0] == 1009 and img.size[1] == 1009, f"heightmap should be 1009 px: {tuple(img.size)}")
    # Every pixel, so a flip or a mid-range shift shows, not only the corners.
    want = export.resample(np.where(np.isnan(h), lo, h), 1009)
    err = np.abs(lo + px * (hi - lo) - want).max()
    check(err < (hi - lo) / 65535 * 2 + 1e-3, f"heightmap off by up to {err:.4f} m")
    with open(os.path.join(out, "height.png"), "rb") as fh:
        ihdr = fh.read(26)
    check(ihdr[24] == 16 and ihdr[25] == 0, f"height.png should be 16-bit grayscale: depth {ihdr[24]}, colour type {ihdr[25]}")
    raw = np.fromfile(os.path.join(out, "height.r16"), "<u2")
    check(raw.size == 1009 * 1009, f"height.r16 should be 1009 x 1009: {raw.size}")
    missing = [n for n in export.MASKS if n in masks and not os.path.exists(os.path.join(out, f"mask_{n[3:]}.png"))]
    check(masks and not missing, f"mask images missing: {missing}")
    return f"{os.path.basename(out)}: recipe, height.png 1009 px, height.r16, {len(masks)} masks; every pixel within two 16-bit steps; base left out"


@test("T33", "Flooded chamber: flat water wall to wall, formations clear of it")
def _t33():
    # D193 (Mike): Water = Flooded Chamber fills the chamber with one flat sheet at Water Level, its shore on the
    # walls (no gap, nothing past the shell); no stalactite tip in the water, no stalagmite wholly under it; the same
    # at every Detail Level; None and Puddles grow no flood sheet.
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    fresh_scene()
    bpy.ops.landscape.add_cave()
    ob = bpy.context.view_layer.objects.active
    c = ob.lg_cave
    c.chamber, c.ceiling, c.chamber_drop, c.formations = 30.0, 16.0, 8.0, 1.0

    def look():
        dg = bpy.context.evaluated_depsgraph_get(); dg.update()
        ev = ob.evaluated_get(dg); me = ev.to_mesh()
        wet = me.attributes.get("lg_water")
        wv = [v.co.copy() for v in me.vertices if wet and wet.data[v.index].value]
        dry = [i for i, v in enumerate(me.vertices) if not (wet and wet.data[v.index].value)]
        dset = set(dry)
        bvh = BVHTree.FromPolygons([v.co.copy() for v in me.vertices], [tuple(f.vertices) for f in me.polygons if all(x in dset for x in f.vertices)])
        ev.to_mesh_clear()
        pcs = [(i.object.name, i.matrix_world.copy(), i.object) for i in dg.object_instances
               if i.is_instance and i.parent and i.parent.original == ob and "KB Formation" in i.object.name]
        return wv, bvh, pcs
    c.water = 'PUDDLES'
    wv, _b, _p = look()
    c.water = 'FLOOD'
    seen = {}
    for level in ('PREVIEW', 'HIGH'):
        c.detail = level
        wv, bvh, pcs = look()
        zs = {round(v.z, 3) for v in wv}
        check(len(wv) > 100 and len(zs) == 1, f"{level}: the flood should be one flat sheet: {len(wv)} points at {len(zs)} heights")
        wz = wv[0].z
        # shore on the wall: every sheet point is in the cave (roof straight above) or on the shell itself
        off = 0
        for v in wv[::7]:
            up = bvh.ray_cast(v + Vector((0, 0, 0.01)), Vector((0, 0, 1)), 500.0)
            near = bvh.find_nearest(v)
            off += not ((up[0] is not None and up[1].z > 0) or (near[0] is not None and near[3] < 0.5))
        check(off == 0, f"{level}: {off} water points sit inside the rock, away from the wall")
        wet_tip, drowned = 0, 0
        for n, m, o in pcs:
            zz = [(m @ Vector(b)).z for b in o.bound_box]
            if "Stalactite" in n and min(zz) < wz:
                wet_tip += 1
            if "Stalagmite" in n and max(zz) < wz:
                drowned += 1
        check(not wet_tip and not drowned, f"{level}: {wet_tip} stalactite tips in the water, {drowned} stalagmites under it")
        seen[level] = sorted((round(m.translation.x, 1), round(m.translation.y, 1)) for _n, m, _o in pcs)
    check(seen['PREVIEW'] == seen['HIGH'], "the same formations should stand at every level when flooded")
    c.water = 'NONE'
    check(not look()[0], "Water None should grow no water")
    return f"one flat sheet at {wz:.1f} m, shore on the walls, {len(seen['HIGH'])} formations clear of it at Preview and High; None dry"


@test("T34", "Base: solid sides to a flat bottom, watertight, top untouched; bakes; water inside it")
def _t34():
    # LG-070 (D203): Base off leaves the landscape as it was; on, the border goes straight down to a flat bottom
    # Base Depth below the lowest ground and the bottom is closed. Only sides and bottom carry lg_base. Top and
    # base are told apart by lg_base and position, never by point or face order.
    import bmesh
    fresh_scene()
    ob = add("mountains")
    lg.sync_object(ob)

    def read(me):
        co = np.empty(len(me.vertices) * 3)
        me.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3)
        flag = np.zeros(len(me.polygons), bool)
        if "lg_base" in me.attributes:
            me.attributes["lg_base"].data.foreach_get("value", flag)
        wet = np.zeros(len(me.vertices), bool)
        if "lg_water" in me.attributes:
            me.attributes["lg_water"].data.foreach_get("value", wet)
        h = np.zeros(len(me.vertices))
        if "lg_height" in me.attributes:
            me.attributes["lg_height"].data.foreach_get("value", h)
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.faces.ensure_lookup_table()
        edge_faces = [len(e.link_faces) for e in bm.edges if not wet[e.verts[0].index]]
        faces = [(np.array([v.index for v in f.verts]), np.array(f.normal), np.array(f.calc_center_median()))
                 for f in bm.faces]
        bm.free()
        return co, flag, wet, h, edge_faces, faces

    def look():
        dg = bpy.context.evaluated_depsgraph_get()
        dg.update()
        ev = ob.evaluated_get(dg)
        out = read(ev.to_mesh())
        ev.to_mesh_clear()
        return out

    def key(p):
        return (round(float(p[0]), 3), round(float(p[1]), 3))
    check(not ob.lg.base, "Base should start off")
    co0, flag0, _w, h0, ef0, faces0 = look()
    check(not flag0.any() and min(ef0) == 1, "Base off should leave the open landscape sheet")
    top0 = {key(p): (p[2], hh) for p, hh in zip(co0, h0)}
    ob.lg.base, ob.lg.base_depth = True, 15.0
    co, flag, _w, h, ef, faces = look()
    bottom = co0[:, 2].min() - 15.0
    check(min(ef) == 2 and max(ef) == 2, f"not watertight: edges with {sorted(set(ef))} faces")
    check((~flag).sum() == len(faces0), f"{(~flag).sum()} unmarked faces, the top has {len(faces0)}")
    top = np.zeros(len(co), bool)
    for (vs, _n, _m), on in zip(faces, flag):
        if not on:
            top[vs] = True
    check(top.sum() == len(co0), f"{top.sum()} top points, Base off had {len(co0)}")
    moved = 0
    for p, hh in zip(co[top], h[top]):
        z0, h_0 = top0.get(key(p), (None, None))
        moved += z0 is None or abs(p[2] - z0) > 1e-4 or abs(hh - h_0) > 1e-5
    check(moved == 0, f"the base moved or re-masked {moved} top points")
    low = np.abs(co[:, 2] - bottom) < 1e-3
    check(np.array_equal(low, ~top), f"base points should all sit flat at lowest - depth ({bottom:.2f} m)")
    half = np.abs(co[top, :2]).max(0) + 1e-3  # the top's own footprint (it can sit a hair past Size / 2)
    check((np.abs(co[:, :2]) <= half).all(), "the base reaches past the landscape edge")
    side = cap = 0
    for (vs, nrm, mid), on in zip(faces, flag):
        check(on == bool(low[vs].any()), "lg_base should be on the sides and bottom only")
        if not on:
            continue
        if low[vs].all():
            cap += 1
            check(nrm[2] < -0.99, "the bottom should face down")
        else:
            side += 1
            check(abs(nrm[2]) < 1e-3 and nrm[0] * mid[0] + nrm[1] * mid[1] > 0, "sides should be vertical and face out")
    check(side > 0 and cap > 0, "no sides or no bottom")
    # Water + Base: the sheet stays inside the slab's footprint.
    ob.lg.water, ob.lg.water_level = True, 0.4
    cw, _f, wet, _h, ef_w, _fc = look()
    check(wet.sum() == 4 and min(ef_w) == 2, "water on should add its sheet and keep the slab watertight")
    land = cw[~wet]
    check((np.abs(cw[wet][:, :2]).max(axis=0) <= np.abs(land[:, :2]).max(axis=0) + 1e-3).all(), "water hangs past the slab edge")
    # Bake to Mesh keeps the base: lg_base and watertight once the water is split off.
    with bpy.context.temp_override(active_object=ob, object=ob):
        check(bpy.ops.landscape.bake(save_preset=False) == {'FINISHED'}, "Bake did not finish")
    check("lg_base" in ob.data.attributes, "bake lost lg_base")
    _c, bflag, _w, _h, ef_b, _fb = read(ob.data)
    check(bflag.any() and min(ef_b) == 2 and max(ef_b) == 2, "baked slab is not watertight")
    fresh_scene()
    ob = add("mountains")
    lg.sync_object(ob)
    check(len(look()[5]) == len(faces0), "a new landscape with Base off should have the same faces as before")
    return f"off: {len(faces0)} faces, open border; on: {side} side + {cap} bottom faces, watertight, flat at {bottom:.2f} m, top and masks untouched; water inside; bake keeps it"


print("\n=== KitBash Landscape Generator tests ===")
for tid, name, ok, detail in RESULTS:
    print(f"{'PASS' if ok else 'FAIL'}  {tid:4} {name}: {detail}")
failed = [r for r in RESULTS if not r[2]]
print(f"{len(RESULTS) - len(failed)}/{len(RESULTS)} passed")
sys.exit(1 if failed else 0)

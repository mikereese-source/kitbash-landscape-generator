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
    ob.lg.base = False  # same for the base (on by default since 2026-11-11): its side and bottom points aren't on the grid
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


MASKS = ("lg_height", "lg_slope", "lg_curvature", "lg_flow", "lg_wear", "lg_deposit", "lg_talus", "lg_depth")


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


@test("T9", "Masks exist and are 0-1; wear and deposit vary")
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
            mid = np.zeros(len(m["lg_wear"]), bool)
            for n in ("lg_wear", "lg_deposit"):  # the masks measured the uplift: deposit 1 on 89% of Mountains (LG-075)
                full = float((m[n] > 0.99).mean())
                check(full < 0.2, f"{key}: {n} at 1 on {full:.0%} of the surface, want under 20%")
                mid |= (m[n] > 0.1) & (m[n] < 0.9)
            check(mid.mean() > 0.1, f"{key}: wear or deposit in 0.1-0.9 on {mid.mean():.0%} of the surface, want over 10%")
            check(m["lg_talus"].min() >= 0.0, f"{key}: lg_talus under 0 ({m['lg_talus'].min():.4f}): the cubic read undershoots unless clamped")
            if rec["erosion"].get("scree"):  # rockfall debris marked where it came to rest (LG-080)
                check(m["lg_talus"].max() > 0.99, f"{key}: lg_talus never reaches 1 ({m['lg_talus'].max():.2f}): no talus")
        if not (rec.get("erosion") or {}).get("scree"):
            check(m["lg_talus"].max() == 0.0, f"{key}: lg_talus should be 0 without rockfall, up to {m['lg_talus'].max():.2f}")
    fresh_scene()
    ob = add("mountains")
    m = masks_of(ob)
    wet = m["lg_flow"] > 0.6
    check(m["lg_curvature"][wet].mean() > m["lg_curvature"].mean(), "flow should run in hollows (high curvature)")
    fresh_scene()
    ob = add("mesa")
    check((masks_of(ob)["lg_slope"] > 0.6).mean() > 0.01, "Mesa cliffs should be steep in the slope mask")
    return f"{len(MASKS)} masks on all {len(lg.TYPES)} types, in 0-1; flow in hollows; {eroded} eroded types have flow and wear/deposit"


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
    check(open2 > 0 and bad2 == 0 and len(cave2) > 50, f"cave lost on a bigger landscape: {len(cave2)} cave points (want over 50), {bad2} non-manifold edges (want 0), {open2} open edges")
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


@test("T11", "Erosion carves Mountains steeper as it rises")
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
    # D211 (Mike, LG-076): incision 1.8 cuts V valleys and steep walls, so the steepest slopes rise with erosion (they fell at 0.5).
    check(out[0] < out[1] <= out[2] + 0.5, f"steepest slopes should rise as erosion carves: {[round(v, 1) for v in out]}")
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
    check(ob.lg.bl_rna.properties["base"].default, "Base should be on by default (Mike, 2026-11-11)")
    co0, flag0, _w, h0, ef0, faces0 = look()
    check(not flag0.any() and min(ef0) == 1, "Base off should leave the open landscape sheet")
    top0 = {}
    for p, hh in zip(co0, h0):  # a list per position: the breakup can stack two points within 1 mm on a sheer wall (LG-079 Log)
        top0.setdefault(key(p), []).append((p[2], hh))
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
        cand = top0.get(key(p), [])
        hit = next((i for i, (z0, h_0) in enumerate(cand) if abs(p[2] - z0) <= 1e-4 and abs(hh - h_0) <= 1e-5), None)
        moved += hit is None
        if hit is not None:
            cand.pop(hit)  # each stacked point matches once, so one moving onto its neighbour still counts (LG-079 code review)
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


def heap_rocks(ob):
    """The cave's loose rocks, each measured against the shell and the other rocks (LG-061): its kit size, its
    width, how upright it stands, the gap under its middle (straight down from its underside to whatever is
    below; under 0 it sits in it), how much of it is inside a bigger rock (share of its points) and how far its
    middle is over the cave's floor."""
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    from mathutils.kdtree import KDTree
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    verts = [v.co.copy() for v in me.vertices]
    faces = [tuple(p.vertices) for p in me.polygons]
    ev.to_mesh_clear()
    owner = [-1] * len(faces)  # which rock each face of the one big tree belongs to (-1 the shell)
    shell = BVHTree.FromPolygons(verts, faces)
    found = [(i.object.name, i.matrix_world.copy()) for i in dg.object_instances
             if i.is_instance and i.parent and i.parent.original == ob and "KB Rock" in i.object.name]
    local, rocks = {}, []
    for k, (name, m) in enumerate(found):
        if name not in local:
            src = bpy.data.objects[name].data
            lv = [v.co.copy() for v in src.vertices]
            local[name] = (lv, [tuple(p.vertices) for p in src.polygons],
                           Vector([min(v[a] for v in lv) for a in range(3)]), Vector([max(v[a] for v in lv) for a in range(3)]))
        lv, lf, lo, hi = local[name]
        wv = [m @ v for v in lv]
        scale = m.to_scale()
        base = len(verts)
        verts.extend(wv)
        faces.extend(tuple(base + i for i in f) for f in lf)
        owner.extend([k] * len(lf))
        rocks.append(dict(name=name, size=next(s for s in ("Big", "Medium", "Small") if f" {s} " in name), at=m.translation.copy(),
                          mid=m @ ((lo + hi) * 0.5), across=max(hi.x - lo.x, hi.y - lo.y) * scale.x, tall=(hi.z - lo.z) * scale.z,
                          up=(m.to_3x3() @ Vector((0, 0, 1))).normalized().z, verts=wv, tree=BVHTree.FromPolygons(wv, lf)))
    tree = BVHTree.FromPolygons(verts, faces)
    down = Vector((0, 0, -1))
    def beyond(k, start, way):
        """The first face that is not rock k's own, from `start` along `way`: (distance, its rock or -1, its normal)."""
        o, gone = start.copy(), 0.0
        for _ in range(12):
            hit = tree.ray_cast(o, way)
            if hit[0] is None:
                return None
            gone += hit[3]
            if owner[hit[2]] != k:
                return gone, owner[hit[2]], hit[1]
            o = hit[0] + way * 1e-4
            gone += 1e-4
        return None
    for k, r in enumerate(rocks):
        under = r["tree"].ray_cast(r["mid"], down)  # its own underside, straight below its middle
        r["over"] = shell.ray_cast(r["mid"], down)[3] or 0.0
        below, above = beyond(k, r["mid"], down), beyond(k, r["mid"], -down)
        # Its middle under the floor (the floor seen from below looks down) or inside another rock (leaving it by
        # its top): set in, not floating.
        if above is not None and ((above[1] == -1 and above[2].z < 0.0) or (above[1] >= 0 and above[2].z > 0.0)):
            r["gap"] = -above[0]
        else:
            r["gap"] = None if below is None or under[0] is None else below[0] - under[3]
    kd = KDTree(max(len(rocks), 1))
    for k, r in enumerate(rocks):
        kd.insert(r["mid"], k)
    kd.balance()
    widest = max((r["across"] for r in rocks), default=0.0)
    for k, r in enumerate(rocks):
        r["inside"] = 0.0
        for _co, j, dist in kd.find_range(r["mid"], (r["across"] + widest) * 0.75):
            o = rocks[j]
            if j == k or o["across"] < r["across"] or dist > (r["across"] + o["across"]) * 0.75:
                continue  # the smaller rock of a pair carries the overlap
            n_in = 0
            for v in r["verts"]:
                loc, nor, _i, _d = o["tree"].find_nearest(v)
                n_in += (v - loc).dot(nor) < 0.0
            r["inside"] = max(r["inside"], n_in / len(r["verts"]))
    return rocks


@test("T35", "Jointed heaps: a layered drop, no rock floats or sits deep in another, Spread sets the footprint")
def _t35():
    # LG-061 (D204, docs/RESEARCH-rubble.md): the jointed heaps are dropped in layers, big then medium then small,
    # each rock onto the floor or the rocks below. No rock floats (a gap under its middle), none sits deep inside
    # a bigger one (over half its points), none leans steeply; sizes run about 10x across, very many small and
    # few big, all three kit sizes used; Spread sets the piles' footprint; the same rocks at Preview and High.
    # A pile is wider than tall, not a cairn: no rock lands higher than a 22 degree cone over the pile's footprint
    # (0.4 of its radius, which is at most 0.8 x 1.35 of the entrance's half width), and the big blocks lie on the
    # floor. Spread moves the rocks together or apart and keeps their number (low Spread used to lose rocks).
    fresh_scene()
    bpy.ops.landscape.add_cave()
    ob = bpy.context.view_layer.objects.active
    c = ob.lg_cave
    c.rock, c.rubble = 'JOINTED', 1.0
    c.width, c.height, c.depth, c.chamber, c.ceiling, c.chamber_drop = 24.0, 14.0, 60.0, 50.0, 24.0, 10.0

    def look(level):
        rocks = heap_rocks(ob)
        check(len(rocks) > 60, f"{level}: a jointed cave at Rubble 1 should have rock piles: {len(rocks)} rocks")
        floats = [r for r in rocks if r["gap"] is None or r["gap"] > 0.02 + 0.05 * r["tall"]]
        check(not floats, f"{level}: {len(floats)} of {len(rocks)} rocks float, the worst {max((r['gap'] or 99.0) for r in floats) if floats else 0:.2f} m over what is under it")
        deep = [r for r in rocks if r["inside"] > 0.5]
        check(not deep, f"{level}: {len(deep)} of {len(rocks)} rocks sit deep inside a bigger rock (the worst {max(r['inside'] for r in deep) if deep else 0:.0%} of it)")
        tipped = [r for r in rocks if r["up"] < 0.65]  # 40 degrees of slope at most, and the Tilt slider's own tip
        check(not tipped, f"{level}: {len(tipped)} rocks lean over 50 degrees")
        cap = 0.4 * 0.8 * 1.35 * c.width * 0.5
        high_up = [r for r in rocks if r["over"] - 0.5 * r["tall"] > cap + 0.5]
        check(not high_up, f"{level}: piles should be wider than tall, no rock more than {cap:.1f} m up: {len(high_up)} are, the highest {max((r['over'] - 0.5 * r['tall'] for r in high_up), default=0):.1f} m")
        stacked = [r for r in rocks if r["size"] == "Big" and r["over"] > r["tall"]]
        check(not stacked, f"{level}: the big blocks should lie on the floor: {len(stacked)} sit on other rocks")
        return rocks

    def area(rocks, cell=3.0):  # floor covered: grid cells with a rock in them
        return len({(int(r["at"].x // cell), int(r["at"].y // cell)) for r in rocks}) * cell * cell
    rocks = look("Preview")
    count = {s: sum(r["size"] == s for r in rocks) for s in ("Big", "Medium", "Small")}
    check(count["Big"] >= 1 and count["Small"] > count["Medium"] > count["Big"], f"very many small, few big, every kit size used: {count}")
    wide = sorted(r["across"] for r in rocks)
    check(wide[-1] / wide[0] > 8.0, f"sizes should run about 10x across: {wide[0]:.2f} to {wide[-1]:.2f} m")
    big = np.mean([r["across"] for r in rocks if r["size"] == "Big"])
    check(big > 2.5 * np.median(wide), f"the big blocks should be really big: {big:.1f} m against a median {np.median(wide):.1f} m")
    spots = sorted((round(r["at"].x, 1), round(r["at"].y, 1)) for r in rocks)
    c.spread = 0.0
    n_tight = look("Spread 0")
    c.spread = 1.0
    n_strewn = look("Spread 1")
    tight, strewn = area(n_tight), area(n_strewn)
    check(strewn > tight * 1.4, f"Spread should set the piles' footprint: {tight:.0f} m2 at 0, {strewn:.0f} m2 at 1")
    check(all(abs(len(n) - len(rocks)) < 0.25 * len(rocks) for n in (n_tight, n_strewn)),
          f"Spread should keep the number of rocks: {len(n_tight)} at 0, {len(rocks)} at 0.5, {len(n_strewn)} at 1")
    c.spread = 0.5
    c.detail = 'HIGH'
    high = look("High")
    check(sorted((round(r["at"].x, 1), round(r["at"].y, 1)) for r in high) == spots, f"the same rocks in the same spots at every level: {len(rocks)} at Preview, {len(high)} at High")
    return (f"{len(rocks)} rocks ({count['Big']} big, {count['Medium']} medium, {count['Small']} small), {wide[0]:.2f} to {wide[-1]:.2f} m across; none floats, "
            f"none deep in another, none leaning, none over a low cone; footprint {tight:.0f} m2 at Spread 0, {strewn:.0f} m2 at 1 ({len(n_tight)} and {len(n_strewn)} rocks); the same at Preview and High")


def piece_chunks(ob):
    """The jointed pieces as they show (LG-064): each connected patch of piece faces standing in the open, as
    (its area, the air under its foot down to the cave's rock, its lowest point, how near the mouth it comes). A piece's buried faces (behind
    the shell, whose normals point into the rock) don't count. The foot is its lowest quarter
    (a piece standing at the brink of a drop has its lowest point over the drop), and the air under each is
    measured 3 m out from the rock nearest it: straight under a piece that runs into the wall there is only wall."""
    import bmesh
    from mathutils.bvhtree import BVHTree
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    ev = ob.evaluated_get(dg)
    bm = bmesh.new()
    bm.from_mesh(ev.to_mesh())
    ev.to_mesh_clear()
    lp = bm.verts.layers.bool.get("lg_piece")
    check(lp is not None, "the cave should mark its jointed pieces (lg_piece)")
    bm.faces.ensure_lookup_table()
    tree = BVHTree.FromPolygons([v.co.copy() for v in bm.verts], [[v.index for v in f.verts] for f in bm.faces if not f.verts[0][lp]])

    def in_open(v):
        loc, nrm, _i, _d = tree.find_nearest(v.co)
        return (v.co - loc).dot(nrm) <= 0.0

    free = {v.index: in_open(v) for v in bm.verts if v[lp]}
    shown = {f.index for f in bm.faces if f.verts[0][lp] and any(free[v.index] for v in f.verts)}
    seen, chunks = set(), []
    for start in shown:
        if start in seen:
            continue
        seen.add(start)
        todo, group = [start], []
        while todo:
            f = bm.faces[todo.pop()]
            group.append(f)
            for e in f.edges:
                for g in e.link_faces:
                    if g.index in shown and g.index not in seen:
                        seen.add(g.index)
                        todo.append(g.index)
        pts = [v.co for v in {v for f in group for v in f.verts} if free[v.index]]
        low = min(pts, key=lambda p: p.z)
        air = float("inf")
        top = max(q.z for q in pts)
        for q in [q for q in pts if q.z <= low.z + 0.25 * (top - low.z)]:  # every foot point: a capped sample hung on vertex order
            hit = tree.ray_cast(q - tree.find_nearest(q)[1] * 3.0, (0.0, 0.0, -1.0))
            if hit[0] is not None:
                air = min(air, max(q.z - hit[0].z, 0.0))
        chunks.append((sum(f.calc_area() for f in group), air, low.copy(), min(q.y for q in pts)))
    bm.free()
    return chunks


@test("T37", "Jointed pieces: every one stands on rock, none hangs; the passage has its pieces")
def _t37():
    fresh_scene()
    check(bpy.ops.landscape.add_cave() == {'FINISHED'}, "Add Cave did not finish")
    ob = bpy.context.view_layer.objects.active
    c = ob.lg_cave
    c.rock = 'JOINTED'
    # Mike's review cave (D205): a short passage into a big sunk chamber. Its pieces showed as masses hanging on the
    # chamber's walls and over the opening, and none came nearer the mouth than 42 m.
    for k, v in dict(width=60.0, height=40.0, depth=100.0, chamber=120.0, ceiling=60.0, chamber_drop=60.0, roughness=1.0, wall_shape=0.8).items():
        setattr(c, k, v)
    chunks = piece_chunks(ob)
    check(len(chunks) > 0, "jointed rock should show its pieces")
    # Standing: no more air under its foot than 15% of the entrance height (a Preview voxel is 12%). Specks smaller
    # than 2% of the entrance's face (a boulder) are not masses.
    gap, speck = 0.15 * c.height, 0.02 * c.width * c.height
    hung = sorted((ch for ch in chunks if ch[0] > speck and ch[1] > gap), key=lambda ch: -ch[0])
    check(not hung, f"no jointed piece should hang: {len(hung)} of {len(chunks)} stop short of the floor, {sum(ch[0] for ch in hung):.0f} m2; the biggest "
                    f"{hung[0][0]:.0f} m2 with {hung[0][1]:.0f} m of air under it at {tuple(round(x) for x in hung[0][2])}" if hung else "")
    front = min(ch[3] for ch in chunks if ch[0] > speck)
    check(front < 0.5 * c.width, f"the passage should have its pieces: the nearest stands {front:.0f} m in from the mouth, want under {0.5 * c.width:.0f} m")
    specks = [ch for ch in chunks if ch[0] <= speck and ch[1] > gap]
    # The same rule on the default Jointed cave, on a bent one (pieces placed by distance along the path, not by Y),
    # and on the review cave at High (code review of LG-064).
    others = []
    for label, sets, detail in (("default", {}, "PREVIEW"), ("bent", dict(wiggle=1.0, turn=0.6, depth=120.0), "PREVIEW"), ("review cave at High", {}, "HIGH")):
        if label != "review cave at High":
            fresh_scene()
            check(bpy.ops.landscape.add_cave() == {'FINISHED'}, "Add Cave did not finish")
            ob = bpy.context.view_layer.objects.active
            c = ob.lg_cave
            c.rock = 'JOINTED'
            for k, v in sets.items():
                setattr(c, k, v)
        c.detail = detail
        ch2 = piece_chunks(ob)
        g2, s2 = 0.15 * c.height, 0.02 * c.width * c.height
        h2 = [ch for ch in ch2 if ch[0] > s2 and ch[1] > g2]
        check(not h2, f"{label}: no jointed piece should hang, {len(h2)} of {len(ch2)} stop short of the floor, the biggest {max((ch[0] for ch in h2), default=0):.0f} m2")
        others.append(f"{label} {len(ch2)} pieces")
    return (f"{len(chunks) - len(specks)} pieces show, {sum(ch[0] for ch in chunks):.0f} m2, each standing on rock (at most {gap:.0f} m of air under a foot); "
            f"the nearest {front:.0f} m in from the mouth; {len(specks)} specks under {speck:.0f} m2 ({sum(ch[0] for ch in specks):.0f} m2) stop short; none hang on: {', '.join(others)}")


@test("T41", "Landscape face counts per Detail Level match the built mesh")
def _t41():
    # LG-085 (Mike): the panel shows each level's faces before switching, as caves do (LG-055). Within 2% of the mesh.
    # Ultra (17M points) is the same formula and too heavy to build here; a cave cut in adds about 0.4% (code review).
    fresh_scene()
    ob = add("hills")
    out = []
    for base, water, final, wide, cave in ((False, False, False, False, False), (True, True, False, True, False), (True, False, False, False, True), (True, False, True, False, False)):
        ob.lg.base, ob.lg.water, ob.lg.final = base, water, final
        ob.lg.size_x, ob.lg.size_y = (300.0, 150.0) if wide else (200.0, 200.0)
        ob.lg.cave_layout = 'ENTRANCE' if cave else 'NONE'
        lg.sync_object(ob)
        counts = lg.landscape_counts(ob.lg, lg.landscape_modifier(ob))
        dg = bpy.context.evaluated_depsgraph_get()
        dg.update()
        ev = ob.evaluated_get(dg)
        me = ev.to_mesh()
        real = len(me.polygons)
        ev.to_mesh_clear()
        est = counts[1 if final else 0][2]
        check(abs(est - real) <= 0.02 * real, f"base {base}, water {water}, 300x150 {wide}, cave {cave}, {'High' if final else 'Preview'}: panel says {est:,} faces, the mesh has {real:,}; want within 2%")
        out.append(f"{est:,} vs {real:,}")
    return "; ".join(out)

@test("T42", "Preview and High erode alike")
def _t42():
    # LG-078 (Mike: match exactly): both levels erode on the 512 grid; Preview on its own 256 had 14.6% against 17.5%.
    fresh_scene()
    ob = add("mountains")
    ob.lg.size_x = ob.lg.size_y = 2000.0
    share, cells = [], 1
    kept = lg.TYPES["mountains"]["breakup"]
    lg.TYPES["mountains"]["breakup"] = 0.0  # erosion only: the breakup shows fewer block sizes at Preview on purpose (LG-077)
    kept_crest = lg.TYPES["mountains"]["crest"]
    lg.TYPES["mountains"]["crest"] = 0.0  # nor the crest lift: it comes after erosion too (LG-086)
    try:
        for final in (False, True):
            ob.lg.final = final
            lg.sync_object(ob)
            p = evaluated_points(ob)
            n = int(round(np.sqrt(len(p))))
            ix, iy = (np.rint((p[:, k] - p[:, k].min()) / np.ptp(p[:, k]) * (n - 1)).astype(int) for k in (0, 1))
            z = np.zeros((n, n))
            z[iy, ix] = p[:, 2]  # binned by position, not point order
            if final:
                k = (n - 1) // cells  # High read on Preview's spacing
                z = z[::k, ::k]
            cells = n - 1
            gy, gx = np.gradient(z, 2000.0 / (z.shape[0] - 1))
            share.append(100.0 * float((np.degrees(np.arctan(np.hypot(gx, gy))) > 60).mean()))
    finally:
        lg.TYPES["mountains"]["breakup"] = kept
        lg.TYPES["mountains"]["crest"] = kept_crest
    check(abs(share[0] - share[1]) <= 1.0, f"over 60 deg: Preview {share[0]:.1f}%, High {share[1]:.1f}%; want within 1 point")
    return f"over 60 deg: Preview {share[0]:.1f}%, High {share[1]:.1f}%"

@test("T43", "Bedrock breakup: steep rock breaks into blocks, scree-angle ground stays smooth")
def _t43():
    # LG-077 (review S4): blocks and ledges on Mountains steeper than 40 to 52 deg; gentler ground left alone, no points added.
    fresh_scene()
    ob = add("mountains")
    set_size(ob, 2000.0)
    kept = lg.TYPES["mountains"]["breakup"]
    check(kept > 0, "Mountains should ship with Breakup on")
    try:
        on = evaluated_points(ob)
        lg.TYPES["mountains"]["breakup"] = 0.0
        lg.sync_object(ob)
        off = evaluated_points(ob)
    finally:
        lg.TYPES["mountains"]["breakup"] = kept
    check(len(on) == len(off), f"breakup must not add points: {len(off):,} without, {len(on):,} with")
    # Slope from the unbroken grid, binned by position; on and off are one mesh before and after a per-point push (no join or merge), so index i is the same point.
    n = int(round(math.sqrt(len(off))))
    ix, iy = (np.rint((off[:, k] - off[:, k].min()) / np.ptp(off[:, k]) * (n - 1)).astype(int) for k in (0, 1))
    check(len(set(zip(ix.tolist(), iy.tolist()))) == len(off), "Mountains without breakup should be one point per grid cell")
    grid = np.zeros((n, n))
    grid[iy, ix] = off[:, 2]
    gy, gx = np.gradient(grid, 2000.0 / (n - 1))
    deg = np.degrees(np.arctan(np.hypot(gx, gy)))[iy, ix]
    gentle, steep = deg < 30.0, deg > 50.0
    check(gentle.mean() > 0.05 and steep.mean() > 0.02, f"need both kinds of ground: {gentle.mean():.0%} under 30 deg, {steep.mean():.0%} over 50 deg")
    # Height is stretched back to the exact relief after the breakup, so take that stretch out before comparing.
    a, c = np.polyfit(off[gentle, 2], on[gentle, 2], 1)
    moved = np.linalg.norm(on - np.c_[off[:, :2], a * off[:, 2] + c], axis=1)
    calm, broken = float(np.percentile(moved[gentle], 95)), float(np.sqrt((moved[steep] ** 2).mean()))
    check(calm < 0.5, f"ground under 30 deg should stay as it was: 95% of it moved up to {calm:.2f} m (limit 0.5 m)")
    check(broken > 1.5, f"rock over 50 deg should break into blocks meters deep: it moved {broken:.2f} m rms (want over 1.5 m)")
    return f"2 km Mountains, Preview: rock over 50 deg moved {broken:.1f} m rms, ground under 30 deg {calm:.2f} m; {len(on):,} points both ways"

@test("T44", "Crest sharpen: round tops rise to points with no teeth, other ground stays, Preview and High alike")
def _t44():
    # LG-086 (Mike: sharp mountain tops, no small spikes along ridges): the lift alone, breakup off (a later stage).
    fresh_scene()
    ob = add("mountains")
    set_size(ob, 2000.0)
    kept = {k: lg.TYPES["mountains"][k] for k in ("breakup", "rock", "crest")}
    check(kept["crest"] > 0, "Mountains should ship with Crest on")
    lift, counts = [], []
    try:
        lg.TYPES["mountains"].update(breakup=0.0, rock=0.0)  # grain and breakup come after the lift
        for final in (False, True):
            ob.lg.final = final
            grids = []
            for crest in (0.0, kept["crest"]):
                lg.TYPES["mountains"]["crest"] = crest
                lg.sync_object(ob)
                p = evaluated_points(ob)
                counts.append(len(p))
                n = int(round(math.sqrt(len(p))))
                ix, iy = (np.rint((p[:, k] - p[:, k].min()) / np.ptp(p[:, k]) * (n - 1)).astype(int) for k in (0, 1))
                z = np.zeros((n, n))
                z[iy, ix] = p[:, 2]  # binned by position, not point order
                grids.append(z)
            off, on = grids
            # The lifted tops take their room above the lift's height ramp, so no line fit: one hid a 3% squeeze (LG-086 cp2).
            low = off < off.min() + np.ptp(off) * (lg.nodes.CR_HIGH[0] - 0.05)
            lift.append((on - off, low, 2000.0 / (n - 1), off > off.min() + np.ptp(off) * lg.nodes.CR_HIGH[0]))
    finally:
        lg.TYPES["mountains"].update(kept)
    check(counts[0] == counts[1] and counts[2] == counts[3], f"the lift must not add points: {counts}")
    (pv, low, step, above), (hi, _, _, _) = lift
    k = (hi.shape[0] - 1) // (pv.shape[0] - 1)
    calm, top, share = float(np.percentile(np.abs(pv[low]), 99)), float(pv.max()), float((pv > 1.0).mean())
    check(calm < 0.3, f"the ground below the lift's height ramp should stay exactly as it was, unsqueezed: 99% of it moved up to {calm:.2f} m (limit 0.3 m)")
    check(top > 15.0 and 0.03 < share < 0.3, f"round tops should rise by tens of meters on a small share of the ground: highest lift {top:.1f} m, {share:.0%} lifted over 1 m")
    # The lift never digs; the restretch eases only the ground above the lift's height ramp down to make room (LG-086 cp2a).
    dug = pv < -0.5
    check(not (dug & ~above).any(), f"only ground above the lift's height ramp may come down: {int((dug & ~above).sum())} points below it dropped over 0.5 m")
    check(-float(pv.min()) <= top, f"the top should come down no further than the highest lift goes up: lowest {pv.min():.2f} m, highest lift {top:.1f} m")
    # Teeth and walls come from a lift that falls away much faster than its 50 deg tent, tan 1.2 (LG-086 Log: the old scratch reached 6.7).
    gy, gx = np.gradient(pv, step)
    fall = float(np.hypot(gx, gy).max())
    check(fall < 4.5, f"the lift should fall away little faster than its tent sides (1.2): steepest {fall:.2f} m per m (limit 4.5)")
    gap = float(np.percentile(np.abs(hi[::k, ::k] - pv), 99))
    check(gap < 1.0, f"Preview and High should lift alike: 99% within {gap:.2f} m (limit 1.0 m)")
    return f"2 km Mountains: highest lift {top:.1f} m, {share:.0%} of the ground over 1 m, lift slope {fall:.2f}, lower 40% moved {calm:.2f} m, top eased down up to {-pv.min():.1f} m, Preview against High {gap:.2f} m"

def face_share(z, step, D=5.0, k=3, deg=5.0, margin=5.0, steep=45.0, edge=40):
    """LG-089: share of ground over 45 deg on flat faces: normals within 5 deg rms over D, and a face, not a pillow
    (the window k times as wide spreads more than k times as much plus 5 deg; a soft surface spreads in proportion)."""
    gy, gx = np.gradient(z, step)
    ln = np.sqrt(gx * gx + gy * gy + 1.0)
    nrm = (-gx / ln, -gy / ln, 1.0 / ln)
    def spread(w):
        cs = [np.pad(a, ((w // 2 + 1, w // 2), (w // 2 + 1, w // 2))).cumsum(0).cumsum(1) for a in nrm]
        mean = [(c[w:, w:] - c[:-w, w:] - c[w:, :-w] + c[:-w, :-w]) / (w * w) for c in cs]
        return np.degrees(np.sqrt(np.maximum(2.0 * (1.0 - np.sqrt(mean[0] ** 2 + mean[1] ** 2 + mean[2] ** 2)), 0.0)))
    w = max(3, int(round(D / step)) | 1)
    sp, wide = spread(w), spread((w * k) | 1)
    on = nrm[2] < math.cos(math.radians(steep))
    on[:edge] = on[-edge:] = False
    on[:, :edge] = on[:, -edge:] = False
    return 100.0 * float(((sp < deg) & (wide > k * sp + margin))[on].mean())


def t45_facets(n=400, cell=15.0, seed=0):
    """A 55 deg slope cut into planar facets: the upper envelope of tilted planes, each kept near its own site."""
    rng = np.random.default_rng(seed)
    y, x = np.mgrid[0:n, 0:n].astype(np.float64)
    h = np.full(x.shape, -1e9)
    for j in range(-1, int(n / cell) + 2):
        for i in range(-1, int(n / cell) + 2):
            cx, cy = (i + rng.random()) * cell, (j + rng.random()) * cell
            a, b = rng.uniform(-0.35, 0.35, 2)
            h = np.maximum(h, np.where((x - cx) ** 2 + (y - cy) ** 2 > (1.2 * cell) ** 2, -1e9, a * (x - cx) + b * (y - cy)))
    return h + 1.43 * x


def top_grid(ob, step=1.0):
    """The top surface on a grid of `step` m (1 m by default) by rays from above, as the board's measure (LG-087 prep.py): the breakup pushes points sideways."""
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    bvh = BVHTree.FromObject(ob, dg)
    half = ob.lg.size_x / 2.0
    n = int(ob.lg.size_x / step) + 1
    z, down = np.empty((n, n)), Vector((0.0, 0.0, -1.0))
    for j in range(n):
        y = min(max(j * step - half, 0.01 - half), half - 0.01)
        for i in range(n):
            x = min(max(i * step - half, 0.01 - half), half - 0.01)
            hit = bvh.ray_cast(Vector((x, y, 5000.0)), down)[0] or bvh.find_nearest(Vector((x, y, 0.0)))[0]
            z[j, i] = hit.z
    return z, step

@test("T45", "Flat faces: steep rock blocks take their own plane; a soft surface does not count as flat")
def _t45():
    # LG-089 (c197: the granite scan is flat planes meeting at hard steps): the Done-when measure itself, the two-window face share.
    y, x = np.mgrid[0:400, 0:400].astype(np.float64)
    plane, dome, facets = (face_share(h, 1.0) for h in (1.5 * x + 0.2 * y, 1.5 * x - ((x - 200) ** 2 + (y - 200) ** 2) / 2000.0, t45_facets()))
    check(plane == 0.0 and dome < 2.0 and facets > 15.0, f"the measure: a lone plane {plane:.1f}% and a soft dome {dome:.1f}% should not count (0, under 2%), planar facets {facets:.1f}% should (over 15%)")
    fresh_scene()
    ob = add("mountains")
    set_size(ob, 2048.0)
    ob.lg.final = True
    kept = lg.TYPES["mountains"]["breakup"]
    check(kept > 0, "Mountains should ship with Breakup on")
    share = []
    try:
        for b in (0.0, kept):
            lg.TYPES["mountains"]["breakup"] = b
            lg.sync_object(ob)
            share.append(face_share(*top_grid(ob)))
    finally:
        lg.TYPES["mountains"]["breakup"] = kept
    check(share[0] < 4.0, f"the soft surface (breakup off) should not count as flat faces: {share[0]:.1f}% (limit 4%)")
    check(share[1] > max(2.5, share[0]), f"steep rock should carry flat faces bounded by creases, more than the soft surface: {share[1]:.1f}% of ground over 45 deg (want over 2.5% and over {share[0]:.1f}%; main before LG-089 0.8%, granite scan 8.6%)")
    return f"2 km Mountains, High: flat faces {share[1]:.1f}% with the breakup, {share[0]:.1f}% without; measure self-check plane {plane:.1f}%, dome {dome:.1f}%, facets {facets:.1f}%"

def t46_teeth(h, edge=40):
    """LG-086's counter (lib86.py): a spike stands 3 m or more above every 24 m line through it (8 directions), one per 24 m;
    a tooth ends on its ridge (under twice that height above 80 m lines), a horn keeps widening downward (a summit)."""
    def shift(a, dy, dx, fill):
        out = np.full_like(a, fill)
        H, W = a.shape
        ys, yd = (slice(dy, H), slice(0, H - dy)) if dy >= 0 else (slice(0, H + dy), slice(-dy, H))
        xs, xd = (slice(dx, W), slice(0, W - dx)) if dx >= 0 else (slice(0, W + dx), slice(-dx, W))
        out[yd, xd] = a[ys, xs]
        return out

    def line_open(half):  # ridges survive (long one way), spikes don't
        best = np.full_like(h, -1e9)
        for dx, dy in ((1, 0), (0, 1), (1, 1), (1, -1), (2, 1), (1, 2), (2, -1), (1, -2)):
            k = max(1, int(round(half / math.hypot(dx, dy))))
            ero = h.copy()
            for i in range(1, k + 1):
                ero = np.minimum(ero, np.minimum(shift(h, dy * i, dx * i, 1e9), shift(h, -dy * i, -dx * i, 1e9)))
            dil = ero.copy()
            for i in range(1, k + 1):
                dil = np.maximum(dil, np.maximum(shift(ero, dy * i, dx * i, -1e9), shift(ero, -dy * i, -dx * i, -1e9)))
            best = np.maximum(best, dil)
        return best
    th = h - line_open(12.0)
    th[:edge] = th[-edge:] = 0
    th[:, :edge] = th[:, -edge:] = 0
    mx = th.copy()
    for ax in (0, 1):
        m2 = mx.copy()
        for i in range(1, 13):
            m2 = np.maximum(m2, np.maximum(np.roll(mx, i, ax), np.roll(mx, -i, ax)))
        mx = m2
    ys, xs = np.nonzero((th >= mx) & (th >= 3.0))
    keep, seen = [], np.zeros(h.shape, bool)
    for y, x in sorted(zip(ys, xs), key=lambda q: -th[q]):
        if not seen[y, x]:
            keep.append((y, x))
            seen[max(0, y - 12):y + 13, max(0, x - 12):x + 13] = True
    big = h - line_open(40.0)
    teeth = [(y, x) for y, x in keep if big[y, x] < 2.0 * th[y, x]]
    return len(teeth), len(keep) - len(teeth), teeth

def crest_grids(kind):
    """T46, T48: the finished 2 km High top grid, breakup on, with Crest off and at the type's own (LG-086 Done when)."""
    fresh_scene()
    ob = add(kind)
    set_size(ob, 2048.0)
    ob.lg.final = True
    t = lg.TYPES[kind]
    kept = t.get("crest", 0.0)
    check(kept > 0 and t.get("breakup", 0.0) > 0 and t["recipe"] in lg.nodes.CR_RECIPES, f"{kind} should ship with Crest and Breakup on and its recipe in nodes.CR_RECIPES")
    grids = []
    try:
        for c in (0.0, kept):
            t["crest"] = c
            lg.sync_object(ob)
            grids.append(top_grid(ob)[0])
    finally:
        t["crest"] = kept
    return grids

@test("T46", "Crest sharpen with the breakup on: summits become horns, no more added ridge teeth than accepted")
def _t46():
    # LG-086 (Done when: no small spikes along ridges), the Done-when measure on the finished High mesh, not a stand-in (LG-086 cp2 Log).
    (t0, h0, _), (t1, h1, _) = (t46_teeth(g) for g in crest_grids("mountains"))
    check(t1 - t0 <= 11, f"the crest sharpen should add no more ridge teeth than Mike accepted (24 -> 35, +11; checkpoint 1 added 23, LG-086 Log): {t0} without it, {t1} with")
    check(h1 >= h0 + 9, f"round summits should become horns, as Mike accepted at Crest 0.5 on the hard-rock map (8 -> 17, +9; LG-079 Log): {h0} without the crest sharpen, {h1} with (want 9 more)")
    return f"2 km Mountains, High, breakup on: teeth / horns {t0} / {h0} without the crest sharpen, {t1} / {h1} with"

@test("T47", "Bedrock breakup on Glacial, Canyon, Mesa and Cliffs: steep rock breaks up, scree-angle ground stays")
def _t47():
    # LG-077 cp2 (Done when: the other rocky types), T43's measure on each type by position: rays on the Preview's 4 m grid, breakup on and off.
    out = []
    for kind in ("glacial", "canyon", "mesa", "cliffs"):
        t = lg.TYPES[kind]
        kept = t.get("breakup", 0.0)
        check(kept > 0 and t["recipe"] in lg.nodes.BK_RECIPES, f"{kind} should ship with Breakup on and its recipe in nodes.BK_RECIPES")
        fresh_scene()
        ob = add(kind)
        set_size(ob, 2048.0)
        try:
            on = top_grid(ob, 4.0)[0]
            t["breakup"] = 0.0
            lg.sync_object(ob)
            off = top_grid(ob, 4.0)[0]
        finally:
            t["breakup"] = kept
        gy, gx = np.gradient(off, 4.0)
        deg = np.degrees(np.arctan(np.hypot(gx, gy)))
        inner = np.zeros(off.shape, bool)
        inner[10:-10, 10:-10] = True  # 40 m in: within a block of the border the breakup only moves up and down
        scree, rock = inner & (deg < 35.0), inner & (deg > 50.0)
        check(scree.mean() > 0.05 and rock.mean() > 0.005, f"{kind}: need both kinds of ground: {scree.mean():.0%} under 35 deg, {rock.mean():.1%} over 50 deg")
        a, c = np.polyfit(off[scree], on[scree], 1)  # Height is stretched back to the exact relief after the breakup
        e = np.abs(on - (a * off + c))
        calm, broken, want = float(np.percentile(e[scree], 95)), float(np.sqrt((e[rock] ** 2).mean())), 0.025 * t["block_size"]
        check(calm < 0.5, f"{kind}: ground under 35 deg (scree and flats) should stay as it was: 95% of it moved up to {calm:.2f} m (limit 0.5 m)")
        check(broken > want, f"{kind}: rock over 50 deg should break into blocks: it moved {broken:.2f} m rms (want over {want:.2f} m, T43's 1.5 m at a 60 m block)")
        out.append(f"{kind} {broken:.1f} / {calm:.2f} m")
    return "2 km, Preview, rock over 50 deg moved (rms) / ground under 35 deg (95%): " + ", ".join(out)

@test("T48", "Crest sharpen on Glacial: summits sharpen, no more ridge teeth added than accepted (by position); Crest and CR_RECIPES agree")
def _t48():
    # LG-086 cp2b (Done when: the other peaked types), T46's measure on Glacial; Volcano left off, it has no erosion map to read (LG-086 Log).
    crest = {t["recipe"] for t in lg.TYPES.values() if t.get("crest", 0.0) > 0}
    check(crest == set(lg.nodes.CR_RECIPES), f"types.json Crest and nodes.CR_RECIPES should agree: recipes {sorted(crest)} against {lg.nodes.CR_RECIPES}")
    off, on = crest_grids("glacial")
    (t0, h0, p0), (t1, h1, p1) = t46_teeth(off), t46_teeth(on)
    added = sum(1 for y, x in p1 if not any(abs(y - v) <= 12 and abs(x - u) <= 12 for v, u in p0))  # matched within 12 m, as T46's teeth window (LG-086 cp2b Log)

    def tops(h):  # upper-third crest sharpness: 1st percentile of the 1 m curvature x relief, on the top third (LG-087 measure.py)
        gy, gx = np.gradient(h)
        lap = np.gradient(gy, axis=0) + np.gradient(gx, axis=1)
        lo, hi = np.percentile(h, [1, 99])
        return float(-np.percentile(lap[h > lo + 0.67 * (hi - lo)], 1)) * (hi - lo)
    k0, k1 = tops(off), tops(on)
    check(added <= 1, f"the crest sharpen should add no more ridge teeth than measured at cp2b (+1, from the lift): {added} new by position ({t0} without it, {t1} with)")
    check(k1 > 4.0 * k0 and h1 >= h0 + 4, f"Glacial summits should sharpen as Mike accepted at cp2b (67 -> 293, 4.3 times; horns 0 -> 4): upper-third crest {k0:.0f} -> {k1:.0f} (want over 4 times), horns {h0} -> {h1} (want 4 more)")
    return f"2 km Glacial, High, breakup on: teeth / horns {t0} / {h0} -> {t1} / {h1}, {added} new by position, upper-third crest {k0:.0f} -> {k1:.0f}"

@test("T49", "Hard-rock map on Mountains: rock on steep high ground with soft beds and joints; summits sharpen, steep share not raised")
def _t49():
    # LG-079 (review S2; Done when: horns and aretes, crest sharpness measured): the Done-when measure on the finished 2 km High mesh, at the values on board c202.
    fresh_scene()
    ob = add("mountains")
    set_size(ob, 2048.0)
    ob.lg.final = True
    check(lg.TYPES["mountains"]["recipe"] in lg.nodes.HR_RECIPES, "Mountains should be in nodes.HR_RECIPES")
    lg.sync_object(ob)
    er = lg.nodes.input_socket(lg.landscape_modifier(ob), "Erosion")
    kept_er = er.value
    h, hard, _s, pad = lg._sample_shape(ob, 512)  # the engine's input, as erosion reads it
    er.value = kept_er  # _sample_shape leaves Erosion at 0 for the engine to set: put the eroded map back before measuring
    ob.update_tag()
    h, hard = h[pad:-pad, pad:-pad], hard[pad:-pad, pad:-pad]
    u = (h - h.min()) / np.ptp(h)
    gy, gx = np.gradient(h * 2048.0, 2048.0 / (h.shape[0] - 1))
    steep_high = (u > 0.55) & (np.degrees(np.arctan(np.hypot(gx, gy))) > 30.0)
    rock, low = hard[steep_high], hard[u < 0.2]
    soft = float((rock[rock > 0.05] < 0.45).mean())  # soft beds (0.25) and joints (0.35) inside the rock, by attribute
    check(0.07 < (hard > 0.5).mean() < 0.10, f"hard rock (over 0.5) should cover 8.6% of the shape as on c202 (limits 7-10%): {(hard > 0.5).mean():.1%}")
    check(rock.mean() > 0.45 and low.max() < 0.01, f"hard rock should sit on steep high ground, none on the low third: mean {rock.mean():.2f} there (c202 0.47, want over 0.45), low ground up to {low.max():.2f}")
    check(0.4 < soft < 0.6, f"soft beds and joints should break the rock up (beds about one in three, plus joints; c202 49%, limits 40-60%): {soft:.0%} of the rock under 0.45")
    z = top_grid(ob)[0]
    teeth, horns, _p = t46_teeth(z)
    gy, gx = np.gradient(z)
    lap = np.gradient(gy, axis=0) + np.gradient(gx, axis=1)
    lo, hi = np.percentile(z, [1, 99])
    tops = float(-np.percentile(lap[z > lo + 0.67 * (hi - lo)], 1)) * (hi - lo)  # upper-third crest sharpness (LG-087 measure.py)
    over60 = 100.0 * float((np.degrees(np.arctan(np.hypot(gx, gy))) > 60.0).mean())
    check(tops > 1095 and horns >= 17, f"summits should sharpen as on c202 at Crest 0.5 (upper-third crest on this full grid 1019 -> 1123 with the hard map, 1098 with the talus, LG-080, Mike approved c203; horns 17): {tops:.0f}, horns {horns} (want over 1095 and 17)")
    check(teeth <= 38, f"ridge teeth should stay at c202's 38 (main 35; the Sierra squeezed to our relief has 49; at Crest 1.0 the lift on the new crests made 74, LG-079 Log): {teeth}")
    check(over60 <= 19.8, f"steep ground should stay at c202's 19.8% over 60 deg (main 21.2%, real Sierra 11.7%): {over60:.1f}%")
    return f"2 km Mountains, High: hard over 0.5 on {(hard > 0.5).mean():.1%}, {soft:.0%} of rock soft; upper-third crest {tops:.0f}, teeth / horns {teeth} / {horns}, over 60 deg {over60:.1f}%"

T50_LIMITS = {  # LG-080 tests_t50b.log (breakup, crest and rock grain off): talus cover %, its median slope range, 30-38 deg points added,
    # over 60 deg points dropped. Measured 7.3% / 33.0 deg / +0.6 / -0.7, 3.6% / 30.3 / +0.6 / -0.4, 2.5% / 30.5 / +0.7 / -0.2; limits 0.1 point
    # under for the cover, slope +-1.5 deg (debris rests at 34 deg, scree_deg; the concave toe pulls the median down); the gain and drop
    # floors are guard floors, 0.1 point under the measured values (Cliffs' drop 0.1 against 0.2 measured).
    "mountains": (7.2, 31.5, 34.5, 0.5, 0.6),
    "mesa": (3.5, 28.8, 31.8, 0.5, 0.3),
    "cliffs": (2.4, 29.0, 32.0, 0.6, 0.1),
}


@test("T50", "Talus: rockfall debris rests at the scree angle under walls on Mountains, Mesa and Cliffs, marked by lg_talus")
def _t50():
    # LG-080 (review S6; Done when: shed stops at 33-36 deg, scree share against real): the talus stage at 2 km High, breakup, crest and
    # rock grain off (later stages; the grain moves points sideways), against the same landscape with the rockfall off, by position.
    # Mask fix B (review section 5): the rockfall runs after every fill is counted, so the talus never enters deposit's fill,
    # and in the one channel the stronger of wear and deposit takes the cell.
    er = lg.erosion
    yy, xx = np.mgrid[0:96, 0:96] / 95.0
    ramp = 0.3 * xx + 0.25 * (xx > 0.6) + 0.004 * np.sin(40 * yy)
    hard = (xx > 0.6).astype(float)
    _z0, (_f0, cut0, fill0, land0) = er.erode(ramp, {"scree": 0.0, "passes": 4}, hard, masks=True)
    _z1, (_f1, cut1, fill1, land1) = er.erode(ramp, {"scree": 0.02, "passes": 4}, hard, masks=True)
    check(land0.max() == 0.0 and land1.max() > 0.0, f"fix B: talus should land only with the rockfall on ({land0.max():.2g} off, {land1.max():.2g} on)")
    check(np.array_equal(fill0, fill1) and (cut1 >= cut0).all(), "fix B: the rockfall should add to wear (its walls) and never to deposit's fill")
    c = er.change_mask(np.array([1.0, 0.2, 0.0]), np.array([0.2, 1.0, 0.0]), 1.0)
    check(c[0] < 0.5 < c[1] and c[2] == 0.5, f"fix B: the stronger of wear and deposit should take the cell, untouched 0.5: {c}")
    out = []
    for kind, (cover_min, lo, hi, gain_min, drop_min) in T50_LIMITS.items():
        rec = lg.TYPES[kind]
        kept = {k: rec[k] for k in ("breakup", "crest", "rock") if k in rec}
        scree = rec["erosion"]["scree"]
        check(scree > 0, f"{kind} should ship with rockfall on (types.json scree)")
        res = {}
        try:
            rec.update(breakup=0.0, crest=0.0, rock=0.0)
            for on in (True, False):
                rec["erosion"]["scree"] = scree if on else 0.0
                fresh_scene()
                ob = add(kind)
                set_size(ob, 2048.0)
                ob.lg.final = True
                m = masks_of(ob)
                p = evaluated_points(ob)
                res[on] = {k: (s, t) for k, s, t in zip(map(tuple, np.rint(p[:, :2] * 4.0).astype(int).tolist()), m["lg_slope"] * 90.0, m["lg_talus"])}
        finally:
            rec["erosion"]["scree"] = scree
            for k in ("breakup", "crest", "rock"):
                rec.pop(k, None)
            rec.update(kept)
        keys = sorted(set(res[True]) & set(res[False]))
        check(len(keys) > 0.99 * len(res[True]), f"{kind}: with and without rockfall should be the same points by position ({len(keys):,} of {len(res[True]):,})")
        s_on, t_on = (np.array([res[True][k][i] for k in keys]) for i in (0, 1))
        s_off, t_off = (np.array([res[False][k][i] for k in keys]) for i in (0, 1))
        cover, rest = 100.0 * float((t_on > 0.5).mean()), float(np.median(s_on[t_on > 0.5]))
        scree_on, scree_off = (100.0 * float(((s >= 30.0) & (s < 38.0)).mean()) for s in (s_on, s_off))
        o60_on, o60_off = (100.0 * float((s > 60.0).mean()) for s in (s_on, s_off))
        check(t_off.max() == 0.0, f"{kind}: lg_talus should be 0 with the rockfall off, up to {t_off.max():.2f}")
        check(cover >= cover_min, f"{kind}: talus (lg_talus over 0.5) should cover {cover_min}% as on c203: {cover:.1f}%")
        check(lo <= rest <= hi, f"{kind}: talus should rest at the scree angle (c203 median {lo}-{hi} deg): {rest:.1f} deg")
        check(scree_on - scree_off >= gain_min, f"{kind}: ground at 30-38 deg should grow by {gain_min} points as on c203: {scree_off:.1f} -> {scree_on:.1f}%")
        check(o60_off - o60_on >= drop_min, f"{kind}: ground over 60 deg should drop by {drop_min} points as on c203: {o60_off:.1f} -> {o60_on:.1f}%")
        out.append(f"{kind} talus {cover:.1f}% at {rest:.1f} deg, 30-38 deg {scree_off:.1f} -> {scree_on:.1f}%, over 60 {o60_off:.1f} -> {o60_on:.1f}%")
    return "; ".join(out)

print("\n=== KitBash Landscape Generator tests ===")
for tid, name, ok, detail in RESULTS:
    print(f"{'PASS' if ok else 'FAIL'}  {tid:4} {name}: {detail}")
failed = [r for r in RESULTS if not r[2]]
print(f"{len(RESULTS) - len(failed)}/{len(RESULTS)} passed")
sys.exit(1 if failed else 0)

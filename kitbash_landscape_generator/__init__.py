# SPDX-License-Identifier: GPL-3.0-or-later
"""KitBash Landscape Generator: a sidebar tab that adds landscapes to the scene."""

import hashlib
import json
import math
import os
import random
import re
import threading
import time

import bpy
import bpy.utils.previews
import numpy as np
from mathutils import Vector
from bpy.app.handlers import persistent
from bpy.props import BoolProperty, EnumProperty, FloatProperty, IntProperty, PointerProperty, StringProperty
from bpy.types import Operator, Panel, PropertyGroup, UIList

from . import erosion, nodes, presets

MODIFIER_NAME = "KB Landscape"
HERE = os.path.dirname(__file__)

with open(os.path.join(HERE, "types.json"), encoding="utf-8") as fh:
    TYPES_FILE = json.load(fh)
TYPES = TYPES_FILE["types"]
TYPE_GROUPS = TYPES_FILE.get("groups", [])  # picker order and headers (by setting)

# types.json key -> node group input, for the parts of a recipe the panel doesn't expose
TYPE_INPUTS = {"recipe": "Recipe", "detail": "Detail", "warp": "Warp", "rock": "Rock",
               "grain_roughness": "Grain Roughness"}
# Shape settings: the panel edits these; picking a type or Reset loads them from types.json.
LOOK_INPUTS = {"height": "Height", "feature_scale": "Feature Scale", "roughness": "Roughness",
               "sharpness": "Sharpness"}

_previews = None
_type_items = []  # Blender needs enum items kept alive while the enum is in use


def _type_enum(_self, _context):
    return _type_items


# Types are saved by key (e.g. "dunes"), never by list position, so adding a type can't
# change landscapes in saved files. M1 files stored a position; this was the M1 order.
_M1_ORDER = ("hills", "mountains", "dunes")
_GENERATED_NAME = re.compile(r"^Landscape(_[A-Za-z]+)?(\.\d{3})?$")


def _index_of(key):
    for k, _n, _l, _i, value in _type_items:
        if k == key:
            return value
    return 0


def _key_of(value):
    for k, _n, _l, _i, v in _type_items:
        if v == value:
            return k
    return TYPES_FILE["default"]


def _object_type_key(props):
    if props.type_key:
        return props.type_key
    old = props.get("land_type")  # M1 file
    return _M1_ORDER[old] if isinstance(old, int) and 0 <= old < len(_M1_ORDER) else TYPES_FILE["default"]


def _get_object_type(props):
    return _index_of(_object_type_key(props))


def _set_object_type(props, value):
    set_type(props.id_data, _key_of(value))


def set_type(ob, key):
    """Give a landscape a type: its recipe and that type's tuned look."""
    ob.lg.type_key = key
    apply_type_look(ob.lg)
    sync_object(ob)


def apply_type_look(props):
    recipe = TYPES.get(_object_type_key(props), TYPES[TYPES_FILE["default"]])
    for key in LOOK_INPUTS:
        setattr(props, key, recipe[key])
    for ctl in recipe.get("controls", ()):
        props[ctl["prop"]] = ctl["default"]  # raw write: no rebuild per control
    er = recipe.get("erosion", {})
    props["erosion_on"] = bool(er.get("on", False))
    props["erosion_amount"] = float(er.get("amount", 0.5))
    props["terraces"], props["terrace_strength"], props["terrace_tilt"] = 8, 0.0, 0.0  # off until asked for
    water = recipe.get("water", {})
    props["water"], props["water_level"] = bool(water.get("on", False)), float(water.get("level", 0.3))
    styles = recipe.get("styles")
    props.style_key = styles[0]["key"] if styles else ""
    _apply_style_look(props)
    props.look_set = True


def _style_entry(props):
    for st in TYPES.get(_object_type_key(props), {}).get("styles", ()):
        if st["key"] == props.style_key:
            return st
    return None


def _apply_style_look(props):
    st = _style_entry(props)
    for key, value in (st or {}).get("look", {}).items():
        setattr(props, key, value)


_style_items = []


def _style_enum(props, _context):
    # Rebuilt per call for the landscape's type; kept in a module list so Blender can hold it.
    _style_items[:] = [(st["key"], st["name"], st["desc"], i)
                       for i, st in enumerate(TYPES.get(_object_type_key(props), {}).get("styles", ()))] \
        or [("NONE", "None", "", 0)]
    return _style_items


def _get_style(props):
    styles = TYPES.get(_object_type_key(props), {}).get("styles", ())
    return next((i for i, st in enumerate(styles) if st["key"] == props.style_key), 0)


def _set_style(props, value):
    styles = TYPES.get(_object_type_key(props), {}).get("styles", ())
    if 0 <= value < len(styles):
        props.style_key = styles[value]["key"]
        _apply_style_look(props)
        sync_object(props.id_data)


def _get_scene_type(scene):
    return _index_of(scene.lg_type_key or TYPES_FILE["default"])


def _set_scene_type(scene, value):
    scene.lg_type_key = _key_of(value)
    _pick_type(scene, bpy.context)


def _load_type_items():
    global _previews
    _previews = bpy.utils.previews.new()
    _type_items.clear()
    # Values stay each type's position in types.json (stable for saved files); the list follows the groups.
    value = {key: i for i, key in enumerate(TYPES)}
    for key in [k for g in TYPE_GROUPS for k in g[2]] or list(TYPES):
        t = TYPES[key]
        path = os.path.join(HERE, "thumbs", key + ".png")
        icon = _previews.load(key, path, 'IMAGE').icon_id if os.path.exists(path) else 0
        _type_items.append((key, t["name"], t["look"], icon, value[key]))


def landscape_modifier(ob):
    if ob is None or not ob.lg.is_landscape:
        return None
    mod = ob.modifiers.get(MODIFIER_NAME)
    return mod if mod and mod.node_group else None


def current_landscape(context):
    """The landscape the tab edits: the active object if it is one, else the one picked in the list.
    So you can select other objects (e.g. for Fit to selection) without losing the landscape."""
    ob = context.active_object
    if landscape_modifier(ob):
        return ob
    scene = context.scene
    if 0 <= scene.lg_index < len(scene.objects):
        ob = scene.objects[scene.lg_index]
        if landscape_modifier(ob):
            return ob
    return None


def sync_object(ob):
    """Push every setting into the node group. Setting a modifier input from Python stores the
    value but doesn't rebuild the landscape in Blender 5.2, so the panel edits ob.lg and this
    writes it across (D19)."""
    mod = landscape_modifier(ob)
    if mod is None:
        return
    props = ob.lg
    props["size_seen"] = max(props.size_x, props.size_y)  # baseline for Proportional Feature Scaling
    want = nodes.ensure_group(TYPES.get(_object_type_key(props), TYPES[TYPES_FILE["default"]])["recipe"])
    if mod.node_group != want:  # each type has its own group; swapping resets inputs, all rewritten below
        mod.node_group = want
    values = {name: default for name, _t, default, *_rest in nodes.INPUTS}
    values.update({"Size X": props.size_x, "Size Y": props.size_y, "Final": props.final or props.ultra,
                   "Ultra": props.ultra})
    if not props.look_set:  # landscape from before step 2.2
        apply_type_look(props)
    recipe = TYPES.get(_object_type_key(props), TYPES[TYPES_FILE["default"]])
    values.update({sock: recipe[key] for key, sock in TYPE_INPUTS.items()})
    values.update({sock: getattr(props, key) for key, sock in LOOK_INPUTS.items()})
    values["Seed"] = props.seed
    st = _style_entry(props)
    if st:
        values["Style"] = st["index"]
    for ctl in recipe.get("controls", ()):
        values[ctl["slot"]] = _control_value(props, ctl)
    values["Show Mask"] = MASK_INDEX.get(props.show_mask, 0)
    values["Terraces"], values["Terrace Strength"], values["Terrace Tilt"] = float(props.terraces), props.terrace_strength, props.terrace_tilt
    if props.terrace_strength <= 0:  # count and tilt do nothing without strength: keep them out of the erosion key
        values["Terraces"], values["Terrace Tilt"] = 8.0, 0.0
    values["Water"], values["Water Level"] = props.water, props.water_level
    values["Cave"] = CAVE_INDEX[props.cave_layout]
    values["Cave X"], values["Cave Y"], values["Cave Size"] = props.cave_x, props.cave_y, props.cave_size
    values["Mask Heatmap"] = props.mask_colors == 'HEAT'
    managed = {"Erosion", "Erosion Map"}  # set by the erosion engine below, not reset on every sync
    # Eroded types always use the drained primary shape; Erosion Amount 0 shows it with full fine detail
    # and no erosion run (the old tick box swapped in a weaker pre-erosion shape; Mike, Pass 4 review).
    has_erosion = bool(recipe.get("erosion"))
    eroding = has_erosion and props.erosion_amount > 0
    values["Detail Floor"] = 4.0 * max(props.size_x, props.size_y) / EROSION_GRID[True] if eroding else 0.25  # 4 cells: resamples cleanly
    values["Primary"] = 1.0 if has_erosion else 0.0  # erosion builds on the drained primary shape (D55)
    for name, value in values.items():
        if name not in managed:
            nodes.input_socket(mod, name).value = value
    _erosion_update(ob, recipe, values)
    ob.update_tag()


# Erosion (R6, D54): computed on a capped grid from the landscape's own shape, cached per
# landscape as an image the node tree adds. The shape updates instantly; the eroded version
# replaces it a moment later (in the background build it runs straight away).
EROSION_GRID = {False: 256, True: 512}  # Preview / Final and Ultra
_KEY_SKIP = {"Final", "Ultra", "Preview Resolution", "Final Resolution", "Ultra Resolution", "Rock",
             "Grain Roughness", "Size X", "Size Y", "Erosion", "Erosion Map", "Detail Floor", "Show Mask", "Mask Heatmap",
             "Water", "Water Level", "Cave", "Cave X", "Cave Y", "Cave Size"}  # water and caves never change the eroded terrain: no re-erosion
_pending = {}


CAVE_ITEMS = (
    ('NONE', "None", "No cave"),
    ('ENTRANCE', "Entrance", "A grotto cut into the ground"),
    ('TUNNEL', "Entrance + Tunnel", "The entrance runs on into a winding passage"),
    ('CAVERN', "Entrance + Cavern", "The passage opens into a large chamber"),
)
CAVE_INDEX = {key: i for i, (key, _n, _d) in enumerate(CAVE_ITEMS)}


def _cave_changed(props, context):
    # Real-size caves (D91): the first cave on a landscape starts at a size that suits it, capped to fit.
    if props.cave_layout != 'NONE' and not props.cave_size_set:
        props["cave_size"] = min(max(min(props.size_x, props.size_y) * 0.06, 3.0), 60.0)
        props["cave_size_set"] = True
    _sync(props, context)


MASK_ITEMS = (
    ('NONE', "None", "Normal shading"),
    ('HEIGHT', "Height", "Low (dark) to high (bright)"),
    ('SLOPE', "Slope", "Flat (dark) to vertical (bright): where rock shows"),
    ('CURVATURE', "Curvature", "Ridges dark, hollows and valleys bright, even ground in between"),
    ('FLOW', "Flow", "Where water drains: bright along streams and rivers"),
    ('WEAR', "Wear", "Where erosion cut into the ground"),
    ('DEPOSIT', "Deposit", "Where erosion laid down sediment: fans and valley fill"),
    ('DEPTH', "Water Depth", "How deep the water is: dark at the shoreline, bright in deep water (Water on)"),
)
MASK_INDEX = {key: i for i, (key, _n, _d) in enumerate(MASK_ITEMS)}


_prev_shading = {}  # 3D view area (pointer) -> (shading type, colour type) before the mask viewer took it


def _show_mask_changed(props, context):
    """Colour the viewport by the picked mask: the landscape's lg_view colour attribute, shown by every 3D
    view's Solid mode in Attribute colour (enum 'VERTEX'). Back to None restores each view's own shading."""
    ob = props.id_data
    ob.data.color_attributes.active_color_name = "lg_view"
    sync_object(ob)
    showing = props.show_mask != 'NONE'
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            if area.type != 'VIEW_3D':
                continue
            sh = area.spaces.active.shading
            key = area.as_pointer()
            if showing:
                _prev_shading.setdefault(key, (sh.type, sh.color_type))
                if sh.type not in ('SOLID', 'WIREFRAME'):
                    sh.type = 'SOLID'
                sh.color_type = 'VERTEX'  # shown as "Attribute" in the Solid shading popover
            elif key in _prev_shading:
                sh.type, sh.color_type = _prev_shading.pop(key)


def _control_value(props, ctl):
    """A control limited to some styles ("styles": [...]) sits at its default in the others."""
    if "styles" in ctl and props.style_key not in ctl["styles"]:
        return ctl["default"]
    return getattr(props, ctl["prop"])


def _erosion_settings(recipe, props):
    er = dict(recipe.get("erosion", {}))
    for st in recipe.get("styles", ()):  # a style can change the erosion (Badlands Mounds: fine rills, not gullies)
        if st["key"] == props.style_key:
            er.update(st.get("erosion", {}))
    for k in ("on", "amount"):
        er.pop(k, None)
    er["seed"] = props.seed  # same seed, same erosion (T7)
    # Amount is erosion time: 0 none, 1 the type's full erosion. Every process scales with it, so a low
    # Amount keeps the shape (only incision scaled before, so 0.03 still melted it), and the drainage
    # stays whole (blending plain and eroded heights dammed rivers into pools; Mike, Pass 3).
    a = min(max(props.erosion_amount, 0.0), 1.0)
    d = erosion.DEFAULTS
    er["passes"] = max(int(round(er.get("passes", d["passes"]) * a)), 1)
    er["uplift"] = er.get("uplift", d["uplift"]) * a
    er["finish_blur"] = int(round(er.get("finish_blur", d["finish_blur"]) * a))
    er["final_slump"] = max(int(round(er.get("final_slump", d["final_slump"]) * a)), 1)
    er["floor_width"] = int(round(er.get("floor_width", d["floor_width"]) * a))
    er["floor_carve"] = int(round(er.get("floor_carve", d["floor_carve"]) * min(a * 2.0, 1.0)))
    for c in recipe.get("controls", ()):  # a slider can stretch an erosion setting: {"apron": [at 0, at 1]}
        for k, (lo, hi) in c.get("erosion", {}).items():
            er[k] = er.get(k, d[k]) * (lo + (hi - lo) * _control_value(props, c))
    return er


def _erosion_update(ob, recipe, values):
    mod = landscape_modifier(ob)
    props = ob.lg
    strength = nodes.input_socket(mod, "Erosion")
    if not (recipe.get("erosion") and props.erosion_amount > 0):  # Amount 0: plain shape, no run
        strength.value = 0.0
        return
    grid = EROSION_GRID[bool(props.final or props.ultra)]
    shape = sorted((k, round(v, 6) if isinstance(v, float) else v) for k, v in values.items() if k not in _KEY_SKIP)
    shape += [("aspect", round(props.size_x / props.size_y, 4)), ("grid", grid),
              ("erosion", json.dumps(_erosion_settings(recipe, props), sort_keys=True))]
    key = hashlib.sha1(repr(shape).encode()).hexdigest()
    img = bpy.data.images.get(ob.get("lg_erosion_img", ""))
    if img and ob.get("lg_erosion_key") == key:
        nodes.input_socket(mod, "Erosion Map").value = img
        strength.value = 1.0
        return
    job = _jobs.get(ob.name)
    if job and job["key"] == key and job["thread"].is_alive():  # already eroding exactly this
        return
    strength.value = 0.0  # show the new shape now; the eroded one follows
    if bpy.app.background:
        run_erosion(ob, grid, key)
        return
    _pending[ob.name] = (grid, key, time.time())
    if not bpy.app.timers.is_registered(_erosion_timer):
        bpy.app.timers.register(_erosion_timer, first_interval=0.1)


QUICK_GRID = 128  # a first look while the full erosion runs (speed, Mike Pass 4 review)
_jobs = {}  # landscape name -> running full erosion: {"key", "thread", "out"}


def _erosion_timer():
    now = time.time()
    for name, (grid, key, t) in list(_pending.items()):
        if now - t >= 0.35:  # wait until the slider has settled
            del _pending[name]
            ob = bpy.data.objects.get(name)
            if ob and landscape_modifier(ob):
                _start_erosion(ob, grid, key)
    for name, job in list(_jobs.items()):
        if job["thread"].is_alive():
            continue
        del _jobs[name]
        ob = bpy.data.objects.get(name)
        # Drop a result the artist has already moved on from (a newer request is pending or running).
        if ob and landscape_modifier(ob) and "eroded" in job["out"] and ob.get("lg_erosion_want") == job["key"]:
            _apply_erosion(ob, job["out"]["eroded"], job["key"], job["out"]["seconds"])
    _redraw_panels()  # keeps the "Eroding..." note current
    return 0.1 if (_pending or _jobs) else None


def _redraw_panels():
    for win in getattr(bpy.context.window_manager, "windows", ()):
        for area in win.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()


def _start_erosion(ob, grid, key):
    """Erode in the background so Blender stays responsive: a quick coarse pass shows at once, the full
    one replaces it when done (the engine is plain numpy and never touches Blender data)."""
    ob["lg_erosion_want"] = key
    if grid > QUICK_GRID:
        sample = _sample_shape(ob, QUICK_GRID)
        if sample:
            _apply_erosion(ob, _compute_erosion(*sample), None, 0.0)
    sample = _sample_shape(ob, grid)
    if not sample:
        return
    out = {}

    def work():
        t0 = time.time()
        out["eroded"] = _compute_erosion(*sample)
        out["seconds"] = round(time.time() - t0, 2)

    th = threading.Thread(target=work, daemon=True)
    _jobs[ob.name] = {"key": key, "thread": th, "out": out}
    th.start()
    if not bpy.app.timers.is_registered(_erosion_timer):
        bpy.app.timers.register(_erosion_timer, first_interval=0.1)


def _sample_shape(ob, grid):
    """The plain shape (no grain, no erosion) on a padded grid, plus the recipe's hard rock (main thread)."""
    mod = landscape_modifier(ob)
    props = ob.lg
    recipe = TYPES.get(_object_type_key(props), TYPES[TYPES_FILE["default"]])
    sock = {n: nodes.input_socket(mod, n) for n in ("Final", "Ultra", "Preview Resolution", "Rock", "Erosion", "Pad Cells")}
    saved = {n: s.value for n, s in sock.items()}
    sock["Final"].value, sock["Ultra"].value = False, False
    sock["Preview Resolution"].value, sock["Rock"].value, sock["Erosion"].value = grid, 0.0, 0.0
    # Erode a ring of the shape beyond the edges and crop it: fixed edges carved notches and drips
    # along every border (how terrain tools handle edges; Pass 3).
    pad = max(int(round(grid * 0.08)), 2)
    sock["Pad Cells"].value = float(pad)
    ob.update_tag()
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    hard = np.zeros(len(me.vertices))
    if "lg_hard" in me.attributes:  # hard rock from the recipe (Pass 3)
        me.attributes["lg_hard"].data.foreach_get("value", hard)
    ev.to_mesh_clear()
    for n, s in sock.items():
        if n != "Erosion":
            s.value = saved[n]
    ob.update_tag()
    if co.size < 12:  # not built yet (e.g. mid Add Landscape): the next sync erodes it
        return None
    co = co.reshape(-1, 3)
    order = np.lexsort((co[:, 0], co[:, 1]))  # rows of increasing y, each of increasing x
    co, hard = co[order], hard[order]
    nx = int(np.unique(np.round(co[:, 0], 5)).size)
    ny = co.shape[0] // nx
    h = co[:, 2].reshape(ny, nx) / max(props.size_x, props.size_y)
    settings = _erosion_settings(recipe, props)
    settings["edge_blend"] = 0.0  # the padding takes care of the edges
    return h, hard.reshape(ny, nx), settings, pad


def _compute_erosion(h, hard, settings, pad):
    """Pure numpy: safe on a worker thread."""
    z, (flow, change) = erosion.erode(h, settings, hard, masks=True)
    crop = (slice(pad, -pad), slice(pad, -pad))
    return z[crop], flow[crop], change[crop]


def _apply_erosion(ob, eroded, key, seconds):
    """Store the eroded heights as the landscape's erosion map (main thread)."""
    mod = landscape_modifier(ob)
    props = ob.lg
    # Eroded heights in units of Height (the node tree blends them in), one texel per grid point, read
    # with the node tree's smooth cubic lookup. Doubling it first left kinks (linear) or ringing at every
    # cliff (Catmull-Rom): 4 m and false 114 m spectrum spikes on Badlands and Mesa (Pass 6). (Storing only
    # the change kept the shape's fine detail everywhere and lost the smooth-floor / rough-rock contrast:
    # rough split 0.68 vs 1.27 real, Pass 2.)
    eroded, flow, change = eroded  # heights, plus the flow and wear/deposit masks (M3) in G and B
    delta = eroded / max(props.height, 1e-6)
    ny, nx = delta.shape
    name = f"LG Erosion {ob.name}"
    img = bpy.data.images.get(ob.get("lg_erosion_img", "")) or bpy.data.images.get(name)
    if img is None or tuple(img.size) != (nx, ny):
        if img is not None:
            bpy.data.images.remove(img)
        img = bpy.data.images.new(name, nx, ny, float_buffer=True, alpha=False)
        img.colorspace_settings.name = "Non-Color"
    rgba = np.zeros((ny, nx, 4), dtype=np.float32)
    rgba[..., 0] = delta
    rgba[..., 1] = flow
    rgba[..., 2] = change
    rgba[..., 3] = 1.0
    img.pixels.foreach_set(rgba.ravel())
    img.file_format = 'OPEN_EXR'
    try:
        img.pack()  # saved inside the .blend, so reopening doesn't recompute
    except RuntimeError:
        pass
    nodes.input_socket(mod, "Erosion Map").value = img
    nodes.input_socket(mod, "Erosion").value = 1.0
    ob["lg_erosion_key"] = key or ""  # the quick look has no key, so the full result still replaces it
    ob["lg_erosion_img"] = img.name
    ob["lg_erosion_seconds"] = seconds
    ob.update_tag()


def run_erosion(ob, grid=None, key=None):
    """Erode this landscape's shape now (synchronously) and store the result as its erosion map."""
    grid = grid or EROSION_GRID[bool(ob.lg.final or ob.lg.ultra)]
    sample = _sample_shape(ob, grid)
    if sample:
        t0 = time.time()
        _apply_erosion(ob, _compute_erosion(*sample), key, round(time.time() - t0, 2))


def _sync(props, _context):
    sync_object(props.id_data)


def _size_changed(props, _context):
    """Any size change (typed, 2X/4X, Fit to Selection): with Proportional Feature Scaling on,
    features keep their real size, so a bigger landscape fits more of them."""
    new = max(props.size_x, props.size_y)
    old = props.get("size_seen", new)
    if props.proportional and old > 0 and new != old:
        f = new / old
        props["feature_scale"] = min(max(props.feature_scale * f, 0.1), 50.0)
        props["height"] = min(max(props.height / f, 0.0), 1.0)
    sync_object(props.id_data)


def _refresh_all():
    """Rebuild an outdated node group and re-push every landscape's settings into it
    (a rebuild resets all modifier inputs to zero)."""
    landscapes = [ob for ob in bpy.data.objects if landscape_modifier(ob)]
    if not landscapes:
        return
    for ob in landscapes:
        sync_object(ob)
    old = bpy.data.node_groups.get(nodes.GROUP_NAME)  # the single shared group from before D43
    if old and old.users == 0:
        bpy.data.node_groups.remove(old)


@persistent
def _on_load(_dummy):
    _refresh_all()


def _ref(props):
    return max(props.size_x, props.size_y)


# The panel shows Height and Feature Size in meters but stores them as fractions of the
# landscape's size, so resizing keeps the look (D3). Sharpness % maps 0/50/100 to x0.25/x1/x4.
def _get_height_m(props):
    return props.height * _ref(props)


def _set_height_m(props, value):
    props.height = min(max(value / _ref(props), 0.0), 1.0)  # bigger = scale up Size; taller turns into a spire
    sync_object(props.id_data)


def _get_feature_m(props):
    return _ref(props) / props.feature_scale


def _set_feature_m(props, value):
    props.feature_scale = min(max(_ref(props) / max(value, 1e-3), 0.1), 50.0)
    sync_object(props.id_data)


def _get_rough_pct(props):
    return props.roughness * 100.0


def _set_rough_pct(props, value):
    props.roughness = value / 100.0
    sync_object(props.id_data)


def _get_sharp_pct(props):
    return 50.0 + 25.0 * math.log2(max(props.sharpness, 1e-6))


def _set_sharp_pct(props, value):
    props.sharpness = 2.0 ** ((value - 50.0) / 25.0)
    sync_object(props.id_data)


def _set_detail(props, value):
    props["final"] = value >= 1
    props["ultra"] = value == 2
    sync_object(props.id_data)


class LG_ObjectProps(PropertyGroup):
    is_landscape: BoolProperty(name="Is Landscape", default=False)
    type_key: StringProperty(name="Type Key", default="")
    land_type: EnumProperty(name="Type", description="What kind of landscape this is", items=_type_enum, get=_get_object_type, set=_set_object_type)
    size_x: FloatProperty(name="Width", description="Width of the landscape in meters",
                          default=200.0, min=1.0, max=100000.0, soft_max=5000.0, unit='LENGTH', update=_size_changed)
    size_y: FloatProperty(name="Depth", description="Depth of the landscape in meters",
                          default=200.0, min=1.0, max=100000.0, soft_max=5000.0, unit='LENGTH', update=_size_changed)
    detail: EnumProperty(name="Detail Level", description="How many points the landscape is built from: light while editing, heavy for the finished shot", items=(
        ('PREVIEW', "Preview", "Light and fast, for dialing in the look"),
        ('FINAL', "High", "Full detail for the finished landscape (about 4 million points)"),  # key kept: saved files
        ('ULTRA', "Ultra", "Hero detail for close-up shots. Heavy: about 17 million points")),
        get=lambda p: 2 if p.ultra else 1 if p.final else 0, set=lambda p, v: _set_detail(p, v))
    ultra: BoolProperty(name="Ultra", description="Hero detail for close-up shots. Heavy: about 17 million points",
                        default=False, update=_sync)
    final: BoolProperty(name="High", description="Full detail for the finished landscape. Off = lighter Preview for editing",
                        default=False, update=_sync)
    # Stored look (fractions of size / raw recipe values)
    look_set: BoolProperty(default=False)
    height: FloatProperty(default=0.15)
    feature_scale: FloatProperty(default=3.0)
    roughness: FloatProperty(default=0.5)
    sharpness: FloatProperty(default=1.0)
    # Per-type style and controls (which types use them is set in types.json)
    style_key: StringProperty(default="")
    style: EnumProperty(name="Style", description="Which kind of this landscape to build",
                        items=_style_enum, get=_get_style, set=_set_style)
    crater_size: FloatProperty(name="Crater Size", description="How wide the crater at the top is",
                               default=0.5, min=0.0, max=1.0, subtype='FACTOR', update=_sync)
    steepness: FloatProperty(name="Steepness", description="Gentle slopes, or steep sides that rise sharply to the top",
                             default=0.5, min=0.0, max=1.0, subtype='FACTOR', update=_sync)
    gullies: FloatProperty(name="Gullies", description="Channels worn down the sides by water and landslides",
                           default=0.5, min=0.0, max=1.0, subtype='FACTOR', update=_sync)
    breach: FloatProperty(name="Breach", description="Opens the crater wall on one side, where lava or a blast broke through",
                          default=0.0, min=0.0, max=1.0, subtype='FACTOR', update=_sync)
    crater_depth: FloatProperty(name="Crater Depth", description="How deep the crater goes",
        default=0.5, min=0.0, max=1.0, subtype='FACTOR', update=_sync)
    rim_thickness: FloatProperty(name="Rim Thickness", description="How thick the crater rim and summit stay, so the top never thins to a spike",
        default=0.3, min=0.0, max=1.0, subtype='FACTOR', update=_sync)
    crater_count: FloatProperty(name="Crater Count", description="How many craters: a few, or a saturated surface",
        default=0.5, min=0.0, max=1.0, subtype='FACTOR', update=_sync)
    crater_scale: FloatProperty(name="Crater Size", description="How big each crater is compared with its spacing",
        default=0.5, min=0.0, max=1.0, subtype='FACTOR', update=_sync)
    crater_variety: FloatProperty(name="Variety", description="Range from the smallest crater to the largest: similar sizes, or huge basins down to pinpricks",
        default=0.6, min=0.0, max=1.0, subtype='FACTOR', update=_sync)
    erosion_on: BoolProperty(name="Erosion (unused, kept for old files)", description="Water carves valleys, sediment settles, loose rock slides into scree. Updates a moment after you change the shape",
                             default=False, update=_sync)
    erosion_amount: FloatProperty(name="Erosion Amount", description="How long erosion runs: a light touch that keeps the shape, up to fully eroded (1)",
                                  default=0.5, min=0.0, max=1.0, subtype='FACTOR', update=_sync)
    crater_age: FloatProperty(name="Age", description="Surface age: young = many fresh, sharp craters; old = mostly soft, worn ghost craters with a few fresh ones (like the Moon)",
        default=0.6, min=0.0, max=1.0, subtype='FACTOR', update=_sync)
    ridge_width: FloatProperty(name="Ridge Width", description="Knife-thin ridgelines, or broad rounded ridges",
        default=0.6, min=0.0, max=1.0, subtype='FACTOR', update=_sync)
    wind_direction: FloatProperty(name="Wind Direction", description="Which way the wind blows the dunes",
        default=0.0, subtype='ANGLE', update=_sync)
    channel_width: FloatProperty(name="Channel Width", description="Narrow slot canyons, or wide open valleys",
        default=0.4, min=0.0, max=1.0, subtype='FACTOR', update=_sync)
    plateau_amount: FloatProperty(name="Plateau Amount", description="How much of the land stays up on the flat plateau",
        default=0.6, min=0.0, max=1.0, subtype='FACTOR', update=_sync)
    plateau_coverage: FloatProperty(name="Plateau Coverage", description="How much of the land is flat tabletop",
        default=0.5, min=0.0, max=1.0, subtype='FACTOR', update=_sync)
    talus_spread: FloatProperty(name="Talus Spread", description="How far the rubble slopes at the foot of the cliffs reach out",
        default=0.5, min=0.0, max=1.0, subtype='FACTOR', update=_sync)
    caprock_tiers: FloatProperty(name="Caprock Tiers", description="None, or a stepped upper tier on the biggest mesas",
        default=0.5, min=0.0, max=1.0, subtype='FACTOR', update=_sync)
    mesa_floor: BoolProperty(name="Floor", description="Off: no desert floor, just the mesas and their talus aprons, to place on your own ground",
        default=True, update=_sync)
    valley_width: FloatProperty(name="Valley Width", description="How wide the U-shaped valley floor is",
        default=0.4, min=0.0, max=1.0, subtype='FACTOR', update=_sync)
    channel_count: FloatProperty(name="Channel Count", description="A few big channels, or many small braided ones",
        default=0.4, min=0.0, max=1.0, subtype='FACTOR', update=_sync)
    inner_cone: FloatProperty(name="Inner Cone", description="An island cone in a caldera, or a lava dome in a stratovolcano's crater",
        default=0.6, min=0.0, max=1.0, subtype='FACTOR', update=_sync)
    gully_density: FloatProperty(name="Gully Density", description="Few broad mounds, or many tight gullies",
        default=0.5, min=0.0, max=1.0, subtype='FACTOR', update=_sync)
    show_mask: EnumProperty(name="Show Mask", description="Colour the viewport by one of the landscape's data masks, the maps materials and scatter use",
                            items=MASK_ITEMS, default='NONE', update=_show_mask_changed)
    terraces: IntProperty(name="Terraces", description="How many terrace steps from the lowest to the highest ground",
                          default=8, min=2, max=40, update=_sync)
    terrace_strength: FloatProperty(name="Terrace Strength", description="None, up to flat benches between steep rock steps",
                                    default=0.0, min=0.0, max=1.0, subtype='FACTOR', update=_sync)
    terrace_tilt: FloatProperty(name="Terrace Tilt", description="Level layers, or layers that dip to one side so the steps run at an angle",
                                default=0.0, min=0.0, max=1.0, subtype='FACTOR', update=_sync)
    water: BoolProperty(name="Water", description="A water surface at the water level: lakes, sea and flooded valleys where the ground is lower",
                        default=False, update=_sync)
    water_level: FloatProperty(name="Water Level", description="How high the water comes: 0 the lowest ground, 1 the highest",
                               default=0.3, min=0.0, max=1.0, subtype='FACTOR', update=_sync)
    cave_layout: EnumProperty(name="Cave", description="Carve a cave into the landscape. Every cave starts with an entrance",
                              items=CAVE_ITEMS, default='NONE', update=_cave_changed)
    cave_x: FloatProperty(name="Across", description="Where the cave sits across the landscape, left to right",
                          default=0.5, min=0.0, max=1.0, subtype='FACTOR', update=_sync)
    cave_y: FloatProperty(name="Front to Back", description="Where the cave sits from the front edge to the back",
                          default=0.5, min=0.0, max=1.0, subtype='FACTOR', update=_sync)
    cave_size: FloatProperty(name="Entrance Width", description="How wide the cave mouth is, in real size: it stays the same when you resize the landscape",
                             default=12.0, min=0.5, soft_max=200.0, unit='LENGTH', update=_sync)
    cave_size_set: BoolProperty(default=False)
    mask_colors: EnumProperty(name="Colours", description="How the mask viewer shows a mask",
                              items=(('GRAY', "Grayscale", "Black (0) to white (1), as game engines and material editors show these maps"),
                                     ('HEAT', "Heatmap", "Dark blue (0) through teal to yellow (1): easier to read small differences")),
                              default='GRAY', update=_sync)
    proportional: BoolProperty(name="Proportional Feature Scaling", description="On: scaling keeps hills, peaks and dunes their real size, so a bigger landscape fits more of them. Off: everything grows together",
                               default=False)
    seed: IntProperty(name="Seed", description="Same seed, same landscape. Change it for a new layout of the same look",
                      default=0, min=0, max=99999, update=_sync)
    # What the panel shows
    height_m: FloatProperty(name="Height", description="How tall the tallest parts get. Grows with the size",
                            min=0.0, soft_max=20000.0, unit='LENGTH', get=_get_height_m, set=_set_height_m)
    feature_m: FloatProperty(name="Feature Size", description="How big the main hills, peaks or dunes are",
                             min=0.01, soft_max=5000.0, unit='LENGTH', get=_get_feature_m, set=_set_feature_m)
    roughness_pct: FloatProperty(name="Roughness", description="Smooth and soft, or bumpy with lots of small detail",
                                 min=0.0, max=100.0, subtype='PERCENTAGE', get=_get_rough_pct, set=_set_rough_pct)
    sharpness_pct: FloatProperty(name="Peak Sharpness",
                                 description="Rounded tops and full valleys, or pointy tops and flatter lows",
                                 min=0.0, max=100.0, subtype='PERCENTAGE', get=_get_sharp_pct, set=_set_sharp_pct)


def _select_listed(scene, _context):
    """Picking a row in the list makes that landscape the active object."""
    if not 0 <= scene.lg_index < len(scene.objects):
        return
    ob = scene.objects[scene.lg_index]
    view_layer = bpy.context.view_layer
    if ob.name not in view_layer.objects:
        return
    for other in view_layer.objects.selected:
        other.select_set(False)
    ob.select_set(True)
    view_layer.objects.active = ob
    if ob.lg.is_landscape:
        scene.lg_type_key = _object_type_key(ob.lg)  # show its type without re-triggering the pick


def _pick_type(scene, context):
    """Picking a type changes the active landscape; Add Landscape uses it for new ones."""
    ob = current_landscape(context)
    key = scene.lg_type_key
    if ob and _object_type_key(ob.lg) != key:
        set_type(ob, key)
        if _GENERATED_NAME.match(ob.name):  # keep names the user typed
            ob.name = "Landscape_" + TYPES[key]["name"].replace(" ", "")


class LG_OT_add_landscape(Operator):
    bl_idname = "landscape.add"
    bl_label = "Add Landscape"
    bl_description = "Add a new landscape of the picked type at the 3D cursor"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def execute(self, context):
        scene = context.scene
        kind = scene.lg_type_key or TYPES_FILE["default"]
        name = "Landscape_" + TYPES[kind]["name"].replace(" ", "")
        previous = current_landscape(context)
        ob = bpy.data.objects.new(name, bpy.data.meshes.new(name))
        ob.location = scene.cursor.location
        ob.lg.is_landscape = True
        if previous:  # a new landscape matches the size and detail you dialed in
            for prop in ("size_x", "size_y", "final", "ultra"):
                ob.lg[prop] = getattr(previous.lg, prop)
        ob.modifiers.new(MODIFIER_NAME, 'NODES').node_group = nodes.ensure_group(TYPES[kind]["recipe"])
        set_type(ob, kind)
        context.collection.objects.link(ob)
        for other in context.selected_objects:
            other.select_set(False)
        ob.select_set(True)
        context.view_layer.objects.active = ob
        scene.lg_index = list(scene.objects).index(ob)
        return {'FINISHED'}


class LG_OT_scale_size(Operator):
    bl_idname = "landscape.scale_size"
    bl_label = "Scale Landscape"
    bl_description = "Multiply the landscape's width and depth. Shapes stay the same"
    bl_options = {'REGISTER', 'UNDO'}

    factor: FloatProperty(name="Factor", default=2.0, min=0.001, max=1000.0)

    @classmethod
    def poll(cls, context):
        return current_landscape(context) is not None

    def execute(self, context):
        props = current_landscape(context).lg
        props.size_x *= self.factor  # the property's min/max clamp tiny and huge sizes
        props.size_y *= self.factor
        return {'FINISHED'}


class LG_OT_pick_type(Operator):
    bl_idname = "landscape.pick_type"
    bl_label = "Pick Type"
    bl_description = "Use this landscape type"
    bl_options = {'REGISTER', 'UNDO'}

    type_key: StringProperty()

    @classmethod
    def description(cls, _context, props):
        t = TYPES.get(props.type_key)
        return f"{t['name']}: {t['look']}" if t else cls.bl_description

    def execute(self, context):
        if self.type_key in TYPES:
            context.scene.lg_type = self.type_key
        return {'FINISHED'}


class LG_OT_randomize(Operator):
    bl_idname = "landscape.randomize"
    bl_label = "Randomize"
    bl_description = "Try a new layout with the same look (new seed)"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return current_landscape(context) is not None

    def execute(self, context):
        props = current_landscape(context).lg
        props.seed = (props.seed + random.randint(1, 99998)) % 100000  # always a different seed
        return {'FINISHED'}


class LG_OT_reset_look(Operator):
    bl_idname = "landscape.reset_look"
    bl_label = "Reset"
    bl_description = "Put Height, Feature Size, Roughness, Peak Sharpness, the style and this type's own sliders back to its tuned look"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return current_landscape(context) is not None

    def execute(self, context):
        ob = current_landscape(context)
        apply_type_look(ob.lg)
        sync_object(ob)
        return {'FINISHED'}


# Saved looks (presets.py): name a landscape's full look, load it in any project (Mike, 2026-10-25).
CONTROL_PROPS = sorted({c["prop"] for t in TYPES.values() for c in t.get("controls", ())})
_preset_items = []


def _preset_enum(_self, _context):
    _preset_items.clear()
    for i, name in enumerate(sorted(presets.load_all(), key=str.lower)):
        _preset_items.append((name, name, f"Load the look saved as {name}", i))
    if not _preset_items:
        _preset_items.append(("", "No saved presets yet", "Save a look you like with Save Preset", 0))
    return _preset_items


class LG_OT_preset_save(Operator):
    bl_idname = "landscape.preset_save"
    bl_label = "Save Preset"
    bl_description = "Save this landscape's whole look (type, style, every slider, seed, erosion, size) under a name, for any project"
    bl_options = {'REGISTER'}
    name: StringProperty(name="Name", default="My Landscape")

    @classmethod
    def poll(cls, context):
        return current_landscape(context) is not None

    def invoke(self, context, _event):
        ob = current_landscape(context)
        self.name = f"My {TYPES.get(_object_type_key(ob.lg), {}).get('name', 'Landscape')}"
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        name = self.name.strip()
        if not name:
            self.report({'WARNING'}, "Give the preset a name")
            return {'CANCELLED'}
        presets.save(name, current_landscape(context).lg, CONTROL_PROPS)
        context.scene.lg_preset = name
        self.report({'INFO'}, f"Saved preset {name}")
        return {'FINISHED'}


class LG_OT_preset_load(Operator):
    bl_idname = "landscape.preset_load"
    bl_label = "Load"
    bl_description = "Give the selected landscape the picked preset's look (with no landscape selected, add a new one)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        data = presets.load_all().get(context.scene.lg_preset)
        if not data:
            self.report({'WARNING'}, "Pick a saved preset first")
            return {'CANCELLED'}
        ob = current_landscape(context)
        if ob is None:
            if data.get("type") in TYPES:
                context.scene.lg_type = data["type"]
            bpy.ops.landscape.add()
            ob = context.view_layer.objects.active
        presets.apply(ob.lg, data, TYPES)
        sync_object(ob)
        return {'FINISHED'}


class LG_OT_preset_rename(Operator):
    bl_idname = "landscape.preset_rename"
    bl_label = "Rename Preset"
    bl_description = "Rename the picked preset"
    name: StringProperty(name="New name", default="")

    def invoke(self, context, _event):
        self.name = context.scene.lg_preset
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        new = self.name.strip()
        if not new or not context.scene.lg_preset:
            return {'CANCELLED'}
        presets.rename(context.scene.lg_preset, new)
        context.scene.lg_preset = new
        return {'FINISHED'}


class LG_OT_preset_delete(Operator):
    bl_idname = "landscape.preset_delete"
    bl_label = "Delete Preset"
    bl_description = "Delete the picked preset for good (it is removed from every project)"

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        if context.scene.lg_preset:
            presets.delete(context.scene.lg_preset)
        return {'FINISHED'}


FIT_MARGIN = 1.1  # 10% border around the fitted objects


def _fit_sources(context):
    return [o for o in context.selected_objects if not o.lg.is_landscape and o.type != 'CAMERA' and o.type != 'LIGHT']


class LG_OT_fit_selection(Operator):
    bl_idname = "landscape.fit_selection"
    bl_label = "Fit to Selection"
    bl_description = ("Resize the landscape so it covers the selected objects, with a margin. "
                      "It stays where it is; place it with the 3D cursor")
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if current_landscape(context) is None:
            return False
        if not _fit_sources(context):
            cls.poll_message_set("Select the objects to cover first")
            return False
        return True

    def execute(self, context):
        ob = current_landscape(context)
        cx, cy = ob.matrix_world.translation.xy
        reach_x = reach_y = 0.0
        for src in _fit_sources(context):
            for corner in src.bound_box:
                x, y, _z = src.matrix_world @ Vector(corner)
                reach_x, reach_y = max(reach_x, abs(x - cx)), max(reach_y, abs(y - cy))
        # Sized around the landscape's own centre, so it covers them without moving.
        ob.lg.size_x = max(2 * reach_x * FIT_MARGIN, 1.0)
        ob.lg.size_y = max(2 * reach_y * FIT_MARGIN, 1.0)
        return {'FINISHED'}


class LG_UL_landscapes(UIList):
    def draw_item(self, _context, layout, _data, item, _icon, _active_data, _active_prop, _index):
        layout.prop(item, "name", text="", emboss=False, icon='MESH_GRID')

    def filter_items(self, _context, data, propname):
        objects = getattr(data, propname)
        flags = [self.bitflag_filter_item if ob.lg.is_landscape else 0 for ob in objects]
        return flags, []


RECIPE_KEY = "lg_recipe"  # the landscape's full settings, kept on a baked mesh so it can be rebuilt


class LG_OT_bake(Operator):
    bl_idname = "landscape.bake"
    bl_label = "Bake to Mesh"
    bl_description = ("Turn the landscape into a plain mesh you can sculpt and edit, keeping its masks. The "
                      "sliders stop working; its settings are kept so it can be restored")
    bl_options = {'REGISTER', 'UNDO'}

    save_preset: BoolProperty(name="Save as preset", default=True,
                              description="Also keep its settings as a preset you can load on any landscape")

    @classmethod
    def poll(cls, context):
        return current_landscape(context) is not None

    def invoke(self, context, _event):
        return context.window_manager.invoke_props_dialog(self, width=360)

    def draw(self, _context):
        col = self.layout.column()
        col.label(text="The sliders stop working on a baked mesh.")
        col.label(text="Its settings stay on the mesh:")
        col.label(text="Restore Landscape rebuilds it any time.")
        col.prop(self, "save_preset")

    def execute(self, context):
        ob = current_landscape(context)
        if ob.name in _pending or ob.name in _jobs:
            self.report({'WARNING'}, "Erosion is still running: bake once the eroded look has arrived")
            return {'CANCELLED'}
        props = ob.lg
        recipe = presets.capture(props, CONTROL_PROPS)
        mod = landscape_modifier(ob)
        # Bake only the landscape: the artist's own modifiers (Array, Displace...) stay live on top of the
        # baked mesh; baking them in as well applied them twice (M4 checker).
        others = [(m, m.show_viewport) for m in ob.modifiers if m.name != mod.name]  # by name: bpy wrappers differ per access
        for m, _on in others:
            m.show_viewport = False
        ob.update_tag()
        context.view_layer.update()  # re-evaluate with only the landscape on (dg.update alone kept a stale result)
        dg = context.evaluated_depsgraph_get()
        me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
        for m, on in others:
            m.show_viewport = on
        me.name = f"{ob.name} baked"
        # Water becomes its own object (Mike): one flat quad at the water level, with its own material.
        water_z = None
        wet = me.attributes.get("lg_water")
        if wet is not None:
            import bmesh
            flags = [False] * len(me.vertices)
            wet.data.foreach_get("value", flags)
            if any(flags):
                water_z = next(v.co.z for v, f in zip(me.vertices, flags) if f)
                bm = bmesh.new()
                bm.from_mesh(me)
                bm.verts.ensure_lookup_table()
                bmesh.ops.delete(bm, geom=[bm.verts[i] for i, f in enumerate(flags) if f], context='VERTS')
                bm.to_mesh(me)
                bm.free()
            me.attributes.remove(me.attributes["lg_water"])
        for i in reversed(range(len(me.materials))):  # the water's material slot went with the water
            if me.materials[i] is not None and me.materials[i].name.startswith(nodes.WATER_MATERIAL):
                me.materials.pop(index=i)
        img = bpy.data.images.get(ob.get("lg_erosion_img", ""))
        old = ob.data
        ob.modifiers.remove(mod)
        ob.data = me
        if old.users == 0:
            bpy.data.meshes.remove(old)
        if img is not None and img.users == 0:
            bpy.data.images.remove(img)  # the erosion map lives on in the mesh now
        props.is_landscape = False
        for key in ("lg_erosion_img", "lg_erosion_key", "lg_erosion_want"):
            ob.pop(key, None)
        ob[RECIPE_KEY] = json.dumps(recipe)
        if water_z is not None:
            wme = bpy.data.meshes.new(f"{ob.name} water")
            hx, hy = props.size_x / 2, props.size_y / 2
            wme.from_pydata([(-hx, -hy, water_z), (hx, -hy, water_z), (hx, hy, water_z), (-hx, hy, water_z)], [], [(0, 1, 2, 3)])
            wme.materials.append(nodes.water_material())
            water = bpy.data.objects.new(f"{ob.name}_Water", wme)
            for col in ob.users_collection:
                col.objects.link(water)
            water.matrix_world = ob.matrix_world.copy()
            ob["lg_water_obj"] = water.name  # so Restore hides it with the mesh (Mike: the water stayed behind)
        if self.save_preset:
            presets.save(f"{ob.name} (baked)", props, CONTROL_PROPS)
        self.report({'INFO'}, f"Baked {ob.name}" + (" and its water" if water_z is not None else ""))
        return {'FINISHED'}


class LG_OT_restore(Operator):
    bl_idname = "landscape.restore"
    bl_label = "Restore Landscape"
    bl_description = "Rebuild the live landscape this mesh was baked from, with all its settings, beside it"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        return ob is not None and RECIPE_KEY in ob.keys()

    def execute(self, context):
        baked = context.active_object
        try:
            data = json.loads(baked[RECIPE_KEY])
        except (TypeError, ValueError):
            self.report({'WARNING'}, "This mesh's stored settings can't be read")
            return {'CANCELLED'}
        if data.get("type") not in TYPES:
            self.report({'WARNING'}, f"Its landscape type ({data.get('type')}) isn't in this version of the add-on")
            return {'CANCELLED'}
        scene = context.scene
        keep_type, keep_cursor = scene.lg_type, scene.cursor.location.copy()
        scene.lg_type = data["type"]
        scene.cursor.location = baked.matrix_world.translation
        bpy.ops.landscape.add()
        ob = context.view_layer.objects.active
        for col in list(ob.users_collection):  # beside the baked mesh, in its collections
            col.objects.unlink(ob)
        for col in baked.users_collection:
            col.objects.link(ob)
        presets.apply(ob.lg, data, TYPES)
        ob.matrix_world = baked.matrix_world.copy()
        sync_object(ob)
        scene.lg_type, scene.cursor.location = keep_type, keep_cursor
        baked.hide_set(True)  # the live one takes its place; the baked mesh stays in the file
        water = bpy.data.objects.get(baked.get("lg_water_obj", ""))
        if water is not None:
            water.hide_set(True)  # the restored landscape has its own water
        return {'FINISHED'}


class LG_PT_main(Panel):
    bl_label = "KitBash Landscape Generator"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Landscape"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        row = layout.row()
        row.scale_y = 1.6
        row.operator(LG_OT_add_landscape.bl_idname, icon='ADD')

        # Each section folds open and closed, so artists keep open only what they need (Mike, Pass 4 review:
        # Add, Type, Size & Shape, then later Water, Materials, Mood).
        header, box = layout.panel("lg_scene", default_closed=False)
        header.label(text="In this scene")
        if box:
            if any(ob.lg.is_landscape for ob in scene.objects):
                box.template_list("LG_UL_landscapes", "", scene, "objects", scene, "lg_index", rows=3)
            else:
                col = box.column(align=True)
                col.label(text="No landscapes yet.")
                col.label(text="Pick a type, then press Add Landscape.")

        header, box = layout.panel("lg_type_section", default_closed=False)
        header.label(text="Landscape type")
        if box:
            box.template_icon_view(scene, "lg_type", show_labels=True, scale=6.0, scale_popup=5.0)
            picked = TYPES[scene.lg_type_key or TYPES_FILE["default"]]
            col = box.column(align=True)
            col.label(text=picked["name"])
            col.label(text=picked["look"])
            header, body = box.panel("lg_all_types", default_closed=True)
            header.label(text="All types")
            header.prop(scene, "lg_types_view", expand=True, icon_only=True)
            if body:
                if scene.lg_types_view == 'LIST':
                    col = body.column(align=True)
                    for _gkey, label, keys in TYPE_GROUPS:  # grouped by setting (Mike)
                        col.label(text=label)
                        for key in keys:
                            col.prop_enum(scene, "lg_type", key)
                        col.separator()
                else:
                    # shortcut: Blender add-on buttons draw icons at a fixed small size, so a big image can't
                    # itself be a button; the name button under each image picks it. The gallery popup above
                    # is the one place large thumbnails are clickable.
                    grid = body.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True)
                    for key, name, _look, icon, _i in _type_items:
                        cell = grid.column(align=True)
                        cell.template_icon(icon_value=icon, scale=4.0)
                        # An operator, not prop_enum: prop_enum repeats the thumbnail as a tiny icon and
                        # pushes the name off-centre.
                        cell.operator(LG_OT_pick_type.bl_idname, text=name,
                                      depress=key == (scene.lg_type_key or TYPES_FILE["default"])).type_key = key

        header, box = layout.panel("lg_presets", default_closed=True)
        header.label(text="Presets")
        if box:
            row = box.row(align=True)
            row.prop(scene, "lg_preset", text="")
            row.operator(LG_OT_preset_load.bl_idname, icon='IMPORT')
            row = box.row(align=True)
            row.operator(LG_OT_preset_save.bl_idname, icon='FILE_TICK')
            row.operator(LG_OT_preset_rename.bl_idname, text="", icon='GREASEPENCIL')
            row.operator(LG_OT_preset_delete.bl_idname, text="", icon='TRASH')

        ob = current_landscape(context)
        if ob is None:
            if context.active_object is not None and RECIPE_KEY in context.active_object.keys():
                box = layout.box()
                box.label(text="A baked landscape: its sliders are kept on it.")
                box.operator(LG_OT_restore.bl_idname, icon='LOOP_BACK')
            return
        mod = landscape_modifier(ob)
        props = ob.lg

        header, box = layout.panel("lg_size", default_closed=False)
        header.label(text="Size")
        if box:
            for factors in ((2, 4, 8), (1 / 2, 1 / 4, 1 / 8)):
                row = box.row(align=True)
                for f in factors:
                    label = f"{f:g}X" if f > 1 else f"1/{round(1 / f)}"
                    row.operator(LG_OT_scale_size.bl_idname, text=label).factor = f
            col = box.column(align=True)
            col.prop(props, "size_x")
            col.prop(props, "size_y")
            box.operator(LG_OT_fit_selection.bl_idname, icon='FULLSCREEN_ENTER')
            box.prop(props, "proportional")
            col = box.column()
            col.label(text="Scaling adds more features at the same size." if props.proportional
                      else "Shapes stay the same at any size.")

        header, box = layout.panel("lg_detail", default_closed=False)
        header.label(text="Detail Level")
        if box:
            row = box.row(align=True)
            row.prop(props, "detail", expand=True)
            res = nodes.input_socket(mod, "Ultra Resolution" if props.ultra else
                                     "Final Resolution" if props.final else "Preview Resolution").value
            size_x, size_y = props.size_x, props.size_y
            spacing = max(size_x, size_y) / res
            points = (round(size_x / spacing) + 1) * (round(size_y / spacing) + 1)
            box.label(text=f"A point every {spacing:.2f} m · {points / 1000:,.0f} k points")

        header, box = layout.panel("lg_water", default_closed=True)
        header.label(text="Water")  # label first, so it lines up with the other section titles (Mike)
        header.prop(props, "water", text="")
        if box:
            row = box.row()
            row.enabled = props.water
            row.prop(props, "water_level", slider=True)
            box.label(text="Plain water for now; full lake, sea and river shaders come with the materials", icon='INFO')

        header, box = layout.panel("lg_caves", default_closed=True)
        header.label(text="Caves")
        if box:
            box.prop(props, "cave_layout")
            col = box.column()
            col.enabled = props.cave_layout != 'NONE'
            col.prop(props, "cave_size")
            col.prop(props, "cave_x", slider=True)
            col.prop(props, "cave_y", slider=True)

        header, box = layout.panel("lg_masks", default_closed=True)
        header.label(text="Masks")
        if box:
            box.prop(props, "show_mask", text="Show")
            if props.show_mask != 'NONE':
                box.row(align=True).prop(props, "mask_colors", expand=True)
                box.label(text=dict((k, d) for k, _n, d in MASK_ITEMS)[props.show_mask])
                if props.show_mask in ('FLOW', 'WEAR', 'DEPOSIT') and not TYPES.get(_object_type_key(props), {}).get("erosion"):
                    box.label(text="This type has no erosion, so this mask is empty", icon='INFO')
                if props.show_mask == 'DEPTH' and not props.water:
                    box.label(text="Turn Water on to see the water depth", icon='INFO')

        header, box = layout.panel("lg_shape", default_closed=False)
        header.label(text="Shape")
        header.operator(LG_OT_reset_look.bl_idname, text="Reset", icon='LOOP_BACK')
        if box:
            recipe = TYPES.get(_object_type_key(props), {})
            if recipe.get("styles"):  # style first, then its parameters (Mike)
                box.prop(props, "style")
            col = box.column()
            for prop in ("height_m", "feature_m", "roughness_pct", "sharpness_pct"):
                if prop == "feature_m":  # named per type, with how many fit across (Mike: "hill density")
                    col.prop(props, prop, text=recipe.get("feature_label", "Feature Size"))
                    if recipe.get("feature_noun"):
                        col.label(text=f"About {props.feature_scale:.0f} {recipe['feature_noun']} across")
                    continue
                col.prop(props, prop, slider=prop.endswith("_pct"))
            for ctl in recipe.get("controls", ()):
                if "styles" not in ctl or props.style_key in ctl["styles"]:
                    box.prop(props, ctl["prop"], slider=True)
            if recipe.get("terraces"):
                col = box.column(align=True)
                col.prop(props, "terrace_strength", slider=True)
                if props.terrace_strength > 0:
                    col.prop(props, "terraces")
                    col.prop(props, "terrace_tilt", slider=True)
            if recipe.get("erosion"):
                box.prop(props, "erosion_amount", slider=True)
                if ob.name in _pending or ob.name in _jobs:  # so artists know the look is still coming (Mike)
                    box.label(text="Eroding... the eroded look follows in a moment", icon='TIME')
            row = box.row(align=True)
            row.prop(props, "seed")
            row.operator(LG_OT_randomize.bl_idname, text="Randomize", icon='FILE_REFRESH')

        header, box = layout.panel("lg_bake", default_closed=True)
        header.label(text="Bake")
        if box:
            box.label(text="A plain mesh to sculpt and edit; water becomes its own object")
            box.operator(LG_OT_bake.bl_idname, icon='MESH_GRID')


classes = (LG_ObjectProps, LG_OT_add_landscape, LG_OT_scale_size, LG_OT_pick_type, LG_OT_randomize, LG_OT_reset_look,
           LG_OT_fit_selection, LG_OT_preset_save, LG_OT_preset_load, LG_OT_preset_rename, LG_OT_preset_delete,
           LG_OT_bake, LG_OT_restore,
           LG_UL_landscapes, LG_PT_main)


def register():
    _load_type_items()
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Object.lg = PointerProperty(type=LG_ObjectProps)
    bpy.types.Scene.lg_index = IntProperty(default=-1, update=_select_listed)
    bpy.types.Scene.lg_type_key = StringProperty(name="Picked Type", default="")
    bpy.types.Scene.lg_preset = EnumProperty(name="Preset", description="Saved looks: pick one, then Load", items=_preset_enum)
    bpy.types.Scene.lg_type = EnumProperty(name="Landscape Type", description="What kind of landscape Add Landscape makes", items=_type_enum,
                                           get=_get_scene_type, set=_set_scene_type)
    bpy.types.Scene.lg_types_view = EnumProperty(name="View", items=(
        ('LIST', "List", "Show all types as a list", 'LONGDISPLAY', 0),
        ('GRID', "Grid", "Show all types as thumbnails", 'IMGDISPLAY', 1)))
    bpy.app.handlers.load_post.append(_on_load)
    bpy.app.timers.register(_refresh_all, first_interval=0.1)  # landscapes already open when enabled


def unregister():
    if _on_load in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_on_load)
    del bpy.types.Scene.lg_types_view
    del bpy.types.Scene.lg_preset
    del bpy.types.Scene.lg_type
    del bpy.types.Scene.lg_type_key
    del bpy.types.Scene.lg_index
    del bpy.types.Object.lg
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    bpy.utils.previews.remove(_previews)

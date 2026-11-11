# SPDX-License-Identifier: GPL-3.0-or-later
"""Export a landscape as a .kblandscape package (docs/PACKAGE.md, LG-023, D206): recipe.json, a 16-bit
heightmap, one 16-bit image per mask, and optionally a raw 16-bit heightmap for Unity."""

import json
import os

import bpy
import numpy as np

from . import presets

SIZES = (1009, 2017, 4033)  # Unreal-friendly; 2017 is the default (D206)
MASKS = ("lg_height", "lg_slope", "lg_curvature", "lg_flow", "lg_wear", "lg_deposit", "lg_depth")


def top_grid(me, size_x, size_y):
    """The landscape's top surface as a regular grid: (heights, {mask: grid}), row 0 at -Y, column 0 at -X.
    The base's sides and bottom (lg_base) and the water sheet (lg_water) are not heights (PACKAGE.md)."""
    n = len(me.vertices)
    co = np.zeros(n * 3)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    keep = np.ones(n, bool)
    wet = me.attributes.get("lg_water")
    if wet is not None:
        w = np.zeros(n, bool)
        wet.data.foreach_get("value", w)
        keep &= ~w
    base = me.attributes.get("lg_base")
    if base is not None:
        f = np.zeros(len(me.polygons), bool)
        base.data.foreach_get("value", f)
        loops = np.zeros(len(me.loops), np.int32)
        me.loops.foreach_get("vertex_index", loops)
        starts = np.zeros(len(me.polygons), np.int32)
        me.polygons.foreach_get("loop_start", starts)
        totals = np.zeros(len(me.polygons), np.int32)
        me.polygons.foreach_get("loop_total", totals)
        on_base = np.repeat(f, totals)
        low = np.zeros(n, bool)
        low[loops[on_base]] = True
        top = np.zeros(n, bool)
        top[loops[~on_base]] = True
        keep &= top | ~low  # border points are shared with the sides: they stay
    idx = np.nonzero(keep)[0]
    xs, ys = co[idx, 0], co[idx, 1]
    nx = len(np.unique(np.round(xs, 4)))
    ny = len(np.unique(np.round(ys, 4)))
    ix = np.clip(np.round((xs + size_x / 2) / size_x * (nx - 1)).astype(int), 0, nx - 1)
    iy = np.clip(np.round((ys + size_y / 2) / size_y * (ny - 1)).astype(int), 0, ny - 1)
    h = np.zeros((ny, nx))
    h[iy, ix] = co[idx, 2]
    masks = {}
    for name in MASKS:
        a = me.attributes.get(name)
        if a is None or a.domain != 'POINT':
            continue
        v = np.zeros(n)
        a.data.foreach_get("value", v)
        g = np.zeros((ny, nx))
        g[iy, ix] = v[idx]
        masks[name] = g
    return h, masks


def resample(g, size):
    """Bilinear, corners on corners (pixel centres on the grid's ends, PACKAGE.md)."""
    ny, nx = g.shape
    y = np.linspace(0, ny - 1, size)
    x = np.linspace(0, nx - 1, size)
    y0 = np.minimum(np.floor(y).astype(int), ny - 2)
    x0 = np.minimum(np.floor(x).astype(int), nx - 2)
    fy, fx = (y - y0)[:, None], (x - x0)[None, :]
    a = g[y0][:, x0]
    b = g[y0][:, x0 + 1]
    c = g[y0 + 1][:, x0]
    d = g[y0 + 1][:, x0 + 1]
    return a * (1 - fy) * (1 - fx) + b * (1 - fy) * fx + c * fy * (1 - fx) + d * fy * fx


def save_png16(values01, filepath):
    """A 0-1 grid as a 16-bit grayscale PNG (row 0 = bottom, as Blender stores pixels)."""
    size = values01.shape[0]
    img = bpy.data.images.new("lg_export", size, size, alpha=False, float_buffer=True, is_data=True)
    try:
        px = np.repeat(np.clip(values01, 0.0, 1.0).astype(np.float32).reshape(-1, 1), 4, axis=1)
        px[:, 3] = 1.0
        img.pixels.foreach_set(px.ravel())
        img.filepath_raw = filepath
        img.file_format = 'PNG'
        scene = bpy.context.scene
        settings = scene.render.image_settings
        old = (settings.file_format, settings.color_mode, settings.color_depth)
        settings.file_format, settings.color_mode, settings.color_depth = 'PNG', 'BW', '16'
        try:
            img.save_render(filepath, scene=scene)
        finally:
            settings.file_format, settings.color_mode, settings.color_depth = old
    finally:
        bpy.data.images.remove(img)


def write_package(ob, folder, recipe, size=2017, raw16=False, depsgraph=None):
    """Write <folder>/<object name>.kblandscape/ and return its path."""
    dg = depsgraph or bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    try:
        h, masks = top_grid(me, ob.lg.size_x, ob.lg.size_y)
    finally:
        ev.to_mesh_clear()
    out = os.path.join(folder, f"{ob.name}.kblandscape")
    os.makedirs(out, exist_ok=True)
    lo, hi = float(h.min()), float(h.max())
    hs = resample(h, size)
    h01 = (hs - lo) / max(hi - lo, 1e-9)
    save_png16(h01, os.path.join(out, "height.png"))
    if raw16:  # Unity RAW: top row first, little-endian
        np.round(h01[::-1] * 65535).astype("<u2").tofile(os.path.join(out, "height.r16"))
    for name, g in masks.items():
        save_png16(resample(g, size), os.path.join(out, f"mask_{name[3:]}.png"))
    data = {
        "format": "kblandscape", "version": 1, "app": "blender",
        "units": "meters", "size": [ob.lg.size_x, ob.lg.size_y], "height_range": [lo, hi],
        "heightmap": {"file": "height.png", "size": size, "bits": 16},
        "masks": sorted(f"mask_{n[3:]}.png" for n in masks),
        "tiles": [{"grid": [0, 0], **recipe}],
    }
    with open(os.path.join(out, "recipe.json"), "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=1, sort_keys=True, default=str)
    return out

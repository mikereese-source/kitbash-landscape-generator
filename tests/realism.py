"""Realism check: compare each landscape type with real elevation data for its reference place.

Run:  blender -b --factory-startup --python tests/realism.py -- [DEM folder]
DEM folder default: E:/Projects/3D/Terrain Generator_Build/Terrain References/copernicus-glo30
(Copernicus GLO-30 tiles, 1 arc-second; see tiles.txt there). Writes tests/realism_report.json.

Measures, on the real window and on our landscape built at the same width:
  relief   - height range (1st-99th percentile) / width
  slope50  - median slope, degrees
  slope90  - 90th percentile slope, degrees
  hyps     - hypsometric integral: how much of the height sits high (0.5 = even; low = mostly lowland)
  rough    - small-scale roughness: std of (height - blurred height) / relief
"""

import json
import math
import os
import sys

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import kitbash_landscape_generator as lg  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
DEM_DIR = argv[0] if argv else r"E:/Projects/3D/Terrain Generator_Build/Terrain References/copernicus-glo30"

# type key -> (tile id in tiles.txt, centre lat, lon, window width km, our style)
PLACES = {
    "hills": ("hills", 4.0, None),
    "mountains": ("mountains", 10.0, None),
    "dunes": ("dunes", 3.0, ("dunes", "star")),  # Erg Chebbi is a star-dune erg; crescents are checked on White Sands lidar
    "cliffs": ("cliffs", 2.0, None),
    "canyon": ("canyon", 10.0, None),
    "mesa": ("mesa", 6.0, None),
    "badlands": ("badlands", 2.0, None),
    "volcanic": ("volcanic", 4.0, None),
    "volcano_strato": ("volcano_strato", 30.0, ("volcano", "strato")),
    "volcano_caldera": ("volcano_caldera", 15.0, ("volcano", "caldera")),
    "volcano_shield": ("volcano_shield", 40.0, ("volcano", "shield")),
    "volcano_cinder": ("volcano_cinder", 2.5, ("volcano", "cinder")),
    "craters": ("craters", 3.0, None),
    "glacial": ("glacial", 8.0, None),
    "riverbed": ("riverbed", 2.0, None),
}
ARC = 30.87  # meters per arc-second of latitude


def read_tiles():
    rows = {}
    with open(os.path.join(DEM_DIR, "tiles.txt"), encoding="utf-8") as fh:
        for line in fh:
            parts = line.split()
            if parts:
                rows[parts[0]] = (parts[1], float(parts[-2]), float(parts[-1]))
    return rows


def load_dem(tile):
    path = os.path.join(DEM_DIR, f"Copernicus_DSM_COG_10_{tile}_DEM", f"Copernicus_DSM_COG_10_{tile}_DEM.tif")
    if not os.path.exists(path):
        path = os.path.join(DEM_DIR, f"Copernicus_DSM_COG_10_{tile}_DEM.tif")
    img = bpy.data.images.load(path, check_existing=False)
    img.colorspace_settings.name = "Non-Color"
    w, h = img.size
    px = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    bpy.data.images.remove(img)
    return px.reshape(h, w, 4)[::-1, :, 0]  # Blender stores bottom row first; flip to north-up


def window(dem, tile, lat, lon, width_km):
    lat0 = int(tile[1:3]) * (1 if tile[0] == "N" else -1)
    lon0 = int(tile[8:11]) * (1 if tile[7] == "E" else -1)  # e.g. N46_00_W118_00
    h, w = dem.shape
    dx = ARC * math.cos(math.radians(lat)) * 3600 / w  # meters per pixel east-west
    dy = ARC * 3600 / h
    cx = (lon - lon0) * w
    cy = (lat0 + 1 - lat) * h
    hx = width_km * 500 / dx
    hy = width_km * 500 / dy
    x0, x1 = int(max(cx - hx, 0)), int(min(cx + hx, w))
    y0, y1 = int(max(cy - hy, 0)), int(min(cy + hy, h))
    return dem[y0:y1, x0:x1].astype(np.float64), dx, dy


def blur(a, k):
    k = max(int(k), 1)
    c = np.cumsum(np.cumsum(np.pad(a, k, mode="edge"), 0), 1)
    c = np.pad(c, ((1, 0), (1, 0)))
    n = 2 * k + 1
    s = c[n:, n:] - c[:-n, n:] - c[n:, :-n] + c[:-n, :-n]
    return s / (n * n)


def metrics(hgt, dx, dy):
    lo, hi = np.percentile(hgt, [1, 99])
    relief = hi - lo
    width = max(hgt.shape[1] * dx, hgt.shape[0] * dy)
    gy, gx = np.gradient(hgt, dy, dx)
    slope = np.degrees(np.arctan(np.hypot(gx, gy)))
    fine = hgt - blur(hgt, max(hgt.shape) / 40)
    return {
        "relief": round(float(relief / width), 4),
        "slope50": round(float(np.percentile(slope, 50)), 1),
        "slope90": round(float(np.percentile(slope, 90)), 1),
        "hyps": round(float((np.clip(hgt, lo, hi).mean() - lo) / max(relief, 1e-6)), 3),
        "rough": round(float(fine.std() / max(relief, 1e-6)), 4),
    }


def ours(type_key, style, width_m, real_shape):
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    scene = bpy.context.scene
    scene.cursor.location = (0, 0, 0)
    scene.lg_type = type_key
    bpy.ops.landscape.add()
    ob = bpy.context.view_layer.objects.active
    if style:
        ob.lg.style = style
    ob.lg.size_x = ob.lg.size_y = width_m
    ob.lg.final = True
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    ev.to_mesh_clear()
    co = co.reshape(-1, 3)
    # Mesh order, not sorted by x/y: rock grain pushes points sideways along the normal (D47).
    n = int(round(math.sqrt(len(co))))
    grid = co[:, 2].reshape(n, n)
    # Sample ours at the real data's spacing (~30 m): slope depends on point spacing.
    m = max(min(real_shape), 8)
    idx = np.linspace(0, n - 1, m).round().astype(int)
    grid = grid[np.ix_(idx, idx)]
    step = width_m / (m - 1)
    return metrics(grid, step, step)


lg.register()
tiles = read_tiles()
report = {}
for name, (tile_key, width_km, style) in PLACES.items():
    tile, lat, lon = tiles[tile_key]
    real_h, dx, dy = window(load_dem(tile), tile, lat, lon, width_km)
    real = metrics(real_h, dx, dy)
    type_key, st = style if style else (name, None)
    report[name] = {"width_km": width_km, "real": real, "ours": ours(type_key, st, width_km * 1000, real_h.shape)}
    print(name, report[name])

# T6 (auto): bands against the real data. Slope bands only where 30 m data resolves the
# landform; Cliffs and Badlands windows are not representative yet (half sea / flat prairie).
BANDS = {"relief": 0.30, "hyps": 0.15, "slope50": 0.5}
SLOPE_OK = {"hills", "mountains", "mesa", "volcano_strato", "volcano_caldera", "volcano_shield", "glacial"}
SKIP = {"cliffs", "craters"}  # craters are checked against the Moon instead (tests/moon_check.py, D46)
# D73, Mike at the M2 gate: waived after 8 realism passes; still measured and reported. Mesa: the 30 m
# reference tile has no true mesas (it passes Monument Valley at 1 m).
WAIVED = {"mesa": {"relief", "slope50"}, "volcanic": {"relief", "hyps"}}
failed = []
for name, row in report.items():
    if name in SKIP:
        continue
    real, got = row["real"], row["ours"]
    checks = [("relief", abs(got["relief"] - real["relief"]) / real["relief"] <= BANDS["relief"]),
              ("hyps", abs(got["hyps"] - real["hyps"]) <= BANDS["hyps"])]
    if name in SLOPE_OK:
        checks.append(("slope50", abs(got["slope50"] - real["slope50"]) / max(real["slope50"], 1) <= BANDS["slope50"]))
    bad = [k for k, ok in checks if not ok and k not in WAIVED.get(name, ())]
    row["t6"] = "PASS" if not bad else "FAIL: " + ", ".join(bad)
    print(f"T6 {name}: {row['t6']}")
    failed += bad and [name]

with open(os.path.join(HERE, "realism_report.json"), "w", encoding="utf-8") as fh:
    json.dump(report, fh, indent=1)
print("wrote realism_report.json")
print(f"T6: {len([r for r in report if r not in SKIP]) - len(failed)}/{len([r for r in report if r not in SKIP])} types within bands")
sys.exit(1 if failed else 0)

"""Close-range realism check (R3) against USGS 3DEP 1 m lidar.

Run:  blender -b --factory-startup --python tests/lidar_check.py -- [lidar folder]
Folder default: E:/Projects/3D/Terrain Generator_Build/Terrain References/usgs-3dep-1m
(tiles.txt there: "<type> <file> <lat> <lon> [any|sea|coast]"; file may be ../other-folder/x.tif). Writes tests/lidar_report.json and
docs/realism/lidar/*.png hillshades.

Both sides are 2048 points at the data's spacing (1 m lidar; ~3.4 m NOAA seabed); ours is built 2048 x spacing wide at Final.
  s1/s8/s64 - roughness at 1, 8 and 64 m: rms height change over that distance / the 512 m value
  h_small   - how roughness grows from 1 to 16 m (Hurst; ~0.5-0.9 for real rock and soil)
  h_mid     - the same from 16 to 256 m
  slope50/90 at 1 m
  spikes    - worst bump of the radial spectrum (4-128 m) above its smooth trend, in dB (stripes, repeats)
  streaks   - fine detail (2-20 m) concentrated in one direction: strongest of 12 directions / mean
"""

import json
import math
import os
import struct
import sys

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import kitbash_landscape_generator as lg  # noqa: E402
sys.path.insert(0, HERE)
from terrain_structure import structure  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ONLY = argv[argv.index("--only") + 1].split(",") if "--only" in argv else None  # e.g. --only mountains,dunes
argv = [a for i, a in enumerate(argv) if a != "--only" and (i == 0 or argv[i - 1] != "--only")]
SRC = argv[0] if argv else r"E:/Projects/3D/Terrain Generator_Build/Terrain References/usgs-3dep-1m"
OUT = os.path.join(os.path.dirname(HERE), "docs", "realism", "lidar")
os.makedirs(OUT, exist_ok=True)
WIN = 2048
STYLES = {"volcano_cinder": ("volcano", "cinder"), "volcano_strato": ("volcano", "strato"),
          "volcano_caldera": ("volcano", "caldera")}


def geo_tags(path):
    """Upper-left corner (UTM m) and pixel size from the GeoTIFF tie point and scale tags."""
    with open(path, "rb") as fh:
        head = fh.read(8)
        e = "<" if head[:2] == b"II" else ">"
        fh.seek(struct.unpack(e + "I", head[4:])[0])
        tags = {}
        for _ in range(struct.unpack(e + "H", fh.read(2))[0]):
            tag, typ, cnt, val = struct.unpack(e + "HHI4s", fh.read(12))
            if tag in (33550, 33922) and typ == 12:
                here = fh.tell()
                fh.seek(struct.unpack(e + "I", val)[0])
                tags[tag] = struct.unpack(e + "d" * cnt, fh.read(8 * cnt))
                fh.seek(here)
    tie, scale = tags[33922], tags[33550]
    return tie[3], tie[4], scale[0], scale[1]


def utm(lat, lon, zone):
    """WGS84 lat/lon to UTM easting/northing (northern hemisphere)."""
    a, f, k0 = 6378137.0, 1 / 298.257223563, 0.9996
    e2 = f * (2 - f)
    ep2 = e2 / (1 - e2)
    phi, lam = math.radians(lat), math.radians(lon)
    lam0 = math.radians(zone * 6 - 183)
    n = a / math.sqrt(1 - e2 * math.sin(phi) ** 2)
    t, c = math.tan(phi) ** 2, ep2 * math.cos(phi) ** 2
    A = math.cos(phi) * (lam - lam0)
    m = a * ((1 - e2 / 4 - 3 * e2 ** 2 / 64 - 5 * e2 ** 3 / 256) * phi
             - (3 * e2 / 8 + 3 * e2 ** 2 / 32 + 45 * e2 ** 3 / 1024) * math.sin(2 * phi)
             + (15 * e2 ** 2 / 256 + 45 * e2 ** 3 / 1024) * math.sin(4 * phi)
             - (35 * e2 ** 3 / 3072) * math.sin(6 * phi))
    x = k0 * n * (A + (1 - t + c) * A ** 3 / 6 + (5 - 18 * t + t * t + 72 * c - 58 * ep2) * A ** 5 / 120) + 500000
    y = k0 * (m + n * math.tan(phi) * (A * A / 2 + (5 - t + 9 * c + 4 * c * c) * A ** 4 / 24
                                       + (61 - 58 * t + t * t + 600 * c - 330 * ep2) * A ** 6 / 720))
    return x, y


def real_window(name, lat, lon, rule="any"):
    """A WIN x WIN window near the place, resampled square. Returns (heights, meters per point, missing share).
    rule: "any" least missing data; "sea" mostly shelf; "coast" about half land (cliffs);
    "rim" about half flat top (canyon); "steep" the steepest, densest part (badlands); "exact" centred on
    the place, no search (picked by eye from a whole-tile view: Riverbed's channel, Mesa's buttes, Pass 2);
    "whole" the whole feature: 4 x 4 m averaged to one point, 8 km across, centred on the place (volcanoes:
    a 2 km window only saw one flank while ours showed the whole cone, Pass 2)."""
    path = os.path.join(SRC, name)
    x0, y0, sx, sy = geo_tags(path)
    geographic = sx < 0.01  # NOAA CUDEM is in degrees; USGS 3DEP is UTM meters
    if geographic:
        px0, py0 = int((lon - x0) / sx), int((y0 - lat) / sy)
        step_y, step_x = sy * 111320.0, sx * 111320.0 * math.cos(math.radians(lat))
    else:
        ex, ny = utm(lat, lon, int(name.split("_")[2]))
        px0, py0 = int((ex - x0) / sx), int((y0 - ny) / sy)
        step_y = step_x = sy
    img = bpy.data.images.load(path, check_existing=False)
    img.colorspace_settings.name = "Non-Color"
    w, h = img.size
    px = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    bpy.data.images.remove(img)
    dem = px.reshape(h, w, 4)[::-1, :, 0]
    del px
    if rule == "whole":
        k = 4
        half = WIN * k // 2
        cx, cy = min(max(px0, half), w - half), min(max(py0, half), h - half)
        win = dem[cy - half:cy + half, cx - half:cx + half].astype(np.float64)
        bad = win < -1e4
        win[bad] = np.median(win[~bad])
        win = win.reshape(WIN, k, WIN, k).mean(axis=(1, 3))
        return win, step_y * k, float(bad.mean())
    half_y = WIN // 2
    half_x = int(round(half_y * step_y / step_x))  # more columns when they are narrower than rows
    best = None
    reach = 0 if rule == "exact" else 3
    for dy in range(-reach * half_y, reach * half_y + 1, half_y // 2):
        for dx in range(-reach * half_x, reach * half_x + 1, half_x // 2):
            cx = min(max(px0 + dx, half_x), w - half_x)
            cy = min(max(py0 + dy, half_y), h - half_y)
            a = dem[cy - half_y:cy + half_y:16, cx - half_x:cx + half_x:16]
            ok = a > -1e4
            miss = float(1 - ok.mean())
            if rule == "sea":  # continental shelf: 8-120 m deep, not a submarine canyon
                fit = 1 - float(((a < -8) & (a > -120) & ok).mean())
            elif rule in ("rim", "steep"):
                gy_, gx_ = np.gradient(np.where(ok, a, np.nan), 16 * step_y)
                flat_share = float(np.nanmean(np.hypot(gx_, gy_) < 0.15))
                # rim: about half flat top and half wall, like our Canyon; steep: the dense core
                fit = abs(flat_share - 0.45) if rule == "rim" else flat_share
                fit = fit if np.isfinite(fit) else 1.0
            elif rule == "coast":  # empty cells are sea in coastal lidar
                fit = abs(float(((a > 2) & ok).mean()) - 0.5)
            else:
                fit = 0.0
            key = (round(fit, 1), round(miss, 2), abs(dx) + abs(dy))
            if best is None or key < best[0]:
                best = (key, cx, cy)
    _, cx, cy = best
    win = dem[cy - half_y:cy + half_y, cx - half_x:cx + half_x].astype(np.float64)
    bad = win < -1e4
    if bad.any():
        # Coast tiles leave the sea empty: fill it flat at the lowest land, not at the middle.
        win[bad] = np.percentile(win[~bad], 1) if rule == "coast" else np.median(win[~bad])
    if win.shape[1] != WIN:  # resample columns so points are square
        xs = np.linspace(0, win.shape[1] - 1, WIN)
        i0 = np.floor(xs).astype(int)
        i1 = np.minimum(i0 + 1, win.shape[1] - 1)
        t = xs - i0
        win = win[:, i0] * (1 - t) + win[:, i1] * t
    return win, step_y, float(bad.mean())


def metrics(h, step=1.0):
    lags = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512]
    s = {L: math.sqrt(0.5 * (((h[:, L:] - h[:, :-L]) ** 2).mean() + ((h[L:] - h[:-L]) ** 2).mean())) for L in lags}
    fit = lambda a, b: float(np.polyfit(np.log(lags[a:b]), np.log([max(s[L], 1e-9) for L in lags[a:b]]), 1)[0])
    gy, gx = np.gradient(h, step)
    slope = np.degrees(np.arctan(np.hypot(gx, gy)))
    # Spectrum of the detrended, windowed field.
    yy, xx = np.mgrid[0:WIN, 0:WIN]
    A = np.c_[xx.ravel(), yy.ravel(), np.ones(h.size)]
    flat = h - (A @ np.linalg.lstsq(A, h.ravel(), rcond=None)[0]).reshape(h.shape)
    win = np.outer(np.hanning(WIN), np.hanning(WIN))
    P = np.abs(np.fft.fftshift(np.fft.fft2(flat * win))) ** 2
    ky, kx = np.mgrid[-WIN // 2:WIN // 2, -WIN // 2:WIN // 2]
    k = np.hypot(kx, ky)
    ring = np.round(k).astype(int)
    radial = np.bincount(ring.ravel(), P.ravel()) / np.maximum(np.bincount(ring.ravel()), 1)
    kk = np.arange(len(radial))
    sel = (kk >= 16) & (kk <= WIN // 4)  # 128 m down to 4 m: below the main shapes, so a peak means stripes
    logp = np.log10(radial[sel] + 1e-30)
    trend = np.polyval(np.polyfit(np.log10(kk[sel]), logp, 2), np.log10(kk[sel]))
    resid = logp - trend
    # Smooth over 5 rings so random scatter doesn't count; a real stripe stands out over several.
    resid = np.convolve(resid, np.ones(5) / 5, mode="same")
    band = (k >= WIN / 20) & (k <= WIN / 2)
    ang = (np.degrees(np.arctan2(ky, kx)) % 180)[band]
    bins = np.bincount((ang // 15).astype(int) % 12, P[band], minlength=12)
    s512 = max(s[512], 1e-9)  # a flat window (lake, sea) would divide by zero
    return {"s1": round(s[1] / s512, 4), "s8": round(s[8] / s512, 4), "s64": round(s[64] / s512, 3),
            "h_small": round(fit(0, 5), 2), "h_mid": round(fit(4, 9), 2),
            "slope50": round(float(np.percentile(slope, 50)), 1), "slope90": round(float(np.percentile(slope, 90)), 1),
            "spikes": round(float(resid.max() * 10), 1), "spike_m": round(WIN * step / float(kk[sel][np.argmax(resid)]), 1), "streaks": round(float(bins.max() / bins.mean()), 2),
            "relief": round(float(np.ptp(np.percentile(h, [1, 99]))), 1)}


def ours(type_key, style, width=float(WIN), relief_m=None):
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    bpy.context.scene.cursor.location = (0, 0, 0)
    bpy.context.scene.lg_type = type_key
    bpy.ops.landscape.add()
    ob = bpy.context.view_layer.objects.active
    if style:
        ob.lg.style = style
    ob.lg.size_x = ob.lg.size_y = width  # Final: 2048 points across, so the spacing is width / 2048
    if relief_m:  # whole-feature windows compare form, so ours gets the real relief (Height is the user's)
        ob.lg.height_m = relief_m
    ob.lg.final = True
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    ev.to_mesh_clear()
    n = int(round(math.sqrt(len(co) // 3)))
    return co[2::3].reshape(n, n)[:WIN, :WIN]  # mesh order: rock grain pushes points sideways (D47)


def hillshade_png(h, name, px=700):
    k = max(h.shape[0] // px, 1)
    a = h[::k, ::k]
    gy, gx = np.gradient(a, float(k))
    lit = np.clip((0.42 + 0.9 * (-gx * 0.6 + gy * 0.6)) / np.sqrt(1 + gx * gx + gy * gy), 0, 1)
    img = bpy.data.images.new(name, a.shape[1], a.shape[0])
    rgba = np.repeat(lit[::-1, :, None], 4, 2).astype(np.float32)
    rgba[..., 3] = 1
    img.pixels.foreach_set(rgba.ravel())
    img.filepath_raw = os.path.join(OUT, name + ".png")
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)


lg.register()
report = {}
with open(os.path.join(SRC, "tiles.txt"), encoding="utf-8") as fh:
    rows = [line.split() for line in fh if line.strip()]
for key, name, lat, lon, *opt in rows:
    if ONLY and key not in ONLY:
        continue
    real, step, missing = real_window(name, float(lat), float(lon), opt[0] if opt else "any")
    type_key, style = STYLES.get(key, (key, None))
    rule = opt[0] if opt else "any"
    mine = ours(type_key, style, WIN * step, float(np.ptp(real)) if rule == "whole" else None)
    report[key] = {"step_m": round(step, 2), "real": metrics(real, step), "ours": metrics(mine, step),
                   "real_structure": structure(real, step), "ours_structure": structure(mine, step),
                   "missing": round(missing, 3)}
    hillshade_png(real, f"real_{key}")
    hillshade_png(mine, f"ours_{key}")
    print(key, json.dumps(report[key]))

# T6b (auto): close-range bands against the 1 m (seabed 3 m) data. Relief is left out: it is the
# Height slider, so it depends on the user. Bands from the spread between real places (R3, D52).
def bands(real, got):
    bad = []
    if abs(got["slope50"] - real["slope50"]) > max(0.5 * real["slope50"], 2.0):
        bad.append("slope50")
    if abs(got["slope90"] - real["slope90"]) > max(0.35 * real["slope90"], 4.0):
        bad.append("slope90")
    if abs(got["h_mid"] - real["h_mid"]) > 0.2:
        bad.append("h_mid")
    if not 0.6 <= got["s64"] / max(real["s64"], 1e-6) <= 1.6:
        bad.append("s64")
    if got["spikes"] > real["spikes"] + 3.0:
        bad.append("spikes")
    return bad


# Waived until a later milestone, each with its decision. Still measured and reported.
WAIVED = {"canyon": {"h_mid"},  # D52: mid-scale (16-256 m) roughness is drainage, built with erosion in M3
          # D73, Mike at the M2 gate: waived after 8 realism passes; still measured and reported.
          "riverbed": {"spikes"}, "volcano_caldera": {"slope50", "s64", "spikes"}}
failed = []
for key, row in report.items():
    bad = [b for b in bands(row["real"], row["ours"]) if b not in WAIVED.get(key, ())]
    row["t6b"] = "PASS" if not bad else "FAIL: " + ", ".join(bad)
    print(f"T6b {key}: {row['t6b']}")
    failed += bad and [key]
print(f"T6b: {len(report) - len(failed)}/{len(report)} within close-range bands")

# T6c (structure, R5/D53): does it drain like real land? Reported now; it fails the run once the
# erosion engine is in (R7). Cliffs rough_split is skipped: the empty sea in its lidar is filled flat.
ENFORCE_STRUCTURE = False


def structure_bands(real, got, key):
    bad = []
    if got["pit_share"] > real["pit_share"] + 0.03:
        bad.append("pits")
    if real["concavity"] is not None and (got["concavity"] is None or abs(got["concavity"] - real["concavity"]) > 0.3):
        bad.append("concavity")
    if key != "cliffs" and abs(got["rough_split"] - real["rough_split"]) > 0.4:
        bad.append("rough_split")
    if not 0.6 <= got["drainage"] / max(real["drainage"], 1e-6) <= 1.6:
        bad.append("drainage")
    return bad


s_failed = []
for key, row in report.items():
    bad = structure_bands(row["real_structure"], row["ours_structure"], key)
    row["t6c"] = "PASS" if not bad else "FAIL: " + ", ".join(bad)
    print(f"T6c {key}: {row['t6c']}")
    s_failed += bad and [key]
print(f"T6c: {len(report) - len(s_failed)}/{len(report)} drain like the real place"
      + ("" if ENFORCE_STRUCTURE else " (report only until R7)"))
if ENFORCE_STRUCTURE:
    failed += s_failed

with open(os.path.join(HERE, "lidar_report_partial.json" if ONLY else "lidar_report.json"), "w", encoding="utf-8") as fh:
    json.dump(report, fh, indent=1)
print("wrote lidar_report.json")
sys.exit(1 if failed else 0)

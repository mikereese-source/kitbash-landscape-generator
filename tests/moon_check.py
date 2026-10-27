"""Crater realism check against LROC NAC elevation models of the Moon (2 m per point).

Run:  blender -b --factory-startup --python tests/moon_check.py -- [LROC folder] [out folder]
LROC folder default: E:/Projects/3D/Terrain Generator_Build/Terrain References/lroc-nac
(NAC_DTM_LINNECRATER, NAC_DTM_APOLLO14, NAC_DTM_APOLLO16 .TIF from pds.lroc.im-ldi.com).

The same crater finder runs on real windows and on our Cratered Surface built at the same width,
so its misses and false hits are shared. Per field it reports:
  count/km2, size slope (cumulative N(>D) ~ D^slope), cover (crater area share),
  d/D (depth / rim diameter), rim/D (rim height above surroundings / diameter),
  wall (steepest inner wall, deg), flank (outer slope, deg), rimvar (rim height scatter / depth),
  hurst (roughness vs scale), skew (height skew after removing the trend), slope50/90.
Linne (fresh, 2.2 km) gets a full radial profile for the shape of one crater.
Writes moon_report.json and hillshade PNGs to the out folder.
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

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SRC = argv[0] if argv else r"E:/Projects/3D/Terrain Generator_Build/Terrain References/lroc-nac"
OURS_ONLY = "--ours-only" in argv  # skip the slow real-data pass while tuning
argv = [a for a in argv if a != "--ours-only"]
OUT = argv[1] if len(argv) > 1 else os.path.join(os.path.dirname(HERE), "docs", "realism", "moon")
os.makedirs(OUT, exist_ok=True)
STEP = 2.0  # meters per point in every NAC DTM used here
WIN = 1500  # 3 km windows


def read_tiff(path):
    """Memory-map an uncompressed, contiguous, single-band float32 TIFF (all NAC DTMs are)."""
    with open(path, "rb") as fh:
        head = fh.read(8)
        e = "<" if head[:2] == b"II" else ">"
        fh.seek(struct.unpack(e + "I", head[4:])[0])
        n = struct.unpack(e + "H", fh.read(2))[0]
        tags = {}
        for _ in range(n):
            tag, typ, cnt, val = struct.unpack(e + "HHI4s", fh.read(12))
            size = {3: 2, 4: 4}.get(typ, 0)
            if cnt * size <= 4 and size:
                tags[tag] = list(struct.unpack(e + {3: "H", 4: "I"}[typ] * cnt, val[:cnt * size]))
            elif size:
                here = fh.tell()
                fh.seek(struct.unpack(e + "I", val)[0])
                tags[tag] = list(struct.unpack(e + {3: "H", 4: "I"}[typ] * cnt, fh.read(cnt * size)))
                fh.seek(here)
    w, h = tags[256][0], tags[257][0]
    assert tags.get(259, [1])[0] == 1 and tags[258][0] == 32, "needs uncompressed float32"
    offs, counts = tags[273], tags[279]
    assert all(offs[i] + counts[i] == offs[i + 1] for i in range(len(offs) - 1)), "strips not contiguous"
    return np.memmap(path, dtype=np.dtype(e + "f4"), mode="r", offset=offs[0], shape=(h, w))


def valid_windows(dem, count):
    """Up to `count` WIN x WIN windows with no missing data, spread along the strip."""
    h, w = dem.shape
    found = []
    for y in range(0, h - WIN, WIN // 2):
        for x in range(0, max(w - WIN, 0) + 1, 100):
            a = np.asarray(dem[y:y + WIN, x:x + WIN])
            if a.shape == (WIN, WIN) and a.min() > -1e5:
                found.append(a.astype(np.float64))
                break
    pick = np.linspace(0, len(found) - 1, min(count, len(found))).round().astype(int)
    return [found[i] for i in sorted(set(pick))]


def gauss(a, s):
    if s < 0.5:
        return a
    pad = int(3 * s)
    p = np.pad(a, pad, mode="reflect")
    fy = np.fft.fftfreq(p.shape[0])[:, None]
    fx = np.fft.rfftfreq(p.shape[1])[None, :]
    g = np.exp(-2 * (math.pi * s) ** 2 * (fx * fx + fy * fy))
    return np.fft.irfft2(np.fft.rfft2(p) * g, p.shape)[pad:-pad or None, pad:-pad or None]


def ring_profile(h, cy, cx, radii, n_ang=48):
    ang = np.linspace(0, 2 * math.pi, n_ang, endpoint=False)
    ys = np.clip((cy + np.outer(radii, np.sin(ang))).round().astype(int), 0, h.shape[0] - 1)
    xs = np.clip((cx + np.outer(radii, np.cos(ang))).round().astype(int), 0, h.shape[1] - 1)
    return h[ys, xs]  # radii x angles


def find_craters(h):
    """Multi-scale Laplacian-of-Gaussian pits, refined by each pit's radial profile."""
    sigmas = np.geomspace(2.0, WIN / 12, 18)
    stack = []
    for s in sigmas:
        g = gauss(h, s)
        lap = np.roll(g, 1, 0) + np.roll(g, -1, 0) + np.roll(g, 1, 1) + np.roll(g, -1, 1) - 4 * g
        stack.append(lap * s * s / STEP)  # meters of implied depth
    stack = np.array(stack)
    cand = []
    for k in range(1, len(sigmas) - 1):
        r = stack[k]
        m = r > 0.01 * sigmas[k] * STEP
        for d in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
            m &= r >= np.roll(r, d, (0, 1))
        m &= (r >= stack[k - 1]) & (r >= stack[k + 1])
        for y, x in zip(*np.nonzero(m)):
            cand.append((r[y, x], y, x, sigmas[k] * math.sqrt(2)))
    cand.sort(reverse=True)
    kept, out = [], []
    for score, y, x, a0 in cand:
        if any((y - ky) ** 2 + (x - kx) ** 2 < (0.6 * max(a0, ka)) ** 2 and 0.5 < a0 / ka < 2
               for ky, kx, ka in kept):
            continue
        if not (2.6 * a0 < y < h.shape[0] - 2.6 * a0 and 2.6 * a0 < x < h.shape[1] - 2.6 * a0):
            continue
        kept.append((y, x, a0))
        radii = np.linspace(0, 2.5 * a0, 51)
        prof = ring_profile(h, y, x, radii)
        mean = prof.mean(1)
        band = (radii > 0.6 * a0) & (radii < 1.6 * a0)
        i_rim = np.nonzero(band)[0][np.argmax(mean[band])]
        R = radii[i_rim]
        floor = mean[radii <= 0.15 * R].mean()
        outer = mean[(radii >= 1.9 * R / 1.0) & (radii <= 2.4 * R)] if R * 2.4 <= radii[-1] else mean[-5:]
        surround = outer.mean() if outer.size else mean[-5:].mean()
        depth = mean[i_rim] - floor
        D = 2 * R * STEP
        if D < 8 or depth / D < 0.02:
            continue
        inner = np.diff(mean[: i_rim + 1]) / (radii[1] - radii[0]) / STEP
        r15 = np.argmin(abs(radii - 1.5 * R))
        rim_each = prof[max(i_rim - 3, 0): i_rim + 4].max(0)
        out.append({"D": D, "dD": depth / D, "rimD": (mean[i_rim] - surround) / D,
                    "wall": math.degrees(math.atan(inner.max())) if inner.size else 0.0,
                    "flank": math.degrees(math.atan(max(mean[i_rim] - mean[r15], 0) / (0.5 * R * STEP))),
                    "rimvar": float(rim_each.std() / max(depth, 1e-6))})
    return out


def field_metrics(h):
    yy, xx = np.mgrid[0:h.shape[0], 0:h.shape[1]]
    A = np.c_[xx.ravel(), yy.ravel(), np.ones(h.size)]
    flat = h - (A @ np.linalg.lstsq(A, h.ravel(), rcond=None)[0]).reshape(h.shape)
    gy, gx = np.gradient(h, STEP)
    slope = np.degrees(np.arctan(np.hypot(gx, gy)))
    lags = np.array([1, 2, 4, 8, 16, 32, 64, 128])
    rms = [math.sqrt(0.5 * (((h[:, L:] - h[:, :-L]) ** 2).mean() + ((h[L:] - h[:-L]) ** 2).mean())) for L in lags]
    hurst = np.polyfit(np.log(lags), np.log(rms), 1)[0]
    cr = find_craters(h)
    area = (h.shape[0] * STEP / 1000) ** 2
    Ds = np.sort([c["D"] for c in cr])[::-1]
    if len(Ds) >= 8:
        cum = np.arange(1, len(Ds) + 1)
        sel = (Ds >= 20) & (Ds <= 600)  # well sampled by a 3 km window at 2 m
        size_slope = float(np.polyfit(np.log(Ds[sel]), np.log(cum[sel]), 1)[0]) if sel.sum() > 5 else None
    else:
        size_slope = None

    def med(key, lo=0, hi=1e9):
        v = [c[key] for c in cr if lo <= c["D"] < hi]
        return round(float(np.median(v)), 3) if v else None

    return {"craters": len(cr), "per_km2": round(len(cr) / area, 1),
            "size_slope": size_slope and round(size_slope, 2),
            "cover": round(float(sum(math.pi * (c["D"] / 2) ** 2 for c in cr) / (area * 1e6)), 2),
            "dD_small": med("dD", 0, 100), "dD_big": med("dD", 100), "rimD": med("rimD"),
            "wall": med("wall"), "flank": med("flank"), "rimvar": med("rimvar"),
            "fresh_share": round(float(np.mean([c["dD"] > 0.12 for c in cr])), 2) if cr else None,
            "hurst": round(float(hurst), 2), "skew": round(float((flat ** 3).mean() / flat.std() ** 3), 2),
            "slope50": round(float(np.percentile(slope, 50)), 1), "slope90": round(float(np.percentile(slope, 90)), 1),
            "relief": round(float(np.ptp(np.percentile(h, [1, 99])) / (h.shape[0] * STEP)), 4)}


def linne_profile(dem):
    """Find Linne as the deepest smoothed pit; radial mean profile normalised by rim radius."""
    h, w = dem.shape
    coarse = np.asarray(dem[::8, ::8]).astype(np.float64)
    coarse[coarse < -1e5] = np.nan
    cy, cx = np.unravel_index(np.nanargmin(coarse), coarse.shape)
    cy, cx = cy * 8, cx * 8
    half = 2000
    y0, x0 = max(cy - half, 0), max(cx - half, 0)
    a = np.asarray(dem[y0:cy + half, x0:cx + half]).astype(np.float64)
    a[a < -1e5] = np.nan
    radii = np.linspace(0, 1900, 191)
    prof = ring_profile(a, cy - y0, cx - x0, radii, 96)
    mean = np.nanmean(prof, 1)
    i_rim = int(np.nanargmax(mean[:120]))
    R = radii[i_rim]
    far = np.nanmean(mean[radii > 3 * R]) if (radii > 3 * R).any() else np.nanmean(mean[-10:])
    floor = mean[0]
    D = 2 * R * STEP
    norm = [(round(float(r / R), 3), round(float((m - far) / D), 4)) for r, m in zip(radii, mean) if r <= 4 * R]
    rim_each = np.nanmax(prof[max(i_rim - 5, 0): i_rim + 6], 0)
    return {"D_m": round(D), "dD": round(float((mean[i_rim] - floor) / D), 3),
            "rimD": round(float((mean[i_rim] - far) / D), 3),
            "rimvar": round(float(np.nanstd(rim_each) / (mean[i_rim] - floor)), 3), "profile": norm}, a, cy - y0, cx - x0


def ours(set_props, width_m=2048 * STEP):
    """Build at Final (2049 points) so the spacing is exactly STEP, then crop the middle WIN."""
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    bpy.context.scene.cursor.location = (0, 0, 0)
    bpy.context.scene.lg_type = "craters"
    bpy.ops.landscape.add()
    ob = bpy.context.view_layer.objects.active
    ob.lg.size_x = ob.lg.size_y = width_m
    ob.lg.water = False  # terrain only: the water sheet's points aren't on the grid
    ob.lg.final = True
    for k, v in set_props.items():
        setattr(ob.lg, k, v)
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    ev.to_mesh_clear()
    co = co.reshape(-1, 3)
    n = int(round(math.sqrt(len(co))))  # mesh order: rock grain may push points sideways (D47)
    grid = co[:, 2].reshape(n, n)
    o = (n - WIN) // 2  # resampling to another spacing would duplicate rows and fake roughness
    return grid[o:o + WIN, o:o + WIN][::-1]


def hillshade_png(h, name, px=600):
    k = max(h.shape[0] // px, 1)
    a = np.nan_to_num(h[::k, ::k], nan=np.nanmean(h))
    gy, gx = np.gradient(a, STEP * k)
    az, alt = math.radians(315), math.radians(25)  # low sun, as in lunar images
    lit = (math.sin(alt) + math.cos(alt) * (gx * math.cos(az) - gy * math.sin(az) * -1)) / np.sqrt(1 + gx * gx + gy * gy)
    lit = np.clip(lit, 0, 1)
    img = bpy.data.images.new(name, a.shape[1], a.shape[0])
    rgba = np.repeat(lit[::-1, :, None], 4, 2).astype(np.float32)
    rgba[..., 3] = 1
    img.pixels.foreach_set(rgba.ravel())
    img.filepath_raw = os.path.join(OUT, name + ".png")
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)


lg.register()
report = {"real": {}, "ours": {}}
for site in () if OURS_ONLY else ("APOLLO14", "APOLLO16"):
    dem = read_tiff(os.path.join(SRC, f"NAC_DTM_{site}.TIF"))
    rows = []
    for i, win in enumerate(valid_windows(dem, 3)):
        rows.append(field_metrics(win))
        hillshade_png(win, f"real_{site.lower()}_{i}")
        print(site, i, rows[-1])
    report["real"][site] = rows

if not OURS_ONLY:
    lin, lin_a, ly, lx = linne_profile(read_tiff(os.path.join(SRC, "NAC_DTM_LINNECRATER.TIF")))
    report["real"]["LINNE"] = lin
    r = int(lin["D_m"] / STEP * 1.6)
    hillshade_png(lin_a[max(ly - r, 0):ly + r, max(lx - r, 0):lx + r], "real_linne")
    print("LINNE", {k: v for k, v in lin.items() if k != "profile"})

for name, props in (("default", {}), ("fresh", {"crater_age": 0.0}), ("old", {"crater_age": 1.0}),
                    ("dense", {"crater_count": 1.0}), ("variety1", {"crater_variety": 1.0})):
    g = ours(props)
    report["ours"][name] = field_metrics(g)
    hillshade_png(g, f"ours_{name}")
    print("OURS", name, report["ours"][name])

with open(os.path.join(OUT, "moon_report_ours.json" if OURS_ONLY else "moon_report.json"), "w", encoding="utf-8") as fh:
    json.dump(report, fh, indent=1)
print("wrote", os.path.join(OUT, "moon_report.json"))

# T6m (auto): our default Cratered Surface sits within the range of the six Apollo windows,
# widened by 20% (the windows themselves vary that much). Fresh share gets a 0.05 floor.
if not OURS_ONLY:
    rows = report["real"]["APOLLO14"] + report["real"]["APOLLO16"]
    got = report["ours"]["default"]
    bad = []
    for key in ("per_km2", "size_slope", "cover", "dD_small", "dD_big", "wall", "hurst", "skew",
                "slope50", "slope90", "fresh_share"):
        vals = [r[key] for r in rows if r[key] is not None]
        lo, hi = min(vals), max(vals)
        pad = 0.2 * max(abs(lo), abs(hi)) + (0.05 if key == "fresh_share" else 0.0)
        if not (lo - pad <= got[key] <= hi + pad):
            bad.append(f"{key} {got[key]} (Moon {lo}..{hi})")
    print("T6m craters vs Moon:", "PASS" if not bad else "FAIL: " + "; ".join(bad))
    sys.exit(1 if bad else 0)

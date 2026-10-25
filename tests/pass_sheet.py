"""Real vs ours review sheet from the lidar check's hillshades (docs/realism/lidar/real_*.png, ours_*.png).

Run:  blender -b --factory-startup --python tests/pass_sheet.py -- <out.png>
Two pairs per row, in tiles.txt order; each pair is real (left) | ours (right). No labels: the
pass write-up lists the order.
"""

import os
import sys

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
LID = os.path.join(os.path.dirname(HERE), "docs", "realism", "lidar")
SRC = r"E:/Projects/3D/Terrain Generator_Build/Terrain References/usgs-3dep-1m/tiles.txt"
out = sys.argv[sys.argv.index("--") + 1]
keys = [line.split()[0] for line in open(SRC, encoding="utf-8") if line.strip()]
S, GAP = 360, 8


def tile(path):
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    px = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    bpy.data.images.remove(img)
    a = px.reshape(h, w, 4)[..., 0]
    ys = (np.arange(S) * h / S).astype(int)
    xs = (np.arange(S) * w / S).astype(int)
    return a[np.ix_(ys, xs)]


rows = (len(keys) + 1) // 2
W = 2 * (2 * S + GAP) + 3 * GAP
H = rows * (S + GAP) + GAP
sheet = np.ones((H, W), dtype=np.float32) * 0.15
for i, k in enumerate(keys):
    r, c = divmod(i, 2)
    y = H - GAP - (r + 1) * (S + GAP) + GAP  # Blender images run bottom-up
    x = GAP + c * (2 * S + 2 * GAP)
    sheet[y:y + S, x:x + S] = tile(os.path.join(LID, f"real_{k}.png"))
    sheet[y:y + S, x + S + 2:x + 2 * S + 2] = tile(os.path.join(LID, f"ours_{k}.png"))
img = bpy.data.images.new("sheet", W, H)
rgba = np.repeat(sheet[:, :, None], 4, 2)
rgba[..., 3] = 1
img.pixels.foreach_set(rgba.ravel())
img.filepath_raw = out
img.file_format = "PNG"
img.save()
print("wrote", out, keys)

"""Structure measures for a height grid (R5, D53): does the land drain like real land?

Plain numpy, so the realism checks and (later) the erosion engine can share it.
  pit_share    - share of the ground sitting in closed pits deeper than 1 m (real land: near 0)
  drainage     - channel length per area, km/km2 (channel = more than 2 ha drains through it)
  concavity    - how slope falls with drainage area, S ~ A^-concavity (real rivers: ~0.3-0.7)
  rough_split  - rough bedrock next to smooth fill: log10 of local roughness p90 / p10
  trunk        - share of the area that drains through the single biggest channel (connection)
"""

import heapq
import math

import numpy as np

CELL = 4.0  # meters: flow is measured on a 4 m grid for every place, so results compare
CHANNEL_M2 = 2e4  # 2 ha: where hillslopes give way to channels
PIT_DEPTH = 1.0  # meters: shallower pits are micro-relief (rocks, plants, survey noise)
D8 = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


def resample(h, step):
    """Average down to CELL meters (never up)."""
    k = max(int(round(CELL / step)), 1)
    n = (h.shape[0] // k) * k
    m = (h.shape[1] // k) * k
    return h[:n, :m].reshape(n // k, k, m // k, k).mean(axis=(1, 3)), step * k


def fill(z):
    """Priority-flood depression filling with a tiny rise across flats, so every cell drains to the edge."""
    n, m = z.shape
    out = z.copy()
    done = np.zeros(z.shape, bool)
    heap = []
    for i in range(n):
        for j in (0, m - 1):
            heap.append((z[i, j], i, j))
            done[i, j] = True
    for j in range(1, m - 1):
        for i in (0, n - 1):
            heap.append((z[i, j], i, j))
            done[i, j] = True
    heapq.heapify(heap)
    eps = 1e-4
    while heap:
        h, i, j = heapq.heappop(heap)
        for di, dj in D8:
            a, b = i + di, j + dj
            if 0 <= a < n and 0 <= b < m and not done[a, b]:
                done[a, b] = True
                v = max(z[a, b], h + eps)
                out[a, b] = v
                heapq.heappush(heap, (v, a, b))
    return out


def receivers(z, cell):
    """Steepest-descent neighbor (flat index) and its slope for every cell; edge cells drain out (-1)."""
    n, m = z.shape
    best = np.zeros(z.shape)
    rcv = np.full(z.shape, -1, dtype=np.int64)
    idx = np.arange(n * m).reshape(n, m)
    pad = np.pad(z, 1, mode="edge")
    pidx = np.pad(idx, 1, mode="constant", constant_values=-1)
    for di, dj in D8:
        nb = pad[1 + di:1 + di + n, 1 + dj:1 + dj + m]
        s = (z - nb) / (cell * math.hypot(di, dj))
        better = s > best
        best = np.where(better, s, best)
        rcv = np.where(better, pidx[1 + di:1 + di + n, 1 + dj:1 + dj + m], rcv)
    rcv[0, :] = rcv[-1, :] = rcv[:, 0] = rcv[:, -1] = -1
    return rcv.ravel(), best.ravel()


def accumulate(z, rcv, cell):
    area = np.full(z.size, cell * cell)
    for i in np.argsort(z.ravel())[::-1]:  # highest first, so every cell is done before its receiver
        r = rcv[i]
        if r >= 0:
            area[r] += area[i]
    return area


def structure(h, step):
    z, cell = resample(np.asarray(h, dtype=np.float64), step)
    filled = fill(z)
    pit_share = float(((filled - z) > PIT_DEPTH).mean())
    rcv, slope = receivers(filled, cell)
    area = accumulate(filled, rcv, cell)
    channel = area > CHANNEL_M2
    drainage = float(channel.sum() * cell / 1000.0 / (z.size * cell * cell / 1e6))
    # Slope-area: channel slope averaged over 5 cells downstream (single-cell slopes are ~0 on any
    # flat stretch, a lake or a carved exit, and swamp the fit), median per log-area bin.
    zf = filled.ravel()
    down = np.arange(zf.size)
    length = np.zeros(zf.size)
    for _ in range(5):
        nxt = np.where(rcv[down] >= 0, rcv[down], down)
        step_len = np.where(nxt != down, cell * np.hypot(*np.divmod(np.abs(nxt - down), z.shape[1])).clip(1, 1.5), 0.0)
        length += step_len
        down = nxt
    slope = np.where(length > 0, (zf - zf[down]) / np.maximum(length, 1e-9), 0.0)
    sel = channel & (slope > 0)
    concavity = None
    if sel.sum() > 50:
        la, ls = np.log10(area[sel]), np.log10(slope[sel])
        edges = np.arange(math.log10(CHANNEL_M2), la.max(), 0.25)
        xs, ys = [], []
        for a, b in zip(edges[:-1], edges[1:]):
            inb = (la >= a) & (la < b)
            if inb.sum() >= 20:
                xs.append((a + b) / 2)
                ys.append(np.median(ls[inb]))
        if len(xs) >= 4:
            concavity = round(float(-np.polyfit(xs, ys, 1)[0]), 2)
    # Rough next to smooth: local roughness (residual from a 3x3 mean) over 5x5 patches.
    k = 1
    c = np.pad(np.cumsum(np.cumsum(np.pad(z, k, mode="edge"), 0), 1), ((1, 0), (1, 0)))
    w = 2 * k + 1
    mean = (c[w:, w:] - c[:-w, w:] - c[w:, :-w] + c[:-w, :-w]) / (w * w)
    resid = np.abs(z - mean)
    n5 = (resid.shape[0] // 5) * 5
    m5 = (resid.shape[1] // 5) * 5
    patch = resid[:n5, :m5].reshape(n5 // 5, 5, m5 // 5, 5).mean(axis=(1, 3)).ravel()
    p10, p90 = np.percentile(patch, [10, 90])
    rough_split = round(float(math.log10(max(p90, 1e-6) / max(p10, 1e-6))), 2)
    trunk = round(float(area.max() / (z.size * cell * cell)), 3)
    return {"pit_share": round(pit_share, 3), "drainage": round(drainage, 1), "concavity": concavity,
            "rough_split": rough_split, "trunk": trunk}


if __name__ == "__main__":  # self-check on shapes with known answers
    y, x = np.mgrid[0:256, 0:256] / 255.0
    bowl = ((x - 0.5) ** 2 + (y - 0.5) ** 2) * 400.0  # one big closed pit
    s = structure(bowl, 4.0)
    assert s["pit_share"] > 0.5, s
    cone = -np.hypot(x - 0.5, y - 0.5) * 400.0  # drains outward, no pits
    s = structure(cone, 4.0)
    assert s["pit_share"] == 0.0, s
    print("terrain_structure self-check OK")

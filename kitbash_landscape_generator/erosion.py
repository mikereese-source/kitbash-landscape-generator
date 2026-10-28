"""Erosion engine (R6, D53/D54): water carves, sediment settles, slopes soften, loose rock slumps.

Plain numpy, no Blender: the three.js version ports this file as-is (same steps, same settings
from types.json). Works in landscape-relative units (heights and spacing divided by the landscape's
size), so a 10 m and a 1 km landscape erode the same way and keep their big shapes (D3).

One call, erode(h, settings), returns the eroded heights. Steps per pass:
  1. flow routing: each cell drains to its steepest downhill neighbor (pits filled first)
  2. stream-power incision, solved implicitly so big steps stay stable (Braun & Willett 2013)
  3. sediment: carried downstream, dropped where the flow can't hold it (fans, valley fill)
  4. hillslope softening (diffusion)
  5. talus: rock steeper than its resting angle slides down
"""

import heapq
import math

import numpy as np

D8 = ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1))
DIST = np.array([math.hypot(a, b) for a, b in D8])

DEFAULTS = {
    "passes": 30,        # rise + incision/sediment/softening rounds
    "incision": 3.0,     # how hard water cuts against the land rising (about 1-4; implicit, so stable)
    "m": 0.5,            # drainage-area exponent (concavity m/n, real rivers ~0.5)
    "deposit": 0.1,      # how readily carried sediment settles where slopes flatten
    "soften": 0.2,       # hillslope diffusion
    "soften_rounds": 4,  # diffusion steps per pass: more = wider valley spacing
    "talus_deg": 35.0,   # resting angle of loose rock (scree spreads down to it)
    "cliff_deg": 70.0,   # steepest bedrock stands (walls cut steeper fall back to it)
    "start": 1.0,        # share of the shape present before it starts rising and eroding
    "rise_blur": 0.03,   # the land rises by the shape blurred over this share of its width
    "uplift": 0.2,       # even rise against the fixed edges, as a share of the relief
    "edge_lift": False,
    "keep_detail": 1.0,  # how much of the shape's fine detail returns on slopes and ridges after smoothing
    "edge_blend": 0.03,  # the result fades back to the plain shape over this share of the width at the border
    "edge_fade": 0.0,    # the rise fades out over this share of the width at the border
    "exit_slope": 0.02,  # breached exits fall this much per cell (~1 deg) so trunks aren't flat
    "floor_slope": 0.0,  # filled basins slope toward their outlet (0: flat; above 0 the fill makes geometric ramps)
    "channel": 0.0005,   # share of the landscape that must drain through a cell before water cuts it;
                         # above it channels incise, below it hillslopes stay smooth and rounded
    "final_slump": 20,   # talus rounds after the last pass
    "protect": 4.0,      # channels this many times the cutting threshold shed hillslope debris (rills below fill in)
    "floor_width": 16,   # rounds of channel-floor widening at the end (cells)
    "finish_blur": 16,   # rounds of smoothing at the very end (rounds off one-cell stair steps; dams are cut after)
    "floor_carve": 2,    # channels are at least this many cells either side of their bed...
    "bank_deg": 25.0,    # ...with banks no steeper than this
    "floor_from": 1e-5,  # share of the landscape draining through a channel before its floor widens
    "slump_every_pass": 4,  # talus rounds per pass, so incised trenches widen into V valleys
    "target_pits": "fill",  # the shape's own basins: fill (lakes) or breach (cut a flat exit; trunks came out flat)
    "pit_mode": "fill",  # pits that form while it grows: breach (cut an exit) or fill (flat lake)
    "sea_level": 0.0,    # share of the relief below which ground is sea (0 = no sea)
    "lean": 0.0,         # hilltops lean downwind by this share of the width at full height: one steep
                         # side, one long gentle side, like wind-built Palouse loess hills (0 = even)...
    "lean_axis": 1,      # ...along X (1) or Y (0)
    "apron": 0.0,        # talus aprons below hard caprock reach this share of the width out (0 = none)...
    "apron_rise": 0.5,   # ...and climb this share of the cliff height up its foot
    "min_cap": 0.0,      # caprock narrower than this share of the width breaks off into talus (thin fins; 0 = keep)...
    "fin_tol": 0.06,     # ...and spurs that narrow standing more than this share of the relief proud are cut down
    "pediment": 0.0,     # beyond the apron the floor still falls away from the caprock, this share of the cliff
                         # height over four apron reaches, so the floor drains to washes between the blocks
    "hardness": 0.4,     # how much rock hardness varies from place to place (0 = even); harder patches
                         # cut slower, so channels wander, branch and bunch instead of running in rows
    "meander": 0.6,      # fixed, smooth bias on which downhill neighbor water picks (0 = none, ~1 strong):
                         # rills curve and merge instead of following the grid in straight rows
    "jitter": 0.5,       # random nudge to water routing, so channels branch instead of running parallel
    "seed": 0,
    "fill_every": 1000,  # full pit passes are slow; pits pass their water on every pass anyway
}


def fill(z, slope=0.0):
    """Priority-flood: every cell drains to the edge. Filled ground rises by `slope` per cell away
    from the spill point (0 = a flat lake; a little = a valley floor sloping to its outlet)."""
    n, m = z.shape
    out = z.copy()
    done = np.zeros(z.shape, bool)
    done[0, :] = done[-1, :] = done[:, 0] = done[:, -1] = True
    edge = np.argwhere(done)
    heap = [(z[i, j], i, j) for i, j in edge]
    heapq.heapify(heap)
    eps = max(1e-7, slope)
    while heap:
        h, i, j = heapq.heappop(heap)
        for di, dj in D8:
            a, b = i + di, j + dj
            if 0 <= a < n and 0 <= b < m and not done[a, b]:
                done[a, b] = True
                v = z[a, b] if z[a, b] > h + eps else h + eps
                out[a, b] = v
                heapq.heappush(heap, (v, a, b))
    return out


def breach(z, slope=0.0):
    """Drain every pit by carving the cheapest way out, the way a river cuts through a basin's rim,
    instead of filling it into a flat lake. Priority-flood from the edges; a cell lower than the
    cell that reached it keeps its height, and the path back to the outlet is lowered to run downhill,
    falling `slope` per cell (0 = flat trench; a little = an exit channel with a real gradient)."""
    n, m = z.shape
    out = z.ravel().copy()
    parent = np.full(n * m, -1, dtype=np.int64)
    done = np.zeros(n * m, bool)
    heap = []
    for i in range(n):
        for j in range(m):
            if i in (0, n - 1) or j in (0, m - 1):
                k = i * m + j
                done[k] = True
                heap.append((out[k], k))
    heapq.heapify(heap)
    eps = max(1e-7, slope)
    while heap:
        h, k = heapq.heappop(heap)
        i, j = divmod(k, m)
        for di, dj in D8:
            a, b = i + di, j + dj
            if 0 <= a < n and 0 <= b < m:
                q = a * m + b
                if done[q]:
                    continue
                done[q] = True
                parent[q] = k
                if out[q] <= out[k]:  # q sits in a pit: carve the path out instead of filling q
                    c, p = q, k
                    while p >= 0 and out[p] >= out[c] - eps:
                        out[p] = out[c] - eps
                        c, p = p, parent[p]
                heapq.heappush(heap, (out[q], q))
    return out.reshape(n, m)


def routing(z, dx, rng=None, jitter=0.0, bias=None, outlet=None):
    """Steepest-descent receiver (flat index, -1 = drains off the edge) and the distance to it.
    jitter scales each downhill slope by a random factor before picking, so among near-equal
    neighbors the choice varies (branching, not parallel rills); it never turns uphill into downhill."""
    n, m = z.shape
    idx = np.arange(n * m).reshape(n, m)
    pad = np.pad(z, 1, mode="edge")
    pidx = np.pad(idx, 1, mode="constant", constant_values=-1)
    best = np.zeros(z.shape)
    rcv = np.full(z.shape, -1, dtype=np.int64)
    dist = np.full(z.shape, dx)
    for k, (di, dj) in enumerate(D8):
        s = (z - pad[1 + di:1 + di + n, 1 + dj:1 + dj + m]) / (dx * DIST[k])
        if jitter > 0:
            s = s * (1.0 + jitter * rng.random(s.shape))
        if bias is not None:
            s = s * bias[k]
        better = s > best
        best = np.where(better, s, best)
        rcv = np.where(better, pidx[1 + di:1 + di + n, 1 + dj:1 + dj + m], rcv)
        dist = np.where(better, dx * DIST[k], dist)
    # A pit (no lower neighbor) passes its water to its lowest neighbor instead of keeping it;
    # incision then raises it to that neighbor's height, so lakes fill and spill every pass
    # (water stranded in pits left trunk valleys uncut and the final fill flooded them flat).
    low = np.full(z.shape, np.inf)
    low_idx = np.full(z.shape, -1, dtype=np.int64)
    low_dist = np.full(z.shape, dx)
    for k, (di, dj) in enumerate(D8):
        nb = pad[1 + di:1 + di + n, 1 + dj:1 + dj + m]
        lower = nb < low
        low = np.where(lower, nb, low)
        low_idx = np.where(lower, pidx[1 + di:1 + di + n, 1 + dj:1 + dj + m], low_idx)
        low_dist = np.where(lower, dx * DIST[k], low_dist)
    pit = (rcv < 0) & (low_idx >= 0)
    rcv = np.where(pit, low_idx, rcv)
    dist = np.where(pit, low_dist, dist)
    rcv[0, :] = rcv[-1, :] = rcv[:, 0] = rcv[:, -1] = -1
    if outlet is not None:  # the sea: water reaching it leaves the landscape
        rcv[outlet] = -1
    return rcv.ravel(), dist.ravel()


def blur(a, k):
    """Three box blurs of radius k (about a Gaussian)."""
    for _ in range(3):
        c = np.pad(np.cumsum(np.cumsum(np.pad(a, k, mode="edge"), 0), 1), ((1, 0), (1, 0)))
        w = 2 * k + 1
        a = (c[w:, w:] - c[:-w, w:] - c[w:, :-w] + c[:-w, :-w]) / (w * w)
    return a


def hardness_field(shape, rng, amount):
    """Erodibility multiplier, 1 on average: smooth random patches from ~2% to ~25% of the width."""
    if amount <= 0:
        return np.ones(shape)
    f = np.zeros(shape)
    for share in (0.02, 0.06, 0.25):
        g = blur(rng.standard_normal(shape), max(int(share * max(shape) / 2), 1))
        f += g / max(g.std(), 1e-12)
    return np.exp(amount * f / f.std())


def levels(rcv):
    """Cells grouped from ridge tops (no donors) down to outlets: every cell comes after all its donors."""
    n = rcv.size
    has = rcv >= 0
    donors = np.bincount(rcv[has], minlength=n)
    front = np.flatnonzero(donors == 0)
    out = []
    while front.size:
        out.append(front)
        r = rcv[front]
        r = r[r >= 0]
        if not r.size:
            break
        np.subtract.at(donors, r, 1)
        r = np.unique(r)
        front = r[donors[r] == 0]
    return out


def slump(z, talus, dx, rounds, cliff=None):
    """Talus: rock steeper than its resting angle slides to lower neighbors; nothing stands steeper
    than `cliff` (bedrock) above its lowest neighbor."""
    # Each round a cell sheds half its largest excess, split between its over-steep neighbors by how
    # much each is over (thermal erosion). A fixed 1/16 per neighbor took hundreds of rounds to bring
    # a cliff down to its resting angle, so slopes stayed 10-30 deg too steep (Pass 2).
    n, m = z.shape
    thr = [talus * dx * d for d in DIST]  # per direction, computed once (speed, Pass 4)
    ex = np.empty((8, n, m))
    for _ in range(rounds):
        p = np.pad(z, 1, mode="edge")
        for k, (di, dj) in enumerate(D8):
            np.subtract(z, p[1 + di:1 + di + n, 1 + dj:1 + dj + m], out=ex[k])
            ex[k] -= thr[k]
        np.maximum(ex, 0.0, out=ex)
        total = ex.sum(axis=0)
        share = 0.5 * ex.max(axis=0) / np.maximum(total, 1e-30)
        recv = np.zeros((n + 2, m + 2))  # what each cell receives; outward at the border is lost (gives 0 there)
        for k, (di, dj) in enumerate(D8):
            recv[1 + di:1 + di + n, 1 + dj:1 + dj + m] += ex[k] * share
        z = z - total * share + recv[1:-1, 1:-1]
    # Then cap at the bedrock angle: spreading alone moves debris one cell per many rounds, so walls
    # carved faster stood far too steep; past the cap it is carried off by the rivers below.
    for _ in range(rounds if cliff is not None else 0):
        p = np.pad(z, 1, mode="edge")
        z = np.minimum(z, np.min([p[1 + di:1 + di + n, 1 + dj:1 + dj + m] + cliff * dx * d
                                  for (di, dj), d in zip(D8, DIST)], axis=0))
    return z


def widen_floors(z, dx, rounds, low=1e-4):
    """Channels come out one cell wide; real valley floors are several. Smooth along the bigger
    channels, more where more water flows, so floors widen (and survive resampling)."""
    if rounds <= 0:
        return z
    n, m = z.shape
    rcv, dist = routing(z, dx)
    area = np.full(z.size, dx * dx)
    for lv in levels(rcv):
        r = rcv[lv]
        ok = r >= 0
        np.add.at(area, r[ok], area[lv][ok])
    a_rel = (area / (n * m * dx * dx)).reshape(n, m)
    w = np.clip(np.log10(np.maximum(a_rel, 1e-9) / low) / 2.0, 0.0, 1.0) * 0.24  # low -> 100x low of the landscape
    for _ in range(int(rounds)):
        p = np.pad(z, 1, mode="edge")
        # Lower only: banks come down to the floor, the bed never rises, so no channel gets blocked.
        z = np.minimum(z, z + w * (p[:-2, 1:-1] + p[2:, 1:-1] + p[1:-1, :-2] + p[1:-1, 2:] - 4 * z))
        # spread the weight one cell sideways each round, so the floor widens
        q = np.pad(w, 1, mode="edge")
        w = np.maximum(w, 0.8 * np.maximum.reduce([q[:-2, 1:-1], q[2:, 1:-1], q[1:-1, :-2], q[1:-1, 2:]]))
    return z


def wetness(z, channel):
    """0..1: 1 on channels and their floors a few cells either side, 0 on hillslopes."""
    n, m = z.shape
    dx = 1.0 / (max(n, m) - 1)
    rcv, _ = routing(z, dx)
    area = np.full(z.size, dx * dx)
    for lv in levels(rcv):
        r = rcv[lv]
        ok = r >= 0
        np.add.at(area, r[ok], area[lv][ok])
    wet = np.clip(np.log10(np.maximum(area / (n * m * dx * dx), 1e-12) / channel), 0.0, 1.0).reshape(n, m)
    return np.clip(blur(wet, 2) * 3.0, 0.0, 1.0)


def carve_floors(z, dx, rounds, bank_deg, low):
    """Lower the ground beside every channel to at most the channel plus a bank of `bank_deg`, out to
    `rounds` cells: channels come out several cells wide. One-cell channels broke into dams when the
    map was resampled to the mesh, and the trunks came out as flat lakes again (Pass 2)."""
    if rounds <= 0:
        return z
    n, m = z.shape
    rcv, _ = routing(z, dx)
    area = np.full(z.size, dx * dx)
    for lv in levels(rcv):
        r = rcv[lv]
        ok = r >= 0
        np.add.at(area, r[ok], area[lv][ok])
    chan = (area / (n * m * dx * dx)).reshape(n, m) > low
    f = np.where(chan, z, np.inf)
    rise = math.tan(math.radians(bank_deg)) * dx
    for _ in range(int(rounds)):  # all 8 neighbors at their true distance (4 left dashed, beaded lines)
        p = np.pad(f, 1, mode="constant", constant_values=np.inf)
        f = np.minimum(f, np.min([p[1 + di:1 + di + n, 1 + dj:1 + dj + m] + rise * d for (di, dj), d in zip(D8, DIST)], axis=0))
    return np.minimum(z, f)


def lean(z, share):
    """Shift each row downwind (+X) by `share` of the width times the height (0 at the lowest point, 1 at
    the highest): tops lean over, so downwind faces steepen and upwind slopes stretch out."""
    if share <= 0:
        return z
    n, m = z.shape
    hn = (z - z.min()) / max(float(np.ptp(z)), 1e-12)
    cols = np.arange(m, dtype=np.float64)
    src = cols[None, :] - share * m * hn
    return np.array([np.interp(src[r], cols, z[r]) for r in range(n)])


def _grow(m, r, shrink):
    """Binary erode (shrink) or dilate a mask by r cells, 8 neighbours per step."""
    n, k = m.shape
    for _ in range(int(r)):
        p = np.pad(m, 1, mode="edge")
        nb = [p[1 + di:1 + di + n, 1 + dj:1 + dj + k] for di, dj in D8]
        m = np.logical_and.reduce([m] + nb) if shrink else np.logical_or.reduce([m] + nb)
    return m


def _minmax(z, r, fn):
    n, k = z.shape
    for _ in range(int(r)):
        p = np.pad(z, 1, mode="edge")
        z = fn([z] + [p[1 + di:1 + di + n, 1 + dj:1 + dj + k] for di, dj in D8], axis=0)
    return z


def cut_fins(z, r, tol):
    """Lower ground that stands more than `tol` of the relief above a morphological opening of radius r:
    spurs and fins narrower than ~2r cells come down to rubble height (tol above their surroundings);
    anything wider, and every slope and valley, is untouched."""
    opened = _minmax(_minmax(z, r, np.min), r, np.max)
    cap = opened + tol * max(float(np.ptp(z)), 1e-12)
    return np.minimum(z, cap)


def break_thin_caps(z, hard, r):
    """Caprock narrower than 2r cells can't stand as a cliff: it breaks off and slumps (Mike: thin fins and
    strips along Mesa blocks). Those cells drop to the floor and lose their hardness, so the apron and erosion
    turn them into talus spurs; wide blocks are untouched (a morphological opening of the cap mask)."""
    cap = hard > 0.8
    thin = cap & ~_grow(_grow(cap, r, True), r, False)
    if not thin.any():
        return z, hard
    z = np.where(thin, float(z.min()) + 0.15 * (z - float(z.min())), z)  # a stub of rubble, not a hole
    return z, np.where(thin, 0.0, hard)


def apron(z, cap, reach, rise, pediment=0.0):
    """Concave talus aprons around caprock (`cap` True): ground within `reach` cells rises to `rise` of
    the caps' height at the cliff foot, falling to the floor at the edge of the reach, and a gentle
    `pediment` falls away over four reaches. Built from the distance to the nearest cap, so it hugs
    every block and has no creases (Mesa, Pass 6)."""
    if reach < 1 or not cap.any():
        return z
    n, m = z.shape
    base = float(z.min())
    top = float(np.percentile(z[cap], 90))
    d = np.where(cap, 0.0, np.inf)
    far = reach * (4 if pediment > 0 else 1)
    for _ in range(int(far)):  # chamfer distance, all 8 neighbors at their true distance
        p = np.pad(d, 1, mode="constant", constant_values=np.inf)
        d = np.minimum(d, np.min([p[1 + di:1 + di + n, 1 + dj:1 + dj + m] + dd for (di, dj), dd in zip(D8, DIST)], axis=0))
    t = np.clip(1.0 - d / reach, 0.0, 1.0)
    ped = pediment * np.clip(1.0 - d / far, 0.0, 1.0) ** 1.5
    return np.where(cap, z, np.maximum(z, base + (top - base) * rise * t ** 2) + (top - base) * ped)


def edge_lift(diff, edge):
    """A smooth field equal to `diff` on the edges and easing to nothing inside (Laplace relaxation
    on a coarse grid, then scaled up): a gentle tilt that leaves the valley network intact."""
    n, m = diff.shape
    k = 8
    cn, cm = (n - 1) // k + 1, (m - 1) // k + 1
    rows = np.linspace(0, n - 1, cn).round().astype(int)
    cols = np.linspace(0, m - 1, cm).round().astype(int)
    fixed = np.zeros((cn, cm), bool)
    fixed[0, :] = fixed[-1, :] = fixed[:, 0] = fixed[:, -1] = True
    val = np.where(fixed, diff[np.ix_(rows, cols)], 0.0)
    for _ in range(400):
        p = np.pad(val, 1, mode="edge")
        val = np.where(fixed, val, 0.25 * (p[:-2, 1:-1] + p[2:, 1:-1] + p[1:-1, :-2] + p[1:-1, 2:]))
    out = np.array([np.interp(np.arange(m), cols, r) for r in val])
    return np.array([np.interp(np.arange(n), rows, c) for c in out.T]).T


def erode(h, settings=None, hard=None, masks=False):
    """h: 2D heights, landscape-relative (height / size). hard: optional 0..1 hard rock from the recipe
    (cliff bands, caprock, crests): cuts slower, rests steeper, isn't softened. Returns eroded heights."""
    s = dict(DEFAULTS)
    s.update(settings or {})
    # Basins in the shape get an exit cut through their rim before it rises (filling made dead-flat
    # floors channels couldn't reach): real ranges don't start with closed pits, and growing into
    # one would rebuild it every pass. Slumping then widens each cut into a valley.
    h = np.asarray(h, dtype=np.float64)
    h = lean(h, s["lean"]) if s["lean_axis"] == 1 else lean(h.T, s["lean"]).T  # first, so fine detail matches
    target = h
    n0 = max(target.shape)
    if s["min_cap"] > 0 and hard is not None:
        target, hard = break_thin_caps(target, np.asarray(hard, dtype=np.float64), max(int(round(s["min_cap"] * n0 / 2)), 1))
    if s["apron"] > 0 and hard is not None:
        target = apron(target, np.asarray(hard) > 0.8, s["apron"] * n0, s["apron_rise"], s["pediment"])
    target = (fill(target, s["floor_slope"] / (n0 - 1)) if s["target_pits"] == "fill"
              else breach(target, s["exit_slope"] / (n0 - 1)))
    # The shape is grown, not filled: it rises a little each pass while water cuts it, the way real
    # ranges form, so basins drain as they grow instead of becoming flat lakes.
    base = target.min()
    z = base + (target - base) * s["start"]
    # The land rises broadly (the shape, blurred over `rise_blur` of its width) and rivers cut the
    # valleys: rising by the detailed shape gave valley floors no uplift, so they came out dead flat.
    broad = blur(target, max(int(s["rise_blur"] * max(target.shape)), 1))
    rise = np.maximum(broad - base, 0.0) * (1.0 - s["start"]) / max(int(s["passes"]), 1)
    # Plus an even rise of `uplift` (share of the relief over the run) against the fixed edges:
    # this is what keeps channels sloping (steady state S ~ U / (K A^m)).
    rise = rise + s["uplift"] * max(float(np.ptp(target)), 1e-9) / max(int(s["passes"]), 1)
    # The edges are where rivers leave the landscape: held fixed (base level), so the inside rises
    # against them and channels get the slope they need. With the edges rising too, nothing ever
    # had a reason to cut and valleys came out dead flat.
    edge = np.zeros(target.shape, bool)
    edge[0, :] = edge[-1, :] = edge[:, 0] = edge[:, -1] = True
    rise[edge] = 0.0  # edges stay put: they're where rivers leave
    # Below `sea_level` (share of the relief) is sea: base level like the edges, so runoff ends at the
    # shore instead of cutting trenches across a wave-cut platform (Cliffs, Pass 2).
    sea = (target <= base + s["sea_level"] * np.ptp(target)) if s["sea_level"] > 0 else None
    if sea is not None:
        rise[sea] = 0.0
    # Fade the rise out over the outer `edge_fade` of the width, so the border doesn't step.
    yy, xx = np.mgrid[0:target.shape[0], 0:target.shape[1]]
    d_edge = np.minimum(np.minimum(yy, target.shape[0] - 1 - yy), np.minimum(xx, target.shape[1] - 1 - xx)) / float(n0)
    rise *= np.clip(d_edge / max(s["edge_fade"], 1e-6), 0.0, 1.0)
    n, m = z.shape
    dx = 1.0 / (max(n, m) - 1)
    cell = dx * dx
    rng = np.random.default_rng(int(s["seed"]))
    r = np.zeros(h.shape) if hard is None else np.clip(np.asarray(hard, dtype=np.float64), 0.0, 1.0)
    # Hard rock rests at the cliff angle and stands up to near vertical (Pass 3: erosion kept melting
    # caprock, cliff bands and crests into soft slopes).
    talus = np.tan(np.radians(s["talus_deg"] + (s["cliff_deg"] - s["talus_deg"]) * r))
    cliff = np.tan(np.radians(s["cliff_deg"] + (86.0 - s["cliff_deg"]) * r))
    soft_w = 1.0 - r
    # Incision: knickpoints on the main channel move about k_inc of the landscape per pass, so the
    # result doesn't depend on grid size. F = k_inc * A^m / distance, solved implicitly.
    k_inc = s["incision"] * 0.06
    # Sediment settles where a channel's slope falls under this (landscape-relative) gradient.
    settle = s["deposit"] * 0.08
    soften = s["soften"] * 0.2  # diffusion number per pass (stable below 0.25)
    k_cell = (hardness_field(z.shape, np.random.default_rng(int(s["seed"]) + 7), s["hardness"]) * (1.0 - 0.9 * r)).ravel()
    bias = None
    if s["meander"] > 0:  # one smooth random field per direction, the same every pass
        mrng = np.random.default_rng(int(s["seed"]) + 11)
        bias = [np.exp(s["meander"] * (g := blur(mrng.standard_normal(z.shape), 3)) / max(g.std(), 1e-12)) for _ in D8]
    for step in range(int(s["passes"])):
        z = z + rise
        if step % s["fill_every"] == 0 and (step > 0 or s["start"] < 1.0):  # the target is already filled
            z = fill(z) if s["pit_mode"] == "fill" else breach(z)
        # Route on slightly jittered heights: on even slopes the steepest neighbor is then a coin
        # toss among near-equals, so rills join into branching channels (single-direction routing
        # on a clean grid makes parallel straight stripes).
        rcv, dist = routing(z, dx, rng, s["jitter"], bias, sea)  # a pit left between fills drains nowhere this pass
        order = levels(rcv)
        flat = z.ravel().copy()
        area = np.full(flat.size, cell)
        for lv in order:  # drainage area, ridge tops first
            r = rcv[lv]
            ok = r >= 0
            np.add.at(area, r[ok], area[lv][ok])
        a_rel = area / (n * m * cell)
        a_m = a_rel ** s["m"] * np.clip((a_rel - s["channel"]) / s["channel"], 0.0, 1.0)
        F = k_inc * k_cell * a_m / dist
        before = flat.copy()
        for lv in reversed(order):  # outlets first: each receiver already has its new height
            r = rcv[lv]
            ok = r >= 0
            cells = lv[ok]
            hr = flat[r[ok]]
            flat[cells] = np.maximum((flat[cells] + F[cells] * hr) / (1.0 + F[cells]), hr)
        # Sediment: what was cut travels downstream and settles where the channel flattens,
        # raising a cell at most until its slope to the next cell reaches `settle` (fans, fill).
        if settle > 0:
            load = np.maximum(before - flat, 0.0)
            for lv in order:
                r = rcv[lv]
                ok = r >= 0
                cells, rr = lv[ok], r[ok]
                room = np.maximum(flat[rr] + settle * dist[cells] - flat[cells], 0.0)
                drop = np.minimum(load[cells], room) * s["deposit"]
                flat[cells] += drop
                load[cells] -= drop
                np.add.at(load, rr, load[cells])
        cut = flat.reshape(n, m)
        z = slump(cut, talus, dx, s["slump_every_pass"], cliff)  # valley walls fall back to their resting angle
        if soften > 0:  # hillslope softening
            for _ in range(int(s["soften_rounds"])):
                p = np.pad(z, 1, mode="edge")
                z = z + soften * soft_w * (p[:-2, 1:-1] + p[2:, 1:-1] + p[1:-1, :-2] + p[1:-1, 2:] - 4 * z)
        # Rivers carry away what slides and creeps into them: hillslope debris never raises a channel.
        # (Left in, it dammed every trunk into a chain of flat lakes: trunk slopes came out ~10x too
        # gentle, concavity 1.3 against 0.44 real; Pass 2.)
        chan = (a_rel > s["channel"] * s["protect"]).reshape(n, m)
        z = np.where(chan, np.minimum(z, cut), z)
    sea_z = z.copy()  # the sea floor as the passes left it (the finishing steps below don't know the sea)
    if s["edge_lift"]:
        z = z + edge_lift(target - z, edge)  # bring the edges back up to the shape, smoothly
    # Open any last pits, then widen channel floors (breach cuts 1-cell trenches), then only fill
    # what's left: a final breach would re-cut trenches that any resampling breaks into deep pits.
    if s["pit_mode"] == "breach":  # (a fill here was redundant: the last step fills anyway; speed, Pass 4)
        z = breach(z)
    z = widen_floors(z, dx, s["floor_width"], s["floor_from"])
    # The landscape is stretched back to its Height afterwards (D3), which steepens whatever the
    # slumping laid back. Stretch, then slump, until the relief holds, so slopes still sit at their
    # resting angle at the final relief.
    lo, span = float(target.min()), max(float(np.ptp(target)), 1e-12)
    for _ in range(6):
        z = lo + (z - z.min()) / max(float(np.ptp(z)), 1e-12) * span
        before = z
        z = slump(z, talus, dx, s["final_slump"], cliff)
        z = np.where(chan, np.minimum(z, before), z)
        if np.ptp(z) > 0.98 * span:
            break
    z = carve_floors(z, dx, s["floor_carve"], s["bank_deg"], s["channel"])
    # Round off the grid: D8 channels, the cliff cap and the carve leave one-cell stair steps that
    # showed as staircase edges and moire on the mesh (Pass 2). Floors are wide enough now not to dam.
    def smooth_rounds(z, k):
        for _ in range(int(k)):
            p = np.pad(z, 1, mode="edge")
            z = z + 0.2 * soft_w * (p[:-2, 1:-1] + p[2:, 1:-1] + p[1:-1, :-2] + p[1:-1, 2:] - 4 * z)
        return z
    z = smooth_rounds(z, s["finish_blur"])
    if s["finish_blur"] > 3:
        # Heavy smoothing dams channels into chains of flat pools: cut each dam back to a downhill
        # exit, widen the cut, and smooth lightly once more.
        z = breach(z, s["exit_slope"] / (max(n, m) - 1))
        z = carve_floors(z, dx, s["floor_carve"], s["bank_deg"], s["channel"])
        z = smooth_rounds(z, 4)
    if sea is not None:
        z = np.where(sea, np.maximum(z, sea_z), z)
        z = smooth_rounds(z, 2)  # soften the step along the shore
    # Give back the shape's own fine detail (finer than ~3 cells) on slopes and ridges, never in channels
    # or on valley floors: the smoothing above washed every texture away (Mike, Pass 3).
    if s["keep_detail"] > 0:
        fine = np.asarray(h, dtype=np.float64) - blur(np.asarray(h, dtype=np.float64), 1)
        # At a sheer step (caprock rim, cliff top) height minus its blur is a large spike on the top cells, an
        # unsharp-mask halo that stood up as a serrated lip along every Mesa rim (Mike, Pass 8). Clip it to a
        # few times the typical texture: rough ground keeps its detail, step edges lose the halo.
        lim = 4.0 * float(np.median(np.abs(fine))) + 1e-12
        fine = np.clip(fine, -lim, lim)
        z = z + fine * (1.0 - wetness(z, s["channel"])) * s["keep_detail"]
    # Fade back to the plain shape over the outer `edge_blend` of the width: the fixed edges left
    # notches and drips along every border (the "edge frame", Pass 1-3).
    w = np.clip(1.0 - d_edge / max(s["edge_blend"], 1e-6), 0.0, 1.0) if s["edge_blend"] > 0 else 0.0
    z = z * (1.0 - w) + target * w
    if s["min_cap"] > 0:  # knife-edge spurs left between alcoves cut into hard cliffs break off too (Mike)
        z = cut_fins(z, max(int(round(s["min_cap"] * max(n, m) / 2)), 1), s["fin_tol"])
    z = fill(z)
    return (z, erosion_masks(h, z)) if masks else z


def erosion_masks(before, after):
    """(flow, change), both 0..1, for materials and scatter (M3): flow is how much water drains through
    each cell (log of drainage area, 1 on the trunks); change is 0.5 where erosion left the ground alone,
    toward 0 where it cut (wear) and toward 1 where it filled (deposits), at 1 for a 5% of the relief change."""
    n, m = after.shape
    dx = 1.0 / (max(n, m) - 1)
    rcv, _ = routing(after, dx)
    area = np.full(after.size, dx * dx)
    for lv in levels(rcv):
        r = rcv[lv]
        ok = r >= 0
        np.add.at(area, r[ok], area[lv][ok])
    a_rel = (area / (n * m * dx * dx)).reshape(n, m)
    flow = np.clip(np.log10(np.maximum(a_rel, 1e-12) * n * m) / np.log10(n * m), 0.0, 1.0)  # one cell 0, all 1
    span = max(float(np.ptp(after)), 1e-12) * 0.05
    change = np.clip(0.5 + 0.5 * (after - before) / span, 0.0, 1.0)
    return flow, change


if __name__ == "__main__":  # self-check: a noisy ramp erodes, stays finite, loses its pits
    rng = np.random.default_rng(1)
    y, x = np.mgrid[0:128, 0:128] / 127.0
    h = 0.2 * (1 - y) + 0.03 * rng.standard_normal((128, 128))
    out = erode(h)
    assert np.isfinite(out).all(), "erosion produced NaN"
    assert (fill(out) - out).max() < 1e-5, "pits left"
    assert np.abs(out - h).max() > 1e-3, "nothing eroded"
    ridged = 0.2 * (1 - y) + 0.02 * np.sin(x * 20) + 0.003 * rng.standard_normal((128, 128))
    base = fill(ridged)
    soft, stiff = erode(ridged), erode(ridged, hard=np.ones_like(ridged))
    assert np.abs(stiff - base).mean() < 0.5 * np.abs(soft - base).mean(), "hard rock eroded as much as soft"
    flat = np.zeros((64, 64))
    flat[28:36, 28:36] = 1.0
    ap = apron(flat, flat > 0.5, 10, 0.5)
    assert abs(ap[32, 27] - 0.5 * 0.9 ** 2) < 1e-6 and ap[32, 10] == 0.0 and ap[32, 32] == 1.0, "apron shape wrong"
    bump = np.exp(-((np.arange(64) - 32.0) / 6.0) ** 2)[None, :].repeat(4, 0)
    lb = lean(bump, 0.05)[0]
    up, down = np.diff(lb)[:int(np.argmax(lb))], np.diff(lb)[int(np.argmax(lb)):]
    assert -down.min() > 1.3 * up.max(), "lean didn't steepen the downwind side"
    step = np.zeros((64, 64))
    step[:, 32:] = 1.0
    step += 0.002 * np.random.default_rng(2).standard_normal(step.shape)
    out_step = erode(step, {"passes": 2, "keep_detail": 1.0, "edge_blend": 0.0})
    assert out_step[:, 34:].max() < 1.0 + 0.05, "rim halo: detail stood up along the step edge"
    z2, (fl, ch) = erode(h, masks=True)
    assert fl.shape == h.shape and 0.0 <= fl.min() and fl.max() <= 1.0 and 0.0 <= ch.min() and ch.max() <= 1.0, "masks out of range"
    assert fl[-2, :].mean() > fl[1, :].mean(), "flow should gather downhill"
    cap_t = np.zeros((64, 64))
    cap_t[10:40, 10:40] = 1.0  # a wide block
    cap_t[45:47, 5:60] = 1.0   # a 2-cell fin
    zt, ht = break_thin_caps(cap_t.copy(), cap_t.copy(), 3)
    assert zt[25, 25] == 1.0 and zt[46, 30] < 0.2 and ht[46, 30] == 0.0, "thin caprock should break, wide stay"
    ridge = np.zeros((64, 64))
    ridge[:, 20:44] = 1.0       # a wide plateau
    ridge[30:32, 0:20] = 1.0    # a 2-cell fin off its side
    cf = cut_fins(ridge, 3, 0.06)
    assert cf[10, 30] == 1.0 and cf[31, 5] <= 0.07, "fins should drop, the plateau stay"
    print("erosion self-check OK")

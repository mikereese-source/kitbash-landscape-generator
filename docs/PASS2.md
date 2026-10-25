# Realism Pass 2 (2026-10-24): erosion engine fixes, regularity, windows, Volcanic, volcano scale

In progress. Sheet: m2/pass2-real-vs-ours.png (two pairs per row, real left | ours right, in this
order: Canyon, Badlands / Dunes, Cinder / Mountains, Seabed / Cliffs, Hills / Mesa, Volcanic /
Glacial, Riverbed / Strato, Caldera).

## What changed (D58)

- **Trunks drain.** Hillslope creep and slumps no longer raise river channels (rivers carry the debris
  off). They had dammed every trunk into a chain of flat lakes: trunk slopes ~10x too gentle,
  concavity 1.3 against 0.44 real. Mountains concavity now 0.51 (real 0.44).
- **Channels survive the mesh.** Floors are carved at least 2 cells either side of the bed (banks
  at most `bank_deg`). One-cell channels broke into dams when the map was resampled to the mesh.
- **Slopes rest at real angles.** Talus now really converges (thermal erosion plus a cap). There are two
  angles per type: scree spreads to `talus_deg`, bedrock stands up to `cliff_deg`. Slumping is
  repeated at the final relief, because the Height stretch steepened what it had laid back.
- **Less regular.** Rock hardness varies in smooth patches (`hardness`), and water routing has a fixed,
  smooth bias (`meander`), so rills curve and join instead of running in grid rows. Mountains spines
  turn (+-45 deg), vary in spacing and have two sizes of spur.
- **No stair steps.** The engine smooths at the end (16 rounds), then cuts any dams back to a
  downhill exit and re-carves the floors. The node tree reads the map with Cubic lookup (Linear
  made a crease at every texel). Fixed a 9-12 dB stripe at 5.7 m (the 4 m grid's diagonal).
- **Gentler incision.** Gullies were cutting too deep for the big shapes (64 m roughness 1.7x
  real). Mountains, Glacial and Hills now use incision 0.5.
- **Reference windows.** Riverbed is on the Platte's braided channel. Mesa is placed by hand
  (`exact` rule). Strato and Caldera compare the whole volcano: 8 km at 4 m, ours built at the
  real relief (`whole` rule).
- **Volcanic rebuilt.** Overlapping flow lobes (steep fronts, pressure ridges) on a broad sloping
  plain, a few cones, and rough rock grain everywhere (aa lava).
- Badlands Ridge Width still shapes the eroded spurs (T22).

## Second half (D59)

- **Mountains spines** turn up to ~85 deg, each spine has its own height and sharpness, and 40% of
  the old folded-noise ridges are blended in (0.7 left one big basin filled flat). Glacial walls keep
  even spines (weak ones made its trough too gentle: median slope 17 vs 30).
- **Cliffs:** the engine has an optional `sea_level`. Ground below it is base level, so runoff ends at
  the shore instead of trenching the wave-cut platform. The bluff has stronger hardness and meander.
  The shallow stretched-noise ravines are left for erosion to carve.
- **Volcanic:** cones vary in size and placement (Voronoi randomness 1), and the regional slope is
  gentler. Tall cones pass 30 m hypsometry and fail 1 m; short ones the reverse. Kept short (0.4).
- **Mesa window** moved to the most mesa-like part of the tile (flat tops 62%, cliffs 21%, flat
  floor 50%). The tile is Upheaval Dome country, not true mesas: a Monument Valley tile would need a
  new download (Mike's OK).
- Tried and reverted: storing only the erosion change in the map (it lost the smooth-floor /
  rough-rock contrast, rough split 0.68 vs 1.27) and a low-pass on it.

## Scorecard

Unit tests 14/14. T6 (30 m) 11/13 (Pass 1 10/13). T6b (1 m) 7/14 (Pass 1 6/14). T6c (structure)
3+/4 on 8 types (Pass 1: 2 types).

| Type | T6 30 m | T6b 1 m | T6c | D57 status / read |
|---|---|---|---|---|
| Mountains | PASS | PASS | 4/4 | **Checks pass: needs Mike's eye.** Spines turn and vary now |
| Glacial Valley | PASS | PASS | 3/4 | **Checks pass: needs Mike's eye.** Trough still runs straight across |
| Sand Dunes | PASS | PASS | 4/4 | **Checks pass: needs Mike's eye** (unchanged since Pass 1) |
| Canyon | PASS | median slope 28 / 16 deg | 4/4 | Scale question: at whole-canyon scale (8 km) slopes match (32 / 29) |
| Badlands | PASS | s64 1.7x, stripe | 4/4 | Dendritic now; gully relief a bit strong |
| Coastal Cliffs | n/a | stripe 5.4 dB | 3/4 | Platform clean; bluff gullies still fairly even |
| Rolling Hills | PASS | stripe at 31-34 m | 3/4 | Stripe is in the plain shape (knee where shape detail stops and grain starts) |
| Mesa | slope50 | PASS | 2/4 | Reference tile isn't true mesas |
| Volcanic | hyps | h_mid | 2/4 | Rebuilt; cone height trades 30 m against 1 m |
| Riverbed | PASS | stripe | 1/4 | Very low relief: grid and grain traces show |
| Volcano: Strato | PASS | PASS | 2/4 | Shape right at scale; real St Helens is collapsed (R8 lopsided) |
| Volcano: Cinder | PASS | PASS | 2/4 | Unchanged |
| Seabed | n/a | PASS | 2/4 | Unchanged (closed pits on reefs) |
| Volcano: Caldera | PASS | slope50, h_mid, s64 | 0/4 | Real Crater Lake window is mostly lake |

## For Pass 3

The 30 m stripe on smooth types (Hills, Riverbed: shape-detail cutoff vs rock-grain start); Badlands
gully depth; Cliffs bluff gullies; Volcanic cone trade-off; Canyon and Caldera reference questions;
Mesa tile (download).

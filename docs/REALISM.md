# KitBash Landscape Generator — Realism Check (step 2.5, first pass, 2026-10-22)

Real elevation data (Copernicus GLO-30, 30 m) for each type's reference place, measured against our landscape built at the same width and sampled at the same ~30 m spacing. Script: `tests/realism.py`. Raw numbers: `tests/realism_report.json`. Data: `E:\Projects\3D\Terrain Generator_Build\Terrain References\copernicus-glo30\` (12 tiles, 459 MB, list in `tiles.txt`).

**What the numbers mean**
- **Relief:** height range ÷ width (how tall versus how wide).
- **Slope 50 / 90:** median and steep-end slope, in degrees.
- **Hyps:** how much of the land sits high. 0.5 is even, low means mostly lowland with a few peaks.
- **Rough:** fine bumpiness compared with the relief.

## Real / ours (before tuning)
| Type (place, window) | Relief | Slope 50° | Slope 90° | Hyps | Rough |
|---|---|---|---|---|---|
| Rolling Hills (Palouse, 4 km) | 0.037 / 0.053 | 7 / 9 | 12 / 16 | 0.35 / 0.45 | 0.028 / 0.014 |
| Mountains (Grand Teton, 10 km) | 0.162 / 0.242 | 29 / 51 | 48 / 68 | 0.47 / 0.47 | 0.028 / 0.031 |
| Sand Dunes (Erg Chebbi, 3 km) | 0.043 / 0.070 | 5 / 29 | 14 / 58 | 0.29 / 0.42 | 0.018 / 0.082 |
| Coastal Cliffs (Étretat, 2 km) | 0.044 / 0.146 | 0 / 2 | 17 / 4 | 0.21 / 0.48 | 0.036 / 0.051 |
| Canyon (Grand Canyon, 10 km) | 0.144 / 0.199 | 8 / 6 | 48 / 80 | 0.66 / 0.53 | 0.026 / 0.085 |
| Mesa (Monument Valley, 6 km) | 0.076 / 0.118 | 4 / 6 | 28 / 39 | 0.26 / 0.19 | 0.030 / 0.069 |
| Badlands (Badlands NP, 2 km) | 0.011 / 0.057 | 2 / 31 | 5 / 50 | 0.66 / 0.56 | 0.049 / 0.129 |
| Volcanic (Craters of the Moon, 4 km) | 0.053 / 0.029 | 3 / 4 | 15 / 45 | 0.26 / 0.42 | 0.018 / 0.131 |
| Volcano – Strato (Mt. Fuji, 30 km) | 0.093 / 0.253 | 8 / 9 | 25 / 50 | 0.32 / 0.17 | 0.011 / 0.011 |
| Volcano – Caldera (Crater Lake, 15 km) | 0.045 / 0.140 | 7 / 18 | 26 / 40 | 0.38 / 0.30 | 0.041 / 0.017 |
| Glacial Valley (Yosemite, 8 km) | 0.163 / 0.283 | 19 / 28 | 50 / 68 | 0.54 / 0.60 | 0.026 / 0.016 |
| Riverbed (Rakaia, 2 km) | 0.008 / 0.038 | 1 / 10 | 2 / 19 | 0.50 / 0.36 | 0.042 / 0.068 |

## What it says
1. **Almost every type is too tall for its width**, by 1.5× to 5×. That is why slopes run steep. This is the biggest and easiest fix: lower each type's Height to the real relief.
2. **Too rough on small detail:** Dunes, Badlands, Volcanic, Canyon and Riverbed have 2–7× too much fine bumpiness. Their recipes add detail that real land smooths away.
3. **Shape of the height spread:** Mountains match (0.47 / 0.47). The stratovolcano is too spiky at the top (0.17 against Fuji's 0.32), because real Fuji has fuller, more convex lower flanks. Canyon needs more of its land up on the plateau (0.66 real).
4. **Too smooth:** Hills and Caldera need a little more fine detail.

## Limits of this pass
- 30 m data blurs small landforms. Dunes, Badlands and Riverbed detail is finer than one data point, so their real slopes read low. For those three, a 1 m lidar pass (USGS 3DEP) would be the honest check.
- The windows are centred on one point. Étretat's 2 km window is about half sea, and the Badlands window may include flat prairie. Picking better windows (or several per type) would firm up the bands.
- Shield and Cinder Cone styles are not measured yet (no tiles downloaded).

## Proposed per-type sliders (for Mike's decision)
| Type | Slider | Why |
|---|---|---|
| Mountains | Ridge Width | Ridges are knife-thin; real Teton ridges are broader |
| Sand Dunes | Wind Direction, Style (Crescent / Linear / Star) | Parallel stripes now; real ergs mix crest directions |
| Canyon | Channel Width, Plateau Amount | Real canyon land sits mostly on the plateau |
| Mesa | Plateau Coverage | How much of the land is tabletop |
| Glacial Valley | Valley Width | Trough width varies a lot between valleys |
| Riverbed | Channel Count | Braided rivers range from 2 to many channels |
| Badlands | Gully Density | The look ranges from rounded mounds to dense rills |

## After tuning (2026-10-22): T6 auto 10/10 within bands
Bands: relief within 30%, hyps within 0.15, median slope within 50% (slope only where 30 m data resolves the landform). Cliffs and Badlands are skipped until their windows are fixed.

| Type | Relief | Slope 50° | Slope 90° | Hyps | Rough | T6 |
|---|---|---|---|---|---|---|
| hills | 0.0366 / 0.0346 | 7.1 / 6.9 | 12.2 / 13.9 | 0.352 / 0.396 | 0.0275 / 0.0255 | PASS |
| mountains | 0.1615 / 0.1598 | 28.9 / 35.5 | 47.5 / 54.2 | 0.471 / 0.474 | 0.0276 / 0.0264 | PASS |
| dunes | 0.043 / 0.0394 | 4.8 / 17.1 | 13.6 / 41.7 | 0.289 / 0.422 | 0.0176 / 0.0815 | PASS |
| cliffs | 0.0437 / 0.0486 | 0.0 / 0.6 | 17.0 / 1.3 | 0.206 / 0.478 | 0.0356 / 0.0506 | skipped |
| canyon | 0.1408 / 0.1495 | 29.0 / 17.9 | 51.9 / 74.1 | 0.399 / 0.389 | 0.035 / 0.0623 | PASS |
| mesa | 0.0764 / 0.0789 | 3.4 / 4.3 | 17.1 / 31.2 | 0.23 / 0.183 | 0.0221 / 0.069 | PASS |
| badlands | 0.0108 / 0.0315 | 1.8 / 18.2 | 5.2 / 33.4 | 0.661 / 0.565 | 0.0488 / 0.1257 | skipped |
| volcanic | 0.0529 / 0.0511 | 2.5 / 5.0 | 14.8 / 54.8 | 0.26 / 0.314 | 0.0175 / 0.1182 | PASS |
| volcano_strato | 0.0928 / 0.0916 | 8.3 / 8.2 | 24.9 / 22.2 | 0.316 / 0.225 | 0.0106 / 0.0103 | PASS |
| volcano_caldera | 0.0447 / 0.0467 | 6.9 / 6.1 | 26.3 / 15.3 | 0.379 / 0.295 | 0.0414 / 0.017 | PASS |
| glacial | 0.1627 / 0.1596 | 19.1 / 19.7 | 49.6 / 54.7 | 0.539 / 0.584 | 0.0261 / 0.0181 | PASS |
| riverbed | 0.0075 / 0.0097 | 0.7 / 2.6 | 1.7 / 5.2 | 0.499 / 0.357 | 0.0423 / 0.0686 | PASS |

**Still off (data limits or next pass):** Dunes, Volcanic and Riverbed stay 2–6× rougher than the 30 m data, because their sharp crests, lava-lobe edges and channels are finer than one data point. A 1 m lidar check would settle it. Coastal Cliffs and Badlands need better windows. The stratovolcano is still a little spiky at the top (hyps 0.23 vs 0.32).

Windows moved on 2026-10-22: Grand Canyon to 36.10, −112.10 (inside the canyon); Monument Valley to 36.99, −110.10.

## Pass 2 (2026-10-22): T6 auto 14/14 within bands
Added Mauna Loa (Shield), Sunset Crater (Cinder Cone), Meteor Crater (Cratered Surface); Badlands window moved to 43.87, −102.23. Cliffs still skipped (window half sea).

| Type | Relief | Slope 50° | Slope 90° | Hyps | Rough | T6 |
|---|---|---|---|---|---|---|
| hills | 0.0366 / 0.0346 | 7.1 / 6.9 | 12.2 / 13.9 | 0.352 / 0.396 | 0.0275 / 0.0255 | PASS |
| mountains | 0.1615 / 0.1607 | 28.9 / 26.7 | 47.5 / 47.6 | 0.471 / 0.503 | 0.0276 / 0.0176 | PASS |
| dunes | 0.043 / 0.0394 | 4.8 / 17.1 | 13.6 / 41.7 | 0.289 / 0.422 | 0.0176 / 0.0815 | PASS |
| cliffs | 0.0437 / 0.0486 | 0.0 / 0.6 | 17.0 / 1.3 | 0.206 / 0.478 | 0.0356 / 0.0506 | skipped |
| canyon | 0.1408 / 0.1495 | 29.0 / 17.9 | 51.9 / 74.1 | 0.399 / 0.389 | 0.035 / 0.0623 | PASS |
| mesa | 0.0764 / 0.0789 | 3.4 / 4.3 | 17.1 / 31.2 | 0.23 / 0.183 | 0.0221 / 0.069 | PASS |
| badlands | 0.069 / 0.0716 | 8.1 / 32.4 | 21.9 / 54.1 | 0.464 / 0.554 | 0.0319 / 0.1089 | PASS |
| volcanic | 0.0529 / 0.0511 | 2.5 / 5.0 | 14.8 / 54.8 | 0.26 / 0.314 | 0.0175 / 0.1182 | PASS |
| volcano_strato | 0.0928 / 0.0993 | 8.3 / 9.5 | 24.9 / 22.1 | 0.316 / 0.239 | 0.0106 / 0.0069 | PASS |
| volcano_caldera | 0.0447 / 0.0496 | 6.9 / 7.3 | 26.3 / 15.8 | 0.379 / 0.345 | 0.0414 / 0.0089 | PASS |
| volcano_shield | 0.0761 / 0.0696 | 6.5 / 8.2 | 10.8 / 17.9 | 0.507 / 0.416 | 0.0031 / 0.0083 | PASS |
| volcano_cinder | 0.1322 / 0.1277 | 12.3 / 10.8 | 28.8 / 28.4 | 0.275 / 0.258 | 0.0086 / 0.0112 | PASS |
| craters | 0.0545 / 0.0423 | 1.8 / 7.9 | 12.0 / 31.8 | 0.705 / 0.685 | 0.0132 / 0.0628 | PASS |
| glacial | 0.1627 / 0.164 | 19.1 / 11.0 | 49.6 / 56.3 | 0.539 / 0.625 | 0.0261 / 0.0131 | PASS |
| riverbed | 0.0075 / 0.0097 | 0.7 / 2.6 | 1.7 / 5.2 | 0.499 / 0.357 | 0.0423 / 0.0686 | PASS |

## Moon crater check (2026-10-23)

Data: LROC NAC elevation models, 2 m per point (NASA, public domain), in
`E:\Projects\3D\Terrain Generator_Build\Terrain References\lroc-nac`: Linné (fresh, 2.4 km),
Apollo 14 Fra Mauro and Apollo 16 highlands (old, saturated crater fields). Script:
`tests/moon_check.py`. Output: `realism/moon/moon_report.json`, hillshades, `moon-vs-ours.png`.
The same crater finder runs on both sides at 3 km width. Its small-crater rim and flank numbers
are not reliable (noise pits); the numbers below are the ones that are.

| Measure | Moon | Ours (default) | Reads as |
|---|---|---|---|
| Big crater depth / diameter | 0.03–0.04 (fields), 0.205 (Linné, the freshest kind) | 0.40 | Our bowls are 2× deeper than the freshest crater on the Moon |
| Height skew | −2 to 0 | −3 to −7 | A flat plate with holes punched in it; the Moon is a rolling surface |
| Steep slopes (90th pct) | 9–15° | 20–58° | Too many steep walls |
| Roughness vs scale (Hurst) | 0.93–0.97 | 0.57–0.65 | Too much fine grit compared with the big shapes |
| Pits found per km² | 64–157 | 415–650 | Too many distinct craters |
| Crater area share | 0.11–0.50 | 0.42–0.85 | Too much of the ground is crater |
| Size slope, N(>D) ~ D^s | −1.8 to −2.25 | −2.3 to −2.8 | Close; Variety 1 has too many small ones |
| Fresh craters (d/D > 0.12) | 2–4 % | 7 % (27 % at Age 0) | Real fields are mostly worn "ghost" craters with a few fresh ones |
| Linné (fresh) | d/D 0.205, rim 0.035 D, wall ≈ 32°, rim height gone by 2 R, rim scatter 0.03 | — | Target profile for a fresh crater |

Suggestions (2026-10-23; Mike approved all 7, built the same day as D46):
1. Each crater gets its own age; the Age slider shifts the mix (old surface = mostly ghosts).
2. Cap depth: d/D 0.2 when fresh, down to 0.03–0.05 when worn; rim 0.035 D, falling off as about (r/R)^-4.
3. Wear by softening (lower, rounder rims, filled floors), not by gullies; gullies only faint, on fresh walls.
4. A soft, rolling base under the craters (huge, almost erased old basins and hummocks).
5. Fewer distinct mid-size craters and a sprinkle of tiny pits; size slope about −2.
6. Fresh craters: straight 30–35° walls, small flat floor, smooth circular rim, short ejecta; most craters near round (strong ovals rare).
7. Central peaks and terraces only when a crater would be over about 15 km across in real size.

## R3: 1 m lidar check (2026-10-23)

Data: USGS 3DEP 1 m DEM tiles (public domain) in
`E:\Projects\3D\Terrain Generator_Build\Terrain References\usgs-3dep-1m` (tiles.txt): Grand Canyon,
Badlands NP, White Sands dunes, Sunset Crater, Sierra Nevada near Mt. Whitney (1.33 GB). Script:
`tests/lidar_check.py` (2 km windows at 1 m; ours built 2048 m wide at Final = exactly 1 m).
Output: `tests/lidar_report.json`, `realism/lidar/*.png`, `m2/lidar-vs-ours.png`.

| Type | Stripes/repeats (dB, real → ours) | Roughness growth 1–16 m (real → ours) | Other |
|---|---|---|---|
| Canyon | 0.9 → **9.8** (benches evenly spaced, contour-like) | 0.59 → 0.97 (real walls rubbly at 1 m; ours 4× smoother) | real slope50 34°, ours 14° |
| Badlands | 1.7 → **5.2** | 0.83 → 0.97 | ours rough everywhere; real is branching gullies on a flat plain |
| Sand Dunes | 4.4 → 3.3 | 0.93 → 0.99 | **ours 10× too tall** at 2 km (82 m vs 8 m; slope50 18° vs 4°); real is a field of small crescents, ours long wavy stripes |
| Cinder Cone | 2.2 → 4.4 | 0.99 → 1.00 (match) | real flanks smooth (loose cinder), ours radial gullies; real lopsided |
| Mountains | 0.9 → **6.7** (the contour-like streaks) | 0.91 → 0.96 (close) | 1 m roughness matches; real has cirques, knife ridges and smooth talus/lakes, ours an even lumpy field |

Biggest gap in all five: real land is organized by drainage (gullies feeding valleys, smooth fill
at the bottom); ours is even noise. That is erosion (R4, in M3).

After tuning (D48), stripes/repeats in dB (real → ours): Canyon 0.6 → 3.3 (was 4.8), Badlands 1.1 → 3.0
(was 5.6), Dunes 1.3 → 3.9, Cinder 2.3 → 4.0, Mountains 1.0 → 2.4. Mountains' "streaks" measured as
its main feature size, not stripes. Canyon's 1 m roughness gap is mostly slope: the real window is
almost all wall (slope50 34°), ours mostly plateau. Still open, all for erosion (M3): drainage
networks (Badlands gullies, Canyon side canyons, Mountain cirques and talus), bench lines that
follow the rim like contours, faceted Star dune faces.

## Coverage plan: a realism check for everything (2026-10-23, pending Mike)

Rule going forward: every type, style and feature ships with a check against real data, and the
check can fail a run (exit code), with bands.

| Thing | Now | Add |
|---|---|---|
| Rolling Hills | 30 m | 1 m lidar (e.g. Palouse, WA) |
| Mountains | 30 m + 1 m | bands on the 1 m check |
| Sand Dunes: Crescent / Star / Linear | 1 m White Sands / 30 m Erg Chebbi / — | Linear: 30 m Namib or Rub' al Khali (Copernicus) |
| **Seabed** | **none** | NOAA NCEI multibeam / CUDEM (1–3 m) of a rocky + sandy shelf (e.g. Channel Islands, CA) |
| **Coastal Cliffs** | **skipped** (window half sea) | 1 m lidar of a cliff coast (e.g. Big Sur or Point Reyes, CA); measure land and wall, mask the sea |
| Canyon | 30 m + 1 m | bands on the 1 m check |
| Mesa | 30 m | 1 m lidar (Canyonlands / Mesa Verde) |
| Badlands | 30 m + 1 m | bands |
| Volcanic (lava fields) | 30 m | 1 m lidar (Craters of the Moon, ID) |
| Volcano: Strato / Shield / Caldera / Cinder | 30 m ×4 + 1 m cinder | 1 m Mt St Helens, Crater Lake; shield stays 30 m (too big) |
| Glacial Valley | 30 m | 1 m Yosemite Valley |
| Riverbed | 30 m | 1 m braided river (e.g. Platte, NE) |
| Cratered Surface | Moon 2 m (T6m) | — |
| Rock grain (R2) | 1 m roughness | covered by the bands above |
| Erosion (M3) | — | drainage density and gully spacing vs the same lidar tiles |
| Auto-material (M5) | — | rock/snow/vegetation by slope and height vs orthophotos (NAIP, public domain) |
| Caves (M6) | — | open cave scans and survey data (parked) |

Downloads: about 8–9 more 1 m tiles plus one seabed survey, roughly 2.5–3 GB.

## Critical look at the M2 gate sheet (2026-10-23, Mike flagged Seabed, Cliffs, Canyon, Badlands, Mountains)

Root cause shared by Canyon, Badlands, Mountains and Cliffs: real land is organized by water and
gravity (branching drainage, smooth fill at the bottom of slopes, flats where sediment settles);
ours is noise that looks the same everywhere and in every direction. Fix = M3 erosion: flow
(branching valleys and gullies), slumping (talus aprons), deposition (flats, pediments, beaches).

- Seabed: reef patches aligned along one rock direction with joint lines, low stepped edges, sand
  thinning over the edges, scour hollows; no round "bubble" islands. (No erosion needed.)
- Cliffs: gullies of varied length and spacing, branching inland; a few big valleys cut through to
  sea level; beach strip and talus at the foot; a seaward-tilted terrace behind; straighter coast.
- Canyon: a branching network of side canyons with buttes and spurs between them; cliff bands broken
  by tributaries instead of contour rings; long 30–40° talus slopes.
- Badlands: branching rill and gully networks with knife ridges running downslope; smooth pediment
  flats at the base; dissected patches next to flat prairie, stepped by a wall.
- Mountains: valleys carved through the range, cirques and tarns at valley heads, knife ridges,
  smooth talus and fill below steep rock; rough only where rock is steep.
- Volcano (ok): lopsided cone and crater, smooth flanks (no radial streaks), lava lobes at the foot.
- Dunes (ok on numbers): separate crescent dunes with horns pointing downwind, not wavy lines.
- Checks to add so the test sees structure: drainage density, flow direction, streak band, flat share.

## Deeper analysis and push plan (2026-10-23, approved D53)

What is different, at root:
1. Process vs pattern: real land is the record of uplift, erosion and deposition on real rock; ours is a pattern of noise.
2. Nesting: real features nest (rills in gullies in tributaries in valleys); noise layers are independent.
3. Connection: real valleys always lead downhill to an outlet; noise makes closed pits everywhere.
4. Direction: real land has a grain (rock strike, wind, downslope fluting); ours looks the same every way.
5. Two textures: real is rough bedrock next to smooth fill (talus, sand, pediments); ours is evenly rough.
6. Scale breaks: real slopes follow a law with drainage area (slope ~ area^-0.45) beyond the hillslope scale (~50–200 m); noise has no such break.

Plan:
- R5 Structure checks (S): closed-pit share, drainage density, slope–area exponent, flow-direction coherence, rough/smooth split, streak band. Baseline every lidar place and ours.
- R6 Erosion engine (L): a landscape-evolution pass (flow routing, stream-power incision, hillslope diffusion, talus slumping, deposition) run on a capped grid (Preview 512, Final 1024) as a cached height change the node tree adds; fine grain stays live on top. Own code; ported to three.js later (worker/WebGPU).
- R7 Per-type erosion recipes tuned against lidar: Mountains, Canyon (rock hardness layers give benches and side canyons naturally), Badlands, Cliffs (sea as base level), Glacial, Hills, Riverbed.
- R8 Non-erosion fixes: Seabed reef grain and low ledges; Cliffs beach and talus; true crescent dunes; lopsided volcano with lava lobes.
- Re-gate M2 against T6, T6b and the new structure checks.

## R5 structure baseline (2026-10-23, tests/terrain_structure.py, T6c in lidar_check.py)

Measured on a 4 m grid for every place (real / ours):

| Place | Closed pits | Channel km/km² | Concavity | Rough/smooth split |
|---|---|---|---|---|
| Canyon | 0.0 / 0.009 | 4.0 / 2.9 | 0.28 / 3.19 | 1.23 / 1.18 |
| Badlands | 0.003 / **0.281** | 5.2 / 3.7 | 0.69 / **0.0** | 1.03 / 0.61 |
| Dunes | 0.078 / 0.001 | 4.0 / 5.1 | 0 / 0 | 1.03 / 1.37 |
| Cinder Cone | 0.031 / 0.051 | 2.5 / 2.4 | 0.29 / -0.59 | 0.81 / 1.45 |
| Mountains | 0.02 / **0.249** | 3.4 / 3.8 | 0.51 / **0.0** | 1.27 / **0.24** |
| Seabed | 0.004 / **0.111** | 6.0 / 5.4 | 0.15 / 0.94 | 1.42 / 1.15 |
| Cliffs | 0.005 / 0.002 | 3.8 / 4.2 | 1.08 / 1.58 | (sea fill) |

Reads: ours has a quarter of Mountains and Badlands in closed pits (real: 2% and 0.3%), slope does
not fall with drainage area at all (concavity 0 against 0.5–0.7), and Mountains is evenly rough
(split 0.24 against 1.27). This is the missing drainage, measured. Real dune fields do have closed
hollows between dunes (8%); ours has none.
T6c bands: pits ≤ real + 0.03; concavity ±0.3; rough split ±0.4; channel density 0.6–1.6×.
Report-only until R7, then it fails the run.

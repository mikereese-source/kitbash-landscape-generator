# KitBash Landscape Generator — Project Context

> Read this at the start of every session. Update it at the end. Rules: [BUILD_RULES.md](../../../BUILD_RULES.md)

**Track:** full
**Stage:** Build (pre-Alpha)
**Current milestone:** M3 — Terraces, masks, water level (planned 2026-10-26, D74). M2 passed 2026-10-26 (D73, tag m2).
**Last updated:** 2026-10-26

## Pre-build checklist
- [x] Design doc approved (2026-10-22) → `DESIGN.md`
- [x] Boundaries approved (2026-10-22) → `DESIGN.md`
- [x] Clickable prototype approved (2026-10-22, v9) → https://claude.ai/artifact/3q2sd89zXBpTX2LemT8Bd1 (source in docs/prototype/)
- [x] Test plan approved (2026-10-22) → `TEST_PLAN.md`
- [x] Milestone plan approved (below) (2026-10-22)
- [x] Decision log started → `DECISIONS.md`

## One-line summary
A Blender add-on that replaces A.N.T. Landscape: pick a real landscape type, scale it to your scene without losing its shapes, then shape it with a few plain-language controls.

## Architecture
Blender 5.2 add-on. Geometry Nodes node groups do the terrain (live, non-destructive); a thin Python layer adds the menu entry, panel and presets. Details to be settled in DESIGN.md.

## Where things live
- Code: `apps/landscape-generator/kitbash_landscape_generator/` (Blender extension, junction-linked into Blender 5.2 `extensions/user_default/`, D13)
- Prototype: https://claude.ai/artifact/3q2sd89zXBpTX2LemT8Bd1
- Real app / build: <artifact link or path>

## Milestone plan
Every plan includes an errors & edge cases milestone and a final check.

**Pre-build (no add-on code until all approved)**
| # | Step | Done when |
|---|------|-----------|
| P1 | Design doc | Mike approves DESIGN.md (scope, 12 types, 6 controls) |
| P2 | Cave spike (throwaway test) | A 200 m landscape gets one cave and stalactites through the SDF stage in Blender 5.2; we record voxel size, memory and bake time. Decides if caves stay in v1 |
| P3 | Clickable prototype | HTML mock of the Landscape sidebar tab (simple first view + Advanced) approved by Mike |
| P4 | Test plan | Mike approves TEST_PLAN.md |
| P5 | Type recipes | One reference image + target look per type in a type sheet Mike approves |

**M1 steps (checkpoint after each; Mike OKs before the next)**
| Step | What | Size |
|---|---|---|
| 1.1 | Add-on skeleton: Blender extension folder `kitbash_landscape_generator/` (manifest, `__init__`), Landscape sidebar tab, Add Landscape at the top, scene landscape list | S — done 2026-10-22 |
| 1.2 | Core node group, built from Python: grid at Size X/Y, detail in meters per point, Preview/Final cap, height sampled on position ÷ size | M — done 2026-10-22 |
| 1.3 | Type JSON + first 3 recipes (Rolling Hills, Mountains, Sand Dunes), type gallery in the tab | M — done 2026-10-22 |
| 1.4 | Fit to selection (quick scale buttons and detail readout already done; presets dropped, D21) | S — done 2026-10-22 |
| 1.5 | Headless tests T1–T4, T18, T19; then the gate: checker, rollback zip, Mike sign-off | M |

**M2 steps (approved 2026-10-22; checkpoint after each)**
| Step | What | Size |
|---|---|---|
| 2.1 | Fix-first from the M1 gate: store each landscape's type by key, not list position; only rename names we generated; T3 checks the 10% margin | S — done 2026-10-22 |
| 2.2 | Shape controls in the tab: Height (m), Feature Size (m), Roughness, Sharpness, Seed + Randomize, Reset to type defaults; plain tooltips | M — done 2026-10-22 |
| 2.3 | Recipes batch A: Seabed, Coastal Cliffs, Canyon, Mesa (+ thumbnails) | L — done 2026-10-22 (starter looks; tuned in 2.5) |
| 2.4 | Recipes batch B: Badlands, Volcanic, Glacial Valley, Riverbed, and Volcano with a style picker (Stratovolcano, Shield, Cinder Cone, Caldera) and Crater Size, Steepness, Gullies, Breach (+ thumbnails) | XL — done 2026-10-22 (starter looks; tuned in 2.5) |
| 2.5 | Realism check: real elevation tiles per reference place, measure slope spread / relief ratio / height distribution / roughness, tune recipes to match, automate in T6 | L — done 2026-10-22 (T6 10/10; 8 per-type sliders + dune styles added) |
| 2.5b | Mike review fixes: thicker rounded ridges (Mountains, Badlands Ridge Width); Volcano Rim Thickness, Crater Depth, rough crater floor, gullies fade before the rim, breach as a lava-outflow ramp, Height up to 2x size; new Cratered Surface type; realism pass 2 (T6 14/14) | L — done 2026-10-22 |
| R1 | Artifact fixes: Voronoi patterns 2D with sites kept off cell edges and F1+F2 blending (no crater seams, dense overlapping craters); smooth domain warp replaces noise Distortion (no streaks); Canyon rebuilt as plateau + wobbling rock benches only on walls; Badlands stripe bands removed; rocky volcano rim; Height capped at 1x size | M — done 2026-10-22 (T6 14/14) |
| R1.5 | Quality pass: detail tiers Preview 512 / Final 2048 / Ultra 4096 (0.07 s / ~1.2 s / ~5 s); universal 2-point anti-alias blur before the Height stretch; round unbent craters; rounded volcano rim lip; scattered lumpy seabed boulders; flat-topped cinder cones | M — done 2026-10-22 (10/10 tests, T6 14/14) |
| R2 | Slope/height-aware fine detail with a real-world size floor: rock grain in meters on steep and high ground, along the surface normal; shape layers stop at 0.25 m (D47) | M — done 2026-10-23 |
| R3 | 1 m lidar realism check + roughness-vs-size measure: tests/lidar_check.py on 6 USGS 1 m tiles; tuning in D48 | M — done 2026-10-23 |
| R4 | First erosion pass (moved into M3) | L |
| R5 | Structure checks: closed pits, drainage density, slope–area, flow lines, rough/smooth split, streaks (D53) | S |
| R6 | Erosion engine: flow, incision, diffusion, talus, deposition; cached height change; prove on Mountains (D53) | L |
| R7 | Per-type erosion recipes tuned on lidar; remove Canyon h_mid waiver (D53) | M–L |
| R8 | Seabed grain/ledges, Cliffs beach/talus, crescent dunes, lopsided volcano (D53) | M |
| 2.6 | Tests T5–T8, then the gate: checker, rollback zip, Mike sign-off | M |

**M3 steps (approved 2026-10-26, D74; checkpoint after each)**
| Step | What | Size |
|---|---|---|
| 3.1 | Data masks: height, slope, curvature (node tree) and flow, wear, deposits (erosion engine, stored per landscape) as named attributes in 0–1, kept for M5 materials and scatter (T9) | M — done 2026-10-26 (T9 PASS, 18/18) |
| 3.2 | Mask viewer: a "Show mask" choice in the panel that colours the viewport by any mask | S — done 2026-10-26 (T28; viewport checked by Mike 2026-10-26) |
| 3.3 | Terraces / strata control (count, strength, tilt) on Mesa, Canyon, Badlands, Coastal Cliffs and Mountains (T10) | M — done 2026-10-27 (T10 PASS, 20/20) |
| 3.4 | Water level: on/off water plane at a set height for any landscape (lakes, sea, rivers) with one plain water material; full water shaders come in M5 (T27) | S–M — done 2026-10-27 (T27 PASS, 21/21; lg_depth mask added) |
| 3.5 | Tests, then the gate: checker, rollback zip, Mike sign-off | M |

**Build**
| # | Milestone | Definition of done | Status |
|---|-----------|--------------------|--------|
| M1 | Scale-correct core | The Landscape sidebar tab is in place, and Add Landscape creates a live GN landscape at the 3D cursor. Size X/Y, Fit to selection, meters-per-vertex detail, Preview/Final work. 3 types (Rolling Hills, Mountains, Sand Dunes). Shapes match at 10 m, 100 m and 1 km (T1) | Done — gate passed, Mike signed off 2026-10-22 |
| M2 | All types + simple controls | All 13 surface types (D30, D37) plus the main controls, the erosion engine (moved into M2 by the realism push, D53/D54; Erosion Amount slider D63) and Randomize. Every control has a plain tooltip. Recipes load from the JSON type file. Realism check: each type's slope spread, relief ratio, height distribution and roughness match measured real elevation data for its reference place (T6 30 m, T6b 1 m, T6m Moon; D52) | PASSED 2026-10-26 (D73) |
| M3 | Terraces, masks, water level | Terraces/strata control on the rock types (Mesa, Canyon, Badlands, Cliffs, Mountains). Height, slope, curvature, flow, wear and deposits stored as named attributes and viewable in the viewport. A water level with a plain material (D74) | In progress (planned 2026-10-26) |
| M4 | Erosion finish + bake | Small milestone (Mike, D74): erosion itself shipped in M2 (D53/D54). Bake the landscape to a plain editable mesh that keeps its masks (warns the sliders stop); T11 (erosion lowers steep slopes) and T12 (1 km at High in 60 s or less) | Not started |
| M5 | Auto-material | Rock/ground/sand/snow material driven by masks, box-mapped, works in Cycles and Eevee; full water shaders (lake, sea, river) on the M3 water level: surface ripples and wind as a bump/normal pattern, shore foam, small shallow-water ripples and shallow-to-deep colour driven by the lg_depth mask (Mike, 2026-10-27). Material controls that remap the masks so artists dial in where each layer goes, like the Shape controls (Mike, 2026-10-26): e.g. Snow Line and Snow on Slopes, Rock Angle, Grass Amount, Wetness in channels, Sediment in deposits; each with a blend softness. Masks stay raw 0–1 data; the controls live in the material | Not started |
| M6 | Cliffs, caves, stalactites | Side Cliffs, Overhangs, Arches, Stalactites, Stalagmites toggles and the Cave type, through the SDF stage, baked at Final | Not started |
| M7 | Errors & edge cases | Bad input, tiny/huge sizes, too many vertices, missing JSON, undo, save/reopen, old files all handled and tested | Not started |
| Final | Final check + Alpha | Full test run, checker review of whole build vs design doc, prototype vs real add-on walkthrough. Packaged as a Blender extension zip | Not started |

**After v1 (parking list):** stamps and curves, tiling and heightmap export, scattering.

**Project 2 (separate build, after Project 1 Gold):** rewrite the whole tool in three.js for Cargo, reading the same type JSON (D7).

## Gate log
| Milestone | Tests | Checker | Mike sign-off | Rollback point | Docs updated | Date |
|-----------|-------|---------|---------------|----------------|--------------|------|
| M1 | 6/6 PASS (T1–T4, T18, T19) | PASS, 0 must-fix, 7 notes → PARKING | Signed off 2026-10-22 | snapshots/kitbash_landscape_generator-M1-2026-10-22.zip | Yes | 2026-10-22 |

## Current status
2026-10-22: Kickoff. Read the A.N.T. Landscape source; scale bug traced to noise sampled in world units with a fixed height and clamp. Market research done (RESEARCH.md). Mike picked research features 1–5 for v1. DESIGN.md and milestone plan drafted; awaiting approval. 2026-10-22: P2 cave spike PASSED (SPIKE_P2_CAVES.md, D9). P5 type sheet APPROVED. P3 prototype v6 published with Add button at top and cave layouts; awaiting approval, then M1 starts.

## Outside testing (Beta)
- [ ] Installation guide
- [ ] How-to guide
- [ ] Onboarding guide
- [ ] Bug report channel: <where>
- [ ] Reports triaged before next stage

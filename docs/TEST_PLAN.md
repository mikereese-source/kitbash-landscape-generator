# KitBash Landscape Generator — Test Plan

**Status:** Approved (2026-10-22). T18–T19 added at M1 kickoff (2026-10-22).

## What "working" means
An artist can add any of the 12 landscape types, fit it to their scene at any size from 10 m to 2 km, and get the same shapes at every size, already textured, with cliffs and caves when asked, without opening Advanced. Auto tests run headless with `blender -b --python tests/run_tests.py`.

## Tests
| ID | Milestone | Test | How | Pass when | Result |
|----|-----------|------|-----|-----------|--------|
| T1 | M1 | Scale keeps shape | auto | Big shapes (detail under 1/12 of the width removed) at 10 m, 100 m, 1 km differ by < 3% of height range; fine grain is real-size on purpose (D47) || PASS 2026-10-23 (13 types, max 1.46%) |
| T2 | M1 | Detail spacing | auto | Vertex spacing = size ÷ resolution (Preview 512, Final 2048) within 5% at every size (D18, D40) || PASS 2026-10-22 |
| T3 | M1 | Fit to selection | auto | Landscape bounds cover the selected objects' bounds plus margin || PASS 2026-10-22 |
| T4 | M1 | Preview vs Final vs Ultra | auto | Preview 513², Final 2049², Ultra 4097² points (D40) || PASS 2026-10-22 (66,049 / 1,050,625) |
| T5 | M2 | All types build | auto | Each of the 13 types and every style builds with finite, varied (not flat) output | PASS 2026-10-26 (21 type/style combinations) |
| T6 | M2 | Types look right | auto + manual | Auto: slope spread, relief ratio, height distribution and roughness within agreed bands of real elevation data (DEM) for each type's reference place. Manual: Mike reviews side-by-side renders against P5 references | Auto 2026-10-26: T6 30 m 11/13 (Mesa, Volcanic miss), T6b 1 m 12/14 (Riverbed, Caldera miss), T6m Moon PASS; T6c report only. Waivers: Mike at the M2 gate (D57). Manual: Mike at the gate |
| T7 | M2 | Same seed, same result | auto | Two builds with one seed match exactly; different seeds differ | PASS 2026-10-26 |
| T7a | M2 | Type saved by key | auto | Type stored by key; user-typed names survive a type change; M1 files (position-stored type) load as the right type | PASS 2026-10-22 |
| T20 | M2 | Shape controls | auto | Each control changes the landscape; Height (m) equals the real relief and grows with size; Randomize picks a new seed; Reset restores the type look | PASS 2026-10-26 |
| T21 | M2 | Volcano styles and controls | auto | 4 styles give distinct shapes and load their own height; Crater Size, Steepness, Gullies and Breach each change it; Reset restores defaults | PASS 2026-10-26 (5 styles now; Collapsed not yet in the distinct-shape check) |
| T22 | M2 | Per-type sliders | auto | Each per-type slider changes its type; the 3 dune styles differ | PASS 2026-10-26 (16 sliders) |
| T8 | M2 | Controls are plain | auto + manual | Auto: every panel control and button has a tooltip. Manual: a non-specialist explains each one correctly | Auto PASS 2026-10-26 (35 controls, 10 buttons); manual: Mike at the gate |
| T9 | M3 | Masks exist and are 0–1 | auto | height, slope, curvature, flow, deposits attributes present, in range | |
| T10 | M3 | Terraces | auto | Terrace count N gives N flat bands on a test slope | |
| T11 | M4 | Erosion lowers steep slopes | auto | Max slope angle drops as Erosion rises; nothing goes NaN | |
| T12 | M4 | Final build time | auto | 1 km landscape at Final finishes in ≤ 60 s on the team machine (D14) | |
| T13 | M5 | Auto-material | manual | Steep = rock, flat = ground, low pockets = sediment, high = snow in Cycles and Eevee | |
| T14 | M6 | Cave is hollow | auto | Ray from inside the cave hits terrain in all directions; mesh is manifold | |
| T15 | M6 | Stalactites hang, stalagmites stand | auto | Spikes point down from ceilings and up from floors only | |
| T16 | M6 | Caves texture without UVs | manual | No stretching on cave walls | |
| T17 | M7 | Save, reopen, rescale | manual | A saved file reopens identical and still rescales correctly | |
| T18 | M1 | Landscape tab | auto | A "Landscape" tab exists in the 3D Viewport sidebar; Add Landscape sits at the top and creates a landscape at the 3D cursor || PASS 2026-10-22 (auto part; button-at-top is a manual check) |
| T19 | M1 | Landscape list | auto | The list shows every landscape in the scene; picking a row makes it the active object || PASS 2026-10-22 |

## Errors & edge cases
| ID | Case | Expected behavior | Result |
|----|------|-------------------|--------|
| E1 | Bad input: size 0 or negative | Clamped to a minimum; no crash | |
| E2 | Too many vertices requested | Warning in panel, Final capped to budget | |
| E3 | Fit to selection with nothing selected | Button disabled with a hint | |
| E4 | Missing or broken type JSON | Falls back to built-in defaults, shows a warning | |
| E5 | Cave voxel budget exceeded | Coarser voxels used, warning shown | |
| E6 | Undo / redo during edits | Landscape returns to the previous state | |
| E7 | Add-on disabled and re-enabled | Existing landscapes still work | |

## Final check
- [ ] Full test run passes
- [ ] Checker review of whole build vs DESIGN.md passes
- [ ] Prototype vs real add-on walkthrough done with Mike

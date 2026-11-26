# LG-092 Rills on Badlands
Type: feature | Milestone: Model realism | Phase: B2 Model realism | Size: L | Priority: P1
Status: todo | Lane: side | Needs Blender: yes | Mike review: yes
Depends on: LG-090 | Blocks: LG-082, LG-091

## Why
Mike's geometry look pass (2026-11-25): LG-090, then this, then LG-082. LG-077 left Badlands out of the bedrock breakup (Mike, 2026-11-22): its creases come from rills in mudstone, not joint blocks, so a rill stage is its own ticket. Measured in LG-077 (2 km High, 1 m grid, main 4e717f5 against the real South Dakota 1 m lidar): over 60 deg 11.0% (real 4.7), flat faces 8.3% (real 0.4), creases 3.2% (real 53.0%), teeth / horns 31 / 48 (real 615 / 197), relief 155 m (real 130). The breakup probe turned the soft fins into jointed crags. Real Badlands are dense branching rills and fluting with knife ridges between them, running down every slope, nested in the gullies, over a smooth pediment (REALISM.md). REVIEW-realism-2026-11 also found twice the real flat ground and rounded fin crests.

## Done when
- Badlands gets a rill stage: dense, branching rills down every slope with knife ridges between them, nesting into the existing gullies; the pediment stays smooth. Both styles (Wall, Mounds) get it, each at its own strength
- Built after erosion, not before (CODING), and scales with Erosion Amount like every erosion step; any new control follows the Apron pattern in types.json
- Creases and teeth / horns rise toward the SD lidar; over 60 deg and flat faces not above main (both already above real); relief within 2%
- Rill spacing stays meshable at High (no rill narrower than about 3 grid cells); finer fluting is left to materials (lg_flow, MATERIALS-needs X3). Note how the rills fare under LG-091's decimation (about 1M triangles)
- Every other type unchanged (its tests' numbers equal main)
- New test (claim the next free T) at the measured board values; board beside the SD lidar hillshade and the Badlands photo, Preview vs High alike; build and re-evaluation time measured; suite passes; code review

## Files
- `kitbash_landscape_generator/erosion.py` (a rill step, if it sits in the engine as LG-090's trough does)
- `kitbash_landscape_generator/nodes.py`, `node_groups.blend` (if it sits in the node tree; claim the next GROUP_VERSION)
- `kitbash_landscape_generator/types.json`, `__init__.py` (`_erosion_settings`)
- `tests/run_tests.py`

## Agent brief
Read LG-077's Log (the Badlands numbers, the breakup probe and why it was dropped), LG-090's ticket and code (`erosion.trough()`: a step after the finishing smoothing, using the engine's drainage), REALISM.md (Badlands), PASS6.md (Badlands Mounds fine rills: incision 1.5, channel 1e-4) and Badlands in types.json. The measure scripts and SD lidar window are on branch lg-077-cp2 (docs/realism/LG-077_scratch: m77.py, realwin.py, hsreal.py) and in tests/lidar_check.py (`real_window`). Prototype in numpy on a baked Badlands height map first (rills carved from the drainage after erosion vs. finer engine settings vs. a fall-line noise in nodes), and show Mike a board with the numbers before touching the add-on.
Also read docs/tickets/README.md (rules every ticket follows) and docs/CODING.md.

## Log
- 2026-11-26 created (Mike: the second ticket of the geometry look pass, "Let's go")

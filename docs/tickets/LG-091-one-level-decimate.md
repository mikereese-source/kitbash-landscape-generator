# LG-091 One detail level and a decimation pass
Type: feature | Milestone: Model realism | Phase: B2 Model realism | Size: L | Priority: P1
Status: todo | Lane: main | Needs Blender: yes | Mike review: yes
Depends on: the geometry look pass (LG-090 and whatever Mike counts in it) | Blocks: LG-083

## Why
Mike, 2026-11-25: after the geometry look pass and before materials, come back to one detail level instead of three (Preview / High / Ultra) plus a decimation pass. Parked since 2026-10-22 ("build at Ultra, then decimate to a target polygon count (slider)", PARKING.md). LG-087's spike measured it: High's 8.4M triangles are about 8 times what its forms need; Decimate (collapse) to about 1M triangles matches High within 1% on every measure at wide and mid shot distance (height error 0.42 m rms), 500k holds for wide shots only, and taking the grain out of the mesh saves only about 5% (boards c195, c196). Materials (LG-083) should be built on the mesh we keep, so this goes first.

## Done when (draft, refresh with Mike before starting)
- One build resolution replaces the Detail Level menu for landscapes; a face budget control (slider or a few presets) sets the decimated count, default near the LG-087 1M finding
- A fast editing view stays (a proxy while sliders move), with the full build and decimation on demand, not on every slider change
- Decimation keeps crests, breakup blocks and cliff bands (measured: crest sharpness, teeth/horns, over 60 deg within 1% of the full build at the default budget); masks (lg_wear, lg_deposit, lg_talus, lg_hard and the rest) survive on the decimated mesh or are baked to textures for LG-083
- Heightmap export unchanged; old .blend files with a Detail Level open and rebuild cleanly; caves (LG-054's separate levels) decided and noted
- Build time and memory measured before and after; board at shot distance beside the full build; T42 and the Detail Level tests replaced; suite passes; code review

## Files
- `kitbash_landscape_generator/__init__.py` (Detail Level property and panel, build, decimation step)
- `kitbash_landscape_generator/nodes.py`, `node_groups.blend` (if the decimation sits in the node tree)
- `kitbash_landscape_generator/export.py` (masks, heightmap)
- `tests/run_tests.py`

## Agent brief
Read LG-087's Log first (both recommendations, boards c195 and c196) and the LG-087_scratch scripts on branch lg-087-mesh (bake, Decimate, measure). Read the Detail Level code in __init__.py (around `detail: EnumProperty` and the "Faces per Detail Level" panel) and LG-085's face counts. Decide with Mike: Blender's Decimate modifier vs. a geometry-nodes or numpy step, where masks live after decimation, and what the editing proxy is.
Also read docs/tickets/README.md (rules every ticket follows) and docs/CODING.md.

## Log
- 2026-11-25 created (Mike: after the geometry look pass, before materials). From PARKING.md (2026-10-22) and LG-087's findings

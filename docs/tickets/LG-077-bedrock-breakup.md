# LG-077 Bedrock breakup stage on the finished mesh
Type: feature | Milestone: Model realism | Phase: B2 Model realism | Size: M-L | Priority: P1
Status: todo | Lane: side | Needs Blender: yes | Mike review: yes
Depends on: LG-076 | Blocks: LG-082

## Why
Nothing exists between the 16 m shape floor and the 1 m grain, so rock faces read as pillows. A scratch breakup lifted Mountains from 2.9% to 8.6% over 60 deg and smoothness from 0.99 to 0.89 (real 0.89) (review S4). This is secondary volume (5-60 m), so it belongs in the mesh, not the material (D157, D163).

## Done when
- Reference board per rock type first (granite blocks, bedded limestone, sandstone) in `docs/realism/`
- Jointed blocks at three sizes plus strata benches, masked by slope 34-46 deg and rock patches, in `nodes.py` after the erosion blend
- Per-type inputs: Breakup amount, bed thickness, bed dip, block size; tooltips (T8)
- Blocks tilt and push along the normal: no cracked plates from above, no stretched risers on steep faces
- Smallest block at least 2.5-3 mesh points; Preview shows the two bigger sizes only
- Mountains first, then Glacial, Canyon, Mesa, Cliffs, Badlands
- GROUP_VERSION bump, library rebuilt, test added, suite passes
- Code review before merge; Mike signs off the board

## Files
- `kitbash_landscape_generator/nodes.py`
- `kitbash_landscape_generator/types.json`
- `kitbash_landscape_generator/__init__.py`
- `kitbash_landscape_generator/node_groups.blend`
- `tests/run_tests.py`

## Agent brief
Read docs/REVIEW-realism-2026-11.md S4 and the appendix `rock_breakup()`. Fable job. Must port to three.js as vertex displacement: per-point noise only, no neighbours.
Also read docs/tickets/README.md (rules every ticket follows) and docs/CODING.md.

## Log
- 2026-11-11 created from the realism review (D209)

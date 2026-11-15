# LG-077 Bedrock breakup stage on the finished mesh
Type: feature | Milestone: Model realism | Phase: B2 Model realism | Size: M-L | Priority: P1
Status: in progress | Lane: side | Needs Blender: yes | Mike review: yes
Depends on: LG-076 | Blocks: LG-082

## Why
Nothing exists between the 16 m shape floor and the 1 m grain, so rock faces read as pillows. A scratch breakup lifted Mountains from 2.9% to 8.6% over 60 deg and smoothness from 0.99 to 0.89 (real 0.89) (review S4). This is secondary volume (5-60 m), so it belongs in the mesh, not the material (D157, D163).

## Done when
- Sharp summits and knife-edge crests (Mike, 2026-11-12: 'we need to resolve getting sharp mountain tops... overall sharper, more realistic mountains'): the highest peaks read as horns and aretes, not domes, in the wide and mid clay shots; crest sharpness measured as in the realism review (today 38, real Sierra 1351) and logged
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
- 2026-11-12 Mike picked incision 1.8 (LG-076) and asked for sharp mountain tops: added to Done when
- 2026-11-14 checkpoint 1 (Fable 5.2, branch lg-077-breakup): breakup built in `nodes.py` on Mountains, after the erosion blend. Blocks at 60, 22 and 9 m (3D smooth cells, each face a tilted plane, bevelled joints), bedded ledges, pushed along the normal; inputs Breakup, Block Size, Bed Thickness, Bed Dip from `types.json` (Mountains 1.0 / 60 m / 14 m / 4 deg), sizes shrink together under 1/32 of the width. GROUP_VERSION 145, library rebuilt, T43 added. Boards `docs/realism/c191_lg077_mountains.png` and `c191_lg077_refs_granite|limestone|sandstone.png`
- 2026-11-14 counted before fixing: the review's 34-46 deg mask covered 64% of the D211 Mountains (Sierra lidar: 22% over 46 deg), so the mask is 40-52 deg. Hard steps between blocks left 470 edges over 15 m (combs) on the 2 km High mesh; smooth cells left 7. About 2% of faces still lean past vertical where blocks push out of steep walls
- 2026-11-14 numbers, 2 km High, T6b's way (main -> branch, real Sierra): over 60 deg 17.6 -> 19.8% (11.7); 64 m roughness 0.443 -> 0.446 (0.227, waived D211); smoothness 2-16 m 0.98 -> 0.95 (0.89); crest sharpness 87 -> 513 (1351; the review's 38 was before D211). Seen from above (points binned back to a grid): smoothness 0.84, crest 1277. T6b Mountains PASS. Build at High 21.8 -> 23.9 s, re-evaluation 5.1 -> 7.0 s
- 2026-11-14 sharp summits: NOT reached by the breakup. It only works where the ground is steep, and a dome top is flat. Scratch test on the board (right column, not in the branch): a crest sharpen, lift = (Rc / 2) x (s0 - slope)^2 on high convex ground, slope from the normal and convexity from 4 extra reads of the erosion map. It turns round tops into edges and points but leaves small spikes along ridges. Needs its own ticket or a place in LG-079; Mike decides

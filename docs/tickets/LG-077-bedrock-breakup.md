# LG-077 Bedrock breakup stage on the finished mesh
Type: feature | Milestone: Model realism | Phase: B2 Model realism | Size: M-L | Priority: P1
Status: in progress | Lane: side | Needs Blender: yes | Mike review: yes
Depends on: LG-076 | Blocks: LG-082

## Why
Nothing exists between the 16 m shape floor and the 1 m grain, so rock faces read as pillows. A scratch breakup lifted Mountains from 2.9% to 8.6% over 60 deg and smoothness from 0.99 to 0.89 (real 0.89) (review S4). This is secondary volume (5-60 m), so it belongs in the mesh, not the material (D157, D163).

## Done when
- Moved to LG-086 (Mike, 2026-11-15): sharp summits and knife-edge crests (Mike, 2026-11-12: 'we need to resolve getting sharp mountain tops... overall sharper, more realistic mountains'): the highest peaks read as horns and aretes, not domes, in the wide and mid clay shots; crest sharpness measured as in the realism review (today 38, real Sierra 1351) and logged
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
- 2026-11-15 checkpoint 1 finished (Fable 5.2): board, library and log committed (7bb04af). Test renumbered T42 -> T43, LG-078 owns T42 (36584a5). Full suite on Blender 5.2: 38/38 passed, T43 'rock over 50 deg moved 4.4 m rms, ground under 30 deg 0.00 m'
- 2026-11-15 board c191 top-down tile was half blank: the camera sat on the highest point (x 965, y 778), 59 m from the east edge of the 2048 m mesh, so a 700 m frame showed 58% landscape (computed from the baked points, matches the tile). Not clip distance. Both top-down tiles now frame an inner summit (36584a5)
- 2026-11-15 Mike on c191: "This is still much better". Crest sharpening broken out into LG-086 (Mike); the sharp-summits line moved there
- 2026-11-15 commits for checkpoint 1: build 68b6526 (WIP), board and library 7bb04af, T42 renumbered T43 36584a5, log 3a742e7, LG-086 ticket 07190a1. Suite 38/38 (Fable 5.2)
- 2026-11-15 code review (mattpocock-skills:code-review, Sonnet, both axes): T43 read the grid by point order (now binned by position), long comments trimmed to one line, Log refs added; T43 rerun PASS (4.4 m rms, 0.00 m). Open for Mike: Done when still says 34-46 deg (code uses 40-52, logged 2026-11-14); over 60 deg moved away from real (17.6 -> 19.8%, real 11.7); re-evaluation 5.1 -> 7.0 s. Carried to checkpoint 2: beds skip the fold limiter on walls over 59 deg; the 9 m size dropping out at Preview is untested; rock patches only scale the mask (60% minimum)
- 2026-11-15 checkpoint 1 merged to main a4596cd (Mike approved). Checkpoint 2 (Glacial, Canyon, Mesa, Cliffs, Badlands) next; sharp summits are LG-086
- 2026-11-15 lessons: worked: counting before fixing (the 34-46 mask covered 64% against the lidar's 22%; hard block steps made 470 combs, smooth cells 7), and checking the old tiles framed the subject before re-rendering (no new renders needed). Didn't: two parallel lanes both took T42 and GROUP_VERSION 145 (LG-078), costing a renumber and a library rebuild after the second merge; the top-down camera centred on the highest point, which sat 59 m from the edge (half-blank tile); T43 read the grid by point order despite the rule (review caught it). Proposed rule for Mike: lanes claim their test number and GROUP_VERSION when they start

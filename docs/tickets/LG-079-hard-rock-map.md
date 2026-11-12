# LG-079 Hard-rock map and bedrock structure for Mountains
Type: feature | Milestone: Model realism | Phase: B2 Model realism | Size: M | Priority: P2
Status: todo | Lane: side | Needs Blender: yes | Mike review: yes
Depends on: LG-076, LG-078 | Blocks: LG-082

## Why
Mountains have no hardness map, so erosion can't leave cliff bands, ribs and couloirs. With S1 it added ribs along the crests; alone it did almost nothing (review S2).

## Done when
- Sharp summits and knife-edge crests (Mike, 2026-11-12: 'we need to resolve getting sharp mountain tops... overall sharper, more realistic mountains'): the highest peaks read as horns and aretes, not domes, in the wide and mid clay shots; crest sharpness measured as in the realism review (today 38, real Sierra 1351) and logged
- `hard_mountains` field in `hard_by_recipe`: rock on steep high ground, soft beds about one in three, soft joints from ridged noise
- Ridged and strata structure added before erosion where rock is high
- Board with S1 vs S1+S2, crest sharpness measured
- GROUP_VERSION bump, library rebuilt, suite passes, code review, Mike signs off

## Files
- `kitbash_landscape_generator/nodes.py`
- `kitbash_landscape_generator/node_groups.blend`
- `tests/run_tests.py`

## Agent brief
Read docs/REVIEW-realism-2026-11.md S2 and the appendix `hard_mountains()`, `crag_shape()`. Voronoi cell borders as joints drew a polygon net: don't use them. Glacial and Volcano can reuse the field later.
Also read docs/tickets/README.md (rules every ticket follows) and docs/CODING.md.

## Log
- 2026-11-11 created from the realism review (D209)
- 2026-11-12 Mike picked incision 1.8 (LG-076) and asked for sharp mountain tops: added to Done when

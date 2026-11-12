# LG-076 Retune erosion so it carves (Mountains, Glacial, Canyon)
Type: feature | Milestone: Model realism | Phase: B2 Model realism | Size: S | Priority: P1
Status: todo | Lane: main | Needs Blender: yes | Mike review: yes
Depends on: LG-075 | Blocks: LG-077, LG-079

## Why
Mountains are domes: incision 0.5 is too weak and the finishing blur smears edges about 15 m. Incision 1.8 alone gave ridgelines and V valleys in scratch (review S1, board docs/realism/c186_realism_mountains-solutions.png).

## Done when
- Board for Mike: Mountains at incision 1.2, 1.5 and 1.8 beside the Sierra lidar and two photos; Mike picks
- `types.json` set: incision, channel 0.0005 -> 0.0003, finish_blur 16 -> 8, cliff_deg 60 -> 75, talus_deg 38 -> 35, soften 0.2 -> 0.1; Glacial incision 1.0, soften 0.2; Canyon finish_blur 8
- Share over 60 deg near the lidar's 11% (today 2.9%); T6 and T6b bands re-based with Mike's OK
- Wide shot checked for drips at the tile edge (seen on the S1+S2 board)
- Full suite passes

## Files
- `kitbash_landscape_generator/types.json`
- `tests/realism.py` (bands, if re-based)

## Agent brief
Read docs/REVIEW-realism-2026-11.md S1. Settings only, no code. Changes how saved landscapes erode: say so in the log. 1.8 overshoots a little; 3 with channel 0.0001 over-dissects into a comb.
Also read docs/tickets/README.md (rules every ticket follows) and docs/CODING.md.

## Log
- 2026-11-11 created from the realism review (D209)

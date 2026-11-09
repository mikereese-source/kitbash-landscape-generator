# LG-004 Trim floor apron in front of the mouth
Type: bug | Milestone: M5 5.5 | Phase: A Cave fixes | Size: S | Priority: P2
Status: review | Lane: main | Needs Blender: yes | Mike review: yes
Depends on: none | Blocks: LG-008, LG-016

## Why
The floor runs about one entrance width past the mouth; on Jointed its edge is saw-toothed (D196).

## Done when
- Apron shorter, edge soft on all three rocks
- T14 floor-out-front check still passes

## Files
- `kitbash_landscape_generator/features.py`

## Agent brief
apron_grid = cut_at(-0.5, 11.9, ...) in the mouth block.
Also read docs/tickets/README.md (rules every ticket follows).

## Log
- 2026-11-08 created (D201)
- 2026-11-09 built (CAVE_VERSION 206, board docs/m5/c174_step1_fixes.png, tests 30/30): apron about a third of the width out (was half), wandering gently (wander 0.3, scale 1.2, detail 2) so it no longer saws; T14 floor probe at 0.1 W. Waiting on Mike's review

# LG-066 Flooded chamber water pokes out of the cave
Type: bug | Milestone: M5 | Phase: A Cave fixes | Size: S-M | Priority: P1
Status: done | Lane: main | Needs Blender: yes | Mike review: no
Depends on: none | Blocks: none

## Why
On Lava Tube with Flooded Chamber the water sheet sticks out through the bottom of the rock body below the mouth, as a flat plate with a ragged edge outside the cave (review 2026-11-09, lava shots 2-3). Probably the water is clipped by a distance field that doesn't match the hollow body near the mouth.

## Done when
- Water stays inside the cave on all three rocks at every Water Level
- T33 extended: no water faces outside the rock body

## Files
- `kitbash_landscape_generator/features.py`
- `tests/run_tests.py`

## Agent brief
Read D193, PLAN-flooded-chamber.md, D196 (hollow body, lg_odist). Related: LG-063 (holes in the water). Mike's screenshots 2026-11-09 (lava review) in docs/m5/review-2026-11-09/
Also read docs/tickets/README.md (rules every ticket follows).

## Log
- 2026-11-09 created from Mike's review (lava)
- 2026-11-09 prioritized P1, step 5 of the review order (TICKETS.md)
- 2026-11-09 built (CAVE_VERSION 206, board docs/m5/c174_step1_fixes.png, tests 30/30): same change: the space test keeps the sheet out from under the rock body. Waiting on Mike's review
- 2026-11-13 Mike approved (board c174) -> done

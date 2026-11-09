# LG-063 Holes in the flooded chamber water next to pieces
Type: bug | Milestone: M5 | Phase: A Cave fixes | Size: S-M | Priority: P1
Status: review | Lane: main | Needs Blender: yes | Mike review: no
Depends on: none | Blocks: none

## Why
With Flooded Chamber on Jointed the water sheet has holes cut next to the jointed pieces / columns standing in it (review 2026-11-09, jointed shot 6). Probably the water is cut by a zone around each piece.

## Done when
- Water is one flat sheet wall to wall with no holes beside pieces, columns or formations
- T33 extended to check for holes near pieces

## Files
- `kitbash_landscape_generator/features.py`
- `tests/run_tests.py`

## Agent brief
Read D193 and PLAN-flooded-chamber.md. Check how the sheet is clipped to the cave space (formation clearance zones?). Mike's screenshots 2026-11-09 (jointed review) in docs/m5/review-2026-11-09/
Also read docs/tickets/README.md (rules every ticket follows).

## Log
- 2026-11-09 created from Mike's review (jointed)
- 2026-11-09 prioritized P1, step 4 of the review order (TICKETS.md)
- 2026-11-09 built (CAVE_VERSION 206, board docs/m5/c174_step1_fixes.png, tests 30/30): flood sheet kept by a ray against the cave's space AND the finished mesh, a jointed piece above counting as inside: no holes beside pieces. Waiting on Mike's review

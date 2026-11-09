# LG-003 Floating piles in cave renders
Type: bug | Milestone: M5 | Phase: A Cave fixes | Size: S | Priority: P1
Status: blocked | Lane: main | Needs Blender: yes | Mike review: yes
Depends on: none | Blocks: LG-016

## Why
Mike saw floating piles in the c171 renders; the first-pass reviewer did not find them (PARKING).

## Done when
- Mike names the render and spot
- Cause traced; no rock or heap floats at any Detail Level
- A check added to T14 or a new test

## Files
- `kitbash_landscape_generator/features.py`
- `kitbash_landscape_generator/rocks.py`

## Agent brief
Blocked on Mike: which render and where. on_floor() already drops rocks with Y < -0.3W.
Also read docs/tickets/README.md (rules every ticket follows).

## Log
- 2026-11-08 created (D201)

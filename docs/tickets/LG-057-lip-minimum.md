# LG-057 Lip minimum 0.25, default 0.3, and fix pinches
Type: bug | Milestone: M5 | Phase: A Cave fixes | Size: S-M | Priority: TBD (set after Mike's full review)
Status: todo | Lane: main | Needs Blender: yes | Mike review: yes
Depends on: none | Blocks: none

## Why
At Lip 0.2 and below the lip turns into thin flaps that look like errors (shot 3 at 0.10, shot 2 at 0.15). 0.25 is getting there, 0.3 looks good, but even 0.3 has some pinches (review 2026-11-09).

## Done when
- Lip slider runs from 0.25; default 0.3; old files below 0.25 open at 0.25
- No pinches or thin flaps at 0.25-0.4 on all three rocks
- T14 Lip check updated (0.25 < 0.3 < 0.4)

## Files
- `kitbash_landscape_generator/features.py`
- `kitbash_landscape_generator/caves.py`
- `tests/run_tests.py`

## Agent brief
Lip FloatProperty is 0.05-0.4, default 0.15 in caves.py. wall_t = max(W x Lip, 1.5 voxels) at the mouth (D197). Find the pinch spots at 0.3 on a board before changing code. Mike's screenshots 2026-11-09 (limestone review), copied to docs/m5/review-2026-11-09/
Also read docs/tickets/README.md (rules every ticket follows).

## Log
- 2026-11-09 created from Mike's review (limestone)

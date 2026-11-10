# LG-057 Lip minimum 0.3, range to 0.5, and fix pinches
Type: bug | Milestone: M5 | Phase: A Cave fixes | Size: S-M | Priority: P1
Status: review | Lane: main | Needs Blender: yes | Mike review: yes
Depends on: none | Blocks: none

## Why
At Lip 0.2 and below the lip turns into thin flaps that look like errors (shot 3 at 0.10, shot 2 at 0.15). 0.25 is getting there, 0.3 looks good, but even 0.3 has some pinches (review 2026-11-09).

## Done when
- Lip slider runs 0.3-0.5 (or more); default 0.3; old files below 0.3 open at 0.3
- No pinches or thin flaps at 0.3-0.5 on all three rocks
- T14 Lip check updated (0.3 < 0.4 < 0.5)

## Files
- `kitbash_landscape_generator/features.py`
- `kitbash_landscape_generator/caves.py`
- `tests/run_tests.py`

## Agent brief
Lip FloatProperty is 0.05-0.4, default 0.15 in caves.py. wall_t = max(W x Lip, 1.5 voxels) at the mouth (D197). Find the pinch spots at 0.3 on a board before changing code. Mike's screenshots 2026-11-09 (limestone review), copied to docs/m5/review-2026-11-09/
Also read docs/tickets/README.md (rules every ticket follows).

## Log
- 2026-11-09 created from Mike's review (limestone)
- 2026-11-09 Mike (lava review): 0.3 is the minimum for all rocks; 0.4-0.5 give some pretty cool results. Minimum raised to 0.3, range up to at least 0.5
- 2026-11-09 prioritized P1, step 1 of the review order (TICKETS.md)
- 2026-11-09 built (CAVE_VERSION 206, board docs/m5/c174_step1_fixes.png, tests 30/30): Lip range 0.3-0.5, default 0.3, old caves open at 0.3; T14 checks 0.3 < 0.4 < 0.5. Pinches: the dark grooves stay with the lip surface off, so they come from the base shape's roof ledges/cut lines; need Mike to circle the pinches he means on c174. Waiting on Mike's review
- 2026-11-10 Mike: the lip is good. Slider now reads 0.1-1 and maps to 0.3-0.8 of the entrance width (caves.lip_thickness; 0.1 = the old 0.3 minimum, 1 = a heavy hood); default 0.1. T14 checks 0.1 < 0.55 < 1. Board docs/m5/c176_lip_range.png. Caves saved with the old 0.3-0.5 values now read a little thicker
- 2026-11-10 Mike: maximum 0.7 (was 0.8); T14 passes

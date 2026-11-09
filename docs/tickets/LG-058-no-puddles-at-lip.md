# LG-058 No puddles at the lip
Type: bug | Milestone: M5 | Phase: A Cave fixes | Size: S | Priority: P1
Status: review | Lane: main | Needs Blender: yes | Mike review: no
Depends on: none | Blocks: none

## Why
With Puddles at 0.8 a little water shows up right at the lip, which reads as an error (review 2026-11-09, shot 6).

## Done when
- No puddle within the mouth zone at any Puddles value
- Puddles still form inside the cave

## Files
- `kitbash_landscape_generator/features.py`

## Agent brief
Puddles are the silt-flat hollows (D193 area). Mask them with the same at_mouth / lg_outer test the lip uses.
Also read docs/tickets/README.md (rules every ticket follows).

## Log
- 2026-11-09 created from Mike's review (limestone)
- 2026-11-09 prioritized P1, step 2 of the review order (TICKETS.md)
- 2026-11-09 built (CAVE_VERSION 206, board docs/m5/c174_step1_fixes.png, tests 30/30): no puddles within 0.75-1.0 of the width (where the lip surface ends) or on the rock body's outside. Waiting on Mike's review

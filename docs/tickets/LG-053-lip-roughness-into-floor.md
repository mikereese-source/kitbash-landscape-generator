# LG-053 Carry the lip roughness into the cave floor
Type: feature | Milestone: M5 | Phase: A Cave fixes | Size: M | Priority: P2
Status: done | Lane: main | Needs Blender: yes | Mike review: yes
Depends on: none | Blocks: none

## Why
Mike likes the limestone lip's roughness and wants some of it on the floor and lower walls at the mouth, so the lip is integrated with the cave instead of sitting on a smooth floor (review 2026-11-09, shot 4: arrow from the lip down onto the floor).

## Done when
- The rough lip surface fades into the floor and wall foot at the mouth, no hard line
- Walk-in floor stays walkable (T14 floor check passes)
- Board against cave-mouth references

## Files
- `kitbash_landscape_generator/features.py`

## Agent brief
The lip surface is position noise in the mouth push block (D197), masked by at_mouth and Z > 0.06-0.2 H. Extend it down with a softer fade rather than a second noise. Mike's screenshots 2026-11-09 (limestone review), copied to docs/m5/review-2026-11-09/
Also read docs/tickets/README.md (rules every ticket follows).

## Log
- 2026-11-09 created from Mike's review (limestone)
- 2026-11-09 prioritized P2, step 10 of the review order (TICKETS.md)
- 2026-11-10 built by Opus 5.5 (CAVE_VERSION 208, board docs/m5/c180_lip_roughness.png, T14/T31/T33 pass): the lip surface now also covers the floor at the mouth at a third of its strength, so the floor stays walkable (T14 flat floor passes). Waiting on Mike's review
- 2026-11-13 Mike approved (board c180) -> done

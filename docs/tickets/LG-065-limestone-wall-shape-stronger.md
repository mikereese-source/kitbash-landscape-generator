# LG-065 Limestone Wall Shape: make 1.0 much stronger
Type: feature | Milestone: M5 | Phase: A Cave fixes | Size: S | Priority: P1
Status: todo | Lane: main | Needs Blender: yes | Mike review: yes
Depends on: none | Blocks: none

## Why
On Limestone the Wall Shape (wall detail) slider is too subtle. 0 is fine; 1.0 should be about 2-3x what it is now (review 2026-11-09).

## Done when
- Wall Shape 1.0 reads 2-3x stronger on Limestone; 0 unchanged; 0.5 default still looks right
- Board at 0 / 0.5 / 1.0 against limestone references
- Tests pass

## Files
- `kitbash_landscape_generator/features.py`

## Agent brief
Read D158-D163 (limestone walls). Check the push doesn't break the wall thickness (lg_odist) or the lip.
Also read docs/tickets/README.md (rules every ticket follows).

## Log
- 2026-11-09 created from Mike's review (jointed)
- 2026-11-09 prioritized P1, step 7 of the review order (TICKETS.md)

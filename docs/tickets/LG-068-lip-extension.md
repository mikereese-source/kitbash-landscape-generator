# LG-068 Extend the lip outward (all three rocks)
Type: feature | Milestone: M5 | Phase: A Cave fixes | Size: M | Priority: TBD (set after Mike's full review)
Status: todo | Lane: main | Needs Blender: yes | Mike review: yes
Depends on: none | Blocks: none

## Why
Mike would like a control to extend the lip entrance outward, for all three rocks, so artists get more of a hood over the mouth. Skip it if it causes a lot of problems (review 2026-11-09).

## Done when
- Short feasibility note first (what it costs in the SDF mouth cuts)
- If built: a Lip Reach control; no thin spots, pinches or floating pieces at any value
- T14 still passes

## Files
- `kitbash_landscape_generator/features.py`
- `kitbash_landscape_generator/caves.py`
- `tests/run_tests.py`

## Agent brief
The front cuts (cut_at, steps) set where the lip ends; a reach control would shift the front cut and roof ledges outward. Check against LG-057's thickness rules.
Also read docs/tickets/README.md (rules every ticket follows).

## Log
- 2026-11-09 created from Mike's review (lava)

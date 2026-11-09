# LG-062 Puddles slider greyed out on Jointed
Type: bug | Milestone: M5 | Phase: A Cave fixes | Size: S | Priority: TBD (set after Mike's full review)
Status: todo | Lane: main | Needs Blender: yes | Mike review: no
Depends on: none | Blocks: none

## Why
With Water set to Puddles on Jointed the Puddles slider is greyed out and no puddles form. Mike sees no reason Jointed can't have puddles (review 2026-11-09, jointed shot 5).

## Done when
- Puddles work on Jointed (and Lava, unless there's a reason; say so)
- Puddles stay off the lip (LG-058)

## Files
- `kitbash_landscape_generator/features.py`
- `kitbash_landscape_generator/caves.py`

## Agent brief
Find where the panel disables Puddles by Rock in caves.py and where the puddle hollows are gated in features.py.
Also read docs/tickets/README.md (rules every ticket follows).

## Log
- 2026-11-09 created from Mike's review (jointed)

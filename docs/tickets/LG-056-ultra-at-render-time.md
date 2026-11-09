# LG-056 Ultra at render time (and camera-based detail)
Type: feature | Milestone: M5 | Phase: A Cave fixes | Size: M-L | Priority: TBD (set after Mike's full review)
Status: todo | Lane: main | Needs Blender: yes | Mike review: yes
Depends on: none | Blocks: none

## Why
Ultra as real geometry is about 25-28M faces. Mike wants Ultra applied at render time instead, so the viewport stays fast and artists control the cost; and asks if detail can follow a camera (review 2026-11-09).

## Done when
- Short options note first: Cycles adaptive subdivision with displacement (its Dicing Camera makes detail camera-based), a baked displacement map, and what Eevee can do
- Mike picks; the chosen path built and measured (viewport faces, render time, look vs current Ultra)

## Files
- `kitbash_landscape_generator/features.py`
- `kitbash_landscape_generator/caves.py`

## Agent brief
Cycles adaptive subdivision is per object and uses the scene's Dicing Camera, so near rock gets more detail than far rock. Eevee has no adaptive subdivision. Ties into LG-016 (speed pass) and LG-054.
Also read docs/tickets/README.md (rules every ticket follows).

## Log
- 2026-11-09 created from Mike's review (limestone)

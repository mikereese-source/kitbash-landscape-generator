# LG-016 Cave speed pass
Type: perf | Milestone: M5 | Phase: B M5 finish | Size: M | Priority: P2
Status: todo | Lane: main | Needs Blender: yes | Mike review: yes
Depends on: LG-001, LG-002, LG-003, LG-004, LG-005, LG-008, LG-009, LG-013, LG-052 | Blocks: LG-017

## Why
The hollow rock body doubles faces and build time (194k Preview, 5.8M High, Ultra ~25-28M). Quality first, then speed (D196, D197).

## Done when
- Faster with no visible loss at every Detail Level (board side by side)
- Options tried: coarser outside, fewer cut grids, Bake node cache, render-time displacement for Ultra
- The first build of a new cave is much faster (Mike, review 2026-11-09: "it takes a long time for the initial cave to build"); time it before and after

## Files
- `kitbash_landscape_generator/features.py`

## Agent brief
Read PARKING 'Cave speed pass'. Do only after Mike signs off cave quality.
Also read docs/tickets/README.md (rules every ticket follows).

## Log
- 2026-11-08 created (D201)
- 2026-11-09 Mike: initial cave build is slow; added to Done when. See also LG-054 (separate Detail Levels), LG-056 (Ultra at render time)

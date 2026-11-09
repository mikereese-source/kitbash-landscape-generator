# LG-061 Rethink the rubble heaps and rubble scatter
Type: feature | Milestone: M5 | Phase: A Cave fixes | Size: M-L | Priority: P1
Status: todo | Lane: main | Needs Blender: yes | Mike review: yes
Depends on: none | Blocks: none

## Why
Mike likes having rock piles, but on Jointed they don't make sense: some float, they don't fall naturally, many overlap, they are all about the same size, and they sit in unnatural piles in the corners. Spread seems to do nothing; Rock Size scales them all together, so the spread of sizes is what's missing (review 2026-11-09, jointed shots 1, 2, 5). This is also where the floating piles were (LG-003).

## Done when
- Options note first with references (rockfall / breakdown piles, talus at the wall foot): how piles form, size mix, where they sit
- Mike picks the approach
- No rock floats or deeply overlaps another; a real size mix (few big, many small); Spread visibly changes the pile
- Checked on all three rocks

## Files
- `kitbash_landscape_generator/features.py`
- `kitbash_landscape_generator/rocks.py`

## Agent brief
Read D108 (rock library), D192 (heap Rock Size bug), on_floor(). Look at why Spread has no effect before anything else. Mike's screenshots 2026-11-09 (jointed review) in docs/m5/review-2026-11-09/
Also read docs/tickets/README.md (rules every ticket follows).

## Log
- 2026-11-09 created from Mike's review (jointed)
- 2026-11-09 Mike (lava review): the lava rubble also overlaps oddly at times (lava shot 1). Use the same new scatter for all rubble, not only the Jointed heaps
- 2026-11-09 prioritized P1, step 15 of the review order (TICKETS.md)
- 2026-11-09 options note written: docs/RESEARCH-rubble.md (Spread is never read by the Jointed heaps; recommends a layered drop big-medium-small with culling and raycast stacking). Waiting on Mike's pick

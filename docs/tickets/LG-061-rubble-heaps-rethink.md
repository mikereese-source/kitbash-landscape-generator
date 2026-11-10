# LG-061 Rethink the rubble heaps and rubble scatter
Type: feature | Milestone: M5 | Phase: A Cave fixes | Size: M-L | Priority: P1
Status: ready | Lane: main | Needs Blender: yes | Mike review: yes
Depends on: none | Blocks: none

## Why
Mike likes having rock piles, but on Jointed they don't make sense: some float, they don't fall naturally, many overlap, they are all about the same size, and they sit in unnatural piles in the corners. Spread seems to do nothing; Rock Size scales them all together, so the spread of sizes is what's missing (review 2026-11-09, jointed shots 1, 2, 5). This is also where the floating piles were (LG-003).

## Done when
Option B, layered drop (Mike, 2026-11-10, D204; docs/RESEARCH-rubble.md). Four checkpoints, Mike reviews each:
1. Spread wired in everywhere (the Jointed heaps never read it) and a real size mix: power law, Big really big, Small used
2. Layered drop on the Jointed heaps: big, then medium, then small; each culled against the layer before and raycast onto the floor plus the rocks below; slope limit so nothing leans steeply; piles sit where rock falls (under wide roof, wall foot), not random corners
3. Limestone and Lava foot rubble and the ramp scree on the same scatter
4. Side-by-side board against the reference photos for all three rocks; rebuild time measured (budget about +10-30%)
- No rock floats or deeply overlaps another at any Detail Level; tests added
- Option C (physics settle bake) stays parked

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
- 2026-11-10 Mike chose option B (layered drop), D204

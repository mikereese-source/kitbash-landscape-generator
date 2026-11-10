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
- 2026-11-10 WIP, checkpoints 1 and 2 on the Jointed heaps (model: Claude Fable 5.2, claude-fable-5-2; branch lg-061-rubble; CAVE_VERSION 207). Stopped early on the usage limit: NOT done, T35 fails
  - Built: heap block in features.py replaced by a layered drop. Piles sited where rock falls (mid floor weighted by chamber / bend / junction, or at the wall foot); Spread scales each footprint 0.6x-1.4x; five sizes 2.2 to 0.27 of the old block (Big kit really big, Small kit used); each layer Poisson-spaced, raycast onto the floor plus the Preview rocks of the layers before, 40 degree slope limit, six level rays cull overlap, tipped to the hit, sunk 18%. New inputs Rubble Big/Medium/Small Proxy (Preview kit, set in caves.py). Rocks keep clear of the jointed masses by rule (h_edge), not by reading them (they follow each level's wall; reading them gave 845 vs 847 rocks at Preview vs High)
  - Measured (Preview rebuild, min of 3): default Jointed 1.37 s before, 1.34 s after; Mike's review cave 1.44 s before, 1.39 s after; High 13.2 s before, 12.1 s after. Mike's cave: 117 rocks before, 1068 after (5 big, 103 medium, 960 small, 0.94 to 10.1 m), same count at Preview and High
  - Open: T35 (added to tests/run_tests.py) fails: 53 of 1850 rocks in its test cave sit 1-2 m over what is under their middle (35 of 1068 in Mike's cave), about 1% sit over half inside a bigger rock. Not diagnosed: suspect the last step (each rock moved by the finished-floor difference under its own spot, so a stack can come apart) or small rocks tipped on a rock's shoulder. Next: debug those rocks, then T14, T15, T35 and the full suite (none run yet on this branch), Ultra check, rebuild node_groups.blend
  - Board docs/m5/c178_rubble_layered_wip.png (Preview, rendered from this branch: tests/render_view.py now imports its own checkout). Stacks at pile centres read a little like cairns; Stretch is not wired into the heaps; Spread under 0.5 shrinks piles (fewer rocks) as density is already at its cap

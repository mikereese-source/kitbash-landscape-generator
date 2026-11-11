# LG-061 Rethink the rubble heaps and rubble scatter
Type: feature | Milestone: M5 | Phase: A Cave fixes | Size: M-L | Priority: P1
Status: in progress | Lane: main | Needs Blender: yes | Mike review: yes
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
- 2026-11-11 Checkpoints 1 and 2 finished on the Jointed heaps, ready for Mike's review (model: Claude Fable 5.2, claude-fable-5-2; branch lg-061-rubble; CAVE_VERSION 210). Commits: 702032e (main merged in, 209 + 1), 3a6201a (the floating fix), d062687 (piles and Spread), and this wrap-up
  - Floating, diagnosed with numbers (T35's cave, 53 of 1,850 rocks floating): 15 came from the last step (each rock moved by the finished-floor difference under its own spot, so a stack came apart), 38 from rocks landing on a block's bevelled edge and hanging off its side. All 53 were tipped rocks, none on flat floor. Fix: each stack moves onto the finished floor as one (every rock carries the floor spot of the rock at the bottom of its stack, "h_anchor"), and a rock must have ground under four more spots across its width. 0 floating and 0 deep overlaps after, at Preview, High and Ultra (Mike's cave: the same 924 rocks at each)
  - Cairns: big blocks now lie round each pile's toe (fall sorting, ref 9), medium rocks make the body, and no rock lands higher than a 22 degree cone over the pile's footprint (refs 1, 3). Big blocks all sit on the floor
  - Spread keeps the rock count: footprint 0.75x at 0, 0.9x at 0.5, 1.35x at 1, the rock thinned by the area. T35's cave: 841, 933, 974 rocks at Spread 0, 0.5, 1; footprint 945 to 1,530 m2
  - Tests: T35 extended (pile no taller than the cone, big blocks on the floor, Spread keeps the count within 25%) and passing; full suite 33/33
  - Timings (rebuild, min of 3; main at 209 measured in the same run, then this branch): default Jointed Preview 1.36 s, now 1.34 s; default High 39.65 s, now 39.52 s; Mike's cave Preview 1.45 s, now 1.45 s; Mike's cave High 11.87 s, now 11.87 s. No cost (the 2026-11-10 numbers were 1.37, 1.44 and 13.2 s at 206)
  - Board docs/m5/c178_rubble_layered.png: before (206) and after (210) at Preview and High, and a pile close-up
  - Not sure about: (1) the middle Spread packs each size at two thirds of its tightest, so piles are a little looser than the WIP board; (2) the big blocks stand clear of the pile's middle, which can read as a ring on a small pile; (3) rocks lean to the Preview-grid floor, not the finished floor, so a few sit a little tipped on flat ground; (4) the no-floating check measures under a rock's middle only
  - Left for checkpoint 3: Limestone and Lava foot rubble and the ramp scree onto the same scatter; Stretch is still not wired into the heaps. Checkpoint 4: the board against the reference photos for all three rocks
- 2026-11-11 cp1-2 merged into main (CAVE_VERSION 210, suite 35/35, board c178). Review logged; carried to cp3/4: several floor samples under big rocks, T35 edge + Ultra checks, Scree proxies, tidy h_layer, Tilt kept unless Mike says otherwise. Look note: small rocks read as rounded pills, sparse; check against gravel references in cp4
- 2026-11-11 lessons (Fable 5.2): counted and sorted all 53 failures by cause before fixing; placement on Preview stand-ins so every level matches at no cost; rules from real rockfall (power law, toe sorting, cone cap); timings against main in the same run; clean WIP handoffs. Weak: middle-only test, small scope creep (Tilt), long function with magic numbers. Four rules added to CODING.md (770f70b)

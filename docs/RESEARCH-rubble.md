# Research: rubble heaps and rubble scatter (LG-061)

2026-11-09. Research only. No code changed. Mike picks an option (section 3) before any build.

Mike's review: piles float in places, overlap a lot, are all about one size, sit in odd heaps in corners. Spread seems dead. Rock Size scales everything together. He wants piles kept, but natural. The lava rubble overlaps too, so the fix covers all rubble, not only Jointed.

## 1. Why Spread does nothing (on Jointed)

Spread is read in two places only. Both are switched off on Jointed. The heaps never read it.

- `kitbash_landscape_generator/features.py:441` declares the `Spread` socket. `caves.py:183` says what it should do: "Rocks kept tight to the walls (0), or strewn out across the floor (1)".
- `features.py:615` uses Spread to pull the wall-foot rubble rows in off the wall (`reach_out`).
- `features.py:646-647` uses Spread to throw pebbles out across and along the floor.
- `features.py:637` sets `not_jointed = 1 - (Rock == 1)`. Lines 638, 639 and 652 multiply the big, medium and pebble keep masks by it. On Jointed, all three are 0, so no wall-foot rubble and no pebbles are made. The only Spread-driven rocks are gone.
- `features.py:1876-1938` builds the Jointed breakdown heaps. Nothing in that block reads `gin["Spread"]`. Heap radius is `r * rand(0.5, 0.8)` (1899). The apron reach is a fixed `rand(0, 0.35)` (1910).

So on Jointed, Spread changes nothing at all. That is the bug, not a weak setting.

On Limestone and Lava, Spread does work, but weakly:
- Medium and big rubble move in by at most `0.4 * r * Spread` (615). At the default 0.5, the mean shift is 0.1 of the passage radius. That is hard to see.
- The extra rocks from Rubble (`more`, 622-623) spread along the passage by a fixed `rand(-0.7, 0.7)`. They ignore Spread.
- Most of the visible change is in the pebbles (646-647). Pebbles are small, so the slider reads as "nothing happens".

### Other causes found while reading (same code)

- **All one size (heaps).** Block size is `hr * 0.14 * Rock Size * (0.5 .. 1.1) * rand(0.7, 1.3)` (1922-1923). That is a narrow, flat (uniform) spread: about 3x from smallest to largest.
- **Big blocks are not big (heaps).** The Big kit is built 2-3x a medium rock (`rocks.py:18`). The heap then scales it by `k = 0.4` (1934, 1937). 0.4 x 2-3 = 0.8-1.2. The "big" blocks end up the same size as the medium ones. The Small kit is never used in heaps.
- **All one size (wall-foot rubble).** Size is `rock_r * rand(0.12, 0.32) * 0.8` (674), again a flat range. Real rubble is many small, few big (section 2).
- **Floating (heaps).** Each block is put on an imaginary cone: ground height plus `cone = hr * 0.65 * (1 - d)^0.8` (1924-1926). The cone is not geometry. Blocks under a block are random, so where no block happens to sit below, the upper one hangs in air.
- **Overlap (heaps and rubble).** Points are plain random (`sqrt(rand)` disc, 1910). Random points clump and leave holes. Clumps overlap deeply; holes cause the floating. Nothing checks rock against rock. The only tests are rock against the cave walls (1840-1849, 1926-1931).
- **Heaps in corners.** Heap centres are Poisson points on any floor face past 30% of the cave (1891-1898). They are not tied to a roof break or a wall. Where a heap meets a wall, the wall test (1926-1931) deletes the blocks that touch it, leaving a cut-off cone jammed in the corner.
- **Tumble.** Blocks tip up to +-0.7 rad (40 degrees) on X and Y (1933), whatever is under them. Some stand on an edge.

## 2. What real cave rubble looks like

### How it forms
- **Breakdown** is rock fallen from the roof or upper walls that has not moved far from where it broke. Cavers class it as block, slab, plate and chip (Davies 1949, in White and White 1969).
- Shape follows the bedding. Thin-bedded rock drops flat slabs and plates. Massive rock drops chunky blocks. Jointed rock drops blocks bounded by joint planes: flat faces, sharp edges.
- Piles sit **under the roof that failed**. Wide spans fail first: chambers, junctions, bends. The roof above a pile is often a flat, freshly broken ceiling or a dome.
- Big piles can fill a passage wall to wall (Violet City, Mammoth Cave) or sit as one giant block (Giant's Coffin).
- **Lava tubes** shed rock as the lining cools and cracks. Floors get rubble-strewn stretches between clear ones. Where the roof falls in, a skylight or collapse trench forms. Coarse talus piles sit at the foot of those collapse walls. Big roof blocks (up to about 6 m long at Lava Beds) lie half buried in smaller roof debris (USGS Bulletin 1673).
- **Wall-foot talus**: rock spalls off the wall and collects as an apron against it. The apron slope stands at about 35 degrees at most. It is sorted: small stuff near the wall and the top, the biggest blocks roll furthest and end at the toe.

### Size mix
- Rockfall fragment sizes follow a power law above a small cut-off. Many small, few big. The count of rocks bigger than a size falls steeply as size grows (Ruiz-Carulla et al. 2015; Lanfranconi et al. 2024; USGS rockfall fragmentation).
- Rule of thumb for us: per pile, about 1 big : 5-8 medium : 25-40 small. Sizes vary about 10x across a pile, not 3x.
- Small pieces fill the gaps between big ones. That is why piles look solid and nothing hangs in air.

### How rocks sit
- Every rock rests on something: the floor or two or three rocks under it.
- Big blocks lie flat-side down. Slabs lie flat or lean against a bigger block or the wall.
- Rocks touch, but never pass through each other. A small rock can tuck into a gap under a big one.
- A pile is low and wide: a cone or fan at 25-35 degrees. Its edge feathers out into scattered small rocks across the floor.

### Reference photos (view only, nothing downloaded)

| # | What it shows | Link | Licence |
|---|---|---|---|
| 1 | Violet City, Mammoth Cave: a breakdown pile filling the passage | https://commons.wikimedia.org/wiki/File:Breakdown_(Violet_City,_Mammoth_Cave,_Kentucky,_USA).jpg | CC BY 2.0, James St. John |
| 2 | Giant's Coffin, Mammoth Cave: one huge flat-sided block | https://commons.wikimedia.org/wiki/File:Breakdown_(Giant%27s_Coffin,_Main_Cave,_Mammoth_Cave,_Kentucky,_USA)_7_(38165873492).jpg | CC BY 2.0, James St. John |
| 3 | Turner Avenue, Mammoth Cave: breakdown pile | https://commons.wikimedia.org/wiki/File:108A_Breakdown_in_Turner_Avenue_4_(8321126043).jpg | CC BY 2.0, James St. John |
| 4 | Standing Rocks, Mammoth Cave: slabs on edge, leaning | https://commons.wikimedia.org/wiki/File:Breakdown_(Standing_Rocks,_Main_Cave,_Mammoth_Cave,_Kentucky,_USA)_7_(26344553219).jpg | CC BY 2.0, James St. John |
| 5 | Detached block, Kentucky Avenue, Mammoth Cave | https://commons.wikimedia.org/wiki/File:Detached_limestone_block_(Kentucky_Avenue,_Mammoth_Cave,_Kentucky,_USA)_(38909490762).jpg | CC BY 2.0, James St. John |
| 6 | Surtshellir lava tube, Iceland: breakdown in the tube | https://commons.wikimedia.org/wiki/File:Inside-surtshellir.jpg | Public domain, Jabbi |
| 7 | Raufarhólshellir lava tube, Iceland: breakdown piles under a skylight | https://commons.wikimedia.org/wiki/File:Island_2017_372-0_(38300421166).jpg | CC BY-SA 2.0, Markus Trienke |
| 8 | Lava tube on Heimaey, Iceland: skylight with breakdown piles | https://commons.wikimedia.org/wiki/File:Volcanic_cave_(3337865831).jpg | CC BY-SA 2.0, Thomas Quine |
| 9 | Talus aprons at the foot of Yosemite Valley walls (sorting, slope angle) | https://www.usgs.gov/media/images/talus-flows-yosemite-valley | Public domain (USGS) |

Also more in the Commons categories "Breakdown (speleology)" and "Breakdown piles (speleology) in lava tubes". Already on file: `breakdown-sea-cave-rockfall.jpg` (RESEARCH-caves.md). Licences read from each file page on 2026-11-09. For images 6-8, the category says breakdown; I did not see the images.

### Sources (text)
- White and White 1969, Processes of cavern breakdown, NSS Bulletin 31(4): https://legacy.caves.org/pub/journal/PDF/V31/v31n4-White.htm
- USGS Bulletin 1673, Lava Beds caves (collapse trenches, talus, block sizes): https://npshistory.com/publications/geology/bul/1673/sec3l.htm
- Ruiz-Carulla et al. 2015, rockfall fragment size distribution: https://www.doi.org/10.1007/S10346-015-0600-7
- Lanfranconi et al. 2024, rockfall fragmentation: https://boa.unimib.it/retrieve/9bc5af54-6b9b-40da-81de-39f7f93d4e3f/Lanfranconi-2024-Engineering%20Geology-VoR.pdf
- USGS, rockfall fragmentation field evidence: https://pubs.usgs.gov/publication/70258360
- Talus sorting and repose angle: https://encyclopedia.com/science/encyclopedias-almanacs-transcripts-and-maps/talus-pile-or-talus-slope and https://boa.unimib.it/handle/10281/453717

## 3. How others do it (scatter techniques)

- **Poisson disk with a radius per size (Unreal PCG "Self Pruning", Large to Small).** Place points, give each the radius of its rock, then delete any point that overlaps a bigger one. Big rocks win. Fast and stable. It stops overlap but not floating. PCG's node is known to over-prune when the bounds are wrong, so the radius must match the mesh. https://dev.epicgames.com/documentation/en-us/unreal-engine/procedural-content-generation-framework-node-reference-in-unreal-engine
- **Same idea in Geometry Nodes.** Distribute Points on Faces (Poisson) takes one Distance Min per node, not per point. So run one pass per size: Big, then Medium, then Small. Each later pass deletes points that sit within (own radius + nearest earlier rock's radius) of an earlier rock. Sample Nearest gives the nearest earlier point; Sample Index reads its stored radius. One extra lookup per rock: cheap.
- **Stack by raycast (drop onto what is below).** Place big rocks on the floor. Turn them into a low-poly collision mesh (the Preview-level rock, or a convex hull). Drop the medium rocks by raycast onto floor + big rocks. Then drop small rocks onto all of that. Each rock lands on something real, so nothing floats. Costs a Realize Instances of the earlier layers and one raycast per rock.
- **Settle along slope.** After a rock lands, tip it to the hit normal (we already do this for foot rubble, 1855-1868), and nudge it a little downhill if the slope under it is steeper than about 35 degrees. Gives the fan shape.
- **Relax in a Repeat Zone.** A few rounds of "push overlapping points apart, then drop again". Fixes leftover overlaps. Each round is one proximity lookup and one raycast per rock. 3-5 rounds are usually enough.
- **Physics bake (Houdini RBD / Bullet, Blender Rigid Body).** Drop real rocks and let them settle. Most natural result. But: slow (seconds to minutes for 1-2k rocks), needs real objects not GN instances, must re-bake on every slider change, and results shift between runs and versions. Houdini artists use convex hulls and sleep settings just to make piles come to rest in reasonable time. https://sidefx.com/docs/houdini/dyno/rbd.html
- **World Creator.** A Talus filter builds slope deposits below a set angle at cliff feet. A Debris simulation drops physics particles, with bigger debris on lower levels (size grading by height). https://docs.world-creator.com/reference/terrain/biome/filters/sediment/talus and https://docs.world-creator.com/reference/terrain/simulation-layers/debris

## 4. Three options for us

All three: one scatter for all rubble on all three rocks (Mike's log, 2026-11-09). Spread wired in. Big rocks really big. Sizes drawn from a power law, with Rock Size moving the whole range.

### Option A. Fix the knobs, keep the cone (S)
- Wire Spread into the heaps: heap radius and apron reach grow with Spread. Keep Spread on the foot rubble but widen its effect.
- Power-law sizes. Drop the `k = 0.4` on Big. Use the Small kit to fill the heap's surface and apron.
- Poisson spots on the cone, not plain random. Per-size overlap cull (Large to Small).
- Lower and flatten the cone to about 30 degrees so the shell of rocks covers it.
- Pros: small change, almost no speed cost (one Sample Nearest per size).
- Cons: the cone is still imaginary. Floating gets rarer, not gone. Piles still look "placed".
- Build: about 1 session. Speed: under +5%.

### Option B. Layered drop: big, then medium, then small (M-L) - recommended
- **Where**: pile sources come from the cave, not random floor spots. Breakdown under wide roof (chamber, bends, junctions) as a heap. Talus as an apron along the wall foot. Lava: strewn stretches plus piles under skylights. Each source has a footprint that Spread scales (tight at 0, strewn out at 1).
- **Big layer**: few big blocks, Poisson-spaced, dropped onto the floor, flat side down. Biggest toward the pile's toe (fall sorting).
- **Medium layer**: more, smaller. Culled where it overlaps a big rock. Dropped by raycast onto floor + big rocks (Preview-level meshes as the collision mesh). Tipped to the surface it lands on.
- **Small layer**: many, small. Same cull and drop onto everything below. Fills gaps and feathers the pile's edge out across the floor.
- Optional 2-3 relax rounds in a Repeat Zone to clear leftover overlap.
- Pros: nothing floats by construction (every rock lands on a real hit). No deep overlap. Real size mix. The pile shape comes from the drop, not a fixed cone. Same everywhere (all three rocks, ramp scree too). Deterministic, so the same at every Detail Level if it runs on the Preview rocks.
- Cons: biggest rewrite of the rock code (replaces 1876-1938 and the foot rubble, 575-676). Needs a check that the realized Preview rocks stay light. Raycast hits on a rock's side can leave a rock leaning steeply; needs a slope limit.
- Build: about 2-3 sessions, with Mike review between. Speed: roughly +10-30% on cave rebuild time (two Realize Instances of low-poly proxies plus 2-3 raycasts per rock). Not measured yet; measure on the 100 m Jointed cave from the review.

### Option C. Physics settle as a bake button (L)
- Option B places the rocks. A "Settle rubble" button then runs a Blender rigid-body bake on real copies and stores the result.
- Pros: the most natural packing and contact. Rocks wedge and lean like real ones.
- Cons: seconds to minutes per bake. Live sliders stop matching until you re-bake. Results drift between runs and Blender versions. Needs real objects, which breaks the instance workflow and the Unreal export path we planned. Hard to keep the same at every Detail Level.
- Build: 3+ sessions on top of B. Speed: live rebuild unchanged, bake 10 s to minutes.

## 5. Recommendation

Option B. It is the only option that removes floating and deep overlap by construction, not by luck. It also makes the size mix and Spread real. It is fast enough to stay live and deterministic.

Do it in this order, each a checkpoint for Mike:
1. Wire Spread and fix the size mix (power law, Big really big, Small used). A quick win that shows Spread works. This is most of option A.
2. Layered drop with per-size cull, on the Jointed heaps first.
3. Move Limestone and Lava foot rubble and the ramp scree onto the same scatter.
4. Check all three rocks against the reference photos side by side. Measure rebuild time.

Leave option C on the parking list. Revisit only if B's piles still look "placed" after Mike's review.

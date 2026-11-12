# Realism review of the landscape models (2026-11-11)

Reviewer: Claude Fable 5.2 (`claude-fable-5-2`), as a subagent. Analysis only: no add-on code changed (D208).
Branch `lg-m7-spike`. Scope: the shapes of all 13 landscape types and their styles; caves, texturing and shaders are out.

Boards (all in `docs/realism/`):
- `c186_realism_mountains-glacial-canyon-mesa-badlands-cliffs.png` (per type, 1 of 2)
- `c186_realism_hills-dunes-seabed-riverbed-volcanic-volcano-craters.png` (per type, 2 of 2)
- `c186_realism_mountains-solutions.png` (Mountains: today against three fixes, with references)
- `c186_realism_masks.png` (erosion masks: today against two fixes)

## 1. Summary

1. **The Mountains are domes because nothing in the pipeline makes rock.** Four causes, each measured and switched off or on in a scratch copy:
   - Erosion cuts too weakly (incision 0.5). Valley heads never reach the crests, so the tops keep the round starting shape. Raising incision to 1.8 alone takes ground steeper than 60° from 1.2% to 15.7% on the erosion grid (the Sierra lidar has 11%).
   - Mountains has no hard-rock map (`lg_hard` is 0 everywhere), so every slope rests at one scree angle and nothing stands as a cliff.
   - Nothing exists between 16 m and 1 m. Shape layers stop at 4 erosion cells (15.6 m on a 2 km landscape) and the rock grain above it is about 1 m tall. Faces are mathematically smooth from 2 to 16 m: smoothness 0.99, where real rock is 0.78 to 0.90.
   - The engine's finishing blur and softening spread every edge over about 15 m.
2. **The smooth 2 to 16 m band is shared by every rocky type**: Mountains 0.99, Canyon 0.98, Glacial 0.97, Badlands 0.96, Cliffs 0.95, Mesa 0.94, Riverbed 0.93. That is what textures exposed in the spike.
3. **The erosion masks are saturated by the engine's uplift, not by erosion.** With uplift off, Mountains deposit = 1 falls from 87% of the surface to 1%. Deposit is 1 on more than half the surface for 6 of the 10 eroded types and styles. Two fixes are proven on the board.
4. **Preview and High erode differently.** Every smoothing and slumping step counts in grid cells, so Preview (256) is twice as blurred as High (512) in meters: crests half as sharp, 0.5% against 1.2% of ground over 60°.
5. **Three fixes shown working in a scratch copy** (board `c186_realism_mountains-solutions.png`): erosion settings (S1), a hard-rock map with bedrock structure (S2), and a bedrock breakup stage on the finished mesh (S4). S4 alone, on today's shape, moves Mountains at 1 m from 2.9% to 8.6% of ground over 60° (real 11.7%), smoothness 0.99 to 0.89 (real 0.89), crest sharpness 38 to 617 (real 1351). The full stack was rendered but not measured at 1 m. The look is a first draft, not a finished one.
6. **Lift:** about 5 to 7 tickets for the shared fixes, then a tuning pass per type. That closes most of the distance to Gaea and World Machine in clay at wide and mid range. Close-range rock (overhangs, true vertical faces) stays behind them until the SDF stage is used on cliffs.
7. **Materials:** fix the masks first (S3, small), then S1, S2 and S4 on Mountains. Re-run checkpoint 1 on that Mountains before starting checkpoint 2, and change checkpoint 2 to use the new masks (talus, bedrock).

## 2. How this was measured

- Every type and style built at 2 km, High (2049 × 2049 points, about 1 m), water off. The pre-erosion shape, hard map and erosion settings were dumped at the 256 and 512 erosion grids; the finished mesh heights and masks at 1 m.
- Real data: the same 2 km windows of 1 m lidar that T6b uses (`tests/lidar_check.py` window picker; seabed at 3.4 m; Strato and Caldera at 4 m).
- Numbers: slope percentiles; share of ground steeper than 45° and 60°; share flatter than 5°; **smoothness** = how roughness grows from 2 m to 16 m (1.0 is perfectly smooth; the lidar report calls it `h_small`); **crest sharpness** = the 1st percentile of curvature times the relief.
- Causes were proven by switching them off in numpy on the dumped shapes with the add-on's own `erosion.py`, never in the add-on (CODING.md).
- Clay: Cycles, the neutral sky `kloofendal_48d_partly_cloudy_puresky_4k.hdr` as fill, a sun at 22° standing 60° to the side of the camera, grey with ambient-occlusion and pointiness cavity shading. One render per process through `tests/blender.sh`.
- Scratch scripts are outside the repo (session scratchpad). The solution code is in the appendix so it is not lost.
- Limits: one seed and one size (2 km) per type. Real windows are taller than ours for the same width (Sierra 727 m, ours 312 m), so compare slope shares and smoothness, not heights. Styles without a lidar tile (Linear and Star dunes, Hero Butte, Mounds, Shield, Collapsed) are judged by eye from hillshades only; they have no clay render here.

## 3. Per-type table

"Shared" means one of the shared causes in section 6. Size: S under a day, M a few days, L a week or more.

| Type | What falls apart (ours / real) | Cause | Shared or own | Fix | Size | Risk |
|---|---|---|---|---|---|---|
| **Mountains** | Domes, even 30 to 45° flanks. Over 60°: 2.9% / 11.7%. 99th pct slope 65° / 80°. Crest sharpness 38 / 1351. Smoothness 0.99 / 0.89. No talus cones | Weak incision, no hard map, empty 2 to 16 m band, blur | Shared (all four) | S1, S2, S4, then S6 for talus | M | Medium: over-dissection if incision goes past about 1.5 |
| **Glacial Valley** | Walls lean back: 90th pct 43° / 63°, over 60° 2.2% / 12%. Tops are smooth swells. Cliff band is an even comb. No hanging valleys | Same four; hard band is one narrow strip (10% of the grid); soften 0.6 | Shared + own | S1 (soften 0.6 → 0.2), S4; own: widen `hard_glacial` down the wall, tributaries that stop high on the wall | M | Medium: U profile must survive more incision |
| **Canyon** | Reads as fluted hills. Too much mid slope: over 45° 11.7% / 5.6%; median 24° / 16°. Rims round (sharpness 47 / 524). Smoothness 0.98 / 0.82 | Talus 32° relaxes every wall to one angle; benches not flat; blur rounds the rim | Shared + own | S4 with flat-bedded strata (dip 0); own: benches as hard caps (flat tread, sheer riser), plateau kept flat | M | Medium |
| **Mesa** (Field, Hero) | Best rocky type. Cliff faces are smooth flutes; floor gullies even. Smoothness 0.94 / 0.78. Over 60° 5.0% / 1.9% | Empty 2 to 16 m band; gully spacing from one channel threshold | Shared | S4 (vertical joints on the cliff band); vary `channel` by a low-frequency field | S | Low |
| **Badlands** (Wall, Mounds) | Drainage good. Twice the flat ground: under 5° 35% / 17%. Fin crests rounded (70 / 178). Smoothness 0.96 / 0.78. Mounds: deposit mask 90% saturated | Flat floor share from the recipe; blur on crests; uplift 0.42 | Shared + own | S5 (less blur at High); own: shrink the flat pediment share; S3 | S | Low |
| **Coastal Cliffs** | Land behind the bluff is a plate: slope spread 3° / 11°. Bluff low and its face rounded scallops; no rills, ledges or beach | Plateau fBM too weak; face has no bedrock structure | Shared + own | S4 on the face; own: stronger headland relief, face rills (ridged noise along the fall line) | M | Low |
| **Rolling Hills** | One swell with dimples at 2 km; real Palouse packs dozens of hills. 90th pct 17° / 13° | `feature_scale` 2.2 is right for 200 m, not for 2 km; channel creases are short scratches | Own | Scale hill count with size (or raise `feature_scale` when Proportional Feature Scaling is off); swales that join (lower `channel`, more soften rounds) | S | Low |
| **Sand Dunes** (Crescent, Linear, Star) | Crescent matches lidar. Slip faces soft: 99th pct 23° / 31°. Star: 19% over 45°, steeper than sand can stand | No slope rule: sand rests at 32 to 34° | Own | A thermal pass at 33° on the dune field (S6 code, no erosion needed) | S | Low |
| **Seabed** | Blobby mounds; nothing over 17° (real 26°); reef patches have no ledges or broken edges | fBM plus soft Voronoi; no rock structure | Shared + own | S4 on the reef mask only | S | Low |
| **Riverbed** | A few ditches on a plate. Banks too steep (99th pct 24° / 11°). Too smooth at 2 m (0.93 / 0.67): no bars | Channels are carved lines, not braids; no bar texture | Own | Braids from 3 offset channel fields that cross; bars as low lens shapes between; `bank_deg` 25 → 12 | M | Medium |
| **Volcanic** | Roughness matches. Cones are one size and profile. Lobe edges too steep (over 45° 2.7% / 0.3%); flow tops too lumpy (flat 11% / 25%) | Cone recipe has one radius; lobe mask steps too sharply | Own | Cone size from a hash (0.4× to 1.6×), breached cones; ease lobe edges to 20 to 25° | S | Low |
| **Volcano** (Strato, Shield, Cinder, Caldera, Collapsed) | Lathe-turned cone, faint even gullies; no ravines that deepen downhill, no flow ridges. Caldera walls 29° / 63° at the 99th pct. Cinder crater rim 51° / 33° | Radial profile plus polar noise; no erosion on this type | Own | Run the engine on Strato and Collapsed with radial drainage (incision about 1.0, `channel` 0.0002); hard rim on Caldera with S4; cap Cinder at 33° | M | Medium: cone symmetry |
| **Cratered Surface** | Tuned to LROC and reads right. Small pits are all one crisp bowl | Smallest layer has no age spread | Own | Give the pit layer the same per-crater age as the big ones | S | Low |

## 4. Mountains in depth

### Why they come out as domes

Measured on the 512 erosion grid (4 m cells, 2 km), middle of the landscape:

| Stage | Over 45° | Over 60° | 99th pct slope | Crest sharpness |
|---|---|---|---|---|
| Shape before erosion | 14.1% | 1.6% | 62° | 30 |
| After erosion (today) | 12.4% | 1.2% | 61° | 20 |
| Finished mesh, 1 m | 22.7% | 2.9% | 65° | 38 |
| Sierra lidar, 1 m | 23.4% | 11.7% | 80° | 1351 |

The shape is already a dome before erosion, and erosion leaves the slope spread almost untouched. In order of effect:

1. **The starting shape is round, by design.** `nodes.py`, recipe 1: spines are `soft_ridge(fract(phase), P1)` with `ridge_width` 0.6, which gives a crest rounding of `0.02 + 0.6 × 0.45 = 0.29` of the spine spacing. Spurs are two fBM layers with 2 and 3 octaves. Pass 1 found the ridges "knife-thin" and widened them; nothing sharp was put back.
2. **Erosion is too weak to reshape it.** `types.json` Mountains: `incision 0.5` (D58 lowered it), default `channel 0.0005`. Stream power only cuts where more than 0.05% of the landscape drains through a cell; above that line the slopes are shaped only by slumping to 38° and by softening. Valley heads stop far below the crest, so summits keep the starting shape with 38° sides. Proof: the same shape with incision 1.5 has 7.2% over 60° (was 1.2%); with 1.8 and `channel` 0.0003, 15.7%.
3. **No hard rock.** `hard_by_recipe` in `nodes.py` has entries for Cliffs, Canyon, Mesa, Badlands and Glacial, not Mountains. With `hard = 0`: the scree angle is 38° everywhere, bedrock is capped at `cliff_deg` 60°, softening runs at full strength on every cell, and all rock cuts at one rate. Real alpine faces stand at 60 to 85° because jointed bedrock is far stronger than its own debris.
4. **An empty band from 2 to 16 m.** `__init__.py` sets `Detail Floor = 4 × size / 512`, 15.6 m at 2 km, so no shape layer is finer than that. The rock grain starts there (`l_max = min(30, size / 16, Detail Floor)`) with an amplitude of `Rock × bare × (0.4 + 1.2 × Roughness) × l_max × 0.06`, about 1 m on a 312 m relief. Roughness doubles each time the distance doubles (smoothness 0.99): a pillow with a fine skin.
5. **Blur.** `erode()` runs 13 rounds of `finish_blur`, 4 more after the dams are cut, and 96 softening rounds across the passes: about 15 m of spread at High, 30 m at Preview. Switching `finish_blur` off raises the 99th pct slope from 61° to 75° and crest sharpness from 20 to 105, but leaves one-cell stair steps (why it was added, Pass 2). It cannot simply be removed; it needs to stop touching hard rock and to be sized in meters (S5).

Switching each erosion step off, one at a time (512 grid):

| Variant | Over 60° | 99th pct slope | Crest sharpness |
|---|---|---|---|
| Today | 1.2% | 61° | 20 |
| No finishing blur | 3.2% | 75° | 105 |
| No softening | 1.1% | 60° | 20 |
| No slumping at all | 3.6% | 66° | 34 |
| Bedrock cap 85° | 1.3% | 61° | 20 |
| No uplift | 2.1% | 64° | 25 |
| Incision 1.5, scree 35° | 7.2% | 70° | 32 |
| Incision 1.8, channel 0.0003, blur 6, bedrock 75° (S1) | 15.7% | 78° | 72 |
| S1 + hard map + bedrock structure (S2) | 16.1% | 78° | 90 |
| Incision 3, channel 0.0001 | 27.5% | 82° | 157 (over-dissected) |

### What makes real alpine faces craggy

- **Jointed bedrock.** Granite and gneiss break along joint sets; faces are planes between joints, steps where a block has fallen out. Rock mass strength, not the scree angle, sets the wall angle (60 to 85°).
- **Frost shattering** works fastest in the top few hundred meters and on shaded faces, which is why crests and headwalls are serrated while lower slopes are smooth.
- **Cirques and arêtes.** Glaciers and gullies eat backward into the crest from both sides; where two headwalls meet the ridge becomes a knife edge. The Sierra hillshade on the board shows exactly this: a sharp arête with a cliff on one side and smooth talus on the other.
- **Cliff bands and ledges** where hard and soft layers alternate.
- **Talus.** Everything that falls collects at 32 to 38° as cones under each gully and aprons under each wall; talus is smooth at 10 m and rough at 1 m.
- **Erosion that respects hardness:** gullies follow weak joints and soft beds, so couloirs are straight and ribs stand between them.

### How the tools get it (from their documentation, as I recall it; node names are worth re-checking against the current manuals, see `RESEARCH-features.md` for what was opened on 2026-11-08)

- **Gaea.** Primitives such as Mountain and Ridge already carry sharp ridged structure. `Rugged` and `Shatter` break slopes into rocky facets; `Stratify` and `Terraces` cut tilted, uneven rock layers; `Erosion 2` then runs with separate controls for downcutting, sediment and feature scale, and outputs wear, deposit and flow masks. The usual chain is primitive → Rugged/Stratify → Erosion → a second light detail pass. The point for us: rock structure goes in **before** erosion and a detail pass comes **after** it, both at full resolution.
- **World Machine.** `Erosion` has a rock-hardness setting and takes a hardness mask, so layers stand as bands. `Thermal Weathering` breaks cliffs back at a talus angle and outputs a talus mask; its fracture size sets the block scale. `Terrace` and layered hardness give strata. The point: thermal erosion is a first-class step with its own deposit output.
- **World Creator.** Filters applied in a stack on the GPU at full resolution: erosion and sediment filters, terrace and rocky/ridged filters, each masked by slope, height and noise. The point: the rock filters are local per-cell operations, which is why they run in real time, and why they port to WebGPU.

All three share one idea we lack: **a rock stage**. We go from a smooth shape through a smoothing erosion to a 1 m grain.

## 5. Erosion masks

### Finding

Share of the surface at each end of the mask, finished High mesh:

| Type | Deposit = 1 | Deposit = 0 | Wear = 1 | Wear = 0 | Uplift (share of relief) |
|---|---|---|---|---|---|
| Mountains | 89% | 3% | 1% | 97% | 0.16 |
| Badlands, Mounds | 90% | 3% | 0.5% | 98% | 0.42 |
| Mesa Field | 87% | 4% | 2% | 96% | 0.12 |
| Glacial | 86% | 0.4% | 0% | 99.7% | 0.16 |
| Mesa Hero | 80% | 9% | 3% | 95% | 0.12 |
| Canyon | 58% | 10% | 2% | 92% | 0.12 |
| Badlands, Wall | 44% | 33% | 23% | 70% | 0.42 |
| Cliffs | 1% | 51% | 5% | 88% | 0.14 |
| Hills | 0.1% | 1% | 0% | 99% | 0.04 |
| Riverbed | 0.1% | 22% | 4% | 84% | 0.10 |

### Cause

`erosion.py`, `erosion_masks(before, after)`: `change = 0.5 + 0.5 × (after − before) / (5% of the relief)`. `after − before` is not what erosion did. It also holds:

1. **The even uplift.** `erode()` adds `uplift × relief / passes` to every cell on every pass (0.16 of the relief on Mountains) against fixed edges. The edges are in the padding that gets cropped, so every cell the artist sees has risen by about 10% of the relief: twice the 5% the mask treats as full deposit. The median change on Mountains is +9.5% of the relief.
2. The stretch back to the full relief, which lifts everything above the lowest point.
3. Pit filling and the Mesa talus apron, added to the target before erosion starts.

**Proof:** Mountains with `uplift = 0`: deposit = 1 on 0.9% (was 86.6%), wear = 1 on 11.5%, and 73% of the surface in the middle of the range. Nothing else changed.

Wear is nearly empty for the mirror reason: a cell has to lose 5% of the relief net of a 10% rise.

### Fix (both on board `c186_realism_masks.png`)

- **Fix A, take the lift out (S, low risk).** In `erosion_masks`: compare with the pit-filled shape, subtract the change blurred over 5% of the width (the broad lift), and scale by the 97th percentile instead of a fixed 5%. About 6 lines. Result on Mountains: deposit = 1 on 0.6%, 45% of the surface between 0.1 and 0.9; wear between 0.1 and 0.9 on 22%. Deposit lands on valley floors and fans (mean slope 30° on Mountains, 17° on Glacial).
- **Fix B, count the work (M, low risk).** Inside the pass loop, add up what each pass removes and adds per cell (`z_in − z` after the pass, split by sign), and the same in the final slump loop. Wear = total cut, deposit = total fill, each scaled by its own 97th percentile. 8 lines in `erode()` plus the scaling. This is how Gaea and World Machine build their wear and deposit outputs. Deposits then sit where the engine actually put debris: at the scree angle under walls (mean slope 35° on Mountains) and along channel floors. The Mesa apron must be added to the fill by hand, since `apron()` builds it before the loop.
- **Recommended:** fix A now, because it unblocks the material rules in one small ticket, and fix B together with the talus pass (S6), which gives a third mask, `lg_talus`, the one scree and soil really want.
- **three.js:** both are per-cell arithmetic on buffers the erosion already holds; fix A needs one separable blur. No new cost.
- Tests: T-number for "no mask has more than 60% of its cells at 0 or at 1 on any eroded type" at Preview and High.

## 6. Shared causes, most lift first

| # | Shared cause | Evidence | Types hit | Fix |
|---|---|---|---|---|
| 1 | **No rock stage: nothing between the 16 m shape floor and the 1 m grain** | Smoothness 0.93 to 0.99 on every rocky type; real 0.67 to 0.89. Crest sharpness 3× to 35× too low | Mountains, Glacial, Canyon, Mesa, Badlands, Cliffs, Seabed, Volcano | S4 |
| 2 | **Erosion too gentle and too blurred to carve the form** | Incision 0.5 on Mountains, Glacial, Canyon, Hills, Riverbed; slope spread unchanged by erosion; S1 alone gives ridgelines | Mountains, Glacial, Canyon | S1 |
| 3 | **Hardness is missing or thin** | `lg_hard` 0 on Mountains, Hills, Riverbed; 10% of cells on Glacial and Mesa | Mountains, Glacial, Volcano | S2 |
| 4 | **Masks measure uplift, not erosion** | Section 5 | Every eroded type | S3 |
| 5 | **Erosion counts in cells, not meters** | Preview 0.5% over 60°, High 1.2%; crest sharpness 10 against 20; blur 30 m against 15 m | Every eroded type | S5 |
| 6 | **No talus as a landform** | Slumping moves debris but the result is blurred and never marked; no cones, no aprons outside Mesa | Mountains, Glacial, Canyon, Cliffs, Volcano | S6 |
| 7 | **Erosion grid capped at 512** | 4 m cells at 2 km, 20 m at 10 km: gullies under about 5 cells cannot exist | Large landscapes of every eroded type | S7 |
| 8 | **Feature count does not follow size** | Hills, Cliffs and Riverbed look empty at 2 km | Hills, Cliffs, Riverbed, Seabed | Per type (section 3) |

Not shared, and fine: Dunes, Craters and Volcanic match their data on roughness; their gaps are their own (section 3).

## 7. Solutions, ordered by lift

Each is written to become a ticket. "Proven" means shown in a scratch copy on a board.

### S1. Retune erosion so it carves (proven; S; medium risk)

- **Technique:** stream-power incision strong enough for valley heads to reach the crests, with a lower channel threshold and less finishing blur. Same engine (Braun & Willett 2013, implicit stream power).
- **Where:** `types.json` only. Mountains: `incision` 0.5 → 1.2 to 1.8, `channel` 0.0005 → 0.0003, `finish_blur` 16 → 8, `cliff_deg` 60 → 75, `talus_deg` 38 → 35, `soften` 0.2 → 0.1. Glacial: `incision` 0.5 → 1.0, `soften` 0.6 → 0.2. Canyon: `finish_blur` → 8. Tune each against the lidar numbers; 1.8 overshoots Mountains a little (15.7% over 60° on the grid against 11%), and incision 3 with `channel` 0.0001 over-dissects into a comb (27%).
- **Result:** board, "S1": ridgelines, spurs and V valleys in place of domes.
- **three.js:** no change; these are the same settings the port reads.
- **Risk:** T6 and T6b bands will move (median slope rises to about 38°); Mike signed the current look in Pass 2, so this needs his eye. Changes saved landscapes' erosion.

### S4. A bedrock breakup stage on the finished mesh (proven as a draft; M to L; medium risk)

- **Technique:** where the ground is steeper than scree can lie, replace the smooth surface with jointed rock: (a) joint-bounded blocks at three sizes (60, 22, 9 m at 2 km), each block face set a little proud or back and tilted its own way, from a domain-warped cellular noise; (b) strata benches and risers every 10 to 20 m of height on beds that dip a few degrees. Masked by slope (34 to 46°) and by rock patches. Gaea: Rugged/Shatter and Stratify after Erosion. World Creator: rocky and terrace filters masked by slope. World Machine: fracture size in Thermal Weathering.
- **Where:** `nodes.py`, the R2 rock-grain block (after the erosion map is blended in, before the masks). Add a `rock` field (`smooth(slope, 34°, 46°) × patch noise`, or `lg_hard` once S2 exists) and push points by `rock × (blocks + 0.45 × strata)`. Blocks: Voronoi texture, `F1` cell colour for the offset and tilt, position warped by a noise of 3 block sizes. Strata: the existing Terraces formula (`floor(lv) + fract(lv)^4`) on world height with a dip term. Sizes in meters, clamped to at least 2.5 mesh points so Preview shows the two bigger sizes only. Push along the normal, as the grain does, so walls break sideways. Per-type inputs: `Breakup` amount, bed thickness, bed dip (0 for Canyon and Mesa, 3 to 6° for Mountains), block size. Bump `GROUP_VERSION`, rebuild the library.
- **Result:** Mountains at 1 m, today's shape plus this stage only: over 60° 2.9% → 8.6% (real 11.7%), 90th pct slope 52° → 58° (63°), smoothness 0.99 → 0.89 (0.89), crest sharpness 38 → 617 (1351). Board, "today + S4" and "S1 + S2 + S4".
- **Honest limits of the draft:** blocks read as cracked plates from above and risers stretch into combs on near-vertical faces, because a heightfield has one height per point. The node version should tilt blocks more, push along the normal, and fade the smallest size with distance. It needs a reference board per rock type (granite blocks, bedded limestone, sandstone) before Mike sees it. D157 and D163 moved fine cave ledges to materials; this is different in scale (5 to 60 m forms on a 2 km landscape are secondary volume), but the smallest block size should stay above about 3 mesh points and leave finer cracks to the material.
- **three.js:** ideal GPU work: per-vertex noise, no neighbours. Cellular noise and the terrace function are a few lines of TSL in the vertex stage or a compute pass; it can run as displacement at any LOD.
- **Risk:** face counts unchanged; stretching on steep faces; T6b spike check may flag the strata period (vary bed thickness).

### S3. Masks that vary (proven; S for fix A, M for fix B; low risk)

Section 5. `erosion.py`, `erosion_masks()` and the pass loop. No node change: the image channels stay the same.

### S2. A hard-rock map and bedrock structure for Mountains (proven; M; medium risk)

- **Technique:** tell the erosion where bedrock is, and give that bedrock layers and joints before eroding, so cutting follows weak rock: soft beds become ledges, soft joints become couloirs, hard ribs stand between. World Machine: hardness mask into Erosion. Gaea: Stratify before Erosion.
- **Where:** `nodes.py`: a `hard_mountains` field added to `hard_by_recipe` (key 1). `rock = max(smooth(slope of the blurred shape, 24°, 38°), 0.6 × smooth(height, 0.55, 0.85)) × smooth(height, 0.25, 0.55) × patch noise (1/5 of the width)`; `hard = rock × bed × joint`, where `bed` is 0.25 for about one bed in three (14 dipping beds over the relief) and `joint` falls to 0.35 in the valleys of a ridged noise at about 1/23 of the width. Then add structure to the shape itself where `rock` is high: ridged noise at 1/12, 1/24 and 1/48 of the width, amplitude 0.11 of the relief, and strata steps blended at 0.55. The Terraces block already has the step formula.
- **Result:** with S1, crest sharpness on the erosion grid 72 → 90 and visible ribs along the crests (board, hillshade "S1 + S2"). On its own, without S1, it does almost nothing (over 60° 1.2% → 1.8%): the engine's blur and weak incision erase it. So it ships after S1 and S5.
- **Tried and dropped:** Voronoi cell borders as joints drew a polygon net across every face.
- **three.js:** the hard map is per-cell noise; the erosion port already takes `hard`.
- **Risk:** medium; tuning per seed. Glacial and Volcano can reuse the field.

### S5. Erosion in meters, the same at Preview and High (not prototyped; M; medium risk)

- **Technique:** size every smoothing and slumping step by distance, not by rounds of cells: `finish_blur`, `soften_rounds`, `floor_width`, `floor_carve`, `final_slump`, and the 3-cell cut-off in `keep_detail`. Rounds scale with `(grid / 512)²` for diffusion and with `grid / 512` for the cell-per-round steps. Also weight the finishing blur by `1 − hard` everywhere (it already is in `smooth_rounds`) and skip it on cells steeper than `talus_deg`.
- **Where:** `erosion.py`, `erode()`; settings stay as they are, read as "at 512".
- **Why:** CODING.md says each Detail Level keeps the quality approved at it (D196). Today Preview and High are different landscapes: 0.5% against 1.2% over 60°.
- **three.js:** required anyway, since the browser will run other grid sizes.
- **Risk:** every eroded type shifts slightly at Preview; the suite's erosion tests need re-baselining.

### S6. Talus as a landform and a mask (not prototyped; M; low risk)

- **Technique:** thermal erosion with a deposit counter (Musgrave, Kolb and Mace 1989; World Machine Thermal Weathering). After the passes: cells of hard rock steeper than their angle shed material; it moves downhill cell to cell and stops where the slope drops under 33 to 36°. Keep the shed and received totals. Do not blur the talus afterwards.
- **Where:** `erosion.py`: `slump()` already does the movement; add the counters and return a third mask. Store it in the erosion image's alpha channel, add `lg_talus` beside the other masks in `nodes.py`.
- **Gives:** cones under gullies and aprons under walls on every rocky type (the Mesa apron code can go), and the mask scree materials need. Also the 33° rule Dunes and Cinder cones need.
- **three.js:** thermal erosion is the easiest erosion on a GPU: a fixed stencil, a ping-pong buffer, no ordering.
- **Risk:** low.

### S7. A finer erosion grid at High and Ultra (not prototyped; M; medium risk on time)

- **Technique:** 1024 at High, 2048 at Ultra, or erode at 512 and add a second, short erosion at 1024 that starts from the upsampled result (multigrid, as in Gaea's and World Machine's build resolutions).
- **Where:** `EROSION_GRID` in `__init__.py`; `fill()` and `breach()` in `erosion.py` are Python heap loops and will dominate (512 takes 6.7 s today; 1024 would take about 30 s). They need a vectorised or compiled priority flood first.
- **three.js:** this is the open risk `RESEARCH-engines.md` already names: pit filling and flow accumulation are sequential.
- **Do after** S1 to S6; much of the gain comes from S4 without it.

### S8. Per-type fixes

Section 3, in this order: Glacial walls and Canyon benches (with S4), Hills count, Dunes and Cinder repose angle (with S6), Volcano erosion, Riverbed braids, Volcanic cone variety, Cliffs headland, Seabed reef, Crater pits.

## 8. three.js and WebGPU, geometry only

What others do, and what each of our fixes needs there. Existing notes: `RESEARCH-engines.md` (opened 2026-11-06). Sources below are from memory and were not re-opened in this session; check the links before quoting them.

- **Noise on the GPU.** Standard: fBM, ridged and cellular noise in the vertex or compute stage; three.js has the `webgpu_tsl_procedural_terrain` example and MaterialX noise nodes in TSL (`mx_noise_float`, `mx_worley_noise_float`, `mx_fractal_noise_float`). Our shapes, S2's hard map and S4's breakup are all this kind of work. Analytic derivatives (Inigo Quilez, "Value noise derivatives") give slope without neighbours, which S4's slope mask can use.
- **Hydraulic erosion on the GPU.** Three families: (1) the pipe model, a grid of water and sediment (Mei, Decaudin and Hu 2007, "Fast Hydraulic Erosion Simulation and Visualization on GPU"; the soilwebgpu and Eulerian demos in `RESEARCH-engines.md`); (2) droplets, which need atomics or fixed-point heights in WGSL; (3) stream power, ours. Stream power on a GPU is published: Schott et al. 2023, "Large-scale terrain authoring through interactive erosion simulation" (ACM TOG) solves it with an explicit, parallel scheme and approximated drainage area that converges over frames; Cordonnier et al. 2016 is the uplift-plus-stream-power origin; Tzathas et al. 2024, "Physically-based analytical erosion for fast terrain generation" (Eurographics) gets closed-form results for speed. For parity with `erosion.py`, the plan in `RESEARCH-engines.md` stands: the exact engine in a Web Worker (numpy → TypeScript or WASM), a GPU approximation for the live preview.
- **Thermal erosion on the GPU.** A fixed neighbourhood and ping-pong buffers (Jákó and Tóth 2011, "Fast hydraulic and thermal erosion on the GPU"). S6 ports directly and can run every frame.
- **Detail by displacement.** Browser terrains keep a coarse simulated heightfield and add rock detail as vertex displacement or as tessellated patches near the camera, with normals from the displaced height. S4 is designed for this: it reads only position, slope and a seed.
- **LOD.** Geometry clipmaps (Losasso and Hoppe 2004; Asirvatham and Hoppe 2005, GPU Gems 2) or CDLOD quadtrees (Strugar 2010). Our landscapes are bounded tiles of 1k to 4k points, so one mesh with distance-based displacement LOD is enough at first; clipmaps matter only for the "infinite" case.
- **Vertical faces.** A heightfield cannot hold overhangs. Tools that show true cliffs in real time use a second representation near the camera: triplanar-projected displacement, or an SDF patch meshed on the GPU. We already have the SDF stage for caves (D9); cliffs are the same problem later.

What ports cleanly, per fix:

| Fix | Blender | three.js / WebGPU |
|---|---|---|
| S1 settings | `types.json` | Same file |
| S2 hard map | Node fields | TSL noise in a compute pass; output a texture |
| S3 masks | numpy | Same arithmetic in the worker or a compute pass |
| S4 breakup | Node fields on the mesh | Vertex-stage displacement; best fit of all |
| S5 meters | numpy | Same code |
| S6 talus | numpy `slump()` | Compute shader, ping-pong; real time |
| S7 finer grid | Needs a fast priority flood | The known risk: sequential steps; worker or a GPU approximation |

Rule for the Blender work: keep new shape logic either per-point (noise, masks, displacement) or fixed-stencil (thermal). Both port. Avoid adding more ordered, cell-after-cell steps like the priority flood.

## 9. Size of the lift against Gaea, World Machine and World Creator

Where we are, in clay: wide shots of Mesa, Badlands, Dunes and Craters hold up. Mountains, Glacial and Canyon do not; they read as smoothed noise. Mid and close shots of any rock fail.

| Step | Work | Gets us to |
|---|---|---|
| S3 fix A, S1 | 2 small tickets | Masks usable; Mountains read as an eroded range at wide range |
| S4, S2 | 2 medium tickets plus a reference board per rock type | Rock reads as rock at wide and mid range on eight types; numbers within T6b-style bands for steep ground and smoothness |
| S5, S6 | 2 medium tickets | Preview matches High; talus cones and a talus mask |
| Per-type pass (S8) | About 10 small tickets | No type is an obvious outlier |
| S7 | 1 medium to large ticket | Fine gullies on large landscapes |

That is roughly 6 shared tickets and a tuning pass. After it I would expect clay wide and mid shots to stand beside Gaea and World Machine defaults for most types. Still behind them after that: their erosion carries real sediment transport at 4k to 8k (ours is 512 to 1k), their rock detail is art-directed over many versions, and none of us on a heightfield shows true overhangs. Honest uncertainty: S4 is proven in numbers and as a draft look, not as a finished one.

## 10. Recommended next steps, and when to return to materials

1. **S3 fix A** (masks). Small, no look change, unblocks material rules.
2. **S1 on Mountains** behind Mike's eye: a board at incision 1.2, 1.5 and 1.8 against the Sierra lidar and two photos.
3. **S4 on Mountains**, built in nodes, with a granite reference board; then switch it on for Glacial, Canyon, Mesa, Cliffs, Badlands with per-type bed and block settings.
4. **S2**, then **S5** and **S6** with mask fix B and `lg_talus`.
5. Per-type pass in the order of section 7, S8.

**Materials:** not checkpoint 2 as it stands. Come back after steps 1 to 3 on Mountains. Re-shoot checkpoint 1's three views on the new Mountains first (cheap: the material is unchanged), because the rules were tuned against saturated masks (`render_m7.py` even picks its close-up spot with `lg_deposit > 0.9`, which today is true almost everywhere). Then change checkpoint 2 to: rock on the breakup's `rock` field or `lg_hard`, scree on `lg_talus` (after S6), soil and turf on the fixed deposit and flow masks. The other types' materials wait for S4 on those types.

## Appendix: the scratch solution code

Plain numpy, the units `erosion.py` uses. This ran only in memory beside the add-on (the render script replaced `erosion.erode` with a wrapper for one render). It is a prototype for the tickets above, not finished code.

```python
"""Scratch solution prototypes (realism review 2026-11). Plain numpy, same units as erosion.py (heights / size).
Never imported by the add-on: the review's render script wraps erosion.erode in memory.

  hard_mountains(h)   S1: a hard-rock map for Mountains (the type has none today): bedrock on steep, high ground,
                      broken by soft beds (strata) and soft joints, so erosion leaves cliff bands, ribs and couloirs.
  crag_shape(h, rock) S2: adds the missing 20-200 m structure to the bedrock before erosion: tilted strata steps
                      (Gaea Stratify) and ridged, jointed blocks (Gaea Rugged / World Machine hardness layers).
  masks_from_work()   S3: wear and deposit from what the engine actually moved, scaled to span 0..1.
"""
import numpy as np


def _smooth(x, a, b):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def value_noise(shape, cells, rng):
    """Smooth random field, about `cells` grid cells per feature, 0..1."""
    n, m = shape
    gy, gx = int(n / cells) + 3, int(m / cells) + 3
    g = rng.random((gy, gx))
    y, x = np.arange(n) / cells, np.arange(m) / cells
    yi, xi = y.astype(int), x.astype(int)
    fy, fx = y - yi, x - xi
    fy, fx = fy * fy * (3 - 2 * fy), fx * fx * (3 - 2 * fx)
    a = g[np.ix_(yi, xi)] * (1 - fx) + g[np.ix_(yi, xi + 1)] * fx
    b = g[np.ix_(yi + 1, xi)] * (1 - fx) + g[np.ix_(yi + 1, xi + 1)] * fx
    return a * (1 - fy)[:, None] + b * fy[:, None]


def ridged(shape, cells, rng, octaves=3, gain=0.5):
    """Ridged multifractal: sharp crests, each octave weighted by the one above (Musgrave)."""
    out, amp, w, tot = np.zeros(shape), 1.0, np.ones(shape), 0.0
    for o in range(octaves):
        r = 1.0 - np.abs(2.0 * value_noise(shape, cells / 2 ** o, rng) - 1.0)
        r = r * r * w
        out += r * amp
        tot += amp
        w = np.clip(r * 2.0, 0.0, 1.0)
        amp *= gain
    return out / tot


def worley(shape, cells, rng):
    """F1 and F2 - F1 (0 on cell borders = joints) on a jittered grid, in units of the cell size."""
    n, m = shape
    gy, gx = int(n / cells) + 4, int(m / cells) + 4
    py, px = rng.random((gy, gx)), rng.random((gy, gx))
    y, x = np.mgrid[0:n, 0:m] / cells + 1.0
    yi, xi = y.astype(int), x.astype(int)
    f1, f2 = np.full(shape, 9.0), np.full(shape, 9.0)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            cy, cx = yi + dy, xi + dx
            d = np.hypot(cy + py[cy, cx] - y, cx + px[cy, cx] - x)
            f2 = np.where(d < f1, f1, np.minimum(f2, d))
            f1 = np.minimum(f1, d)
    return f1, f2 - f1


def slope_tan(z):
    dx = 1.0 / (max(z.shape) - 1)
    gy, gx = np.gradient(z, dx)
    return np.hypot(gx, gy)


def _dip(shape, rng):
    n = max(shape)
    yy, xx = np.mgrid[0:shape[0], 0:shape[1]] / float(n)
    return 2.5 * xx + 1.2 * yy + 1.2 * (value_noise(shape, n / 6.0, rng) - 0.5)


def hard_mountains(h, seed=0, beds=14, joint_cells=22.0):
    """(hard 0..1, rock 0..1). Bedrock where the shape is steep and high; soft interbeds (about one bed in three) and
    soft joints between blocks stay erodible, so erosion cuts ledges and couloirs and the debris piles below as talus."""
    rng = np.random.default_rng(seed + 31)
    n = max(h.shape)
    rel = max(float(np.ptp(h)), 1e-9)
    u = (h - h.min()) / rel
    broad = h.copy()
    for _ in range(3):  # slope of the big shape, not of its texture
        p = np.pad(broad, 1, mode="edge")
        broad = (p[:-2, 1:-1] + p[2:, 1:-1] + p[1:-1, :-2] + p[1:-1, 2:] + 4 * broad) / 8.0
    steep = _smooth(np.degrees(np.arctan(slope_tan(broad))), 24.0, 38.0)
    lith = 0.55 + 0.45 * _smooth(value_noise(h.shape, n / 5.0, rng), 0.3, 0.7)  # rock type patches ~1/5 of the width
    rock = np.maximum(steep, 0.6 * _smooth(u, 0.55, 0.85)) * _smooth(u, 0.25, 0.55) * lith
    lv = u * beds + _dip(h.shape, np.random.default_rng(seed + 5))
    band = rng.random(int(lv.max()) + 3)[np.floor(lv).astype(int) + 1]
    bed_hard = np.where(band < 0.33, 0.25, 1.0)
    # Joints: the valleys of a ridged noise, soft, so erosion opens them into couloirs. (Voronoi cell borders
    # drew a polygon net across every face: tried first, board c186 row 2 note.)
    joint = _smooth(ridged(h.shape, joint_cells, rng, octaves=2), 0.06, 0.22)
    return np.clip(rock * bed_hard * (0.35 + 0.65 * joint), 0.0, 1.0), rock


def crag_shape(h, rock, seed=0, amount=1.0, beds=14):
    """Bedrock structure added to the shape before erosion: jointed, ridged blocks, then strata steps."""
    rng = np.random.default_rng(seed + 47)
    n = max(h.shape)
    rel = max(float(np.ptp(h)), 1e-9)
    lo = float(h.min())
    # 1. Rugged: ridged blocks at ~1/12, 1/24, 1/48 of the width (160, 80, 40 m on 2 km); joints as notches.
    rug = ridged(h.shape, n / 12.0, rng, octaves=3, gain=0.55) - 0.45
    z = h + amount * rock * rel * 0.11 * rug
    # 2. Stratify: a flat-ish bench then a steep riser per bed, beds dipping across the landscape.
    dip = _dip(h.shape, np.random.default_rng(seed + 5))
    lv = (z - lo) / rel * beds + dip
    step = np.floor(lv) + (lv - np.floor(lv)) ** 5
    zs = lo + rel * (step - dip) / beds
    return z + (zs - z) * 0.55 * amount * rock


def masks_from_work(cut, fill, relief):
    """wear, deposit 0..1 from the heights the engine removed and added, each scaled so the 97th percentile of the
    cells that changed at all is 1: both masks span their range on every type."""
    out = []
    for a in (cut, fill):
        moved = a[a > 1e-4 * relief]
        k = float(np.percentile(moved, 97)) if moved.size else 1.0
        out.append(np.clip(a / max(k, 1e-12), 0.0, 1.0))
    return out


def rock_breakup(z, dx, seed=0, bed_m=14.0, block_m=(60.0, 22.0, 9.0), amount=1.0):
    """S4 (scratch): bedrock breakup on the finished mesh heights (meters, spacing dx), where the ground is bare rock
    (steeper than scree can lie). Strata ledges and risers plus jointed blocks at 60, 22 and 9 m: the 5-60 m band that
    sits between the erosion grid and the rock grain and is empty today. Gaea: Stratify + Rugged/Shatter after Erosion;
    World Creator: Rocky/terrace filters masked by slope; World Machine: layer hardness in Thermal."""
    rng = np.random.default_rng(seed + 71)
    n = max(z.shape)
    k = max(int(round(6.0 / dx)), 1)
    c = np.pad(np.cumsum(np.cumsum(np.pad(z, k, mode="edge"), 0), 1), ((1, 0), (1, 0)))
    w = 2 * k + 1
    broad = (c[w:, w:] - c[:-w, w:] - c[w:, :-w] + c[:-w, :-w]) / (w * w)   # slope of the form, not of its texture
    gy, gx = np.gradient(broad, dx)
    deg = np.degrees(np.arctan(np.hypot(gx, gy)))
    patch = 0.6 + 0.4 * _smooth(value_noise(z.shape, 250.0 / dx, rng), 0.3, 0.7)
    rock = _smooth(deg, 34.0, 46.0) * patch
    # Blocks: each joint-bounded block sits a little proud or back from its neighbours (facets, not bumps).
    dz = np.zeros(z.shape)
    for size, amp in zip(block_m, (4.5, 2.2, 1.0)):
        wy = (value_noise(z.shape, 3.0 * size / dx, rng) - 0.5) * 1.6 * size / dx   # bend the joints: no straight polygon net
        wx = (value_noise(z.shape, 3.0 * size / dx, rng) - 0.5) * 1.6 * size / dx
        cells = size / dx
        gyc, gxc = int(z.shape[0] / cells) + 8, int(z.shape[1] / cells) + 8
        py, px, ph = rng.random((gyc, gxc)), rng.random((gyc, gxc)), rng.random((gyc, gxc))
        ty, tx = rng.random((gyc, gxc)) - 0.5, rng.random((gyc, gxc)) - 0.5  # each block face tilts its own way
        y, x = np.mgrid[0:z.shape[0], 0:z.shape[1]].astype(np.float32)
        y, x = (y + wy) / cells + 3.0, (x + wx) / cells + 3.0
        yi, xi = y.astype(int), x.astype(int)
        f1, hh = np.full(z.shape, 9.0, np.float32), np.zeros(z.shape, np.float32)
        for a in (-1, 0, 1):
            for b in (-1, 0, 1):
                cy, cx = yi + a, xi + b
                oy, ox = cy + py[cy, cx] - y, cx + px[cy, cx] - x
                d = np.hypot(oy, ox)
                near = d < f1
                hh = np.where(near, ph[cy, cx] + 2.2 * (ty[cy, cx] * oy + tx[cy, cx] * ox), hh)
                f1 = np.where(near, d, f1)
        dz += amp * (hh - 0.5) * 2.0
    # Strata: benches and risers every ~bed_m of height, beds dipping and of uneven thickness.
    yy, xx = np.mgrid[0:z.shape[0], 0:z.shape[1]] / float(n)
    dip = 9.0 * xx + 5.0 * yy + 3.0 * (value_noise(z.shape, 300.0 / dx, rng) - 0.5)  # beds dip ~4 deg: benches cross the contours
    lv = (z + dz * rock) / bed_m + dip
    fr = lv - np.floor(lv)
    riser = np.floor(lv) + fr ** 4
    strata = (riser - lv) * bed_m
    return z + amount * rock * (dz + 0.45 * strata)
```

The S1 wrapper used for the "after" renders:

```python
def erode(h, settings=None, hard=None, masks=False):
    s = dict(settings or {})
    s.update({"incision": 1.8, "channel": 3e-4, "talus_deg": 35.0, "cliff_deg": 75.0, "finish_blur": 6, "soften": 0.1})
    hard, rock = crag.hard_mountains(np.asarray(h, dtype=np.float64), seed=int(s.get("seed", 0)))
    h = crag.crag_shape(np.asarray(h, dtype=np.float64), rock, seed=int(s.get("seed", 0)))
    return _erode(h, s, hard, masks)
```

Mask fix B, the lines added to a copy of `erode()`:

```python
    cut_acc, fill_acc = np.zeros(z.shape), np.zeros(z.shape)
    for step in range(int(s["passes"])):
        z = z + rise
        z_in = z
        ...                                   # the pass, unchanged
        cut_acc += np.maximum(z_in - z, 0.0)
        fill_acc += np.maximum(z - z_in, 0.0)
    ...
        z = slump(z, talus, dx, s["final_slump"], cliff)          # in the final stretch-and-slump loop
        z = np.where(chan, np.minimum(z, before), z)
        cut_acc += np.maximum(before - z, 0.0)
        fill_acc += np.maximum(z - before, 0.0)
```

Mask fix A:

```python
    dz = after - fill(before)
    dz = dz - blur(dz, max(int(0.05 * max(after.shape)), 1))      # take out the broad lift
    k = np.percentile(np.abs(dz), 97)
    wear, deposit = np.clip(-dz / k, 0, 1), np.clip(dz / k, 0, 1)
```

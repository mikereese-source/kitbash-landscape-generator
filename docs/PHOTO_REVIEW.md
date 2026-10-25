# Photo review: every type read from ground-level photos (2026-10-25)

The lidar checks prove the numbers (slopes, drainage, roughness). This review asks the other question:
does it *read* as the place from a person's eye? Photos from Wikimedia Commons searches (links below).
Each type: what sells it, where ours differs, and the fix: **shape** (now, Geometry Nodes / erosion) or
**material** (M5, colour, banding, wetness, vegetation) or **scatter** (later: boulders, trees).

Mesa and Badlands were done first in detail (Pass 5 rebuild). Notes here cover the rest.

| Type | What sells it in photos | Where ours differs | Fix |
|---|---|---|---|
| **Rolling Hills** (Palouse) | Smooth, rounded, *asymmetric* hills (steep north faces, long gentle south slopes from wind-blown loess); hill after hill to the horizon; field patterns and shadows do much of the work | Shapes right, but hills are too symmetric and too few across at big sizes | Shape: one-sided steepness (a wind direction); Hill Size readout done. Material: crop strips, green/gold fields |
| **Mountains** (Sierra Nevada) | Jagged granite crests, broken summit ridges, big talus cones and scree fans at the foot of every cliff, smooth glaciated slabs lower down | Drained spines and tributaries read well (Mike signed the look). Crests a little rounded; scree fans weak | Shape: sharper crest only where hard rock (hard map); scree cones from talus deposits. Scatter: boulders |
| **Glacial Valley** (Yosemite) | Flat valley floor, sheer near-vertical granite walls (El Capitan), hanging side valleys with waterfalls, domes, talus slopes against the walls | Trough bends now, walls hard. Walls not sheer enough at the base; no hanging valleys | Shape: steeper lower walls, flatter wider floor, tributaries that end high on the wall (hanging valleys). Water: waterfalls later |
| **Canyon** (Grand Canyon rim) | Many stacked horizontal bands: cliff, slope, cliff, slope; buttes and temples standing inside; flat rim | Bands and hard rock read; inner buttes rare | Shape: isolated temples (from hard cap blocks, like the new Mesa). Material: the red/buff/white bands |
| **Coastal Cliffs** (Torrey Pines) | Golden sandstone bluff with sharp crest, deep rilled gullies down the face, a beach and wave-cut platform at the foot, flat terrace on top | Platform clean; gullies branch; bluff a bit low and soft | Shape: taller, steeper bluff face with fine vertical rills (the comb is right on the *face* itself, not across the land); beach strip. Material: sand vs rock |
| **Volcanic** (Craters of the Moon) | Black, rough, broken lava (aa) and ropy (pahoehoe) flows with clear edges; low spatter cones and cinder cones of different sizes; sagebrush in the gaps | Lobes and cones visible now; flows too smooth on top | Shape: rougher broken flow surface (blocky grain on the lobes), pressure ridges; cones with breached sides. Material: black lava, red cinder |
| **Riverbed** (braided rivers) | Many shallow interlacing channels and gravel bars, very flat, wide; braids split and rejoin | Too few braids, reads like a few separate gullies | Shape: denser braids that split and rejoin (several offset channel fields), bars between. Water: the channels hold water (water plane) |
| **Sand Dunes** (White Sands) | Crisp sharp crests with steep slip faces, soft ripples, wide smooth interdune flats | Matches well (all checks pass) | Shape: sharpen crests a touch. Material: white or orange sand, ripples in normal map |
| **Volcano: Strato** (St Helens) | Crater walls are sheer and banded; lava dome inside; rough rubble; gullies radiating down the flanks; snow/ice on the rim | Shape and scale right; crater walls smooth, no dome | Shape: steeper banded crater walls, an optional dome in the crater; more gully relief |
| **Volcano: Caldera** (Crater Lake) | A lake fills it; steep cliff walls all around, an island cone (Wizard Island), uneven rim | Dry bowl; even rim | Shape: Island toggle (a small cone inside), uneven rim heights. Water: lake on by default |
| **Volcano: Cinder** (SP Crater / Sunset Crater) | Near-perfect cone at ~30-33 deg with a flat-floored summit crater; a lava flow often from the base | Round now; good | Shape: optional breach with a lava flow from the base (reuse the Breach control) |
| **Cratered Surface** (Apollo photos) | Very soft rolling ground, every scale of crater, sharp fresh ones rare, scattered boulders near fresh craters | Tuned to LROC; matches | Scatter: boulders near fresh craters (later) |
| **Seabed** | (Photos underwater aren't useful at this scale; the NOAA survey is the reference) | Roughness now works | None now |

## Takeaways

1. Most remaining realism is **material and scatter** work (colour bands, lava colour, sand vs rock,
   boulders, vegetation): M5 and later. The shapes are close on most types.
2. Shape work still worth doing before the gate, smallest first: Riverbed braids, Rolling Hills
   asymmetry, Caldera island + lake, Glacial sheer lower walls, Volcanic rough flow tops.
3. The new **hard-rock map** is the tool for most of these (caps, crests, temples, cliff faces).

## Sources (Wikimedia Commons searches)
- [Palouse rolling hills](https://commons.wikimedia.org/w/index.php?search=Palouse+rolling+hills&title=Special:MediaSearch&type=image)
- [Sierra Nevada granite peaks](https://commons.wikimedia.org/w/index.php?search=Sierra+Nevada+mountains+granite+peaks+ridge&title=Special:MediaSearch&type=image)
- [Yosemite Valley](https://commons.wikimedia.org/w/index.php?search=Yosemite+Valley+U-shaped+glacial+valley&title=Special:MediaSearch&type=image)
- [Grand Canyon from rim](https://commons.wikimedia.org/w/index.php?search=Grand+Canyon+from+rim&title=Special:MediaSearch&type=image)
- [Torrey Pines cliffs](https://commons.wikimedia.org/w/index.php?search=Torrey+Pines+cliffs&title=Special:MediaSearch&type=image)
- [Craters of the Moon](https://commons.wikimedia.org/w/index.php?search=Craters+of+the+Moon+National+Monument&title=Special:MediaSearch&type=image)
- [Braided rivers](https://commons.wikimedia.org/w/index.php?search=braided+river&title=Special:MediaSearch&type=image)
- [White Sands dunes](https://commons.wikimedia.org/w/index.php?search=White+Sands+dunes&title=Special:MediaSearch&type=image)
- [Mount St Helens crater](https://commons.wikimedia.org/w/index.php?search=Mount+St+Helens+crater&title=Special:MediaSearch&type=image)
- [Crater Lake caldera](https://commons.wikimedia.org/w/index.php?search=Crater+Lake+caldera+rim&title=Special:MediaSearch&type=image)
- [Apollo lunar surface](https://commons.wikimedia.org/w/index.php?search=Apollo+lunar+surface+craters+panorama&title=Special:MediaSearch&type=image)
- [Badlands South Dakota](https://commons.wikimedia.org/w/index.php?search=Badlands+South+Dakota+formations&title=Special:MediaSearch&type=image)

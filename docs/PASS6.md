# Pass 6 (2026-10-26): Mesa and Badlands against the photos and lidar, erosion map fix

Render: m2/pass6-mesa-badlands.png (top: Mesa Field, Hero Butte, Hero Butte close; bottom: Badlands
Wall, Mounds, Mounds close). Rollback: git (d7d84db is the last commit before this pass).

## What changed (D66)
- **Mesa floor:** rough, dissected desert floor instead of flat: gentle swells plus folded ridgelets
  (Roughness sets how many), a steeper drain to one end, and erosion settings that cut dense gullies
  (incision 2, channel 7e-5). Real Monument Valley slope50 15.3 deg; ours 11.9 (was 1.0).
- **Mesa talus aprons:** two parts. In the shape, an apron built from the distance to the block's edge
  (Voronoi Distance to Edge plus the neighbouring block, F2), so it always hugs the blocks (Pass 5's
  separate noise left orphan lumps). In the erosion engine, a new `apron` step: a smooth concave cone
  from the caprock (chamfer distance to the hard caps, no creases) reaching ~7% of the width out and
  half the cliff height up, plus a gentle `pediment` beyond it so the floor drains to washes between
  the blocks. Erosion then cuts radial gullies into the aprons, as in the lidar.
- **Softer block edges:** a short rounded bevel where a cap meets open ground; joint randomness 0.8.
- **Hero Butte style:** one standalone butte in the middle, still built from whole joint blocks.
  New sliders for both Mesa styles: **Talus Spread** (apron reach, shape and erosion) and **Caprock
  Tiers** (none to a tall stepped upper tier). Footprint = Plateau Coverage, cliff height = Height,
  flute depth = Roughness. A slider can now stretch an erosion setting from types.json
  (`"erosion": {"apron": [0.4, 1.6]}`).
- **Mesa grain:** rock 1.2, grain roughness 0.7 (the 4-16 m scales were too smooth).
- **Badlands Wall:** shallower gullies (incision 3.5, cliff 62 deg, talus 42 deg, soften 0.12).
  s64 0.53 vs 0.35 real, inside the band (was 0.63, the one failing measure).
- **Badlands Mounds:** rebuilt as separate haystacks: bell profile with round shoulders, about one
  spacing across and packed at 1.2x the old density, so they read ~1:1.5 tall to wide; the two
  nearest mounds are both drawn, so cells meet without seams. Mounds get their own lighter erosion
  (fine rills: incision 1.5, channel 1e-4, talus 40 deg). A style can now change erosion settings.
- **Erosion map, every type:** stored at one texel per grid point and read with the node tree's
  smooth cubic lookup. Doubling it first (Catmull-Rom) rang at every sharp cliff, alternating texel
  to texel; that showed as a false 9-12 dB "114 m" spike on Mesa, and plain-average doubling left a
  kink every 4 m (Badlands 5.6 dB at 4.3 m). `upsample2` removed.

## Checks
Unit tests 17/17. T6b (1 m lidar) 9/14 (was 7/14): Mesa and Badlands now pass; Riverbed T6 (30 m)
passes too. T6c (drainage, report only) 4/14: Mesa now passes.
- **Mesa: passes T6b and T6c** for the first time (Monument Valley 1 m). T6 (30 m) still fails relief
  and slope50, but that 30 m tile has no true mesas (Pass 5 note); the 1 m Monument Valley tile is the
  reference that counts.
- **Rolling Hills regressed** on T6 (relief), T6b (slope90) and T6c (concavity). Not from this pass: the
  new default look Mike picked on 2026-10-25 (Height 0.0625, Sharpness 2) is about twice the relief of
  the old one (110 m vs 56 m over 2 km; Palouse ~150 m but gentler slopes, slope90 13 deg vs ours 27).
  Mike to decide: keep his look, or soften the default toward the Palouse.
- No other type changed result.

## Lesson
Node edits after a library rebuild don't show until GROUP_VERSION is bumped: the prebuilt group is
appended whenever its version matches (two Mounds renders came out unchanged).

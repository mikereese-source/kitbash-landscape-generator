# Pass 8 (2026-10-26): photo-review shape fixes

Render: m2/pass8-photo-review.png (top: Rolling Hills, Volcanic, Caldera; bottom: Strato, Coastal
Cliffs, Canyon). Rollback: git (c642764 is the last commit before this pass).

## What changed (D69)
- **Rolling Hills, one-sided hills:** new erosion step `lean`: each row shifts downwind in proportion
  to height, so tops lean over, one face steepens and the other stretches out (wind-built Palouse
  loess). Hills lean 0.03 across the ridges (Y); 0.05 pushed slope90 out of band (18.5 vs 17.8).
- **Volcanic, rough flow tops:** broken aa rubble on every flow (two scales of folded noise; Roughness
  sets it), lower lobe fronts, broader plain. Rock grain can't do this on types that aren't eroded: it
  only starts below the shape's own detail. slope50 3.6 -> 7.1 deg (real 10.2): passes. s64 still 1.9x
  real (was 2x), the one T6b fail left.
- **Caldera island and Strato dome:** new Volcano slider **Inner Cone** (Strato and Caldera only):
  an off-centre island cinder cone with its own summit crater in a Caldera (Wizard Island), a rounded
  rubbly lava dome near the middle of a Strato crater (Mount St Helens). The lake waits for water.
- **Coastal Cliffs, taller bluff and beach:** narrower, steeper bluff zone, a sand beach ramping up to
  its foot, finer erosion drainage (channel 3e-4, soften 0.3) so ravines dissect the land behind the
  bluff as at Torrey Pines. **Cliffs now passes T6b** (slope90 20.2 vs 26.9 real; h_mid 0.54 vs 0.74
  sits on the band edge).
- **Canyon, inner buttes:** small isolated temples inside the canyon: the depth field is lifted back
  toward the rim in patches, so the strata step their sides into the same tiers as the walls, with a
  hard cap. Small and subtle at 800 m; Mike to judge.

## Bug fixed on the way
The Inner Cone code reused the name `inner` (the inner-area selection the Height stretch uses), so
every type's relief came out wrong (Dunes by 10^13). Caught by checking mesh relief against Height.

## Checks
Unit tests 17/17. T6b (1 m) 10/14 (was 9): Cliffs now passes; Hills, Mesa, Badlands, Glacial,
Canyon, Dunes, Mountains, Seabed, Cinder, Strato pass. Still failing: Volcanic (s64), Riverbed (spikes),
Caldera (slope50, s64, spikes). T6 (30 m) 11/13. T6c (report only) 4/14.

## Note
render_sheet.py crashed Blender (EXCEPTION_ACCESS_VIOLATION) on a 6-shot batch; each shot renders
fine on its own. Not seen in the add-on itself.

# Pass 5 (2026-10-25): Mike's review fixes, Mesa and Badlands rebuilt from photos, speed

Renders: m2/pass5-mesa-badlands.png (top: Mesa overview, low camera, Coverage 0.1 buttes, Coverage 0.9
plateau; bottom: Badlands Wall overview, low camera, Mounds x2). Realism sheet: m2/pass5-real-vs-ours.png.
Photo review of all types: PHOTO_REVIEW.md. Rollback: snapshots/kitbash_landscape_generator-pass4-2026-10-25.zip.

## What changed (D63)
- Erosion tick box gone: eroded types always use the drained primary shape; "Erosion Amount" 0 = full
  shape detail, no erosion run.
- Seabed Roughness wired in (reef break-up and ledges, ripple strength).
- Feature Size named per type (Hill Size, Ridge Spacing, Dune Spacing, Mesa Size, ...) with an
  "About N ... across" readout.
- Panel sections fold open/closed (In this scene, Landscape type, Size, Shape).
- Speed: erosion runs on a background thread (Blender stays responsive); a 128-grid quick look shows in
  under a second, the full result follows (2 km High Mountains: 0.85 s quick, ~6 s full). Engine ~1.5x
  faster (vectorised slump, redundant fills removed).
- Mesa: joint-block outlines (straight edges, corners), one caprock level, sheer fluted cliffs
  (Roughness = flute depth), stepped talus ledges, hard caprock/cliff, soft talus; default height 0.15.
- Badlands: Style Wall & Pinnacles (escarpment between a gently sloped grass table and the floor,
  fluted gullies, remnant buttes, concave apron, thin hard beds and caps) or Mounds (banded haystacks).
  The table slopes gently to the rim: dead flat, erosion went chaotic and failed the scale test (T1).

## Checks
Unit tests 14/14. Badlands: T6 30 m PASS, 1 m fails s64 (gully relief strong), structure 3/4.
Mesa: the reference tile has no true mesas, so its numbers say little (30 m relief/slope, 1 m slope50);
judge by eye against the photos. Monument Valley tile still needs Mike's download OK.

## Monument Valley reference (2026-10-25)
Downloaded USGS 1 m tiles x58y410 and x57y410 (UT_WestEast_B22, 206 MB, Mike approved). USGS 1 m stops
at the Arizona border, so the Mittens and Merrick Butte (Navajo Nation, AZ) aren't covered; the Utah side
(Eagle Mesa area) is. Mesa window now 37.03279, -110.07921 (exact). Real: a mesa with stepped cliff
bands, wide talus aprons, and a heavily gullied, rough floor; slope50 15 deg vs ours 1 deg (our floor is
flat desert). Stripe spike 9.1 dB on ours (the joint-block edges). Next: rougher, gullied floor and wider
talus aprons; soften the block-edge stripe.

## Mike's live review (2026-10-25, after Pass 5)
- Style picker first in Shape; Detail its own section (Size, Detail, Shape).
- Volcano Roughness: crags and rubbly flanks scale with it (0.2-2.4x).
- Volcano no longer "too perfect": crater edge wanders, rim height varies, chutes down the inner wall,
  breach walls wander downhill, meandering channels and rubble on the breach floor.
- Glacial: softer ridge crests (soften 1.0, talus 33); still to check against perspective photos
  (the pinching between ridge and trough).
- "Eroding..." note in the panel while erosion runs (High takes a few seconds).
- **Saved presets (Mike 2026-10-25, must-have):** "Save Preset" names and stores the full look (type,
  style, every slider, seed, erosion, size) to a user presets file that lives outside any .blend, so it
  shows in every project; a preset list to load one onto the selected landscape (or Add it new), plus
  rename and delete. KitBash starter presets can ship alongside (read-only). Same JSON for three.js later.
  (Not the size presets dropped in D21: those were fixed sizes.)

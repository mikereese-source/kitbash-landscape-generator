# Pass 7 (2026-10-26): Rolling Hills toward the Palouse, Glacial Valley from Yosemite

Renders: m2/pass7-glacial-hills.png. Rollback: git (48bfd6c is the last commit before this pass).

## What changed (D68)
- **Rolling Hills default** (Mike: "towards the Palouse numbers"): Height 0.0625 -> 0.045, Peak
  Sharpness 2 -> 1.4; Roughness, Hill Size and erosion stay as Mike set them. Palouse 1 m slope90
  13.2 deg; ours 17.0 (was 26.6, band up to 17.8). Passes T6 and T6b again; T6c 3 of 4 (concavity out).
- **Glacial Valley rebuilt from Yosemite photos:**
  - Flat floor between sheer walls that stand straight up from it and round over at the rim
    (profile 1 - (1 - s)^2: steepest at the foot), hard granite on the wall band.
  - The rim is one even height (small variation along the valley), so ridges no longer pinch into the
    trough. Pass 4's walls borrowed the Mountains spines, which ran parallel to the trough and pinched a
    second valley in beside it.
  - Above the rim, drained mountains with ridges every way, rising away from it; firm (domes).
  - Hanging valleys: side valleys at intervals along the trough cut into the uplands but never below
    the rim, so their floors end high on the wall.
  - Erosion soften 1.0 -> 0.6 (uplands melted); default Height 0.17 -> 0.19 (Yosemite 8 km relief 0.163).

## Checks
Glacial: T6 PASS, T6b PASS (slope50 16.2 vs 29.9 real, slope90 42.7 vs 63.2: the 2 km Yosemite window is
mostly wall, ours is a whole valley), T6c 3 of 4 (concavity 0.39 vs 0.82). Hills: T6 PASS, T6b PASS.
T6 (30 m) 11/13.

Render layout: top row Glacial overview and low view (seed 0); bottom row Glacial seed 12, Rolling Hills 1 km.

## Open for Mike's review
- The hanging-valley notches sit at fairly even spacing along the wall (a comb on some seeds).
- Rolling Hills at 1 km shows only a few hills: hill count is Hill Size / Proportional Feature Scaling.

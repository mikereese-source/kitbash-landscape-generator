# Realism Pass 4 (2026-10-24): volcano outlines, Glacial, Cliffs, Volcanic, smooth types

Sheet: m2/pass4-real-vs-ours.png (two pairs per row, real left | ours right; order as in PASS2.md).

## What changed (D62)

- **Volcano outlines:** one smooth octave of lopsidedness, faded to round at the summit (the crater
  rim had scalloped). Per-style amount: Cinder nearly round (0.12), Strato and Collapsed 0.6,
  Shield 0.5, Caldera 0.45. The summit offset scales with it.
- **Glacial Valley:** the trough bends (axis noise x2 frequency and amplitude). Granite trough walls
  are hard rock (`lg_hard`).
- **Coastal Cliffs:** with erosion on, the stretched-noise ravines are gone (they were the comb).
  The bluff caprock is patchy (hard headlands, soft reaches), and the bluff zone is wider. Erosion
  channel threshold is 0.0005 and incision 3. Ravines branch now, and the structure check passes 4/4.
- **Volcanic:** softer flow fronts (1 m slope90 now matches); lobes and plain rebalanced.
- **Rock grain** starts at the shape's detail floor instead of 30 m (no gap or overlap between them).
- Tried and reverted: a steeper Volcanic regional slope (failed 30 m relief) and stronger grain on
  Hills/Riverbed (barely moved their stripe).

## Scorecard

Unit tests 14/14. T6 (30 m) 11/13. T6b (1 m) 8/14. T6c 4/4 on 5 types, 3+/4 on 8.

| Type | T6 | T6b | T6c | Status / read |
|---|---|---|---|---|
| Mountains | PASS | PASS | 3/4 | **Checks pass: needs Mike's eye** |
| Canyon | PASS | PASS | 3/4 | **Checks pass: needs Mike's eye** |
| Badlands | PASS | PASS | 4/4 | **Checks pass: needs Mike's eye** |
| Sand Dunes | PASS | PASS | 4/4 | **Checks pass: needs Mike's eye** |
| Glacial Valley | PASS | PASS | 2/4 (rough split, drainage) | Trough bends now; looks better than it measures |
| Volcano: Cinder | PASS | PASS | 2/4 | Round now (better look); structure dropped from 4/4 |
| Volcano: Strato | PASS | PASS | 1/4 | Crater is a closed pit by nature; lopsided foot reads well |
| Coastal Cliffs | n/a | slope90 12 / 27 | 4/4 | Drains like the real coast; bluff zone still too narrow |
| Rolling Hills | PASS | stripe 34 m | 4/4 | Stripe at the shape's detail cutoff: needs a smoother last-octave fade |
| Riverbed | relief | stripe | 4/4 | Same stripe; very low relief |
| Mesa | PASS | slope50 | 2/4 | Reference tile isn't true mesas |
| Volcanic | relief | slope50, s64 | 3/4 | Visible lobes and cones now; measures trade against each other |
| Seabed | n/a | PASS | 1/4 | Unchanged since Pass 1 |
| Volcano: Caldera | PASS | many | 0/4 | Real window is mostly lake |

## Mike's review notes (for the final targeted pass)

- **Mountains:** looks right with erosion on, even at Amount 0. Remove the Erosion tick box; the slider
  is labelled "Erosion Amount" (0 = no erosion). Eroded types always use the drained primary shape;
  Amount 0 shows the shape's full fine detail with no erosion run. Retire the pre-erosion recipe shapes
  that only showed when the box was unticked.
- **Seabed:** wire Roughness into the recipe (reef ledge/break-up detail, ripple strength): it does nothing now.
  Peak Sharpness stays the same on every type (its smooth-to-rough look on Seabed comes from the
  sloping shelf); the deliberate version is the Gradient control (parked).
- **Feature Size:** rename per type (Hill Size, Peak Spacing, Dune Spacing, ...) with an "≈ N across"
  readout (Mike to confirm the option).
- **Speed (Mike: always think about how fast artists can dial in):** erosion in a background thread so
  Blender never freezes; progressive (a quick coarse erosion right away, the full one when idle);
  profile the engine's Python loops. Measure before/after on Preview and High.

# Realism Pass 3 (2026-10-24): erosion keeps form and texture, volcanoes

Sheet: m2/pass3-real-vs-ours.png (two pairs per row, real left | ours right; order as in PASS2.md).
Erosion amount renders: m2/pass3-erosion-amount.png (Amount 0 / default / 1 for Mountains, Canyon,
Mesa, Badlands).

## What changed (D60, D61)

- **Erosion Amount is erosion time.** Every process scales with it: 0 = the plain shape, 1 = full.
  Low Amount used to melt the shape anyway, because only incision scaled. A height blend was tried
  and dropped: it dammed rivers into pools.
- **Hard rock from the recipe.** Canyon cliff bands and rim, Mesa caprock, Badlands crests and the
  Cliffs bluff erode slower, stand near vertical and aren't smoothed. Canyon cliffs back to 70 deg.
- **Texture survives erosion.** The shape's own fine detail returns on slopes and ridges (not in
  channels or floors). Rock grain now starts at ~22 deg with 20% everywhere.
- **Edges:** erosion runs on a padded grid and crops back, so no drips or frame.
- **Defaults:** Amount 0.6 Canyon/Mesa/Badlands, 0.7 Cliffs, 0.8 the rest.
- **Detail levels:** Preview / High / Ultra (labels only; saved files unchanged).
- **Volcanic:** lobes and cones carry the relief (the broad plain hid them). Cones are broad, with
  craters.
- **Volcanoes:** an off-centre summit and a lopsided outline per seed. New **Collapsed** style (St Helens:
  horseshoe amphitheater, hummocky debris).

## Scorecard

Unit tests 14/14. T6 (30 m) 12/13 (Pass 2 11/13). T6b (1 m) 8/14 (7/14). T6c (structure) 5/14 at 4/4,
11 types at 3+/4.

| Type | T6 | T6b | T6c | D57 status / read |
|---|---|---|---|---|
| Mountains | PASS | PASS | 3/4 | **Checks pass: needs Mike's eye** |
| Canyon | PASS | PASS | 3/4 | **Checks pass: needs Mike's eye** (new this pass) |
| Badlands | PASS | PASS | 4/4 | **Checks pass: needs Mike's eye** (new this pass) |
| Sand Dunes | PASS | PASS | 4/4 | **Checks pass: needs Mike's eye** |
| Volcano: Cinder | PASS | PASS | 4/4 | **Checks pass**, but the outline is now too scalloped (see review) |
| Glacial Valley | PASS | PASS | 2/4 | Trough still straight bands; concavity 0.48 vs 0.82, rough split 0.88 vs 1.52 |
| Volcano: Strato | PASS | PASS | 2/4 | Shape right at scale; closed pits in the crater, high concavity |
| Rolling Hills | PASS | stripe 8.5 dB | 4/4 | Stripe is in the plain shape (detail cutoff vs grain start) |
| Mesa | PASS | median slope 3.5 / 10 | 3/4 | Reference tile isn't true mesas |
| Volcanic | PASS | slope90, h_mid, s64 | 3/4 | Lobe fronts too sharp and too much 64 m relief |
| Coastal Cliffs | n/a | h_mid, stripe | 3/4 | Bluff gullies still a comb |
| Riverbed | relief (30 m) | stripe | 4/4 | Drains like the real Platte now; too few braids |
| Seabed | n/a | PASS | 1/4 | Unchanged since Pass 1 (pits on reefs) |
| Volcano: Caldera | PASS | slope50, s64 | 0/4 | Real window is mostly lake |

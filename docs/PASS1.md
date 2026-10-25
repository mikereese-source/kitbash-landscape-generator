# Realism Pass 1 (2026-10-23): first cut of primary shapes + erosion

Erosion on for 8 types (Mountains, Canyon, Badlands, Coastal Cliffs, Glacial Valley, Rolling Hills,
Riverbed, Mesa), each with a drained primary shape (D55). No erosion: Sand Dunes, Cratered Surface,
Seabed, Volcanic, Volcano (its crater is a real pit; erosion would fill it). New 1 m references for
Hills (Palouse), Mesa, Volcanic (Craters of the Moon), Glacial (Yosemite), Riverbed, Strato
(St Helens), Caldera (Crater Lake). Sheet: m2/pass1-real-vs-ours.png.

Checks: unit tests 14/14; T6 30 m 10/13 (fail: Mesa slope50, Glacial slope50, Riverbed hyps);
T6b 1 m 6/14; T6c structure 2/14 (Dunes, Glacial). Closed pits now 0 on every eroded type.

| Type | Close range (T6b) | Structure (T6c) | Read |
|---|---|---|---|
| Mountains | PASS | concavity 1.31 / 0.44 | Drained spines + tributaries; spines too parallel |
| Canyon | slopes too steep (60° p90 / 37°) | concavity 0.86 / 0.28 | Plateau now dissected by branching channels; walls too steep, fans too radial |
| Badlands | stripes 5.2 dB | concavity 0.79 / 0.39 | Dense gully network, much closer; gully spacing too even |
| Coastal Cliffs | stripes 4.6 dB | concavity | Gullies still a comb along the bluff |
| Glacial Valley | PASS | PASS | Trough + drained walls; walls too parallel; 30 m median slope low |
| Rolling Hills | PASS | concavity 2.1 / 0.45 | Soft hills, faint drainage; fewer channels than real |
| Mesa | median slope 5.5° / 14.4° | concavity, split | Blocks small and scattered; real window is mixed terrain (pick a better one) |
| Riverbed | h_mid | concavity | Real window is farmland, not the braided channel (move it) |
| Seabed | PASS | pits 0.11 | Unchanged this pass |
| Sand Dunes | PASS | PASS | Unchanged |
| Volcanic | all slope bands | pits, split | Regular dotted cones on flat lava; real is overlapping flow lobes |
| Volcano: Cinder | PASS | concavity, split | Unchanged |
| Volcano: Strato / Caldera | slopes far too gentle | — | 2 km real windows sit on a steep flank; ours shows the whole cone at that size (scale mismatch) |

Pass 2 candidates: break up spine/gully regularity (Mountains, Glacial, Cliffs, Badlands), canyon wall
steepness and fan shape, move the Riverbed and Mesa reference windows, Volcanic flow lobes, compare
volcanoes at matching size.

**Pass 2 approved (Mike, 2026-10-23), start next session:** all candidates above: break up spine/gully regularity (Mountains, Glacial, Cliffs, Badlands); Canyon wall steepness and fan shape; move the Riverbed and Mesa reference windows; Volcanic flow lobes; compare volcanoes at matching size.

**Exit rule (D57):** a type is done when it passes T6 and T6b, is within band on at least 3 of 4 structure measures, and Mike would ship it from the sheet. When every type is done, M2 re-gates.

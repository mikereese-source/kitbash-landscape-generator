# KitBash Landscape Generator — P5 Type Sheet

**Status:** Approved (2026-10-22)

One reference photo, target look, key forms, a starter recipe and real-world scale for each type. Every photo is freely licensed on Wikimedia Commons and was checked on 2026-10-22; the page is `https://commons.wikimedia.org/wiki/File:<name>`. Recipe numbers are in a normalized 0–1 tile: **features** = how many main forms cross the tile, **relief** = height range as a fraction of the width. These recipes seed the type JSON (D5) and are what T6 reviews against.

| # | Type | Reference (Commons file, license, place) | Target look | Key forms | Starter recipe | Real scale (tile / relief) |
|---|---|---|---|---|---|---|
| 1 | Rolling Hills | PalouseHillsFromSteptoeButteMay2017-10.jpg — CC BY 4.0, Palouse, WA | Soft rounded swells, no sharp edges or bare rock | Domes, shallow saddles, gentle swales | fbm 3–4 octaves, 3–5 features, relief 0.04–0.08, light warp, low erosion | 2–5 km / 50–150 m |
| 2 | Mountains | Central_Teton_range_WY1.jpg — CC BY-SA 4.0, Teton Range, WY | Jagged peaks on knife-edge ridges, steep faces, scree aprons | Ridgelines, couloirs, scree fans, flatter valley floor | Ridged multifractal 6–8 octaves, 2–4 peaks, relief 0.25–0.4, high erosion | 8–15 km / 1.5–2.5 km |
| 3 | Sand Dunes | Erg_Chebbi_sunset.jpg — CC BY-SA 4.0, Erg Chebbi, Morocco | Repeating crests: gentle wind side, steep slip face | Asymmetric crests, ~33° slip faces, flats, ripples | Directional sawtooth warped into crescents, 4–8 crests, relief 0.05–0.12, fine ripple layer, slope clamp | 1–3 km / 30–150 m |
| 4 | Seabed ⚠ | Sea_floor_sand.jpg — CC BY 2.0 (weak: close-up only) | Smooth sediment plains with ripples, rock outcrops, reef mounds | Ripples, boulders/reef patches, shallow trenches | Low fbm + directional ripples + sparse Voronoi rock mask, relief 0.03–0.08 | 0.2–2 km / 5–50 m |
| 5 | Coastal Cliffs | Falaises_d'Amont.jpg — CC BY-SA 4.0, Étretat, France | Flat headland ending in a near-vertical wall above the sea | Plateau top, banded face, wave-cut platform, sea stacks, coves | fbm plateau × warped coastline step, 2–4 headlands, relief 0.1–0.2, optional strata, sea-level clamp | 1–3 km / 60–200 m |
| 6 | Canyon | Grand_Canyon_Mather_Point_2013.jpg — CC BY-SA 3.0, Grand Canyon, AZ | Deep channel cut through flat rock, stepped walls | Flat rims, stepped bands, side canyons, inner gorge, buttes | Flat base minus a warped meandering channel + 3–6 side channels, relief 0.15–0.3, terraces 6–12 steps | 5–15 km / 0.5–1.8 km |
| 7 | Mesa | Mesa_and_Buttes,_Monument_Valley,_AZ.jpg — CC BY-SA 2.0, Monument Valley | Flat-topped blocks with sheer caprock cliffs over a desert floor | Flat tops, vertical upper walls, talus skirts, buttes, spires | Thresholded Voronoi plateaus + smoothstep cliff + talus ramp, 2–6 mesas, relief 0.08–0.15, 1–3 hard terraces | 3–10 km / 100–300 m |
| 8 | Badlands | Badlands_along_South_Dakota_Highway_44…_2009_(1).jpg — CC0, Badlands NP, SD | Dense gullies, sharp fins and spires, colored bands | Rills, fins, pinnacles, flat pediment | High-frequency ridged + fbm, 20–60 spurs, relief 0.05–0.1, many soft bands, high erosion | 0.5–2 km / 50–150 m |
| 9 | Volcanic | Mount_Bromo_at_sunrise…_(background).jpg — CC BY-SA 3.0, Bromo, Java (reference to replace with a lava-field shot) | The ground around volcanoes: rough lava fields, flow lobes, scattered cinder cones | Lava flow lobes, pressure ridges, small cinder cones, collapsed lava channels | Lobed flow masks + rough fBM, a few small cones, relief 0.03–0.08 | 1–5 km / 20–150 m |
| 9b | Volcano | Mount_Bromo_at_sunrise…_(background).jpg (and Fuji, Mauna Loa, Sunset Crater, Crater Lake for the styles) | One big volcano as the hero feature | Styles: Stratovolcano (steep symmetric cone, summit crater), Shield (broad gentle dome), Cinder Cone (small steep cone, big bowl crater), Caldera (collapsed ring rim around a flat floor or lake). Breach opens the crater on one side | Radial profile per style (concave exponent, crater bowl, rim ring), polar ridged noise for gullies, breach = angular notch in rim | Strato 2–4 km tall; shield 4–9 km tall, 100+ km wide; cinder 50–400 m |
| 10 | Glacial Valley | Tunnel_View,_Yosemite_Valley,_Yosemite_NP_-_Diliff.jpg — CC BY-SA 3.0, Yosemite | Broad U-shaped trough, flat floor, steep smooth walls | U section, flat floor, cirques, hanging valleys, moraines | Ridged mountains minus a U profile (exponent 2–3) along a curving path, 2–3 hanging valleys, relief 0.2–0.35 | 4–10 km / 0.8–1.5 km |
| 11 | Riverbed | Braided_river._Canterbury_NZ._(14663811351).jpg — CC0, Canterbury, NZ | Wide gravel floor with braided channels and low banks | Braids, gravel bars, cut banks, edge terraces, boulders | Flat base minus warped channel bands along the flow, 3–8 braids, relief 0.01–0.04, 1–2 bank steps, water mask | 0.5–2 km / 2–20 m |
| 12b | Cratered Surface | Meteor Crater AZ (elevation data; photo to add) | A field of impact craters, fresh to worn | Bowls with raised rims at several sizes, overlapping | Voronoi bowls + Gaussian rims at 3 sizes; Age lowers rims and fills bowls | 1–5 km / 20–200 m |
| 12 | Cave | Lava_River_Cave_Arizona-interior_view.jpg — CC BY-SA 4.0, Lava River Cave, AZ | A hill with a chamber inside: arched ceiling, lumpy floor, formations | Arched ceiling, rubble floor, alcoves, chambers joined by passages | Always starts with an entrance on a steep face. Layouts: Entrance / Entrance + Tunnel / Entrance + Cavern. SDF stage (proven in P2): tunnel = points along a procedural curve into a sparse SDF, cavern = warped chamber, both minus billow noise | Passage 50–500 m / ceiling 3–30 m |

## Cliff features (toggles on any type)
| Feature | Reference | How it's built |
|---|---|---|
| Side Cliffs | The_Nose_El_Capitan_Yosemite.jpg — CC BY 2.0 | Slope/step mask pushes faces near-vertical. Horizontal face noise, vertical fractures, scree ramp. Works on the heightfield up to ~85° |
| Overhangs | Cliff_Palace-Colorado-Mesa_Verde_NP.jpg — CC BY-SA 4.0 | SDF stage: carve an undercut band under a hard caprock |
| Arches | Delicate_Arch_sunset.jpg — CC BY-SA 3.0 | SDF stage: noise-displaced arc shape, legs blended into the terrain |
| Stalactites | 2015_Jaskinia_Niedźwiedzia_w_Kletnie,_szata_naciekowa_26.jpg — CC BY-SA 4.0 | Instanced tapered cones on faces pointing down (normal z < −0.7), clustered. 0.1–3 m |
| Stalagmites | Stalagmite_in_Vrelo_Cave.jpg — CC0 | Blunter cones on cave floors, placed under stalactites as drip pairs. 0.2–5 m |

## Open items
- **Seabed** needs a better reference: a wide underwater shot (NOAA Ocean Exploration images are public domain).
- **Real scale vs default size:** real tiles are often kilometers wide. The tool defaults to 200 m and keeps shapes at any size, so these scales set the *look* (relief ratio), not the default size.

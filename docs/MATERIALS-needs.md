# M7 material needs list (2026-11-06)

What the M7 auto-material spike (Mountains) and the full set of 14 types and 5 climates need. Research only:
nothing has been downloaded. Built on RESEARCH-materials.md, its "Mike's answers", D194 and D195.

**Rules this list follows (D194, D195):**
- Procedural plus texture maps. The spike uses CC0 Poly Haven sets; the final version uses only KitBash 3D (KB3D)
  materials. So every texture row has a blank **KB3D library match** column for Mike.
- Climates: Temperate, Arid, Alpine, Volcanic, Lush.
- Camera range: from background mountains down to walkable game ground (close, not macro). Near-ground sets target
  **about 1024 px/m**: tileable, layered, and blended with distance into a large-scale colour.
- Water shaders are their own milestone (left out). Wet edges stay in, as a ground effect.
- Grass and foliage come later as instanced meshes (section 5). The grass *ground* layer here is the turf colour
  under them.

**How to read "procedural / texture".** *Texture* = the tiling Poly Haven (later KB3D) set gives the near-ground
colour, roughness, normal and height. *Procedural* = Blender nodes do the placement (mask rules, height blend), the
large-scale colour, tint shifts per climate, anti-tiling and the effects with no texture (wetness, glow).
**Maps per texture set:** colour (diffuse), roughness, normal (OpenGL), height (displacement, 16-bit EXR, used for the
height blend and for bump or Cycles displacement). AO is not needed (Blender computes it); it can be added later.

**Resolution rule.** Real tile size x 1024 px/m, rounded up to 2K / 4K / 8K, accepting about 900 px/m. A 2 m tile
needs 2K; 2.1-4.5 m needs 4K; up to 9 m needs 8K. Mid/far sets (aerial scans of 15-90 m) are always 8K; they cover the
distance between the near sets and the macro colour (about 90-550 px/m).

---

## 1. Mountains spike: layer list

Order is bottom to top of the stack (RESEARCH-materials.md 4.1). Masks are our named attributes: lg_height,
lg_slope, lg_curvature, lg_flow, lg_wear, lg_deposit, lg_depth, lg_water; "facing" means read from the normal.

| # | Layer | Role | Masks that drive it | Procedural / texture | Maps | Target res / tile |
|---|---|---|---|---|---|---|
| L1 | Mountain rock (near) | Cliffs and steep faces, the base of the stack | lg_slope high, lg_curvature (ridges lighter) | Texture for detail (slot M1); procedural for colour variation, streaks down the face (lg_flow), box mapping on steep faces | colour, rough, normal, height | 4K over 2.7 m (1517 px/m) |
| L2 | Rock, mid/far | Rock read from 50-500 m, before the macro colour takes over | same as L1, distance blend | Texture (slot M2) + distance blend | colour, rough, normal, height | 8K over 90 m (91 px/m) |
| L3 | Scree / talus | Aprons under cliffs and in gullies, lighter than the cliff | lg_deposit, lg_wear, lg_slope mid (25-38 degrees), below steep rock | Texture (M3); procedural lightening and coarser toward the foot | colour, rough, normal, height | 4K over 3 m (1365 px/m) |
| L4 | Soil / bare ground | Eroded slopes, between turf and rock, paths | lg_wear, lg_flow, lg_slope mid | Texture (M4); procedural wet/dry value bands from lg_flow | colour, rough, normal, height | 2K over 2.07 m (989 px/m) |
| L5 | Grass ground (turf base) | Colour of the turf on flats and gentle slopes; meshes go on later | lg_slope low, lg_height below the snow line, facing | Texture (M5); procedural green/olive/straw patches, drier on crests (lg_curvature) | colour, rough, normal, height | 4K over 2.51 m (1631 px/m) |
| L6 | Sediment / valley gravel | Valley floors, stream beds, deposits | lg_deposit, lg_flow high | Texture (M8) | colour, rough, normal, height | 4K over 2.9 m (1412 px/m) |
| L7 | Moss / lichen on rock | Moss on rock tops and shaded wet faces; lichen tint on dry rock | lg_curvature (tops), facing (shade), lg_flow / lg_water (near water) | Texture (M7) for moss; lichen as a procedural tint only | colour, rough, normal, height | 4K over 3 m (1365 px/m) |
| L8 | Snow | Alpha layer on top: ledges, flats, lee sides; off steep faces | lg_height (Snow Line), lg_slope (Snow on Slopes, gone above about 50-60 degrees), facing | Texture (M6) near; procedural blue-in-shade tint, sparkle-free roughness | colour, rough, normal, height | 2K over 2 m (1024 px/m) |
| L9 | Wet edge | Darker, glossier band above water and in flow channels | lg_water, lg_depth, lg_flow | **Procedural only** (darken colour, lower roughness on the layers below) | none | n/a |
| L10 | Macro colour | Large-scale colour that the near sets fade into with distance | all masks + world position | **Procedural only** (climate palette, broad noise, colour along the drainage) | none (baked on export) | 1 sample per grid vertex |

Spike total: **10 layers, 8 texture slots** (M1-M8), 2 procedural-only layers.

## 2. Extra layers for the other 13 types and the 5 climates

| # | Layer | Used by | Role | Masks | Procedural / texture | Maps | Target res / tile |
|---|---|---|---|---|---|---|---|
| X1 | Sandstone | Canyon, Mesa, Badlands, Hero Butte; Arid | Banded cliff rock | lg_slope high, lg_height (bands follow our terraces) | Texture (E1) + **procedural height bands** (2-3 close colours, cross-bed lines in height) | colour, rough, normal, height | 2K over 2 m |
| X2 | Red / pitted arid rock | Canyon, Mesa, Badlands; Arid | Alcoves, pitted faces, varnish streaks | lg_curvature (hollows), lg_flow (streaks) | Texture (E2); procedural dark varnish streaks | colour, rough, normal, height | 2K over 1 m |
| X3 | Badlands clay | Badlands; Arid | Rills and banded clay slopes | lg_flow (rills), lg_height bands | Texture (E3) + procedural colour bands | colour, rough, normal, height | 2K over 2 m |
| X4 | Desert sand | Sand Dunes, deposits in Canyon and Mesa; Arid | Dune surface | lg_deposit, lg_slope low | Texture (E4) for grain; **procedural ripples** (wind direction, none on slip faces) | colour, rough, normal, height | 8K over 15 m (546 px/m); near ripples procedural |
| X5 | Arid cracked ground | Badlands, Mesa floors, Volcanic flats; Arid | Playas, dry flats | lg_slope low, lg_deposit, low lg_flow | Texture (E5) | colour, rough, normal, height | 4K over 4 m |
| X6 | Mud / silt | Riverbed, Seabed shallows, lake shores, cave floors (limestone silt) | Wet low ground | lg_deposit, lg_flow, lg_depth | Texture (E6); procedural gloss in hollows | colour, rough, normal, height | 2K over 1.3 m |
| X7 | Wet beach sand | Coastal Cliffs, Seabed | Shoreline band | lg_water, lg_depth, lg_slope low | Texture (E7) | colour, rough, normal, height | 2K over 1.87 m |
| X8 | Shingle / pebbles | Coastal Cliffs, Riverbed, Glacial Valley outwash, Seabed | Pebble beaches, bars | lg_deposit, lg_flow | Texture (E8) | colour, rough, normal, height | 2K over 2.16 m |
| X9 | Limestone | Coastal Cliffs, caves (Limestone), rock Kits | Pale grey cliff and cave rock; fine beds as height detail (D163) | lg_slope, lg_tube (caves) | Texture (E9) + procedural bed lines and solution grooves | colour, rough, normal, height | 8K over 6.8 m |
| X10 | Basalt / dark volcanic rock | Volcanic, Volcano, jointed caves, lava tubes, rock Kits | Near-black rock, sharp joints | lg_slope, lg_curvature | Texture (E10); **procedural columns/joints** | colour, rough, normal, height | 4K over 2.42 m |
| X11 | Lava rock (pahoehoe, aa, crust) | Volcanic, Volcano, lava tubes; Volcanic | Fresh flows: silver ropy skin or rubbly aa; crust (D184) | lg_flow, lg_curvature, type | **Procedural**; no Poly Haven set (gap) | colour, rough, normal, height (from procedural, or KB3D later) | 4K over 4 m if a set is authored |
| X12 | Glowing lava | Volcanic, Volcano | Emission only in cracks and flow fronts | lg_curvature (cracks), type | **Procedural only** (emission) | none | n/a |
| X13 | Volcanic ash / cinder | Volcanic, Volcano; Volcanic | Grey-black ash plains and cinder slopes | lg_slope low, lg_height | Texture (E11, lunar regolith as a stand-in) + procedural darkening | colour, rough, normal, height | 4K over 3.1 m |
| X14 | Lunar regolith | Cratered Surface | Moon ground | all | Texture (E12) | colour, rough, normal, height | 4K over 3.1 m |
| X15 | Glacier ice | Glacial Valley, ice caves; Alpine | Grey-white dirty ice, blue only in fresh breaks, debris bands | lg_flow (bands), lg_curvature | **Procedural**; no Poly Haven set (gap) | colour, rough, normal, height | 4K over 4 m if authored |
| X16 | Forest floor | Lush climate (all vegetated types) | Mossy litter ground under trees | lg_slope low, facing, lg_flow | Texture (E13) | colour, rough, normal, height | 4K over 3 m |
| X17 | Dry grass ground | Arid and Alpine climates | Straw-coloured turf base | as L5 | Texture (E14) | colour, rough, normal, height | 2K over 2 m |
| X18 | Granite slabs (domes, corestones) | Mountains, Glacial Valley, Rolling Hills outcrops; Alpine | Smooth pale slabs with few cracks | lg_slope, lg_curvature | Uses M1 alternates (Rock Face), procedural smoothing | as L1 | as L1 |

Climates mostly reuse these layers with a different palette and rules. What each climate swaps in:

| Climate | Ground / turf | Rock | Extra | Snow |
|---|---|---|---|---|
| Temperate | L5 grass ground | L1 | L7 moss | High peaks only |
| Arid | X17 dry grass, X5 cracked ground, X4 sand | X1 sandstone, X2 | Varnish streaks, no moss | None |
| Alpine | X17 dry grass (short alpine turf), L3 scree heavy | L1 / X18 granite | Lichen tint | Low snow line, L8 dominant, X15 ice |
| Volcanic | X13 ash / cinder | X10 basalt, X11 lava rock | X12 glow | Summits only |
| Lush | L5 (greener) + X16 forest floor | L1 with heavy L7 moss | Wetter: L9 wider | High peaks only |

Totals: **18 extra layers** (28 in all), **14 extra texture slots** (22 in all), 2 more procedural-only layers (lava
glow; and lava rock and glacier ice are procedural until KB3D authors them).

## 3. Texture slots and Poly Haven candidates

Source: Poly Haven public API, read-only GETs on 2026-11-06: https://api.polyhaven.com/assets?t=textures (869
texture sets) and https://api.polyhaven.com/files/<id> for each candidate. All Poly Haven assets are CC0. "Real
size" is Poly Haven's stated dimensions. Every candidate has 1K, 2K, 4K and 8K; the flag shows which also go to 16K.
"Res. for target" follows the resolution rule above. Fill **KB3D library match** with the KitBash material that
should replace the set in the final version.

**M1 Mountain rock (granite/gneiss cliff faces)**

| Pick | Poly Haven set | Real size | Resolutions (max) | Res. for target | px/m at that res | Why it fits | KB3D library match |
|---|---|---|---|---|---|---|---|
| Recommended | [Rock Face 03](https://polyhaven.com/a/rock_face_03) | 2.7 x 2.7 m | 1K, 2K, 4K, 8K, 16K **(8K, 16K)** | 4K | 1517 | grey cracked cliff face, weathered; neutral mountain rock | |
| Alt | [Rock Face](https://polyhaven.com/a/rock_face) | 2.38 x 2.38 m | 1K, 2K, 4K, 8K, 16K **(8K, 16K)** | 4K | 1721 | solid rock face, Namaqualand; broad smooth planes like granite slabs | |
| Alt | [Dark Rock 02](https://polyhaven.com/a/dark_rock_02) | 2 x 2 m | 1K, 2K, 4K, 8K **(8K)** | 2K | 1023 | dark fractured, stratified rock face; good for darker or wet rock | |

**M2 Rock, mid/far (aerial cliff and boulder field)**

| Pick | Poly Haven set | Real size | Resolutions (max) | Res. for target | px/m at that res | Why it fits | KB3D library match |
|---|---|---|---|---|---|---|---|
| Recommended | [Rocky Terrain 03](https://polyhaven.com/a/rocky_terrain_03) | 90 x 90 m | 1K, 2K, 4K, 8K **(8K)** | 8K | 91 | 90 m aerial of boulders and rock landforms: mid-distance detail before macro colour | |
| Alt | [Aerial Rocks 02](https://polyhaven.com/a/aerial_rocks_02) | 50 x 50 m | 1K, 2K, 4K, 8K **(8K)** | 8K | 163 | 50 m aerial rock face with moss | |
| Alt | [Aerial Rocks 04](https://polyhaven.com/a/aerial_rocks_04) | 80 x 80 m | 1K, 2K, 4K, 8K **(8K)** | 8K | 102 | 80 m aerial rough rock with moss and lichen | |

**M3 Scree / talus**

| Pick | Poly Haven set | Real size | Resolutions (max) | Res. for target | px/m at that res | Why it fits | KB3D library match |
|---|---|---|---|---|---|---|---|
| Recommended | [Rocks Ground 06](https://polyhaven.com/a/rocks_ground_06) | 3 x 3 m | 1K, 2K, 4K, 8K **(8K)** | 4K | 1365 | broken angular rock and gravel, 3 m: reads as scree | |
| Alt | [Rock Ground 02](https://polyhaven.com/a/rock_ground_02) | 3 x 3 m | 1K, 2K, 4K, 8K **(8K)** | 4K | 1365 | broken gravel ground with loose stones | |
| Alt | [Rocks Ground 09](https://polyhaven.com/a/rocks_ground_09) | 3 x 3 m | 1K, 2K, 4K, 8K **(8K)** | 4K | 1365 | broken rock, gravel and scattered pebbles | |

**M4 Soil / bare ground**

| Pick | Poly Haven set | Real size | Resolutions (max) | Res. for target | px/m at that res | Why it fits | KB3D library match |
|---|---|---|---|---|---|---|---|
| Recommended | [Dirt Floor](https://polyhaven.com/a/dirt_floor) | 2.07 x 2.07 m | 1K, 2K, 4K, 8K **(8K)** | 2K | 989 | brown forest dirt, uneven; neutral bare soil | |
| Alt | [Forest Ground 05](https://polyhaven.com/a/forest_ground_05) | 2 x 2 m | 1K, 2K, 4K, 8K, 16K **(8K, 16K)** | 2K | 1024 | compact soil with scattered rocks, 16K | |
| Alt | [Rocks Ground 05](https://polyhaven.com/a/rocks_ground_05) | 3 x 3 m | 1K, 2K, 4K, 8K **(8K)** | 4K | 1365 | rocky dry soil with pebbles: eroded slopes | |

**M5 Grass ground (turf base under later meshes)**

| Pick | Poly Haven set | Real size | Resolutions (max) | Res. for target | px/m at that res | Why it fits | KB3D library match |
|---|---|---|---|---|---|---|---|
| Recommended | [Grass Ground](https://polyhaven.com/a/grass_ground) | 2.51 x 2.51 m | 1K, 2K, 4K, 8K, 16K **(8K, 16K)** | 4K | 1631 | dry grass, dirt and roots: turf base that reads at a distance | |
| Alt | [Sparse Grass](https://polyhaven.com/a/sparse_grass) | 2 x 2 m | 1K, 2K, 4K, 8K **(8K)** | 2K | 1024 | sparse grass with roots and soil | |
| Alt | [Leafy Grass](https://polyhaven.com/a/leafy_grass) | 2 x 2 m | 1K, 2K, 4K, 8K **(8K)** | 2K | 1024 | green leafy ground cover | |

**M6 Snow**

| Pick | Poly Haven set | Real size | Resolutions (max) | Res. for target | px/m at that res | Why it fits | KB3D library match |
|---|---|---|---|---|---|---|---|
| Recommended | [Snow 02](https://polyhaven.com/a/snow_02) | 2 x 2 m | 1K, 2K, 4K, 8K **(8K)** | 2K | 1024 | smooth powdery snowfield, no footprints | |
| Alt | [Snow Field Aerial](https://polyhaven.com/a/snow_field_aerial) | 80 x 80 m | 1K, 2K, 4K, 8K **(8K)** | 8K | 102 | 80 m aerial snowfield with mud patches: mid/far | |
| Alt | [Snow 04](https://polyhaven.com/a/snow_04) | 4 x 4 m | 1K, 2K, 4K, 8K **(8K)** | 4K | 1024 | snow with mud showing through: melt edge | |

**M7 Moss / lichen on rock**

| Pick | Poly Haven set | Real size | Resolutions (max) | Res. for target | px/m at that res | Why it fits | KB3D library match |
|---|---|---|---|---|---|---|---|
| Recommended | [Mossy Rock](https://polyhaven.com/a/mossy_rock) | 3 x 3 m | 1K, 2K, 4K, 8K **(8K)** | 4K | 1365 | rock with moss patches | |
| Alt | [Lichen Rock](https://polyhaven.com/a/lichen_rock) | 2 x 2 m | 1K, 2K, 4K, 8K **(8K)** | 2K | 1024 | rock face with lichen and moss | |
| Alt | [Rock 3](https://polyhaven.com/a/rock_3) | 1.5 x 1.5 m | 1K, 2K, 4K, 8K **(8K)** | 2K | 1365 | grey seaside rock with mossy patches | |

**M8 Sediment / valley-floor gravel**

| Pick | Poly Haven set | Real size | Resolutions (max) | Res. for target | px/m at that res | Why it fits | KB3D library match |
|---|---|---|---|---|---|---|---|
| Recommended | [River Small Rocks](https://polyhaven.com/a/river_small_rocks) | 2.9 x 2.9 m | 1K, 2K, 4K, 8K, 16K **(8K, 16K)** | 4K | 1412 | small river stones and debris, 16K | |
| Alt | [Dry River Pebbles](https://polyhaven.com/a/dry_river_pebbles) | 2 x 2 m | 1K, 2K, 4K, 8K **(8K)** | 2K | 1023 | rounded river pebbles | |
| Alt | [Gravel Stones](https://polyhaven.com/a/gravel_stones) | 2 x 2 m | 1K, 2K, 4K, 8K, 16K **(8K, 16K)** | 2K | 1024 | grey gravel, 16K | |

**E1 Sandstone (Canyon, Mesa, Badlands, Hero Butte)**

| Pick | Poly Haven set | Real size | Resolutions (max) | Res. for target | px/m at that res | Why it fits | KB3D library match |
|---|---|---|---|---|---|---|---|
| Recommended | [Worn Rock Natural 01](https://polyhaven.com/a/worn_rock_natural_01) | 2 x 2 m | 1K, 2K, 4K, 8K **(8K)** | 2K | 1024 | weathered yellow sandstone face | |
| Alt | [Cliff Side](https://polyhaven.com/a/cliff_side) | 1.83 x 1.83 m | 1K, 2K, 4K, 8K, 16K **(8K, 16K)** | 2K | 1119 | orange eroded cliff rock, 16K | |
| Alt | [Rock 06](https://polyhaven.com/a/rock_06) | 1.5 x 1.5 m | 1K, 2K, 4K, 8K **(8K)** | 2K | 1365 | yellow striated cliff rock | |

**E2 Red/orange arid rock and pitted rock**

| Pick | Poly Haven set | Real size | Resolutions (max) | Res. for target | px/m at that res | Why it fits | KB3D library match |
|---|---|---|---|---|---|---|---|
| Recommended | [Rock Pitted Mossy](https://polyhaven.com/a/rock_pitted_mossy) | 1 x 1 m | 1K, 2K, 4K, 8K **(8K)** | 2K | 2048 | red pitted sandstone with moss: alcoves and wet faces | |
| Alt | [Rock Boulder Cracked](https://polyhaven.com/a/rock_boulder_cracked) | 1.39 x 1.39 m | 1K, 2K, 4K, 8K **(8K)** | 2K | 1473 | orange cracked boulder rock | |
| Alt | [Tiger Rock](https://polyhaven.com/a/tiger_rock) | 2.55 x 2.55 m | 1K, 2K, 4K, 8K, 16K **(8K, 16K)** | 4K | 1606 | banded weathered cliff boulder, 16K | |

**E3 Badlands clay / eroded soil**

| Pick | Poly Haven set | Real size | Resolutions (max) | Res. for target | px/m at that res | Why it fits | KB3D library match |
|---|---|---|---|---|---|---|---|
| Recommended | [Excavated Soil Wall](https://polyhaven.com/a/excavated_soil_wall) | 2 x 2 m | 1K, 2K, 4K, 8K, 16K **(8K, 16K)** | 2K | 1024 | dry cracked soil wall: exposed clay banks, 16K | |
| Alt | [Cracked Red Ground](https://polyhaven.com/a/cracked_red_ground) | 2 x 2 m | 1K, 2K, 4K, 8K **(8K)** | 2K | 1024 | dry red cracked ground | |
| Alt | [Red Mud Stones](https://polyhaven.com/a/red_mud_stones) | 1.5 x 1.5 m | 1K, 2K, 4K, 8K **(8K)** | 2K | 1365 | red compact soil with stones | |

**E4 Desert sand / dunes**

| Pick | Poly Haven set | Real size | Resolutions (max) | Res. for target | px/m at that res | Why it fits | KB3D library match |
|---|---|---|---|---|---|---|---|
| Recommended | [Aerial Sand](https://polyhaven.com/a/aerial_sand) | 15 x 15 m | 1K, 2K, 4K, 8K **(8K)** | 8K | 546 | 15 m aerial sand: dune-scale grain and ripples | |
| Alt | [Red Sand](https://polyhaven.com/a/red_sand) | 3 x 3 m | 1K, 2K, 4K, 8K **(8K)** | 4K | 1365 | red sand with tracks (Arid red dunes) | |
| Alt | [Dense Sand](https://polyhaven.com/a/dense_sand) | 1.8 x 1.8 m | 1K, 2K, 4K, 8K **(8K)** | 2K | 1137 | compact tan sand, close-up | |

**E5 Arid cracked ground / playa**

| Pick | Poly Haven set | Real size | Resolutions (max) | Res. for target | px/m at that res | Why it fits | KB3D library match |
|---|---|---|---|---|---|---|---|
| Recommended | [Dry Ground 01](https://polyhaven.com/a/dry_ground_01) | 4 x 4 m | 1K, 2K, 4K, 8K **(8K)** | 4K | 1024 | baked cracked desert ground, 4 m | |
| Alt | [Mud Cracked Dry Riverbed 002](https://polyhaven.com/a/mud_cracked_dry_riverbed_002) | 2 x 2 m | 1K, 2K, 4K, 8K **(8K)** | 2K | 1024 | dry riverbed mud cracks | |
| Alt | [Dry Ground Rocks](https://polyhaven.com/a/dry_ground_rocks) | 4 x 4 m | 1K, 2K, 4K, 8K **(8K)** | 4K | 1024 | cracked dry ground with stones | |

**E6 Mud / silt (Riverbed, Seabed shallows, lake shores, cave floors)**

| Pick | Poly Haven set | Real size | Resolutions (max) | Res. for target | px/m at that res | Why it fits | KB3D library match |
|---|---|---|---|---|---|---|---|
| Recommended | [Brown Mud 03](https://polyhaven.com/a/brown_mud_03) | 1.3 x 1.3 m | 1K, 2K, 4K, 8K **(8K)** | 2K | 1575 | wet brown mud, compact soil | |
| Alt | [Muddy Tracks](https://polyhaven.com/a/muddy_tracks) | 2.25 x 2.25 m | 1K, 2K, 4K, 8K **(8K)** | 2K | 910 | wet muddy surface (has tracks) | |
| Alt | [Rocks Ground 08](https://polyhaven.com/a/rocks_ground_08) | 3 x 3 m | 1K, 2K, 4K, 8K **(8K)** | 4K | 1365 | damp muddy ground with scattered rocks: cave floors | |

**E7 Wet beach sand / shore (Coastal Cliffs, Seabed)**

| Pick | Poly Haven set | Real size | Resolutions (max) | Res. for target | px/m at that res | Why it fits | KB3D library match |
|---|---|---|---|---|---|---|---|
| Recommended | [Damp Beach Sand 02](https://polyhaven.com/a/damp_beach_sand_02) | 1.87 x 1.87 m | 1K, 2K, 4K, 8K **(8K)** | 2K | 1095 | damp striated tidal sand | |
| Alt | [Damp Sand](https://polyhaven.com/a/damp_sand) | 2.04 x 2.04 m | 1K, 2K, 4K, 8K **(8K)** | 2K | 1003 | wet coarse sand | |
| Alt | [Low Tide Rocks](https://polyhaven.com/a/low_tide_rocks) | 2.17 x 2.17 m | 1K, 2K, 4K, 8K **(8K)** | 2K | 943 | wet ground with scattered rocks | |

**E8 Shingle / pebble beach**

| Pick | Poly Haven set | Real size | Resolutions (max) | Res. for target | px/m at that res | Why it fits | KB3D library match |
|---|---|---|---|---|---|---|---|
| Recommended | [Ganges River Pebbles](https://polyhaven.com/a/ganges_river_pebbles) | 2.16 x 2.16 m | 1K, 2K, 4K, 8K, 16K **(8K, 16K)** | 2K | 948 | scattered river pebbles, 16K | |
| Alt | [Coast Sand 03](https://polyhaven.com/a/coast_sand_03) | 3 x 3 m | 1K, 2K, 4K, 8K, 16K **(8K, 16K)** | 4K | 1365 | sand with pebbles and stones, 16K | |
| Alt | [Shell Floor 01](https://polyhaven.com/a/shell_floor_01) | 3 x 3 m | 1K, 2K, 4K, 8K **(8K)** | 4K | 1365 | broken shells (Seabed) | |

**E9 Limestone (Coastal Cliffs, caves, rock Kits)**

| Pick | Poly Haven set | Real size | Resolutions (max) | Res. for target | px/m at that res | Why it fits | KB3D library match |
|---|---|---|---|---|---|---|---|
| Recommended | [Marble Cliff 02](https://polyhaven.com/a/marble_cliff_02) | 6.8 x 6.8 m | 1K, 2K, 4K, 8K **(8K)** | 8K | 1204 | pale weathered sedimentary cliff rock, 6.8 m | |
| Alt | [Marble Cliff 03](https://polyhaven.com/a/marble_cliff_03) | 5.75 x 5.75 m | 1K, 2K, 4K, 8K **(8K)** | 8K | 1425 | craggy pale cliff rock, 5.7 m | |
| Alt | [Seaside Rock](https://polyhaven.com/a/seaside_rock) | 2 x 2 m | 1K, 2K, 4K, 8K **(8K)** | 2K | 1024 | coastal cliff rock face | |

**E10 Basalt / dark volcanic rock**

| Pick | Poly Haven set | Real size | Resolutions (max) | Res. for target | px/m at that res | Why it fits | KB3D library match |
|---|---|---|---|---|---|---|---|
| Recommended | [Dark Rock](https://polyhaven.com/a/dark_rock) | 2.42 x 2.42 m | 1K, 2K, 4K, 8K **(8K)** | 4K | 1691 | dark fissured craggy rock | |
| Alt | [Dark Rock 02](https://polyhaven.com/a/dark_rock_02) | 2 x 2 m | 1K, 2K, 4K, 8K **(8K)** | 2K | 1023 | dark stratified fractured rock | |

**E11 Volcanic ash / cinder ground (Volcanic, Volcano)**

| Pick | Poly Haven set | Real size | Resolutions (max) | Res. for target | px/m at that res | Why it fits | KB3D library match |
|---|---|---|---|---|---|---|---|
| Recommended | [Moon 01](https://polyhaven.com/a/moon_01) | 3.1 x 3.1 m | 1K, 2K, 4K, 8K, 16K **(8K, 16K)** | 4K | 1321 | grey coarse regolith: stand-in for ash and cinder plains | |
| Alt | [Moon 03](https://polyhaven.com/a/moon_03) | 3.2 x 3.2 m | 1K, 2K, 4K, 8K, 16K **(8K, 16K)** | 4K | 1280 | coarse regolith | |
| Alt | [Burned Ground 01](https://polyhaven.com/a/burned_ground_01) | 1 x 1 m | 1K, 2K, 4K, 8K **(8K)** | 2K | 2048 | burned ground with ash (has leaf litter) | |

**E12 Cratered Surface (lunar)**

| Pick | Poly Haven set | Real size | Resolutions (max) | Res. for target | px/m at that res | Why it fits | KB3D library match |
|---|---|---|---|---|---|---|---|
| Recommended | [Moon 02](https://polyhaven.com/a/moon_02) | 3.1 x 3.1 m | 1K, 2K, 4K, 8K, 16K **(8K, 16K)** | 4K | 1321 | lunar regolith | |
| Alt | [Moon Meteor 01](https://polyhaven.com/a/moon_meteor_01) | 3.2 x 3.2 m | 1K, 2K, 4K, 8K, 16K **(8K, 16K)** | 4K | 1280 | regolith with small craters | |
| Alt | [Moon 04](https://polyhaven.com/a/moon_04) | 3.2 x 3.2 m | 1K, 2K, 4K, 8K, 16K **(8K, 16K)** | 4K | 1280 | lunar regolith | |

**E13 Lush forest floor (Lush climate)**

| Pick | Poly Haven set | Real size | Resolutions (max) | Res. for target | px/m at that res | Why it fits | KB3D library match |
|---|---|---|---|---|---|---|---|
| Recommended | [Forest Leaves 02](https://polyhaven.com/a/forest_leaves_02) | 3 x 3 m | 1K, 2K, 4K, 8K **(8K)** | 4K | 1364 | mossy forest floor with leaves and twigs | |
| Alt | [Forest Ground 01](https://polyhaven.com/a/forrest_ground_01) | 2 x 2 m | 1K, 2K, 4K, 8K **(8K)** | 2K | 1024 | forest ground with grass and litter | |
| Alt | [Brown Mud Leaves 01](https://polyhaven.com/a/brown_mud_leaves_01) | 1.3 x 1.3 m | 1K, 2K, 4K, 8K **(8K)** | 2K | 1575 | mud, moss and leaves | |

**E14 Dry grass (Arid, Alpine climates)**

| Pick | Poly Haven set | Real size | Resolutions (max) | Res. for target | px/m at that res | Why it fits | KB3D library match |
|---|---|---|---|---|---|---|---|
| Recommended | [Withered Grass](https://polyhaven.com/a/withered_grass) | 2 x 2 m | 1K, 2K, 4K, 8K **(8K)** | 2K | 1024 | dried-up grass | |
| Alt | [Dry Decay Leaves](https://polyhaven.com/a/dry_decay_leaves) | 2 x 2 m | 1K, 2K, 4K, 8K, 16K **(8K, 16K)** | 2K | 1024 | dead grass and litter, 16K | |

### Slots where Poly Haven has nothing good
Searched names, tags and descriptions of all 869 sets for lava, basalt, volcanic, glacier, ice, frozen, silt,
scree, cinder, pumice, obsidian, limestone and granite (2026-11-06):
- **Lava rock (X11) and glacier ice (X15):** no sets at all ("volcanic" only matches man-made tiles). Procedural for
  the spike; KitBash would need to author them.
- **Basalt (E10):** no columnar or true basalt; Dark Rock is generic dark rock. Columns and joints stay procedural.
- **Limestone (E9):** no set is tagged limestone; the Marble Cliff scans are pale, weathered sedimentary-looking
  cliffs and are the closest stand-in.
- **Volcanic ash / cinder (E11):** no ash or cinder ground; lunar regolith is a stand-in in colour and grain.
- **Fine silt and tidal mudflat (E6):** only trodden or tracked mud; no clean glossy silt flat.
- **Dune ripples (E4):** sand sets are beach or trampled; dune-scale ripples stay procedural.
- **Scree (M3):** no set tagged scree; broken-rock ground sets are the stand-in.

## 4. Gap list for KitBash 3D

The final version uses only KB3D materials (D194). Every texture row above with an empty **KB3D library match**
cell is a material KitBash would need to author (or source) before release. From the Poly Haven search, the slots
most likely to stay empty because nobody offers them well are: **lava rock (pahoehoe, aa, crust), glacier ice,
basalt with joints, limestone with bed lines, volcanic ash and cinder, glossy silt / mudflat, scree** and **dune sand
with ripples**. Each needs, at minimum, colour, roughness, normal and a 16-bit height map, tileable, at about
1024 px/m (2K over 2 m or 4K over 4 m), plus a mid/far version for rock and snow if KB3D has no aerial scans.

## 5. Ground cover meshes (later, instanced)

For Mike to source against (placeholder or final). Not part of M7; listed so the material layers leave room for them.
- **Grass:** short turf clumps (Temperate), tall meadow grass, dry/straw grass (Arid, Alpine), tussock grass
  (Alpine, moorland), dune grass (Sand Dunes, Coastal), lush broad-leaf grass (Lush).
- **Flowers and small plants:** meadow flowers, alpine cushion plants, ferns (Lush, cave mouths), succulents and
  cacti (Arid), weeds for cracks.
- **Shrubs:** low alpine shrubs, sagebrush / desert scrub (Arid), heather / heath (moorland), lush bushes (Lush),
  pioneer plants on old lava (Volcanic).
- **Trees (later still):** conifers (Alpine), broadleaf (Temperate, Lush), sparse desert trees (Arid), dead trees.
- **Rocks:** pebbles, small rocks (5-30 cm), scree stones, boulders (we already have the cave rock Kits; landscape
  versions share the materials, Parking).
- **Dead wood and litter:** fallen branches, logs, stumps, leaf-litter patches.
- **Moss and lichen clumps:** cushion moss for rocks near water.
- **Shore and water edge:** reeds, kelp / seaweed piles (Coastal, Seabed), driftwood.
- **Snow and ice:** snow-covered rocks, small ice chunks (Glacial Valley).
- **Volcanic:** cinder chunks, lava bombs, sulphur crust patches.

## 6. Download plan (for approval; nothing downloaded)

Size per set = colour JPG + normal (GL) JPG + roughness JPG + height EXR, from the Poly Haven files API.

| Option | Sets | 2K | 4K | 8K | At target res (mixed 2K/4K/8K) |
|---|---|---|---|---|---|
| **A. Spike only** (recommended picks M1-M8) | 8 | 92 MB | 345 MB | 1.2 GB | **388 MB** |
| B. All recommended picks (M1-M8, E1-E14) | 22 | 239 MB | 890 MB | 3.1 GB | 875 MB |
| C. Every candidate (recommended + alternates) | 63 | 712 MB | 2.6 GB | 9.0 GB | n/a |

**Ask:** approve **A at target resolution (8 sets, about 390 MB)** for the M7 spike now; B when the spike moves to the
other types; C only if we want side-by-side comparisons. Files would go to
`E:\Projects\3D\Terrain Generator_Build\Materials\polyhaven\<id>\`, each with a `sources.json` (id, page, CC0, author,
resolution), and are never shipped (final version is KB3D only).

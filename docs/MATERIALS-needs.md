# M7 material needs list (2026-11-06)

What the M7 auto-material spike (Mountains) and the full set of 14 types and 5 climates need. Research, plus the
Poly Haven downloads Mike approved on 2026-11-06 (section 6). Built on RESEARCH-materials.md, its "Mike's answers", D194 and D195.

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

## 6. Download plan and what was downloaded

Size per texture set = colour JPG + normal (GL) JPG + roughness JPG + height EXR, from the Poly Haven files API.

| Option | Sets | 2K | 4K | 8K | At target res (mixed 2K/4K/8K) |
|---|---|---|---|---|---|
| A. Spike only (recommended picks M1-M8) | 8 | 92 MB | 345 MB | 1.2 GB | 388 MB |
| **B. All recommended picks (M1-M8, E1-E14)** | 22 | 239 MB | 890 MB | 3.1 GB | 875 MB; **596 MB with the 4K cap** |
| C. Every candidate (recommended + alternates) | 63 | 712 MB | 2.6 GB | 9.0 GB | n/a |
| **D. Ground-cover meshes for a Mountains demo** (section 7, "Demo" picks) | 15 models | 82 MB (1K) | 387 MB (4K) | n/a | **153 MB as glTF with 2K textures** |

**Approved and downloaded (Mike, 2026-11-06): B and D, no 8K, no alternates.**
- **4K cap:** every texture set was downloaded at its target resolution but never above 4K; 2K targets stayed 2K.
  Three sets were capped from 8K:
  - Rocky Terrain 03 (M2 rock mid/far, 90 m): 4K, about **46 px/m** (8K would have been 91).
  - Aerial Sand (E4 desert sand, 15 m): 4K, about **273 px/m** (8K would have been 546). Close dune detail now
    relies even more on procedural ripples.
  - Marble Cliff 02 (E9 limestone, 6.8 m): 4K, about **602 px/m** (8K would have been 1204), under the 1024 px/m
    near-ground target; fine for cliffs, soft at the closest camera.
- **Meshes:** glTF with 2K textures (Poly Haven's default; no model above 4K was taken).
- **Result:** 22 texture sets (596 MB) and 15 models (153 MB), **37 assets, 169 files, 748 MB** in all. Every file
  matched the size the API states; no failures.
- **Where:** `E:\Projects\3D\Terrain Generator_Build\Materials\polyhaven\<id>\` (texture sets) and
  `...\polyhaven\models\<id>\` (glTF, .bin and textures), each with a `sources.json` (id, name, page, license CC0,
  authors, files with URL and size, resolution, px/m, date). Full list: `...\polyhaven\manifest.json`.
- Nothing was opened or run. These are spike stand-ins only and are never shipped (final version is KB3D only).

## 7. Poly Haven ground-cover meshes

Source: Poly Haven public API, read-only, 2026-11-06: https://api.polyhaven.com/assets?t=models (521 models; 110
"nature") and https://api.polyhaven.com/files/<id> for each match. All CC0. "Bounding size" is Poly Haven's stated
dimensions in metres; several assets hold a row or cluster of variants, so the bounding box is larger than one plant.
Polycount is Poly Haven's figure for the whole asset; **no LODs are listed** for any of them. File sizes are the full
download (model plus textures). "Demo" marks the 15 picks for a Mountains demo (option D, downloaded).
**Mike may cover** marks grass and trees, which Mike likely has in his own library.

Counts: grass 4, flowers 8, ferns and small plants (incl. moss) 9, shrubs and bushes 10, trees 13, small rocks and
boulders 17, dead wood and roots 14, shoreline 3. **78 matches.**

**Grass and grass clumps** (4)

| Pick | Poly Haven model | What it is | Bounding size (m) | Polycount | glTF 1K / 2K / 4K (MB) | .blend 1K / 2K / 4K (MB) | Suits (types; climates) | Mike may cover |
|---|---|---|---|---|---|---|---|---|
| Demo | [Grass Medium 01](https://polyhaven.com/a/grass_medium_01) | meadow grass clumps (several variants) | 7.3 x 1.3 x 1.2 | 1,606,633 | 3.1 / 8.0 / 25.1 | 8.0 / 21.2 / 61.6 | Rolling Hills, Mountains valleys, Glacial Valley; Temperate, Lush | Yes |
| Demo | [Grass Medium 02](https://polyhaven.com/a/grass_medium_02) | short green meadow grass clumps | 3.6 x 1.4 x 1.4 | 1,043,926 | 0.8 / 1.8 / 4.7 | 2.0 / 5.9 / 53.4 | Rolling Hills, Mountains; Temperate, Lush, Alpine (short turf) | Yes |
|  | [Grass Bermuda 01](https://polyhaven.com/a/grass_bermuda_01) | low spreading Bermuda grass | 3.1 x 1.1 x 1.1 | 223,596 | 1.5 / 4.8 / 15.9 | 2.7 / 8.3 / 26.4 | Rolling Hills, Coastal tops, Riverbed banks; Temperate, Arid edges | Yes |
|  | [Flower Heliophila](https://polyhaven.com/a/flower_heliophila) | tiny white Karoo plant, grass-like | 2.8 x 1.4 x 0.4 | 324,914 | 3.8 / 6.7 / 15.6 | 8.2 / 12.7 / 26.7 | Arid flats; Arid | Yes |

**Flowers** (8)

| Pick | Poly Haven model | What it is | Bounding size (m) | Polycount | glTF 1K / 2K / 4K (MB) | .blend 1K / 2K / 4K (MB) | Suits (types; climates) | Mike may cover |
|---|---|---|---|---|---|---|---|---|
| Demo | [Dandelion 01](https://polyhaven.com/a/dandelion_01) | dandelion plants | 4.2 x 0.26 x 0.17 | 64,099 | 3.1 / 6.3 / 16.9 | 3.5 / 8.2 / 22.8 | Rolling Hills, Mountains meadows; Temperate, Alpine |  |
|  | [Celandine 01](https://polyhaven.com/a/celandine_01) | celandine flowering plants (several) | 3.5 x 0.93 x 0.93 | 1,746,764 | 1.5 / 4.1 / 12.6 | 2.7 / 7.1 / 20.0 | Rolling Hills, forest edges; Temperate, Lush |  |
|  | [Periwinkle Plant](https://polyhaven.com/a/periwinkle_plant) | small periwinkle flowering shrub | 1.2 x 0.33 x 0.41 | 67,388 | 2.9 / 5.1 / 12.1 | 10.0 / 29.1 / 79.6 | Rolling Hills; Temperate, Lush |  |
|  | [Flower Gazania](https://polyhaven.com/a/flower_gazania) | orange Karoo wildflower | 1.6 x 0.81 x 0.4 | 25,819 | 2.8 / 7.5 / 22.2 | 5.2 / 14.7 / 44.6 | Arid flats; Arid (spring bloom) |  |
|  | [Flower Ursinia](https://polyhaven.com/a/flower_ursinia) | orange Karoo wildflower | 2.2 x 0.34 x 0.17 | 44,360 | 2.1 / 5.0 / 14.8 | 4.3 / 11.1 / 32.1 | Arid; Arid |  |
|  | [Flower Empodium](https://polyhaven.com/a/flower_empodium) | yellow Karoo wildflower | 1.3 x 0.28 x 0.27 | 5,820 | 0.9 / 2.5 / 7.0 | 1.2 / 3.3 / 9.4 | Arid; Arid |  |
|  | [Flower Stinkkruid](https://polyhaven.com/a/flower_stinkkruid) | yellow Karoo wildflower | 1.7 x 0.3 x 0.18 | 103,778 | 4.8 / 7.9 / 18.3 | 4.9 / 9.8 / 26.3 | Arid; Arid |  |
|  | [Leipoldtia Schultzei](https://polyhaven.com/a/leipoldtia_schultzei) | purple flowering succulent | 2.3 x 0.81 x 0.32 | 654,080 | 13.1 / 14.7 / 19.3 | 15.0 / 17.7 / 24.8 | Arid; Arid |  |

**Ferns and small plants** (9)

| Pick | Poly Haven model | What it is | Bounding size (m) | Polycount | glTF 1K / 2K / 4K (MB) | .blend 1K / 2K / 4K (MB) | Suits (types; climates) | Mike may cover |
|---|---|---|---|---|---|---|---|---|
| Demo | [Fern 02](https://polyhaven.com/a/fern_02) | fern | 2 x 1.7 x 0.43 | 6,232 | 1.1 / 3.4 / 10.8 | 1.8 / 5.3 / 17.1 | Mountains forest, cave mouths, Riverbed; Lush, Temperate |  |
|  | [Nettle Plant](https://polyhaven.com/a/nettle_plant) | nettle | 1.1 x 0.095 x 0.22 | 46,195 | 2.5 / 6.1 / 18.1 | 7.1 / 20.7 / 62.3 | Rolling Hills, Riverbed; Temperate |  |
|  | [Weed Plant 02](https://polyhaven.com/a/weed_plant_02) | weed plant | 2.1 x 0.29 x 0.075 | 17,062 | 2.0 / 6.5 / 22.5 | 3.2 / 10.1 / 34.5 | cracks, paths; Temperate, Arid |  |
|  | [Shrub Sorrel 01](https://polyhaven.com/a/shrub_sorrel_01) | small sorrel plant | 0.35 x 0.15 x 0.058 | 3,319 | 1.2 / 3.7 / 11.9 | 2.1 / 6.7 / 20.7 | forest floor; Temperate, Lush |  |
| Demo | [Moss 01](https://polyhaven.com/a/moss_01) | moss clump | 0.84 x 0.3 x 0.3 | 246,170 | 0.9 / 3.3 / 11.6 | 1.9 / 6.1 / 21.3 | rocks near water, forest floor, cave mouths; Lush, Temperate |  |
|  | [Cheiridopsis Succulent](https://polyhaven.com/a/cheiridopsis_succulent) | small Karoo succulents | 2.2 x 0.96 x 0.27 | 198,888 | 4.3 / 8.9 / 23.6 | 8.0 / 17.1 / 42.5 | Arid flats, Badlands; Arid |  |
|  | [Crystalline Iceplant](https://polyhaven.com/a/crystalline_iceplant) | ice-plant succulent | 1.7 x 0.74 x 0.083 | 23,487 | 2.6 / 8.4 / 27.6 | 4.0 / 12.1 / 39.2 | Coastal, Arid; Arid |  |
|  | [Calathea Orbifolia 01](https://polyhaven.com/a/calathea_orbifolia_01) | broad-leaf tropical plant | 2.5 x 1.2 x 0.42 | 16,688 | 1.9 / 5.7 / 20.3 | 4.4 / 14.7 / 51.0 | Lush (tropical) only |  |
|  | [Anthurium Botany 01](https://polyhaven.com/a/anthurium_botany_01) | broad-leaf tropical plant | 2.8 x 1.8 x 0.51 | 4,134 | 3.2 / 7.1 / 20.9 | 3.6 / 12.3 / 41.5 | Lush (tropical) only |  |

**Shrubs and bushes** (10)

| Pick | Poly Haven model | What it is | Bounding size (m) | Polycount | glTF 1K / 2K / 4K (MB) | .blend 1K / 2K / 4K (MB) | Suits (types; climates) | Mike may cover |
|---|---|---|---|---|---|---|---|---|
| Demo | [Shrub 02](https://polyhaven.com/a/shrub_02) | leafy sapling-shrub | 5.3 x 2.1 x 2.1 | 52,317 | 2.0 / 4.8 / 14.1 | 2.9 / 7.2 / 20.2 | Mountains valleys, Rolling Hills; Temperate, Lush |  |
| Demo | [Shrub 04](https://polyhaven.com/a/shrub_04) | small green shrub | 0.75 x 0.19 x 0.28 | 47,813 | 1.9 / 4.4 / 12.2 | 3.2 / 6.7 / 17.2 | Mountains, Rolling Hills; Temperate, Alpine |  |
|  | [Shrub 01](https://polyhaven.com/a/shrub_01) | leafy ground shrub with flowers | 2.6 x 0.22 x 0.4 | 282,224 | 6.9 / 10.8 / 23.8 | 10.1 / 18.2 / 43.5 | Rolling Hills; Temperate, Lush |  |
|  | [Shrub 03](https://polyhaven.com/a/shrub_03) | small meadow shrub | 1.4 x 0.15 x 0.4 | 16,955 | 1.6 / 4.5 / 13.2 | 2.2 / 5.9 / 15.7 | Rolling Hills, Mountains; Temperate |  |
|  | [Wild Rooibos Bush](https://polyhaven.com/a/wild_rooibos_bush) | dry Karoo shrub | 2.3 x 0.85 x 0.54 | 76,521 | 2.5 / 6.0 / 19.9 | 4.3 / 9.0 / 27.3 | Arid, Badlands, Mesa; Arid |  |
|  | [Didelta Spinosa](https://polyhaven.com/a/didelta_spinosa) | green desert shrub | 2.1 x 4.6 x 2.1 | 694,671 | 14.8 / 17.0 / 23.7 | 17.6 / 23.6 / 38.6 | Arid; Arid |  |
|  | [Searsia Lucida](https://polyhaven.com/a/searsia_lucida) | dry Karoo bush | 4.8 x 2.8 x 2.3 | 841,648 | 19.8 / 24.8 / 43.3 | 23.3 / 30.5 / 56.7 | Arid; Arid |  |
|  | [Searsia Burchellii](https://polyhaven.com/a/searsia_burchellii) | large dry Karoo bush | 8.4 x 5.1 x 3.2 | 1,427,042 | 34.6 / 38.4 / 53.1 | 45.5 / 50.2 / 68.4 | Arid; Arid |  |
|  | [Othonna Cerarioides](https://polyhaven.com/a/othonna_cerarioides) | succulent bush | 4 x 1.8 x 2 | 651,641 | 7.9 / 14.1 / 37.2 | 23.5 / 32.4 / 66.2 | Arid; Arid |  |
|  | [Pachira Aquatica 01](https://polyhaven.com/a/pachira_aquatica_01) | tropical shrub | 6.9 x 1 x 1.9 | 76,914 | 5.1 / 12.4 / 36.3 | 17.2 / 51.3 / 155.5 | Lush (tropical) only |  |

**Trees (Mike may cover)** (13)

| Pick | Poly Haven model | What it is | Bounding size (m) | Polycount | glTF 1K / 2K / 4K (MB) | .blend 1K / 2K / 4K (MB) | Suits (types; climates) | Mike may cover |
|---|---|---|---|---|---|---|---|---|
| Demo | [Fir Sapling](https://polyhaven.com/a/fir_sapling) | small fir sapling | 2.7 x 0.83 x 1.3 | 433,021 | 25.4 / 34.6 / 61.1 | 30.9 / 80.0 / 252.4 | Mountains, Glacial Valley; Alpine, Temperate | Yes |
| Demo | [Pine Sapling Small](https://polyhaven.com/a/pine_sapling_small) | small pine sapling | 2.6 x 0.77 x 1.3 | 398,144 | 21.9 / 32.2 / 63.4 | 33.5 / 90.0 / 290.1 | Mountains; Alpine, Temperate | Yes |
|  | [Fir Tree 01](https://polyhaven.com/a/fir_tree_01) | full fir tree (geometry nodes) | 27 x 6.5 x 19 | 7,853,731 | 487.4 / 510.2 / 583.8 | 274.8 / 425.7 / 956.6 | Mountains, Glacial Valley; Alpine, Temperate | Yes |
|  | [Pine Tree 01](https://polyhaven.com/a/pine_tree_01) | full pine tree (geometry nodes) | 27 x 1.3 x 18 | 17,427,094 | 958.1 / 982.1 / 1060.3 | 627.1 / 777.4 / 1309.4 | Mountains; Alpine, Temperate | Yes |
|  | [Fir Sapling Medium](https://polyhaven.com/a/fir_sapling_medium) | medium fir | 26 x 5.4 x 9.2 | 2,308,249 | 78.1 / 87.5 / 115.3 | 63.1 / 120.2 / 322.8 | Mountains; Alpine | Yes |
|  | [Pine Sapling Medium](https://polyhaven.com/a/pine_sapling_medium) | medium pine | 23 x 5.5 x 12 | 9,784,670 | 267.8 / 278.6 / 311.5 | 223.8 / 284.9 / 503.6 | Mountains; Alpine | Yes |
|  | [Tree Small 02](https://polyhaven.com/a/tree_small_02) | small broadleaf tree | 2.9 x 4.3 x 4.6 | 4,652,585 | 101.0 / 115.3 / 160.9 | 84.1 / 129.1 / 263.0 | Rolling Hills; Temperate, Lush | Yes |
|  | [Island Tree 01](https://polyhaven.com/a/island_tree_01) | broadleaf tree | 12 x 4.8 x 5 | 3,729,692 | 66.3 / 79.8 / 124.5 | 79.9 / 138.0 / 338.5 | Rolling Hills, Coastal; Temperate, Lush | Yes |
|  | [Island Tree 02](https://polyhaven.com/a/island_tree_02) | broadleaf tree | 8.5 x 4.1 x 3.4 | 1,762,064 | 46.2 / 59.2 / 101.3 | 60.6 / 118.1 / 314.8 | Rolling Hills; Temperate, Lush | Yes |
|  | [Island Tree 03](https://polyhaven.com/a/island_tree_03) | broadleaf tree | 8.5 x 2.9 x 2.6 | 4,760,490 | 84.9 / 97.6 / 139.6 | 94.3 / 151.5 / 347.7 | Rolling Hills; Temperate, Lush | Yes |
|  | [Jacaranda Tree](https://polyhaven.com/a/jacaranda_tree) | jacaranda tree | 24 x 18 x 20 | 312,356 | 214.6 / 229.6 / 277.6 | 213.2 / 300.0 / 584.5 | Lush, warm Temperate | Yes |
|  | [Quiver Tree 01](https://polyhaven.com/a/quiver_tree_01) | quiver tree (aloe) | 1.2 x 0.97 x 2.7 | 269,522 | 8.9 / 21.6 / 69.0 | 31.8 / 94.9 / 312.9 | Arid | Yes |
|  | [Quiver Tree 02](https://polyhaven.com/a/quiver_tree_02) | small quiver tree | 0.87 x 0.88 x 1.5 | 153,887 | 4.5 / 11.1 / 35.7 | 9.0 / 18.0 / 51.6 | Arid | Yes |

**Small rocks, pebbles and boulders** (17)

| Pick | Poly Haven model | What it is | Bounding size (m) | Polycount | glTF 1K / 2K / 4K (MB) | .blend 1K / 2K / 4K (MB) | Suits (types; climates) | Mike may cover |
|---|---|---|---|---|---|---|---|---|
| Demo | [Rock Moss Set 01](https://polyhaven.com/a/rock_moss_set_01) | set of mossy rocks and pebbles | 8 x 6.9 x 1.8 | 63,127 | 1.9 / 3.3 / 8.2 | 4.5 / 10.5 / 34.4 | Mountains, Rolling Hills, Riverbed; Temperate, Lush, Alpine |  |
| Demo | [Rock Moss Set 02](https://polyhaven.com/a/rock_moss_set_02) | set of mossy rocks and pebbles | 8.3 x 3.4 x 1.4 | 57,647 | 1.9 / 3.6 / 9.5 | 4.7 / 11.4 / 37.2 | Mountains, Riverbed; Temperate, Lush, Alpine |  |
| Demo | [Boulder 01](https://polyhaven.com/a/boulder_01) | lichen-covered boulder | 1.3 x 1.8 x 1 | 123,976 | 5.8 / 13.5 / 43.2 | 9.3 / 20.3 / 63.3 | Mountains, Glacial Valley (erratics), Rolling Hills; all but Volcanic |  |
|  | [Rock 07](https://polyhaven.com/a/rock_07) | small weathered rock | 0.17 x 0.32 x 0.14 | 27,830 | 2.2 / 6.3 / 20.4 | 3.7 / 10.6 / 34.2 | everywhere |  |
|  | [Rock 09](https://polyhaven.com/a/rock_09) | pebble-size rock | 0.074 x 0.14 x 0.033 | 23,280 | 2.0 / 5.8 / 17.5 | 3.5 / 9.9 / 28.1 | everywhere |  |
|  | [Stone 01](https://polyhaven.com/a/stone_01) | small quartz stone | 0.15 x 0.089 x 0.072 | 71,916 | 3.7 / 10.1 / 31.4 | 8.4 / 23.1 / 74.1 | everywhere |  |
|  | [Namaqualand Boulder 02](https://polyhaven.com/a/namaqualand_boulder_02) | brown desert boulder | 2.5 x 1.2 x 0.88 | 183,681 | 5.1 / 13.0 / 42.9 | 10.4 / 21.0 / 61.8 | Arid, Mesa, Badlands; Arid |  |
|  | [Namaqualand Boulder 03](https://polyhaven.com/a/namaqualand_boulder_03) | brown desert boulder | 2.4 x 3.1 x 1.5 | 121,546 | 3.8 / 10.2 / 34.0 | 7.4 / 15.8 / 45.0 | Arid; Arid |  |
|  | [Namaqualand Boulder 04](https://polyhaven.com/a/namaqualand_boulder_04) | brown desert boulder | 2.5 x 2.5 x 1.9 | 110,746 | 3.7 / 10.1 / 32.5 | 7.1 / 15.5 / 43.5 | Arid; Arid |  |
|  | [Namaqualand Boulder 05](https://polyhaven.com/a/namaqualand_boulder_05) | brown desert boulder | 1.4 x 0.75 x 0.54 | 117,622 | 4.7 / 11.9 / 37.6 | 7.5 / 16.9 / 49.5 | Arid; Arid |  |
|  | [Namaqualand Boulder 06](https://polyhaven.com/a/namaqualand_boulder_06) | brown desert boulder | 0.68 x 1.2 x 0.65 | 204,584 | 5.3 / 13.2 / 43.7 | 11.1 / 22.0 / 64.1 | Arid; Arid |  |
|  | [Namaqualand Boulders 01](https://polyhaven.com/a/namaqualand_boulders_01) | small desert boulders | 1.1 x 0.59 x 0.25 | 76,590 | 3.6 / 10.5 / 33.0 | 6.3 / 15.5 / 45.2 | Arid; Arid |  |
|  | [Namaqualand Rocks 01](https://polyhaven.com/a/namaqualand_rocks_01) | quartz stones | 1.4 x 0.22 x 0.15 | 160,716 | 4.8 / 12.1 / 36.5 | 10.1 / 22.4 / 64.3 | Arid; Arid |  |
|  | [Namaqualand Stones 01](https://polyhaven.com/a/namaqualand_stones_01) | quartz pebbles | 1 x 0.11 x 0.084 | 106,602 | 4.2 / 10.7 / 32.7 | 7.5 / 18.4 / 55.1 | Arid; Arid |  |
|  | [Moon Rock 01](https://polyhaven.com/a/moon_rock_01) | small lunar rock | 0.21 x 0.11 x 0.075 | 18,668 | 1.7 / 4.7 / 14.5 | 4.4 / 13.9 / 45.5 | Cratered Surface; Volcanic (cinder stand-in) |  |
|  | [Moon Rock 02](https://polyhaven.com/a/moon_rock_02) | small lunar rock | 0.25 x 0.25 x 0.2 | 6,194 | 1.5 / 5.2 / 17.3 | 2.7 / 8.8 / 28.8 | Cratered Surface |  |
|  | [Moon Rock 03](https://polyhaven.com/a/moon_rock_03) | small lunar rock | 0.11 x 0.086 x 0.058 | 10,492 | 1.5 / 4.9 / 16.6 | 4.2 / 14.1 / 48.4 | Cratered Surface |  |

**Dead wood, logs, stumps, branches, roots** (14)

| Pick | Poly Haven model | What it is | Bounding size (m) | Polycount | glTF 1K / 2K / 4K (MB) | .blend 1K / 2K / 4K (MB) | Suits (types; climates) | Mike may cover |
|---|---|---|---|---|---|---|---|---|
| Demo | [Dead Tree Trunk](https://polyhaven.com/a/dead_tree_trunk) | fallen dead log | 3.1 x 0.28 x 0.29 | 101,802 | 4.8 / 11.3 / 32.3 | 8.8 / 19.3 / 51.5 | Mountains forests, Rolling Hills; Temperate, Alpine, Lush |  |
| Demo | [Tree Stump 01](https://polyhaven.com/a/tree_stump_01) | tree stump | 1.4 x 1.6 x 0.57 | 41,046 | 3.9 / 11.4 / 34.8 | 6.5 / 17.6 / 54.0 | Mountains forests; Temperate, Alpine |  |
| Demo | [Dry Branches Medium 01](https://polyhaven.com/a/dry_branches_medium_01) | dry fallen branches | 1.1 x 1.3 x 0.34 | 16,803 | 3.3 / 10.8 / 38.9 | 5.0 / 16.6 / 58.9 | Mountains, Rolling Hills; all but Volcanic |  |
|  | [Dead Tree Trunk 02](https://polyhaven.com/a/dead_tree_trunk_02) | large dead trunk | 4.1 x 1.1 x 1.1 | 155,864 | 4.9 / 13.4 / 46.2 | 9.6 / 20.8 / 64.3 | Mountains, Riverbed; Temperate, Alpine |  |
|  | [Tree Stump 02](https://polyhaven.com/a/tree_stump_02) | tree stump | 1.5 x 1.4 x 0.52 | 62,345 | 4.5 / 13.0 / 43.3 | 7.5 / 20.5 / 66.9 | Mountains forests; Temperate, Alpine |  |
|  | [Pine Roots](https://polyhaven.com/a/pine_roots) | pine roots with needles | 1.8 x 1.9 x 0.15 | 162,693 | 9.7 / 26.7 / 87.0 | 34.0 / 105.4 / 354.6 | Mountains forests; Alpine, Temperate |  |
|  | [Root Cluster 01](https://polyhaven.com/a/root_cluster_01) | exposed root cluster | 4.1 x 2.7 x 1.5 | 225,261 | 9.5 / 18.2 / 51.5 | 13.8 / 25.5 / 70.5 | Riverbed banks, forest; Lush, Temperate |  |
|  | [Root Cluster 02](https://polyhaven.com/a/root_cluster_02) | flat root mat | 2.4 x 2.7 x 0.2 | 339,641 | 14.0 / 20.1 / 42.8 | 16.3 / 24.7 / 55.5 | forest floor; Lush, Temperate |  |
|  | [Single Root](https://polyhaven.com/a/single_root) | single surface root | 0.56 x 1.8 x 0.18 | 114,424 | 3.8 / 9.3 / 28.4 | 7.3 / 14.7 / 40.5 | forest floor |  |
|  | [Bark Debris 01](https://polyhaven.com/a/bark_debris_01) | dead bark and sticks | 1.2 x 0.67 x 0.11 | 362,632 | 8.1 / 16.7 / 46.9 | 16.6 / 27.7 / 66.4 | Arid; Arid |  |
|  | [Dead Quiver Branch 01](https://polyhaven.com/a/dead_quiver_branch_01) | dried desert branch | 0.25 x 0.23 x 0.44 | 14,834 | 2.7 / 8.9 / 30.3 | 4.0 / 13.0 / 44.6 | Arid; Arid |  |
|  | [Dead Quiver Branch 02](https://polyhaven.com/a/dead_quiver_branch_02) | dried desert branch | 0.29 x 0.2 x 0.53 | 14,386 | 2.2 / 6.4 / 19.4 | 3.1 / 8.8 / 24.8 | Arid; Arid |  |
|  | [Dead Quiver Trunk](https://polyhaven.com/a/dead_quiver_trunk) | dead desert trunk / log | 0.31 x 0.27 x 2 | 33,706 | 2.3 / 7.3 / 26.0 | 3.6 / 10.2 / 34.4 | Arid; Arid |  |
|  | [Dry Quiver Leaf](https://polyhaven.com/a/dry_quiver_leaf) | dried desert leaf debris | 0.4 x 0.19 x 0.43 | 147,596 | 4.5 / 11.3 / 35.5 | 9.1 / 18.3 / 51.1 | Arid; Arid |  |

**Shoreline** (3)

| Pick | Poly Haven model | What it is | Bounding size (m) | Polycount | glTF 1K / 2K / 4K (MB) | .blend 1K / 2K / 4K (MB) | Suits (types; climates) | Mike may cover |
|---|---|---|---|---|---|---|---|---|
|  | [Sand Rocks Small 01](https://polyhaven.com/a/sand_rocks_small_01) | sand with small rocks and pebbles patch | 4.6 x 3.9 x 0.54 | 1,386,500 | 23.8 / 31.0 / 55.8 | 53.7 / 65.0 / 103.2 | Coastal Cliffs, Riverbed, Seabed |  |
|  | [Coast Rocks 05](https://polyhaven.com/a/coast_rocks_05) | coastal rock cluster, 3 m | 3 x 2.8 x 1 | 1,446,981 | 25.3 / 33.6 / 62.2 | 55.7 / 67.6 / 109.7 | Coastal Cliffs, Seabed |  |
|  | [Lambis Shell](https://polyhaven.com/a/lambis_shell) | conch shell | 0.14 x 0.075 x 0.047 | 12,498 | 2.2 / 6.1 / 20.2 | 3.4 / 9.0 / 28.9 | Coastal, Seabed beaches |  |

### Best picks for a Mountains demo (downloaded, option D)
Grass Medium 01 and 02 (meadow clumps), Dandelion 01 (meadow flowers), Fern 02 and Moss 01 (shade, near water),
Shrub 02 and Shrub 04, Fir Sapling and Pine Sapling Small (tree line; Mike may cover), Rock Moss Set 01 and 02
(pebbles and small rocks), Boulder 01 (erratics), Dead Tree Trunk, Tree Stump 01 and Dry Branches Medium 01.

### Gaps (what Poly Haven lacks)
- **Alpine:** no cushion plants, no low alpine shrubs or heather, no tussock grass; the Karoo set is desert only.
- **Dry/straw grass and dune grass:** only green meadow grass and Bermuda grass.
- **Lush:** a few tropical broad-leaf plants, but no lush temperate undergrowth beyond ferns and nettles.
- **Cacti:** none outdoors (only a potted cactus); the Arid set is South African succulents and Karoo shrubs.
- **Trees:** the full fir and pine trees are very heavy (7.9M and 17.4M polys, 0.5-1 GB as glTF) and have no LODs.
- **Shoreline:** no reeds, kelp or seaweed piles, no driftwood; only a sand-and-pebble patch, a coastal rock
  cluster and a shell.
- **Snow and ice:** no snow-covered rocks, no ice chunks.
- **Volcanic:** no cinder chunks, lava bombs or sulphur crust; lunar rocks are the only stand-in.
- **Scree-sized rocks:** only a few loose rocks (Rock 07, Rock 09, Stone 01) and the two mossy rock sets; no
  dedicated scree stone set.
- **No LODs anywhere,** so dense scatter needs our own decimation or Blender's instancing display limits.

**Normal maps as PNG (Mike, 2026-11-06):** every texture set's normal map was also downloaded as PNG at the same resolution (22 files, 1.18 GB), so close-up lighting shows no JPG blocks or banding. Use the `*_nor_gl_*.png`; the JPGs stay as backups. Colour and roughness stay JPG, height EXR.

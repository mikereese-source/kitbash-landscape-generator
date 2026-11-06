# Landscape materials research for M7 (2026-11-06)

Research for the M7 auto-material. It extends RESEARCH.md, RESEARCH-terrainforge.md and RESEARCH-procedural-terrains.md
and does not repeat them. **Inspiration only (D49):** no code, shaders, node trees, presets, textures or art were copied.
Every fact below is cited with the URL of a page that was opened. Section 6 lists what could not be verified.

Boards: `docs/m7/c154` to `c167` (one per surface, 5 to 7 real photos each, with one line on what makes each read as
real). Photos: `E:\Projects\3D\Terrain Generator_Build\Terrain References\materials-<surface>\`, each with a
`sources.json` (file, title, page, license, artist). All photos are Wikimedia Commons with free licences.

---

## 0. Conclusions first

1. **Everyone builds terrain materials the same way:** a short stack of layers (rock, debris, soil, grass, sand,
   snow), each placed by a mask rule (height, slope, curvature, flow, deposits). Our seven masks already cover every
   input the leaders use. What we lack is the layer stack, the blend and the controls on top.
2. **The blend is what sells realism, not the textures.** Height-based blending (sand settles in the cracks first,
   rock tops stay clean) is standard in Unreal (LB Height Blend) and World Creator. Plain linear fades read as
   "painted on". Every rule needs a Transition Width.
3. **Gaea's lesson: colour from terrain data beats colour from noise.** Its docs say colour driven by data maps looks
   more believable than slope plus Perlin noise. Gaea 3 also moves colour with the sediment flow (ColorErosion).
   We have the erosion masks, so we can do this cheaply in the shader with lg_flow and lg_wear.
4. **Close detail tiles; far detail is a colour map.** Engines and add-ons all pair a tiling detail set (with
   anti-tiling) with a large-scale colour variation, and blend between them with camera distance. One baked map
   cannot hold both: a 1 km landscape baked at 8K is only 8 px/m.
5. **For engines, materials ship as weight maps plus tiling texture sets, not as baked colour.** Unreal adds one
   RGBA weightmap per 4 paint layers; Gaea, World Creator and Procedural Terrains all export splat maps. TerrainForge
   lands 8 paint layers in Unreal. This decides our export format.

**Quality-bar headline (boards c154-c167):** real surfaces read as real because of how they *meet* each other, not
their grain. Snow sits on ledges and slides off faces steeper than about 50-60 degrees; scree is lighter than the cliff
above it with ragged lobed edges; soil and mud change value with wetness; wet bands sit at every water line; moss
caps tops and shaded wet faces. Almost every one of these is a mask rule plus a height-blended edge, which suits our
masks exactly.

---

## 1. Competitor teardown

### Summary table

| | Gaea (QuadSpinner) | World Creator | Houdini heightfields | Unreal landscape material | TerrainForge (UE plugin, preview) | Blender add-ons (Superhive) |
|---|---|---|---|---|---|---|
| **Layer model** | Colour graph: gradients (CLUTs) mapped onto grey masks, combined in a layer-based Mixer [G1][G6] | Bottom-up material layers, each masked by the Distribution system [W1] | Named layers on the heightfield; MaterialX Mix chains, one mix per layer and per channel [H2] | Landscape Layer Blend node, one input per paint layer [U1] | 8 Unreal paint layers [TF] | Procedural Terrain 2.0: up to 6 layers set by min/max height [B2]; True Terrain: presets, no detail published [B1] |
| **Masks that drive layers** | Data maps: height, slope, angle, curvature, soil, flow, occlusion, Texture, SurfTex [G1][G4][G5] | Height, slope, angle, flow and more (search snippet only, see 6) | Mask by Feature: slope, height, curvature, direction, occlusion; Erode layers: sediment, debris, flow, flowdir [H1][H3] | Painted weights; slope/height logic built by hand in the graph [U1] | Our-style masks exported to PCG [TF] | Height only (Procedural Terrain 2.0) [B2] |
| **Blending** | Combine/Mixer with masks; Soil maps combined with Max [G4][G6] | Height Blending with a displacement texture [W1 snippet] | MtlX Mix with a 0-1 layer as the mix [H2] | LB Weight, LB Alpha, LB Height (height map adds detail at the transition) [U1] | Unreal's | Sharp or smooth min/max fades [B2] |
| **Triplanar** | n/a (2D colour maps) | Triplanar shader option, not exportable [W1 snippet] | Triplanar or Hexagonal Tiling Triplanar (random scale/rotation) recommended for steep slopes [H2] | Manual; community packs make steep faces triplanar [U3][U4] | Unknown | Not stated |
| **Tiling breakup** | n/a | Stochastic sampling, bakeable to the colour map [W1 snippet] | Hexagonal tiling with random scale and rotation [H2] | Community: cell bombing, variation masks [U3][U4] | Unknown | Not stated |
| **Macro / distance** | Whole map is macro colour | Gradients per material [W1 snippet] | n/a | Distance blend near/far is common in packs (End Fade Distance, Fade Length) [U3][U4]; RVT caches landscape shading [U2] | Unknown | Camera-driven LOD (geometry) only [B2] |
| **Snow / sediment / wet** | Snow, Snowfield, Glacier, Dusting sims; Soil, Debris sims; water Depth for colour [G7] | Snow, sand, debris, water sims (WC4) [W2] | Debris and sediment from Erode [H3] | Snow layers in packs; wetness not standard [U3][U4] | Unknown | Not stated |
| **Exports** | Splat node packs masks into RGB(A) [G3]; colour maps | Colour map from all splat layers (snippet) | Layers export as images; forum warns about RGBA premultiply (not verified) | Weightmap per 4 layers [U1] | 8 paint layers, PCG masks [TF] | None stated |
| **What the artist sees** | Gradient pickers, a SatMap library of hundreds of real colour gradients by category (Rocky, Sandy, Green...) [G2]; Mixer 3.0 shows all colour layers in one place [G6] | Material list with distributions; presets save whole biomes (snippet) | Node parameters, ramps per feature [H1] | Paint layers in the Landscape tool [U1] | Presets, agent tools | A single assigned material to edit [B2] |

Source keys are in section 7.

### Short notes per tool

**Gaea.** Colour is a gradient mapped onto any grey mask: "the lowest part of a gradient corresponds to the lowest
part of the terrain" [G1]. SatMaps are hundreds of gradients "extracted from satellite data", picked from a library
with a Random button [G2]; Synth turns any photo into such a gradient [G5]. The Texture data map mixes slope, soil
and "chaos" into one ready texturing mask [G4]. Soil maps simulate dust settling in crevices; combine several with
Max [G4]. Gaea 3 adds Mixer 3.0 (colour generators inside one layer node, under 1 GB instead of 3.8 GB for a
15-node setup), sand simulation and, under Gaea 2 features, **ColorErosion**: it "moves" a colour map "with the
physics of sedimentation" [G6][G7]. Gaea's colour is a baked 2D map, so close-up detail is left to the engine.

**World Creator.** WC4 (Early Access) lists "a new material system" and simulation "organized by substance" (water,
sand, snow, debris) and is now node based [W2]. The old docs (materials, distributions, export) now redirect to the
product page, so the details in the table come from search snippets only (see 6).

**Houdini.** HeightField Mask by Feature isolates slope, height, curvature, facing direction and occlusion, each
with its own ramp; several criteria intersect; masks can be smoothed and combined (Add, Multiply, Max, Blend...) [H1].
HeightField Erode writes sediment (hydro deposits), debris (thermal deposits), flow and flowdir, and its thermal
step uses a Cut Angle and a Repose Angle [H3]. The texturing guide chains MtlX Mix nodes, one layer per mix, and
reads layers by name with a Geometry Property Value node, which is exactly our named-attribute approach [H2]. It
recommends triplanar or hexagonal tiling to fix stretching on steep slopes and seams on large terrains [H2].

**Unreal.** Three blend types: Weight (order-free), Alpha (painted on top, e.g. snow), Height ("dirt appears in
the gaps between rocks at the layer transition point") [U1]. Warning from Epic: when every layer is LB Height
Blend, black spots can appear where all heights are 0; fix it by making one layer (Soil in their example) an Alpha
blend [U1]. Each 4 paint layers add one RGBA8 weightmap; mobile has a hard 16-sampler limit; any layer input can
be a full network, e.g. "transitioning from detail textures to larger macro textures depending on the distance" [U1].
RVT caches landscape shading over large areas and lets meshes blend into the ground [U2]. Community auto-materials
show the expected feature set: 6 layers, slope rules, steep faces triplanar, snow on near-flat ground above a
threshold, distance tiling, cell bombing, RVT, Nanite displacement [U3][U4].

**TerrainForge.** Imports with 8 paint layers and masks for PCG (RESEARCH-terrainforge.md). Its marketing renders
(frames `docs/research/terrainforge/01-hero-alpine.png`, `11-unreal-level-valley.png`) are the current visual bar
for "finished look from a generator".

**Blender add-ons.** Procedural Terrain 2.0: up to 6 height-only layers, each a Principled set or a custom shader,
sharp or smooth transitions, and the shader still works after sculpting because it is height based [B2]. True
Terrain 5 promises to "texture everything in just a few clicks" with presets but documents nothing about masks or
blending [B1]. Terrain Mixer PRO is alpha and says nothing about shading [B3]. **Gap:** no Blender tool documents
slope, flow or deposit driven materials, height blending or export of weight maps.

**Other references used.** Terrain3D (Godot): each paint stores base ID, overlay ID and a blend; an autoshader;
"Wetness adjusts roughness" [T1]. Height blend method: add each layer's height to its weight and keep the top
within a 0.2 band, so "sand settles into the cracks" [R1]. Anti-tiling: a per-tile random offset with 4 fetches, or
a cheap version with "only two texture fetches" [R2].

---

## 2. Quality bar (boards c154-c167)

| Board | Surface | Photos | What makes it read as real (headline) |
|---|---|---|---|
| c154 | Granite | 6 | Smooth pale slabs, dark gaps and water streaks; turf laps onto rock with a dark damp rim |
| c155 | Sandstone | 6 | Cross-bed bands in 2-3 close colours, in the relief as well as the colour; formation colour by height bands |
| c156 | Limestone | 7 | Blue-grey to cream, grooves and bed lines, grass in every crack, pale scree aprons, bleached water-line band |
| c157 | Basalt | 5 | Near black, very little hue; reads by sharp straight joints, lit tops, lichen on dry tops |
| c158 | Scree / talus | 6 | Lighter than the cliff above, cones under gullies, coarse at the foot, ragged lobed edge with turf |
| c159 | Grass | 5 | From afar grass is colour: green/olive/straw patches, dark in hollows, pale and dry on crests |
| c160 | Soil | 6 | Wet/dry value bands, rills along the flow, cracks only where dried |
| c161 | Sand | 6 | Ripples (about 5-20 cm) on every slope except the slip face; sharp crests; plants only in troughs |
| c162 | Snow | 6 | Slope decides: ledges white, steep faces dark stripes; lobed melt patches; blue in shade |
| c163 | Ice | 6 | Mostly grey-white and dirty; blue only in fresh breaks; debris bands along the flow |
| c164 | Mud / silt | 6 | Gloss in the low spots, matte crust higher; channels branch like a flow map |
| c165 | Lava | 6 | Black with silver sheen (pahoehoe) or brown-black rubble (aa); glow only in cracks; old lava brown with lichen |
| c166 | Moss | 6 | On tops and shaded wet faces, thickest by water; bright in sun, dark in shade; fills cracks first |
| c167 | Wet edges | 6 | Darker, glossier band at every water line with a sharp top; old levels as bleached rings |

Numbers worth building in, from opened sources:
- Dry sand stands at 34 degrees, wet sand 45, snow 38 (angle of repose) [P1]. Avalanches start on 30-45 degree slopes
  and are rarer on slopes steeper than 60 degrees [P2], which matches the boards: snow mostly gone above about 50-60.
- Scree is usually less steep than its angle of repose and concave, with the largest blocks at the bottom [P3].
- Desert varnish is orange to black, forms only on stable surfaces, and is missing on limestone; basalt takes a
  shiny black varnish [P4]. So "dark streaks on dry rock" is right for sandstone, granite and basalt, not limestone.

**Tool renders.** Not copied onto the boards (D49 and licensing). Compare against: Gaea's gallery and spotlights
(Alan Wake II, Baldur's Gate 3, Star Wars Jedi) at https://quadspinner.com/Gallery, and the TerrainForge frames
already in `docs/research/terrainforge/`. In those, the strongest reads are the same as in the photos: scree aprons,
snow on ledges and colour that follows the drainage.

---

## 3. Ranked feature list

Impact = how much it changes what an artist sees in the first render. Effort is for us, in Blender 5.2.

| # | Feature | Who has it | Effort | Our masks |
|---|---|---|---|---|
| 1 | **Mask rules with height-blended edges** (each layer: a range on one or more masks, plus Transition Width; sand and soil fill cracks first) | Unreal LB Height [U1], World Creator [W1 snippet], Procedural Terrains (Transition Width), Terrain3D [T1] | M | slope, height, curvature, deposit |
| 2 | **Climate switch** (Temperate, Arid, Alpine, Volcanic, Lush...) swapping the colour sets, snow line, wetness, grass tint | Gaea SatMap library [G2], Procedural Terrains climate biomes, WC biome presets (snippet) | M | all |
| 3 | **Scree and debris under cliffs** (lighter rock colour, coarser at the foot) | Gaea Debris/Soil [G4][G7], Houdini debris layer [H3] | S | deposit, wear, slope |
| 4 | **Snow by slope + height + facing** (Snow Line, Snow on Slopes, softness; lee-side bias) | Gaea Snow sims [G7], Houdini direction mask [H1], UE packs [U3] | S-M | height, slope (+ facing from the normal) |
| 5 | **Anti-tiling plus macro variation plus distance blend** | Houdini hex tiling [H2], WC stochastic (snippet), UE packs [U3][U4], IQ [R2] | M | none (position, camera distance) |
| 6 | **Colour follows the drainage** (streaks and stains below ridges and in channels, the ColorErosion idea done in the shader) | Gaea ColorErosion [G7], Gaea flow-mapped CLUT [G1] | M | flow, wear, curvature |
| 7 | **Wet edges and wetness** (darker, lower roughness band above every water level and in flow channels) | Terrain3D wetness [T1]; not standard elsewhere | S | water, depth, flow |
| 8 | **Rock types as materials** (granite, sandstone bands tied to our terraces, limestone, basalt, lava) shared by landscapes, caves and the rock and formation Kits, with a per-copy tint | Gaea rock tools [G7]; nobody shares terrain materials with instanced rocks | M | curvature, wear, height; per-copy via the Instancer attribute [BL3] |
| 9 | **Moss and lichen** (tops and shaded wet faces, near water) | UE packs partly; Gaea vegetation sim [G7] | S-M | curvature, flow, depth (+ facing) |
| 10 | **Fine detail as displacement** (limestone beds, lava ledges, lava crust, sand ripples; bump in Eevee, true displacement in Cycles) | UE Nanite displacement packs [U4], WC height blend displacement (snippet) | L | tube coords (lg_tube), slope |
| 11 | **Weight-map and baked-map export** (RGBA splat per 4 layers; colour/normal/roughness up to 16K) | Gaea Splat [G3], UE weightmaps [U1], TerrainForge 8 layers, Procedural Terrains | M-L | all (layer weights) |
| 12 | **Glowing lava** (emission only in cracks and at flow fronts) | none of the terrain tools | S | curvature, type |
| 13 | **Solo a layer in the viewport** (like the mask viewer, per material layer) | Gaea Mixer layer view [G6] | S | n/a |

Top 3 for artists: **1, 2 and 5** (believable edges, one-click looks, no visible tiling).

---

## 4. Build plan for Blender 5.2 (a plan, not code)

### 4.1 Node structure
- **One material per landscape, built from shared node groups:** `KB Surface Layer` (a texture set: colour,
  roughness, height, normal, all scaled in metres), `KB Layer Rule` (mask ranges with softness, the same maths the
  dials use) and `KB Height Blend` (weights plus layer heights, normalised, with a Transition Width). The stack in
  order: rock (by type) -> scree/debris -> soil -> grass -> sand/sediment -> mud/wet -> moss -> snow (alpha on top, like
  Unreal's alpha layer, which also avoids the all-height-blend black spots [U1]) -> lava glow / ice where the type
  needs it.
- **Masks are read with the Attribute node** (Geometry type) by name, as Houdini reads layers by name [H2][BL3].
  They stay raw 0-1 data (D75); the material owns the remapping.
- **Facing** (north/lee side for snow and moss) comes from the shading normal, so no new mask is needed.
- **Coordinates in metres**, from object position, so materials keep their real size at every landscape size
  (our scale-to-scene rule). Landscapes: top-down for flats, Box projection with Blend on slopes [BL1]. Caves: the
  existing UV map and lg_tube coordinates for bed lines and flow bands (D163, D157).
- **Rocks and formations** use the same layer groups with an `Instancer` attribute for a per-copy tint and
  offset [BL3], so rocks and ground read as one material (Parking: rocks share the landscape materials).

### 4.2 Textures and resolution
- **Preview and default: procedural** (noise, Voronoi, Gabor for banded rock and ripples [BL4]). No downloads, no
  licence risk, resolution-free.
- **Image texture sets (optional, High and Ultra)**: 2K tiling sets (colour, roughness, height, normal) per layer.
  Where they come from is an open question for Mike (see 4.6). Nothing copied from competitors (D49).
- **Texel density targets** (Maxon's guide: 10.24 px/cm first person, 5.12 third person, 2.56 or less top-down [P5]):
  landscapes 256-512 px/m for the tiling detail (a 2K set tiled every 4-8 m); cave shell and cave rocks
  512-1024 px/m (cameras get close); macro colour 1 sample per grid vertex.
- **Bakes for export** (Parking: up to 16K like TerrainForge): note a 1 km landscape at 16K is about 16 px/m, so
  bakes carry macro colour and weights; close detail must come from tiling sets in the target app.

### 4.3 Performance tiers
| Tier | Layers | Blend | Anti-tiling | Detail |
|---|---|---|---|---|
| Preview (Eevee, viewport) | 4-5 core layers | Height blend | Off (1 fetch) | Bump only |
| High | All layers for the type | Height blend + flow colour | 2-fetch variation [R2] | Bump; Eevee can also do "Displacement and Bump" [BL2] |
| Ultra (Cycles) | All | All | 4-fetch or hex tiling [R2][H2] | True displacement with Adaptive Subdivision (Cycles only) [BL5] |

Eevee true displacement is not precomputed and its cost scales with samples [BL2]; Cycles adaptive subdivision
needs Object-space edge length for instanced meshes [BL5], which affects the rock Kits.

### 4.4 What carries over
- **three.js (Project 2):** the same rule table (mask ranges, softness, colours per climate) in types.json-style
  data; masks as vertex attributes or a mask texture; splat RGBA textures plus a texture array. Triplanar costs
  three fetches per layer, so keep it to steep faces only.
- **Unreal (Project 3):** one paint layer per material layer, LB Height Blend for ground layers and LB Alpha for snow
  [U1]; weights exported as RGBA weightmaps, 4 layers each [U1]; an 8-layer budget matches TerrainForge; RVT for
  performance and mesh-to-ground blending [U2]; our masks also go to PCG.

### 4.5 Risks
- **Mask resolution:** masks live on the grid (metres per vertex), so raw edges are blurry. Height blend plus a small
  noise breakup in the material fixes it; it must be tuned per detail level.
- **Eevee shader compile time and cost** with 8+ layers of procedural noise; keep Preview to the core layers.
- **Procedural noise does not export:** anything shown in Blender must bake to maps for three.js and Unreal, or the
  look will differ between apps. Plan parity checks like the height parity tests.
- **Texture licensing** for any image sets (question 1).
- **Displacement on the cave shell** already failed as geometry (D184, seams and ripples); as a material it needs
  Cycles adaptive subdivision or bump only, and a check at all three levels.
- **Bake memory** at 16K (several maps per landscape).

### 4.6 Sized step list for M7 (checkpoint after each)
| Step | What | Size |
|---|---|---|
| 7.1 | Framework: layer, rule and height-blend groups; rock/scree/grass/snow on Mountains; Preview tier; solo-a-layer view | M |
| 7.2 | All layers and defaults for the 14 types; climate switch with the first climates | M |
| 7.3 | Rock types (granite, sandstone bands on terraces, limestone, basalt, lava) shared with caves, rock and formation Kits; per-copy tint | M |
| 7.4 | Anti-tiling, macro variation, distance blend; texel density checks | M |
| 7.5 | Wet edges and wetness, moss and lichen, colour along the drainage | M |
| 7.6 | Fine detail: displacement tiers; parked cave items (limestone beds D163, lava ledges D157, lava crust D184); glowing lava | L |
| 7.7 | Water shaders and water types (lake, sea, river; clean, murky, gross) | L |
| 7.8 | Material dials in the panel (Snow Line, Snow on Slopes, Rock Angle, Grass, Wetness, Sediment; each with softness) | S-M |
| 7.9 | Export: weight maps (RGBA per 4 layers) and baked colour/normal/roughness up to 16K | L |
| 7.10 | Photo review against boards c154-c167; gallery re-render with HDRI | M |
| 7.11 | Gate | S |

### 4.7 Questions for Mike
1. **Texture sources:** procedural only, or may we use CC0 libraries (for example Poly Haven or ambientCG), or
   KitBash-authored texture sets? D49 rules out competitor textures; CC0 libraries are a licence call.
2. **First climates:** which ship first? Suggested: Temperate, Arid, Alpine, Volcanic, Lush.
3. **Water shaders (7.7):** keep them in M7, or split into their own milestone? They are as big as the ground work.
4. **Unreal layer budget:** is 8 paint layers (2 weightmaps), like TerrainForge, the right target?
5. **Closest camera:** how close should artists get to the ground? It sets the texel density (256-512 vs 1024 px/m)
   and the size of the texture sets.

---

## 5. What we already had vs what's new

**Already had:** the seven masks on landscapes and caves (D74, D140) and lg_water; the decision that masks stay raw
and the dials live in the material (D75); box mapping for UV-less caves (DESIGN.md); cave UVs and tube coordinates
(features.py); a plain KB Water material (D77); Procedural Terrains' Transition Width and climate biomes, and
TerrainForge's 8 paint layers (earlier research); the parked M7 items (climate switch, rocks share materials, water
types, rock texel density, cave fine detail, lava crust, glowing lava, gallery re-render).

**New here:** how Gaea, Houdini and Unreal actually layer and blend (data-driven colour, ColorErosion, mask by
feature, Weight/Alpha/Height blend and the black-spot pitfall, weightmap per 4 layers); the anti-tiling and distance
blend options with their costs; texel density numbers; physical angles for sand, snow and scree; 14 photo boards
(83 photos) with what makes each surface read as real; a ranked feature list; a node structure, tiers, carry-over
plan, risks and an 11-step M7 plan.

---

## 6. Not verified

- **World Creator details:** docs.world-creator.com now redirects to the BiteTheBytes product page. Height
  Blending, triplanar (not exportable), stochastic distribution, distributions by height/slope/flow and the colour
  map export come from search snippets only, not from pages I could open.
- **Gaea 2/3 docs:** most reference pages opened are Gaea 1.3 docs; Gaea 3 facts come from its product pages. The
  Medium colour tutorial returned 403.
- **Unreal:** the "landscape material layer blending" page and the Nanite tessellation pages loaded empty
  (JavaScript only); the facts are from the "landscape materials" page. Nanite displacement claims come from a
  community pack's page only.
- **Blender manual:** docs.blender.org returned 403; facts come from the manual copy bundled with the Blender MCP
  server on this machine (the same RST sources). Blender was not started.
- **True Terrain 5's material internals,** TerrainForge's material rules, and the Houdini RGBA export bug (forum
  snippet only).
- **Tool renders** were linked, not collected as images.
- The ripple spacing (5-20 cm) on board c161 is from the photos, not a measured source.

---

## 7. Sources opened

Earlier project docs: docs/RESEARCH.md, RESEARCH-terrainforge.md, RESEARCH-procedural-terrains.md, PARKING.md,
DECISIONS.md, PROJECT.md, DESIGN.md.

- [G1] https://docs.quadspinner.com/Guide/Using-Gaea/Color-Production.html and https://docs.quadspinner.com/Reference/Color/CLUTer.html
- [G2] https://docs.quadspinner.com/Reference/Color/SatMaps.html
- [G3] https://docs.quadspinner.com/Reference/Color/Splat.html
- [G4] https://docs.quadspinner.com/Reference/Data/Soil.html and https://docs.quadspinner.com/Reference/Data/Texture.html
- [G5] https://docs.quadspinner.com/Reference/Color/Synth.html (also Mixer: https://docs.quadspinner.com/Reference/Color/Mixer.html)
- [G6] https://quadspinner.com/Gaea3
- [G7] https://quadspinner.com/Gaea/Features
- Gaea home and gallery: https://quadspinner.com/ , https://quadspinner.com/Gallery
- [W1] World Creator docs: redirected, see section 6 (https://docs.world-creator.com/reference/terrain/biome/materials)
- [W2] https://www.bitethebytes.com/docs/world-creator (World Creator 4 Early Access page)
- [H1] https://www.sidefx.com/docs/houdini/nodes/sop/heightfield_maskbyfeature.html
- [H2] https://www.sidefx.com/docs/houdini/heightfields/texturelayers.html
- [H3] https://www.sidefx.com/docs/houdini/nodes/sop/heightfield_erode.html
- [U1] https://dev.epicgames.com/documentation/en-us/unreal-engine/landscape-materials-in-unreal-engine
- [U2] https://dev.epicgames.com/documentation/en-us/unreal-engine/runtime-virtual-texturing-in-unreal-engine
- [U3] https://github.com/Kiriql/LandscapeAutoMaterial
- [U4] https://forums.unrealengine.com/t/cgdealers-landscape-auto-material-pro/2653630
- [TF] TerrainForge, via docs/RESEARCH-terrainforge.md and its frames in docs/research/terrainforge/
- [B1] https://superhivemarket.com/products/true-terrain
- [B2] https://superhivemarket.com/products/studio156-procedural-terrain-generator
- [B3] https://superhivemarket.com/products/terrain-mixer-pro
- [T1] https://terrain3d.readthedocs.io/en/latest/docs/texture_painting.html
- [R1] https://www.gamedeveloper.com/programming/advanced-terrain-texture-splatting
- [R2] https://iquilezles.org/articles/texturerepetition/
- [P1] https://en.wikipedia.org/wiki/Angle_of_repose
- [P2] https://en.wikipedia.org/wiki/Avalanche
- [P3] https://en.wikipedia.org/wiki/Scree
- [P4] https://en.wikipedia.org/wiki/Desert_varnish
- [P5] https://help.maxon.net/c4d/2027/en-us/Content/html/Texel_Density.html (read as its .md copy) and
  https://forums.unrealengine.com/t/texel-density-standards-for-aaa-first-person-shooter-games/1646118
- Blender 5.2 manual (bundled RST copy of docs.blender.org): [BL1] render/shader_nodes/textures/image.rst (Box
  projection, Blend); [BL2] render/eevee/material_settings.rst (displacement); [BL3] render/shader_nodes/input/attribute.rst
  (Geometry, Instancer); [BL4] render/shader_nodes/textures/gabor.rst; [BL5] modeling/modifiers/generate/subdivision_surface.rst
  (Adaptive Subdivision, Cycles only)
- Photos: Wikimedia Commons API (https://commons.wikimedia.org/w/api.php), every file page listed in each
  materials-*/sources.json (83 photos)

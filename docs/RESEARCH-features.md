# Feature research: Gaea, World Machine, World Creator vs ours (2026-11-08)

Research only, public web, no logins or trials. Every fact was read on **2026-11-08** from the source in brackets
(list in section 7). Builds on RESEARCH-positioning.md (pricing, company profiles), RESEARCH-engines.md (GPU/engines)
and RESEARCH-materials.md (material systems); those details are not repeated here. **Inspiration only (D49).**
Versions covered: **Gaea 2** (current) and **Gaea 3** (Early Access); **World Machine "Dragontail Peak"** (builds
4059-4065, 2026); **World Creator 3** (current) and **World Creator 4** (Early Access since 2026-11-03).

---

## 1. Summary

1. **The core set is large and settled.** All three ship: procedural generators, hydraulic + thermal erosion with
   sediment, snow, masks from terrain and erosion data, colour/PBR and splat (weight) map export, rivers and lakes,
   heightmap import, 16/32-bit heightmap and mesh export, tiled builds past 8K, an Unreal handoff, and reusable
   graphs (macros or presets). Users will expect all of it from us.
2. **Biggest gaps for us:** heightmap + splat export, an Unreal/engine handoff from Blender, drawn rivers and shapes,
   real-world elevation import, resolution past 4K and tiling, snow as a simulation, and batch/automation. Most are
   parked or sit in Project 2/3; none is in a Project 1 milestone yet.
3. **Each leader has one strong suit.** Gaea: erosion quality and colour (users rate its erosion highest). World
   Machine: the only true 3D overhangs and caves (VDM, experimental). World Creator: real-time GPU speed, a built-in
   scatter + render path to a finished shot, and an MCP server.
4. **Our caves still lead:** World Machine's VDMs "don't support holes", so its cave mouths are limited [WM3]. Gaea
   and World Creator have no caves.
5. **The KitBash edge is everything the three lack around the terrain:** a curated, scale-matched asset library
   (Kits), materials that match those Kits, a browser home in Cargo, and an MCP that can build terrain *and* dress it.

## 2. Feature matrix

Yes = shipping; Partial = limited, gated, Early Access or experimental; No = not found on the vendor's pages;
Unknown = not verifiable. "Ours planned" cites the PROJECT.md milestone, a D-number, or the PARKING.md row title.

| Feature | Gaea (2 / 3 EA) | World Machine (Dragontail Peak) | World Creator (3 / 4 EA) | Ours today (Blender) | Ours planned |
|---|---|---|---|---|---|
| **Primitives / generators** | Yes: "extensive Primitive library" (mountains, canyons, abstract) [G1]; G3 adds new primitives [G2] | Yes: fractal generators, "100+ devices" [WM1][WM2] | Yes: mountains, ridges, cliffs, plateaus, craters, 110+ noises in WC4 (announced) [WC1][WC4] | Yes: 13 surface types + Volcano styles, real-world tuned (M2, D52) | Cave landscape type (M6 6.1), Hero Mesa style (PARKING) |
| **Workflow** | Node graph; Mixer is layer-based for colour [G1] | Node graph ("not a brush") [WM1] | Layers (WC3); live node graph (WC4) [WC1][WC2] | Type picker + plain controls, no graph (M2) | Same in three.js (Project 2, D7) |
| **Hydraulic erosion** | Yes: Erosion_2 "hydraulic, thermal, and gravitational" [G1] | Yes: flow-based erosion [WM2] | Yes: hydraulic and thermal filters (search snippet of docs) [WC6]; "6+ Erosion Filters" [WC1]; new model in WC4 [WC2] | Yes: flow, incision, diffusion, talus, deposition engine, 512 grid (D53, M2) | GPU erosion at full res in Unreal (D82) |
| **Thermal erosion / talus** | Yes [G1]; new thermal in development (G3) [G2] | Yes: thermal builds talus slopes [WM2] | Yes [WC6] | Yes: talus step (D53) | — |
| **Sediment / deposits** | Yes: sediment displacement, Soil/Debris [G1] | Yes: sedimentation, wear, talus masks [WM2] | Yes: sediment filters, Color Erosion [WC1][WC6] | Yes: deposit mask (M3 3.1) | — |
| **Snow** | Yes: snow, glacier, dusting, ice floe [G1] | Yes: snow with wind drifts [WM2] | Yes: snow simulation [WC1] | No (no sim) | Snow as material only: Snow Line / Snow on Slopes (M7) |
| **Sand / dunes sim** | Partial: physics sand solver in G3 EA [G2] | No (community macro only) [WM5] | Yes: sand simulation [WC1] | Partial: Sand Dunes type with styles (M2) | — |
| **Coastal erosion** | No found | Yes: beaches and near-shore [WM2] | No found | No | — |
| **Stamps** | Partial: File node loads any 8/16/32-bit image; Object node rasterizes 3D models [G1][G5] | Partial: File Input device [WM6] | Yes: 2D heightmap+colour stamps, 3D model stamping [WC1] | No | Stamps and curves (PARKING, pending) |
| **Vector shapes (rivers, roads, paths)** | Yes: Draw node; G3 Vector Tools for rivers, lakes, roads [G1][G2] | Yes: Shapes (ex-Layout Generator), Bezier paths, roads, rivers [WM2][WM7] | Yes: vector tools for paths, rivers, mountains [WC1] | No | River curve stamp (PARKING); cave path curve (M5 5.2b) |
| **Brushes / sculpting** | Partial: Draw Tools 3.0 brush mode (G3 EA) [G2] | No found on vendor pages [WM2] | Yes: real-time brushes, custom brushes, grid sculpting [WC1] | Partial: Bake to Mesh, then Blender sculpt (M4 4.1) | Sculpt brushes on a height-offset layer (PARKING) |
| **Masks / selectors** | Yes: data maps height, slope, occlusion, flow, soil [G1][G4] | Yes: elevation, slope, roughness, wetness, convexity, erosion masks [WM2] | Yes: slope, height, curvature, noise, paint, image [WC1] | Yes: height, slope, curvature, flow, wear, deposit, depth + viewer (M3) | Mask-remap material controls (M7) |
| **Colour / texturing** | Yes: SatMaps (1,400+), Synth, ColorErosion, Mixer [G1] | Yes: PBR outputs, material macros [WM2] | Yes: PBR layer stack, Sat Maps, Substance, 140+ scans (paid) [WC1] | No (plain water material only) | Auto-material, climate switch (M7, D195) |
| **Splat / weight-map export** | Yes: Splat node, Unreal weightmaps [G1][M-G3] | Yes: RGBA Weightmap device [WM2] | Yes: splat maps [WC1] | No | 16-bit heightmap + splat export (PARKING → M8 / Project 2); Unreal paint layers (D78) |
| **Vegetation / scatter** | Partial: Vegetation node, G3 EcoSystems out as masks or point clouds, no asset instancing [G1][G2] | No: only a Vegetation Layer mask macro [WM2] | Yes: rule-based scatter, avoidance, manual placement, GPU instancing, 40+ assets, GLB/FBX/OBJ import [WC1] | No | Foliage and scatter from masks, Kits in slots (PARKING, after M7) |
| **Water: rivers** | Yes: river sims; G3 drawn meandering river sim [G1][G2] | Yes: River Tool, Create Water; not yet on VDM terrain [WM2][WM3] | Yes: procedural + manual rivers, meanders, deltas [WC1] | No | — (river curve stamp, PARKING) |
| **Water: lakes / sea** | Yes: lakes, seas, dam overflow; water as mesh [G1] | Yes: lakes, coastal; water as mesh + flow vectors [WM2] | Yes: lakes, ocean rendering, fluid sim [WC1] | Partial: water plane at a set level (M3 3.4) | Water shaders lake/sea/river (M7 and own milestone, D195) |
| **Caves / overhangs (3D)** | No: "2.7D Displacement" only (G3) [G2] | Partial: VDM overhangs, undercuts, caves; experimental; no holes, so cave mouths are limited [WM3][WM4] | No found [WC1] | Yes: walk-in cave object, 3 rock types, formations, mouth (M5) | Carve into landscapes, cliffs, overhangs, arches (M5 5.3, M6 6.2) |
| **Real-world elevation (DEM/GIS)** | Partial: image import; GIS formats not stated [G1][G5] | Partial: File Input; GeoTIFF support inconsistent per forum [WM6] | Yes: GeoTIFF, HGT, DTED, Esri Grid, VRT, XYZ; MapTiler streaming [WC1][WC5] | No (used only for our realism checks, R3) | "Real terrain" option parked (D82, PARKING) |
| **Tiling / large worlds** | Yes: Indie splits tiles; Pro tiled to 262,144²; G3 World Space infinite (Pro) [G3][G2] | Yes (Pro): unlimited tiled, resumable builds [WM2][WM8] | Partial: "virtually unlimited size", tiling not described [WC1] | No | Tiling + heightmap export (PARKING); World Partition in Unreal (Project 3, D78) |
| **Max single build** | 1K free / 8K Indie / 16K Pro ("experimental") [G3] | 1K free / RAM-limited Indie / unlimited Pro [WM8] | Unknown (no number) [WC1] | 4,096 (Ultra tier, R1.5) | 1K-8K in Cargo (PARKING); 4K-16K in Unreal (D78) |
| **GPU** | Yes: CUDA/HIP [E] | No for core; GPU only in the Code device (Slang via Vulkan/Metal) [WM2][WM4] | Yes: "GPU Powered" [WC1] | No (CPU, Geometry Nodes + numpy) [E] | GPU in three.js (Project 2) and Unreal (D82) |
| **Speed / previews** | Progressive previews, Lock Preview, caching; 8K viewport previews (G3) [G1][G2] | Real-time sim feedback; erosion "up to 100× faster" [WM2] | "Everything is Real Time" [WC1] | Preview 0.07 s / Final ~1.2 s / Ultra ~5 s; 1 km High 17.3 s (R1.5, M4) | — |
| **In-app finished render** | Partial: LightX AO/shadows, G3 Renderer 3.0 GI [G1][G2] | Partial: IBL, height fog, tone mapping [WM2] | Yes: path tracer, volumetric clouds, fog, HDRI, DOF, flythroughs [WC1] | Yes via Blender (Cycles/Eevee) | Fog and atmosphere (PARKING; first priority, D194) |
| **Heightmap export** | Yes: EXR, TIFF, PNG, RAW 8-32 bit [G1] | Yes: RAW, EXR, TIFF, PNG, TER [WM2] | Yes: RAW 8/16/32, EXR, ASC, XYZ, DEM [WC1] | No | PARKING → M8 / Project 2 |
| **Mesh export** | Yes: OBJ, FBX, DAE, glTF; Adaptive Tris [G1] | Yes: OBJ, glTF/GLB, VDM [WM2] | Yes: mesh export; OBJ, FBX, glTF [WC1][WC5] | Yes: Bake to Mesh, then any Blender exporter (M4) | Download OBJ/FBX, later glTF/USD (PARKING, Project 2) |
| **Unreal** | Yes: Gaea2Unreal, open source (Indie+) [G1][G3] | Partial: "native support" listed; no plugin described [WM2] | Yes: bridge [WC1] | No | Send to Unreal; Unreal 5.8 plugin (Project 3, D78) |
| **Unity / Godot** | Partial: Unity plugin in G3 EA [G2] | Partial: formats for Unity, Godot (RGB EXR) [WM2][WM4] | Yes: bridges [WC1] | No | — |
| **Houdini** | Yes: Gaea2Houdini (Pro) [G3] | No plugin found | Yes: bridge [WC1] | No | — |
| **Blender / C4D / Max / Maya** | Partial: plugins for Blender, Max, Maya in G3 EA [G2] | No plugin (named as downstream tools) [WM2] | Yes: Blender and C4D bridges [WC1] | Yes: native add-on | Send to Blender from Cargo (PARKING: three-app ecosystem) |
| **USD** | Partial: G3, Pro+ [G2] | No found | No found | No (Blender can export USD after bake) | Later in Cargo (PARKING) |
| **Batch / CLI / scripting** | Yes: Build Swarm CLI (Gaea.Build.exe) [G6]; automation Pro+ [G3] | Yes: script builds (Pro); Lua Code device [WM2][WM8] | No CLI found [WC1] | Partial: headless Blender test scripts, dev only | — |
| **AI / MCP** | No found | No found | Yes: MCP server on the running editor [WC1][WC2] | Partial: Blender MCP, dev only | Cargo MCP builds terrain and places Kits (D194) |
| **Plugin / SDK** | Partial: C# SDK in development (G3, Pro+) [G2] | Partial: Code device ("without building a plugin"); lockable macros for resale [WM2][WM8] | No found | No | — |
| **Presets / templates / community** | Presets in node search; macros (Indie use, Pro create) [G7][G3]; Mutations [G1] | Macros, Blueprints; community Macro Library; paid packs (e.g. HYLK, €34) [WM2][WM5] | 140+ scans, 40+ assets; imports Fab, TurboSquid; 13k Discord (positioning doc) [WC1] | Save/restore presets (M4 4.1) | Shipped KitBash presets (PARKING) |
| **Free tier** | Community: 1K, non-commercial [G3] | Basic: 1K, 4 threads, personal [WM8] | None [P] | n/a | Packaging later (Mike, 2026-11-06) |
| **Platforms** | Windows | Windows, macOS, Linux [WM4] | Windows; WC4 adds Apple Silicon Mac [WC2] | Blender (Win/Mac/Linux) | Browser (Project 2) |

## 3. Core set: what all three share (table stakes)

Users moving from any of the three will expect:

1. **Fast base shapes:** generators or primitives plus noise, with a seed [G1][WM2][WC1].
2. **Erosion with outputs:** hydraulic + thermal + sediment, and the erosion results as masks (flow, wear,
   deposits/talus) [G1][WM2][WC1][WC6].
3. **Snow** as a simulation, not only a colour [G1][WM2][WC1].
4. **Masks / selectors** by height, slope and curvature, combinable [G1][WM2][WC1].
5. **Colour and texturing** driven by those masks, with satellite-style gradients in Gaea and World Creator [G1][WC1]
   and PBR outputs in all three [G1][WM2][WC1].
6. **Splat / weight maps** for engine paint layers [G1][WM2][WC1].
7. **Water:** drawn or simulated rivers, and lakes [G1][WM2][WC1].
8. **Drawn shapes:** vector paths for rivers, roads and ridges [G2][WM7][WC1].
9. **Heightmap import** (at least image files) [G5][WM6][WC1].
10. **Export:** 16/32-bit heightmaps (EXR/RAW/PNG/TIFF) and meshes (OBJ, glTF) [G1][WM2][WC1].
11. **Big terrains:** 8K+ single builds and tiled worlds, gated to paid tiers [G3][WM8][WC1].
12. **Unreal handoff** (plugin or ready formats) [G1][WM2][WC1].
13. **Reuse:** macros, presets or saved graphs [G7][WM2][WC1].
14. **A free or ~$99-$119 entry** with commercial use from the first paid tier (RESEARCH-positioning.md section 2).

Not shared (so not strictly table stakes): scatter with real assets (World Creator only), 3D overhangs (World
Machine only), in-app finished renders (World Creator only), GPU (not World Machine), MCP (World Creator only),
CLI (not World Creator), Houdini (not World Machine).

## 4. Differentiators: what each does that the others don't

Evidence on what users value is thin: forum and Reddit opinions were seen as **search snippets only** (Polycount
returned 403 before, RESEARCH-positioning.md), and the 2026 "best tools" roundups read as SEO lists. Treat the
"valued?" column as weak signal.

### Gaea
| Differentiator | Evidence it's valued |
|---|---|
| Erosion quality (Erosion_2: hydraulic, thermal, gravitational) [G1] | Users "generally rate Gaea's erosion highest"; some World Creator users import Gaea heightfields for its erosion (snippets) [U1]. Asked for by name in 2026 AAA postings (positioning doc) |
| Colour from data: 1,400+ SatMaps, Synth, ColorErosion [G1] | World Creator copied the idea (Sat Maps, Color Erosion) [WC1]: a sign it matters |
| Biggest tiled world: 262,144² (Pro) and infinite World Space (G3) [G3][G2] | Open-world AAA need; no user evidence found |
| EcoSystems / Vegetation sim tied to hydrology and climate, output as masks and point clouds [G1][G2] | Unknown |
| Mutations (coherent variations), Transpose (move one terrain's surface onto another) [G1] | Unknown |
| Open-source Unreal and Houdini plugins; G3 adds Blender, Unity, Max, Maya plugins and USD [G1][G2] | Gaea2Houdini ships in SideFX Labs (search result) [U2] |
| Downside: Windows-only; some users call it "quite buggy" (snippet) [U1] | — |

### World Machine
| Differentiator | Evidence it's valued |
|---|---|
| **True 3D terrain via VDM:** overhangs, undercuts, caves (experimental; no holes; water devices don't work on VDM yet) [WM3][WM4] | Covered by CGChannel and others [WM4]; no user reviews found yet |
| Coastal erosion (beaches, near-shore) [WM2] | Unknown |
| Native macOS and Linux (only one of the three on Linux) [WM4] | Long-requested (forum thread title "Mac World Machine?") [WM9] |
| Code device: Lua host + Slang GPU compute shaders; lockable macros for resale [WM2][WM8] | Paid macro packs exist (HYLK €34) [WM5] |
| Unlimited tiled resolution with resumable builds; oldest pipeline standard [WM2] | Named next to Gaea in AAA postings; quiet forum (45 active users in 30 days) (positioning doc) |

### World Creator
| Differentiator | Evidence it's valued |
|---|---|
| Real-time GPU everything [WC1] | "way faster if you have a good GPU"; "almost real-time" interface (snippets) [U1]; the "speed pick" in roundups [U3] |
| Layers (WC3) as the easy entry [WC1] | Called "more art-directable" (snippet) [U1] |
| Scatter with real assets: rules, avoidance, manual placement, instancing, terrain conforms under structures, Object Area and Camera distributions [WC1][WC5] | 13k-member Discord (positioning doc); feature added in 2026.3 [WC5] |
| A finished shot in-app: path tracer, volumetric clouds, fog, HDRI, DOF, flythroughs [WC1][WC2] | Unknown |
| MCP server that edits the open project atomically, with undo [WC1] | New (2026); no user evidence |
| Real-world data: MapTiler streaming + six GIS formats [WC1][WC5] | Unknown |
| Bridges to six apps incl. Blender and Cinema 4D; Codewalker (GTA V/FiveM) [WC1] | Unknown |
| Planets (WC4) [WC2][WC4] | Unknown |
| Bundled 140+ scans and 40+ 3D assets (paid tiers) [WC1] | Unknown |

## 5. Gaps: table stakes we don't have or plan yet

| Gap | All three have it? | Our status | Note |
|---|---|---|---|
| **Heightmap + splat/weight-map export** | Yes | Parked (→ M8 / Project 2) | Cheapest gap to close; needed for every engine handoff and for "Gaea-style" Unreal pipelines (positioning doc) |
| **Engine handoff from Blender** (Unreal at least) | Yes | Project 3 only (D78) | Blender users today can only export a mesh |
| **Drawn shapes: rivers, roads, ridges** | Yes | Stamps and curves parked; no rivers | Our water is a flat plane; no carved river channels |
| **Real-world elevation import** | Yes (Gaea/WM partial) | Parked (D82) | We already have the DEM pipeline from realism checks (R3) |
| **Snow as a simulation** | Yes | Material only (M7) | Material snow may be enough for shots; sims drift and pile |
| **Resolution past 4K + tiling** | Yes (paid tiers) | Not in Project 1 | Fine for shot-making; matters for open-world users |
| **Texturing** | Yes | M7 in progress | Already the top priority (D194) |
| **Batch / scripted builds** | Gaea, WM (Pro) | None user-facing | Cargo MCP could cover this need differently |
| **Stamps / heightmap import as a shape** | Yes (partial in Gaea, WM) | Parked | — |
| **Free tier** | Gaea, WM | Packaging deferred | Mike: talk packaging later |

Not gaps (we match or lead): erosion with masks, mesh export (via Blender), masks and a viewer, presets, caves.

## 6. Candidate KitBash differentiators (proposals for Mike, not decisions)

Each is grounded in what the three lack. Ranked by how hard it is for them to copy.

| # | Proposal | What competitors lack | Evidence |
|---|---|---|---|
| 1 | **Kits as the scatter and set-dressing library:** pick a Kit, the terrain's masks place its buildings, props and rocks (flat ground for buildings, slopes for rocks, valleys for ruins) at true scale | Gaea and WM have no asset instancing; World Creator scatters generic assets (40+) and imports from Fab/TurboSquid, but has no curated, art-directed library | [G1][WM2][WC1] |
| 2 | **Kit-aware ground:** terrain flattens and blends under placed Kits, with fit-to-scene sizing (our Fit to Selection, M1) and a "Kit footprint" mask feeding erosion and materials | World Creator has "terrain conformity" under structures [WC1], but nobody sizes the terrain to the assets or blends the assets' bases into the ground material | [WC1][WC5] |
| 3 | **Materials that match the Kits:** the climate switch (M7) offers sets matched to Kit art direction (e.g. a Kit's desert or sci-fi palette), shared by terrain, our rock pieces and the Kit's ground | Competitors ship generic scans (WC 140+) or gradients; none matches an asset library's look | [WC1][G1]; RESEARCH-materials.md item 8 |
| 4 | **Cargo MCP: one prompt to a dressed shot:** "desert canyon at dusk, a cave, the Wasteland Kit" builds terrain, cave, materials, fog, places Kits and frames a camera | World Creator's MCP edits terrain only [WC1]; Gaea and WM have none | [WC1]; D194 |
| 5 | **Caves and cliffs as reusable Kits:** walk-in caves with real mouths, formations and rock pieces, exported as meshes (Nanite in Unreal, D89) and sold or bundled like Kits | WM VDM caves can't have holes [WM3]; Gaea/WC have none | [WM3][WM4][G2] |
| 6 | **One recipe, three apps:** the same small recipe rebuilds natively in Cargo (browser), Blender and Unreal at each app's best resolution, instead of shipping baked maps | All three run only on the desktop (none in a browser) [E]; their bridges move baked maps and meshes [G1][WC4] | RESEARCH-engines.md; D7, D78 |
| 7 | **Kit-matched landscape presets:** each Kit release ships a landscape preset (terrain + material + fog + camera) built for it, so a new Kit arrives with a world to put it in | Presets/macros exist (Gaea, WM library) but are terrain-only and unrelated to any asset release | [G7][WM5] |

Weaker ideas, not recommended as headline claims: "no node graph" (World Creator 3 layers already do this), price
(we lose to $99 one-offs), in-app rendering (World Creator already has a path tracer).

## 7. Sources (all accessed 2026-11-08)

Gaea / QuadSpinner
- [G1] https://quadspinner.com/Gaea/Features (reads as the Gaea 2 feature list)
- [G2] https://quadspinner.com/Gaea3 (Gaea 3 Early Access; public beta "estimated to be in October 2026")
- [G3] https://quadspinner.com/Order/ (edition gates and resolutions)
- [G4] RESEARCH-materials.md, Gaea data maps (docs.quadspinner.com, opened 2026-11-06)
- [G5] https://docs.quadspinner.com/Guide/Using-Gaea/Create-Shapes.html (File node formats; Gaea 1.3 docs; search summary only)
- [G6] https://docs.quadspinner.com/Guide/Build/Swarm.html and /Guide/Developers/Automation.html (Build Swarm CLI; Gaea 1.3 docs; search summary only)
- [G7] https://www.cgchannel.com/2024/08/quadspinner-releases-gaea-2-0 and Gaea 2 change log (presets in node search, macros; search results only)
- https://quadspinner.com/Roadmap: HTTP 404

World Machine
- [WM1] https://www.world-machine.com/
- [WM2] https://world-machine.com/features.php
- [WM3] https://help.world-machine.com/topic/build-4059-dragontail-peak/ (updated 2026-08-29)
- [WM4] https://www.cgchannel.com/2026/07/world-machine-software-ships-world-machine-dragontail-peak/ (2026-07-25); https://help.world-machine.com/topic/build-4065-dragontail-peak/
- [WM5] https://world-machine.com/library/ and https://hylk.gumroad.com/l/HYLKMacroPack (search results only)
- [WM6] https://help.world-machine.com/topic/file-input-and-output/ and forum threads on GeoTIFF import (search results only)
- [WM7] https://help.world-machine.com/?p=1375 (Shapes, formerly Layout Generator; search result only)
- [WM8] https://www.world-machine.com/purchase.php
- [WM9] https://forum.world-machine.com/t/mac-world-machine/8410 (title only)
- https://www.world-machine.com/roadmap.php: HTTP 404

World Creator / BiteTheBytes
- [WC1] https://www.bitethebytes.com/products/world-creator/features
- [WC2] https://www.bitethebytes.com/docs/world-creator (WC4 Early Access list)
- [WC4] https://digitalproduction.com/2026/10/13/world-creator-4-planetary-terrain/ (2026-10-13)
- [WC5] https://www.cgchannel.com/2026/03/bitethebytes-releases-world-creator-2026-3/ (2026-03-18, updated 2026-04-28)
- [WC6] https://docs.world-creator.com/reference/terrain/filters (redirects to [WC2]; hydraulic/thermal filter claim from search summary only), https://80.lv/articles/terrain-and-landscape-tool-world-creator-3-released
- [P] RESEARCH-positioning.md, pricing table (2026-11-06)

User opinion (weak evidence, search snippets only)
- [U1] https://polycount.com/discussion/233875/gaea-vs-world-creator, planetside.co.uk forum threads, r/unrealengine comments (snippets via search; not opened)
- [U2] https://www.cgchannel.com/tag/gaea-2-0 (Gaea2Houdini in SideFX Labs; snippet)
- [U3] https://gitnux.org/best/terrain-design-software/ and similar 2026 roundups (SEO lists; snippets)
- https://forum.world-machine.com/t/gaea-2-vs-worldmachine/7183/7: opened, no comparison content

Ours
- [E] RESEARCH-engines.md (GPU and browser findings, 2026-11-06)
- PROJECT.md, PARKING.md, DECISIONS.md (D7, D49, D52, D53, D78, D82, D89, D194, D195)

## Not verified / contradictions

- **⚠ Contradiction (World Machine status):** RESEARCH-positioning.md (2026-11-06) says Dragontail Peak is "still in
  alpha". Newer reading: build 4059 shipped 2026-05-18 and 4065 added macOS/Linux; the homepage calls it "2026
  Current" [WM1][WM4]. VDM devices are still marked experimental [WM3]. Both claims kept; this one is newer.
- **⚠ Contradiction (World Creator prices):** Digital Production (2026-10-13) lists $149 / $289 / $499 / $1,499
  perpetual [WC4]; CGChannel (2026-03-18, updated 2026-04-28) lists $99 / $199 / $399 / $1,499 [WC5]; the vendor
  page shows "pricing on request" (positioning doc). Unresolved.
- Gaea 3 public release: the page said "estimated ... October 2026"; still Early Access as read today [G2].
- Whether Gaea imports GeoTIFF/GIS formats directly, and whether World Machine's GeoTIFF import works reliably: unknown.
- World Creator's maximum resolution and tiling: unknown (an older "128,000 × 128,000" claim seen only in a search
  snippet; not used). Which World Creator editions include the bridges and scans beyond "Professional, Studio and
  Enterprise" for scans: unknown.
- World Machine's Unreal/Unity "native support" may mean export formats, not plugins: unknown.
- WC4 export and bridges in Early Access: not listed [WC2]; Digital Production says the old bridge docs are "not a
  specification for version 4" [WC4].
- User-value evidence is snippets and roundups only; no survey data exists.

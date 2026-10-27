# Project 3 plan: the Unreal version (updated 2026-10-27, after the TerrainForge review)

Status: **proposed**, for Mike. It builds on the three-app plan (PARKING "Three-app ecosystem", 2026-10-25)
and on what TerrainForge shows the bar now is (RESEARCH-terrainforge.md). Project 3 starts after Project 2
(three.js in Cargo). It's built with the Unreal MCP, as Project 1 was with the Blender MCP.

## Positioning (Mike, 2026-10-27)
Not just a terrain generator: **the finished artistic look, faster and easier.** Terrain is a big part of it, but
the product is the whole shot: realistic water, fog and atmosphere, clouds, materials and Kits. You get there
without being bogged down in nodes. It just works, the changes that matter are quick, and the result lands in
your scene fast, in Blender or Unreal and later any DCC Cargo supports. Landscapes are the first beachhead, and
Blender support is a big part of it. The bar: look at least as good as the node-based tools, plus the artistic
flair (fog, water, clouds, finishing) that takes it over the top.

## Flow (Mike, 2026-10-27)
**Cargo is where every landscape is first made.** From Cargo: Send to Blender and Send to Unreal today, more apps
later. Blender and Unreal receive the same package and rebuild it. There's no app-to-app path between them (D80).

**How each app receives it (Mike, D83):**
- **Blender: plugin-free.** A data package (baked heightmap and masks at the export resolution, material maps
  and settings, water and fog settings) plus build instructions carried out through the Blender MCP or a small
  bundled script, using Blender's own tools. No add-on needed, which sidesteps the GPL issue for Blender.
- **Unreal: plugin allowed** (no GPL issue there). The same package lands without it. With our plugin installed,
  Unreal adds GPU erosion at full resolution and lets artists keep editing after import.
- Whatever the app, a render-comparison check proves the result matches the Cargo version.
- **Chad's three.js standalone-tool framework** (the one Rick is using) gives Project 2 its **UI and visual
  framework**, so ours looks and works like the other Cargo generators. Its export is a simple OBJ download for
  simpler generators, so **we build the export layer ourselves on top of it**: the Blender data package with
  build instructions, the Unreal package, and later other DCCs (D84). USD is a far-off option.

## The bar
- **Look:** better than TerrainForge's renders. Real materials, water, grass and sky in the first shot, not grey terrain.
- **Landing:** at least as native as theirs. The import becomes a World Partition landscape with paint layers,
  water bodies and masks ready for PCG, in one step.
- **Resolution:** 8K in Unreal for v1 (AAA), 16K later for VFX, without losing what makes ours different: artist-first controls, the
  hero types and styles, KitBash Kits on the terrain, Cargo as the hub, and agents through our MCP.

## The key idea: the recipe is resolution-free; Unreal rebuilds it at full size
Our landscape isn't a heightmap. It's a **recipe**: type, style, every control, seed, size and Height.
Every shape is sampled in landscape-relative coordinates, so the same recipe gives the same landscape at any
resolution (D3, test T1). So we don't need 16K in three.js. Cargo authors and previews; Unreal **re-evaluates
the same recipe natively at 8K–16K**. Mike's point, "if it's node-based, it's just upscaling within Unreal",
is right for the shape. The one part that isn't free is erosion, which is a simulation, not a formula.

| Layer | How it gets to 16K in Unreal | Cost |
|---|---|---|
| Big shapes (types, styles, controls, terraces) | Re-evaluated from the recipe at full resolution (GPU, a material/compute port of the node math) | Free in quality, fast |
| Erosion (valleys, gullies, talus, fans) | Computed once at 1–2K by the shared engine, shipped as an **erosion layer**, upsampled smoothly | Small file; looks right at the big scale |
| Fine detail on the eroded shape | Rock grain in real meters (D47) and the shape's own fine detail added back at full resolution, kept off channels and floors with the flow mask (the same keep-detail rule as erosion.py) | Cheap, resolution-free |
| Full-resolution erosion (**in v1**, Mike D82) | A GPU erosion pass in Unreal (compute shader) on top of the shipped layer: sharp rills, gullies and fans at full 8K | Heavy; runs on Build, with progress in the build monitor |

So Unreal gets a 16K landscape whose **big forms, valleys and drainage** match what the artist approved in
Cargo, with real 16K detail on top. This also keeps Cargo fast: three.js only ever builds preview resolutions.

### Resolution per app
| App | Interactive | Final | Erosion grid |
|---|---|---|---|
| Cargo (three.js, WebGPU) | 1K | 2K–4K (Ultra; GPU displacement and level of detail) | 512–1K, WebGPU compute |
| Blender (Project 1) | Preview 512 | High 2K / Ultra 4K | 512 (CPU, the reference engine) |
| Unreal (Project 3) | Recipe preview 1–2K | 4K / **8K (v1 target)**; 16K tier for VFX later | Ships the 1–2K layer; optional GPU refinement at full size |

A **parity test** checks all three: the same recipe built in each app gives matching heights and masks at a shared resolution.

## The package (what "Send to Unreal" hands over)
- `recipe.json`: type, style, controls, seed, size, Height, terraces, water, version (the same JSON as presets)
- `erosion.exr`: the eroded heights at 1–2K (16-bit float), plus `flow / wear / deposit` in its channels
- `masks.exr`: height, slope, curvature, water depth at the same size (rebuilt at full size in Unreal from
  the rebuilt shape; the shipped copy is for checks and for tools that can't rebuild)
- `material.json`: the M5 material layer choices and dial settings (snow line, rock angle, wetness, ...)
- `scatter.json`: Kit or foliage layers and their mask rules (after the scatter work)
- Sent from Cargo only: Cargo is where a landscape is first made, and it sends to Blender and to Unreal (more apps later). There's no Blender-to-Unreal path; the Blender add-on receives and edits, it doesn't hand on.

## Landing in Unreal (match and beat TerrainForge)
1. **World Partition landscape** at the chosen resolution, with component sizes picked automatically, plus tiling
   for big worlds.
2. **Paint layers from our masks.** About 8 layers: rock, scree, sand, grass, forest floor, snow, wet ground,
   sediment. Each is weighted by the masks through the same dial controls as the M5 material, so it matches Blender.
3. **One landscape material** with those layers, the M5 dials and real-size rock detail, using Nanite tessellation
   or displacement where available.
4. **Water bodies:** a Water Body Lake or Ocean at our water level, and Water Body River along the main
   flow-mask channels. The depth mask drives shore foam and colour.
5. **PCG-ready:** the masks are exposed as landscape layers or PCG attributes, so a PCG graph puts forest
   "where forest would grow". It ships with KitBash PCG graphs for scattering Kits.
6. **Finishing look:** sky, fog and atmosphere, and clouds (the parked fog/atmosphere step), as one-click moods, so the first look is a finished shot.

## New features this adds to the roadmap
- **Real places (from TerrainForge): parked (D82).** Artist-driven first: dial in realism with our types and presets, then try a few real DEM tiles (Copernicus 30 m, open 1 m data) and see if they look as good.
- **A realism score users can see:** undecided, not now (D82). We already measure it per type (T6, T6b) as our quality bar.
- **Build monitor:** progress, time left and memory for long builds (Final 16K, GPU erosion).
- **Agent tools in the Cargo MCP and the Unreal plugin:** create a landscape, set its type, set a control,
  build, send to Unreal, validate. Plus skills for whole flows ("a 4 km alpine valley with a lake, Kits on the
  shore"). The agent proposes, the artist keeps the final say.

## What we keep that TerrainForge doesn't have
- Plain-language controls for artists, not a node graph to learn. A graph view could come later, for technical
  users only.
- Three apps from one recipe, with Cargo as the hub, and part of the Cargo subscription.
- KitBash Kits placed and scattered on the terrain.
- Hero types and styles: volcano breach, collapse and inner cone; Hero Butte with no floor; terraces; presets.
- Realism per landscape type, each against its own real place.

## Project 3 milestones (proposed; each ends at a gate)
| # | Milestone | Done when |
|---|---|---|
| U1 | Recipe core in Unreal | The same recipe builds the same big shapes as Blender/three.js (parity test), live preview at 1–2K |
| U2 | Erosion layer + full-res rebuild | Shipped erosion layer upsampled; 4K and 8K builds with fine detail added back; build monitor |
| U2b | GPU erosion at full resolution (v1, D82) | A compute-shader erosion pass on the rebuilt 8K landscape that refines the shipped layer and passes the 1 m realism checks; fast enough to use straight away |
| U3 | World Partition landing | One-click import: landscape, component sizes, tiling; size and Height exact |
| U4 | Material + paint layers | 8 layers from the masks, M5 dials, matches the Blender look |
| U5 | Water + PCG + sky | Water bodies from our water level and flow; masks for PCG; Kit scatter graphs; sky/atmosphere preset |
| U6 | Agents + Send to Unreal | MCP tools and skills; Send to Unreal from Cargo |
| U7 | 16K VFX tier | 16K builds for VFX shots (memory, tiling, build time) |
| U8 | Errors, edge cases, final check | Bad input, huge sizes, missing data, old packages; final checker review |

Real places are parked (D82). When they come back they land in Cargo first and reach Unreal through the package.

## Questions for Mike
1. ~~16K or 8K as the first target?~~ **Decided (Mike, D81): at least 8K for v1**, the max for most AAA studios; Unreal upscales from there. 16K is a later tier for VFX studios' bigger shots (U7).
2. ~~GPU erosion in v1?~~ **Decided (Mike, D82): yes.** Erosion adds a ton and people should want to use it straight away; it's milestone U2b.
3. ~~Real places?~~ **Parked (Mike, D82).** Artist-driven first: dial in realism with our types and presets, then try a few real places and see if they look as good.
4. **Realism score in the product:** undecided; not now (Mike, D82). It stays our internal quality bar.

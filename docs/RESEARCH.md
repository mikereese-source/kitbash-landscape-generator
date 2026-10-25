# KitBash Landscape Generator — Market Research (2026-10-22)

Quick scan of existing landscape tools to find what ours should add. Prices and claims are as found on 2026-10-22; unverified items are flagged at the bottom.

## Blender tools on Superhive Market
| Product | Price | Approach | Standout | Weak spots |
|---|---|---|---|---|
| True TERRAIN 5 | $49–99 (pages disagree) | One-click UI, presets | Erosion, water, 220+ scatter assets, layers | 4/5 (33 ratings): learning curve on advanced options, slow in big scenes, preset errors |
| Terrain Mixer PRO | $59 (free base version on Extensions) | Geometry Nodes, modular | Non-destructive terrain blending | Alpha, docs unfinished |
| Procedural Terrain 2.0 (Studio156) | $15 | Geometry Nodes + shaders (v1 Python was dropped for speed) | Camera-driven LOD, 6 height-based material layers, apply-then-sculpt | No reviews |
| Geoscape Terrain Nodes | $35 | GN node library (50+) | Hydraulic erosion, rivers, plateaus, 20+ mask nodes | Few sales |
| Desert Cliff Generator, Cliff Cooker, Stylized Cliff Generator | ~$25 | Geometry Nodes | Overhang and arch types (Desert Cliff) | — |

**Gap:** no dedicated cave generator on Superhive, and nobody markets scale-correct terrain.

Sources: superhivemarket.com/products/true-terrain/ratings, /trueworld, /terrain-mixer-pro, /studio156-procedural-terrain-generator, /geoscapes, /cliff-cooker

## Standalone tools
- **Gaea (QuadSpinner):** Create → Modify → Erode → Texture → Export. Fast erosion with snow, scree and sediment. Data maps (height, slope, curvature, wear, deposits, flow) feed every node's mask input. Seamless tiling, LOD variants. Free to $299. docs.quadspinner.com
- **World Machine:** node graph, tiled builds, macros. New version erodes cliff faces, underhangs and caves — closest precedent for our caves. world-machine.com
- **World Creator:** real-time GPU, terrain stamps (mountains, cliffs, craters), exports to Blender/Unreal/Unity. world-creator.com
- **Houdini heightfields:** layered bedrock/soil, mask by height/slope/facing, hydraulic and thermal erosion, tiling. sidefx.com/docs/houdini/model/heightfields.html
- **Terragen:** render-first; displacement adds cliffs and overhangs on top of a heightfield. planetside.co.uk
- **Unity Terrain Tools:** hydraulic, thermal and wind (dune) erosion, often driven by one "Simulation Scale" control. docs.unity3d.com

## Features worth taking (ranked, Geometry Nodes feasibility)
1. Scale-to-scene with normalized noise — easy. Our headline fix.
2. Landscape types with 4–6 plain-language sliders, advanced hidden — easy. True Terrain's top complaint is the advanced-option learning curve.
3. Data masks (height, slope, curvature, flow, deposits) stored as named attributes — easy to medium. Feeds materials and scatter.
4. Erosion slider: thermal erosion in a repeat zone plus faked hydraulic gullies masked by flow — medium. Real droplet erosion is hard and needs baking.
5. Slope/height auto-material (rock on steep, grass on flat, snow high, sediment low) — easy. Every competitor has it.
6. Volume/SDF stage for caves, overhangs, arches, stalactites, stalagmites — medium to hard. Heightfield → Mesh to SDF Grid → SDF Grid Boolean with cave shapes → Grid to Mesh. Costs memory; loses UVs.
7. Terraces and strata for mesa, canyon, badlands — easy.
8. Preview/final resolution toggle plus Bake — easy.
9. Stamps and curves: river curve, crater, volcano cone, U-shaped glacial valley — medium.
10. Dune wind pass, seamless tiling, heightmap export for Unreal — medium.

## Checked in Blender 5.2 (2026-10-22)
The installed build has the nodes the plan needs: `MeshToSDFGrid`, `SDFGridBoolean`, `SDFGridFillet`, `SDFGridOffset`, `GridToMesh`, `VolumeToMesh`, `GridDilateAndErode`, `GridAdvect`, repeat zones, simulation zones and `Bake`.

## Not verified
- True TERRAIN 5's exact price and internals.
- Gaea 2 tiling/build details (taken from 1.3 docs).
- Official Unreal landscape/PCG docs; World Creator and World Machine prices.

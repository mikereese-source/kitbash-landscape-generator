# Procedural Terrains: what to learn from it

Studied 2026-10-23. Site: https://procedural-terrains.com (v2.0.3). Source: https://github.com/ZyFou/ProceduralTerrains.
**Inspiration only (D49).** We study the ideas and write all of our own code, shaders, presets and art. Nothing is copied.

## Licenses
- **Web app:** MIT, "Copyright (c) 2026 ZyFou". The grant line leaves out the usual "and/or sell", which is one more reason not to copy any of it.
- **Blender plugin:** GPL-3.0-or-later.
- **Textures:** CC0 (Poly Haven, ambientCG).
- **Cursor files:** 15 `.cur` files with no license (possibly Microsoft's). Avoid.

## What it is
- **The app:** a three.js + WebGL2 web app with five ways to start: Procedural (a layer stack), Nodes, Manual (drag landforms onto the ground), Real Terrain (real-world elevation tiles) and Mini Terrain (a diorama on a cut-away base).
- **Engine and plugins:** terrain heights are computed on the GPU. Its Blender and Unity plugins rebuild the terrain natively from a JSON recipe.

## How it works (from its source)
- **Layer stack:** up to 12 layers, each with a type, blend mode, strength, opacity, seed offset, parameters and masks. There are 11 blend modes: add, subtract, multiply, divide, max, min, replace, difference, overlay, carve and flatten. Masks use height, slope or noise. One table generates both GPU code and CPU code, so the two can't drift apart.
- **Node mode:** high-level landform nodes (Mountain, Ridge, Crater, Canyon, Dune Sea, and others) plus Terrace, Stratify and erosion nodes.
- **"Eroded fractal":** each noise layer is weakened where the layers above it are already steep, and bent by their slope. It gives an erosion look with no simulation.
- **Simulated erosion:** water droplets carve, then loose material slides downhill. It runs in a background worker, or on the GPU through WebGPU. The result is stored as a separate height change that can be turned off. It has six presets (Lite, Natural, Mountain, Canyon, Heavy Rain, Dry Thermal) and 192–512 grids.
- **Performance:** heights are computed on the GPU and baked into a texture only when the terrain changes. Moving the camera changes only the level of detail. Shaders compile one at a time, and quality steps down automatically when frames get slow.
- **Artist UX:**
  - Every parameter has a label, range, step, default and a "rebuilds the shader" flag, and the UI is generated from that.
  - 13 stack presets, 8 terrain presets and node templates.
  - Settings search (Ctrl+K), 100-step undo, randomize, and a project file (ZIP + JSON).
- **Materials:** climate-driven biomes plus rock and snow set by slope. Snow lays continuously on top. A Transition Width slider softens edges, and ridge crests are brightened by curvature.
- **Export:**
  - Meshes: GLB/GLTF/OBJ, with skirts and a base.
  - Maps: splat, normal and color maps.
  - Heightmaps: 16-bit RAW/R16, with presets for Unity, Unreal, Godot, Blender and three.js.
- **Shared recipe:** one JSON recipe is rebuilt natively by each plugin. Matching results are kept by tests that compare heights. Anything a plugin can't rebuild is listed in `unsupportedFeatures`.

## Where we are ahead
- **Realism is measured, not guessed.** Each type is checked against real elevation data (Copernicus 30 m, USGS 1 m lidar, LROC Moon), and tests enforce it. They publish no realism checks and almost no performance numbers.
- **Scale-to-scene:** the big shapes stay the same at any size, while fine grain follows real size.
- **Type-first, plain-language picking,** with per-type controls such as crater age and volcano breach.

## Ideas to rebuild our own way
| # | Idea | For | Where it fits |
|---|---|---|---|
| 1 | A typed parameter schema in types.json (label, range, step, default, "advanced") that generates the panel, Reset and the three.js UI | both | Before Project 2. Small. |
| 2 | Blending as a short layer stack: our types as layers, a few blend modes, and height/slope/gradient masks | both | The parked blending feature. Shapes its design. |
| 3 | Cheap erosion look: weaken fine detail on steep ground. GN noise has no slope output, so it needs extra samples (cost to measure) | both | M3 (R4 erosion) |
| 4 | Simulated erosion stored as a toggleable height change, with recipes (Natural, Canyon, Heavy Rain…) scaled to Preview/Final/Ultra. In Blender: a Geometry Nodes Repeat Zone (grid-based water flow plus slope slumping) | both | M3 (R4 erosion). This is our biggest realism gap (the lidar check). |
| 5 | Material rules: rock and snow by slope, continuous snow, a Transition Width slider, curvature on ridges | both | M5 auto-material |
| 6 | "Manual" stamps: drop a mountain, crater or ridge where you want it | both | New, parked |
| 7 | Mini diorama: cut-away base with layered sides, water stopping at the edge (product shots) | both | New, parked |
| 8 | 16-bit heightmap and splat export with engine presets (Unreal R16) | both | M7 / Project 2 |
| 9 | GPU heights baked on change, camera level-of-detail, erosion in a worker or WebGPU | three.js | Project 2 |
| 10 | Height-comparison parity test: same JSON + seed gives matching heights in Blender and three.js | both | Project 2 |

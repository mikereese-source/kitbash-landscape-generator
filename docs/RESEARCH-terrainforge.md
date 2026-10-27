# TerrainForge (kovati.dev): what it is, how it compares, what we take from it (2026-10-27)

Source: the YouTube video "From a Real Valley to a Playable Unreal Level, With Nodes" (6:47, kovati.dev),
its description, and the author's post in the KitBash Discord. Frames: `docs/research/terrainforge/`.
TerrainForge is in preview, will be a paid Unreal plugin, and its agent toolset will be open source.

## What it is
A Gaea-style node graph that lives inside the Unreal editor.
- **Nodes:** any terrain built from nodes, with 18 presets as editable graphs (alpine, volcanic island,
  canyon, dunes, coastal island, layered canyon...). Live preview in under 0.1 s.
- **Process model:** uplift first, then ice, rain and erosion cut it down (frame 04).
- **Real places:** search anywhere on Earth and drag a square; the real elevation arrives as a node.
  1 m lidar in France, Switzerland, the US, the Netherlands and Norway; 30 m Copernicus elsewhere (frames 07–08).
- **Scale:** builds up to 16K. A 4K alpine build takes about 1 min on a laptop GPU, under 3 min on CPU.
  It has a build monitor showing each node's state, time and memory (frame 09).
- **Realism score:** "How Earth-like is it?", scored against 79 real elevation scans. Plain noise scores 64,
  their first showcase 64, the alpine preset today 77 (frame 10).
- **Into Unreal:** imports to a World Partition level with the landscape, 8 paint layers, real Unreal
  water bodies, and masks that PCG scatter graphs read ("forest grows where forest would grow") (frames 11–12).
- **Agents:** 45 MCP tools plus skills for whole flows, e.g. "Make me a 4 km alpine valley with a lake"
  (frames 02, 13).
- **How it was built:** AI agents worked 91 small work packages; 630 tests pass.

## How close it is to what we're doing
Very close in approach, which is a good sign that ours is on the right track:
- realism measured against real elevation data (our T6 30 m, T6b 1 m lidar, Moon check)
- erosion built on uplift and incision (our engine, D53/D54)
- masks feeding scatter (our M3 masks, parked foliage scatter)
- MCP tools for agents (our Cargo MCP plan)

## Where it is ahead of us today
1. **Real places on Earth** as a starting point. We only parked this ("Real terrain" option).
2. **Resolution and speed:** GPU builds up to 16K. Our Ultra is 4K and erosion runs on a 512 grid on the CPU.
3. **Native Unreal output:** World Partition, paint layers, water bodies, PCG masks, in one import.
4. **Flexibility:** a full node graph for technical users. Every step is editable.
5. **Finished look in its marketing:** its renders have materials, grass, water and sky. Ours are still grey
   clay until M5.

## Where we are (or will be) ahead
1. **Artist-first controls:** pick a landscape type and shape it with plain-language sliders. No node graph.
   That suits KitBash's audience (artists building shots and scenes) better than a Gaea clone.
2. **Three apps, one recipe:** Blender, three.js in Cargo as the hub, and Unreal. TerrainForge is Unreal only.
3. **KitBash Kits on the terrain:** scatter and place Kit assets through Cargo and our MCP. Nobody else has the
   Kits.
4. **Hero features as types and styles:** volcano styles with breach, collapse and inner cone, Hero Butte with
   no floor, terraces. Their presets are generic landforms.
5. **Part of the Cargo subscription,** not a separate paid plugin.
6. **Realism per landscape type,** each against its own reference place (13 types, 30 m and 1 m), not one
   score across all terrain.

## What we take from it (proposed, for Mike)
- **Bring "real places" into scope.** Start from a real DEM tile (Copernicus 30 m everywhere, USGS/IGN/swisstopo
  1 m where open), then shape it with our types and controls. We already download and read these tiles for our
  realism checks.
- **Plan resolution and speed for Project 2:** erosion and builds on the GPU (WebGPU compute in three.js, compute
  shaders in Unreal) so we can match 8K–16K. The Blender CPU engine stays the reference.
- **Define the Send-to-Unreal package to land natively:** World Partition landscape, paint layers from our masks,
  Water Body actors from our water level, and our masks exposed to PCG. That is the bar now.
- **Show a realism score to users** (per type, against its real place): it is a strong, simple marketing message,
  and we already measure it.
- **A build progress readout** for long builds (we have "Eroding..." today).
- **MCP tools for the landscape in our Cargo MCP**, with skills for whole flows ("a 4 km alpine valley with a
  lake"), so agents can drive it while the artist keeps the final say.
- **Make the look land:** M5 materials and water shaders, a sky/fog finishing step, and scatter are what will make
  ours look better than this. That is where to put the effort after M3/M4.

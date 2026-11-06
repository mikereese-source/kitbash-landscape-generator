# Engines under the competitors, and whether three.js can carry Project 2 (2026-11-06)

Research only. Extends RESEARCH-positioning.md (competitors, pricing), RESEARCH-terrainforge.md, RESEARCH-materials.md
and RESEARCH.md; it does not repeat their detail. Every fact below was read on 2026-11-06 from the page cited next to
it. "Not verified" means I only saw it in a search snippet, or the page would not open. No logins, trials or paid pages.

---

## 1. Conclusions first

1. **Every serious competitor computes on the GPU now, on the desktop.** Gaea uses CUDA/HIP, World Creator is
   "GPU powered, everything real time", TerrainForge has a "graphics-card module", Houdini erosion runs through OpenCL.
   World Machine is the exception (fast CPU code, GPU still in preview). **None of them runs in a browser.**
2. **The browser tools that exist are demos, not products:** Terrain Studio (three.js, WebGL2) and a few WebGPU erosion
   demos (soilwebgpu runs up to 4096² in Chrome). Nobody ships a browser terrain tool with caves, materials and
   engine export. The space is open.
3. **three.js verdict: yes, three.js is powerful enough, on WebGPU.** Its WebGPU renderer and TSL now have real
   compute shaders, storage buffers, atomics, 3D storage textures, triplanar mapping, volumetric fog and water
   examples. 1k–4k heightfields, GPU marching cubes and instanced rocks are proven in WebGPU by others. The WebGL2
   fallback does **not** run compute, so the generator itself needs WebGPU (about 89% of browsers globally).
4. **The real risk is our erosion, not three.js.** erosion.py uses steps that run one cell after another (pit filling
   with a priority queue, drainage in downhill order, the Braun & Willett implicit solve). These do not port "as-is" to
   GPU threads. They need GPU-friendly rewrites, and the result will look close to Blender's, not identical.
5. **Recommended shape:** everything interactive on the GPU in the browser (shape, masks, preview erosion, caves,
   materials, water, fog, rocks). The exact reference erosion (erosion.py) runs in a Web Worker or on a server for
   the Final build. Send-to-Blender/Unreal sends the recipe plus 16-bit heightmap and mask images, not giant meshes.

## 2. What each competitor is built on

| Tool | App / language | Renderer | Compute | In a browser? | Resolution / speed claims | Source |
|---|---|---|---|---|---|---|
| **Gaea 2/3** (QuadSpinner) | Windows desktop app; language/UI framework **not verified** | Own viewport (not verified further) | **GPU: NVIDIA CUDA 12.5+ or AMD HIP 6.0+**; can run CPU-only; CPU must have AVX2 | No | 16K "experimental, may need very large RAM"; 64–128 GB RAM for complex high-res. Pro builds 16K, tiled to 262,144² (pricing page, in RESEARCH-positioning) | help.quadspinner.com/article/9 |
| **World Creator 3 (2022–2026)** (BiteTheBytes) | Own engine. "C# and Vulkan" is in the company history: **not verified** (page redirects; snippet only) | Own real-time renderer | "First procedural beast to actually tap into GPU power"; "GPU Powered · Everything is Real Time" | No | "Virtually unlimited size"; no number given | bitethebytes.com/docs/world-creator/world-creator-story; /products/world-creator/features |
| **World Creator 4** (EA since 2026-11-03) | Same company engine; Windows x64 and Apple Silicon Mac, Linux "coming soon" | **Path tracer with hardware ray tracing and NVIDIA DLSS**, plus a rasterizer | GPU | No | No number | bitethebytes.com/docs/world-creator/faq/general |
| **World Creator 2** (older, context) | Was built on **Unity**: **not verified** (company history via snippet only) | — | "Fully GPU powered" | No | 8192 × 8192 heightmaps; "unlimited, only limit is your SSD" | 80.lv/articles/world-creator-2-released |
| **TerrainForge** (kovati.dev) | Unreal Engine plugin (language not stated) | Unreal | "Graphics-card module"; every step also runs on CPU and falls back on its own | No | 4K mountain build: under 1.5 min on GPU vs nearly 4 min on CPU (one laptop). Up to 16K (from video, RESEARCH-terrainforge) | kovati.dev/plugins/terrainforge/ |
| **Houdini heightfields** (SideFX) | C++ app, Win/Mac/Linux | Houdini viewport / Karma | Heightfields are "2D volumes". Heightfield Erode uses **OpenCL** (2017 crash reports "OpenCL Exception" on that node; staff suggested forcing the OpenCL CPU device). Current docs don't mention GPU | No | Docs: erosion features depend on heightfield resolution; no number | sidefx.com/docs/houdini/model/heightfields.html; /heightfields/erosion.html; sidefx.com/forum/topic/52656 |
| **Unreal Landscape + PCG** (Epic) | C++ engine | Unreal (Lumen/Nanite etc.) | Landscape on GPU; **PCG GPU execution is Beta**: a few nodes plus a Custom HLSL compute node; CPU↔GPU transfers cost CPU time | Only via Pixel Streaming (video stream) | Largest recommended landscape **8129 × 8129** vertices (1024 components); heightmaps as 16-bit PNG or r16 | dev.epicgames.com: landscape-technical-guide, using-pcg-with-gpu-processing |
| **Instant Terra** (Wysilab) | Windows 7/8/10 64-bit; Python & C# API, C++ live link | Own (not verified further) | Needs a DirectX 11 GPU with 1 GB VRAM. "Uses CPU and GPU dynamically": **not verified** (snippet only) | No | Real time "in the final resolution"; examples of 32k² and 64k² "size limit depends on the version" | wysilab.com/OnLineDocumentation/Overview/Prerequisites.html; wysilab.com |
| **World Machine** (Dragontail Peak 2026) | Native Windows, macOS, Linux | Own 3D viewport | **CPU** (AVX2/SSE "up to 8×"); multithreaded; licence gates CPU cores. GPU compute only in the "Code" device (Lua host), still a development preview | No | Erosion "more than 50× faster" at high res (build 4046 notes) vs "up to 100×" (homepage): two claims differ. Tiled builds "larger than memory: entire continents". Caves and underhangs carved by erosion | world-machine.com; help.world-machine.com/?p=1636 |
| **Terragen 4** (Planetside) | Desktop app | Own renderer | CPU rendering; GPU rendering "in development": **not verified** (forum 503, snippet only) | No | — | planetside forum (did not open) |
| **Blender add-ons** (A.N.T., True TERRAIN, ours) | Python + Geometry Nodes inside Blender | Cycles / EEVEE | **CPU.** Geometry Nodes have "no immediate plans" for GPU (Blender module meeting 2025-04-01); modifiers and GN "mostly rely on the CPU". Our erosion is numpy on CPU at a 512 grid | No | True TERRAIN: no numbers ("terrains in seconds"). Ours: Ultra 4K mesh, erosion 512 | devtalk.blender.org 2025-04-01 meeting; blendernation.com 2025-02-14; superhivemarket.com/products/true-terrain; our erosion.py |
| **Terrain Studio** (open source, 2026) | React + Vite + **three.js (WebGL2)** | three.js | Height, normals, biome colour on GPU | **Yes** | Tile, infinite and planet modes; exports heightmaps or textured meshes for Blender/engines. No erosion mentioned; resolution not stated | gamefromscratch.com/terrain-studio-procedural-terrain-software/ (2026-06-25) |
| **soilwebgpu** (open source demo) | TypeScript, **raw WebGPU + WGSL** (no three.js) | Own | WebGPU compute; needs atomics, so the main model is WebGPU-only; WebGL2 path 27–70× slower | **Yes** (Chrome/Edge) | Up to **4096²**. M2 Max: 1.1 ms/iteration at 256², 14.1 ms at 1024²; 4096² full run about 5–10 min (README contradicts itself) | github.com/taesiri/soilwebgpu |
| **Eulerian erosion** (itch.io demo) | WebGPU compute (no three.js) | Own | Grid-based water + wetness-dependent thermal erosion; avoids atomics | **Yes** | No numbers | sapereaude1490.itch.io/eulerian-erosion |
| **Cinevva "open world in the browser"** (blog) | WGSL compute | Own | Droplet erosion ported to WebGPU; heights as fixed-point ints because WGSL has no float atomics | **Yes** | No numbers | app.cinevva.com/blog/2026-05-13-open-world-browser-part-27-island-and-terrain |
| **Babylon.js erosion sample** | Babylon.js | Babylon | **CPU** (the docs say high settings "can freeze the browser") | Yes | — | doc.babylonjs.com compute shader page |
| **World Labs Marble** (AI worlds) | Cloud AI; viewer is **Spark, a three.js Gaussian-splat renderer** (MIT, by World Labs) | three.js, WebGL2 ("98%+ support") | Generation on their servers | Viewer yes | No numbers on the repo page | github.com/sparkjsdev/spark |
| **Terrain Diffusion** (AI, SIGGRAPH 2026) | Python / PyTorch | — | NVIDIA CUDA strongly recommended; CPU "much slower" | No | Infinite, real-time streaming claimed; 30 m and 90 m models; no benchmarks on the page | github.com/xandergos/terrain-diffusion |

**Not found:** any Unity WebGL or PlayCanvas terrain tool worth listing.

## 3. Is three.js enough? Per need

Current three.js is r187 (GitHub shows "30 Oct"; the year is not printed on the page). `WebGPURenderer` "tries to
use a WebGPU backend… If not, falls back to a WebGL 2 backend" (threejs.org/docs/pages/WebGPURenderer.html). TSL has
`compute()`, `storage()`, `instancedArray()`, `atomicAdd` and the other atomics, `workgroupBarrier()`,
`textureStore()` and `triplanarTexture()` (threejs.org/docs/pages/TSL.html).

**Browser limits that matter** (MDN GPUSupportedLimits defaults; real devices can request more):
2D texture 8192 px, 3D texture 2048 per side, one buffer 256 MB, one storage binding 128 MB. Browsers report limits
in tiers to stop fingerprinting. On web3dsurvey, 92% of devices offer a storage binding of at least 1 GB and 78% a
buffer of about 2 GB, but **we must ask for them at start-up** (survey date and sample size not stated).

Memory sums for us: a 4096² float heightfield is 64 MB, so it fits the defaults; erosion with 6–10 working buffers is
about 0.4–0.6 GB of GPU memory. 8192² is 256 MB per buffer and needs the raised limit or tiles. A 256³ cave volume is
64 MB; 512³ is 512 MB (too big; use bricks or half floats).

| Need | Verdict | Proof (opened) | Where it's weak |
|---|---|---|---|
| **Interactive heightfield generation, 1k–4k** | **Works today** | three.js `webgpu_tsl_procedural_terrain`: noise terrain in the vertex shader, 500×500 grid, live sliders. soilwebgpu runs 4096² in WebGPU. TSL compute writes storage buffers/textures | Shape noise must be rewritten in TSL (no Blender code; GPL). 4k mesh display needs a LOD/clipmap or a GPU-displaced grid, not a 16M-vertex mesh |
| **Masks (height, slope, curvature, flow, wear, deposit, depth)** | **Works today** for height/slope/curvature; **with effort** for flow | Per-cell math is ideal compute work | Flow (drainage area) is a sequential sum in erosion.py; needs a parallel version |
| **GPU erosion** | **Works with effort; risky for exact parity** | soilwebgpu (4096², 14 ms per iteration at 1024² on M2 Max); Eulerian erosion; Cinevva droplets with fixed-point atomics. Interactive stream-power erosion exists in research (Schott et al., TOG 2023, "fast yet accurate approximation of drainage area and flow routing"); **whether it runs on the GPU is not verified** | Our engine is stream-power + priority-flood + downhill-ordered sums. Those are not thread-parallel. GPU versions are approximations: the look will differ from Blender unless we keep erosion.py as the reference. Float atomics don't exist in WGSL (Cinevva) |
| **SDF caves meshed on the GPU (marching cubes / surface nets)** | **Works with effort** | Will Usher, WebGPU marching cubes: 256³ volumes in 31–54 ms, within ~10% of native Vulkan on an RTX 3080. three.js `webgpu_compute_texture_3d` fills a 200³ 3D texture by compute every frame | three.js has no GPU marching-cubes node; we write the scan/compaction ourselves (Usher's approach). Volume size must stay local to the cave (≤256³ per brick). Seam between cave mesh and heightfield needs care |
| **Instanced formations and rocks** | **Works today** | `InstancedMesh` in `webgpu_instance_mesh`; `instancedArray` lets compute place instances (`webgpu_compute_water` moves 100 instanced ducks from a storage buffer). Many more instance/indirect examples exist (`webgpu_struct_drawindirect`, `webgpu_meshlets_instanced`) | Example scale is small (1,000 instances); I found no published three.js number for 100k+ rocks. GPU culling is our job |
| **PBR terrain materials, triplanar, height blend** | **Works today** | TSL `triplanarTexture()`; Cinevva shipped triplanar Poly Haven PBR layers in WebGPU. The procedural-terrain example blends sand/grass/rock/snow by slope and height | Height-blend is custom TSL (small). Triplanar costs 3 fetches per layer (RESEARCH-materials). Blender's procedural noise must be baked to maps first |
| **Water** | **Works today** for lakes/sea; **with effort** for rivers | `webgpu_water`, `webgpu_backdrop_water`, `webgpu_ocean` (reflective WaterMesh with sky), `webgpu_compute_water` (128² simulated ripples) | No FFT ocean or river-flow example found; rivers along our flow mask are custom work |
| **Volumetric fog** | **Works with effort** | `webgpu_volume_lighting`: raymarched fog volume with shadowed light shafts, 12 steps, rendered at 25% resolution and blurred. Also `webgpu_fog_height`, `webgpu_custom_fog_scattering`, `webgpu_volume_cloud` | Cost scales with steps and resolution; low-res fog needs denoising. Not verified on low-end laptops |
| **Export for Blender and Unreal** | **glTF: works today. USD: weak. Heightmaps: with effort** | `GLTFExporter`: .glb, textures, `EXT_mesh_gpu_instancing`. Unreal imports .gltf/.glb through Interchange. Unreal Landscape wants **16-bit PNG or r16** heightmaps | three.js only has a **USDZ** exporter (AR/QuickLook-oriented, textures capped at 1024 by default), not a general USD writer. Browsers can't write 16-bit PNG from a canvas; needs a small encoder. A 4k terrain as a mesh is too big to send: send images + recipe instead |
| **WebGL2 fallback** | **Risky** | The renderer falls back to WebGL2 | three.js's compute examples simply throw "No WebGPU support" (`webgpu_compute_water`, `webgpu_compute_texture_3d`). Storage-buffer attributes are WebGPU-only (three.js docs). A WebGL2 user could get a preview, not the generator |
| **Browser coverage** | **Works today for most pros** | caniuse: 88.6% global. Chrome/Edge 113+ (Win, Mac, ChromeOS); Safari 26 (Mac, iOS, iPadOS, visionOS); Firefox 141 Windows, 145 Apple Silicon Mac | Firefox on Linux and Android not shipped (expected 2026); Chrome on Linux only Intel Gen12+ and NVIDIA on Wayland; Firefox Intel Macs not shipped (gpuweb Implementation Status, edited 2026-10-02) |
| **Library stability** | **Watch** | r186 added `compileComputeAsync()`; r187 changed compute dispatch rules (mixing `count` and `dispatchSize` now throws) | WebGPU API in three.js still moves every release; pin a version |

## 4. Alternatives, briefly

| Option | What it gives | Against it for us |
|---|---|---|
| **three.js WebGPU + TSL** (our plan) | Biggest web 3D community; compute, volume, water, fog examples in the box; glTF export; Spark shows it carries a big AI-world product | Compute is WebGPU-only; API churn; no ready GPU marching cubes or USD export |
| **Babylon.js** | Compute shaders since v5 (WGSL, storage buffers/textures); ocean demo runs ~200–250 compute shaders a frame | Compute also WebGPU-only; its own erosion sample is CPU. Same capability, no reason to switch unless Cargo already uses Babylon |
| **PlayCanvas** | WGSL compute, storage buffers/textures, async readback | Compute WebGPU-only, "not available when using WebGL". Smaller ecosystem for this kind of tool |
| **Raw WebGPU** | Full control; soilwebgpu and Usher's marching cubes are raw WebGPU | We'd rebuild the renderer, materials, fog, water and export three.js already has. Best used for a few kernels, not the whole app |
| **Rust/wgpu → WASM** | One core for browser (WebGPU or WebGL2) and native (Vulkan, Metal, DX12); Firefox's own WebGPU is built on wgpu | Highest engineering cost; Rust skills; still need three.js-level rendering on top. Worth it only if the Unreal plugin should share the exact same compute core |
| **Unreal Pixel Streaming** | Real Unreal quality in a browser over WebRTC, nothing to install | A packaged Unreal app runs on a PC or cloud server per stream: hosting cost per user and latency. Docs give no scaling or latency numbers. Fits a premium "final render" more than an everyday Cargo tool |
| **Server-side generation** | Runs erosion.py as-is (numpy) for exact parity with Blender; no browser limits | Seconds of wait, server cost per build, queueing. Good for the Final build, bad for slider feedback |
| **Pyodide (Python in the browser)** | NumPy 2.4.6 and SciPy 1.18.0 run in Pyodide, so erosion.py could run in a Web Worker on the user's CPU | CPU speed only (fine at 512–1024, slow at 4k); speed not measured |

## 5. Recommended architecture and risks

**In the browser, on the GPU (three.js WebGPURenderer + TSL compute):**
1. **Shape:** the type recipe from types.json, as TSL noise in compute, written to a storage texture (1k Preview,
   2k–4k Final).
2. **Masks:** height, slope, curvature on the GPU every change; flow/wear/deposit from the erosion pass.
3. **Preview erosion:** GPU-friendly versions of our steps (thermal slump, diffusion, multi-pass drainage, iterative
   incision) at 1k, live. Tuned by eye against erosion.py output for each type.
4. **Caves:** SDF in a local 3D texture (≤256³ per brick) → GPU marching cubes or surface nets (Usher's method) →
   formations as instanced meshes placed by compute.
5. **Look:** triplanar PBR with height blend driven by the masks; water plane/WaterMesh; height fog plus a quarter-res
   raymarched volumetric pass; sky.

**Off the GPU:**
6. **Reference erosion:** erosion.py unchanged, in a Web Worker via Pyodide at 512–1024, or on a server for 4k Final.
   Pick after a spike that measures speed and how close the GPU version looks.
7. **Send-to-Blender:** the recipe (type, seed, controls) plus 32-bit/16-bit heightmap and mask images, plus cave glTF.
   The Blender add-on rebuilds from the same recipe. **Send-to-Unreal:** 16-bit PNG heightmap at Unreal-friendly sizes
   (up to 8129² vertices), mask images as paint layers, water level, cave and rock glTF.
8. **No WebGPU:** show a "needs a WebGPU browser" message, or a view-only preview with server-built results.

**Risks, biggest first**
1. **Erosion parity:** GPU erosion won't match Blender's exactly. Mitigation: erosion.py stays the reference;
   the browser is "preview", the Final is the reference engine.
2. **GPU memory at 4k+ and lost devices:** request higher limits at start-up and handle device loss; tile above 4k.
3. **Browser gaps:** Firefox Linux/Android, Linux Chrome on most GPUs, older Intel Macs in Firefox. Probably small for
   KitBash's buyers (Windows/Mac pros), but not measured.
4. **Effort for caves:** GPU marching cubes and the cave/terrain seam are the largest custom pieces.
5. **three.js churn:** compute APIs changed in each of the last two releases. Pin a version; upgrade on purpose.
6. **Export holes:** no USD writer, no 16-bit PNG from canvas: small libraries or our own code.
7. **Licence:** DESIGN.md says the web version is written fresh to stay free of GPL. erosion.py is plain numpy written
   for us; reusing it in Cargo needs a licensing call (see questions).

**Suggested first spike (before any build):** in three.js r187, a 2048² TSL noise heightfield + slope mask + thermal
erosion on GPU + triplanar material + one 256³ cave brick through GPU marching cubes, timed on a mid laptop (Windows
and Mac). Then run erosion.py in Pyodide at 1024 and time it.

## 6. Questions for Mike

1. **What is Cargo's web front-end built on today?** If it already uses three.js (or Babylon), Project 2 should match.
2. **Is "needs a WebGPU browser" acceptable** for the generator, with a view-only fallback for the rest?
3. **Are server builds OK** (a cost per Final build), or must everything run on the user's machine?
4. **Can erosion.py be reused in Cargo?** It's our own numpy code but ships in a GPL add-on; KitBash owns it, so it
   may be dual-licensed. Needs a yes from whoever handles licences.
5. **Which matters more for Final: matching Blender exactly, or higher resolution?** Exact match points to erosion.py
   on a worker/server; resolution points to GPU erosion at 4k–8k.
6. **Is Unreal Pixel Streaming off the table** for Cargo (cost per user), or worth a look for a premium render?

## 7. Not verified

- World Creator 3's "C# and Vulkan" engine and World Creator 2 being built on Unity: company history page redirected;
  seen in search snippets only. World Creator system requirements page returned 404.
- Gaea's app framework and language. Instant Terra's "uses CPU and GPU" claim (snippet only).
- Terragen's CPU-only rendering and GPU plans (forum returned 503; snippet only).
- Houdini: whether current (Houdini 21) Heightfield Erode still uses OpenCL; evidence is 2017 forum crash reports.
- Whether Schott et al.'s interactive stream-power erosion runs on the GPU (project pages and repo don't say).
- PlayCanvas's WebGPU "Beta" label (snippet only; the compute page I opened gives no label).
- Blender's glTF importer support for `EXT_mesh_gpu_instancing` (Blender manual returned 403).
- Unreal's glTF import feature list (page lists formats only). Pixel Streaming hosting cost and latency (not on page).
- three.js r187's release year (GitHub shows "30 Oct" only).
- web3dsurvey limit shares: no date or sample size on the page.
- Any performance number for our own needs: nothing here was measured on KitBash hardware.

## 8. Sources opened (all 2026-11-06)

Competitors
- https://help.quadspinner.com/article/9-what-are-the-system-requirements-for-gaea
- https://www.bitethebytes.com/docs/world-creator/faq/general (via world-creator.com/en/faq.phtml redirect)
- https://www.bitethebytes.com/docs/world-creator/world-creator-story
- https://www.bitethebytes.com/products/world-creator/features
- https://80.lv/articles/world-creator-2-released
- https://kovati.dev/plugins/terrainforge/
- https://www.sidefx.com/docs/houdini/model/heightfields.html
- https://www.sidefx.com/docs/houdini/heightfields/erosion.html
- https://www.sidefx.com/docs/houdini/nodes/sop/heightfield_erode.html
- https://www.sidefx.com/forum/topic/52656/?page=1
- https://dev.epicgames.com/documentation/en-us/unreal-engine/landscape-technical-guide-in-unreal-engine
- https://dev.epicgames.com/documentation/en-us/unreal-engine/using-pcg-with-gpu-processing-in-unreal-engine
- https://wysilab.com/OnLineDocumentation/Overview/Prerequisites.html
- https://www.wysilab.com/
- https://www.world-machine.com/
- https://help.world-machine.com/?p=1636
- https://superhivemarket.com/products/true-terrain
- https://extensions.blender.org/add-ons/antlandscape/
- https://devtalk.blender.org/t/2025-04-01-nodes-physics-module-meeting/39846
- https://www.blendernation.com/2025/02/14/what-in-blender-needs-a-gpu/
- https://gamefromscratch.com/terrain-studio-procedural-terrain-software/
- https://github.com/taesiri/soilwebgpu
- https://sapereaude1490.itch.io/eulerian-erosion
- https://app.cinevva.com/blog/2026-05-13-open-world-browser-part-27-island-and-terrain
- https://github.com/sparkjsdev/spark
- https://github.com/xandergos/terrain-diffusion
- https://h-schott.github.io/p/uplift, https://github.com/H-Schott/StreamPowerErosion,
  https://aparis69.github.io/public_html/projects/schott2023_Uplift.html

Browser platform and three.js
- https://caniuse.com/webgpu
- https://web.dev/blog/webgpu-supported-major-browsers (2025-11-25)
- https://webkit.org/blog/17333/webkit-features-in-safari-26-0/ (2025-09-15)
- https://mozillagfx.wordpress.com/2025/07/15/shipping-webgpu-on-windows-in-firefox-141/
- https://github.com/gpuweb/gpuweb/wiki/Implementation-Status
- https://developer.mozilla.org/en-US/docs/Web/API/GPUSupportedLimits
- https://web3dsurvey.com/webgpu/limits/maxStorageBufferBindingSize
- https://web3dsurvey.com/webgpu/limits/maxBufferSize
- https://threejs.org/docs/pages/WebGPURenderer.html
- https://threejs.org/docs/pages/TSL.html
- https://threejs.org/docs/pages/GLTFExporter.html
- https://threejs.org/docs/pages/USDZExporter.html
- https://threejs.org/examples/files.json
- https://github.com/mrdoob/three.js/releases
- https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/webgpu_tsl_procedural_terrain.html
- https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/webgpu_compute_water.html
- https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/webgpu_volume_lighting.html
- https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/webgpu_ocean.html
- https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/webgpu_compute_texture_3d.html
- https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/webgpu_instance_mesh.html
- https://www.willusher.io/graphics/2024/04/22/webgpu-marching-cubes
- https://dev.epicgames.com/documentation/en-us/unreal-engine/importing-gltf-files-into-unreal-engine

Alternatives
- https://doc.babylonjs.com/features/featuresDeepDive/materials/shaders/computeShader
- https://developer.playcanvas.com/user-manual/graphics/shaders/compute-shaders/
- https://wgpu.rs/
- https://dev.epicgames.com/documentation/en-us/unreal-engine/pixel-streaming-in-unreal-engine
- https://pyodide.org/en/stable/usage/packages-in-pyodide.html

Failed to open (not cited as sources): quadspinner.com/Support/FAQ/Requirements (404), threejs.org/manual/en/webgpurenderer
(404), docs.world-creator.com/german/world-creator-story (redirect), bitethebytes.freshdesk.com specs (404),
animationmagazine.net WC3 article (403), planetside.co.uk forum (503), docs.blender.org (403), developer.blender.org
and projects.blender.org commits (403), webgpureport.org (no static content).

---

## Mike's answers (2026-11-06)

1. **Cargo front end:** not known. KitBash is building **Orbit**, a 3D web viewer Mike believes runs on WebGPU. Check
   Orbit's stack with its team; if it is WebGPU (three.js or otherwise), the generator should share its renderer.
2. **"Needs a WebGPU browser":** acceptable. Cargo is a web app, and the three.js version targets WebGPU only.
3. **Server builds:** Mike read "server" as the user's own computer, which he is happy with. Clarified: the plan is to
   run the exact erosion on the user's computer, in the browser background (Web Worker). KitBash cloud servers are
   not needed for now.
4. **Reuse erosion.py in Cargo:** yes, Mike believes so (it is our own code). Confirm before Project 2 that it holds no
   code from other GPL sources.
5. **Exact Blender match vs resolution:** neither. What matters is that it **looks really good**; small differences
   between Blender, three.js and other DCCs are fine. The Blender add-on is where we solve the hard look problems first,
   then carry them to three.js and the standalone version.
6. **Pixel Streaming:** off the table. Clarified: Pixel Streaming means Unreal running on a KitBash cloud graphics card
   and streamed to the browser as video. That is different from Send-to-Unreal, which opens the result in the user's
   own Unreal on their own graphics card, and stays the plan.

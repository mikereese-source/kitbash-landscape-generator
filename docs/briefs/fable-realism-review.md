# Fable brief: realism review and research (analysis only)

Ready-to-send prompt for a `model: "fable"` subagent (written 2026-11-11, Mike's job). Check `get_usage` first.

---

You are running a review and research session on the realism gaps in the KitBash Landscape Generator. It's a Blender 5.2 Geometry Nodes add-on built from Python, with a three.js / WebGPU version for Cargo to follow. **This is analysis only: make no fixes.** Mike wants your view on the way forward before material checkpoint 2, which is on hold. Say at the top of your report which model and version you are.

**Why:** reviewers found realism gaps in the material spike's checkpoint 1 board (`docs/m7/c183_spike_layers.png`), and Mike agrees with them.

**Where:** read anywhere in the repo. The spike branch is the worktree `E:\Projects\Cowork\apps\lg-m7-spike`, branch `lg-m7-spike`. Write only your outputs there:
- `docs/REVIEW-realism-2026-11.md`
- boards in `docs/m7/` named `c186_realism_*.png`

Commit on that branch. Renders and measurements are fine, through `bash tests/blender.sh` (a shared lock, one Blender at a time, one shot per process). Don't change add-on code.

**Scope: every landscape type, not just Mountains (Mike, 2026-11-11). Caves are out of scope.** The materials made it plain: once they're on, the shapes fall apart. So the main job is a holistic analysis of the models (the shapes) across all 13 types: Hills, Mountains, Dunes, Seabed, Cliffs, Canyon, Mesa, Badlands, Volcanic, Volcano, Glacial, Riverbed and Craters, plus their styles.
- For each type, render it with the spike's material on (the Mountains-tuned material as it is; it's a probe, not the final look) at a wide and a mid shot. Put it beside that type's own references. One board per few types, `c186_realism_<types>.png`.
- Per type, say where the shape gives itself away once it's textured: rounded or blobby forms, missing crags and cliff bands, wrong scale of detail, smooth or noisy surfaces, missing drainage, repeated or stretched patterns, flat masks. Measure where you can: slope histograms, the T6 / T6b numbers, mask ranges.
- Look for causes common to every type (the noise base, the detail cutoff, the erosion model, the mask normalisation, the Preview/High detail) and causes per type. Most of the lift should come from fixing shared causes once.
- The four gaps below are the ones seen on Mountains; check each on every type (for example, flat erosion masks on all of them?).

**Compare against what we already have:**
- the reference boards `docs/m7/c154-c167`, `docs/m5/`, and the type references in `Terrain References` (`E:\Projects\3D\Terrain Generator_Build\Terrain References\`, with sources.json)
- the realism work so far: `docs/REALISM.md`, `PASS1-8.md`, `PHOTO_REVIEW.md`, the T6 / T6b checks against real elevation data (`tests/realism.py`, `lidar_check.py`), decisions D52-D73
- `docs/RESEARCH-materials.md`, `RESEARCH-engines.md`, `RESEARCH-features.md`, `RESEARCH-positioning.md`

**Cover each of these gaps, each with a finding (measured where you can) and a way to close it:**
1. **Close up, the grass is taller than in the reference.** Scale and texel density against c159 E and the close-camera target (256-1024 px/m).
2. **The mountains are rounded domes; the rock faces should be crags.** This is about the Mountains shape, not the material. Find why in `types.json`, the recipe, `nodes.py` and `erosion.py`. Compare against the Mountains references and the lidar checks. What makes real alpine faces craggy (jointed bedrock, frost shattering, cliff bands, talus, plus erosion with hardness) and how competitors get it (Gaea's Rugged / Stratify / Erosion2, World Machine's Thermal plus hardness, World Creator).
3. **The erosion masks barely vary on Mountains:** deposit is 1.0 on 95% of it and wear is 0 on 98%. Find the cause in `erosion.py` (normalisation? thresholds? the sediment model?) and say whether and how it can be fixed.
4. **Texture cost:** one material without normal or roughness maps, yet rock alone takes 18 texture reads, which is heavy for three.js. Answer what to do: fewer triplanar reads (biplanar, stochastic or hash tiling), packed textures (height, roughness and AO in one map), texture arrays, a baked macro colour and normal map for the far range, detail only up close, virtual texturing, and how the per-layer cost adds up.
5. **Research how others reach this level of realism in three.js / WebGPU:** WebGPU terrain demos, three.js TSL terrain shaders, published techniques (Unity and Unreal landscape layer blends, The Witcher 3 and Horizon terrain talks, Far Cry procedural terrain), and browser products. Say what we would need: textures and resolution, shader structure, a read budget per pixel, LOD and geometry (tessellation or displacement, clipmaps), lighting (an HDRI plus a sun, AO, shadows), atmosphere and post (tonemapping, fog, colour grading).

**Mike's decision:** materials are on by default, as in the panel plan. Record that in your recommendations; the change itself happens with the fixes.

**Deliverable: `docs/REVIEW-realism-2026-11.md`:**
- a summary up front;
- one section per gap: finding, evidence, how to close it, size (S / M / L) and risk;
- the texture-cost answer, with a read budget;
- the three.js / WebGPU research with sources;
- a per-type table (type, what falls apart, cause, shared or own, fix, size); the size of the lift to get close to Gaea, World Machine and World Creator, split into shape, erosion, materials, lighting and atmosphere, and three.js;
- your view on the best next steps, and whether to go to checkpoint 2 now, after some fixes, or in a changed form.

Boards (side-by-side with references) where they make a point. Plain short sentences.

**Rules:**
- Follow `docs/CODING.md`'s "Finding and fixing problems": count and measure, and prove causes by switching them off in a scratch copy, not in the add-on.
- Don't download anything new without Mike's OK.
- Commit at clean points. Messages end with `Co-Authored-By: Claude <noreply@anthropic.com>`.

**Report (under 400 words):** model, commits, the top findings per gap, the size of the lift, your recommended next steps, and your view on checkpoint 2.

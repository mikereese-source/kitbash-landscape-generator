# Fable brief: realism review of the landscape models (analysis only)

Ready-to-send prompt for a `model: "fable"` subagent (written 2026-11-11, Mike's job; scope narrowed to the models the same day, D208). Check `get_usage` first.

---

You are running a review and research session on the realism gaps in the **landscape models** (the shapes) of the KitBash Landscape Generator. It's a Blender 5.2 Geometry Nodes add-on built from Python, with a three.js / WebGPU version for Cargo to follow. **This is analysis only: make no fixes.** Say at the top of your report which model and version you are.

**Why:** the material spike on Mountains (`docs/m7/c183_spike_layers.png`) showed that once materials are on, the shapes fall apart. The Mountains are rounded domes where the rock faces should be crags. Mike wants the models closed up first, across every landscape type, before any more material work. Materials get re-evaluated once the models are better (D208). Material checkpoint 2 is on hold.

**Scope:**
- All 13 landscape types and their styles: Hills, Mountains, Dunes, Seabed, Cliffs, Canyon, Mesa, Badlands, Volcanic, Volcano, Glacial, Riverbed and Craters. Caves are out of scope.
- Shapes only. Leave texturing, grass, texture-read cost and shaders out; they come later.
- Judge the shapes in clay under good light, which shows form honestly: the neutral sky HDRI `E:\Projects\3D\Terrain Generator_Build\Materials\polyhaven\hdris\kloofendal_48d_partly_cloudy_puresky_4k.hdr`, a low sun, and cavity or curvature shading.
- The Mountains spike board is evidence of what textures expose. You may use a slope or curvature view as a probe, but build no materials.

**Where:** read anywhere in the repo. Work in the worktree `E:\Projects\Cowork\apps\lg-m7-spike`, branch `lg-m7-spike`, writing only:
- `docs/REVIEW-realism-2026-11.md`
- boards in `docs/m2/` (or `docs/realism/`) named `c186_realism_<types>.png`

Commit on that branch. Renders and measurements go through `bash tests/blender.sh` (a shared lock, one Blender at a time, one shot per process). Don't change add-on code.

**Compare against what we already have:**
- each type's references in `E:\Projects\3D\Terrain Generator_Build\Terrain References\` (with sources.json), and the photo boards in `docs/`
- the realism work so far: `docs/REALISM.md`, `PASS1-8.md`, `PHOTO_REVIEW.md`, `TYPE_SHEET.md`, the T6 / T6b / T6m checks against real elevation data (`tests/realism.py`, `lidar_check.py`, `moon_check.py`, `realism_report.json`, `lidar_report.json`), the waivers at the M2 gate (D57, D73), and decisions D52-D73
- `docs/RESEARCH-features.md` and `RESEARCH-positioning.md` (competitors), `RESEARCH-engines.md` (three.js)

**What to find:**
1. **Per type:** where the shape gives itself away. Rounded or blobby forms, missing crags, cliff bands and joints, the wrong scale of detail (too smooth close up, too noisy far off), missing or weak drainage, stretched or repeated patterns, uniform slopes, no talus or aprons where there should be. Wide and mid shots, each beside the type's references. Measure where you can: slope histograms, the T6 / T6b numbers, roughness by scale, hypsometric curves.
2. **Mountains in depth:** why they come out as domes and not crags. Look in `types.json`, the recipe, `nodes.py` and `erosion.py`. Find what makes real alpine faces craggy: jointed bedrock, frost shattering, cliff bands, talus, erosion that respects rock hardness. Find how Gaea (Rugged, Stratify, Erosion 2), World Machine (Thermal plus hardness) and World Creator get it.
3. **Erosion masks:** on Mountains, deposit is 1.0 on 95% of the surface and wear is 0 on 98%. Check every type. Find the cause in `erosion.py` (scaling, thresholds, the sediment model) and how to fix it. The masks drive the materials later, so they must vary.
4. **Shared causes:** what's common to every type (the noise base, the detail cutoff at Preview and High, the erosion model, mask scaling, resolution). Fixing those once should give most of the lift. Separate them from per-type causes.
5. **three.js and WebGPU, geometry only:** how others generate and erode realistic terrain in the browser (WebGPU compute erosion, GPU noise, clipmaps and LOD, detail by displacement). What our shape fixes would need there, so whatever we pick for Blender also ports.

**Rules:**
- Follow `docs/CODING.md`'s "Finding and fixing problems": count and measure, and prove causes by switching them off in a scratch copy, never in the add-on.
- Don't download anything new without Mike's OK.
- Commit at clean points. Messages end with `Co-Authored-By: Claude <noreply@anthropic.com>`.

**Deliverable, `docs/REVIEW-realism-2026-11.md`:**
- a summary up front;
- a per-type table: type, what falls apart, cause, shared or own, fix, size (S / M / L), risk;
- the Mountains deep dive;
- the erosion mask finding and fix;
- the shared causes and their fixes, in the order that gives the most lift first;
- the three.js geometry notes, with sources;
- the size of the lift to get the models close to Gaea, World Machine and World Creator;
- your view on the best next steps for the models, and when to come back to materials (checkpoint 2 as is, changed, or after which model fixes).

Boards side by side with the references.

**Report (under 400 words):** model, commits, the top findings, the biggest shared causes, the size of the lift, the recommended next steps, and your view on when to return to materials.

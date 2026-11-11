# Fable brief: M7 material spike on Mountains (LG-027, LG-028, LG-029)

Ready-to-send prompt for a `model: "fable"` subagent (written 2026-11-11; Mike chose this as Fable's top task). Before sending:
- run `git worktree add ../lg-m7-spike -b lg-m7-spike` from main, after LG-061 is merged;
- check `get_usage` (both the weekly and the 5-hour window).

It runs in three checkpoints, with Mike's review after each. Send one checkpoint at a time, or tell the agent to stop and report after each.

---

You are building the M7 material spike on the Mountains landscape type in the KitBash Landscape Generator. It's a Blender 5.2 Geometry Nodes add-on built from Python. This is the look that sells the whole tool: a Mountains landscape that looks finished, like a real photo, at a shot distance and up close. Say at the top of your report which model and version you are.

**Where:** the git worktree `E:\Projects\Cowork\apps\lg-m7-spike`, branch `lg-m7-spike`. Never edit the main checkout or Mike's open Blender.

**Blender:** only through `bash tests/blender.sh <args>`: a shared lock, one Blender at a time. Render one shot per process. Renders for review: Cycles and Eevee, with a proper HDRI sky.

**Read first:**
- `docs/CODING.md`
- `docs/tickets/README.md`
- `docs/tickets/LG-027-m7-mountains-layers.md`, `LG-028-m7-material-controls.md`, `LG-029-fog-atmosphere.md`
- `docs/RESEARCH-materials.md`, all of it: conclusions, competitor teardown, quality bar, the build plan in 4.1-4.6, and the risks
- `docs/MATERIALS-needs.md`
- the reference boards `docs/m7/c154-c167`
- decisions D74, D75 (masks stay raw 0-1; the dials live in the material) and D194 (finished look first; the spike uses Poly Haven CC0 plus procedural; the final version uses KitBash 3D materials only)
- PARKING.md rows "Climate switch" and "Fog and atmosphere"

**Textures:** Poly Haven CC0 sets, already downloaded, in `E:\Projects\3D\Terrain Generator_Build\Materials\polyhaven\` (`textures/`, `models/`, `manifest.json`). Use 4K at most (2K where that's the target). Don't download anything new without Mike's OK.

**Lighting (Mike, 2026-11-11):** default lighting is a neutral sky HDRI, Poly Haven `kloofendal_48d_partly_cloudy_puresky` (CC0, 4K), already downloaded to `E:\Projects\3D\Terrain Generator_Build\Materials\polyhaven\hdris\`. Add an HDRI slot to the panel: a file picker that swaps the sky, plus strength and rotation. The default is used when the slot is empty. Set it up as the World only when the artist asks: a "Use Landscape Lighting" button. Never replace an artist's World silently. All review boards use it.

**The masks you drive the look from:** `lg_height`, `lg_slope`, `lg_curvature`, `lg_flow`, `lg_wear`, `lg_deposit`, `lg_depth`, plus `lg_water`. They're on every landscape (test T9). Box or triplanar mapping, since landscapes have no UVs.

**Checkpoint 1, LG-027 layers:**
- Rock, scree, grass or alpine meadow, soil and snow on Mountains, blended by height (not plain crossfades) and driven by the masks.
- Erosion masks colour the drainage: flow, wear and deposit.
- Rock reads as rock on steep faces, scree collects in gullies and at the cliff foot, snow sits on flat high ground and thins on slopes.
- Anti-tiling and macro variation so nothing repeats from a distance.
- Board `docs/m7/c183_spike_layers.png`: a wide shot, a mid shot and a ground close-up, Cycles and Eevee, beside the reference photos for each layer.
- Stop and report.

**Checkpoint 2, LG-028 controls:**
- Snow Line, Snow on Slopes, Rock Angle, Grass Amount, Wetness and Sediment, each with a blend softness. They remap the masks inside the material; the masks stay raw.
- **Basic look controls per layer (Mike, 2026-11-11):** the ones artists expect, so they can change the colour of the grass, foliage, rock, soil and snow. At least colour tint, brightness, saturation, roughness and texture scale per layer. Check what Gaea, World Machine and World Creator offer (`RESEARCH-materials.md` section 1, `RESEARCH-features.md`) and match their basic set; keep it simple.
- A panel section in the same plain style as the Shape controls, with tooltips (T8 checks them). Reset works.
- A test that each control changes its layer.
- Board `c184_spike_controls.png`.
- Stop and report.

**Checkpoint 3, LG-029 fog and atmosphere:**
- Height fog in the valleys, haze with distance, a low cloud layer and sky.
- Presets: morning mist, dusty, stormy.
- Works in Cycles and Eevee.
- Board `c185_spike_atmosphere.png`: the hero shot, Mountains looking finished.
- Stop and report.

**Rules:**
- Every look traces to a reference photo, with side-by-side boards.
- Viewport stays usable: say the Eevee frame time and the Cycles sample time for the hero shot.
- New code lives in `kitbash_landscape_generator/materials.py` and `atmosphere.py`, with small hooks in `__init__.py`.
- Bump `GROUP_VERSION` and rebuild the library only if you change a node group.
- Full suite passes. Commit at every checkpoint. Messages end with `Co-Authored-By: Claude <noreply@anthropic.com>`.
- The main session does the code review and the merge.

**Report at each checkpoint (under 350 words):** model, commits, what the board shows against the references, render times, tests, what you were unsure about.

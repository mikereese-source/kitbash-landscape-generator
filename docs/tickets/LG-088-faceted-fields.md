# LG-088 Spike 2: faceted shape fields (sharp forms in the fields)
Type: spike | Milestone: Model realism | Phase: B2 Model realism | Size: M-L | Priority: P1
Status: todo | Lane: side | Needs Blender: yes | Mike review: yes
Depends on: LG-087 | Blocks: -
Claimed: test T45, GROUP_VERSION 149 (CODING.md: lanes claim their numbers)

## Why
LG-087 (boards c195, c196): cutting High to about 1M triangles keeps its look but adds no sharpness, and taking the grain out changes almost nothing. The softness is in the shape fields (cubic erosion-map reads, smoothstep, blurs), not in the face count or the grain. The scans (Megascans granite cliff: 8 m, about 15k triangles plus a normal map) get their sharpness from faceted form: flat faces meeting at hard creases. Mike, 2026-11-18: run spike 2 next.

## Done when
- Faceted fields tried on Mountains, each switchable, each measured alone and together:
  - plane cells at cliff scale: steep rock broken into cells about 30-120 m, each cell a tilted plane (LG-077's block idea one size up), bevelled joints
  - creases in the main shape: ridged noise (abs) where the rock is hard and high
  - the grain (D47) capped at 5-10 m wavelength in the mesh (LG-087 recommendation; finer detail goes to materials)
- A flat-face measure added to the numbers: the share of steep ground whose normals lie within a few degrees of a local plane, measured on the scans too (or on a Megascans cliff mesh) so it has a real target
- Numbers for each variant at 2 km High: crest sharpness, teeth / horns, over 60 deg, flat-face share, relief; T42 Preview vs High still within 1 point
- Board in `docs/realism/` (next free number, c197) against main and the scans: wide, mid, cliff close-up, clay as c194
- Per-point fields only (ports to three.js as vertex displacement); no new faces; build time at High logged
- Recommendation in the Log: which variants to keep, at what settings, and what becomes a feature ticket. Code stays on the branch until Mike decides; scratch in `docs/realism/LG-088_scratch/`

## Files
- `kitbash_landscape_generator/nodes.py`, `types.json`, `node_groups.blend` (on the branch only, behind type inputs)
- `tests/run_tests.py` (T45, if a variant is kept)
- `docs/realism/` (board), `docs/tickets/LG-088-faceted-fields.md`

## Agent brief
Read LG-087's Log and boards c195, c196, and LG-077 / LG-086's Logs (block cells, crest lift, the teeth counter). Reuse the measuring tools on branches `lg-087-mesh` (`docs/realism/LG-087_scratch/`) and `lg-086-crest` (`lib86.py`). Count before fixing; prove each effect by switching it off. Opus 5.5 at high effort (Fable needs usage credits since 2026-11-18). Save-as-you-go rules: WIP commits, findings in the Log, Blender output to log files, message main before any run over 10 minutes. Also read docs/tickets/README.md and docs/CODING.md.

## Log
- 2026-11-18 created from LG-087's recommendation (Mike: "Then spike 2?")

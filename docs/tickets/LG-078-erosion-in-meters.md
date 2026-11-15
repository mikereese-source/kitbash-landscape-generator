# LG-078 Erosion in meters, the same at Preview and High
Type: feature | Milestone: Model realism | Phase: B2 Model realism | Size: M | Priority: P2
Status: done | Lane: side | Needs Blender: tests only | Mike review: no
Depends on: LG-076 | Blocks: LG-079

## Why
Smoothing steps count in cells, so Preview and High are different landscapes (0.5% vs 1.2% over 60 deg). That breaks D196: each Detail Level keeps the approved quality (review S5).

## Done when
- finish_blur, soften_rounds, floor_width, floor_carve, final_slump and the 3-cell cut in keep_detail scale with grid size (settings read as 'at 512')
- Finishing blur weighted by 1 - hard and skipped on cells steeper than talus_deg
- Preview and High within 1 point of each other on the over-60-deg share on Mountains
- Erosion tests re-based; suite passes; code review before merge

## Files
- `kitbash_landscape_generator/erosion.py`
- `kitbash_landscape_generator/__init__.py` (Preview grid, LG-078)
- `kitbash_landscape_generator/features.py`, `nodes.py`, `node_groups.blend` (cave seam, option B)
- `tests/run_tests.py`

## Agent brief
Read docs/REVIEW-realism-2026-11.md S5. Needed for three.js anyway (other grid sizes).
Also read docs/tickets/README.md (rules every ticket follows) and docs/CODING.md.

## Log
- 2026-11-11 created from the realism review (D209)
- 2026-11-14 (Opus 5.5, branch lg-078-meters) cell counts scale with the grid (ec2ad8c); Mike chose Preview eroding on the 512 grid (exact match, T42: 18.3% both). Full suite 37/38: T30 fails, the cave patch seam goes non-manifold on some landscapes. Probed 6 seeds x 2 sizes: main 0/12 at Preview and High; branch 2-3/12 whatever the change (512 grid, steep skip off, 2 rounds of Preview softening (option A) all still fail), so the seam itself is fragile and any change to the eroded ground moves the failures. Mike: fix the seam itself (option B) next session. Uncommitted WIP committed here (512 grid, mesh_soften 2)
- 2026-11-15 (Opus 5.5) seam fixed (option B, Mike). Counted on the branch: 3 of 12 failing. Switched each cut stage off in a scratch copy: 2 cases came from Triangulate (a ground n-gon and a cave n-gon share a two-edge corner on the cut line; both clipped the same ear, so the edge across it had 3 faces), 1 from the Exact difference (a 4-face edge where the cave floor touched the ground). Fix in `features.py` cut_group: triangulate ground n-gons only, Manifold difference (D93 kept Exact without a recorded reason). CLIP triangulation made it worse (5/12). Probe after: 0 of 20 at Preview, 0 of 8 at High. Preview softening (`mesh_soften`, option A) deleted: it never fixed T30 and broke the exact Preview/High match. CUT_VERSION 10, GROUP_VERSION 146 (LG-077 has 145), library rebuilt. Full suite 38/38 (T30, T42 pass)
- 2026-11-15 seam fix and softening removal committed 0798973
- 2026-11-15 code review (mattpocock-skills:code-review, Sonnet, both axes). Fixed: T42 binned by position, not point order; keep_detail's 3-cell cut scales with the grid; settings take their scale from the grid actually eroded (the 128 quick pass was eroding at 512's scale); one-line comments; board row and Files lists. Glacial probe then failed 1 of 10 (main too: 1 of 10): a ground n-gon touching the cave at two corners a cave edge already joined got that diagonal again (4-face edge). Triangulate now takes only ground n-gons clear of the cave (CUT_VERSION 11, library rebuilt). Probe after: 0 of 80 (Mountains and Glacial 20 each, Cliffs, Mesa, Canyon, Badlands 10 each); T30, T24, T41, T42, T7, T9, T11 pass. Left: the cell-count scaling only runs at 512 and the 128 quick pass (256 stays about 4.6 points steeper even scaled, 2026-11-14), so LG-081 must prove it at other grids; cave n-gons and ground n-gons at the cave rim stay untriangulated (any triangulation there re-cuts a shared edge), shading unchecked; the late smooth_rounds(4) and sea blur still blur steep walls
- 2026-11-15 merged to main with LG-077 (Mike approved). Merge: GROUP_VERSION 147 (LG-077 had 145, this branch 146), library rebuilt. Merged suite 38/39: T42 failed at 29.6% Preview against 33.8% High because LG-077's breakup leaves out the 9 m blocks at Preview on purpose; proven by switching it off in T42 (18.3% against 18.5%), so T42 now measures erosion with the breakup off. T42 and T43 rerun PASS. Status done

# LG-087 Spike: one sharp mesh instead of Detail Levels
Type: spike | Milestone: Model realism | Phase: B2 Model realism | Size: M | Priority: P1
Status: todo | Lane: research | Needs Blender: yes | Mike review: yes
Depends on: - | Blocks: -

## Why
Mike, 2026-11-16: competitors don't ship Preview/High/Ultra geometry ("the geo is the geo"), and his scan references (Megascans, `D:\Megascans\VaultCache\FabLibrary`) read sharper and more realistic, especially hard cliffs, with fewer, well-placed polygons. Proposal: one mesh with a face budget between Preview and High, built to be sharp, with tertiary detail left to materials (D157, D163).
What we know now: each Detail Level samples the same fields on a finer grid (Preview 513 x 513, High 2049 x 2049 points). The erosion map is 512 cells at every level (LG-078), read with cubic interpolation, so big forms can't be sharper than about 8-12 m on a 2 km landscape; High's extra points mostly draw grain noise (D47) and the mesh-scale passes (LG-077 breakup, LG-086 crest lift). Softness comes from smooth fields, not from the face count. Scans look sharp because their forms are faceted (flat faces, hard creases) and their triangles sit where the curvature is.

## Done when
- Test 1, placement alone: today's 2 km Mountains at High (4.2M faces), decimated headless with Blender's Decimate (collapse) to about 1M and 500k faces, rendered in clay beside Preview and High from the same cameras (wide, mid on an inner peak, cliff close-up; neutral sky, low sun as c191/c194); crest sharpness, teeth and over 60 deg measured for each
- Test 2, grain out of the mesh: the same with the grain (D47) turned off in the geometry, to show how much tertiary detail materials would have to carry
- Board in `docs/realism/` (next free number from c195) beside the granite and cliff scan references, with face counts and the numbers
- A one-page recommendation in the ticket Log for Mike: what face budget reads like the scans at shot distance, what faceted generation would add (spike 2), and the costs: masks baked to textures for materials, heightmap export unchanged (it reads the fields), no vertical or overhanging faces in a heightfield (cliff meshes from Kits or SDF, D9), the editing Preview kept only as a proxy, three.js port of the mesher
- No add-on code changes; scratch in `docs/realism/LG-087_scratch/` on the branch (CODING.md), squash merge of the board and Log only

## Files
- `docs/realism/` (board), `docs/tickets/LG-087-one-sharp-mesh.md`
- Scratch scripts only (bake, decimate, render, measure); no files in `kitbash_landscape_generator/`

## Agent brief
Fable job, in its own worktree. Reuse the bake and measure scripts from LG-086's scratch (branch `lg-086-crest`, `docs/realism/lg086_scratch/`: the teeth counter, crest sharpness, clay render setup). Decimate with Blender's Decimate modifier (collapse; also try planar for the flat ground) on the baked mesh, one render per process. Measure on the area the artist sees.
Spike 2 (later, Mike decides after test 1): faceted generation in the fields: plane cells at cliff scale (LG-077's block idea one size up), ridged-noise creases, strata ledges, less blur on steep rock, finer erosion where rock is hard (LG-079, LG-081); then adaptive or feature-aligned triangulation (a first cheap step: flip each quad's diagonal along the ridge direction).
Context from the discussion: close-up hard cliffs need real geometry for their silhouette, so terrain plus Kit cliff meshes on steep zones stays in the picture; materials carry tertiary detail from scan textures, driven by baked masks (M7, LG-083).
Follow the save-as-you-go rules: WIP commits, findings in the Log, Blender output to log files, message main before any run over 10 minutes. Also read docs/tickets/README.md and docs/CODING.md.

## Log
- 2026-11-16 created from Mike's question on one mesh without Detail Levels (discussion in the main session); start when usage resets

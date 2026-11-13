# LG-084 Blender 5.3: jointed rubble missing, cave UV evenness under its limit
Type: bug | Milestone: M5 | Phase: A Cave fixes | Size: M | Priority: P2
Status: todo | Lane: main | Needs Blender: yes | Mike review: no
Depends on: none | Blocks: none

## Why
Mike moved to Blender 5.3 (2026-11-13). The full suite on 5.3 (clean copy of main at 4015a2e, `LG_BLENDER=.../Blender 5.3/blender.exe bash tests/blender.sh ...`) passes 33/35; 5.2 LTS passes 35/35. Development stays on 5.2 LTS until this is fixed.

## Done when
- T35 passes on 5.3: a jointed cave at Rubble 1 builds its rock piles (0 rocks on 5.3, 933 on 5.2)
- T31 passes on 5.3 (88% of the area within 0.5x-2x of the average texel density, want over 90%; 92% on 5.2)
- Full suite passes on 5.2 and 5.3; blender_manifest stays 5.2 minimum

## Files
- `kitbash_landscape_generator/features.py`
- `tests/run_tests.py` (only if a check needs version-aware limits)

## Agent brief
Bisect so far (scratch scripts, nothing changed in the add-on): the shell, formations and water build the same on 5.3 (181,474 shell points). Rubble points are spawned (2,709 with every Delete Geometry muted, same as 5.2). The cause needs two things together: the pile-site thinning (Delete Geometry.010, features.py `spots = t.node('GeometryNodeDeleteGeometry', ...)` near the rubble block) and each layer's rest filter (`kept = ... Selection=h_rests < 0.5` in `h_layer`). With the thinning on, every big rock (layer 1) has h_rests < 0.5 on 5.3 (13 of 13; 1 of 13 on 5.2). Swapping the rest filters for Separate Geometry changes nothing, and Realize Instances' new Preserve Normals (the only 5.3 change listed for a node we use) is not it. Next: store h_reach, h_d, the land raycast's hit and normal, room and pokes per rock before the layer filter, on both versions, and find which differs; suspects are Sample Nearest / Sample Index on the thinned spots (h_pile) and the raycasts. 5.3 release notes: https://developer.blender.org/docs/release_notes/5.3/geometry_nodes/ (open in Chrome; the page blocks automated fetches).
Also read docs/tickets/README.md and docs/CODING.md.

## Log
- 2026-11-13 created: 5.3 suite 33/35 (T31, T35); bisect notes above

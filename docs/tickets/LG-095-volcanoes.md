# LG-095 Volcanoes: Volcano erosion, Caldera rim, Volcanic cones
Type: feature | Milestone: Model realism | Phase: B2 Model realism | Size: M | Priority: P2
Status: todo | Lane: side | Needs Blender: yes | Mike review: yes
Depends on: LG-094 (Cinder) | Blocks: LG-082

## Why
Third of the four tickets LG-082 was split into (Mike, 2026-11-28). Review section 3: Volcano is a lathe-turned cone with faint even gullies, no ravines that deepen downhill and no flow ridges; Caldera walls reach 29 deg at the 99th percentile against a real 63. Volcanic cones are all one size and profile, lobe edges are too steep (over 45 deg 2.7%, real 0.3%) and flow tops too lumpy (flat 11%, real 25%).

## Done when
- Strato and Collapsed run the erosion engine with radial drainage (review: incision about 1.0, channel 0.0002), so ravines deepen downhill, without losing the cone
- Caldera gets a hard rim with the bedrock breakup
- Volcanic: cone size varies (0.4 to 1.6 times, from a hash), some cones breached; lobe edges eased to 20 to 25 deg; flow tops flatter
- Clay renders of Shield and Collapsed
- Each type measured against main and its real 1 m lidar window on the 1 m grid (LG-077's m77 measures); board per type beside its references; Mike signs off each type; every other type unchanged (its tests equal main); new test (claim the next free T) at the measured board values; build and re-evaluation time measured; suite passes; code review

## Files
- `kitbash_landscape_generator/types.json`, `nodes.py`, `node_groups.blend` (claim the next GROUP_VERSION), `erosion.py`, `__init__.py`
- `tests/run_tests.py`

## Agent brief
Read REVIEW-realism-2026-11.md section 3 (Volcanic, Volcano) and S4, and LG-077's breakup code.
Also read docs/tickets/README.md (rules every ticket follows) and docs/CODING.md.

## Log
- 2026-11-28 created: LG-082 split into four tickets (Mike: "Yes, as drafted")

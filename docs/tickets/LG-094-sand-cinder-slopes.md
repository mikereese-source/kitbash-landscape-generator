# LG-094 Sand and cinder slopes: Dunes, Cinder
Type: feature | Milestone: Model realism | Phase: B2 Model realism | Size: S | Priority: P2
Status: todo | Lane: side | Needs Blender: yes | Mike review: yes
Depends on: LG-080 | Blocks: LG-082

## Why
Second of the four tickets LG-082 was split into (Mike, 2026-11-28). Loose sand and cinder rest at about 32 to 34 deg. Review section 3: dune slip faces are soft (99th percentile 23 deg, real 31), Star dunes have 19% over 45 deg, steeper than sand can stand, and the Cinder crater rim is 51 deg against a real 33.

## Done when
- A repose pass at about 33 deg on Dunes (Crescent, Linear, Star) and Cinder, reusing LG-080's talus code where it fits
- Crescent still matches its lidar; slip faces sharpen toward 31 deg; Star loses its over-steep ground; Cinder's rim comes down to about 33 deg
- Clay renders of Linear and Star dunes
- Each type measured against main and its real 1 m lidar window on the 1 m grid (LG-077's m77 measures); board per type beside its references; Mike signs off each type; every other type unchanged (its tests equal main); new test (claim the next free T) at the measured board values; build and re-evaluation time measured; suite passes; code review

## Files
- `kitbash_landscape_generator/types.json`, `erosion.py` or `nodes.py`, `node_groups.blend` (if the tree changes), `__init__.py`
- `tests/run_tests.py`

## Agent brief
Read REVIEW-realism-2026-11.md section 3 (Sand Dunes, Volcano) and S6, and LG-080's ticket and talus code.
Also read docs/tickets/README.md (rules every ticket follows) and docs/CODING.md.

## Log
- 2026-11-28 created: LG-082 split into four tickets (Mike: "Yes, as drafted")

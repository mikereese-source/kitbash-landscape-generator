# LG-096 Gentle types: Hills, Riverbed, Seabed, Crater, Cliffs headland
Type: feature | Milestone: Model realism | Phase: B2 Model realism | Size: M | Priority: P2
Status: todo | Lane: side | Needs Blender: yes | Mike review: yes
Depends on: - | Blocks: LG-082

## Why
Fourth of the four tickets LG-082 was split into (Mike, 2026-11-28). Review section 3: Rolling Hills is one swell at 2 km where the Palouse packs dozens; Riverbed is a few ditches on a plate with banks too steep (99th percentile 24 deg, real 11) and no bars; Seabed reef patches have no ledges; Crater's small pits are all one crisp bowl; Coastal Cliffs' land behind the bluff is a plate and the bluff face is rounded scallops.

## Done when
- Hills: hill count scales with size; swales join
- Riverbed: braids from crossing channel fields, low bars between them, `bank_deg` 25 to about 12
- Seabed: bedrock breakup on the reef mask only
- Crater: the small pit layer gets the same age spread as the big craters
- Cliffs: stronger headland relief behind the bluff and rills down the face
- Each type measured against main and its real 1 m lidar window on the 1 m grid (LG-077's m77 measures); board per type beside its references; Mike signs off each type; every other type unchanged (its tests equal main); new test (claim the next free T) at the measured board values; build and re-evaluation time measured; suite passes; code review

## Files
- `kitbash_landscape_generator/types.json`, `nodes.py`, `node_groups.blend` (claim the next GROUP_VERSION), `__init__.py`
- `tests/run_tests.py`

## Agent brief
Read REVIEW-realism-2026-11.md section 3 (Rolling Hills, Riverbed, Seabed, Cratered Surface, Coastal Cliffs) and S4. One type at a time, each board to Mike.
Also read docs/tickets/README.md (rules every ticket follows) and docs/CODING.md.

## Log
- 2026-11-28 created: LG-082 split into four tickets (Mike: "Yes, as drafted")

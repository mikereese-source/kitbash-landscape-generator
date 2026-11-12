# LG-082 Per-type realism pass (all 13 types)
Type: feature | Milestone: Model realism | Phase: B2 Model realism | Size: L | Priority: P2
Status: todo | Lane: main | Needs Blender: yes | Mike review: yes
Depends on: LG-077, LG-079, LG-080 | Blocks: LG-083

## Why
Each type keeps its own tells after the shared fixes (review section 3 and S8).

## Done when
- In this order: Glacial walls and Canyon benches (with the breakup), Hills count, Dunes and Cinder repose angle (with talus), Volcano erosion, Riverbed braids, Volcanic cone variety, Cliffs headland, Seabed reef, Crater pits
- Clay renders for the six styles judged only from hillshades (Linear and Star dunes, Hero Butte, Mounds, Shield, Collapsed)
- Boards beside each type's references; T6/T6b numbers logged; Mike signs off per type

## Files
- `kitbash_landscape_generator/types.json`
- `kitbash_landscape_generator/nodes.py`
- `tests/run_tests.py`

## Agent brief
Read docs/REVIEW-realism-2026-11.md sections 3 and 7 (S8). Split into one ticket per type when it starts.
Also read docs/tickets/README.md (rules every ticket follows) and docs/CODING.md.

## Log
- 2026-11-11 created from the realism review (D209)

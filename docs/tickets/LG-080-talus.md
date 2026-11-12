# LG-080 Talus as a landform and the lg_talus mask (plus mask fix B)
Type: feature | Milestone: Model realism | Phase: B2 Model realism | Size: M | Priority: P2
Status: todo | Lane: side | Needs Blender: yes | Mike review: yes
Depends on: LG-075, LG-078 | Blocks: LG-082, LG-083

## Why
No type has talus cones or aprons under its walls, and scree materials need a mask (review S6). Mask fix B (cut and fill accumulated over the passes) goes in here.

## Done when
- Thermal shed from hard steep cells, stopping at 33-36 deg, not blurred after
- Shed and received totals kept; `lg_talus` stored beside the other masks (alpha channel of the erosion image)
- Mask fix B: wear and deposit from accumulated cut and fill
- Cones under gullies on Mountains, Mesa, Cliffs; Mesa apron code removed if redundant
- Board beside the Svalbard talus reference; T9 lists lg_talus; suite passes; code review

## Files
- `kitbash_landscape_generator/erosion.py`
- `kitbash_landscape_generator/nodes.py`
- `kitbash_landscape_generator/node_groups.blend`
- `tests/run_tests.py`

## Agent brief
Read docs/REVIEW-realism-2026-11.md S6 and the mask fix B lines in the appendix. `slump()` already moves the material; add the counters. Fixed stencil, so it ports to a compute shader.
Also read docs/tickets/README.md (rules every ticket follows) and docs/CODING.md.

## Log
- 2026-11-11 created from the realism review (D209)

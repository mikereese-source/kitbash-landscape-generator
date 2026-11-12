# LG-078 Erosion in meters, the same at Preview and High
Type: feature | Milestone: Model realism | Phase: B2 Model realism | Size: M | Priority: P2
Status: todo | Lane: side | Needs Blender: tests only | Mike review: no
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
- `tests/run_tests.py`

## Agent brief
Read docs/REVIEW-realism-2026-11.md S5. Needed for three.js anyway (other grid sizes).
Also read docs/tickets/README.md (rules every ticket follows) and docs/CODING.md.

## Log
- 2026-11-11 created from the realism review (D209)

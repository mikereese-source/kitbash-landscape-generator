# LG-075 Erosion masks that vary (mask fix A)
Type: feature | Milestone: Model realism | Phase: B2 Model realism | Size: S | Priority: P1
Status: ready | Lane: side | Needs Blender: tests only | Mike review: no
Depends on: - | Blocks: LG-076

## Why
On Mountains deposit is 1 on 87-95% of the surface: the masks measure the engine's uplift, not erosion. Six of ten eroded types are over half saturated. The masks drive every material later (D208; review S3).

## Done when
- `erosion_masks()` uses fix A: height change minus fill, broad lift removed with a blur of 5% of the width, scaled by the 97th percentile
- Every eroded type and style: deposit = 1 and wear = 0 each under 20% of the surface; numbers in the log
- No node change, no look change to the shape
- Test in `tests/run_tests.py` that wear and deposit span 0..1 on Mountains, Canyon, Badlands
- Board in `docs/realism/`: masks before and after on three types
- Code review: mattpocock-skills:code-review before merge

## Files
- `kitbash_landscape_generator/erosion.py`
- `tests/run_tests.py`

## Agent brief
Read docs/REVIEW-realism-2026-11.md sections 5 and 7 (S3) and the appendix (fix A code). Fix B (accumulated cut and fill) comes with LG-080. `render_m7.py` picks its close-up with `lg_deposit > 0.9`: note it for LG-083, don't change it here.
Also read docs/tickets/README.md (rules every ticket follows) and docs/CODING.md.

## Log
- 2026-11-11 created from the realism review (D209)

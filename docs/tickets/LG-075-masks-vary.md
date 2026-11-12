# LG-075 Erosion masks that vary (mask fix A)
Type: feature | Milestone: Model realism | Phase: B2 Model realism | Size: S | Priority: P1
Status: done | Lane: side | Needs Blender: tests only | Mike review: no
Depends on: - | Blocks: LG-076

## Why
On Mountains deposit is 1 on 87-95% of the surface: the masks measure the engine's uplift, not erosion. Six of ten eroded types are over half saturated. The masks drive every material later (D208; review S3).

## Done when
- `erosion_masks()` uses fix A: height change minus fill, broad lift removed with a blur of 5% of the width, scaled by the 97th percentile
- Every eroded type: deposit = 1 and wear = 1 each under 20% of the surface, and over 10% of it in 0.1-0.9 (wear = 0 is right wherever ground was filled, so that end isn't capped); numbers in the log
- No node change, no look change to the shape
- T9 checks it on every eroded type; the erosion.py self-check fails on the old code (68% saturated) and passes on the new (3%)
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
- 2026-11-12 fix A in erosion_masks (pit fill and broad lift taken out, 97th-percentile scale with a 0.5% relief floor); T9 extended; worktree lg-075-masks
- 2026-11-12 0ca174c committed; T9, T5, T7, T11, T39 pass. Preview, % of surface with deposit = 1 / wear = 1 / either mask in 0.1-0.9, main -> fix: hills 42.5 / 0.0 / 33 -> 0.2 / 1.4 / 63; mountains 93.5 / 0.7 / 4 -> 0.4 / 1.2 / 67; cliffs 1.3 / 12.8 / 24 -> 0.0 / 3.0 / 31; canyon 47.7 / 4.7 / 34 -> 0.2 / 2.4 / 68; mesa 83.8 / 5.4 / 8 -> 0.0 / 2.0 / 29; badlands 42.1 / 33.8 / 13 -> 1.1 / 1.8 / 74; glacial 86.7 / 0.0 / 9 -> 0.1 / 1.5 / 61; riverbed 0.4 / 3.3 / 66 -> 0.0 / 1.9 / 48. Board: c186_realism_masks.png (the review's fix A). Code review next
- 2026-11-12 code review (mattpocock, standards + spec). Fixed: the lift was measured on the padded grid, so the visible edges kept a deposit band; change_mask() now runs on the cropped area in _compute_erosion (edge/inside deposit, Mountains Preview 2.01 -> 1.15, High 1.69 -> 1.04, Hills 1.56 -> 0.89); T9's 0.1-0.9 check is a union with a 'want' message; one-line comments. Every eroded style checked (Mesa Field/Hero, Badlands Wall/Mounds) and Mountains at High: deposit = 1 at most 1.0%, wear = 1 at most 2.4%, 26-85% in 0.1-0.9. Known leak left for LG-080 (fix B): the Mesa apron and the floor slope still count as deposit. T9, T5, T7, T11, T29, T39 pass. Board docs/realism/c188_lg075_masks.png: rows top to bottom glacial, canyon, mountains; columns main deposit | main wear | fix deposit | fix wear (white = 1). Done-when edits need Mike's OK: 'wear = 0 under 20%' can't hold (wear is 0 wherever ground was filled), so the check is wear = 1 under 20% plus a 0.1-0.9 band -> review
- 2026-11-12 Mike approved the Done-when change and the merge; merged into main -> done
- 2026-11-12 Lessons: (1) a quick numpy self-check run against the old and new code (68% -> 3% saturated) proved the test catches the bug before Blender ran; (2) the spec review caught what my own measure missed: masks computed on the padded grid. Any mask or stat should be measured on the area the artist sees; (3) changing Done-when lines mid-ticket needs Mike's OK first, not a note after

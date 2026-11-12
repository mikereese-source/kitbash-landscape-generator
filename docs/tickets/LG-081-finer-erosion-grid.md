# LG-081 Finer erosion grid at High and Ultra
Type: perf | Milestone: Model realism | Phase: B2 Model realism | Size: M | Priority: P3
Status: todo | Lane: side | Needs Blender: tests only | Mike review: no
Depends on: LG-077, LG-078, LG-079, LG-080 | Blocks: -

## Why
The 512 grid limits detail at High and Ultra. Gaea and World Machine build at higher resolutions (review S7).

## Done when
- Vectorised or compiled priority flood first (fill and breach take 6.7 s at 512 today)
- 1024 at High, 2048 at Ultra, or a short second erosion at 1024 from the upsampled 512
- Timings before and after in one session; suite passes; code review

## Files
- `kitbash_landscape_generator/erosion.py`
- `kitbash_landscape_generator/__init__.py`
- `tests/run_tests.py`

## Agent brief
Read docs/REVIEW-realism-2026-11.md S7 and RESEARCH-engines.md (the sequential pit fill is the known three.js risk). Do last; most of the gain comes from LG-077.
Also read docs/tickets/README.md (rules every ticket follows) and docs/CODING.md.

## Log
- 2026-11-11 created from the realism review (D209)

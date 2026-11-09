# LG-023 6.3b Heightmap and mask export
Type: feature | Milestone: M6 6.3b | Phase: E M6 | Size: S | Priority: P2
Status: todo | Lane: side | Needs Blender: tests only | Mike review: no
Depends on: LG-021, LG-022 | Blocks: LG-026, LG-042

## Why
Cheapest table-stakes gap; needed for every engine handoff (RESEARCH-features.md, D198).

## Done when
- 16-bit PNG/EXR at Unreal sizes + Unity RAW
- Masks as splat images
- Recipe JSON
- New test T34; all pass

## Files
- `kitbash_landscape_generator/export.py (new)`
- `kitbash_landscape_generator/__init__.py`
- `tests/run_tests.py`

## Agent brief
Follow docs/PACKAGE.md exactly.
Also read docs/tickets/README.md (rules every ticket follows).

## Log
- 2026-11-08 created (D201)

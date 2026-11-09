# LG-041 Heightmap and real-elevation import
Type: feature | Milestone: M8 | Phase: G M8 | Size: S-M | Priority: P2
Status: todo | Lane: side | Needs Blender: tests only | Mike review: yes
Depends on: LG-022 | Blocks: LG-045

## Why
Import a heightmap as base or stamp; also reads Copernicus .tif (D82 un-parked, D198).

## Done when
- PNG/EXR/.tif import scaled to metres
- Test
- Code review: `mattpocock-skills:code-review` against this ticket before merge; findings fixed or made tickets; logged in TICKETS.md Code reviews (D202)

## Files
- `kitbash_landscape_generator/heightmap_import.py (new)`
- `kitbash_landscape_generator/__init__.py`
- `tests/run_tests.py`

## Agent brief
Reuse the loader in tests/realism.py:65.
Also read docs/tickets/README.md (rules every ticket follows).

## Log
- 2026-11-08 created (D201)
- 2026-11-08 code review step added (D202)

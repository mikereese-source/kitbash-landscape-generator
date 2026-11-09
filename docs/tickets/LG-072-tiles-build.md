# LG-072 Multi-tile landscapes: tiles and seams
Type: feature | Milestone: M7b | Phase: F2 Multi-tile | Size: L | Priority: P2
Status: todo | Lane: main | Needs Blender: yes | Mike review: yes
Depends on: LG-071 | Blocks: LG-073

## Why
Build the tile grid: each cell evaluates its own type and controls, heights blend across soft seams.

## Done when
- 2x2 with four different types builds; seams read natural (board)
- Per-tile controls and Randomize
- Presets save the whole layout
- Tests: shapes at each tile match the single-tile build away from seams

## Files
- `kitbash_landscape_generator/nodes.py`
- `kitbash_landscape_generator/__init__.py`
- `kitbash_landscape_generator/types.json`
- `tests/run_tests.py`

## Agent brief
Follow docs/PLAN-tiles.md.
Also read docs/tickets/README.md (rules every ticket follows).

## Log
- 2026-11-09 created (D203)

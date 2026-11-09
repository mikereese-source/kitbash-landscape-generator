# LG-073 Multi-tile landscapes: erosion across tiles
Type: feature | Milestone: M7b | Phase: F2 Multi-tile | Size: M | Priority: P2
Status: todo | Lane: main | Needs Blender: yes | Mike review: yes
Depends on: LG-072 | Blocks: LG-074

## Why
Erosion run once over the combined landscape is what makes tiles read as one place (flows running between two volcanoes).

## Done when
- Erosion over the whole grid; channels cross seams
- Build time measured for 1, 4 and 9 tiles; within the agreed budget
- T11/T12 style checks for a tiled landscape

## Files
- `kitbash_landscape_generator/erosion.py`
- `kitbash_landscape_generator/nodes.py`
- `tests/run_tests.py`

## Agent brief
erosion.py already runs on the whole grid; the work is feeding it the blended heights and the per-tile recipes (hardness etc.).
Also read docs/tickets/README.md (rules every ticket follows).

## Log
- 2026-11-09 created (D203)

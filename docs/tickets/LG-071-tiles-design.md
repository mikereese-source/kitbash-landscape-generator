# LG-071 Multi-tile landscapes: design
Type: docs | Milestone: M7b | Phase: F2 Multi-tile | Size: S | Priority: P2
Status: todo | Lane: main | Needs Blender: no | Mike review: yes
Depends on: LG-035 | Blocks: LG-072

## Why
Competitors let artists build one landscape from several parts: two volcanoes side by side, mountains next to a plain (Mike, 2026-11-09, World Creator volcano shot). Start simple, after the single tile looks right.

## Done when
- docs/PLAN-tiles.md: grid layouts (1x2, 2x2, 3x3), each cell its own type, preset, controls and seed; soft noisy seams with a Blend Width; erosion once over the whole landscape; build-time cost; UI (a tile list like the landscape list)
- Recipe JSON as a list of tiles, matching docs/PACKAGE.md (LG-022)
- Mike approves

## Files
- `docs/PLAN-tiles.md (new)`

## Agent brief
Read PARKING rows: Landscape blending, Four-quadrant blend, Volcano chain, Surroundings for hero features, Gradient control. Not the same as huge-world tiling past 4K (Project 3).
Also read docs/tickets/README.md (rules every ticket follows).

## Log
- 2026-11-09 created (D203)

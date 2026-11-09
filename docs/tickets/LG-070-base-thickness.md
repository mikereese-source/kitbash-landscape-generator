# LG-070 Base thickness (solid sides)
Type: feature | Milestone: M6 6.4c | Phase: E M6 | Size: S | Priority: P2
Status: ready | Lane: main | Needs Blender: yes | Mike review: yes
Depends on: none | Blocks: none

## Why
Other terrain tools show the landscape as a solid slab with thick sides, which reads better than a thin sheet (Mike, 2026-11-09, World Creator beach shot; PARKING 'Mini diorama').

## Done when
- Base on/off and Depth control: the border pushed down to a flat base, bottom closed, watertight
- Masks unaffected; heightmap export (LG-023) and the Unreal handoff leave the base out
- Water level stops at the base edge
- Layered rock material on the sides comes later in M7 (LG-031 area)
- Test

## Files
- `kitbash_landscape_generator/nodes.py`
- `kitbash_landscape_generator/__init__.py`
- `tests/run_tests.py`

## Agent brief
Geometry only. Pushing the boundary down plus a bottom cap; check Bake to Mesh (T29) keeps it.
Also read docs/tickets/README.md (rules every ticket follows).

## Log
- 2026-11-09 created (D203)

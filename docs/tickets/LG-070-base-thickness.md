# LG-070 Base thickness (solid sides)
Type: feature | Milestone: M6 6.4c | Phase: E M6 | Size: S | Priority: P2
Status: done | Lane: side | Needs Blender: yes | Mike review: yes
Depends on: none | Blocks: none

## Why
Other terrain tools show the landscape as a solid slab with thick sides, which reads better than a thin sheet (Mike, 2026-11-09, World Creator beach shot; PARKING 'Mini diorama').

## Done when
- Base on/off and Depth control: the border pushed down to a flat base, bottom closed, watertight
- Masks unaffected; heightmap export (LG-023) and the Unreal handoff leave the base out
- Water level stops at the base edge
- Layered rock material on the sides comes later in M7 (LG-031 area)
- Test
- Code review: mattpocock-skills:code-review against this ticket before merge

## Files
- `kitbash_landscape_generator/nodes.py`
- `kitbash_landscape_generator/__init__.py`
- `kitbash_landscape_generator/presets.py`
- `tests/run_tests.py`

## Agent brief
Geometry only. Pushing the boundary down plus a bottom cap; check Bake to Mesh (T29) keeps it.
Also read docs/tickets/README.md (rules every ticket follows).

## Log
- 2026-11-09 created (D203)
- 2026-11-09 a210071 built in worktree lg-070-base-thickness: Base + Base Depth (20 m), T34; library rebuild and tests still to run (no Blender) -> review
- 2026-11-09 a5273aa code-review fixes: T34 order-free, bake + water checks, why-comments, Base Depth max; lane side
- 2026-11-09 code review done (logged in TICKETS.md), fixes a5273aa; tests found the bottom points off level, snapped flat (1db679d, GROUP_VERSION 144); merged into main (1d3f8c0); full suite 31/31; board docs/m5/c175_base_thickness.png. Waiting on Mike's review
- 2026-11-11 Mike signed off -> done
- 2026-11-11 Mike: make Base on by default. Uncommitted in the main checkout: __init__.py base default=True; run_tests.py add() turns base off for grid tests, T34 checks the default. Full suite not yet run (paused); run it, then commit
- 2026-11-12 full suite 35/35 with Base on by default; committed

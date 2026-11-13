# LG-043 Checker-note fixes
Type: bug | Milestone: M8 | Phase: G M8 | Size: S | Priority: P3
Status: done | Lane: side | Needs Blender: tests only | Mike review: no
Depends on: none | Blocks: LG-045

## Why
Old checker notes: list index drift (store a pointer), Fit to Selection ignores rotation/scale, refresh timer guard on disable, quick scale keeps Width:Depth at the 1 m minimum (PARKING).

## Done when
- Each fixed with a test or check
- Code review: `mattpocock-skills:code-review` against this ticket before merge; findings fixed or made tickets; logged in TICKETS.md Code reviews (D202)

## Files
- `kitbash_landscape_generator/__init__.py`
- `tests/run_tests.py`

## Agent brief
Small, in __init__.py; can run beside main-lane work.
Also read docs/tickets/README.md (rules every ticket follows).

## Log
- 2026-11-08 created (D201)
- 2026-11-08 code review step added (D202)
- 2026-11-11 built by Opus 5.5 in main: the picked landscape is held by reference (scene.lg_picked), Fit to Selection measures in the landscape's own axes and scale, timers unregistered on disable, quick scale clamps one factor so Width:Depth survives the 1 m / 100 km limits. New T38; T3/T18/T19/T26 pass. Code review still to run
- 2026-11-11 code review done (logged); fixes: old-file fallback, zero-scale guard, scaled-landscape fit tested. Left: no test for the timer guard; the list's highlighted row can still drift after a removal (cosmetic)
- 2026-11-13 Mike approved (board panel check / skim) -> done

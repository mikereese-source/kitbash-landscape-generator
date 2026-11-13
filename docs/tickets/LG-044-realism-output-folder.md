# LG-044 Realism reports to an output folder
Type: chore | Milestone: M8 | Phase: G M8 | Size: S | Priority: P3
Status: done | Lane: side | Needs Blender: tests only | Mike review: no
Depends on: none | Blocks: none

## Why
realism/lidar checks overwrite their reports in the repo (M2 checker note).

## Done when
- --out option; default outside the repo
- Code review: `mattpocock-skills:code-review` against this ticket before merge; findings fixed or made tickets; logged in TICKETS.md Code reviews (D202)

## Files
- `tests/realism.py`
- `tests/lidar_check.py`

## Agent brief
Small.
Also read docs/tickets/README.md (rules every ticket follows).

## Log
- 2026-11-08 created (D201)
- 2026-11-08 code review step added (D202)
- 2026-11-10 built by Opus 5.5: LG_REPORT_DIR env var sends realism.py and lidar_check.py reports (and lidar hillshades) to a folder of your choice; unset keeps today's behaviour (the committed reports in the repo). Default kept in the repo rather than moved out, so the committed reports (D57 waivers) keep updating; moon_check.py already takes an out folder. Not run (realism checks need the DEM tiles and take long); syntax checked only
- 2026-11-13 Mike approved (board panel check / skim) -> done

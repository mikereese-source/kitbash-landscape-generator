# LG-007 Preset save location
Type: feature | Milestone: M5 | Phase: A Cave fixes | Size: S | Priority: P2
Status: ready | Lane: side | Needs Blender: tests only | Mike review: yes
Depends on: none | Blocks: none

## Why
Artists need to see and pick where presets save (Mike, 2026-11-06, PARKING).

## Done when
- First Save Preset opens a folder dialog starting next to the .blend
- Later saves go straight there until the folder icon is clicked
- Folder remembered per .blend file
- Preset list shows the 5 most recently saved
- T25 extended; 30/30
- Code review: `mattpocock-skills:code-review` against this ticket before merge; findings fixed or made tickets; logged in TICKETS.md Code reviews (D202)

## Files
- `kitbash_landscape_generator/presets.py`
- `kitbash_landscape_generator/__init__.py`
- `kitbash_landscape_generator/caves.py`
- `tests/run_tests.py`

## Agent brief
Read PARKING row 'Preset save location' for the full spec. No features.py changes, so it can run beside main-lane work if Blender time is shared.
Also read docs/tickets/README.md (rules every ticket follows).

## Log
- 2026-11-08 created (D201)
- 2026-11-08 code review step added (D202)

# LG-007 Preset save location
Type: feature | Milestone: M5 | Phase: A Cave fixes | Size: S | Priority: P2
Status: done | Lane: side | Needs Blender: tests only | Mike review: yes
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
- 2026-11-10 built by Opus 5.5 in main: first Save Preset in a .blend opens a folder browser (starts next to the .blend, or home if unsaved) with the name field; later saves go straight there; folder icon in the Presets panel changes it; folder stored on the scene, so per .blend; file kitbash_landscape_presets.json in that folder; list shows the 5 most recently saved (each preset stamped 'saved'). Before a folder is picked, presets stay in Blender's user config as before. T25 extended; T8/T18/T19 pass. Code review still to run
- 2026-11-10 code review done (logged); fixes: presets copied into a newly picked folder so none vanish, folder created on save, unwritable folder reported, sorted newest first then by name. Open question for Mike: only the 5 most recent show, so older presets can't be loaded, renamed or deleted from the panel. Keep the cap, or add a 'show all' toggle?
- 2026-11-10 Mike: add a Show All toggle (D206). Built: toggle beside Load lists every preset; T25 checks 5 then all 6
- 2026-11-13 Mike approved (board panel check / skim) -> done

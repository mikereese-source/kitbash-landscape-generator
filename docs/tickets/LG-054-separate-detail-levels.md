# LG-054 Separate Detail Levels for shell, rubble and formations
Type: feature | Milestone: M5 | Phase: A Cave fixes | Size: M | Priority: TBD (set after Mike's full review)
Status: todo | Lane: main | Needs Blender: yes | Mike review: yes
Depends on: none | Blocks: none

## Why
One Detail Level drives the cave shell, the rubble and the formations together. Mike wants each to have its own Preview / High / Ultra: it speeds things up, keeps the geometry separate, and artists who scatter their own meshes may not want them subdivided at all (review 2026-11-09).

## Done when
- Three Detail Level pickers: Cave, Rubble, Formations (plus a 'keep my mesh as is' option for custom pieces)
- Old files open with all three set to their old single level
- T32 (same formations at every level) and T15 still pass

## Files
- `kitbash_landscape_generator/features.py`
- `kitbash_landscape_generator/caves.py`
- `kitbash_landscape_generator/rocks.py`
- `kitbash_landscape_generator/formations.py`
- `tests/run_tests.py`

## Agent brief
Read D105, D108 (rock library per Detail Level), D169. Check how the rock and formation libraries pick their level today.
Also read docs/tickets/README.md (rules every ticket follows).

## Log
- 2026-11-09 created from Mike's review (limestone)

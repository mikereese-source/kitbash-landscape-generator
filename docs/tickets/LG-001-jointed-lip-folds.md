# LG-001 Jointed lip folds into pale patches
Type: bug | Milestone: M5 5.3a | Phase: A Cave fixes | Size: S-M | Priority: P1
Status: ready | Lane: main | Needs Blender: yes | Mike review: yes
Depends on: none | Blocks: LG-008, LG-016

## Why
Seen from inside, the jointed lip's blocky surface folds through itself as pale patches round the opening (D197, PARKING).

## Done when
- No pale fold patches from inside at Preview and High (board c174+)
- Outside reads as bedded blocks, not stuck-on lumps
- T14, T31 pass; 30/30

## Files
- `kitbash_landscape_generator/features.py`

## Agent brief
Read D196, D197, board c173. Cause found: the lip surface's blocks (turning it off clears them). First idea: blocks only on the outward-facing rock, not the inside face.
Also read docs/tickets/README.md (rules every ticket follows).

## Log
- 2026-11-08 created (D201)

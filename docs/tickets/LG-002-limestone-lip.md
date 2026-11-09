# LG-002 Limestone lip too lumpy, hollow at front-left foot
Type: bug | Milestone: M5 5.3a | Phase: A Cave fixes | Size: S | Priority: P1
Status: ready | Lane: main | Needs Blender: yes | Mike review: yes
Depends on: none | Blocks: LG-008, LG-016

## Why
At High the limestone lip is very lumpy, with a small round hollow at the front-left foot of the arch (D197).

## Done when
- Lip reads as limestone against the cave-photo references
- No hollow at the arch foot
- 30/30

## Files
- `kitbash_landscape_generator/features.py`

## Agent brief
Read D197, board c173, Terrain References cave-photos. Lip surface is the IndexSwitch by Rock in the mouth push block.
Also read docs/tickets/README.md (rules every ticket follows).

## Log
- 2026-11-08 created (D201)
- 2026-11-09 Mike's review: the lip roughness "feels really great"; the lumpiness is no longer an issue. Left: the hollow at the front-left foot (recheck), plus LG-057 (lip minimum and pinches)

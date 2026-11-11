# LG-028 M7 spike: material controls
Type: feature | Milestone: M7 | Phase: C Material spike | Size: M | Priority: P1
Status: todo | Lane: main | Needs Blender: yes | Mike review: yes
Depends on: LG-027 | Blocks: LG-033, LG-034, LG-037

## Why
Snow Line, Snow on Slopes, Rock Angle, Grass Amount, Wetness, Sediment, each with a blend softness; masks stay raw (Mike, 2026-10-26).

## Done when
- Each control moves its layer; Reset works
- Basic look controls per layer (Mike, 2026-11-11): colour tint, brightness, saturation, roughness, texture scale for grass/foliage, rock, soil, snow, matching competitors' basic set

## Files
- `kitbash_landscape_generator/materials.py`
- `kitbash_landscape_generator/__init__.py`

## Agent brief
Read the M7 row in PROJECT.md.
Also read docs/tickets/README.md (rules every ticket follows).

## Log
- 2026-11-08 created (D201)
- 2026-11-11 Mike: add basic per-layer look controls (colour etc.) as competitors have; added to Done when and the Fable brief

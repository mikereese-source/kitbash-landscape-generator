# LG-029 M7 spike: fog and atmosphere
Type: feature | Milestone: M7 | Phase: C Material spike | Size: M | Priority: P1
Status: todo | Lane: main | Needs Blender: yes | Mike review: yes
Depends on: LG-027 | Blocks: LG-033

## Why
Height fog, distance haze, clouds; part of the finished look in every app (D194).

## Done when
- Presets (morning mist, dusty, stormy)
- Cycles and Eevee
- Default lighting: neutral sky HDRI (Poly Haven kloofendal_48d_partly_cloudy_puresky, CC0), with an HDRI slot to swap it, plus strength and rotation; set as the World only on request (Mike, 2026-11-11)

## Files
- `kitbash_landscape_generator/atmosphere.py (new)`
- `kitbash_landscape_generator/__init__.py`

## Agent brief
Read PARKING 'Fog and atmosphere'.
Also read docs/tickets/README.md (rules every ticket follows).

## Log
- 2026-11-08 created (D201)
- 2026-11-11 Mike: neutral sky HDRI for basic lighting + a slot to replace it; HDRI downloaded (hdris/sources.json); added to the Fable brief

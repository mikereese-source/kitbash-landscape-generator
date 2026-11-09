# LG-069 Lava Roughness: fix 0 and push 1.0 harder
Type: feature | Milestone: M5 | Phase: A Cave fixes | Size: S-M | Priority: TBD (set after Mike's full review)
Status: todo | Lane: main | Needs Blender: yes | Mike review: yes
Depends on: none | Blocks: none

## Why
On Lava Tube, Roughness 0 shows square artifacts that look like pinched normals (lava shot 4). Mike likes the noise but wants it stronger: 0.5 should look like 1.0 does now, and 1.0 should exaggerate the detail, about 30-50% more than now (review 2026-11-09).

## Done when
- No square artifacts or pinched normals at Roughness 0
- Remap: 0.5 = today's 1.0; 1.0 about 30-50% stronger
- Board at 0 / 0.5 / 1.0, Preview and High; still reads as lava against references

## Files
- `kitbash_landscape_generator/features.py`

## Agent brief
Read D146-D157 (lava walls). The square pattern at 0 suggests a quantized or grid-aligned term left in when the noise is off. Similar ask on Limestone: LG-065. Mike's screenshots 2026-11-09 (lava review) in docs/m5/review-2026-11-09/
Also read docs/tickets/README.md (rules every ticket follows).

## Log
- 2026-11-09 created from Mike's review (lava)

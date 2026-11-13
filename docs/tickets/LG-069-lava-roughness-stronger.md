# LG-069 Lava Roughness: fix 0 and push 1.0 harder
Type: feature | Milestone: M5 | Phase: A Cave fixes | Size: S-M | Priority: P1
Status: done | Lane: main | Needs Blender: yes | Mike review: yes
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
- 2026-11-09 prioritized P1, step 8 of the review order (TICKETS.md)
- 2026-11-10 built by Opus 5.5 (CAVE_VERSION 207, board docs/m5/c179_step2_sliders.png, cave tests 5/5): Lava Roughness remapped: R (2.6 - 1.2 R) (0.5 -> today's 1, 1 -> 1.4). The square artifacts at 0 did not show in headless renders (smooth wall at Preview); Mike to point at where he saw them. Waiting on Mike's review
- 2026-11-13 Mike approved (board c179) -> done

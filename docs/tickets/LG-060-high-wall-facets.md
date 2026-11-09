# LG-060 Faceted patches on the inside wall at High
Type: bug | Milestone: M5 | Phase: A Cave fixes | Size: S-M | Priority: P2
Status: todo | Lane: main | Needs Blender: yes | Mike review: yes
Depends on: none | Blocks: none

## Why
At High with Lip 0.4 and Roughness 1.0 Mike circled an inside wall behind the lip: flat faceted triangles and a streaky rough patch (review 2026-11-09, shot 5).

## Done when
- Mike confirms the issue
- Wall reads as continuous limestone at High, no flat facets

## Files
- `kitbash_landscape_generator/features.py`

## Agent brief
Check whether the facets come from the lip surface fading into the tube-coordinate wall detail, or from subdivision steps on large flat SDF faces. Mike's screenshots 2026-11-09 (limestone review), copied to docs/m5/review-2026-11-09/
Also read docs/tickets/README.md (rules every ticket follows).

## Log
- 2026-11-09 created from Mike's review (limestone)
- 2026-11-09 prioritized P2, step 12 of the review order (TICKETS.md)

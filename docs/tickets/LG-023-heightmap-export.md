# LG-023 6.3b Heightmap and mask export
Type: feature | Milestone: M6 6.3b | Phase: E M6 | Size: S | Priority: P2
Status: review | Lane: side | Needs Blender: tests only | Mike review: no
Depends on: LG-021, LG-022 | Blocks: LG-026, LG-042

## Why
Cheapest table-stakes gap; needed for every engine handoff (RESEARCH-features.md, D198).

## Done when
- 16-bit PNG/EXR at Unreal sizes + Unity RAW
- Masks as splat images
- Recipe JSON
- New test T34; all pass
- Code review: `mattpocock-skills:code-review` against this ticket before merge; findings fixed or made tickets; logged in TICKETS.md Code reviews (D202)

## Files
- `kitbash_landscape_generator/export.py (new)`
- `kitbash_landscape_generator/__init__.py`
- `tests/run_tests.py`

## Agent brief
Follow docs/PACKAGE.md exactly.
Also read docs/tickets/README.md (rules every ticket follows).

## Log
- 2026-11-08 created (D201)
- 2026-11-08 code review step added (D202)
- 2026-11-10 D206: Blender writes the full package (all exports), folder named after the landscape, default 2017
- 2026-11-11 built by Opus 5.5 in main (export.py; Export Package button in the Bake section): <name>.kblandscape with recipe.json (tiles list), 16-bit grayscale height.png at 1009/2017/4033 (default 2017), one 16-bit PNG per mask, optional height.r16; base and water left out. Masks as PNGs not one EXR (PACKAGE.md updated); splats wait for M7; caves .glb waits for LG-021. T39 (corners within one 16-bit step, PNG header checked); suite 34/34. Code review next
- 2026-11-11 code review done (logged) and fixed; T39 now checks every pixel and the recipe schema. Left: Unity RAW row order not checked in Unity; Mesa Floor off and 4033 untested

# LG-089 Breakup blocks replace the surface with their plane
Type: feature | Milestone: Model realism | Phase: B2 Model realism | Size: M | Priority: P1
Status: todo | Lane: side | Needs Blender: yes | Mike review: yes
Depends on: LG-077, LG-088 | Blocks: -
Claimed: test T45, GROUP_VERSION 149 (released unused by LG-088)

## Why
LG-088 (board c197): faceted fields in the base shape fail (plane cells left 968 teeth), and with LG-077's breakup off the flat-face share goes to 75.6% and creases to 0.5%, so the breakup sets both measures. Today each block adds a tilted plane on top of the soft surface, so faces stay pillowed under the plane. Real rock (the Megascans granite in the same clay, c197) shows flat planes meeting at hard steps. Mike, 2026-11-18: make it a ticket.

## Done when
- On steep rock, each LG-077 block replaces the surface inside the block with its own plane (blended over the bevel), instead of adding a plane to it
- Flat-face and crease shares measured on main, the branch and the scans (granite 16.7 / 43.8, layered sandstone 4.6 / 69.0, dolerite 0.3 / 54.4); a pillow-versus-face check added to the flat measure (two window sizes) so a soft surface no longer counts as flat
- Teeth and crest sharpness no worse than main (47 teeth, 1141 crest, LG-087 measure); T42 Preview vs High within 1 point
- Board in `docs/realism/` (next free number) against main and the granite scan, clay as c197
- Per-point only, no new faces; GROUP_VERSION 149, library rebuilt, T45 tests the flat-face measure itself (CODING.md: the Done-when measure, not a stand-in); full suite passes
- Code review before merge; Mike signs off the board

## Files
- `kitbash_landscape_generator/nodes.py`, `node_groups.blend`
- `tests/run_tests.py` (T45)
- `docs/realism/` (board), `docs/tickets/LG-089-blocks-replace-surface.md`

## Agent brief
Read LG-077, LG-086, LG-087 and LG-088's Logs. Reuse LG-088's measure (flat share, creases; branch lg-088-facets, docs/realism/LG-088_scratch/measure.py, scan_measure.py) and LG-086's teeth counter. Prototype the replace-with-plane step in numpy on a bake first and measure where neighbouring blocks meet before building it in nodes. Opus 5.5 at high effort unless Fable is available. Save-as-you-go rules. Also read docs/tickets/README.md and docs/CODING.md.

## Log
- 2026-11-18 created from LG-088's recommendation (Mike approved)

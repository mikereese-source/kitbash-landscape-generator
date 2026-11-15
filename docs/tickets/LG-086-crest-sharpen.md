# LG-086 Crest sharpen: sharp summits and knife-edge crests
Type: feature | Milestone: Model realism | Phase: B2 Model realism | Size: M | Priority: P1
Status: todo | Lane: side | Needs Blender: yes | Mike review: yes
Depends on: LG-077 | Blocks: LG-082

## Why
Mike, 2026-11-12: 'we need to resolve getting sharp mountain tops... overall sharper, more realistic mountains'. LG-077's breakup only acts on steep ground, so dome tops stay domes. Fable's scratch crest sharpen (c191, right column) pointed the tops but left small spikes along ridges. Mike, 2026-11-15: break it out into its own ticket.

## Done when
- The highest peaks read as horns and aretes, not domes, in the wide and mid clay shots (board against c191 and the granite references)
- No small spikes along ridges: spikes counted before and after, as in T6b
- Crest sharpness measured as in the realism review and logged (LG-077: 513, real Sierra 1351)
- Per-point fields only, so it ports to three.js as vertex displacement; no new faces; each Detail Level keeps its quality
- GROUP_VERSION bump, library rebuilt, test added, suite passes
- Code review before merge; Mike signs off the board

## Files
- `kitbash_landscape_generator/nodes.py`
- `kitbash_landscape_generator/types.json`
- `kitbash_landscape_generator/node_groups.blend`
- `tests/run_tests.py`

## Agent brief
Start from Fable's scratch test in LG-077's Log (2026-11-14): lift = (Rc / 2) x (s0 - slope)^2 on high convex ground, slope from the normal and convexity from 4 extra reads of the erosion map. Count the ridge spikes it leaves and find their cause before tuning (CODING.md, "Finding and fixing problems"). Runs after LG-077's breakup, so the breakup covers the new faces. Overlaps LG-079's sharp-summits line: whichever lands first, the other checks against it.
Also read docs/tickets/README.md (rules every ticket follows) and docs/CODING.md.

## Log
- 2026-11-15 created from LG-077 checkpoint 1 (Mike: break crest sharpening out into its own ticket; LG-077 "still much better")
- 2026-11-15 claimed T44 and GROUP_VERSION 148 (CODING.md rule); brief docs/briefs/fable-LG-086.md. Start after the usage reset (Mike)

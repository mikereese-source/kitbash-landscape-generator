# LG-090 Glacial-style valley walls on Mountains
Type: feature | Milestone: Model realism | Phase: B2 Model realism | Size: L | Priority: P2
Status: todo | Lane: side | Needs Blender: yes | Mike review: yes
Depends on: LG-079, LG-080 | Blocks: LG-082

## Why
Mike, 2026-11-25, testing LG-080 in 5.3: Glacial gets really nice cliffs, and Mountains would get better shapes from the same approach. Glacial draws its walls on purpose (nodes.py recipe 9): a valley line, a wall that stands straight up from the floor and rounds over at an even rim, and its own hard map so erosion keeps the wall sheer. Mountains has no valley line, so its cliffs only appear where noise ridges happen to get steep: broken and scattered, not the tall even headwalls and trough sides of real glaciated ranges.

## Done when
- Mountains gets drawn walls along its main valleys: cirque headwalls at valley heads and trough sides lower down, built from the Glacial wall profile (shared code, not a copy)
- The new walls feed the LG-079 hard-rock map so erosion keeps them steep; talus (LG-080) collects at their feet
- Glacial looks the same (T48 numbers unchanged)
- Mountains is no worse on the accepted measures: teeth/horns not above main, over 60 deg not above main (real 11.7%), upper-third crest at or above T49's floor; relief within 2%
- A new measure for tall continuous walls (height of unbroken over-60-deg faces) rises toward the reference; its test sits at the measured board value
- Board beside a glaciated-range reference (cirque headwall + trough wall), Preview vs High alike, suite passes, code review

## Files
- `kitbash_landscape_generator/nodes.py` (Mountains recipe 1, the Glacial wall profile pulled into a shared helper)
- `kitbash_landscape_generator/node_groups.blend`
- `kitbash_landscape_generator/types.json` (any new per-type value)
- `tests/run_tests.py`

## Agent brief
Read nodes.py recipe 9 (the `axis`, `across`, `ws`, `wall`, `hard_glacial` lines) and recipe 1. The hard part is the valley line: Glacial uses one noise axis; Mountains needs its main valleys found, for example from the flow or drainage the erosion already computes, or from low lines in the base shape. Prototype in numpy on a baked Mountains height map first and show Mike a board before touching nodes. Keep the extra re-evaluation time small and measure it.
Also read docs/tickets/README.md (rules every ticket follows) and docs/CODING.md.

## Log
- 2026-11-25 created (Mike, after testing LG-080 in 5.3)

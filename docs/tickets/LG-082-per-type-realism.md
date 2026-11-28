# LG-082 Per-type realism pass (all 13 types)
Type: feature | Milestone: Model realism | Phase: B2 Model realism | Size: L | Priority: P2
Status: todo | Lane: main | Needs Blender: yes | Mike review: yes
Depends on: LG-093, LG-094, LG-095, LG-096 | Blocks: LG-083

## Why
Each type keeps its own tells after the shared fixes (review section 3 and S8).

## Done when
- Split into four tickets (Mike, 2026-11-28): LG-093 rock walls (Glacial, Canyon, plus Mesa gullies and Badlands flats), LG-094 sand and cinder slopes, LG-095 volcanoes, LG-096 gentle types (Hills, Riverbed, Seabed, Crater, Cliffs headland). This closes when all four are done; clay renders, boards and per-type sign-off live in them

## Files
- `kitbash_landscape_generator/types.json`
- `kitbash_landscape_generator/nodes.py`
- `tests/run_tests.py`

## Agent brief
Read docs/REVIEW-realism-2026-11.md sections 3 and 7 (S8). Split into one ticket per type when it starts.
Also read docs/tickets/README.md (rules every ticket follows) and docs/CODING.md.

## Log
- 2026-11-11 created from the realism review (D209)
- 2026-11-13 from LG-076: also try the S1 settings on Glacial (incision 1.0, soften 0.2) and Canyon (finish_blur 8), each with a board for Mike
- 2026-11-28 refreshed against LG-076 to LG-092 and split into LG-093 to LG-096 (Mike: "Yes, as drafted"). Mountains and the Badlands rills are already handled; the Mountains far-wall stripes stay in PARKING

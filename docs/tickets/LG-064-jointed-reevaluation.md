# LG-064 Jointed: full re-evaluation against the earlier version
Type: feature | Milestone: M5 | Phase: A Cave fixes | Size: L | Priority: P1
Status: todo | Lane: main | Needs Blender: yes | Mike review: yes
Depends on: none | Blocks: none

## Why
Mike: Jointed needs the most work. The noise around the mouth and chamber looks very bad (spiky rim, jointed shot 3), odd hanging masses near the chamber (shot 4), and it makes less sense than the Jointed we had before the mouth rebuild (review 2026-11-09).

## Done when
- Side-by-side board: Jointed at 187 (before the mouth rebuild) vs now vs the jointed references and the target (docs/m5/target_jointed_passage.png)
- List what changed and why it reads worse; Mike picks what to keep
- Rebuild to the agreed look; no spiky rim, no hanging masses

## Files
- `kitbash_landscape_generator/features.py`

## Agent brief
Read D116-D118 (masses, target), D164, D188, D196-D197. LG-001 (lip folds) and LG-006 (shards) fold into this re-evaluation. Mike wants suggestions before code. Mike's screenshots 2026-11-09 (jointed review) in docs/m5/review-2026-11-09/
Also read docs/tickets/README.md (rules every ticket follows).

## Log
- 2026-11-09 created from Mike's review (jointed)
- 2026-11-09 prioritized P1, step 14 of the review order (TICKETS.md)
- 2026-11-10 re-evaluation done, analysis only, no code (model: Claude Fable 5.2, claude-fable-5-2). Boards docs/m5/c177_jointed_then_now_1_review_settings.png and c177_jointed_then_now_2_causes_refs.png; write-up docs/REVIEW-jointed-2026-11-10.md. Found: spiky rim and rim noise are the jointed lip surface (tested: off, they go); the mouth cut strips the passage pieces; the hanging masses are also in 187 (masses placed by path fraction land over the chamber drop). Recommends option B in two steps. Waiting on Mike's pick; status stays todo.

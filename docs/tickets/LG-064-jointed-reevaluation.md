# LG-064 Jointed: full re-evaluation against the earlier version
Type: feature | Milestone: M5 | Phase: A Cave fixes | Size: L | Priority: P1
Status: review | Lane: main | Needs Blender: yes | Mike review: yes
Depends on: none | Blocks: none

## Why
Mike: Jointed needs the most work. The noise around the mouth and chamber looks very bad (spiky rim, jointed shot 3), odd hanging masses near the chamber (shot 4), and it makes less sense than the Jointed we had before the mouth rebuild (review 2026-11-09).

## Done when
Mike's pick (2026-11-10, D205): the recommendation in docs/REVIEW-jointed-2026-11-10.md, option B in two steps, plus:
- **Plain ledges** at the mouth: the jointed lip reads as plain stepped rock ledges, not the blocky noise (no spikes at any Lip value)
- **No hanging pieces**: every jointed piece rests on rock (floor, wall or roof it grows from); nothing free-hanging in the passage or over the chamber drop
- **The chamber looks good**: Mike's review cave (width 60, height 40, depth 100, chamber 120, ceiling 60, chamber drop 60) is a common one, so its chamber and the passage into it are the look to get right; boards at Preview and High against the jointed references and the target
- Step 1 (S): tame/cap the jointed lip surface, limit the mouth zone's length, calmer cut
- Step 2 (M): pieces back in the passage, placed by its real length, nothing hanging
- All tests pass; a test that no jointed piece hangs free; code review before merge
- Full rebuild (option C) stays parked

## Files
- `kitbash_landscape_generator/features.py`

## Agent brief
Read D116-D118 (masses, target), D164, D188, D196-D197. LG-001 (lip folds) and LG-006 (shards) fold into this re-evaluation. Mike wants suggestions before code. Mike's screenshots 2026-11-09 (jointed review) in docs/m5/review-2026-11-09/
Also read docs/tickets/README.md (rules every ticket follows).

## Log
- 2026-11-09 created from Mike's review (jointed)
- 2026-11-09 prioritized P1, step 14 of the review order (TICKETS.md)
- 2026-11-10 re-evaluation done, analysis only, no code (model: Claude Fable 5.2, claude-fable-5-2). Boards docs/m5/c177_jointed_then_now_1_review_settings.png and c177_jointed_then_now_2_causes_refs.png; write-up docs/REVIEW-jointed-2026-11-10.md. Found: spiky rim and rim noise are the jointed lip surface (tested: off, they go); the mouth cut strips the passage pieces; the hanging masses are also in 187 (masses placed by path fraction land over the chamber drop). Recommends option B in two steps. Waiting on Mike's pick; status stays todo.
- 2026-11-10 Mike picked the recommendation + plain ledges, remove hanging pieces, make the common review chamber look good (D205). To Fable 5.2 after the weekly usage reset
- 2026-11-12 step 1 built (model: Claude Fable 5.2, claude-fable-5-2), commit 1e100c7, CAVE_VERSION 211. Jointed lip surface is a low swell sized to the width (not blocky steps sized to the wall); the jointed mouth zone stops a tenth short of where the chamber opens; jointed cuts wander 0.3 not 0.8. Limestone and lava untouched. Counted on Mike's review cave at Preview, sharp edges (over 50 degrees) on the mouth's rock: Lip 0.1 1237 -> 20, Lip 0.55 916 -> 41, Lip 1 3500 -> 45. Board docs/m5/c181_jointed_fix_step1.png
- 2026-11-12 step 2 built (same model), commit e0e3943, CAVE_VERSION 212. Counted first: 4 of the 9 pieces that show stopped short of the floor (2542 m2, 38% of what shows). Causes, each proven by switching it off in a scratch copy: 3 were the chamber's ring columns (only their tops showed; now measured from a tenth to 70% of the way up, so they stand on the floor); 1 was a roof stub over the way in (roof blocks placed by path fraction over the drop, and the wandering mouth cut slicing pieces). Passage masses are now placed by the passage's real length, and the pieces are cut straight where the mouth zone ends. New test T37: fails on 210 (4 hang), passes on 212 (7 pieces, each standing, nearest 22 m in from the mouth, was 42 m). Left over: 4 specks under 48 m2 (80 m2 in all) still stop short at Preview, a few more at High. Board docs/m5/c182_jointed_fix_step2.png
- 2026-11-12 timings, one slider change, 210 -> 212, same run: Mike's review cave Preview 1.4 -> 1.4 s, High 12.4 -> 11.8 s; default Jointed cave Preview 1.4 -> 1.4 s, High 41.3 -> 41.9 s. Main merged in (3bed1e8); full suite 36/36 after the merge. Waiting on code review and Mike's look at both boards

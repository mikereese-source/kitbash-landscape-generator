# LG-055 Show face counts per Detail Level before switching
Type: feature | Milestone: M5 | Phase: A Cave fixes | Size: S | Priority: P2
Status: done | Lane: side | Needs Blender: tests only | Mike review: yes
Depends on: none | Blocks: none

## Why
Mike switched to High and got 15M faces with no warning, so he never tried Ultra. Artists need to know what each level will cost before they pick it (review 2026-11-09, shot 5: 15.1M faces at High).

## Done when
- Panel shows the estimated faces for Preview, High and Ultra for the current cave (shell + rubble + formations)
- Estimate within about 20% of the real count at Preview and High
- Warning colour above a threshold (e.g. 5M)
- Code review: `mattpocock-skills:code-review` against this ticket before merge; logged in TICKETS.md Code reviews (D202)

## Files
- `kitbash_landscape_generator/caves.py`

## Agent brief
The panel already says 'Shell about 0.15M / 4M faces'; that is the shell basis only and is far off once the hollow body, rubble and formations are added (D197). Estimate from the basis face count the node tree already computes.
Also read docs/tickets/README.md (rules every ticket follows).

## Log
- 2026-11-09 created from Mike's review (limestone)
- 2026-11-09 prioritized P2, step 17 of the review order (TICKETS.md)
- 2026-11-10 built by Opus 5.5 in main (small enough; no worktree): panel shows the rock shell's faces at Preview / High / Ultra, red over 5M; estimated from the current build (lg_basis stored by the node tree, steps and voxel scaling as the cave picks them), within 2-4% of real (T36). Mike's review cave: Preview 0.47M, High 13.3M, Ultra about 53M. Rocks and formations not counted (labelled). CAVE_VERSION 209. Code review still to run before closing
- 2026-11-10 code review done (logged); guard for a cave mesh without lg_basis; T36 says why when it can't estimate. Counts the rock shell only: rocks and formations are labelled as extra. features.py was touched (stores lg_basis)
- 2026-11-13 Mike approved (board panel check / skim) -> done

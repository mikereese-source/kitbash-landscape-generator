# LG-055 Show face counts per Detail Level before switching
Type: feature | Milestone: M5 | Phase: A Cave fixes | Size: S | Priority: TBD (set after Mike's full review)
Status: todo | Lane: side | Needs Blender: tests only | Mike review: yes
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

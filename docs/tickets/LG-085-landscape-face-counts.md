# LG-085 Face counts per Detail Level for landscapes
Type: feature | Milestone: M6 | Phase: E M6 | Size: S | Priority: P2
Status: todo | Lane: side | Needs Blender: tests only | Mike review: yes
Depends on: none | Blocks: none

## Why
Mike, 2026-11-13: caves show each Detail Level's face count before switching (LG-055); the landscape panel only says 'A point every 0.39 m · 263 k points'. Add the face counts there too.

## Done when
- Under the landscape's Detail Level buttons: the face count for Preview, High and Ultra, in the same style as the cave readout (LG-055)
- Counts include the base's sides and bottom when Base is on, and the water sheet when Water is on
- Counts match the built mesh within 2% at each level (a test, like T36)
- Code review before merge

## Files
- `kitbash_landscape_generator/__init__.py`
- `tests/run_tests.py`

## Agent brief
Reuse the cave readout's wording and layout (caves.py face_estimates, LG-055). A landscape grid of n x n points has (n-1)^2 quads; the base adds 4(n-1) side faces and a bottom. No node change.
Also read docs/tickets/README.md and docs/CODING.md.

## Log
- 2026-11-13 created (Mike, panel screenshot)

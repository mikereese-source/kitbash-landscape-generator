# LG-026 6.5 M6 gate
Type: gate | Milestone: M6 6.5 | Phase: E M6 | Size: M | Priority: P1
Status: todo | Lane: main | Needs Blender: yes | Mike review: yes
Depends on: LG-020, LG-023, LG-024, LG-025 | Blocks: LG-048

## Why
Close M6: tests, checker, rollback, sign-off, AI-world check.

## Done when
- All pass; Mike signs off
- Code review: `ponytail:ponytail-review` on the M6 diff (last gate tag to HEAD); findings fixed or made tickets; logged in TICKETS.md Code reviews (D202)

## Files
- `tests/run_tests.py`

## Agent brief
Follow BUILD_RULES gates.
Also read docs/tickets/README.md (rules every ticket follows).

## Log
- 2026-11-08 created (D201)
- 2026-11-08 code review step added (D202)

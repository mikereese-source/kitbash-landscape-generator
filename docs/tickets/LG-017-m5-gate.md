# LG-017 5.5 Cave creator gate
Type: gate | Milestone: M5 5.5 | Phase: B M5 finish | Size: S-M | Priority: P1
Status: todo | Lane: main | Needs Blender: yes | Mike review: yes
Depends on: LG-005, LG-006, LG-010, LG-014, LG-015, LG-016, LG-052 | Blocks: LG-019, LG-031

## Why
Close M5: tests, checker, rollback zip, Mike sign-off; first AI-world-tools check (D194).

## Done when
- All tests pass
- Checker review (CHECKER.md)
- Rollback zip in snapshots/
- positioning-researcher AI-world pass
- Mike signs off
- Code review: `ponytail:ponytail-review` on the M5 diff (last gate tag to HEAD); findings fixed or made tickets; logged in TICKETS.md Code reviews (D202)

## Files
- `tests/run_tests.py`
- `docs/PROJECT.md`

## Agent brief
Follow BUILD_RULES gates.
Also read docs/tickets/README.md (rules every ticket follows).

## Log
- 2026-11-08 created (D201)
- 2026-11-08 code review step added (D202)

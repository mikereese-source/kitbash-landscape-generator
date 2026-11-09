# LG-052 Baseline code audit (ponytail-audit)
Type: review | Milestone: M5 | Phase: B M5 finish | Size: M | Priority: P1
Status: todo | Lane: research | Needs Blender: no | Mike review: no
Depends on: LG-051 | Blocks: LG-016, LG-017

## Why
features.py (176K) and the rest have never had a code review; an audit before the cave speed pass finds slow paths that feed it (Mike, D202).

## Done when
- `ponytail:ponytail-audit` run on the whole repo
- Report saved as docs/reviews/2026-MM-DD-audit.md
- Every finding fixed, made a ticket, or marked won't-fix with a reason
- Logged in TICKETS.md Code reviews

## Files
- `docs/reviews/ (new)`

## Agent brief
Read-only run; no code changes in this ticket. Run after the A-phase cave fixes land so it sees current code.
Also read docs/tickets/README.md (rules every ticket follows).

## Log
- 2026-11-08 created (D202)

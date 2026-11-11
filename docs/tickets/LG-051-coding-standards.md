# LG-051 CODING.md: written coding standards
Type: docs | Milestone: M5 | Phase: B M5 finish | Size: S | Priority: P2
Status: review | Lane: research | Needs Blender: no | Mike review: yes
Depends on: none | Blocks: LG-052

## Why
mattpocock code-review checks code against written standards; we have none, only gotchas spread through memory and DECISIONS (D202).

## Done when
- docs/CODING.md: version bumps (CAVE_VERSION / GROUP_VERSION, rebuild node_groups.blend), line endings per file, bounded seeds (FLOORED_MODULO 100), never reuse node-builder names, headless Blender one process at a time, tests per feature, every shape traced to a reference
- Mike approves

## Files
- `docs/CODING.md (new)`

## Agent brief
Pull from DECISIONS, memory notes and tickets/README.md. Short: one line per rule with its why.
Also read docs/tickets/README.md (rules every ticket follows).

## Log
- 2026-11-08 created (D202)
- 2026-11-10 written by Opus 5.5: docs/CODING.md. Waiting on Mike's OK

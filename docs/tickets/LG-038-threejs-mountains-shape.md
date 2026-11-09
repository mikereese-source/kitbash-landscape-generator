# LG-038 three.js spike: Mountains shape and erosion
Type: spike | Milestone: Project 2 spike | Phase: D three.js spike | Size: M-L | Priority: P1
Status: todo | Lane: side | Needs Blender: no | Mike review: yes
Depends on: LG-037 | Blocks: LG-039

## Why
Mountains shape from types.json plus erosion in WebGPU; erosion is the main port risk.

## Done when
- Same seed reads like the Blender Mountains; build time measured
- Code review: `mattpocock-skills:code-review` against this ticket before merge; findings fixed or made tickets; logged in TICKETS.md Code reviews (D202)

## Files
- `apps/landscape-spike-threejs/ (new, throwaway)`

## Agent brief
No copied GPL Blender code (D49 rule). Read erosion.py for the algorithm only.
Also read docs/tickets/README.md (rules every ticket follows).

## Log
- 2026-11-08 created (D201)
- 2026-11-08 code review step added (D202)

# LG-022 Export package spec (PACKAGE.md)
Type: docs | Milestone: M6 6.3b | Phase: E M6 | Size: S | Priority: P2
Status: ready | Lane: research | Needs Blender: no | Mike review: yes
Depends on: none | Blocks: LG-023, LG-041, LG-071

## Why
Write the package layout once so Blender, three.js, Unreal and C4D all write/read the same files (D198).

## Done when
- docs/PACKAGE.md: file names, sizes (1009/2017/4033), bit depth, mask/splat channels, recipe JSON schema (a list of tiles from the start, so multi-tile landscapes need no format change, D203), cave meshes
- Mike approves

## Files
- `docs/PACKAGE.md`

## Agent brief
Read PLAN-unreal.md (data package), RESEARCH-engines.md (Send-to), D89, D198. No code.
Also read docs/tickets/README.md (rules every ticket follows).

## Log
- 2026-11-08 created (D201)
- 2026-11-09 recipe must allow multiple tiles (D203)

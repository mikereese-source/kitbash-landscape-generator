# Ticket board

Every ticket in plan order (D201). Rules and template: [tickets/README.md](tickets/README.md). Phases follow the demo path
(D199, D200): A cave fixes, B M5 finish, C material spike (week of 2026-11-23), D three.js spike, E M6, F rest of M7, F2 multi-tile (M7b),
G M8, H Final. Phase E (M6) may move before C or D; Mike decides.

**Can run now in parallel with main-lane LG-001:** LG-022 package spec (research), LG-018 cave realism refs (research),
LG-043 checker-note fixes and LG-044 realism output folder (side, Blender for tests only, so not while main is testing).
LG-007 preset save location (side) also fits. LG-051 CODING.md (research) also fits. **Blocked on Mike:** none.

## Next up: review order (Mike's review 2026-11-09, prioritized same day)

Quality first, then speed (D196). Main lane runs top to bottom; the parallel items can run beside it.

1. **Quick fixes that look like errors:** LG-057 lip minimum 0.3 + pinches, LG-058 no puddles at the lip, LG-062 puddles on every rock, LG-063 + LG-066 flooded water (holes, and water outside the cave; same code, one pass), LG-004 floor apron
2. **Look pushes:** LG-065 Limestone Wall Shape stronger and LG-069 Lava Roughness (same kind of remap, one pass), LG-067 lava lip roughness, LG-053 lip roughness into the floor
3. **Confirm, then fix:** LG-059 outside lumps, LG-060 High wall facets (Mike confirms what was circled), LG-002 limestone hollow recheck
4. **Rethinks (options first, Mike picks):** LG-064 Jointed full re-evaluation, LG-061 rubble scatter, LG-068 lip reach (feasibility)
5. **Cost and speed:** LG-054 separate Detail Levels, LG-056 Ultra at render time, LG-052 baseline audit, then LG-016 speed pass
6. Then the rest of phase B as listed below (LG-005, LG-008, LG-009 ...)

**Parallel now (no clash with step 1):** options notes for LG-061 (rockfall references, research lane) and LG-064 (needs Blender renders, so after step 1's tests), LG-055 face-count readout (side lane), LG-051 CODING.md, LG-022 package spec.

| ID | Title | Phase | Milestone | Status | Size | Pri | Lane | Blender | Files | Depends on |
|---|---|---|---|---|---|---|---|---|---|---|
| [LG-001](tickets/LG-001-jointed-lip-folds.md) | Jointed lip folds into pale patches | A Cave fixes | M5 5.3a | folded into LG-064 | S-M | P1 | main | yes | features.py | - |
| [LG-002](tickets/LG-002-limestone-lip.md) | Limestone lip too lumpy, hollow at front-left foot | A Cave fixes | M5 5.3a | ready | S | P1 | main | yes | features.py | - |
| [LG-003](tickets/LG-003-floating-piles.md) | Floating piles in cave renders | A Cave fixes | M5 | todo | S | P1 | main | yes | features.py; rocks.py | - |
| [LG-004](tickets/LG-004-floor-apron.md) | Trim floor apron in front of the mouth | A Cave fixes | M5 5.5 | review | S | P2 | main | yes | features.py | - |
| [LG-005](tickets/LG-005-stalactites-through-ledge.md) | Stalactites hang through rock ledges | A Cave fixes | M5 5.5 | ready | S-M | P2 | main | yes | formations.py; features.py | - |
| [LG-006](tickets/LG-006-jointed-shards.md) | Jointed shards under the passage join (outside) | A Cave fixes | M5 5.5 | folded into LG-064 | S | P3 | main | yes | features.py | - |
| [LG-007](tickets/LG-007-preset-save-location.md) | Preset save location | A Cave fixes | M5 | ready | S | P2 | side | tests only | presets.py; __init__.py; caves.py; run_tests.py | - |
| [LG-008](tickets/LG-008-floor-detail.md) | 5.4b Cave floor detail | B M5 finish | M5 5.4b | todo | M | P2 | main | yes | features.py; rocks.py | LG-001, LG-002, LG-004 |
| [LG-009](tickets/LG-009-cutter-and-carve.md) | 5.3b Cutter mesh and carve into landscapes | B M5 finish | M5 5.3b | todo | M-L | P2 | main | yes | features.py; caves.py; run_tests.py | LG-008 |
| [LG-010](tickets/LG-010-rocks-dress-entrance.md) | Rocks dress the cave entrance | B M5 finish | M5 5.3 | todo | M | P3 | main | yes | features.py; rocks.py | LG-009 |
| [LG-011](tickets/LG-011-path-curve.md) | 5.2b Cave path you draw: path curve | B M5 finish | M5 5.2b | todo | M | P2 | main | yes | features.py; caves.py | LG-009 |
| [LG-012](tickets/LG-012-path-strands.md) | 5.2b Cave path: strands and branching | B M5 finish | M5 5.2b | todo | M | P2 | main | yes | features.py; caves.py | LG-011 |
| [LG-013](tickets/LG-013-path-tests.md) | 5.2b Cave path: single-path fixes and tests | B M5 finish | M5 5.2b | todo | S-M | P2 | main | yes | run_tests.py; features.py | LG-012 |
| [LG-014](tickets/LG-014-cave-outside-surface.md) | Cave outside surface | B M5 finish | M5 / M7 | todo | S | P3 | main | yes | features.py | LG-009 |
| [LG-015](tickets/LG-015-drapes-tuning.md) | Drapes tuning | B M5 finish | M5 | todo | M | P3 | main | yes | formations.py; features.py | LG-013 |
| [LG-016](tickets/LG-016-cave-speed-pass.md) | Cave speed pass | B M5 finish | M5 | todo | M | P2 | main | yes | features.py | LG-001, LG-002, LG-003, LG-004, LG-005, LG-008, LG-009, LG-013, LG-052 |
| [LG-017](tickets/LG-017-m5-gate.md) | 5.5 Cave creator gate | B M5 finish | M5 5.5 | todo | S-M | P1 | main | yes | run_tests.py; PROJECT.md | LG-005, LG-006, LG-010, LG-014, LG-015, LG-016, LG-052 |
| [LG-051](tickets/LG-051-coding-standards.md) | CODING.md: written coding standards | B M5 finish | M5 | ready | S | P2 | research | no | CODING.md | - |
| [LG-052](tickets/LG-052-baseline-audit.md) | Baseline code audit (ponytail-audit) | B M5 finish | M5 | todo | M | P1 | research | no | reviews/ | LG-051 |
| [LG-018](tickets/LG-018-cave-realism-refs.md) | Cave realism reference research | B M5 finish | M6 prep | ready | S | P3 | research | no | RESEARCH-caves.md | - |
| [LG-019](tickets/LG-019-cave-landscape-type.md) | 6.1 Cave landscape type | E M6 | M6 6.1 | todo | L | P2 | main | yes | features.py; types.json; __init__.py | LG-017, LG-018 |
| [LG-020](tickets/LG-020-cliff-features.md) | 6.2 Cliff features | E M6 | M6 6.2 | todo | M-L | P2 | main | yes | features.py | LG-019 |
| [LG-021](tickets/LG-021-bake-with-caves.md) | 6.3 Bake and Restore with caves | E M6 | M6 6.3 | todo | M | P2 | main | yes | __init__.py; run_tests.py | LG-019 |
| [LG-022](tickets/LG-022-package-spec.md) | Export package spec (PACKAGE.md) | E M6 | M6 6.3b | ready | S | P2 | research | no | PACKAGE.md | - |
| [LG-023](tickets/LG-023-heightmap-export.md) | 6.3b Heightmap and mask export | E M6 | M6 6.3b | todo | S | P2 | side | tests only | export.py; __init__.py; run_tests.py | LG-021, LG-022 |
| [LG-024](tickets/LG-024-drag-handles.md) | 6.4 Drag handles for everything | E M6 | M6 6.4 | todo | M | P2 | side | tests only | gizmos.py; __init__.py | LG-019 |
| [LG-025](tickets/LG-025-carve-strokes.md) | 6.4b Carve strokes | E M6 | M6 6.4b | todo | M | P2 | main | yes | features.py; __init__.py; run_tests.py | LG-019 |
| [LG-070](tickets/LG-070-base-thickness.md) | Base thickness (solid sides) | E M6 | M6 6.4c | review | S | P2 | side | yes | nodes.py; __init__.py; presets.py; run_tests.py | - |
| [LG-026](tickets/LG-026-m6-gate.md) | 6.5 M6 gate | E M6 | M6 6.5 | todo | M | P1 | main | yes | run_tests.py | LG-020, LG-023, LG-024, LG-025 |
| [LG-027](tickets/LG-027-m7-mountains-layers.md) | M7 spike: Mountains material layers | C Material spike | M7 | todo | L | P1 | main | yes | materials.py; __init__.py | - |
| [LG-028](tickets/LG-028-m7-material-controls.md) | M7 spike: material controls | C Material spike | M7 | todo | M | P1 | main | yes | materials.py; __init__.py | LG-027 |
| [LG-029](tickets/LG-029-fog-atmosphere.md) | M7 spike: fog and atmosphere | C Material spike | M7 | todo | M | P1 | main | yes | atmosphere.py; __init__.py | LG-027 |
| [LG-030](tickets/LG-030-water-shaders.md) | M7 water shaders and water types | F M7 rest | M7 | todo | M-L | P2 | side | yes | materials.py | LG-027 |
| [LG-031](tickets/LG-031-cave-rock-materials.md) | M7 cave rock materials | F M7 rest | M7 | todo | L | P2 | main | yes | materials.py | LG-027, LG-017 |
| [LG-032](tickets/LG-032-rock-uvs-texel.md) | Rock UVs and texel density | F M7 rest | M7 | todo | M | P3 | side | yes | rocks.py | LG-031 |
| [LG-033](tickets/LG-033-climate-switch.md) | Climate switch | F M7 rest | M7 | todo | M | P2 | main | yes | materials.py; __init__.py | LG-028, LG-029, LG-030 |
| [LG-034](tickets/LG-034-8k-texture-test.md) | 8K texture test | F M7 rest | M7 | todo | S | P3 | research | yes | - | LG-028 |
| [LG-035](tickets/LG-035-m7-gate.md) | M7 gate | F M7 rest | M7 | todo | M | P1 | main | yes | run_tests.py | LG-031, LG-032, LG-033 |
| [LG-071](tickets/LG-071-tiles-design.md) | Multi-tile landscapes: design | F2 Multi-tile | M7b | todo | S | P2 | main | no | PLAN-tiles.md | LG-035 |
| [LG-072](tickets/LG-072-tiles-build.md) | Multi-tile landscapes: tiles and seams | F2 Multi-tile | M7b | todo | L | P2 | main | yes | nodes.py; __init__.py; types.json; run_tests.py | LG-071 |
| [LG-073](tickets/LG-073-tiles-erosion.md) | Multi-tile landscapes: erosion across tiles | F2 Multi-tile | M7b | todo | M | P2 | main | yes | erosion.py; nodes.py; run_tests.py | LG-072 |
| [LG-074](tickets/LG-074-m7b-gate.md) | M7b multi-tile gate | F2 Multi-tile | M7b | todo | S-M | P1 | main | yes | run_tests.py | LG-073 |
| [LG-036](tickets/LG-036-orbit-check.md) | Check Orbit's stack | D three.js spike | Project 2 prep | ready | S | P2 | research | no | RESEARCH-engines.md | - |
| [LG-037](tickets/LG-037-threejs-spike-plan.md) | three.js spike plan | D three.js spike | Project 2 spike | todo | S | P1 | main | no | PLAN-threejs-spike.md | LG-028, LG-036 |
| [LG-038](tickets/LG-038-threejs-mountains-shape.md) | three.js spike: Mountains shape and erosion | D three.js spike | Project 2 spike | todo | M-L | P1 | side | no | landscape-spike-threejs | LG-037 |
| [LG-039](tickets/LG-039-threejs-mountains-look.md) | three.js spike: Mountains materials, side by side | D three.js spike | Project 2 spike | todo | M | P1 | side | no | landscape-spike-threejs | LG-038 |
| [LG-040](tickets/LG-040-threejs-cave-check.md) | three.js spike: small cave check | D three.js spike | Project 2 spike | todo | M | P2 | side | no | landscape-spike-threejs | LG-037 |
| [LG-041](tickets/LG-041-heightmap-import.md) | Heightmap and real-elevation import | G M8 | M8 | todo | S-M | P2 | side | tests only | heightmap_import.py; __init__.py; run_tests.py | LG-022 |
| [LG-042](tickets/LG-042-batch-script.md) | Headless batch build script | G M8 | M8 | todo | S | P3 | side | tests only | batch_build.py | LG-023 |
| [LG-043](tickets/LG-043-checker-notes.md) | Checker-note fixes | G M8 | M8 | ready | S | P3 | side | tests only | __init__.py; run_tests.py | - |
| [LG-044](tickets/LG-044-realism-output-folder.md) | Realism reports to an output folder | G M8 | M8 | ready | S | P3 | side | tests only | realism.py; lidar_check.py | - |
| [LG-045](tickets/LG-045-m8-edge-cases.md) | M8 edge cases and gate | G M8 | M8 | todo | M | P2 | main | yes | __init__.py; run_tests.py | LG-041, LG-042, LG-043 |
| [LG-046](tickets/LG-046-shipped-presets.md) | Shipped KitBash presets | H Final | Final | todo | S-M | P2 | main | yes | presets | LG-035 |
| [LG-047](tickets/LG-047-thumbnails.md) | Re-render gallery thumbnails | H Final | Final | todo | S | P3 | side | yes | thumbs | LG-035 |
| [LG-048](tickets/LG-048-final-alpha.md) | Final check and Alpha package | H Final | Final | todo | M | P1 | main | yes | PROJECT.md | LG-026, LG-045, LG-046, LG-047 |
| [LG-049](tickets/LG-049-project2-plan.md) | Project 2 plan | H Final | Project 2 | todo | M | P2 | main | no | PLAN-threejs.md | LG-039, LG-040, LG-048 |
| [LG-050](tickets/LG-050-blender-writeup.md) | Blender milestone write-up | H Final | Final | todo | S-M | P3 | research | no | - | LG-048 |

## From Mike's review 2026-11-09 (prioritize when the review is done)

| ID | Title | Phase | Milestone | Status | Size | Pri | Lane | Blender | Files | Depends on |
|---|---|---|---|---|---|---|---|---|---|---|
| [LG-053](tickets/LG-053-lip-roughness-into-floor.md) | Carry the lip roughness into the cave floor | A Cave fixes | M5 | todo | M | P2 | main | yes | features.py | - |
| [LG-054](tickets/LG-054-separate-detail-levels.md) | Separate Detail Levels for shell, rubble and formations | A Cave fixes | M5 | todo | M | P1 | main | yes | features.py; caves.py; rocks.py; formations.py; run_tests.py | - |
| [LG-055](tickets/LG-055-face-count-readout.md) | Show face counts per Detail Level before switching | A Cave fixes | M5 | todo | S | P2 | side | tests only | caves.py | - |
| [LG-056](tickets/LG-056-ultra-at-render-time.md) | Ultra at render time (and camera-based detail) | A Cave fixes | M5 | todo | M-L | P2 | main | yes | features.py; caves.py | - |
| [LG-057](tickets/LG-057-lip-minimum.md) | Lip minimum 0.3, range to 0.5, and fix pinches | A Cave fixes | M5 | review | S-M | P1 | main | yes | features.py; caves.py; run_tests.py | - |
| [LG-058](tickets/LG-058-no-puddles-at-lip.md) | No puddles at the lip | A Cave fixes | M5 | review | S | P1 | main | yes | features.py | - |
| [LG-059](tickets/LG-059-outside-hull-lumps.md) | Lumps and dimples on the outside of the cave | A Cave fixes | M5 | todo | S | P2 | main | yes | features.py | - |
| [LG-060](tickets/LG-060-high-wall-facets.md) | Faceted patches on the inside wall at High | A Cave fixes | M5 | todo | S-M | P2 | main | yes | features.py | - |
| [LG-061](tickets/LG-061-rubble-heaps-rethink.md) | Rethink the rubble heaps and rubble scatter | A Cave fixes | M5 | todo | M-L | P1 | main | yes | features.py; rocks.py | - |
| [LG-062](tickets/LG-062-puddles-on-jointed.md) | Puddles slider greyed out on Jointed | A Cave fixes | M5 | review | S | P1 | main | yes | features.py; caves.py | - |
| [LG-063](tickets/LG-063-flooded-water-holes.md) | Holes in the flooded chamber water next to pieces | A Cave fixes | M5 | review | S-M | P1 | main | yes | features.py; run_tests.py | - |
| [LG-064](tickets/LG-064-jointed-reevaluation.md) | Jointed: full re-evaluation against the earlier version | A Cave fixes | M5 | todo | L | P1 | main | yes | features.py | - |
| [LG-065](tickets/LG-065-limestone-wall-shape-stronger.md) | Limestone Wall Shape: make 1.0 much stronger | A Cave fixes | M5 | todo | S | P1 | main | yes | features.py | - |
| [LG-066](tickets/LG-066-flooded-water-outside.md) | Flooded chamber water pokes out of the cave | A Cave fixes | M5 | review | S-M | P1 | main | yes | features.py; run_tests.py | - |
| [LG-067](tickets/LG-067-lava-lip-roughness.md) | More roughness on the lava lip | A Cave fixes | M5 | todo | S | P2 | main | yes | features.py | - |
| [LG-068](tickets/LG-068-lip-extension.md) | Extend the lip outward (all three rocks) | A Cave fixes | M5 | todo | M | P3 | main | yes | features.py; caves.py; run_tests.py | - |
| [LG-069](tickets/LG-069-lava-roughness-stronger.md) | Lava Roughness: fix 0 and push 1.0 harder | A Cave fixes | M5 | todo | S-M | P1 | main | yes | features.py | - |

## Code reviews (D202)

When they run (every one is a Done-when line on its ticket, so a ticket or gate can't close without it):
- **Every side-lane ticket:** `mattpocock-skills:code-review` against the ticket file (spec) and docs/CODING.md (standards), before merge.
- **Every milestone gate (LG-017, 026, 035, 045, 048):** `ponytail:ponytail-review` on the milestone's diff.
- **Whole repo:** `ponytail:ponytail-audit` at LG-052 (before the cave speed pass) and again at Final (LG-048).
- Findings: fix now, make a ticket, or mark won't-fix with a reason. Reports go in docs/reviews/.
- At every session start, check this log against tickets marked done; a done ticket with a missing review is reopened.

| Date | Ticket | Skill | Scope | Findings | Tickets made | Report |
|---|---|---|---|---|---|---|

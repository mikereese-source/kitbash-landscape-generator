# Ticket board

Every ticket in plan order (D201). Rules and template: [tickets/README.md](tickets/README.md). Phases follow the demo path
(D199, D200): A cave fixes, B M5 finish, C material spike (week of 2026-11-23), D three.js spike, E M6, F rest of M7,
G M8, H Final. Phase E (M6) may move before C or D; Mike decides.

**Can run now in parallel with main-lane LG-001:** LG-022 package spec (research), LG-018 cave realism refs (research),
LG-043 checker-note fixes and LG-044 realism output folder (side, Blender for tests only, so not while main is testing).
LG-007 preset save location (side) also fits. LG-051 CODING.md (research) also fits. **Blocked on Mike:** LG-003 (which render shows floating piles),
LG-036 (Orbit team contact).

| ID | Title | Phase | Milestone | Status | Size | Pri | Lane | Blender | Files | Depends on |
|---|---|---|---|---|---|---|---|---|---|---|
| [LG-001](tickets/LG-001-jointed-lip-folds.md) | Jointed lip folds into pale patches | A Cave fixes | M5 5.3a | ready | S-M | P1 | main | yes | features.py | - |
| [LG-002](tickets/LG-002-limestone-lip.md) | Limestone lip too lumpy, hollow at front-left foot | A Cave fixes | M5 5.3a | ready | S | P1 | main | yes | features.py | - |
| [LG-003](tickets/LG-003-floating-piles.md) | Floating piles in cave renders | A Cave fixes | M5 | blocked | S | P1 | main | yes | features.py; rocks.py | - |
| [LG-004](tickets/LG-004-floor-apron.md) | Trim floor apron in front of the mouth | A Cave fixes | M5 5.5 | ready | S | P2 | main | yes | features.py | - |
| [LG-005](tickets/LG-005-stalactites-through-ledge.md) | Stalactites hang through rock ledges | A Cave fixes | M5 5.5 | ready | S-M | P2 | main | yes | formations.py; features.py | - |
| [LG-006](tickets/LG-006-jointed-shards.md) | Jointed shards under the passage join (outside) | A Cave fixes | M5 5.5 | ready | S | P3 | main | yes | features.py | - |
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

## Code reviews (D202)

When they run (every one is a Done-when line on its ticket, so a ticket or gate can't close without it):
- **Every side-lane ticket:** `mattpocock-skills:code-review` against the ticket file (spec) and docs/CODING.md (standards), before merge.
- **Every milestone gate (LG-017, 026, 035, 045, 048):** `ponytail:ponytail-review` on the milestone's diff.
- **Whole repo:** `ponytail:ponytail-audit` at LG-052 (before the cave speed pass) and again at Final (LG-048).
- Findings: fix now, make a ticket, or mark won't-fix with a reason. Reports go in docs/reviews/.
- At every session start, check this log against tickets marked done; a done ticket with a missing review is reopened.

| Date | Ticket | Skill | Scope | Findings | Tickets made | Report |
|---|---|---|---|---|---|---|

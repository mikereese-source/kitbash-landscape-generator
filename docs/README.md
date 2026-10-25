# Build Kit

Blank starter files for a build under [BUILD_RULES.md](../../BUILD_RULES.md). At kickoff, copy this folder into the project's home (usually `apps/<project-name>/docs/`) and fill it in.

| File | Rule it covers | Full | Lite |
|------|----------------|------|------|
| `PROJECT.md` | Project context file + milestone plan + gate log | ✓ | ✓ (holds everything) |
| `DESIGN.md` | Design doc, boundaries, prototype link | ✓ | summary goes in PROJECT.md |
| `TEST_PLAN.md` | Test plan, tests named before building | ✓ | tests go in PROJECT.md |
| `DECISIONS.md` | Decision log | ✓ | optional |
| `PARKING.md` | Parking list for mid-build ideas | ✓ | optional |
| `CHECKER.md` | Prompt for the checker subagent | ✓ | ✓ (final check) |

**Lite track:** copy only `PROJECT.md` and `CHECKER.md`.

**Rollback points:** an artifact gets a labelled publish at each gate (e.g. "M2 gate"). Local code gets a zip in `snapshots/` named `<project>-M<n>-YYYY-MM-DD.zip`. Record which in the gate log.

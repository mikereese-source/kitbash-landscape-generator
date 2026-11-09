# Tickets: how they work

Plan work and parked bugs live as tickets here, one markdown file each, so any piece can be handed to a subagent with
everything it needs (D201). The board is [../TICKETS.md](../TICKETS.md). PARKING.md stays for raw ideas: once Mike puts
an idea in the plan, or a bug is parked for later instead of fixed on the spot, it becomes a ticket.

## Template

```markdown
# LG-0NN Title
Type: feature|bug|perf|test|research|docs|chore|spike|gate | Milestone: M6 6.3b | Phase: E M6 | Size: S|M|L | Priority: P1-P3
Status: todo|ready|blocked|in progress|review|done | Lane: main|side|research | Needs Blender: yes|tests only|no | Mike review: yes|no
Depends on: LG-0NN | Blocks: LG-0NN

## Why
One or two lines, with the decision or PARKING row it comes from.

## Done when
- Checks that prove it (tests by number, boards, Mike sign-off)

## Files
- Paths it creates or touches (this is how collisions are spotted)

## Agent brief
What to read first, gotchas, where it starts.

## Log
- YYYY-MM-DD what happened (commit, decision)
```

## Rules

- **IDs** run on from the highest one; never reuse. File name `LG-0NN-short-slug.md`.
- **Status:** `ready` = nothing it depends on is open; `blocked` = waiting on Mike or outside info (say what in the brief).
  Update the ticket and its board row together; add a Log line on every status change with the commit or D-number.
- **Lanes:**
  - `main` = `features.py` and visual work: one at a time, in the main session, reviewed by Mike after each stage.
  - `side` = separate modules: a subagent in its own git worktree, merged after review.
  - `research` = research agents and docs; no code.
  - Review goes to the `mike-first-pass-reviewer` agent before Mike sees visual work.
- **Running in parallel:** two tickets run together only if their Files lists don't overlap and at most one needs Blender
  (Blender runs headless, one process at a time, never in Mike's open Blender).
- **Every code ticket:** bump CAVE_VERSION / GROUP_VERSION after node edits, rebuild node_groups.blend, all tests pass,
  every shape traced to a reference, new ideas to PARKING.md not into the ticket.
- **Code reviews (D202):** side-lane tickets get `mattpocock-skills:code-review` before merge; gates get `ponytail:ponytail-review`;
  whole-repo `ponytail:ponytail-audit` at LG-052 and Final. Each run gets a row in the board's Code reviews log.
- **Done** = the Done-when list is met (including its code review), tests pass, the commit is in the Log, and Mike signed off where review is yes.

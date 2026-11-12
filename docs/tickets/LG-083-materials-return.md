# LG-083 Back to materials: re-shoot checkpoint 1, rework checkpoint 2
Type: spike | Milestone: Model realism | Phase: B2 Model realism | Size: S-M | Priority: P1
Status: todo | Lane: main | Needs Blender: yes | Mike review: yes
Depends on: LG-075, LG-076, LG-077 | Blocks: LG-028

## Why
Fable's view: return to materials once the masks, the erosion retune and the breakup are in on Mountains (D209).

## Done when
- Checkpoint 1's three views re-shot on the new Mountains (material unchanged); the `render_m7.py` close-up no longer picks `lg_deposit > 0.9`
- Checkpoint 2 brief updated: rock on the breakup's rock field or lg_hard, scree on lg_talus (after LG-080), soil and turf on the fixed deposit and flow masks
- Mike decides when checkpoint 2 runs

## Files
- `tests/render_m7.py` (lg-m7-spike)
- `docs/briefs/fable-M7-spike.md`

## Agent brief
Read docs/REVIEW-realism-2026-11.md section 10. Other types' materials wait for the breakup on those types.
Also read docs/tickets/README.md (rules every ticket follows) and docs/CODING.md.

## Log
- 2026-11-11 created from the realism review (D209)

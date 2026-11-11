# Fable brief: LG-064 Jointed fix

Ready-to-send prompt for a `model: "fable"` subagent (written 2026-11-10). Before sending:
- run `git worktree add ../lg-064-fix -b lg-064-fix` from main;
- check `get_usage`;
- schedule it after LG-061 merges, or tell the agent the heap code is being replaced. Both tickets touch `features.py`, so merge order matters.

---

You are building ticket LG-064 "Jointed: full re-evaluation", the fix Mike picked (D205), in the KitBash Landscape Generator. It's a Blender 5.2 Geometry Nodes add-on built from Python. You wrote the analysis behind it yourself in an earlier session: `docs/REVIEW-jointed-2026-11-10.md`. Say at the top of your report which model and version you are.

**Where:** the git worktree `E:\Projects\Cowork\apps\lg-064-fix`, branch `lg-064-fix`. Never edit the main checkout or Mike's open Blender.

**Blender:** only through `bash tests/blender.sh <args>`: a shared lock, one Blender at a time. Render one shot per process.

**Read first:**
- `docs/CODING.md`
- `docs/tickets/README.md`
- `docs/tickets/LG-064-jointed-reevaluation.md`: its "Done when" is Mike's pick
- `docs/REVIEW-jointed-2026-11-10.md`
- the boards `docs/m5/c177_jointed_then_now_*.png`
- the target `docs/m5/target_jointed_passage.png` and the reference shapes `docs/m5/ref_jointed_shapes.jpg`
- Mike's shots `docs/m5/review-2026-11-09/jointed_shot1-6.webp`

**What Mike wants (D205):**
1. **Step 1 (small, low risk):** cap the jointed lip surface (`features.py`, around the lip-surface IndexSwitch, jointed `l_step x 0.7`). Its size scales with `wall_t`, which LG-057 doubled, so the steps grew to 5-9 m on 15 m cells. Also cap how far the mouth zone reaches (sized by width only, it reaches the chamber at depth 100), and calm the jointed cut.
2. **Plain ledges:** the jointed mouth reads as plain stepped rock ledges, with no blocky noise and no spikes, at Lip 0.1, 0.55 and 1.
3. **Step 2 (medium):** put the pieces back in the passage. The mouth cut strips about 37% of the piece geometry, including the slabs framing the chamber opening. Place passage pieces by the passage's real length, not by path fraction 0.3-0.58, which lands them over the chamber drop.
4. **No hanging pieces:** every jointed piece rests on rock (the floor, or the wall or roof it grows from). Add a test, T37, that finds pieces with nothing under or around them.
5. **The common chamber:** Mike's review cave is a common one, so its chamber and the passage into it are the look to get right. Settings: width 60, height 40, depth 100, chamber 120, ceiling 60, chamber drop 60, roughness 1, wall shape 0.8. Check against the jointed references and the target.

**Rules:**
- Every shape traces to a reference.
- Lean polygons, nothing floating.
- Each Detail Level keeps its quality.
- Bump CAVE_VERSION. Keep each file's line endings.
- Full suite passes: `bash tests/blender.sh -b --factory-startup -P tests/run_tests.py`.

**Boards:**
- `docs/m5/c181_jointed_fix_step1.png`: mouth outside and front, Lip 0.1, 0.55 and 1, Preview. Old (CAVE_VERSION 209) against new.
- `docs/m5/c182_jointed_fix_step2.png`: passage and chamber, Preview and High, against the target.

Checkpoint after step 1: commit, then carry on to step 2. Mike reviews both boards together.

**Wrap up:** ticket Log (model, commits, timings before and after on Mike's cave), commit on your branch. Messages end with `Co-Authored-By: Claude <noreply@anthropic.com>`. The main session does the code review and the merge.

**Report (under 350 words):** model, commits, tests, what each board shows, what you were unsure about.

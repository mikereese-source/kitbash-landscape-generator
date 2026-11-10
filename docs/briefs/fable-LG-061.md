# Fable brief: LG-061 rubble, finish checkpoints 1-2

Ready-to-send prompt for a `model: "fable"` subagent (written 2026-11-10). Check `get_usage` first. Start it only with room to finish, and tell it to stop at a clean point before the weekly limit.

---

You are finishing ticket LG-061 "Rethink the rubble heaps and rubble scatter", checkpoints 1 and 2, in the KitBash Landscape Generator. It's a Blender 5.2 Geometry Nodes add-on built from Python. Say at the top of your report which model and version you are.

**Where:** the git worktree `E:\Projects\Cowork\apps\lg-061-rubble`, branch `lg-061-rubble`. Your earlier WIP commit is `42c026a`. Never edit the main checkout `E:\Projects\Cowork\apps\landscape-generator` or Mike's open Blender.

**Blender:** only through `bash tests/blender.sh <args>`. It holds a shared lock: one Blender at a time across every session. Render one shot per process.

**Read first:**
- `docs/CODING.md` (the coding rules)
- `docs/tickets/README.md`
- `docs/tickets/LG-061-rubble-heaps-rethink.md`: its Log says exactly where you stopped
- `docs/RESEARCH-rubble.md`, option B, which Mike chose (D204)
- your board `docs/m5/c178_rubble_layered_wip.png`

**Steps:**
1. **Bring main in first:** `git merge main`. Main has moved on to CAVE_VERSION 209: step 2 slider changes, `lg_basis` for the face-count readout, preset folder changes, the tests T36 and T25, the Lip mapping in `caves.lip_thickness`. For CAVE_VERSION take the higher number and add 1. Keep both sides' changes in `tests/run_tests.py`; it mixes CR CR LF line endings, so edit with Python and `newline=''`. Run `LG_ONLY=T14,T15,T31,T35,T36 bash tests/blender.sh -b --factory-startup -P tests/run_tests.py`.
2. **Fix the floating rocks.** T35 fails: 35 of 1,068 rocks in Mike's cave sit 1-2 m above what is under them, and about 1% sit more than half inside a bigger rock. Your suspects:
   - the last step, which moves each rock by the finished-floor difference under its own spot, so a stack comes apart;
   - small rocks tipped on another rock's shoulder.

   Diagnose with numbers before changing anything (print the gaps and which layer they're in). Fix the root cause. T35 must pass at Preview and High. Check Ultra too: same rocks, nothing floating.
3. **Cairns:** stacks at the pile centres read like cairns. Real breakdown piles are wider than tall. Each pile should spread low at the toe, with the big blocks there (fall sorting). Check against the references in `RESEARCH-rubble.md`.
4. **Spread below 0.5:** low Spread should mean tighter piles, not fewer rocks. Keep the count; shrink the footprint.
5. **Full suite:** `bash tests/blender.sh -b --factory-startup -P tests/run_tests.py`. Everything passes.
6. **Board:** `docs/m5/c178_rubble_layered.png`. Before and after at Mike's review settings (LG_ROCK=JOINTED, LG_SET="width=60,height=40,depth=100,chamber=120,ceiling=60,chamber_drop=60,roughness=1,wall_shape=0.8"), Preview and High, plus one close-up of a pile. Label it with CAVE_VERSION.
7. **Timings:** Preview and High rebuilds on the default Jointed cave and on Mike's cave. Compare against the before numbers in the ticket Log.
8. **Wrap up:** update the ticket Log (model, commits, timings, what's left for checkpoint 3) and commit on your branch. Messages end with `Co-Authored-By: Claude <noreply@anthropic.com>`. The main session does the code review and the merge.

**Not in scope:** checkpoint 3 (Limestone and Lava rubble, ramp scree), and wiring Stretch.

**Report (under 350 words):** model, commits, test results, timings, what the board shows, what you were unsure about, and what's left.

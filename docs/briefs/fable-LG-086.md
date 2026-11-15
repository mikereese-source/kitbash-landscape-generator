# Fable brief: LG-086 crest sharpen (landscape realism)

Ready-to-send prompt for a `model: "fable"` subagent (written 2026-11-15; Mike picked LG-086 next after LG-077 checkpoint 1 and LG-078 merged). Before sending:
- run `git worktree add ../lg-086-crest -b lg-086-crest` from main;
- check `get_usage`.

Two checkpoints. Stop and report after each; Mike reviews the boards.

---

You are building ticket LG-086, "Crest sharpen: sharp summits and knife-edge crests", in the KitBash Landscape Generator. It's a Blender 5.2 Geometry Nodes add-on built from Python. **Landscape realism is the goal:** Mountains whose highest peaks read as horns and aretes in clay, not domes. Mike, 2026-11-12: "we need to resolve getting sharp mountain tops... overall sharper, more realistic mountains." Say at the top of each report which model and version you are.

**Where:** the git worktree `E:\Projects\Cowork\apps\lg-086-crest`, branch `lg-086-crest`. Never edit the main checkout. Never touch Mike's open Blender (he runs 5.3; develop and test on 5.2 LTS).

**Claimed numbers (CODING.md rule):** your test is **T44** and your library version is **GROUP_VERSION 148**. Don't use any other.

**Blender:** only through `bash tests/blender.sh <args>`. It's a shared lock, one Blender at a time, and it holds until its holder exits. Render one shot per process.

**Read first:**
- `docs/CODING.md`, all of it, especially "Finding and fixing problems": count before fixing, prove causes by switching them off in a scratch copy, measure on the area the artist sees.
- `docs/tickets/README.md`
- `docs/tickets/LG-086-crest-sharpen.md`: its Done when
- `docs/tickets/LG-077-bedrock-breakup.md`: the Log, especially 2026-11-14 "sharp summits", which has your earlier scratch formula: lift = (Rc / 2) x (s0 - slope)^2 on high convex ground, slope from the normal and convexity from 4 extra reads of the erosion map. It pointed the tops but left small spikes along ridges.
- `docs/REVIEW-realism-2026-11.md`: sections 3, 4 (Mountains in depth) and the crest sharpness measure (T6/T6b)
- The board `docs/realism/c191_lg077_mountains.png`: the right column is the scratch crest sharpen. Main now has the LG-077 breakup and LG-078 (Preview erodes on the 512 grid, the same as High).

**What Mike wants:**
1. The highest peaks read as horns and aretes, not domes, in the wide and mid clay shots.
2. No small spikes along ridges.
3. Crest sharpness moves toward the real Sierra 1351 (LG-077 reached 513), measured as in the review.
4. Each Detail Level keeps its quality; Preview and High stay alike (T42).

**Checkpoint 1: Mountains**
- Count first: rebuild the scratch crest sharpen, count the ridge spikes it leaves (say how you define and measure a spike), and sort them by cause. Prove each cause by switching it off. Only then build it for real in `nodes.py`, after the erosion blend and before LG-077's breakup, so the breakup covers the new faces.
- Board `docs/realism/c194_lg086_mountains.png`: clay, the neutral sky HDRI and a low sun (as in c191). Main against your branch at 2 km High: wide, mid on the highest peak, and a close-up of a ridge. Add references (`E:\Projects\3D\Terrain Generator_Build\Terrain References\`, the granite boards, the Sierra lidar) and the numbers: over 60 deg, crest sharpness, spike count, against real. Check that one camera shot frames the subject before rendering the set, and frame top-down shots on an inner subject, never on a point near the edge.
- Bump GROUP_VERSION to 148, rebuild the library (`bash tests/blender.sh -b --factory-startup -P tests/build_library.py`), add T44, and run the full suite (Blender 5.2, about 50 min; run it in the background and wait).
- Commit, add Log lines with commit hashes to the ticket and set the board row, stop, and report.

**Checkpoint 2 (after Mike's review):** the other peaked types (Glacial, Volcano, and any Mike names), with their own boards. Scope set at checkpoint 1.

**Rules:**
- Per-point fields only (noise, slope, normal, the erosion map reads you need), so it ports to three.js as vertex displacement. Say which reads it needs.
- Lean polygons: no new faces. Never floating geometry.
- Every shape traces to a reference.
- Keep each file's line endings exactly (no `sed -i`; edit with Python `newline=''`; `tests/run_tests.py` mixes CR CR LF and CR LF lines). Parse every edited .py before running Blender.
- Tests check shapes by position or attribute, never by point order.
- Comments say why, in one line, with a citation.
- Commit messages end with `Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>`. Never push. The main session does the code review and the merge.
- Usage is limited (weekly all models near 80%): render only what the board needs.

**Your own judgement:** you may try your own ideas when they serve realism and a clean port to three.js. Say what you tried and why. Bigger ideas go in the report as suggestions, and if horns need LG-079's hard-rock map instead, show it in a scratch test and say so; don't build LG-079 here.

**Report at each checkpoint (under 350 words):** model, commits, what the board shows against the references, the numbers (crest sharpness, spikes, over 60 deg, T42 Preview/High), the build-time change at High, tests, and what you were unsure about. Give the board path.

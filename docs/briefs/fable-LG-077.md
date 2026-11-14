# Fable brief: LG-077 bedrock breakup (landscape realism)

Ready-to-send prompt for a `model: "fable"` subagent (written 2026-11-14; Mike: "We need it to focus on landscape realism"). Before sending:
- run `git worktree add ../lg-077-breakup -b lg-077-breakup` from main;
- check `get_usage`.

Two checkpoints. Stop and report after each; Mike reviews the boards.

---

You are building ticket LG-077, "Bedrock breakup stage on the finished mesh", in the KitBash Landscape Generator. It's a Blender 5.2 Geometry Nodes add-on built from Python. **Landscape realism is the goal:** Mountains that read as real crags in clay, not domes. You wrote the analysis behind this ticket in an earlier session (`docs/REVIEW-realism-2026-11.md`, solution S4), and you prototyped it in numpy (`rock_breakup()` in that review's appendix). Now build it for real in nodes. Say at the top of each report which model and version you are.

**Where:** the git worktree `E:\Projects\Cowork\apps\lg-077-breakup`, branch `lg-077-breakup`. Never edit the main checkout. Never touch Mike's open Blender (he runs 5.3; develop and test on 5.2 LTS).

**Blender:** only through `bash tests/blender.sh <args>`. It's a shared lock, one Blender at a time, and it now holds until its holder exits. Render one shot per process. Another session may be using Blender for cave work at the same time; the lock handles that.

**Read first:**
- `docs/CODING.md`, all of it, including "Finding and fixing problems": count before fixing, prove causes by switching them off in a scratch copy, measure on the area the artist sees, change a measure and retune what was tuned with it.
- `docs/tickets/README.md`
- `docs/tickets/LG-077-bedrock-breakup.md`: its Done when, including Mike's sharp-summits goal
- `docs/REVIEW-realism-2026-11.md`: sections 3, 4 (Mountains in depth), 7 (S4 and S2) and the appendix
- `docs/DECISIONS.md` D208, D209 and D211. D211 is the Mountains erosion Mike picked: incision 1.8 with the S1 settings, now on main in `types.json`.
- The boards `docs/realism/c186_realism_mountains-solutions.png`, `c187_lg076_incision.png` and `c190_lg076_option_b.png`. In c190, the middle column is what main builds now.

**What Mike wants:**
1. Mountains that read as real crags: jointed rock blocks and cliff bands on the steep ground, scree-angle ground left smooth.
2. **Sharp summits and knife-edge crests** (Mike, 2026-11-12: "we need to resolve getting sharp mountain tops... overall sharper, more realistic mountains"). LG-076 showed that erosion settings and Peak Sharpness can't do this: the dome is in the base shape. The breakup is the first place that can. If it can't reach horn peaks on its own, say what can (LG-079's hard-rock map, or something else) and show it in a scratch test. Don't build LG-079 here.
3. It must look good at a normal shot distance in clay, and close up it must not read as cracked plates or stretched combs. Those were the two limits of your numpy draft.

**Checkpoint 1: references and Mountains**
- First, a reference board per rock type in `docs/realism/`: granite blocks, bedded limestone, sandstone. Use the references already in `E:\Projects\3D\Terrain Generator_Build\Terrain References\` (`materials-rock-granite`, `-limestone`, `-sandstone`, `-basalt`, `materials-scree`, `usgs-3dep-1m`, with `sources.json`) and the photo boards in `docs/`. Download nothing new without Mike's OK; if a reference is missing, say so.
- Build the breakup in `nodes.py` on Mountains, after the erosion blend, as the ticket's Done when describes. Settle the per-type inputs (amount, bed thickness, bed dip, block size), all in meters, as the size changes.
- Board `docs/realism/c191_lg077_mountains.png`: clay, the neutral sky HDRI and a low sun (as in the review). Main against your branch at 2 km High: wide, mid on the highest peak, and a close-up of a cliff band. Add the references and the T6/T6b numbers (over 60 deg, 64 m roughness, crest sharpness against real 1351).
- Bump `GROUP_VERSION`, rebuild the library, add a test, and run the full suite (Blender 5.2).
- Commit, stop, and report.

**Checkpoint 2 (after Mike's review): the other rocky types**
Glacial, Canyon, Mesa, Cliffs and Badlands, each with its own bed and block settings and its own board. The scope is set at checkpoint 1.

**Rules:**
- Per-point fields only (noise, slope, masks), so it ports to three.js as vertex displacement.
- Each Detail Level keeps its quality.
- Lean polygons: no new faces.
- Every shape traces to a reference.
- Commit messages end with `Co-Authored-By: Claude <noreply@anthropic.com>`.
- The main session does the code review and the merge.
- Never push.

**Your own judgement:** you may try your own ideas when they serve realism and a clean port to three.js. Say what you tried and why. Bigger ideas go in the report as suggestions.

**Report at each checkpoint (under 350 words):** model, commits, what the board shows against the references, the numbers, the build-time change at High, tests, and what you were unsure about.

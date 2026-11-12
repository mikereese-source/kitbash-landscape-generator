# Coding standards

The rules code in this repo follows. Each rule has its reason. Code reviews (D202) check changes against this file and against `docs/tickets/README.md`. Started 2026-11-10 (LG-051), from DECISIONS, past bugs and the ticket rules.

## Node trees

- **Bump the version after any node change.** `CAVE_VERSION` (features.py) for caves, `GROUP_VERSION` (nodes.py) for landscapes. Otherwise old files and the prebuilt library keep the old tree, and the change looks like it did nothing.
- **Rebuild `node_groups.blend` after a `GROUP_VERSION` bump**, with `bash tests/blender.sh -b --factory-startup -P tests/build_library.py`, and commit it. T24 fails until you do.
- **Check that the bump landed.** Read the constant back after editing. Several bumps silently failed because of line-ending mismatches.
- **Never reuse a node-builder name in the same function** (for example `inner`). A second use quietly rewires the first.
- **Bound every seed** with `FLOORED_MODULO 100` before it feeds noise. Big seeds make the noise sawtooth.
- **Set a node's data type before linking its sockets** (Raycast, Store Named Attribute, Field on Domain). Changing the type swaps the sockets and drops the links.
- **Reach for the SDF stage only where shapes fold back** (caves, overhangs). Everything else stays a heightfield. A dense volume over a whole landscape is billions of voxels (D9).
- **Cave mesh normals point into the rock.** Flip after Grid to Mesh. With flipped normals the rock reads as solid and pieces squash flat.

## Look and geometry

- **Every shape traces to a reference.** Put a side-by-side board in `docs/m5/` (or the milestone's folder) before showing Mike. Mike's markups mark problems; they are not feature references.
- **Keep polygons lean, and never leave floating pieces.** Scattered pieces may sink into the ground, but must not hang in the air.
- **Mesh holds primary and secondary volume only.** Fine lines, beds, cracks and wear go to M7 materials (D157, D163).
- **Each Detail Level keeps the quality approved at it.** Higher face counts are fine; speed comes after quality (D196).
- **Never rename, prefix, regroup or tag** anything in a user's file. Naming belongs to KitBash and 3dam.

## Finding and fixing problems (learned from Fable's LG-061 and LG-064 work, 2026-11-11)

- **Count the failures before fixing.** Measure every bad case, then sort them by cause (for example 53 floating rocks: 15 from stacks pulling apart, 38 on bevelled edges). Fix each cause, not the symptom. Never guess at a cause.
- **Prove a cause by switching it off.** Turn the suspect off in a scratch copy and show that the problem goes. Only then call it the cause and change the code.
- **Place on cheap stand-ins, show the real meshes.** Scatter and stacking run on the Preview-level rocks (or the coarse space), and each Detail Level swaps in its own meshes. Placement is then the same at every level and costs no extra time.
- **Measure against main in the same run.** Before and after timings come from one session, on the same caves (the default one and Mike's review cave), at Preview and High.
- **Measure on the area the artist sees.** Masks and stats come from the visible landscape, never from padded or hidden grids: LG-075's masks, measured with the erosion padding, left a deposit band along every edge.

## Python and files

- **Keep each file's line endings exactly.** Check the bytes before editing. `tests/run_tests.py` mixes CR CR LF lines; most others are CRLF. Edit with Python using `newline=''`, and insert the same ending the file already uses.
- **Don't write files with PowerShell here-strings.** They dropped the trailing newline and joined lines three times. Use Python.
- **Parse every edited `.py` before running Blender**: `python -c "import ast; ast.parse(open(p, encoding='latin1').read())"`.
- **Comments say why, in one line**, citing the decision or Mike's note (`# ... (Mike, LG-057)`). Never delete or shorten an existing comment you weren't asked to change.
- **Write the shortest complete change.** No options, wrappers or abstractions nobody asked for. Reuse the `_Tree` helpers (`t.node`, `t.math`, `t.smooth`, ...) and the patterns around the change.

## Blender and tests

- **One headless Blender at a time**, through `bash tests/blender.sh` (a shared lock across sessions and worktrees). Never call `blender.exe` directly. Never use Mike's open Blender. One render per process: batches crashed his open Blender through the GPU.
- **Every feature gets a test in `tests/run_tests.py`**, numbered `Tnn`, with a message that says what was wanted and what was found.
- **The whole suite passes before a commit to main.** Use `LG_ONLY=Tnn,...` while iterating.
- **Tests check the shape by position or attribute, never by point or face order.** Join and merge renumber geometry.

## Process

- **Work from a ticket** (`docs/TICKETS.md`). New ideas go to `PARKING.md`, not into the ticket in hand.
- **Side-lane work happens in its own git worktree** and gets `mattpocock-skills:code-review` before merge. Gates get `ponytail:ponytail-review`. Log every review in TICKETS.md.
- **Commit at each checkpoint.** Messages end with the Co-Authored-By line. Claude never pushes; Mike runs `git push`.

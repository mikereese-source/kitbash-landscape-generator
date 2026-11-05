# 5.3 plan: front opening and cutter (draft for Mike's OK, 2026-11-05)

Scope as approved in PROJECT.md (D167): the cave object gets a real opening, with the shell cut at the front and the cut edge
welded shut into a natural rock lip; a much simpler cutter mesh is made from the shell and used with a Boolean modifier on any
mesh, Kits included; picking a cave in a landscape's panel carves it in watertight with masks (the 5.1 cut, D92).
No code until Mike approves. A checkpoint (board + short summary) after each step.

## What the references say (board docs/m5/c146, 7 entrances in `Terrain References\cave-entrances` + `cave-photos`)
- Openings are wide and low, about 2:1 to 4:1, at the foot of a cliff or slope (Falkensteiner, Dixon, Malanca, Mammoth).
- The lip follows the rock: a stack of rounded, stepped ledges rolling over into the ceiling, never a knife edge (Dixon, Falkensteiner).
- Seen from inside, the roof over the mouth is a slab about 0.1 to 0.3 of the opening's width thick (Vranja jama, Cathedral Caverns; Kitum is volcanic, used for the slab shape only).
- A breakdown or rubble slope runs in through the mouth (Malanca, Kitum).

## Steps

| Step | What | Size | Done when |
|---|---|---|---|
| 5.3a | **Open mouth.** The shell is cut where the passage meets the outside and the cut edge is turned out into a lip: the cut ring is pushed back into the rock as a rim about 0.15 of the entrance width thick (the reference slab), its edge rolled over in 2 to 3 rounded steps so it reads as bedded rock, not a knife edge. All quads, UVs keep their islands (the lip joins the passage island). | M | From outside you see an opening with a thick, rounded rim, not a thin shell; from inside, the roof slab over the mouth matches Vranja / Cathedral; T14 rewritten (the cave is open at the front only, otherwise closed) |
| 5.3b | **Cutter.** A separate, simple closed mesh made from the shell (a few thousand faces, shell only: no rocks, formations, drapes or puddle water sheet), a little bigger than the cave so a cut leaves room for the shell's thickness. An "Add Cutter" button puts it beside the cave, parented, and "Cut Selected" adds a Boolean (Difference, Exact or Manifold) to the selected meshes with the cutter as its object. | M | The cutter is manifold, under 5k faces, covers the shell everywhere by the clearance; a Boolean on a test block and on a KB3D Kit mesh leaves a watertight hole the cave sits in; new test T32 |
| 5.3c | **Carve into a landscape.** The landscape panel gets a Cave Object picker; the cave's cutter feeds the 5.1 watertight cut (D92) instead of the built-in cave shape, so masks are kept and the cave walls get them; the cave object sits in the hole. | M | Pick a cave on a Mesa or Cliffs landscape: one watertight surface, rim welded, masks on the cut walls, the cave visible through the mouth; T30 extended to a cave object |

## Questions for Mike
1. **Lip look:** is the rolled, stepped rim from Dixon and Falkensteiner the look? Default thickness about 0.15 of the entrance width, with a slider (Lip) from thin to thick?
2. **Cutter clearance:** how far outside the shell should the cutter sit, i.e. how thick the rock between the cave and the landscape's other faces? Default 1 voxel (about 3 to 5 m in a big cave)?
3. **Kits:** should Cut Selected leave a live Boolean modifier (editable, slower) or apply it (fast, final)? Default live.
4. **Old built-in landscape caves (5.1):** keep them as they are next to the new Cave Object picker, or replace them?

## Mike's calls (2026-11-05 discussion)
- Lip: yes, kept simple. The opening outline is noisy and irregular, never a clean planar cut.
- One lip shape for all rocks; each rock style adds its own surface (limestone rounded, jointed blocky pieces, lava tube smooth and slumped).
- Lip slider for thickness, default about 0.15 of the entrance width.
- Arch, not a full ring: the lip runs over the roof and down the walls; the walk-in floor stays flat and runs out of the mouth with no step.
- Cutter (5.3b) moves to the very end of M5: a very basic cave shape used only as a Boolean cutter, built as the last thing before M5 wraps up.
- Cutter clearance: about 1 voxel (3-5 m in a big cave) by default, with a slider.
- Cutter on Kits: a live Boolean modifier (editable). Kept basic: Add Cutter, then Blender's own Boolean; a Cut Selected button only if it stays trivial.
- 5.3c dropped (option A). The cave generator stays a standalone object; it goes into a host (Kit or landscape) with the basic cutter as a Boolean. Accepted cost: a Boolean into a landscape has no weld and no masks on the cut walls.
- The old built-in landscape caves (5.1) stay. They become the base for the M6 cave landscape types, with their own, simpler controls.

## Not in 5.3
The rubble slope running in through the mouth (the rocks already lie at the wall foot; a slope at the mouth could follow in 5.5 or M6),
moss/soil on the lip (M7 materials), the drawn path (5.2b).

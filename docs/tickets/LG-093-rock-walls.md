# LG-093 Rock walls: Glacial, Canyon (plus Mesa gullies, Badlands flats)
Type: feature | Milestone: Model realism | Phase: B2 Model realism | Size: L | Priority: P1
Status: todo | Lane: side | Needs Blender: yes | Mike review: yes
Depends on: LG-092 | Blocks: LG-082

## Why
First of the four tickets LG-082 was split into (Mike, 2026-11-28). After LG-077's breakup the creases on these types are near real, but the walls are not: LG-077 cp2 (2 km High, 1 m grid) measured Glacial over 60 deg 3.1% against Yosemite's 12.0% with relief 323 m against 1099 m, and Canyon over 60 deg 4.7% against the Grand Canyon's 2.6% with no flat benches (review section 3). LG-076 handed its Glacial and Canyon settings here; LG-080 left scree on these two types as a follow-up. Mike added two leftovers: Badlands flat ground (40.3% under 12 deg after LG-092, real 25.8%) and Mesa's evenly spaced gullies.

## Done when
- Glacial: walls steepen toward Yosemite (over 60 deg up from 3.1%) and the U profile survives; the hard band reaches down the wall (`hard_glacial`), summits stop reading as crowns (LG-079's hard map may be reused), and the breakup reads calmer, like massive granite. Try LG-076's incision 1.0 / soften 0.2. Tributaries that stop high on the wall only if the board shows they read
- Canyon: benches with flat treads and sheer risers (hard caps), sharp rims, flat plateau; over 60 deg not further above real (2.6%). Try LG-076's finish_blur 8
- Scree on Glacial and Canyon from LG-080's talus, in `lg_talus`
- Mesa: gully spacing varies (channel threshold from a low-frequency field, review section 3)
- Badlands: flat ground share moves toward real (under 12 deg from 40.3%, real 25.8%) with the pediment still smooth; T1 run straight after the change (CODING)
- Clay renders of Hero Butte (Mesa) and Mounds (Badlands)
- Each type measured against main and its real 1 m lidar window on the 1 m grid (LG-077's m77 measures); board per type beside its references; Mike signs off each type; every other type unchanged (its tests equal main); new test (claim the next free T) at the measured board values; build and re-evaluation time measured; suite passes; code review

## Files
- `kitbash_landscape_generator/types.json`, `erosion.py`, `nodes.py`, `node_groups.blend` (claim the next GROUP_VERSION), `__init__.py`
- `tests/run_tests.py`

## Agent brief
Read REVIEW-realism-2026-11.md section 3 (Glacial, Canyon, Mesa, Badlands) and S4 / S6, LG-076's Log (the S1 settings), LG-077's Log (cp2 numbers, board c200, Glacial busier than Yosemite), LG-079 (hard map), LG-080 (talus and its follow-ups), LG-090 (`erosion.trough()`, carved after the finishing smoothing) and LG-092's Log (Badlands numbers, T1's fragility). Measure scripts and lidar windows are on branches lg-077-cp2 and lg-092-rills. Do one type at a time and bring each board to Mike before the next.
Also read docs/tickets/README.md (rules every ticket follows) and docs/CODING.md.

## Log
- 2026-11-28 created: LG-082 split into four tickets (Mike: "Yes, as drafted"), with the Badlands flats and Mesa gullies added

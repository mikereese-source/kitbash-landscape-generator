# KitBash Landscape Generator — Design Doc

**Status:** Approved (2026-10-22)

## What we're building
A full Blender 5.2 add-on that replaces A.N.T. Landscape. It lives in its own **Landscape** tab in the 3D Viewport sidebar (N panel), which stays on screen while you work. You press **Add Landscape** there, pick a real landscape type from a thumbnail gallery, fit it to the size of your scene, then shape it with a handful of plain-language sliders. It stays live and non-destructive: every setting can be changed later. Built on Geometry Nodes, with a Python layer for the sidebar tab, gallery and presets.

## Who it's for
First the KitBash asset team (building scenes and Kit ground planes), then possibly customers. Today they use A.N.T. Landscape, which comes in tiny, loses its shapes when scaled up, names its options after maths ("Hetero Terrain", "lacunarity"), and writes a dead mesh.

## Desired outcomes
- An artist gets a believable landscape of the right size in under a minute, without touching an advanced setting.
- Scaling a landscape from 10 m to 1 km keeps the same mountains, valleys and cliffs. Only the size changes.
- Every control has a name and a tooltip a non-specialist understands.
- The landscape comes out already textured (rock, grass, sand, snow) from its own slope and height.
- Cliffs can overhang, and the tool can make caves, arches, stalactites and stalagmites — which no Blender terrain tool on Superhive does today.

## Boundaries
**In scope (v1)**
0. **Its own sidebar tab.** A "Landscape" tab in the N panel, not an Add > Mesh entry. The first look is simple: an Add Landscape button, a type gallery with thumbnails, size, and the six main controls. Advanced settings, cliff features, masks and material sit in collapsible sections below. A list at the top shows every landscape in the scene, so you can switch between them.
1. **Scale to scene.** Size X/Y in meters plus a "Fit to selection" button that sizes the landscape to the selected objects. Shapes are sampled in normalized space, so they survive any size. Height scales with size. Detail is set in meters per vertex, with Preview and Final resolution.
2. **14 landscape types** (thumbnail gallery, each with its own tuned recipe): Rolling Hills, Mountains, Sand Dunes, Seabed, Coastal Cliffs, Canyon, Mesa, Badlands, Volcanic (lava fields and cinder cones), Volcano (styles: Stratovolcano, Shield, Cinder Cone, Caldera; controls: Crater Size, Steepness, Gullies, Breach), Glacial Valley, Riverbed, Cratered Surface (impact craters; Crater Count, Crater Size, Age), Cave. Types may have a **style picker** for variants.
3. **Six main controls:** Height, Feature Size, Roughness, Peak Sharpness (renamed from Sharpness 2026-10-23), Erosion, Seed (with a Randomize button). Everything else sits in a closed Advanced section.
4. **Cliff features** (toggles that work on any type): Side Cliffs, Overhangs, Arches, Stalactites, Stalagmites.
4b. **Cave systems always start with an entrance.** Three layouts: **Entrance** (a grotto cut into a slope), **Entrance + Tunnel** (the entrance extends into a winding passage), and **Entrance + Cavern** (the passage opens into a large chamber). The entrance sits on a steep face found from the slope mask, facing a direction the user can turn. Tunnel controls: Length, Width, Wiggle, Descent. Cavern controls: Size, Ceiling Height. Works on any landscape type (mountains, cliffs, mesa, canyon), and the Cave type uses it by default.
5. **Terraces and rock layers** (strata) on the rock types: Mesa, Canyon, Badlands, Coastal Cliffs and Mountains (D74).
6. **Data masks** stored on the mesh as named attributes: height, slope, curvature, flow (where water runs), wear (where erosion cut), deposits (where sediment settles) and water depth, with a viewer (D74, D75, D77). A **water level** with a plain material (D77).
7. **Erosion slider:** thermal erosion (slopes slump to a natural angle) plus water gullies that follow the flow mask.
8. **Auto-material:** rock on steep faces, grass or ground on flats, sand or sediment in deposits, snow up high. Built from the masks. Uses box (triplanar) mapping so caves without UVs still texture correctly.
9. **Preview / Final toggle and Bake,** so editing stays fast and heavy steps (erosion, caves) are computed once.

**Out of scope (explicitly)** — see PARKING.md
- Stamps and curve tools (river curve, crater, volcano cone)
- Seamless tiling and heightmap export
- Asset scattering (rocks, trees)
- Real droplet-by-droplet hydraulic erosion
- The three.js / Cargo version. That is Project 2, its own build after this one (D7). v1 keeps the door open (D5)

## How it works (architecture)
Pipeline, one Geometry Nodes modifier on one object:
1. **Grid** at the requested size and resolution.
2. **Shape:** the type's noise recipe, sampled on position ÷ size (normalized), height × size.
3. **Terraces** (optional).
4. **Erosion** (repeat zone; baked at Final).
5. **Masks** written as named attributes.
6. **Volume stage** (only when a cave or cliff feature is on): mesh → SDF grid → boolean cave/arch/overhang shapes → stalactite and stalagmite shapes → back to mesh. Baked at Final.
7. **Material** reads the masks.

Type recipes live in one JSON file of plain parameters (not hard-coded in node trees), so new types are a data change and a future web version can read the same file.

## Clickable prototype
- Link: https://claude.ai/artifact/3q2sd89zXBpTX2LemT8Bd1 (v1, 2026-10-22). Shows: an HTML mock of the Landscape sidebar tab: landscape list, Add Landscape, type gallery with thumbnails, size and Fit to selection, six controls, collapsible Cliffs & Caves, Erosion, Material and Advanced sections)
- Approved: 2026-10-22 (v9)
- Notes from review: Add Landscape button moved to the top with a fixed plain label (D12); cave layout picker added (D10); "Rocky Mountains" renamed "Mountains".

## Key flows
1. **New landscape:** open the Landscape tab → pick a type from the gallery → Add Landscape → it lands at the 3D cursor → Fit to selection (or type a size) → adjust the six controls → switch to Final → Bake.
2. **Rescale later:** change Size → shapes stay, detail rebuilds at the same meters per vertex.
3. **Add a cave:** turn on Overhangs or pick the Cave type → set count and size → Bake.
4. **Try variations:** press Randomize until a layout fits, then fine-tune.

## Risks and limits in Blender
- **Panel styling is Blender's own.** Add-ons can't use custom CSS or fonts. "Looks cool and robust" comes from thumbnail galleries, icons, clear sections and good spacing inside Blender's widget set.
- **Caves are heavy.** The SDF stage needs many voxels for a large landscape. Plan: Preview at coarse voxels, Final baked. Verified spike before M6 (see PROJECT.md).
- **Caves lose UVs.** Solved by box mapping in the material.
- **Live erosion is slow.** Real droplet erosion is out of scope; thermal erosion plus flow gullies is fast enough with a bake.
- **Geometry Nodes can't save image files.** Heightmap export (parked) would need a small Python step.
- **License:** Blender add-ons are GPL. The add-on ships GPL. A future web version must be written fresh (no copied Blender code) to stay free of GPL.

## Open questions
- Who is v1 for: team only, or a customer release on Cargo or Superhive?
- Default Final resolution budget (vertices) for a typical team machine?
- ~~Should "Fit to selection" also sit the landscape under the selection's lowest point?~~ No: placement is the 3D cursor (D28).

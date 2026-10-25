# P2 Cave Spike — Results (2026-10-22)

**Question:** Can Blender 5.2 Geometry Nodes carve a cave with stalactites and stalagmites into a landscape fast enough to keep caves in v1?

**Answer: Yes. Caves stay in v1**, with one design change for big landscapes (see "What this changes").

## What was built
- File: `E:\Projects\3D\Terrain Generator_Build\Terrain Generator_Build_01.blend`, collection `LG_Spike`, object `LG_Spike_Cave`, node group `LG_Spike_CaveSDF`. Throwaway: it is not add-on code.
- 200 m × 200 m landscape (noise sampled on position ÷ size, plus a central hill), with a noise-warped cave chamber 64 m × 32 m × 16 m inside the hill.
- Stalactites hang from the cave ceiling and stalagmites stand on the floor (random lengths 1.5–5.5 m), placed with a Voronoi pattern.
- One signed-distance field built from math: terrain, minus cave, plus spikes. Then `Field to Grid` on a `Cube Grid Topology`, then `Grid to Mesh`. A Cutaway toggle slices the mesh at y = 0 for viewing.

Renders: `spike/p2-cave-cutaway.png` (cross-section showing the cave, stalactites and stalagmites) and `spike/p2-overview.png`.

## Numbers (200 m landscape, 64 m tall volume)
| Voxel size | Voxels | Build time | Vertices | Extra memory |
|---|---|---|---|---|
| 1.0 m | 3 M | 0.14 s | 113 k | small |
| 0.5 m | 20 M | 1.0 s | 470 k | ~0.2 GB |
| 0.25 m | 164 M | 8.1 s | 1.9 M | ~1.3 GB peak |

Takeaway: 0.5 m is live-editable. 0.25 m is fine as a baked Final.

## What this changes for the design
- **A dense volume grows with the cube of the size.** A 1 km landscape at 0.5 m would be about 2 billion voxels, which is not workable. So for large landscapes the volume stage must not cover the whole tile. Two options to settle in M6:
  1. **Local volume patch:** only the area around caves and overhangs goes through the volume. The rest stays a fast heightfield mesh, blended at the seam.
  2. **Sparse SDF:** `Mesh to SDF Grid` keeps only a thin band around the surface, so memory follows surface area, not volume. Then `SDF Grid Boolean` with the cave shapes.
- The spikes need more detail than 0.5 m to look sharp. Plan: build the spikes as instanced cone meshes (from the research), not from voxels.
- Everything closes into a solid block at the volume's edges, which is good for a Kit-ready tile.

## Blender 5.2 API notes (for the build)
- Modifier inputs are set with `mod.properties.inputs.Socket_N.value`. The old `mod["Socket_N"]` no longer works.
- `Grid to Mesh` treats values **above** the threshold as solid, so feed it negative distance (density).
- The region touching the grid bounds gets capped. Clamp with a box distance so the air stays open.
- `Field to Grid` needs a grid item added (`grid_items.new('FLOAT', name)`) and evaluates densely over the topology bounds.

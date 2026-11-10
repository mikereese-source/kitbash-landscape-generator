# Landscape package spec

One folder layout that every version writes and reads: Blender (6.3b export, M8 import), three.js / Cargo, Unreal (Project 3), and maybe Cinema 4D. Written once so no app needs a format change later (D198, D203; LG-022). Builds on the package in PLAN-unreal.md.

## Folder

```
<name>.kblandscape/
  recipe.json          the recipe: rebuilds the landscape in any app
  height.png           16-bit grayscale heightmap (or height.exr, 32-bit float)
  height.r16           raw 16-bit little-endian, Unity's RAW (only when asked for)
  masks.exr            the masks as channels, same size as the heightmap
  splat_0.png          RGBA weight map: rock, scree, sand, grass (16-bit)
  splat_1.png          RGBA weight map: snow, wet, sediment, forest floor (16-bit)
  caves/<cave>.glb     each cave or overhang as its own mesh (D89), placed in landscape space
  preview.jpg          1024 px thumbnail
```

`.kblandscape` is a plain folder. Zipped for Cargo downloads.

## recipe.json

```json
{
  "format": "kblandscape",
  "version": 1,
  "app": "blender 0.x",
  "units": "meters",
  "size": [800.0, 800.0],
  "height_range": [-12.5, 187.3],
  "tiles": [
    {
      "grid": [0, 0],
      "type": "volcano",
      "style": "caldera",
      "controls": { "height": 0.18, "roughness": 0.5, "erosion_amount": 0.6 },
      "seed": 4242
    }
  ],
  "blend_width": 0.1,
  "water": { "on": true, "level": 0.4 },
  "base": { "on": false, "depth": 20.0 },
  "material": {},
  "caves": [ { "file": "caves/cave_1.glb", "location": [10.0, -40.0, 3.0], "recipe": {} } ]
}
```

- **`tiles` is a list from day one** (D203). A single landscape is one tile at `[0, 0]`. M7b fills in more tiles and `blend_width`.
- **`controls`** uses the same keys as presets, so presets and packages share code. Unknown keys are skipped on load, so newer files still open in older apps.
- **`height_range`** is in meters: the heightmap's black and white points.
- **`material`** is empty until M7 (snow line, rock angle and the other dials).
- **`caves[].recipe`** is the cave's own settings (as cave presets), so an app that can build caves rebuilds it; others use the `.glb`.

## Heightmap and masks

| Item | Rule |
|---|---|
| Sizes | 1009, 2017, 4033 for Unreal; Unity takes 2^n + 1 too (1025, 2049, 4097). Pick on export; default 2017 |
| Bit depth | 16-bit PNG by default; EXR 32-bit float when asked |
| Orientation | Image top = landscape +Y edge; left = -X. Pixel centres sit on the grid points, corners on the landscape corners |
| Height mapping | 0 = `height_range[0]`, 65535 = `height_range[1]` |
| Base and water | Left out: the base's sides (`lg_base`) and the water sheet are not heights (LG-070) |
| Caves | Not in the heightmap. Unreal cuts a landscape hole where a cave opens (D89) |
| Masks (`masks.exr`) | Channels named as the attributes: `lg_height`, `lg_slope`, `lg_curvature`, `lg_flow`, `lg_wear`, `lg_deposit`, `lg_depth`, each 0-1 |
| Splat maps | Weights per pixel add up to 1 across both files. Until M7 they are computed from the masks with the default dials |

## Rules

- **Exporters write every file, importers read what they need.** Blender rebuilds from `recipe.json` and uses `height.png` only when the recipe can't be rebuilt (an unknown type, or a hand-sculpted landscape later). Unreal uses both, the recipe for shape and the maps for erosion and layers.
- **One test per app:** export, import, compare. The heights match within one 16-bit step, and the masks within 1%.

## Decided (Mike, 2026-11-10, D206)

1. **Blender gets the full export.** Blender is the test bed for the package: the heightmap and every other export are built there first to work the format out, then three.js and Unreal follow the same spec. This replaces PLAN-unreal.md's "the Blender add-on receives, it doesn't hand on".
2. **Folder name:** the landscape's own name plus `.kblandscape`, e.g. `Volcano Caldera.kblandscape/`.
3. **Default size:** 2017, the Unreal-friendly size; revisit if better data on a default turns up.

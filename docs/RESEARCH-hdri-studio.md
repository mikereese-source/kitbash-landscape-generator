# Chad's HDRI Studio framework: what Project 2 takes from it (2026-10-27)

Source: `KitBash3D-Dev/hdri-studio` (read-only clone), its design system in `design-system/project/` (README,
1-layout … 5-checklist, component cards), `src/studio/`, and `hdri-studio-spec.md`. The published Design
System artifact holds the same package. HDRI Studio is a React 19 + three.js (react-three-fiber) tool with
Radix UI and Tailwind tokens, and it follows the Cargo family look.

## What we adopt as-is (D84)
- **Layout, three fixed columns:** left 322 px to **select** (list and library), centre viewport to
  **manipulate**, right 280 px to **adjust** (the attribute panel). The top bar holds file actions on the left
  and the one brand action on the right ("Export…"). View-only toggles float over the viewport.
- **Attribute panel:** a header (editable name + a meta line), then sections of 2–6 rows, a 92 px label
  column and 28 px rows. Sections are grouped by the question the user is answering. Rows that don't apply are
  hidden, not disabled. No accordions.
- **One control per kind of value:** `ScrubField` for every number (drag, Shift for fine, click to type; no
  slider-plus-box), `Segmented` for 2–4 choices, `Select` for 5+, `ColorInput`/`ColorPicker`, an icon toggle
  for lock/link. An optional feature is switched on in its section's aside, as a `Segmented` with **Off** first.
- **Words:** sentence case, verbs on buttons, the user's word not the code's, hints that give a reference
  value ("Stops: +1 doubles the light").
- **Foundations:** a single dark theme, semantic tokens only, Geist at 12/15 px, the corner and size ladders,
  lime as the one brand action per view, hairline borders, shadows only on floating things.
- **Presets** (PresetsMenu, presetStore) and a **"lucky" dice** (LuckyButton) = our presets and Randomize.

## Patterns worth copying for the landscape export
- **The editable recipe rides inside the export.** `exportHdri.ts` embeds the studio JSON as an EXR/HDR
  attribute, so an exported file opens again for editing. Our package does the same: `recipe.json` inside, so
  anything sent to Blender or Unreal can come back to Cargo and be edited.
- **Big renders are written in strips with progress** (`compositor.exportStrips`, `onProgress`). That's the
  pattern for 4K–8K heightmap and mask export in the browser without running out of memory.
- **Live link to a DCC** (`liveLink.ts`): the studio keeps one EXR on disk in step (2K half-float, written
  ~150 ms after you stop dragging, swapped in atomically), and a Cinema 4D tag watches the file. A landscape
  version could keep the package on disk in step, while Blender rebuilds through the MCP or a small bundled
  watcher. Worth a spike for "edit in Cargo, see it in Blender".
- **Its own file format** (`.hdristudio`, `studioFile.ts`) with assets packed in. Ours: a `.kblandscape` package.

## How our controls map onto it
| Ours (Blender add-on) | In the Cargo version |
|---|---|
| Landscape list + type gallery | Left panel: the landscapes in the scene; the type library (grouped like D65) |
| Viewport | Centre; the mask viewer, water preview and detail level float over it as view toggles |
| Shape: Height, Feature Size, Roughness, Sharpness, per-type sliders | Right panel, first section named after the type ("Mountains"): ScrubFields |
| Style | `Segmented` (2–4 styles) or `Select` (Volcano has 5) at the top of the first section |
| Erosion Amount | Its own section "Erosion", Off first in the aside, then Amount |
| Terraces | Section "Terraces", Off / On in the aside; Count, Strength, Tilt |
| Water | Section "Water", Off / Lake / Sea in the aside; Level (and the M5 shader dials) |
| Masks | A view toggle in the floating bar (Grayscale / Heatmap), not a panel setting |
| Seed + Randomize | The dice beside the type name (LuckyButton) |
| Presets | PresetsMenu in the top bar or the left panel |
| Size, Detail Level | A "Size" section; Detail Level as a view toggle (Preview / High) |
| Export | The one lime brand button: "Send to Blender", "Send to Unreal", "Export package…" |

## What we must add ourselves
The export layer (the Blender data package with build instructions, the Unreal package, later more DCCs), the
landscape engine (shared noise/shape core, WebGPU erosion), materials, water, fog/clouds, and scatter. The
framework gives the shell, the controls and the look.

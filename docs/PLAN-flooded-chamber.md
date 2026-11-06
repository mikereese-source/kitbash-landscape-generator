# Flooded chamber plan (draft for Mike's OK, 2026-11-05)

Mike (D189): a Water switch, Puddles (as now) or Flooded Chamber: the whole chamber filled, the formations still standing in it.
No code until Mike answers the questions below. One checkpoint (board against the references) at the end.

## What the references say (board docs/m5/c151, `Terrain References\cave-flooded-chambers`, 6 photos, Wikimedia Commons)
- The water is one flat, still sheet across the chamber floor, a mirror (Crystal Cave Bermuda, Martel Lake in Drac, Jeita-style lit lake).
- The walls run straight down into it; there is no beach, the shore is wherever the wall meets the level.
- Stalactites hang to just above the water and double in the reflection; none dip in (they don't grow under water).
- Stalagmites and columns rise out of the water (Drac: columns standing in the lake); the floor shows through near the edge when the water is clear (Martel Lake).
- A path or ledge often runs along one side above the level (Drac, Bermuda): here, the passage floor coming in above the lake.

## How it would work
One flat water sheet at the water level across the chamber, cut to the cave's own space and run a little into the walls so its
edge hides behind them (no visible seam, watertight-looking shore). Same plain water material and lg_water mark as the puddles,
lg_depth filled under it for the M7 water shader. Everything else (shell, rocks, formations) stays as it is, except:
stalactites whose tips would reach the water are left out, and stalagmites that would be fully under water are left out.

| Step | What | Size | Done when |
|---|---|---|---|
| F1 | Water switch (Puddles / Flooded Chamber) and a Water Level slider; the flat sheet in the chamber | S | The sheet fills the chamber wall to wall at the level, no gaps or seams at the shore at Preview, High and Ultra |
| F2 | Formations against the water: no stalactite tip in it, no stalagmite fully under it | S | Counted: none breaks either rule; same pieces at every level (T32 rule) |
| F3 | Test (T33) and a board against c151 | S | T33 passes; board side by side with the references |

## Questions for Mike
1. **Water Level control:** a slider from the chamber floor (0) up to the passage floor (1), so the passage stays dry and you walk in onto the shore? Default 0.6?
2. **Rocks:** Flooded Chamber for all three rocks (jointed sea caves flood too), or limestone only like Puddles today?
3. **Switch shape:** one Water setting with three choices: None, Puddles, Flooded Chamber (Puddles amount slider shows only for Puddles)?
4. **Rubble under water:** keep the rocks and heaps under the water (they show through in shallow, clear water), or leave them out below the level?

## Not in this
Water shading, reflections, caustics and murk (M7 materials); water in the passage; waterfalls or streams.

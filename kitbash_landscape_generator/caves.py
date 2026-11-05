# SPDX-License-Identifier: GPL-3.0-or-later
"""The cave object (M5 step 5.2, D93): a standalone cave you place in the scene like the butte, sized in real
meters, then carve into a landscape or use as a Boolean cutter on any mesh."""

import random

import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, IntProperty, PointerProperty
from bpy.types import Operator, PropertyGroup

from . import features, formations, nodes, rocks

CAVE_MODIFIER = "KB Cave"


def cave_modifier(ob):
    if ob is None or not ob.lg_cave.is_cave:
        return None
    return next((m for m in ob.modifiers if m.type == 'NODES' and m.node_group
                 and m.node_group.name.startswith(features.CAVE_GROUP)), None)


# prop -> group input
CAVE_SOCKETS = {"width": "Entrance Width", "height": "Entrance Height", "depth": "Depth", "wiggle": "Wiggle",
                "turn": "Turn", "drop": "Drop", "narrowing": "Narrowing", "chamber": "Chamber Size",
                "ceiling": "Ceiling Height", "chamber_drop": "Chamber Drop", "ramp": "Ramp", "rubble": "Rubble", "wall_shape": "Wall Shape",
                "roughness": "Roughness", "seed": "Seed", "rock_size": "Rock Size", "stretch": "Stretch", "tilt": "Tilt",
                "spread": "Spread", "formations": "Formations", "formation_size": "Formation Size",
                "formation_stretch": "Formation Stretch", "clusters": "Clusters", "puddles": "Puddles",
                "drape_length": "Drape Length", "drape_fullness": "Drape Fullness", "drape_fold": "Drape Fold"}


def sync_cave(ob):
    mod = cave_modifier(ob)
    if mod is None:
        return
    # A cave saved with an older add-on catches up: its group rebuilt to this version (Mike, D189: an old cave
    # kept the 178 group, which had no Drape Lines input, and its sliders stopped reaching the cave).
    if mod.node_group.get("kb_version") != features.CAVE_VERSION:
        mod.node_group = features.cave_group()
    fill_kits(ob.lg_cave)
    for prop, sock in CAVE_SOCKETS.items():
        nodes.input_socket(mod, sock).value = getattr(ob.lg_cave, prop)
    nodes.input_socket(mod, "Detail").value = DETAIL_INDEX[ob.lg_cave.detail]
    nodes.input_socket(mod, "Rock").value = ROCK_INDEX[ob.lg_cave.rock]
    nodes.input_socket(mod, "Show Mask").value = MASK_INDEX[ob.lg_cave.show_mask]
    nodes.input_socket(mod, "Mask Heatmap").value = ob.lg_cave.mask_colors == 'HEAT'
    nodes.input_socket(mod, "Drape Lines").value = ob.lg_cave.drape_lines
    # No rocks picked (an older cave, or the pick cleared): the library's own family.
    for use, kit in (("Rubble", ob.lg_cave.rubble_rocks or rocks.family("Blocks")), ("Scree", ob.lg_cave.scree_rocks or rocks.family("Scree"))):
        for (size, *_), coll in zip(rocks.SIZES, rocks.sizes(kit)):
            nodes.input_socket(mod, f"{use} {size}").value = rocks.at_level(coll, ob.lg_cave.detail.title())
    # Stalactites, stalagmites, columns and lava drips (5.4): the formation library's kits; the cave's Rock picks
    # which of them grow (D168). Any collection can be put on the modifier's inputs instead.
    for fam, prop in FORMATION_KITS.items():
        kit = getattr(ob.lg_cave, prop) or formations.family(fam)
        for (size, *_), coll in zip(formations.SIZES, formations.sizes(kit)):
            nodes.input_socket(mod, f"{fam} {size}").value = rocks.at_level(coll, ob.lg_cave.detail.title())
    # Rebuild the scene's links to the rocks just swapped in (each Detail Level uses its own rock meshes):
    # setting the inputs alone left Blender unaware of the new ones, so they came out empty and a Jointed
    # cave, which cuts its wall masses from them, wiped itself at Ultra after a visit to High (Mike).
    mod.node_group = mod.node_group
    ob.update_tag()



# Formation family -> the cave's kit picker (empty: the library's own); lava drips are not placed (D171).
FORMATION_KITS = {"Stalactites": "stalactite_kit", "Stalagmites": "stalagmite_kit", "Columns": "column_kit",
                  "Stalactite Clusters": "stalactite_cluster_kit", "Stalagmite Clusters": "stalagmite_cluster_kit", "Drapes": "drape_kit"}

DETAIL_ITEMS = (('PREVIEW', "Preview", "Light and fast, for placing and shaping the cave"),
                ('HIGH', "High", "Full rock detail for the finished cave"),
                ('ULTRA', "Ultra", "Hero detail for close-up shots inside the cave. Heavy"))
DETAIL_INDEX = {key: i for i, (key, _n, _d) in enumerate(DETAIL_ITEMS)}
# The landscapes' maps, read for a cave (same names, same order, so materials and exports treat them alike).
MASK_ITEMS = (
    ('NONE', "None", "Normal shading"),
    ('HEIGHT', "Height", "Low (dark) to high (bright)"),
    ('SLOPE', "Slope", "Floor and roof (dark) to standing walls (bright)"),
    ('CURVATURE', "Curvature", "Ridges and edges dark, crevices and hollows bright, even rock in between"),
    ('FLOW', "Flow", "Where water runs and pools: the floor's hollows"),
    ('WEAR', "Wear", "Ridges and edges, where rock gets knocked and worn"),
    ('DEPOSIT', "Deposit", "The flat floor and its hollows, where silt and grit settle"),
    ('DEPTH', "Water Depth", "Empty until caves get water"),
)
MASK_INDEX = {key: i for i, (key, _n, _d) in enumerate(MASK_ITEMS)}


_filling = False


def fill_kits(props):
    """Empty formation pickers show the library's own kit, as the rock pickers do (Mike, D189: empty read as
    nothing loaded). Set quietly: each set would otherwise run a full sync."""
    global _filling
    _filling = True
    try:
        for fam, prop in FORMATION_KITS.items():
            if getattr(props, prop) is None:
                setattr(props, prop, formations.family(fam))
    finally:
        _filling = False


def _sync(props, _context):
    if not _filling:
        sync_cave(props.id_data)


def _show_mask(props, context):
    from . import _show_mask_changed  # the landscapes' viewer: sets every 3D view to show lg_view
    _show_mask_changed(props, context)


ROCK_ITEMS = (('LIMESTONE', "Limestone", "Flat rock beds stepping in and out, flat roofs between them; blocks and slabby scree"),
              ('JOINTED', "Jointed", "Long straight fractures standing the walls in flat faces, as in sea caves and cliffs; angular blocks"),
              ('LAVA', "Lava Tube", "A smooth round tube with long flow ledges along the walls; lava rubble"))
ROCK_INDEX = {key: i for i, (key, _n, _d) in enumerate(ROCK_ITEMS)}
ROCK_KITS = {'LIMESTONE': ("Blocks", "Scree"), 'JOINTED': ("Blocks", "Scree"), 'LAVA': ("Lava", "Lava")}


def _rock_changed(props, _context):
    """A new Rock brings its own rock kits (pick others after, if you like)."""
    rubble, scree = ROCK_KITS[props.rock]
    props.rubble_rocks, props.scree_rocks = rocks.family(rubble), rocks.family(scree)
    sync_cave(props.id_data)


class LG_CaveProps(PropertyGroup):
    is_cave: BoolProperty(default=False)
    show_mask: EnumProperty(name="Show Mask", description="Colour the viewport by one of the cave's data maps, the maps materials and exports use",
                            items=MASK_ITEMS, default='NONE', update=lambda p, c: _show_mask(p, c))
    mask_colors: EnumProperty(name="Colours", description="How the map viewer shows a map",
                              items=(('GRAY', "Grayscale", "Black (0) to white (1), as game engines and material editors show these maps"),
                                     ('HEAT', "Heatmap", "Dark blue (0) through teal to yellow (1): easier to read small differences")),
                              default='GRAY', update=_sync)
    width: FloatProperty(name="Entrance Width", description="How wide the cave mouth is, in real size",
                         default=12.0, min=0.5, soft_max=200.0, unit='LENGTH', update=_sync)
    height: FloatProperty(name="Entrance Height", description="How tall the cave mouth is, floor to roof, in real size",
                          default=6.0, min=0.5, soft_max=100.0, unit='LENGTH', update=_sync)
    depth: FloatProperty(name="Depth", description="How far the cave runs back from the mouth",
                         default=30.0, min=1.0, soft_max=500.0, unit='LENGTH', update=_sync)
    wiggle: FloatProperty(name="Wiggle", description="A straight passage (0), or one that winds from side to side: swinging right first (+) or left first (-)",
                          default=0.3, min=-1.0, max=1.0, update=_sync)
    turn: FloatProperty(name="Turn", description="Bend the passage: left (-1), straight (0) or right (+1)",
                        default=0.0, min=-1.0, max=1.0, update=_sync)
    drop: FloatProperty(name="Drop", description="How far the floor falls from the mouth to the back. 0 keeps it level",
                        default=0.0, min=-50.0, soft_max=100.0, unit='LENGTH', update=_sync)
    narrowing: FloatProperty(name="Narrowing", description="Same size all the way back, or closing in toward the end",
                             default=0.4, min=0.0, max=0.75, subtype='FACTOR', update=_sync)
    chamber: FloatProperty(name="Chamber Size", description="A big chamber at the back of the cave, this wide. 0 for none",
                           default=0.0, min=0.0, soft_max=200.0, unit='LENGTH', update=_sync)
    ceiling: FloatProperty(name="Ceiling Height", description="How tall the chamber is, floor to ceiling",
                           default=10.0, min=1.0, soft_max=150.0, unit='LENGTH', update=_sync)
    chamber_drop: FloatProperty(name="Chamber Drop", description="Sink the chamber's floor below the passage, so it opens out into a big space",
                                default=0.0, min=0.0, soft_max=100.0, unit='LENGTH', update=_sync)
    ramp: BoolProperty(name="Ramp into Chamber", description="A rocky ramp from the passage down into the sunk chamber, so it can be walked down. Off: a drop to climb or jump",
                       default=False, update=_sync)
    rubble: FloatProperty(name="Rubble", description="How much fallen rock lies along the foot of the walls: none (0) to a lot (1). Rock Size sets how big",
                          default=0.5, min=0.0, max=1.0, subtype='FACTOR', update=_sync)
    wall_shape: FloatProperty(name="Wall Shape", description="Smooth walls (0), or big bulges, recesses and alcoves shaped by the rock (1)",
                          default=0.5, min=0.0, max=1.0, subtype='FACTOR', update=_sync)
    roughness: FloatProperty(name="Roughness", description="Smooth, water-worn walls, or rough broken rock",
                             default=0.5, min=0.0, max=1.0, subtype='FACTOR', update=_sync)
    seed: IntProperty(name="Seed", description="Same seed, same cave. Change it for a new winding and rock",
                      default=0, min=0, max=99999, update=_sync)
    detail: EnumProperty(name="Detail Level", description="How finely the cave's rock is built: light while placing it, heavy for the finished shot",
                         items=DETAIL_ITEMS, default='PREVIEW', update=_sync)
    rock_size: FloatProperty(name="Rock Size", description="Make every rock smaller or bigger",
                             default=1.0, min=0.1, soft_max=3.0, update=_sync)
    stretch: FloatProperty(name="Stretch", description="Square rocks (0), or drawn out long, like slabs of slate (1)",
                           default=0.3, min=0.0, max=1.0, subtype='FACTOR', update=_sync)
    tilt: FloatProperty(name="Tilt", description="Rocks lying flat (0), or tipped every which way (1)",
                        default=0.5, min=0.0, max=1.0, subtype='FACTOR', update=_sync)
    spread: FloatProperty(name="Spread", description="Rocks kept tight to the walls (0), or strewn out across the floor (1)",
                          default=0.5, min=0.0, max=1.0, subtype='FACTOR', update=_sync)
    formations: FloatProperty(name="Formations", description="How many stalactites, stalagmites and columns grow along the roof's cracks and ledges in limestone: none (0) to a lot (1). Lava and jointed rock grow none",
                              default=0.5, min=0.0, max=1.0, subtype='FACTOR', update=_sync)
    # As the rocks' controls (Mike): how big, how drawn out, how many grow as clusters, and which kits.
    formation_size: FloatProperty(name="Formation Size", description="Make every stalactite, stalagmite and column smaller or bigger (never under 2 ft)",
                                  default=1.0, min=0.1, soft_max=3.0, update=_sync)
    formation_stretch: FloatProperty(name="Stretch", description="Short and stubby (0), or long and thin (1)",
                                     default=0.5, min=0.0, max=1.0, subtype='FACTOR', update=_sync)
    clusters: FloatProperty(name="Clusters", description="Single pieces (0), or many grown together into clusters (1)",
                            default=0.85, min=0.0, max=1.0, subtype='FACTOR', update=_sync)  # mostly clusters (Mike)
    stalactite_kit: PointerProperty(name="Stalactites", type=bpy.types.Collection, update=_sync,
                                    description="The stalactite kit: a collection with Big and Medium collections inside (or one plain collection)")
    stalagmite_kit: PointerProperty(name="Stalagmites", type=bpy.types.Collection, update=_sync,
                                    description="The stalagmite kit: a collection with Big and Medium collections inside (or one plain collection)")
    column_kit: PointerProperty(name="Columns", type=bpy.types.Collection, update=_sync,
                                description="The column kit: a collection with Big and Medium collections inside (or one plain collection)")
    stalactite_cluster_kit: PointerProperty(name="Stalactite Clusters", type=bpy.types.Collection, update=_sync,
                                            description="The stalactite cluster kit: a collection with Big and Medium collections inside (or one plain collection)")
    stalagmite_cluster_kit: PointerProperty(name="Stalagmite Clusters", type=bpy.types.Collection, update=_sync,
                                            description="The stalagmite cluster kit: a collection with Big and Medium collections inside (or one plain collection)")
    # Drapes are drawn, not scattered (Mike, D185): a curve drawn on the roof, each line a continuous curtain.
    drape_lines: PointerProperty(name="Drape Lines", type=bpy.types.Object, update=_sync, poll=lambda _self, o: o.type in {'CURVE', 'CURVES'},
                                 description="A curve drawn on the cave's roof (Draw tool, projected onto the surface): each line hangs a curtain of drapes")
    drape_length: FloatProperty(name="Drape Length", description="How far the curtains hang: short (0) to long (1), never past a third of the way to the floor",
                                default=0.5, min=0.0, max=1.0, subtype='FACTOR', update=_sync)
    drape_fullness: FloatProperty(name="Fullness", description="A broken row with gaps (0), or one solid curtain along each line (1)",
                                  default=0.8, min=0.0, max=1.0, subtype='FACTOR', update=_sync)
    drape_fold: FloatProperty(name="Fold", description="Shallow ripples (0) to deep folds (1)",
                              default=0.5, min=0.0, max=1.0, subtype='FACTOR', update=_sync)
    drape_kit: PointerProperty(name="Drapes", type=bpy.types.Collection, update=_sync,
                               description="The drape kit: a collection with Big and Medium collections inside (or one plain collection)")
    puddles: FloatProperty(name="Puddles", description="Water in hollows of the limestone floor's silt flats: none (0) to many (1). Plain water for now; the full water shader comes with the materials",
                           default=0.5, min=0.0, max=1.0, subtype='FACTOR', update=_sync)
    rock: EnumProperty(name="Rock", description="What the cave is cut in: it sets the walls and the rocks lying in it",
                       items=ROCK_ITEMS, default='LIMESTONE', update=_rock_changed)
    # Which rock kits: rocks.py builds KB Cave Rocks (four kits, each Big / Medium / Small); any collection works.
    rubble_rocks: PointerProperty(name="Rubble Rocks", type=bpy.types.Collection, update=_sync,
                                  description="The rock kit fallen along the foot of the walls: a collection with Big, Medium and Small collections inside (or one plain collection of rocks)")
    scree_rocks: PointerProperty(name="Scree Rocks", type=bpy.types.Collection, update=_sync,
                                 description="The rock kit on the ramp's slopes: a collection with Big, Medium and Small collections inside (or one plain collection of rocks)")


class LG_OT_randomize_cave(Operator):
    bl_idname = "landscape.randomize_cave"
    bl_label = "Randomize"
    bl_description = "Try a new cave with the same settings: new rock, swings and talus (new seed)"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.lg_cave.is_cave

    def execute(self, context):
        props = context.active_object.lg_cave
        props.seed = (props.seed + random.randint(1, 99998)) % 100000  # always a different seed
        return {'FINISHED'}


# What Reset puts back and what a preset keeps: every setting except Seed and Detail Level (as on the
# landscapes, Reset keeps the layout and detail you picked).
SHAPE_PROPS = ("width", "height", "depth", "wiggle", "turn", "drop", "narrowing", "chamber", "ceiling", "chamber_drop",
               "ramp", "roughness", "rubble", "wall_shape", "rock_size", "stretch", "tilt", "spread", "rock", "formations",
               "formation_size", "formation_stretch", "clusters", "puddles", "drape_length", "drape_fullness", "drape_fold")
PRESET_PROPS = SHAPE_PROPS + ("seed", "detail")


class LG_OT_reset_cave(Operator):
    bl_idname = "landscape.reset_cave"
    bl_label = "Reset"
    bl_description = "Put the cave's sizes and shape back to the starting cave (keeps Seed and Detail Level)"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.lg_cave.is_cave

    def execute(self, context):
        props = context.active_object.lg_cave
        for name in SHAPE_PROPS:
            props.property_unset(name)  # back to the property's default
        sync_cave(context.active_object)
        return {'FINISHED'}


def capture(props):
    """A cave preset: the same file and list as the landscape presets (Mike), marked kind "cave"."""
    data = {"kind": "cave"}
    for name in PRESET_PROPS:
        data[name] = getattr(props, name)
    return data


def apply(props, data):
    for name in PRESET_PROPS:
        if name in data:
            try:
                setattr(props, name, data[name])
            except (TypeError, ValueError):
                pass


class LG_OT_add_cave(Operator):
    bl_idname = "landscape.add_cave"
    bl_label = "Add Cave"
    bl_description = "Add a cave at the 3D cursor: its mouth at the cursor, running back along Y. Move and turn it so the mouth sits in a rock face"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def execute(self, context):
        ob = bpy.data.objects.new("Cave", bpy.data.meshes.new("Cave"))
        ob.location = context.scene.cursor.location
        ob.lg_cave.is_cave = True
        ob.lg_cave.rubble_rocks, ob.lg_cave.scree_rocks = rocks.family("Blocks"), rocks.family("Scree")
        ob.modifiers.new(CAVE_MODIFIER, 'NODES').node_group = features.cave_group()
        context.collection.objects.link(ob)
        for other in context.selected_objects:
            other.select_set(False)
        ob.select_set(True)
        context.view_layer.objects.active = ob
        sync_cave(ob)
        return {'FINISHED'}


def draw_section(layout, context):
    """The selected cave's controls, as a section of the main panel (a separate panel sat above the main one,
    folded shut, and Mike couldn't find it). Add Cave is in the type list, under Caves."""
    ob = context.active_object
    if ob is None or not ob.lg_cave.is_cave:  # Add Cave lives in the type list, under Caves (Mike)
        return
    header, box = layout.panel("lg_caves", default_closed=False)
    header.label(text="Cave")
    header.operator(LG_OT_reset_cave.bl_idname, text="Reset", icon='LOOP_BACK')
    if not box:
        return
    props = ob.lg_cave
    col = box.column()
    col.label(text=ob.name, icon='MESH_UVSPHERE')
    col.prop(props, "width")
    col.prop(props, "height")
    col.prop(props, "depth")
    col.prop(props, "wiggle", slider=True)
    col.prop(props, "turn", slider=True)
    col.prop(props, "narrowing", slider=True)
    col.prop(props, "drop")
    col = box.column()
    col.prop(props, "chamber")
    row = col.row()
    row.enabled = props.chamber > 0
    row.prop(props, "ceiling")
    row = col.row()
    row.enabled = props.chamber > 0
    row.prop(props, "chamber_drop")
    row = col.row()
    row.enabled = props.chamber > 0 and props.chamber_drop > 0
    row.prop(props, "ramp")
    col = box.column()
    col.prop(props, "rock")
    col.prop(props, "roughness", slider=True)
    col.prop(props, "rubble", slider=True)
    col.prop(props, "wall_shape", slider=True)
    row = col.row()
    row.enabled = props.rock == 'LIMESTONE'  # only limestone grows formations (D168, D174)
    row.prop(props, "formations", slider=True)
    row = col.row()
    row.enabled = props.rock == 'LIMESTONE'
    row.prop(props, "puddles", slider=True)
    header, sub = box.panel("lg_cave_rocks", default_closed=False)
    header.label(text="Rocks")
    if sub:
        sub.prop(props, "rubble_rocks", text="Rubble Rocks")
        sub.prop(props, "scree_rocks", text="Scree Rocks")
        sub.prop(props, "rock_size")
        sub.prop(props, "stretch", slider=True)
        sub.prop(props, "tilt", slider=True)
        sub.prop(props, "spread", slider=True)
    header, sub = box.panel("lg_cave_formations", default_closed=False)
    header.label(text="Formations")
    if sub:
        sub.enabled = props.rock == 'LIMESTONE'
        for prop in FORMATION_KITS.values():
            sub.prop(props, prop)
        sub.prop(props, "formation_size")
        sub.prop(props, "formation_stretch", slider=True)
        sub.prop(props, "clusters", slider=True)
        sub.separator()
        sub.prop(props, "drape_lines")
        row = sub.row()
        row.enabled = props.drape_lines is not None
        row.prop(props, "drape_length", slider=True)
        row = sub.row()
        row.enabled = props.drape_lines is not None
        row.prop(props, "drape_fullness", slider=True)
        row = sub.row()
        row.enabled = props.drape_lines is not None
        row.prop(props, "drape_fold", slider=True)
    row = col.row(align=True)  # as on the landscapes
    row.prop(props, "seed")
    row.operator(LG_OT_randomize_cave.bl_idname, text="Randomize", icon='FILE_REFRESH')
    header, sub = box.panel("lg_cave_masks", default_closed=True)
    header.label(text="Masks")
    if sub:
        sub.prop(props, "show_mask", text="Show")
        if props.show_mask != 'NONE':
            sub.row(align=True).prop(props, "mask_colors", expand=True)
            sub.label(text=dict((k, d) for k, _n, d in MASK_ITEMS)[props.show_mask])
    header, sub = box.panel("lg_cave_detail", default_closed=False)
    header.label(text="Detail Level")
    if sub:
        sub.row(align=True).prop(props, "detail", expand=True)
        sub.label(text=f"Shell about {features.CAVE_FACES[DETAIL_INDEX[props.detail]] / 1e6:g}M faces or more for a big cave")


classes = (LG_CaveProps, LG_OT_add_cave, LG_OT_randomize_cave, LG_OT_reset_cave)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Object.lg_cave = PointerProperty(type=LG_CaveProps)


def unregister():
    del bpy.types.Object.lg_cave
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

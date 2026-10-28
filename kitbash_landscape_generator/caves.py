# SPDX-License-Identifier: GPL-3.0-or-later
"""The cave object (M5 step 5.2, D93): a standalone cave you place in the scene like the butte, sized in real
meters, then carve into a landscape or use as a Boolean cutter on any mesh."""

import bpy
from bpy.props import BoolProperty, FloatProperty, IntProperty, PointerProperty
from bpy.types import Operator, PropertyGroup

from . import features, nodes

CAVE_MODIFIER = "KB Cave"


def cave_modifier(ob):
    if ob is None or not ob.lg_cave.is_cave:
        return None
    return next((m for m in ob.modifiers if m.type == 'NODES' and m.node_group
                 and m.node_group.name.startswith(features.CAVE_GROUP)), None)


# prop -> group input
CAVE_SOCKETS = {"width": "Entrance Width", "height": "Entrance Height", "depth": "Depth", "wiggle": "Wiggle",
                "turn": "Turn", "drop": "Drop", "narrowing": "Narrowing", "chamber": "Chamber Size",
                "ceiling": "Ceiling Height", "chamber_drop": "Chamber Drop",
                "roughness": "Roughness", "seed": "Seed", "fine": "Fine"}


def sync_cave(ob):
    mod = cave_modifier(ob)
    if mod is None:
        return
    for prop, sock in CAVE_SOCKETS.items():
        nodes.input_socket(mod, sock).value = getattr(ob.lg_cave, prop)
    ob.update_tag()


def _sync(props, _context):
    sync_cave(props.id_data)


class LG_CaveProps(PropertyGroup):
    is_cave: BoolProperty(default=False)
    width: FloatProperty(name="Entrance Width", description="How wide the cave mouth is, in real size",
                         default=12.0, min=0.5, soft_max=200.0, unit='LENGTH', update=_sync)
    height: FloatProperty(name="Entrance Height", description="How tall the cave mouth is, floor to roof, in real size",
                          default=6.0, min=0.5, soft_max=100.0, unit='LENGTH', update=_sync)
    depth: FloatProperty(name="Depth", description="How far the cave runs back from the mouth",
                         default=30.0, min=1.0, soft_max=500.0, unit='LENGTH', update=_sync)
    wiggle: FloatProperty(name="Wiggle", description="A straight passage, or one that winds from side to side",
                          default=0.3, min=0.0, max=1.0, subtype='FACTOR', update=_sync)
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
    roughness: FloatProperty(name="Roughness", description="Smooth, water-worn walls, or rough broken rock",
                             default=0.5, min=0.0, max=1.0, subtype='FACTOR', update=_sync)
    seed: IntProperty(name="Seed", description="Same seed, same cave. Change it for a new winding and rock",
                      default=0, min=0, max=99999, update=_sync)
    fine: BoolProperty(name="High Detail", description="Finer rock on the walls. Slower to update",
                       default=False, update=_sync)


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
    col = box.column()
    col.prop(props, "roughness", slider=True)
    col.prop(props, "seed")
    col.prop(props, "fine")


classes = (LG_CaveProps, LG_OT_add_cave)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Object.lg_cave = PointerProperty(type=LG_CaveProps)


def unregister():
    del bpy.types.Object.lg_cave
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

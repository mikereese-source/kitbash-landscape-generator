"""Render review images headless (no UI timeouts, never touches an open scene).

Run:  blender -b --factory-startup --python tests/render_sheet.py -- <out_dir> <shots.json>
shots.json: [{"file": "a.png", "type": "craters", "set": {"crater_age": 1.0}, "cam": 0.8,
              "color": [0.6, 0.6, 0.58], "size": 360, "nodes": {"Rock": 0}}, ...]
Landscape is 200 m at Final; "cam" scales the camera distance.
"""

import json
import os
import sys

import bpy
import mathutils

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kitbash_landscape_generator as lg  # noqa: E402

out_dir, shots_path = sys.argv[sys.argv.index("--") + 1:][:2]
shots = json.load(open(shots_path, encoding="utf-8"))
lg.register()
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob)
sc = bpy.context.scene
cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
sc.collection.objects.link(cam)
sc.camera = cam
cam.data.lens = 40
cam.data.clip_end = 100000
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading
sh.light, sh.color_type, sh.show_cavity = 'STUDIO', 'SINGLE', False

for shot in shots:
    for ob in [o for o in sc.objects if o.type == 'MESH']:
        bpy.data.objects.remove(ob)
    sc.lg_type = shot["type"]
    bpy.ops.landscape.add()
    ob = bpy.context.view_layer.objects.active
    ob.lg.detail = shot.get("detail", "FINAL")
    for k, v in shot.get("set", {}).items():
        setattr(ob.lg, k, v)
    for k, v in shot.get("nodes", {}).items():  # raw node inputs, e.g. {"Rock": 0} for a before/after
        lg.nodes.input_socket(lg.landscape_modifier(ob), k).value = v
    ob.update_tag()
    s = shot.get("cam", 1.0)
    loc = mathutils.Vector((0.95, -0.95, 0.62)) * 200 * s
    cam.location = loc
    cam.rotation_euler = (mathutils.Vector((0, 0, 8 * s)) - loc).to_track_quat('-Z', 'Y').to_euler()
    sh.single_color = shot.get("color", (0.6, 0.6, 0.6))
    sc.render.resolution_x = sc.render.resolution_y = shot.get("size", 360)
    sc.render.filepath = os.path.join(out_dir, shot["file"])
    bpy.ops.render.render(write_still=True)
    print("RENDERED", shot["file"])

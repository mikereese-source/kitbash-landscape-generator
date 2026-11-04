"""One headless shot of the cave object (one render per process). Args: out.png view [chamber]"""
import sys, math, os
import bpy
sys.path.insert(0, r"E:\Projects\Cowork\apps\landscape-generator")
import kitbash_landscape_generator as lg
args = sys.argv[sys.argv.index("--") + 1:]
OUT, VIEW = args[0], args[1]
lg.register()
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o)
sc = bpy.context.scene
bpy.ops.landscape.add_cave()
ob = bpy.context.view_layer.objects.active
c = ob.lg_cave
c.detail = os.environ.get('LG_DETAIL', 'PREVIEW' if '--preview' in sys.argv else 'HIGH')
if len(args) > 2 and args[2] == 'shot5':
    for k, v in dict(width=39, height=21, depth=168, wiggle=0.29, turn=-0.06, narrowing=0.0, drop=0.23, chamber=178, ceiling=62, chamber_drop=31, ramp=True, roughness=0.96, rubble=0.2, seed=1322).items():
        setattr(c, k, v)
elif len(args) > 2 and args[2] == 'mike2':
    c.width, c.height, c.depth, c.wiggle, c.narrowing, c.drop = 39.0, 21.0, 138.0, -0.43, 0.33, 0.0
    c.chamber, c.ceiling, c.chamber_drop, c.roughness, c.seed = 93.0, 62.0, 16.0, 0.64, 14510
    c.ramp = '--ramp' in sys.argv
elif len(args) > 2 and args[2] == 'mike':
    c.width, c.height, c.depth, c.wiggle, c.narrowing, c.drop = 36.0, 21.0, 138.0, 1.0, 0.21, 45.0
    c.chamber, c.ceiling, c.chamber_drop, c.roughness = 65.0, 37.0, 27.0, 0.64
elif len(args) > 2:
    c.chamber, c.ceiling, c.depth, c.wiggle, c.chamber_drop = 30.0, 16.0, 50.0, 0.6, 8.0
import os
c.rock = os.environ.get('LG_ROCK', 'LIMESTONE')
if len(args) > 2 and args[2] == 'mike3':
    c.ramp = os.environ.get('LG_RAMP') == '1'
    [setattr(c, k, v) for k, v in dict(width=float(os.environ.get('LG_W',46.32)), height=28.94, depth=168.42, wiggle=0.2928, turn=-0.064, drop=0.23, narrowing=0.0, chamber=float(os.environ.get('LG_CH', 177.88)), ceiling=62.18, chamber_drop=31.28, rubble=float(os.environ.get('LG_RUB',0.5)), wall_shape=float(os.environ.get('LG_WS',1.0)), roughness=0.9588, seed=22635).items()]
if 'LG_ROUGH' in os.environ: c.roughness = float(os.environ['LG_ROUGH'])
c.separate = os.environ.get('LG_SEP', '1') == '1'
if os.environ.get('LG_MASK'): c.show_mask = os.environ['LG_MASK']; c.mask_colors = os.environ.get('LG_COLS', 'GRAY'); ob.data.color_attributes.active_color_name = 'lg_view'
if 'LG_WS' in os.environ: c.wall_shape = float(os.environ['LG_WS'])
lg.caves.sync_cave(ob)
if os.environ.get('LG_FINFO'):
    import collections
    dg = bpy.context.evaluated_depsgraph_get(); dg.update(); cnt = collections.Counter(); big = {}
    for inst in dg.object_instances:
        if inst.is_instance and inst.parent and inst.parent.name == ob.name:
            n = inst.object.name
            if "Formation" in n:
                fam = n.split()[2]; cnt[fam] += 1
                sc_ = inst.matrix_world.to_scale().z; loc = inst.matrix_world.translation
                if sc_ > big.get(fam, (0,))[0]: big[fam] = (sc_, tuple(round(v, 1) for v in loc), n)
    print("FINFO", dict(cnt)); [print("FBIG", k, v) for k, v in big.items()]
    from mathutils.bvhtree import BVHTree
    from mathutils import Vector
    eo = ob.evaluated_get(dg); me = eo.to_mesh(); bvh = BVHTree.FromPolygons([v.co.copy() for v in me.vertices], [tuple(p.vertices) for p in me.polygons])
    import collections as _c; gaps = _c.defaultdict(list)
    for inst in dg.object_instances:
        if inst.is_instance and inst.parent and inst.parent.name == ob.name and "Formation" in inst.object.name:
            fam = " ".join(inst.object.name.split()[2:-2 if inst.object.name.split()[-1] in ("Preview", "Ultra") else -1]); loc = inst.matrix_world.translation
            d = Vector((0, 0, 1)) if fam.startswith(("Stalactite", "Lava")) else Vector((0, 0, -1))
            hit = bvh.ray_cast(loc - d * 3.0, d, 50.0)
            gaps[fam].append(round(hit[3] - 3.0, 2) if hit[0] else None)
    for k, g in gaps.items():
        ok = [x for x in g if x is not None]; print("FGAP", k, "n", len(g), "miss", len(g) - len(ok), "over0.1", sum(1 for x in ok if abs(x) > 0.1), "worst", sorted(ok, key=abs)[-5:] if ok else None)
    sys.exit(0)
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 30
cam.data.clip_end = 5000.0
if VIEW == "eye":   # LG_EYE / LG_LOOK, x,y,z each; LG_LENS
    cam.location = tuple(float(v) for v in os.environ["LG_EYE"].split(",")); look = tuple(float(v) for v in os.environ["LG_LOOK"].split(",")); cam.data.lens = float(os.environ.get("LG_LENS", 35))
elif VIEW == "chback":
    cam.location = (-10.0, 245.0, -22.0); look = (-10.0, 120.0, -12.0); cam.data.lens = 16
elif VIEW == "rim":   # inside the chamber, high up, looking down at the far rim (roof clipped)
    cam.location = (-20.0, 150.0, 40.0); look = (60.0, 250.0, -31.0); cam.data.lens = 24; cam.data.clip_start = 45.0
elif VIEW == "wallu":   # close on the passage wall, for fine pattern
    cam.location = (5.0, 60.0, 8.0); look = (-30.0, 75.0, 12.0); cam.data.lens = 35
elif VIEW == "chwall":   # on the chamber floor, looking up at its wall and roof
    cam.location = (0.0, 230.0, -25.0); look = (-60.0, 262.0, 12.0); cam.data.lens = 24
elif VIEW == "inpass":
    cam.location = (8.0, 0.0, 6.0); look = (0.0, 90.0, 6.0); cam.data.lens = 18
elif VIEW == "outside":
    cam.location = (-260.0, -120.0, 220.0); look = (0.0, 110.0, 0.0); cam.data.lens = 30
elif VIEW == "hall":
    cam.location = (-10.0, 175.0, -24.0); look = (-10.0, 260.0, -10.0); cam.data.lens = 16
elif VIEW == "rampv":
    cam.location = (2.6, 213.0, 5.7); look = (-16.4, 129.4, -15.7); cam.data.lens = 30
elif VIEW == "at":   # facing the wall at a point inside it (LG_AT), from 14 m out in the passage
    from mathutils import Vector
    tx, ty, tz = (float(v) for v in os.environ["LG_AT"].split(","))
    dg = bpy.context.evaluated_depsgraph_get(); dg.update()
    tgt = Vector((tx, ty, tz - 8.0))
    d = Vector((-tx, 0.0, 0.0)).normalized()
    hit, loc, nor, i_, o_, m_ = sc.ray_cast(dg, tgt, d)
    print("WALL", hit, loc)
    cam.location = loc + d * 16.0 + Vector((0.0, -4.0, -4.0)); look = loc
    cam.data.lens = 16
elif VIEW == "drop2":
    cam.location = (10.0, 88.0, 2.0); look = (55.0, 112.0, 16.0); cam.data.lens = 22
elif VIEW == "drop3":
    cam.location = (-10.0, 60.0, 2.0); look = (-55.0, 42.0, 16.0); cam.data.lens = 22
elif VIEW == "drop":
    cam.location = (-30.0, 150.0, -12.0); look = (-100.0, 140.0, 18.0); cam.data.lens = 22
elif VIEW == "wall":
    cam.location = (8.0, 60.0, 0.0); look = (-30.0, 95.0, -2.0); cam.data.lens = 24
elif VIEW == "far":
    cam.location = (0.0, 200.0, -20.0); look = (32.0, 232.0, -26.0); cam.data.lens = 30
elif VIEW == "view2":
    cam.location = (28.0, 144.0, -10.0); look = (-45.4, 185.7, -7.0); cam.data.lens = 50
elif VIEW == "close":
    cam.location = (-1.0, 78.0, -6.0); look = (-10.2, 68.8, -7.5); cam.data.lens = 40
elif VIEW == "mikeview":
    cam.location = (13.0, 104.0, -10.6); look = (-13.5, 62.9, -11.3); cam.data.lens = 35
elif VIEW == "join":   # in the passage before the chamber, looking down the ramp
    import numpy as np
    dg = bpy.context.evaluated_depsgraph_get(); dg.update()
    co = np.array([v.co[:] for v in ob.evaluated_get(dg).data.vertices])
    def mid_x(y):
        band = co[np.abs(co[:, 1] - y) < 3.0]
        return float((band[:, 0].min() + band[:, 0].max()) / 2) if len(band) else 0.0
    y_s = c.depth * 0.25
    cam.location = (mid_x(y_s), y_s, c.height * 0.7); look = (mid_x(c.depth * 0.6), c.depth * 0.6, -c.chamber_drop * 0.5)
    cam.data.lens = 22
elif VIEW == "side":   # outside, level with the chamber, looking at where the ramp comes in
    cam.location = (-170.0, c.depth * 0.75, -c.chamber_drop + 10.0); look = (0.0, c.depth * 0.8, -c.chamber_drop)
    cam.data.lens = 30
elif VIEW == "under":   # outside, below the chamber, looking up at where the passage meets it
    cam.location = (-120.0, c.depth * 0.55, -c.chamber_drop - 70.0); look = (0.0, c.depth * 0.95, -c.chamber_drop)
    cam.data.lens = 24
elif VIEW == "down":   # cutaway from above: the floor of the chamber, roof hidden by a clip
    cam.location = (-40.0, c.depth * 0.55, 45.0); look = (0.0, c.depth * 0.85, -c.chamber_drop)
    cam.data.lens = 18; cam.data.clip_start = 60.0 - (c.ceiling - c.chamber_drop) * 0.6
elif VIEW == "chamber":   # in the passage, looking down into the chamber
    import numpy as np
    dg = bpy.context.evaluated_depsgraph_get(); dg.update()
    co = np.array([v.co[:] for v in ob.evaluated_get(dg).data.vertices])
    def mid_x(y):
        band = co[np.abs(co[:, 1] - y) < 3.0]
        return float((band[:, 0].min() + band[:, 0].max()) / 2) if len(band) else 0.0
    yc, yl = c.depth + c.chamber * 0.15, c.depth * 0.55
    cam.location = (mid_x(yc), yc, -c.chamber_drop + c.ceiling * 0.35); look = (mid_x(yl), yl, -c.chamber_drop * 0.4)
elif VIEW == "passage":   # standing mid-passage on the floor's centre line, looking on down it
    import numpy as np
    dg = bpy.context.evaluated_depsgraph_get(); dg.update()
    co = np.array([v.co[:] for v in ob.evaluated_get(dg).data.vertices])
    def mid_x(y):
        band = co[np.abs(co[:, 1] - y) < 2.0]
        return float((band[:, 0].min() + band[:, 0].max()) / 2) if len(band) else 0.0
    y0_, y1_ = c.depth * 0.3, c.depth * 0.55
    cam.location = (mid_x(y0_), y0_, c.height * 0.3); look = (mid_x(y1_), y1_, c.height * 0.35)
    cam.data.lens = 18
elif VIEW == "tube":   # like the reference photos: mid-passage, low, looking straight down the tube
    import numpy as np
    dg = bpy.context.evaluated_depsgraph_get(); dg.update()
    co = np.array([v.co[:] for v in ob.evaluated_get(dg).data.vertices])
    def mid_x(y):
        band = co[np.abs(co[:, 1] - y) < 2.0]
        return float((band[:, 0].min() + band[:, 0].max()) / 2) if len(band) else 0.0
    y0_, y1_ = float(os.environ.get('LG_TY0', c.depth * 0.08)), float(os.environ.get('LG_TY1', c.depth * 0.3))
    cam.location = (mid_x(y0_), y0_, c.height * 0.25); look = (mid_x(y1_), y1_, c.height * 0.3)
    cam.data.lens = 16
elif VIEW == "mj":   # Mike's viewport 2026-11-01: in the chamber, looking back at where the passage comes in
    cam.location = (-58.1, 242.7, -28.2); look = (-58.1 + 0.8 * 50, 242.7 - 0.59 * 50, -28.2 + 0.02 * 50); cam.data.lens = 22
elif VIEW == "mo":   # Mike's viewport 2026-11-01: below the cave, looking up at its underside
    cam.location = (75.4, 75.0, -230.4); look = (-47.8, 147.2, -2.0); cam.data.lens = 40
elif VIEW == "mp":   # Mike's viewport 2026-11-02: passage wall pinches
    cam.location = (-9.1, 61.9, 15.4); look = (21.9, 68.7, 2.0); cam.data.lens = 50
elif VIEW == "roofv":   # mid-passage, low, looking up at the roof ahead
    import numpy as np
    dg = bpy.context.evaluated_depsgraph_get(); dg.update()
    co = np.array([v.co[:] for v in ob.evaluated_get(dg).data.vertices])
    band = co[np.abs(co[:, 1] - c.depth * 0.2) < 2.0]
    mx = float((band[:, 0].min() + band[:, 0].max()) / 2)
    cam.location = (mx, c.depth * 0.2, c.height * 0.15); look = (mx, c.depth * 0.32, c.height * 1.2); cam.data.lens = 18
elif VIEW == "inside":   # standing in the passage, looking back
    cam.location = (c.width * 0.15, 2.0, 1.7); look = (-c.width * 0.3, 30.0, 0.5)
elif VIEW == "front":   # looking into the mouth
    cam.location = (9.0, -22.0, 7.0); look = (0.0, 4.0, 3.0)
else:                 # three-quarter from above, to see the whole sausage
    k = c.width / 12.0
    cam.location = (-38.0 * k, -18.0 * k, 34.0 * k + 30.0); look = (0.0, c.depth * 0.5, -c.drop * 0.5)
if look is not None:
    dx, dy, dz = (look[i] - cam.location[i] for i in range(3))
    cam.rotation_euler = (math.atan2(math.hypot(dx, dy), -dz), 0, math.atan2(dy, dx) - math.pi / 2)
if os.environ.get('LG_NEAR'):
    import numpy as np
    dg = bpy.context.evaluated_depsgraph_get(); dg.update()
    me = ob.evaluated_get(dg).to_mesh()
    co = np.zeros(len(me.vertices)*3); me.vertices.foreach_get('co', co); co = co.reshape(-1,3)
    def A(n):
        a = np.zeros(len(me.vertices)*3); me.attributes[n].data.foreach_get('vector', a); return a.reshape(-1,3)
    tb, tr = A('lg_tube'), A('lg_tube_r')
    for pt in os.environ['LG_NEAR'].split(';'):
        p = np.array([float(v) for v in pt.split(',')]); i = int(np.argmin(((co-p)**2).sum(1)))
        print("N", pt, "tube", np.round(tb[i],1), "r,tall,ch", np.round(tr[i],2))
    raise SystemExit
if os.environ.get('LG_HN'):
    import numpy as np
    dg = bpy.context.evaluated_depsgraph_get(); dg.update()
    me = ob.evaluated_get(dg).to_mesh()
    co = np.zeros(len(me.vertices)*3); me.vertices.foreach_get('co', co); co = co.reshape(-1,3)
    def A(n):
        a = np.zeros(len(me.vertices)*3); me.attributes[n].data.foreach_get('vector', a); return a.reshape(-1,3)
    tb, tr = A('lg_tube'), A('lg_tube_r')
    sel = np.where(np.abs(co[:,1]-60) < 0.5)[0]
    sel = sel[np.argsort(co[sel,2])]
    for i in sel[::max(1,len(sel)//40)]:
        print("H", np.round(co[i],1), "up", round(tb[i,2],1), "tall", round(tr[i,1],1), "hn", round(tb[i,2]/tr[i,1],2), "side", round(tb[i,1],1), "r", round(tr[i,0],1))
    raise SystemExit
if os.environ.get('LG_ROW'):
    import numpy as np
    dg = bpy.context.evaluated_depsgraph_get(); dg.update()
    me = ob.evaluated_get(dg).to_mesh()
    co = np.zeros(len(me.vertices)*3); me.vertices.foreach_get('co', co); co = co.reshape(-1,3)
    tb = np.zeros(len(me.vertices)*3); me.attributes['lg_tube'].data.foreach_get('vector', tb); tb = tb.reshape(-1,3)
    y0 = float(os.environ['LG_ROW'])
    sel = np.where((np.abs(co[:,1]-y0) < 0.25) & (co[:,2] > 5))[0]
    ang = np.arctan2(co[sel,2]-0, co[sel,0]+10)
    sel = sel[np.argsort(ang)]
    prev = None
    for i in sel[::3][:80]:
        print("R", np.round(co[i],2), np.round(tb[i],3))
    raise SystemExit
if os.environ.get('LG_GRAD'):
    import numpy as np
    dg = bpy.context.evaluated_depsgraph_get(); dg.update()
    me = ob.evaluated_get(dg).to_mesh()
    co = np.zeros(len(me.vertices)*3); me.vertices.foreach_get('co', co); co = co.reshape(-1,3)
    tb = np.zeros(len(me.vertices)*3); me.attributes['lg_tube'].data.foreach_get('vector', tb); tb = tb.reshape(-1,3)
    ev = np.zeros(len(me.edges)*2, np.int32); me.edges.foreach_get('vertices', ev); ev = ev.reshape(-1,2)
    dl = np.linalg.norm(co[ev[:,0]]-co[ev[:,1]], axis=1) + 1e-9
    for k, nm in enumerate(('along','side','up')):
        g = np.abs(tb[ev[:,0],k]-tb[ev[:,1],k]) / dl
        print("G", nm, np.round(np.percentile(g,[50,90,99,99.9]),2))
    # second difference along edges chains: kinks -> compare gradient of each edge to mean of neighbours via vertex average
    raise SystemExit
if os.environ.get('LG_PROBE'):
    import numpy as np
    dg = bpy.context.evaluated_depsgraph_get(); dg.update()
    me = ob.evaluated_get(dg).to_mesh()
    co = np.zeros(len(me.vertices)*3); me.vertices.foreach_get('co', co); co = co.reshape(-1,3)
    tb = np.zeros(len(me.vertices)*3); me.attributes['lg_tube'].data.foreach_get('vector', tb); tb = tb.reshape(-1,3)
    px, pz = (float(v) for v in os.environ['LG_PROBE'].split(','))
    sel = np.where((np.abs(co[:,0]-px) < 6) & (np.abs(co[:,2]-pz) < 1.0))[0]
    sel = sel[np.argsort(co[sel,1])]
    for i in sel[::max(1,len(sel)//60)]:
        print("P", np.round(co[i],1), np.round(tb[i],2))
    raise SystemExit
if os.environ.get('LG_UVSTATS'):
    import numpy as np, time
    if os.environ.get('LG_UVM'):
        for g in bpy.data.node_groups:
            for nd in g.nodes:
                if nd.bl_idname == 'GeometryNodeUVUnwrap': nd.inputs['Method'].default_value = os.environ['LG_UVM']; print("SETM", g.name)
        ob.update_tag()
    t0 = time.time(); dg = bpy.context.evaluated_depsgraph_get(); dg.update()
    me = ob.evaluated_get(dg).to_mesh(); me.calc_loop_triangles()
    print("EVAL", round(time.time() - t0, 1), "s faces", len(me.polygons))
    uvl = me.uv_layers['UVMap'].data
    nt = len(me.loop_triangles)
    li = np.zeros(nt * 3, np.int32); me.loop_triangles.foreach_get('loops', li); li = li.reshape(-1, 3)
    vi = np.zeros(nt * 3, np.int32); me.loop_triangles.foreach_get('vertices', vi); vi = vi.reshape(-1, 3)
    co = np.zeros(len(me.vertices) * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    uv = np.zeros(len(me.loops) * 2); uvl.foreach_get('uv', uv); uv = uv.reshape(-1, 2)
    P = co[vi]; U = uv[li]
    e1, e2 = P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]
    a3 = np.linalg.norm(np.cross(e1, e2), axis=1) / 2
    f1, f2 = U[:, 1] - U[:, 0], U[:, 2] - U[:, 0]
    a2 = np.abs(f1[:, 0] * f2[:, 1] - f1[:, 1] * f2[:, 0]) / 2
    ok = a3 > 1e-9
    k = a2[ok].sum() / a3[ok].sum()
    r = (a2[ok] / a3[ok]) / k
    # anisotropy: singular values of the 3D->UV map per triangle
    n = np.cross(e1, e2); n /= np.linalg.norm(n, axis=1)[:, None] + 1e-12
    ax = e1 / (np.linalg.norm(e1, axis=1)[:, None] + 1e-12); ay = np.cross(n, ax)
    X = np.stack([np.einsum('ij,ij->i', e1, ax), np.einsum('ij,ij->i', e1, ay)], 1)
    Y = np.stack([np.einsum('ij,ij->i', e2, ax), np.einsum('ij,ij->i', e2, ay)], 1)
    Pm = np.stack([X, Y], 2); Um = np.stack([f1, f2], 2)
    good = ok & (np.abs(np.linalg.det(Pm)) > 1e-12)
    J = Um[good] @ np.linalg.inv(Pm[good])
    sv = np.linalg.svd(J, compute_uv=False); aniso = sv[:, 0] / np.maximum(sv[:, 1], 1e-12)
    w = a3[good] / a3[good].sum()
    print("UVFILL", round(a2.sum(), 3), "SCALE r p5/p50/p95", np.round(np.percentile(r, [5, 50, 95]), 2),
          "area-weighted share 0.5<r<2", round(float(((r > 0.5) & (r < 2)) @ (a3[ok] / a3[ok].sum())), 3),
          "ANISO p50/p95", np.round(np.percentile(aniso, [50, 95]), 2), "share<1.5", round(float((aniso < 1.5) @ w), 3))
    part = me.attributes.get('lg_uv_part')
    if part:
        pv = np.zeros(len(me.polygons)); part.data.foreach_get('value', pv)
        print("PARTS", {int(v): int((pv == v).sum()) for v in np.unique(pv)})
    # islands: faces joined across edges whose two corners share UVs
    lv = np.zeros(len(me.loops), np.int32); me.loops.foreach_get('vertex_index', lv)
    key = {}
    parent = list(range(len(me.polygons)))
    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]; a = parent[a]
        return a
    for p in me.polygons:
        ls = list(p.loop_indices)
        for j in range(len(ls)):
            a_, b_ = ls[j], ls[(j + 1) % len(ls)]
            va, vb = lv[a_], lv[b_]
            kk = (min(va, vb), max(va, vb))
            ua = tuple(np.round(uv[a_], 5)); ub = tuple(np.round(uv[b_], 5))
            sig = (ua, ub) if va < vb else (ub, ua)
            if kk in key:
                q, sg = key[kk]
                if sg == sig:
                    ra, rb = find(q), find(p.index)
                    if ra != rb: parent[ra] = rb
            else:
                key[kk] = (p.index, sig)
    roots = [find(i) for i in range(len(me.polygons))]
    from collections import Counter
    cnt = Counter(roots)
    sizes = sorted(cnt.values(), reverse=True)
    print("ISLANDS", len(sizes), "largest", sizes[:10], "under 50 faces", sum(1 for s_ in sizes if s_ < 50))
    raise SystemExit
if os.environ.get('LG_PICK'):
    from mathutils import Vector
    dg = bpy.context.evaluated_depsgraph_get(); dg.update()
    cam.data.sensor_fit = 'HORIZONTAL'
    fr = [cam.matrix_world @ v for v in cam.data.view_frame(scene=sc)]
    for pxy in os.environ['LG_PICK'].split(';'):
        px, py = (float(v) for v in pxy.split(','))
        u, w = px / 960.0, 1.0 - py / 600.0
        # frame: 0 top-right, 1 bottom-right, 2 bottom-left, 3 top-left
        top = fr[3].lerp(fr[0], u); bot = fr[2].lerp(fr[1], u); pt = bot.lerp(top, w)
        d = (pt - cam.location).normalized()
        hit, loc, nor, idx, o, m = sc.ray_cast(dg, cam.location, d)
        me = ob.evaluated_get(dg).data
        piece = None
        if hit and o.original == ob:
            a = me.attributes.get('lg_piece')
            if a: piece = bool(a.data[me.polygons[idx].vertices[0]].value)
        print("PICK", pxy, hit, tuple(round(x, 1) for x in loc), "normal", tuple(round(x, 2) for x in nor), "obj", o.name if o else None, "piece", piece)
    raise SystemExit
sc.render.engine = 'BLENDER_WORKBENCH'
if os.environ.get('LG_MATCOL'): sc.display.shading.color_type = 'MATERIAL'  # water shows in its own colour
if os.environ.get('LG_UV'):
    img = bpy.data.images.new("grid", 2048, 2048); img.generated_type = 'COLOR_GRID'
    mat = bpy.data.materials.new("uvgrid"); mat.use_nodes = True
    tex = mat.node_tree.nodes.new('ShaderNodeTexImage'); tex.image = img
    mat.node_tree.links.new(tex.outputs[0], mat.node_tree.nodes["Principled BSDF"].inputs[0])
    tex.interpolation = 'Closest'
    bpy.context.view_layer.objects.active = ob; ob.select_set(True)
    bpy.ops.object.convert(target='MESH')
    ob = bpy.context.view_layer.objects.active
    ob.data.materials.clear(); ob.data.materials.append(mat)
    for p in ob.data.polygons: p.material_index = 0
    ob.data.uv_layers.active = ob.data.uv_layers['UVMap']
    me = ob.evaluated_get(bpy.context.evaluated_depsgraph_get()).data
    mat.node_tree.nodes.active = tex
    import numpy as np
    uvs = np.array([d.vector[:] for d in me.attributes['UVMap'].data])
    print("UVS", [u.name for u in me.uv_layers], uvs.min(0), uvs.max(0), np.isnan(uvs).sum())
sc.display.shading.light = 'STUDIO'
sc.display.shading.color_type = 'VERTEX' if os.environ.get('LG_MASK') else ('TEXTURE' if os.environ.get('LG_UV') else 'SINGLE')
sc.display.shading.show_cavity = True
sc.render.resolution_x, sc.render.resolution_y = 960, 600
sc.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print("WROTE", OUT)

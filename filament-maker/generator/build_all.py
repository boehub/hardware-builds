"""Build STL set, FBX assembly and renders.   Run with the bpy python:  python build_all.py [stl] [fbx] [render:<view>,...]"""
import sys, os, json, math, zipfile, re
import numpy as np, trimesh
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fm_model
from fm_params import P

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
os.makedirs(OUT + "/stl", exist_ok=True); os.makedirs(OUT + "/img", exist_ok=True)

MAT = {  # rgb, metallic, roughness
    "print": ((0.93, 0.42, 0.10), 0.0, 0.55),
    "tpu": ((0.12, 0.45, 0.22), 0.0, 0.7),
    "alu": ((0.78, 0.80, 0.83), 0.9, 0.38),
    "steel": ((0.62, 0.64, 0.68), 0.95, 0.30),
    "black": ((0.05, 0.05, 0.06), 0.2, 0.45),
    "brass": ((0.80, 0.58, 0.20), 0.9, 0.30),
    "heater": ((0.20, 0.16, 0.14), 0.6, 0.45),
    "copper": ((0.75, 0.38, 0.22), 0.9, 0.3),
    "red": ((0.75, 0.04, 0.05), 0.0, 0.4),
    "spool": ((0.20, 0.30, 0.70), 0.0, 0.5),
    "filament": ((0.95, 0.95, 0.30), 0.0, 0.4),
    "sponge": ((0.90, 0.80, 0.30), 0.0, 0.9),
}

_mats = {}

def slug(s):
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")

# ------------------------------------------------------------------ STL
def export_stl(parts):
    paths = []
    for q in parts:
        if q.kind != "printed" or (len(q.pid) == 4 and q.pid.endswith("b")):
            continue
        m = q.mesh.copy()
        if q.print_rot is not None:
            m.apply_transform(q.print_rot)
        b = m.bounds
        m.apply_translation((-b[0][0], -b[1][0] if False else -b[0][1], -b[0][2]))
        base = q.pid[:-1] if (len(q.pid) == 4 and q.pid.endswith("a")) else q.pid
        name = f"{base}_{slug(q.name)}"
        path = f"{OUT}/stl/{name}.stl"
        m.export(path)
        paths.append((path, name, m.extents.round(1).tolist(), m.is_watertight))
    return paths

# ------------------------------------------------------------------ Blender scene
def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    _mats.clear()
    sc = bpy.context.scene
    sc.unit_settings.system = "METRIC"; sc.unit_settings.scale_length = 1.0; sc.unit_settings.length_unit = "MILLIMETERS"
    return sc

def get_mat(key):
    if key in _mats and _mats[key].name in bpy.data.materials:
        return _mats[key]
    col, met, rough = MAT[key]
    m = bpy.data.materials.new("M_" + key)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Metallic"].default_value = met
    b.inputs["Roughness"].default_value = rough
    _mats[key] = m
    return m

def add_obj(part, offset=(0, 0, 0), collection=None):
    mesh = part.mesh
    try:
        sm = trimesh.graph.smooth_shade(mesh, angle=math.radians(32))
        verts, faces, normals = np.asarray(sm.vertices), np.asarray(sm.faces), np.asarray(sm.vertex_normals)
    except Exception:
        verts, faces, normals = np.asarray(mesh.vertices), np.asarray(mesh.faces), None
    me = bpy.data.meshes.new(f"{part.pid}_mesh")
    me.from_pydata((verts * 0.001).tolist(), [], faces.tolist())
    me.update()
    if normals is not None:
        try:
            me.normals_split_custom_set_from_vertices(normals.tolist())
        except Exception:
            for p_ in me.polygons: p_.use_smooth = True
    ob = bpy.data.objects.new(f"{part.pid}_{slug(part.name)}", me)
    ob.location = (offset[0] * 0.001, offset[1] * 0.001, offset[2] * 0.001)
    (collection or bpy.context.scene.collection).objects.link(ob)
    ob.data.materials.append(get_mat(part.color))
    ob["pid"] = part.pid; ob["kind"] = part.kind; ob["group"] = part.group
    return ob

def setup_world_lights(sc, zfloor):
    w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
    bg = w.node_tree.nodes["Background"]; bg.inputs[0].default_value = (0.92, 0.94, 0.97, 1); bg.inputs[1].default_value = 0.8
    for name, loc, rot, en, size in (("key", (2, -2.5, 3), (0.9, 0.25, 0.6), 1.6, 6), ("fill", (-3, 1, 2), (1.2, 0, -1.4), 0.35, 10)):
        l = bpy.data.lights.new(name, "SUN"); l.energy = en; l.angle = math.radians(size)
        o = bpy.data.objects.new(name, l); o.rotation_euler = rot; sc.collection.objects.link(o)
    # floor
    me = bpy.data.meshes.new("floor")
    s = 6.0
    me.from_pydata([(-s, -s, zfloor), (s, -s, zfloor), (s, s, zfloor), (-s, s, zfloor)], [], [(0, 1, 2, 3)])
    fo = bpy.data.objects.new("floor", me); sc.collection.objects.link(fo)
    m = bpy.data.materials.new("floor"); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value = (0.93, 0.93, 0.94, 1); b.inputs["Roughness"].default_value = 0.9
    fo.data.materials.append(m)

def render_cfg(sc, w, h, samples=24):
    sc.render.engine = "BLENDER_EEVEE"
    sc.render.resolution_x, sc.render.resolution_y = w, h
    sc.render.image_settings.file_format = "PNG"
    for attr, val in (("taa_render_samples", samples), ("use_gtao", True), ("use_shadows", True), ("use_raytracing", False)):
        try: setattr(sc.eevee, attr, val)
        except Exception: pass
    try: sc.view_settings.view_transform = "Standard"
    except Exception: pass

def fit_camera(sc, objs, direction, lens=45, margin=0.92, up=(0, 0, 1), aspect=None, center_bias=(0, 0, 0)):
    cam = bpy.data.cameras.new("cam"); cam.lens = lens; cam.clip_end = 50
    co = bpy.data.objects.new("cam", cam); sc.collection.objects.link(co); sc.camera = co
    bpy.context.view_layer.update()
    pts = []
    for o in objs:
        for c in o.bound_box:
            pts.append(o.matrix_world @ Vector(c))
    mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    ctr = (mn + mx) / 2 + Vector(center_bias)
    d = Vector(direction).normalized()
    # look-at
    def place(dist):
        co.location = ctr + d * dist
        fwd = (ctr - co.location).normalized()
        co.rotation_euler = fwd.to_track_quat("-Z", "Y").to_euler()
        bpy.context.view_layer.update()
    lo, hi = 0.2, 40.0
    for _ in range(40):
        mid = (lo + hi) / 2
        place(mid)
        xs, ys = [], []
        for p in pts:
            v = world_to_camera_view(sc, co, p); xs.append(v.x); ys.append(v.y)
        ext = max(max(xs) - min(xs), max(ys) - min(ys) * (sc.render.resolution_y / sc.render.resolution_x) * 0 + 0)
        fitx = (max(xs) - min(xs)); fity = (max(ys) - min(ys))
        if fitx > margin or fity > margin or min(xs) < 0.03 or max(xs) > 0.97 or min(ys) < 0.03 or max(ys) > 0.97: lo = mid
        else: hi = mid
    place(hi)
    # re-center on screen
    xs, ys = [], []
    for p in pts:
        v = world_to_camera_view(sc, co, p); xs.append(v.x); ys.append(v.y)
    return co

def render(sc, path):
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)

def project_points(sc, cam, pts_mm):
    out = []
    W, H = sc.render.resolution_x, sc.render.resolution_y
    for p in pts_mm:
        v = world_to_camera_view(sc, cam, Vector((p[0] * 0.001, p[1] * 0.001, p[2] * 0.001)))
        out.append((v.x * W, (1 - v.y) * H, v.z))
    return out

# ------------------------------------------------------------------ views
def build_scene(parts, only=None, hide=(), explode=None):
    sc = reset_scene()
    objs = []
    for q in parts:
        if only is not None and q.pid not in only: continue
        if q.pid in hide: continue
        off = (explode or {}).get(q.pid, (0, 0, 0))
        objs.append(add_obj(q, off))
    return sc, objs

VIEWS = {
    # name: (include-filter, hide, direction, size, lens)
    "hero_all": dict(hide=(), direction=(0.35, 1.0, 0.55), size=(2400, 1000), lens=40),
    "hero_ext": dict(only=lambda q: q.group in ("frame", "drive", "barrel", "feed", "electronics") and q.pid not in ("H02", "H03"),
                     direction=(0.55, -1.0, 0.45), size=(2000, 1200), lens=45),
    "drive": dict(only=lambda q: q.pid in ("H10", "H11", "H12", "H13", "H14", "H15", "H16", "H17", "H21", "P01", "P02", "P03", "P04", "H01", "H20", "H22"),
                  direction=(0.5, -1.0, 0.45), size=(1800, 1000), lens=50),
    "hopper": dict(only=lambda q: q.pid in ("P05", "P06", "P07", "P08a", "P08b", "P09", "P10", "H46", "H51", "H56", "H25", "H24", "H34", "H01", "P03", "H23", "H22", "H26"),
                   direction=(0.75, -1.0, 0.35), size=(1500, 1500), lens=50),
    "bath": dict(only=lambda q: q.pid in ("P11", "P12", "P13a", "P13b", "H47", "H54", "H57", "P14", "P15", "P16", "P17", "H35", "H44", "H45", "H02", "H39"),
                 direction=(-0.45, 1.0, 0.55), size=(2000, 1000), lens=50),
    "spooler": dict(only=lambda q: (q.group in ("spooler", "filament") or q.pid == "H03") and q.pid != "H39", direction=(-0.55, -1.0, 0.5), size=(1800, 1000), lens=50),
    "die": dict(only=lambda q: q.pid in ("H26", "H27", "H28", "H29", "H30", "H31", "H02", "P11", "H39", "H01", "H32"),
                direction=(0.7, -1.0, 0.45), size=(1800, 1000), lens=50),
}

def do_render(name, parts, explode=None, extra_hide=()):
    v = VIEWS[name]
    only = None
    if "only" in v:
        pf = v["only"]; only = {q.pid for q in parts if pf(q)}
    sc, objs = build_scene(parts, only=only, hide=tuple(v.get("hide", ())) + tuple(extra_hide), explode=explode)
    zfloor = (P["rail_top"] - 20 - 0.3) * 0.001
    setup_world_lights(sc, zfloor)
    render_cfg(sc, *v["size"])
    cam = fit_camera(sc, objs, v["direction"], lens=v["lens"])
    path = f"{OUT}/img/{name}.png"
    render(sc, path)
    return path

EXPLODE = {
    "H01": (0, 0, -40),
    "H10": (-150, 0, 0), "H11": (-75, 0, 0),
    "H12": (0, 0, 70), "H13": (20, 0, 115), "H14": (0, 0, 60), "H15": (10, 0, 55), "H16": (28, 0, 88), "H17": (50, 0, 55),
    "H21": (75, 0, 0), "H20": (60, 0, 110), "P04": (30, 0, 150),
    "H22": (35, 0, 0), "H23": (70, 0, 0), "H24": (105, 0, 0), "H25": (105, 0, 50), "H34": (105, 0, 0),
    "P05": (105, 0, 100), "P09": (60, 0, 150), "P06": (105, 0, 260), "P07": (105, 0, 400),
    "H26": (170, 0, 0), "H27": (270, 0, 0), "H28": (300, 0, 0),
    "H29": (170, 0, 60), "H30": (170, 0, 60), "H31": (170, 0, 125), "H32": (60, 0, 0),
}
EXPL_KEEP = {"H01", "H10", "H11", "H12", "H13", "H14", "H15", "H16", "H17", "H20", "H21", "H22", "H23", "H24", "H25", "H26", "H27", "H28", "H29", "H30", "H31", "H32", "H34",
             "P01", "P02", "P03", "P04", "P05", "P06", "P07", "P09"}
EXPL_HIDE = ()

def do_exploded(parts):
    sc, objs = build_scene(parts, only=EXPL_KEEP, explode=EXPLODE)
    setup_world_lights(sc, (P["rail_top"] - 20 - 40 - 0.3) * 0.001)
    render_cfg(sc, 2400, 1400)
    cam = fit_camera(sc, objs, (0.30, -1.0, 0.45), lens=45, margin=0.94)
    path = f"{OUT}/img/exploded.png"
    render(sc, path)
    # marker anchors
    anchors = {}
    for q in parts:
        if q.pid not in EXPL_KEEP: continue
        o = EXPLODE.get(q.pid, (0, 0, 0))
        b = q.mesh.bounds
        c = (b[0] + b[1]) / 2
        anchors[q.pid] = [float(c[0] + o[0]), float(c[1] + o[1]), float(c[2] + o[2])]
    pr = project_points(sc, cam, list(anchors.values()))
    json.dump({k: [round(v[0], 1), round(v[1], 1)] for k, v in zip(anchors.keys(), pr)}, open(f"{OUT}/img/exploded_markers.json", "w"))
    return path

def export_fbx(parts, path):
    sc, objs = build_scene(parts)
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs: o.select_set(True)
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, global_scale=1.0, apply_unit_scale=True,
                             object_types={"MESH"}, mesh_smooth_type="FACE" if False else "OFF", path_mode="COPY" if False else "AUTO")

if __name__ == "__main__":
    parts = fm_model.build()
    args = sys.argv[1:]
    if "stl" in args:
        res = export_stl(parts)
        for r in res: print(r)
    if "fbx" in args:
        export_fbx(parts, f"{OUT}/filament_maker_assembly.fbx"); print("fbx ok")
    if "exploded" in args:
        print(do_exploded(parts))
    for a in args:
        if a.startswith("render:"):
            for n in a.split(":")[1].split(","):
                print(do_render(n, parts))

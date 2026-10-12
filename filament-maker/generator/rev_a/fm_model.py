"""Parametric geometry for the filament maker (runs anywhere trimesh + manifold3d + shapely are installed)."""
import math
import numpy as np
import trimesh
import trimesh.boolean as B
from trimesh.transformations import rotation_matrix as RM
from shapely.geometry import Polygon, box as sbox, Point
from shapely.ops import unary_union
from fm_params import P

# ------------------------------------------------------------------ helpers
def box(x0, x1, y0, y1, z0, z1):
    m = trimesh.creation.box(extents=(x1 - x0, y1 - y0, z1 - z0))
    m.apply_translation(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    return m

def cylx(x0, x1, r, y=0.0, z=0.0, n=72):
    m = trimesh.creation.cylinder(radius=r, height=x1 - x0, sections=n)
    m.apply_transform(RM(math.pi / 2, [0, 1, 0]))
    m.apply_translation(((x0 + x1) / 2, y, z))
    return m

def cyly(y0, y1, r, x=0.0, z=0.0, n=72):
    m = trimesh.creation.cylinder(radius=r, height=y1 - y0, sections=n)
    m.apply_transform(RM(-math.pi / 2, [1, 0, 0]))
    m.apply_translation((x, (y0 + y1) / 2, z))
    return m

def cylz(z0, z1, r, x=0.0, y=0.0, n=72):
    m = trimesh.creation.cylinder(radius=r, height=z1 - z0, sections=n)
    m.apply_translation((x, y, (z0 + z1) / 2))
    return m

def U(*ms):
    ms = [m for m in ms if m is not None]
    return B.union(ms, engine="manifold") if len(ms) > 1 else ms[0]

def D(a, *bs):
    return B.difference([a] + [b for b in bs if b is not None], engine="manifold")

def cat(*ms):
    return trimesh.util.concatenate([m for m in ms if m is not None])

def tube_x(x0, x1, ro, ri, y=0.0, z=0.0, n=72):
    return D(cylx(x0, x1, ro, y, z, n), cylx(x0 - 1, x1 + 1, ri, y, z, n))

def prism_xz(pts, y0, y1):
    """polygon given in (x,z), extruded between y0..y1"""
    m = trimesh.creation.extrude_polygon(Polygon(pts), height=y1 - y0)
    m.apply_transform(RM(math.pi / 2, [1, 0, 0]))
    m.apply_translation((0, y1, 0))
    return m

def extrude_x(poly, x0, x1):
    """shapely polygon in (y,z) extruded between x0..x1"""
    m = trimesh.creation.extrude_polygon(poly, height=x1 - x0)
    M = np.array([[0, 0, 1, 0], [1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1]], float)
    m.apply_transform(M)
    m.apply_translation((x0, 0, 0))
    return m

def hexprism_x(x0, x1, af, y=0.0, z=0.0):
    r = af / math.sqrt(3)
    m = trimesh.creation.cylinder(radius=r, height=x1 - x0, sections=6)
    m.apply_transform(RM(math.pi / 2, [0, 1, 0]))
    m.apply_translation(((x0 + x1) / 2, y, z))
    return m

def rounded_box(x0, x1, y0, y1, z0, z1, r=3.0):
    # cheap: box with chamfer-like rounded vertical edges in Z
    poly = sbox(x0 + r, y0 + r, x1 - r, y1 - r).buffer(r, 12)
    m = trimesh.creation.extrude_polygon(poly, height=z1 - z0)
    m.apply_translation((0, 0, z0))
    return m

def helix_flight(x0, x1, r_in, r_out, pitch, t, steps_per_turn=40):
    turns = (x1 - x0 - t) / pitch
    n = int(turns * steps_per_turn) + 1
    th = np.linspace(0, turns * 2 * math.pi, n)
    xs = x0 + t / 2 + pitch * th / (2 * math.pi)
    loops = []
    for a, x in zip(th, xs):
        ca, sa = math.cos(a), math.sin(a)
        corners = [(x - t / 2, r_in), (x - t / 2, r_out), (x + t / 2, r_out), (x + t / 2, r_in)]
        loops.append([(xx, rr * ca, rr * sa) for xx, rr in corners])
    V = np.array(loops).reshape(-1, 3)
    F = []
    for k in range(n - 1):
        for i in range(4):
            a = k * 4 + i; b = k * 4 + (i + 1) % 4
            c = (k + 1) * 4 + (i + 1) % 4; d = (k + 1) * 4 + i
            F += [[a, b, c], [a, c, d]]
    F += [[0, 1, 2], [0, 2, 3]]
    e = (n - 1) * 4
    F += [[e, e + 2, e + 1], [e, e + 3, e + 2]]
    m = trimesh.Trimesh(V, F, process=True)
    trimesh.repair.fix_normals(m)
    return m

def profile_2020(L_poly=True):
    s = 20.0
    outer = sbox(-s / 2, -s / 2, s / 2, s / 2)
    cuts = []
    for ang in (0, 90, 180, 270):
        # slot opening + T chamber on +Y side, rotated
        op = sbox(-3.1, s / 2 - 1.8, 3.1, s / 2 + 0.01)
        ch = sbox(-5.0, 5.2, 5.0, s / 2 - 1.8)
        slot = unary_union([op, ch])
        from shapely import affinity
        cuts.append(affinity.rotate(slot, ang, origin=(0, 0)))
    hole = Point(0, 0).buffer(2.1, 16)
    return outer.difference(unary_union(cuts + [hole]))

_RAIL_POLY = None
def rail_x(x0, x1, y, ztop):
    global _RAIL_POLY
    if _RAIL_POLY is None:
        _RAIL_POLY = profile_2020()
    m = extrude_x(_RAIL_POLY, x0, x1)
    m.apply_translation((0, y, ztop - 10))
    return m

def holes_pcd_x(x0, x1, pcd, d, n=4, off=45):
    out = []
    for k in range(n):
        a = math.radians(off + 360 * k / n)
        out.append(cylx(x0, x1, d / 2, pcd / 2 * math.cos(a), pcd / 2 * math.sin(a), 24))
    return out

# ------------------------------------------------------------------ registry
class Part:
    def __init__(self, pid, name, kind, color, mesh, group, note="", print_rot=None):
        self.pid, self.name, self.kind, self.color, self.mesh = pid, name, kind, color, mesh
        self.group, self.note, self.print_rot = group, note, print_rot

PARTS = []
def add(pid, name, kind, color, mesh, group, note="", print_rot=None):
    PARTS.append(Part(pid, name, kind, color, mesh, group, note, print_rot))

def build():
    PARTS.clear()
    p = P
    ry, rt, ft = p["rail_y"], p["rail_top"], p["foot_t"]
    foot_z0, foot_z1 = rt, rt + ft                     # -85 .. -75

    # =============================== FRAME (hardware)
    for mi, (x0, x1) in enumerate((p["mod1_x"], p["mod2_x"], p["mod3_x"]), 1):
        add(f"H0{mi}", f"2020 rail pair - module {mi}", "hardware", "alu",
            cat(rail_x(x0, x1, -ry, rt), rail_x(x0, x1, ry, rt)), "frame")

    # =============================== DRIVE (hardware)
    gb, gl = p["gb"], p["gb_len"]
    mo, ml = p["motor"], p["motor_len"]
    stepper = extrude_x(sbox(-mo / 2, -mo / 2, mo / 2, mo / 2), -gl - ml, -gl)
    gearbox = U(extrude_x(sbox(-gb / 2, -gb / 2, gb / 2, gb / 2), -gl, -2),
                cylx(-2, 0, 19), cylx(0, p["gb_shaft_l"], p["gb_shaft_d"] / 2, 0, 0, 48))
    add("H10", "NEMA 23 stepper (3 Nm class)", "hardware", "black", stepper, "drive")
    add("H11", "NEMA 23 planetary gearbox 20:1", "hardware", "steel", gearbox, "drive")
    cx0, cx1 = p["cpl_x"]
    cpl = U(cylx(cx0, cx1, p["cpl_d"] / 2), cyly(-14, 14, 2.6, (cx0 + 8), p["cpl_d"] / 2 - 2),
            cyly(-14, 14, 2.6, (cx1 - 8), p["cpl_d"] / 2 - 2))
    add("H12", "Clamp coupler 14 -> 12.7", "hardware", "steel", cpl, "drive")
    sx0, sx1 = p["spindle_x"]
    add("H13", "Spindle 1/2\" rod", "hardware", "steel", cylx(sx0, sx1, p["spindle_d"] / 2, 0, 0, 40), "drive")
    r8 = p["r8"]; hx0, hx1 = p["house_x"]
    b1 = tube_x(hx0 + 4, hx0 + 4 + r8["w"], r8["od"] / 2, r8["id"] / 2)
    b2 = tube_x(hx1 - 4 - r8["w"], hx1 - 4, r8["od"] / 2, r8["id"] / 2)
    add("H14", "R8-2RS bearing x2", "hardware", "steel", cat(b1, b2), "drive")
    t0, t1 = p["thrust_x"]
    add("H15", "Thrust bearing 1/2\" bore", "hardware", "steel", tube_x(t0, t1, p["thrust"]["od"] / 2, p["thrust"]["id"] / 2), "drive")
    c0, c1 = p["collar_x"]
    add("H16", "Shaft collar 1/2\"", "hardware", "black", tube_x(c0, c1, p["collar_d"] / 2, p["spindle_d"] / 2), "drive")
    k0, k1 = p["chuck_x"]
    chuck = U(cylx(k0, k0 + 30, 18), cylx(k0 + 30, k1 - 5, p["chuck_d"] / 2), cylx(k1 - 5, k1, 16))
    chuck = D(chuck, cylx(k1 - 32, k1 + 1, 6.4, 0, 0, 24))
    add("H17", "13 mm keyless chuck", "hardware", "steel", chuck, "drive")

    # =============================== PRINTED: MOTOR WALL
    w0, w1 = p["wall_x"]
    wall = U(box(w0, w1, -70, 70, foot_z0, 62), box(-100, 40, -70, 70, foot_z0, foot_z1),
             prism_xz([(w1, foot_z1), (-60, foot_z1), (w1, 45)], 48, 56),
             prism_xz([(w1, foot_z1), (-60, foot_z1), (w1, 45)], -56, -48))
    cut = [cylx(w0 - 1, w1 + 1, 21, 0, 0, 64)] + holes_pcd_x(w0 - 1, w1 + 1, p["gb_pcd"], 5.5)
    cut += [cylz(foot_z0 - 1, foot_z1 + 1, 2.9, x, y, 20) for x in (-80, -30, 20) for y in (-ry, ry)]
    wall = D(wall, *cut)
    add("P01", "Motor wall", "printed", "print", wall, "drive",
        "PETG/ASA, 5 walls, 50% gyroid. Print on its side (Y up).", RM(math.pi / 2, [1, 0, 0]))

    # =============================== PRINTED: BEARING HOUSING (+ thrust flange)
    fx0, fx1 = p["flange_x"]; hw = p["house_w"] / 2; fw = p["flange_w"] / 2
    rp, rd = p["rod_pos"], p["rod_d"]
    house = U(box(hx0, hx1, -hw, hw, -hw, hw), box(hx0, hx1, -26, 26, foot_z0, 0),
              box(hx0 - 7, fx1 - 5, -70, 70, foot_z0, foot_z1), box(fx0, fx1, -fw / 2 - 0, fw / 2 + 0, -fw / 2, fw / 2),
              prism_xz([(fx0, foot_z1), (fx0 - 50, foot_z1), (fx0, -hw)], 24, 32),
              prism_xz([(fx0, foot_z1), (fx0 - 50, foot_z1), (fx0, -hw)], -32, -24))
    cut = [cylx(hx0 - 1, fx1 + 1, 7.4, 0, 0, 40),
           cylx(hx0 - 1, hx0 + 4 + r8["w"] + 0.4, r8["od"] / 2 + 0.15, 0, 0, 72),
           cylx(hx1 - 4 - r8["w"] - 0.4, hx1 + 0.01, r8["od"] / 2 + 0.15, 0, 0, 72),
           cylx(fx0 + 8, fx1 + 1, 15.2, 0, 0, 72)]
    for sy in (-1, 1):
        for sz in (-1, 1):
            cut.append(cylx(fx0 - 1, fx1 + 1, rd / 2, sy * rp, sz * rp, 24))
    cut += [cylz(foot_z0 - 1, foot_z1 + 1, 2.9, x, y, 20) for x in (hx0 + 5, hx0 + 70) for y in (-ry, ry)]
    house = D(house, *cut)
    add("P02", "Bearing housing + thrust flange", "printed", "print", house, "drive",
        "PETG/ASA, 6 walls, 60% infill. Print flange-face down (X up): layers then lie in the thrust plate, not across it.", RM(math.pi / 2, [0, 1, 0]))

    # =============================== SCREW (hardware)
    s0, s1 = p["shank_x"]; f0, f1 = p["flights_x"]
    shank = hexprism_x(s0, s1, p["shank_af"])
    core = cylx(s1 - 6, f1, p["screw_core"] / 2, 0, 0, 40)
    flight = helix_flight(f0, f1, p["screw_core"] / 2 - 0.3, p["screw_od"] / 2, p["screw_pitch"], p["screw_flight_t"])
    add("H20", "Ship auger screw 20 mm (7/16\" hex shank)", "hardware", "steel", cat(shank, core, flight), "barrel")

    # =============================== PRINTED: HEAD PLATE
    h0, h1 = p["head_x"]
    head = U(box(h0, h1, -70, 70, foot_z0, 74), box(h0 - 15, h1, -70, 70, foot_z0, foot_z1),
             prism_xz([(h0, foot_z1), (h0 - 40, foot_z1), (h0, 20)], 56, 64),
             prism_xz([(h0, foot_z1), (h0 - 40, foot_z1), (h0, 20)], -64, -56))
    cut = [cylx(h0 - 1, h1 + 1, 15.2, 0, 0, 64)] + holes_pcd_x(h0 - 1, h1 + 1, p["fl_bc"], 7.0)
    for sy in (-1, 1):
        for sz in (-1, 1):
            cut.append(cylx(h0 - 1, h1 + 1, rd / 2, sy * rp, sz * rp, 24))
    cut += [cylz(foot_z0 - 1, foot_z1 + 1, 2.9, x, y, 20) for x in (h0 - 8, h0 + 8) for y in (-ry, ry)]
    head = D(head, *cut)
    add("P03", "Head plate (barrel anchor)", "printed", "print", head, "barrel",
        "PETG/ASA, 6 walls, 60% infill. Print plate-face down (X up), same reason as the housing.", RM(math.pi / 2, [0, 1, 0]))

    # tie rods (hardware)
    rods = []
    for sy in (-1, 1):
        for sz in (-1, 1):
            rods.append(cylx(fx0 - 14, h1 + 14, 4, sy * rp, sz * rp, 20))
    nuts = []
    for sy in (-1, 1):
        for sz in (-1, 1):
            for xx in ((fx0 - 14, fx0 - 6), (h1, h1 + 6.5), (h1 + 6.5, h1 + 11.5)):
                if xx[1] - xx[0] > 6:
                    nuts.append(hexprism_x(xx[0], xx[1], 13, sy * rp, sz * rp))
    add("H21", "M8 tie rods x4 + nuts", "hardware", "steel", cat(*rods, *[n for n in nuts if n is not None]), "drive")

    # =============================== BARREL STACK (hardware)
    fh0, fh1 = p["fl_hub_x"]
    flange = U(cylx(h1, h1 + p["fl_t"], p["fl_od"] / 2, 0, 0, 72), cylx(h1 + p["fl_t"], fh1, 19))
    flange = D(flange, cylx(h1 - 1, fh1 + 1, 13.3, 0, 0, 48), *holes_pcd_x(h1 - 1, h1 + p["fl_t"] + 1, p["fl_bc"], 7.0))
    add("H22", "3/4\" NPT floor flange", "hardware", "steel", flange, "barrel")
    n0, n1 = p["close_nip_x"]
    add("H23", "3/4\" close nipple", "hardware", "steel", tube_x(n0, n1, 13.3, 10.4), "barrel")
    t0x, t1x = p["tee_x"]; tcx = (t0x + t1x) / 2
    tee = U(cylx(t0x, t1x, p["tee_d"] / 2), cylz(0, p["port_h"], p["tee_d"] / 2, tcx, 0))
    tee = D(tee, cylx(t0x - 1, t1x + 1, 10.5, 0, 0, 48), cylz(-1, p["port_h"] + 1, 10.5, tcx, 0, 48))
    add("H24", "3/4\" pipe tee (feed port)", "hardware", "steel", tee, "barrel")
    add("H25", "Feed nipple 3/4\" x 2\"", "hardware", "steel", D(cylz(p["port_h"] - 13, p["port_h"] + 38, 13.3, tcx, 0, 48), cylz(p["port_h"] - 14, p["port_h"] + 39, 10.4, tcx, 0, 48)), "barrel")
    b0, b1x = p["barrel_x"]
    add("H26", "Barrel: 3/4\" Sch40 stainless nipple, 12\"", "hardware", "steel", tube_x(b0, b1x, p["barrel_od"] / 2, p["barrel_id"] / 2), "barrel")
    cp0, cp1 = p["cap_x"]
    cap = D(cylx(cp0, cp1, p["cap_od"] / 2), cylx(cp0 - 1, cp1 - 8, 13.4, 0, 0, 48))
    cap = D(cap, cylx(cp1 - 9, cp1 + 1, 5, 0, 0, 32))
    add("H27", "3/4\" NPT cap (die body)", "hardware", "brass", cap, "barrel")
    d0, d1 = p["die_x"]
    die = D(U(cylx(cp1 - 8, cp1, 4.9, 0, 0, 32), hexprism_x(cp1, d1, 14)), cylx(cp1 - 9, d1 + 1, p["die_d"] / 2, 0, 0, 24))
    add("H28", "Die plug (hand-drilled 2.2 mm)", "hardware", "brass", die, "barrel")
    bands = []
    for (a, b) in p["bands"]:
        band = tube_x(a, b, p["band_od"] / 2, p["band_id"] / 2)
        band = U(band, box(a + 8, b - 8, -8, 8, p["band_od"] / 2 - 2, p["band_od"] / 2 + 5))
        bands.append(band)
    add("H29", "Band heaters x4 (120 V, 150-200 W)", "hardware", "heater", cat(*bands), "barrel")
    # thermocouples / leads (stubs)
    tcs = [cyly(-52, -p["band_od"] / 2 + 2, 1.6, (a + b) / 2 + 12, 0, 12) for (a, b) in p["bands"]]
    add("H30", "K thermocouples x4", "hardware", "copper", cat(*tcs), "barrel")
    # heat guard: perforated half-pipe cover over bands
    g0, g1 = p["bands"][0][0] - 6, p["die_x"][0] - 2
    ring = D(cylx(g0, g1, 30, 0, 0, 72), cylx(g0 - 1, g1 + 1, 28.5, 0, 0, 72))
    ring = D(ring, box(g0 - 1, g1 + 1, -40, 40, -40, 9))       # open sides: top arc only
    add("H31", "Heat guard (perforated sheet, hand-bent)", "hardware", "alu", ring, "barrel")
    # barrel strap on angle bracket
    sxx = p["strap_x"]
    strap = U(D(cylx(sxx - 8, sxx + 8, 17.5, 0, 0, 48), cylx(sxx - 9, sxx + 9, 13.3, 0, 0, 48)),
              box(sxx - 8, sxx + 8, -30, 30, foot_z0, foot_z0 + 3),
              box(sxx - 8, sxx + 8, -4, 4, foot_z0, -17), )
    add("H32", "Barrel support strap + angle post", "hardware", "alu", strap, "barrel")

    # =============================== PRINTED: HOPPER
    hc = p["hopper_cx"]; zb = p["port_h"] + 8; collar_h = 30; cone_h = 40
    r_in_c = p["hop_collar_id"] / 2; r_out_c = r_in_c + 3
    top = p["hop_top_r"]; wall_t = 2.4; ztop = zb + collar_h + cone_h + (p["hop_h"] - collar_h - cone_h - 40)
    ztop = p["hop_h"]
    z1 = zb + collar_h; z2 = z1 + cone_h
    outer = np.array([[r_out_c, zb], [r_out_c, z1], [top, z2], [top, ztop], [top - wall_t, ztop], [top - wall_t, z2 + 0.6],
                      [r_in_c, z1 - 0.2], [r_in_c, zb], [r_out_c, zb]])
    hop = trimesh.creation.revolve(outer, sections=96)
    hop.merge_vertices(); trimesh.repair.fill_holes(hop); trimesh.repair.fix_normals(hop)
    # revolve gives axis = Z with profile (x=r, y=?) -> make sure axis vertical
    hop.apply_translation((hc, 0, 0))
    add("P04", "Hopper (2.7 L)", "printed", "print", hop, "feed", "PETG, 3 walls, 15% infill, no top layers. Print upright.", None)
    lid = U(cylz(ztop, ztop + 3, top + 2, hc, 0, 96), cylz(ztop - 6, ztop, top - wall_t - 0.4, hc, 0, 96))
    lid = D(lid, cylz(ztop - 7, ztop - 2, top - wall_t - 3.2, hc, 0, 96))
    add("P05", "Hopper lid", "printed", "print", lid, "feed", "PETG. Print upside down.", RM(math.pi, [1, 0, 0]))

    # =============================== COOLING TROUGH (printed) + fans
    tx0, tx1 = p["trough_x"]; tw = p["trough_w"] / 2
    seg_len = (tx1 - tx0) / 2
    tr = []
    for i in range(2):
        a = tx0 + i * seg_len; b = a + seg_len - 1
        blk = box(a, b, -tw, tw, -34, 8)
        v = trimesh.creation.extrude_polygon(Polygon([(-9, 8.1), (9, 8.1), (0, -1.0)]), height=b - a + 2)
        v.apply_transform(np.array([[0, 0, 1, 0], [1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1]], float))
        v.apply_translation((a - 1, 0, 0))
        seg = D(blk, v)
        tr.append(seg)
        add(f"P06{'ab'[i]}", f"Cooling trough segment {'AB'[i]}", "printed", "print", seg, "cooling",
            "PETG. Print upside down (V-groove up needs support) or on its side.", None)
    fans = []; ducts = []
    for k, xx in enumerate((tx0 + 60, tx0 + 175, tx0 + 290, tx0 + 380)):
        fans.append(box(xx - 20, xx + 20, -20, 20, 38, 48))
        ducts.append(D(box(xx - 20, xx + 20, -20, 20, 10, 38), box(xx - 17, xx + 17, -17, 17, 9, 39)))
    add("P07", "Fan ducts x4", "printed", "print", cat(*ducts), "cooling", "PETG, 3 walls. Print upright.", None)
    add("H33", "40 mm 24 V fans x4", "hardware", "black", cat(*fans), "cooling")
    # feed-throat fan
    ffan = box(tcx - 20, tcx + 20, -70, -60, 5, 45)
    add("H34", "Feed-throat fan 40 mm", "hardware", "black", ffan, "feed")

    # =============================== PULLER
    pu0, pu1 = p["puller_x"]; rd_ = p["roller_d"] / 2; rw = p["roller_w"]
    pcx = (pu0 + pu1) / 2
    plate_b = box(pu0, pu1, -48, -40, foot_z0, 50)
    plate_a = box(pu0, pu1, 40, 48, foot_z0, 50)
    base = box(pu0 - 15, pu1 + 15, -70, 70, foot_z0, foot_z1)
    nipz0 = rd_ + 0.875
    plate_a = D(plate_a, cyly(39, 49, 12, pcx, -nipz0), cyly(39, 49, 3, pcx, nipz0))
    puller = U(plate_a, plate_b, base)
    puller = D(puller, *[cylz(foot_z0 - 1, foot_z1 + 1, 2.9, x, y, 20) for x in (pu0 - 5, pu1 + 5) for y in (-ry, ry)])
    add("P08", "Puller frame (base + side plates)", "printed", "print", puller, "puller", "PETG, 5 walls. Print on its back.", None)
    nipz = rd_ + 0.875
    drive_roll = U(cyly(-20, 20, rd_, pcx, -nipz, 72), cyly(20, 38, 6, pcx, -nipz, 24))
    add("P09", "Puller drive roller + TPU tyre", "printed", "tpu", drive_roll, "puller", "Hub PETG, tyre TPU 95A (or glue 3 mm silicone).", None)
    idler = cyly(-20, 20, rd_, pcx, nipz - 0.3, 72)
    arm = box(pcx - 8, pcx + 8, -44, 44, rd_ + 18, rd_ + 26)
    add("P10", "Puller idler roller + spring arm", "printed", "tpu", cat(idler, arm), "puller", "As P09.", None)
    n17 = box(pcx - 21, pcx + 21, 48, 88, -nipz - 21, -nipz + 21)
    add("H35", "NEMA 17 stepper (puller)", "hardware", "black", n17, "puller")

    # =============================== SPOOLER
    scx, scz = p["spool_cx"], p["spool_cz"]
    plate_z0, plate_z1 = foot_z0, scz + 60
    mplate = box(scx - 40, scx + 40, 40, 50, plate_z0, plate_z1)
    iplate = box(scx - 40, scx + 40, -50, -40, plate_z0, plate_z1)
    sbase = box(scx - 55, scx + 55, -70, 70, foot_z0, foot_z1)
    mplate = D(mplate, cyly(39, 51, 9, scx, scz))
    iplate = D(iplate, cyly(-51, -39, 4.2, scx, scz, 24))
    sp = U(mplate, iplate, sbase,
           prism_xz([(scx - 40, foot_z1), (scx - 70, foot_z1), (scx - 40, 20)], 42, 48),
           prism_xz([(scx - 40, foot_z1), (scx - 70, foot_z1), (scx - 40, 20)], -48, -42))
    sp = D(sp, *[cylz(foot_z0 - 1, foot_z1 + 1, 2.9, x, y, 20) for x in (scx - 40, scx + 40) for y in (-ry, ry)])
    add("P11", "Spooler plates + base", "printed", "print", sp, "spooler", "PETG, 5 walls. Print on its back.", None)
    cone_d = U(cyly(28, 40, 29, scx, scz, 72), cyly(40, 44, 14, scx, scz, 48))
    cone_i = U(cyly(-40, -28, 29, scx, scz, 72), cyly(-44, -40, 12, scx, scz, 48))
    add("P12", "Spool hub cones x2", "printed", "print", cat(cone_d, cone_i), "spooler", "PETG, 100% infill on the shaft boss.", None)
    gm = U(cyly(50, 110, 18.5, scx, scz, 48), cyly(110, 118, 8, scx, scz, 24))
    add("H36", "37 mm 24 V gearmotor, 12 rpm", "hardware", "steel", gm, "spooler")
    # spool + filament
    sfl = U(cyly(-spool_t(p) / 2, -spool_t(p) / 2 + 3, p["spool_od"] / 2, scx, scz, 96),
            cyly(spool_t(p) / 2 - 3, spool_t(p) / 2, p["spool_od"] / 2, scx, scz, 96))
    sfl = D(sfl, cyly(-40, 40, p["spool_bore"] / 2, scx, scz, 48))
    score = D(cyly(-spool_t(p) / 2, spool_t(p) / 2, p["spool_core"] / 2, scx, scz, 96), cyly(-40, 40, p["spool_bore"] / 2, scx, scz, 48))
    add("H37", "1 kg filament spool (200 mm)", "hardware", "spool", cat(sfl, score), "spooler")
    # dancer
    dx = p["dancer_x"]
    post = box(dx - 8, dx + 8, -25, -5, foot_z0, 125)
    dbase = box(dx - 30, dx + 30, -70, 70, foot_z0, foot_z1)
    post = D(U(post, dbase), *[cylz(foot_z0 - 1, foot_z1 + 1, 2.9, x, y, 20) for x in (dx - 22, dx + 22) for y in (-ry, ry)])
    add("P13", "Dancer post + base", "printed", "print", post, "spooler", "PETG.", None)
    arm = U(prism_xz([(dx - 4, 110), (dx + 4, 112), (dx + 125, 2), (dx + 117, -4)], -5, 5), cyly(-5, 14, 11, dx + 121, -1, 48))
    add("P14", "Dancer arm + guide roller", "printed", "print", arm, "spooler", "PETG.", None)
    add("H38", "10 kΩ pot (dancer angle)", "hardware", "black", cyly(-25, -5, 8.5, dx, 111, 32), "spooler")
    # filament line
    fil = cylx(p["die_x"][1], p["spool_cx"] - 40, 0.9, 0, 0, 12)
    add("H39", "Filament line", "hardware", "filament", fil, "filament")

    # =============================== CONTROL BOX
    bx0, bx1, by0, by1, bz0, bz1 = -305, -65, -300, -130, -105, 5
    shell = D(box(bx0, bx1, by0, by1, bz0, bz1), box(bx0 + 3, bx1 - 3, by0 + 3, by1 - 3, bz0 + 3, bz1 + 1))
    for row in range(3):                                    # vents on the rear (+Y side wall) and ends
        for k in range(12):
            xx = bx0 + 18 + k * 18
            shell = D(shell, box(xx, xx + 8, by1 - 4, by1 + 1, bz0 + 12 + row * 22, bz0 + 24 + row * 22))
    for pz in range(3):
        for k in range(6):
            yy = by0 + 20 + k * 22
            shell = D(shell, box(bx1 - 4, bx1 + 1, yy, yy + 10, bz0 + 14 + pz * 26, bz0 + 28 + pz * 26))
    for k in range(4):                                       # REX-C100 windows
        xx = bx0 + 12 + k * 56
        shell = D(shell, box(xx, xx + 45, by0 - 1, by0 + 4, bz0 + 28, bz0 + 73))
    add("P15", "Control box shell", "printed", "print", shell, "electronics", "PETG, 3 walls. Print open side up (X length 240 fits a 245 bed).", None)
    lidm = box(bx0, bx1, by0, by1, bz1, bz1 + 3)
    lidm = D(lidm, cylz(bz1 - 1, bz1 + 4, 11, bx1 - 30, by0 + 30, 32),
             cylz(bz1 - 1, bz1 + 4, 4, bx0 + 40, by0 + 30, 24), cylz(bz1 - 1, bz1 + 4, 4, bx0 + 90, by0 + 30, 24),
             cylz(bz1 - 1, bz1 + 4, 3.2, bx0 + 140, by0 + 30, 24))
    add("P16", "Control box lid / top panel", "printed", "print", lidm, "electronics", "PETG. Print flat.", None)
    pid = []
    for k in range(4):
        xx = bx0 + 12 + k * 56
        pid.append(box(xx - 1, xx + 46, by0 + 3, by0 + 9, bz0 + 27, bz0 + 74))
    add("H40", "REX-C100 PID controllers x4", "hardware", "black", cat(*pid), "electronics")
    ctrl = []
    ctrl.append(cylz(bz1 + 3, bz1 + 20, 9, bx0 + 40, by0 + 30, 24)); ctrl.append(cylz(bz1 + 3, bz1 + 20, 9, bx0 + 90, by0 + 30, 24))
    add("H41", "Speed knobs (screw / puller)", "hardware", "steel", cat(*ctrl), "electronics")
    estop = U(cylz(bz1 + 3, bz1 + 10, 14, bx1 - 30, by0 + 30, 32), cylz(bz1 + 10, bz1 + 26, 10.5, bx1 - 30, by0 + 30, 32))
    add("H42", "E-stop (NC mushroom)", "hardware", "red", estop, "electronics")
    sw = cylz(bz1 + 3, bz1 + 16, 4, bx0 + 140, by0 + 30, 16)
    add("H43", "FWD / OFF / REV toggle", "hardware", "steel", sw, "electronics")
    return PARTS

def spool_t(p):
    return p["spool_w"]

def printed():
    return [q for q in PARTS if q.kind == "printed"]

if __name__ == "__main__":
    parts = build()
    for q in parts:
        m = q.mesh
        print(f"{q.pid:5s} {q.name:48s} {q.kind:8s} wt={m.is_watertight!s:5s} bounds={np.round(m.bounds[0]).astype(int)}..{np.round(m.bounds[1]).astype(int)}")

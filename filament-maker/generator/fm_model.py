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

def frustum_y(y0, y1, r0, r1, x=0.0, z=0.0, n=72):
    """cone frustum along +Y from y0 (radius r0) to y1 (radius r1)"""
    prof = np.array([[0, 0], [r0, 0], [r1, y1 - y0], [0, y1 - y0]], float)
    m = trimesh.creation.revolve(prof, sections=n)
    m.apply_transform(RM(-math.pi / 2, [1, 0, 0]))
    m.apply_translation((x, y0, z))
    return m

def revolve_z(pts, cx=0.0, cy=0.0, n=96):
    pts = [tuple(q) for q in pts]
    if pts[0] != pts[-1]: pts.append(pts[0])
    m = trimesh.creation.revolve(np.array(pts, float), sections=n)
    m.merge_vertices(); trimesh.repair.fill_holes(m); trimesh.repair.fix_normals(m)
    m.apply_translation((cx, cy, 0))
    return m

def seg(p0, p1, r=0.875, n=16):
    p0 = np.array(p0, float); p1 = np.array(p1, float)
    L = np.linalg.norm(p1 - p0)
    m = trimesh.creation.cylinder(radius=r, height=L, sections=n)
    T = trimesh.geometry.align_vectors([0, 0, 1], (p1 - p0) / L)
    m.apply_transform(T)
    m.apply_translation((p0 + p1) / 2)
    return m

def tangent_low(A, C, rc):
    """tangent point on circle (centre C, radius rc) of the line from A that passes on the LOWER side; (x,z) tuples"""
    ax, az = A; cx, cz = C
    dx, dz = cx - ax, cz - az
    L = math.hypot(dx, dz); a0 = math.atan2(dz, dx); al = math.asin(rc / L)
    best = None
    for s in (-1, 1):
        th = a0 + s * al
        l = math.sqrt(L * L - rc * rc)
        T = (ax + l * math.cos(th), az + l * math.sin(th))
        if best is None or T[1] < best[1]: best = T
    return best

def hopper_geom(p):
    r0 = p["hop_collar_id"] / 2.0; R = p["hop_R"]; t = p["hop_wall"]
    z0, z1 = p["hop_collar_z"]
    cone_h = (R - r0) * math.tan(math.radians(p["hop_cone_deg"]))
    return r0, R, t, z0, z1, z1 + cone_h

def hopper_volume_ml(p):
    r0, R, t, z0, z1, z2 = hopper_geom(p)
    h = z2 - z1
    v_cone = math.pi * h / 3 * (R * R + R * r0 + r0 * r0)
    v_col = math.pi * r0 * r0 * (z1 - z0)
    v_drum = math.pi * R * R * p["hop_drum_h"]
    return (v_cone + v_col + v_drum) / 1000.0

def dancer_tip(p, a_deg):
    a = math.radians(a_deg)
    return (p["dancer_x"] + p["dancer_L"] * math.sin(a), p["dancer_pivot_z"] - p["dancer_L"] * math.cos(a))

def dancer_arm_mesh(p, a_deg):
    dx, pz = p["dancer_x"], p["dancer_pivot_z"]
    tx, tz = dancer_tip(p, a_deg)
    v = np.array([tx - dx, tz - pz]); v /= np.linalg.norm(v); n = np.array([-v[1], v[0]])
    w = 6.0
    pts = [(dx + n[0] * w, pz + n[1] * w), (tx + n[0] * 5, tz + n[1] * 5), (tx - n[0] * 5, tz - n[1] * 5), (dx - n[0] * w, pz - n[1] * w)]
    plate = prism_xz(pts, -13, -7)
    hub = cyly(-13, -7, 9, dx, pz, 48)
    boss = cyly(-13, -7, 9, tx, tz, 48)
    arm = U(plate, hub, boss)
    arm = D(arm, cyly(-14, -6, 3.0, dx, pz, 32), cyly(-14, -6, 2.0, tx, tz, 24))
    roller = D(cyly(-5.5, 8.5, 10, tx, tz, 48), cyly(-6, 9, 2.2, tx, tz, 24))
    return arm, roller

# ------------------------------------------------------------------ registry
class Part:
    def __init__(self, pid, name, kind, color, mesh, group, note="", print_rot=None):
        self.pid, self.name, self.kind, self.color, self.mesh = pid, name, kind, color, mesh
        self.group, self.note, self.print_rot = group, note, print_rot

PARTS = []
FILAMENT_PATH = []
def add(pid, name, kind, color, mesh, group, note="", print_rot=None):
    PARTS.append(Part(pid, name, kind, color, mesh, group, note, print_rot))

def build():
    PARTS.clear()
    p = P
    ry, rt, ft = p["rail_y"], p["rail_top"], p["foot_t"]
    foot_z0, foot_z1 = rt, rt + ft                     # -85 .. -75
    feet = lambda xs, ys=(-ry, ry): [cylz(foot_z0 - 1, foot_z1 + 1, 2.9, x, y, 20) for x in xs for y in ys]

    # =============================== FRAME (hardware)
    for mi, (x0, x1) in enumerate((p["mod1_x"], p["mod2_x"], p["mod3_x"]), 1):
        add(f"H0{mi}", f"2020 rail pair - module {mi}", "hardware", "alu",
            cat(rail_x(x0, x1, -ry, rt), rail_x(x0, x1, ry, rt)), "frame")

    # =============================== DRIVE (hardware)
    gb, gl = p["gb"], p["gb_len"]
    mo, ml = p["motor"], p["motor_len"]
    pl0, pl1 = p["gb_pilot"]
    stepper = extrude_x(sbox(-mo / 2, -mo / 2, mo / 2, mo / 2), -gl - ml, -gl)
    gearbox = U(extrude_x(sbox(-gb / 2, -gb / 2, gb / 2, gb / 2), -gl, 0),
                cylx(pl0, pl1, p["gb_pilot_d"] / 2),
                cylx(pl1, pl1 + p["gb_shaft_l"], p["gb_shaft_d"] / 2, 0, 0, 48))
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
    chuck = D(chuck, cylx(k1 - 32, k1 + 1, 6.45, 0, 0, 24))
    add("H17", "13 mm keyless chuck", "hardware", "steel", chuck, "drive")

    # =============================== PRINTED: MOTOR WALL
    w0, w1 = p["wall_x"]
    wall = U(box(w0, w1, -70, 70, foot_z0, 62), box(-100, 40, -70, 70, foot_z0, foot_z1),
             prism_xz([(w1, foot_z1), (-60, foot_z1), (w1, 45)], 48, 56),
             prism_xz([(w1, foot_z1), (-60, foot_z1), (w1, 45)], -56, -48))
    cut = [cylx(w0 - 1, w1 + 1, 21, 0, 0, 64)] + holes_pcd_x(w0 - 1, w1 + 1, p["gb_pcd"], 5.5)
    cut += feet((-80, -30, 20))
    wall = D(wall, *cut)
    add("P01", "Motor wall", "printed", "print", wall, "drive",
        "PETG/ASA, 5 walls, 50% gyroid. Print on its side (Y up).", RM(math.pi / 2, [1, 0, 0]))

    # =============================== PRINTED: BEARING HOUSING (+ thrust flange)
    fx0, fx1 = p["flange_x"]; hw = p["house_w"] / 2; fw = p["flange_w"] / 2
    rp, rd = p["rod_pos"], p["rod_d"]
    house = U(box(hx0, hx1, -hw, hw, -hw, hw), box(hx0, hx1, -26, 26, foot_z0, 0),
              box(hx0 - 7, fx1 - 5, -70, 70, foot_z0, foot_z1), box(fx0, fx1, -fw, fw, -fw, fw),
              prism_xz([(fx0, foot_z1), (fx0 - 50, foot_z1), (fx0, -hw)], 24, 32),
              prism_xz([(fx0, foot_z1), (fx0 - 50, foot_z1), (fx0, -hw)], -32, -24))
    cut = [cylx(hx0 - 1, fx1 + 1, 7.4, 0, 0, 40),
           cylx(hx0 - 1, hx0 + 4 + r8["w"] + 0.4, r8["od"] / 2 + 0.15, 0, 0, 72),
           cylx(hx1 - 4 - r8["w"] - 0.4, hx1 + 0.01, r8["od"] / 2 + 0.15, 0, 0, 72),
           cylx(fx0 + 8, fx1 + 1, 15.2, 0, 0, 72)]
    for sy in (-1, 1):
        for sz in (-1, 1):
            cut.append(cylx(fx0 - 1, fx1 + 1, rd / 2, sy * rp, sz * rp, 24))
    cut += feet((hx0 + 5, hx0 + 70))
    house = D(house, *cut)
    add("P02", "Bearing housing + thrust flange", "printed", "print", house, "drive",
        "PETG/ASA, 6 walls, 60% infill. Print flange-face down (X up): layers then lie in the thrust plate, not across it.", RM(math.pi / 2, [0, 1, 0]))

    # =============================== SCREW (hardware)
    s0, s1 = p["shank_x"]; f0, f1 = p["flights_x"]
    shank = hexprism_x(s0, s1, p["shank_af"])
    core = cylx(s1 - 6, f1, p["screw_core"] / 2, 0, 0, 40)
    flight = helix_flight(f0, f1, p["screw_core"] / 2 - 0.3, p["screw_od"] / 2, p["screw_pitch"], p["screw_flight_t"])
    add("H20", "Ship auger screw 20 mm (7/16\" hex shank)", "hardware", "steel", cat(shank, core, flight), "barrel")

    # dust slinger on the shank (printed)
    sl0, sl1 = p["slinger_x"]
    sling = D(cylx(sl0, sl1, 20, 0, 0, 72), hexprism_x(sl0 - 1, sl1 + 1, p["shank_af"] - 0.1))
    add("P04", "Dust slinger (on the screw shank)", "printed", "print", sling, "barrel", "PETG, 100% infill. Press fit on the hex shank; throws flakes away from the head-plate bore.", RM(math.pi / 2, [0, 1, 0]))

    # =============================== PRINTED: HEAD PLATE
    h0, h1 = p["head_x"]
    head = U(box(h0, h1, -70, 70, foot_z0, 74), box(h0 - 15, h1, -70, 70, foot_z0, foot_z1),
             prism_xz([(h0, foot_z1), (h0 - 40, foot_z1), (h0, 20)], 56, 64),
             prism_xz([(h0, foot_z1), (h0 - 40, foot_z1), (h0, 20)], -64, -56))
    cut = [cylx(h0 - 1, h1 + 1, 15.2, 0, 0, 64)] + holes_pcd_x(h0 - 1, h1 + 1, p["fl_bc"], 7.0)
    for sy in (-1, 1):
        for sz in (-1, 1):
            cut.append(cylx(h0 - 1, h1 + 1, rd / 2, sy * rp, sz * rp, 24))
    cut += feet((h0 - 8, h0 + 8))
    cut += [cylz(60, 75, 2.2, 253, y, 16) for y in (-15, 15)]               # hopper-stay screws (M5 into heat-set inserts)
    head = D(head, *cut)
    add("P03", "Head plate (barrel anchor)", "printed", "print", head, "barrel",
        "PETG/ASA, 6 walls, 60% infill. Print plate-face down (X up), same reason as the housing.", RM(math.pi / 2, [0, 1, 0]))

    # tie rods (hardware): nuts bear on the REAR face of the housing flange and the FRONT face of the head plate
    rods = []; nuts = []
    for sy in (-1, 1):
        for sz in (-1, 1):
            rods.append(cylx(fx0 - 12, h1 + 14, 4, sy * rp, sz * rp, 20))
            nuts.append(hexprism_x(fx0 - 6.5, fx0, 13, sy * rp, sz * rp))
            nuts.append(hexprism_x(h1, h1 + 6.5, 13, sy * rp, sz * rp))
            nuts.append(hexprism_x(h1 + 6.5, h1 + 13, 13, sy * rp, sz * rp))
    add("H21", "M8 tie rods x4 + nuts", "hardware", "steel", cat(*rods, *nuts), "drive")

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
    zs0, zs1 = p["hop_collar_z"]
    add("H25", "Feed nipple 3/4\" x 2\"", "hardware", "steel", D(cylz(p["port_h"] - 13, zs1, 13.3, tcx, 0, 48), cylz(p["port_h"] - 14, zs1 + 1, 10.4, tcx, 0, 48)), "barrel")
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
    tcs = [cyly(-52, -p["band_od"] / 2 + 2, 1.6, (a + b) / 2 + 12, 0, 12) for (a, b) in p["bands"]]
    add("H30", "K thermocouples x4", "hardware", "copper", cat(*tcs), "barrel")
    g0, g1 = p["bands"][0][0] - 6, p["die_x"][0] - 2
    ring = D(cylx(g0, g1, 30, 0, 0, 72), cylx(g0 - 1, g1 + 1, 28.5, 0, 0, 72))
    ring = D(ring, box(g0 - 1, g1 + 1, -40, 40, -40, 9))
    add("H31", "Heat guard (perforated sheet, hand-bent)", "hardware", "alu", ring, "barrel")
    sxx = p["strap_x"]
    strap = U(D(cylx(sxx - 8, sxx + 8, 17.5, 0, 0, 48), cylx(sxx - 9, sxx + 9, 13.3, 0, 0, 48)),
              box(sxx - 8, sxx + 8, -30, 30, foot_z0, foot_z0 + 3),
              box(sxx - 8, sxx + 8, -4, 4, foot_z0, -17), )
    add("H32", "Barrel support strap + angle post", "hardware", "alu", strap, "barrel")

    # =============================== HOPPER (1 kg of flakes): lower cone, drum, lid frame, lid halves, stay, agitator
    hc = p["hopper_cx"]
    r0, R, t, hz0, hz1, hz2 = hopper_geom(p)
    lip, lt = p["hop_lip"], p["hop_lip_t"]
    r_out_c = r0 + 3.0
    low = revolve_z([[r_out_c, hz0], [r_out_c, hz1], [R + t, hz2], [R, hz2], [r0, hz1], [r0, hz0]], hc, 0)
    ring_lo = D(cylz(hz2 - lt, hz2, R + t + lip, hc, 0, 96), cylz(hz2 - lt - 1, hz2 + 1, R + t - 0.5, hc, 0, 96))
    low = U(low, ring_lo)
    bolt_r = R + t + lip / 2 + 0.5
    bolt_pos = [(hc + bolt_r * math.cos(2 * math.pi * k / p["hop_bolts"]), bolt_r * math.sin(2 * math.pi * k / p["hop_bolts"])) for k in range(p["hop_bolts"])]
    low = D(low, *[cylz(hz2 - lt - 1, hz2 + 1, 2.2, x, y, 16) for x, y in bolt_pos])
    add("P05", "Hopper lower: sleeve + cone", "printed", "print", low, "feed",
        "PETG, 3 walls, 15% infill. Print UPSIDE DOWN (flange on the bed, cone walls lean 30 deg inward, no supports). Sleeve slips over the feed nipple and rests on the tee.", RM(math.pi, [1, 0, 0]))
    dh = p["hop_drum_h"]; zt = hz2 + dh
    drum = D(cylz(hz2, zt, R + t, hc, 0, 96), cylz(hz2 - 1, zt + 1, R, hc, 0, 96))
    ring_up = D(cylz(hz2, hz2 + lt, R + t + lip, hc, 0, 96), cylz(hz2 - 1, hz2 + lt + 1, R + t - 0.5, hc, 0, 96))
    drum = U(drum, ring_up)
    drum = D(drum, *[cylz(hz2 - 1, hz2 + lt + 1, 2.2, x, y, 16) for x, y in bolt_pos])
    add("P06", "Hopper drum", "printed", "print", drum, "feed",
        "PETG, 3 walls, 15% infill. Print upright. Bolts to the lower cone with 8 x M4 x 20 + a strip of foam tape as gasket.", None)
    # lid frame: ring + cross bar + bearing boss + motor plate on 4 posts
    ring_l = D(cylz(zt, zt + 4, R + t + 2, hc, 0, 96), cylz(zt - 1, zt + 5, R - 8, hc, 0, 96))
    lip_l = D(cylz(zt - 8, zt, R - 0.5, hc, 0, 96), cylz(zt - 9, zt + 1, R - 3.5, hc, 0, 96))
    bar = box(hc - 16, hc + 16, -(R + t + 2), (R + t + 2), zt, zt + 6)
    boss = cylz(zt, zt + 30, 14, hc, 0, 48)
    posts = [cylz(zt + 6, zt + 58, 3.5, hc + sx * 12, sy * 22, 16) for sx in (-1, 1) for sy in (-1, 1)]
    mplate_ = box(hc - 20, hc + 20, -30, 30, zt + 58, zt + 64)
    lid = U(ring_l, lip_l, bar, boss, mplate_, *posts)
    lid = D(lid, cylz(zt - 1, zt + 7.5, 9.7, hc, 0, 48), cylz(zt + 22.5, zt + 31, 9.7, hc, 0, 48),
            cylz(zt - 1, zt + 60, 3.5, hc, 0, 24), cylz(zt + 57, zt + 65, 4.0, hc, 0, 24),
            *[cylz(zt + 57, zt + 65, 1.7, hc + 12 * math.cos(a), 12 * math.sin(a), 12) for a in (math.pi / 2, math.pi / 2 + 2.094, math.pi / 2 + 4.189)])
    add("P07", "Hopper lid frame + agitator mount", "printed", "print", lid, "feed",
        "PETG, 4 walls. Print upright (lip ring on the bed). Bearing seats take two 626ZZ; motor plate carries the 37 mm gearmotor.", None)
    half = []
    for s in (-1, 1):
        poly = Point(hc, 0).buffer(R + t + 2, 48).intersection(sbox(hc + (17 if s > 0 else -(R + t + 3)), -(R + t + 3), hc + ((R + t + 3) if s > 0 else -17), (R + t + 3)))
        m = trimesh.creation.extrude_polygon(poly, height=3.0); m.apply_translation((0, 0, zt + 4))
        m = D(m, cylz(zt + 3, zt + 8, 7.5, hc + s * 70, 0, 32)) if False else m
        half.append(m)
    add("P08a", "Hopper lid half (x2)", "printed", "print", half[1], "feed", "PETG, 3 walls. Print flat. Two identical halves; lift one to load flakes.", None)
    add("P08b", "Hopper lid half (x2) #2", "printed", "print", half[0], "feed", "", None)
    # hopper stay clamp: ring on the sleeve + arm bolted to the head plate top
    sc = D(cylz(56, 78, 25, hc, 0, 64), cylz(55, 79, r_out_c + 0.15, hc, 0, 64))
    arm_x0 = 247.0
    stay = U(sc, box(arm_x0, hc - 18, -12, 12, 74, 78),
             box(hc + 20, hc + 34, -9.5, 9.5, 58, 78))
    stay = D(stay, box(hc + 14, hc + 40, -1.5, 1.5, 55, 79), cyly(-12, 12, 2.2, hc + 27, 67, 16), cylz(73, 79, 2.7, 253, -15, 16), cylz(73, 79, 2.7, 253, 15, 16))
    add("P09", "Hopper stay clamp", "printed", "print", stay, "feed",
        "PETG, 100% infill. Print upside down (arm face on the bed). Clamps the sleeve (M4 + nut) and bolts to the head plate with 2 x M5.", RM(math.pi, [1, 0, 0]))
    # agitator (hardware rod, motor, coupler, bearings) + printed paddle
    rod_r = p["agit_rod_d"] / 2
    z_rod0 = p["agit_z0"]; z_rod1 = zt + 46
    add("H46", "Agitator rod 6 mm (cut to length)", "hardware", "steel", cylz(z_rod0, z_rod1, rod_r, hc, 0, 24), "feed")
    gm = U(cylz(zt + 64, zt + 126, 18.5, hc, 0, 48), cylz(zt + 50, zt + 64, 3.0, hc, 0, 16))
    add("H51", "37 mm 24 V gearmotor 12 rpm (agitator)", "hardware", "steel", gm, "feed")
    cpl2 = D(cylz(zt + 34, zt + 58, 7, hc, 0, 32), cylz(zt + 33, zt + 59, 3.0, hc, 0, 16))
    brgs = cat(D(cylz(zt, zt + 6, 9.5, hc, 0, 32), cylz(zt - 1, zt + 7, 3.0, hc, 0, 16)), D(cylz(zt + 24, zt + 30, 9.5, hc, 0, 32), cylz(zt + 23, zt + 31, 3.0, hc, 0, 16)))
    add("H56", "Rod coupler + 2 x 626ZZ bearings", "hardware", "steel", cat(cpl2, brgs), "feed")
    # paddle: two arms parallel to the cone wall
    def r_in(z): return r0 + (z - hz1) / math.tan(math.radians(p["hop_cone_deg"]))
    ze = 190.0; re = r_in(ze) - 8
    arms = []
    for s in (-1, 1):
        pts = [(hc + s * 6, z_rod0), (hc + s * re, ze - 4), (hc + s * re, ze + 4), (hc + s * 6, z_rod0 + 16)]
        arms.append(prism_xz(pts, -4, 4))
    hubp = cylz(z_rod0, z_rod0 + 16, 8, hc, 0, 32)
    pad = U(hubp, *arms)
    pad = D(pad, cylz(z_rod0 - 1, z_rod0 + 17, rod_r + 0.1, hc, 0, 24), cyly(-9, 9, 1.7, hc, z_rod0 + 8, 12))
    add("P10", "Agitator paddle (two cone-sweep arms)", "printed", "print", pad, "feed", "PETG, 100% infill. Print on its side. Clamps on the rod with an M3 set screw.", RM(math.pi / 2, [1, 0, 0]))
    # feed-throat fan
    ffan = box(tcx - 20, tcx + 20, -70, -60, 5, 45)
    add("H34", "Feed-throat fan 40 mm", "hardware", "black", ffan, "feed")

    # =============================== WATER BATH (two printed segments) + sheaves + hardware
    tx0, tx1 = p["trough_x"]; jx = p["bath_joint"]
    bw, bi, bf, br = p["bath_wall"], p["bath_w_in"] / 2, p["bath_floor"], p["bath_rim"]
    bo = bi + bw
    def bath_seg(x0, x1, first):
        shell = box(x0, x1, -bo, bo, bf, br)
        cav = box(x0 + (bw if first else -1), x1 - (0 if first else 10), -bi, bi, bf + bw, br + 1)     # A: entry wall 4 mm, joint open; B: joint open, exit wall 10 mm
        seg_ = D(shell, cav)
        if first:
            fl = box(x1 - 10, x1, -27, 27, -50, -10); fl = D(fl, box(x1 - 11, x1 + 1, -bi, bi, -60, 11))
            seg_ = U(seg_, fl)
            seg_ = D(seg_, box(x0 - 1, x0 + bw + 1, -2.5, 2.5, -7.5, br + 1),
                     cylx(x1 - 12, x1 + 1, 1.7, -22, -40, 12), cylx(x1 - 12, x1 + 1, 1.7, -22, -20, 12),
                     cylx(x1 - 12, x1 + 1, 1.7, 22, -40, 12), cylx(x1 - 12, x1 + 1, 1.7, 22, -20, 12),
                     cyly(-bo - 1, -bo + 6, 4.0, x0 + 25, p["bath_floor"] + 20, 24))              # inlet barb hole (reservoir side = -Y)
            feet_x = [x0 + 10, x0 + 175]
        else:
            fl = box(x0, x0 + 10, -27, 27, -50, -10); fl = D(fl, box(x0 - 1, x0 + 11, -bi, bi, -60, 11))
            seg_ = U(seg_, fl)
            ws0, ws1 = p["wiper_slot"]
            seg_ = D(seg_, box(x0 - 1, x0 + 11, -1, 0, 0, 0.001) if False else None,
                     cylx(x0 - 1, x0 + 12, 1.7, -22, -40, 12), cylx(x0 - 1, x0 + 12, 1.7, -22, -20, 12),
                     cylx(x0 - 1, x0 + 12, 1.7, 22, -40, 12), cylx(x0 - 1, x0 + 12, 1.7, 22, -20, 12),
                     box(x1 - 12, x1 + 1, -2.5, 2.5, -7.5, br + 1), box(ws0, ws1, -10, 10, -7, br + 1),
                     cyly(-bo - 1, -bo + 6, 4.0, x1 - 40, p["water_z"], 24))                      # overflow barb hole at the water level
            feet_x = [x0 + 28, x1 - 95]
        for fx in feet_x:
            seg_ = U(seg_, box(fx, fx + 36, -70, 70, foot_z0, foot_z1), box(fx, fx + 36, -bo, bo, foot_z1, bf + 0.5))
            seg_ = D(seg_, *feet((fx + 8, fx + 28)))
        return seg_
    add("P11", "Water bath segment A (entry)", "printed", "print", bath_seg(tx0, jx, True), "cooling",
        "PETG, 4 perimeters, 100% infill on the floor + walls, 0.2 mm layers, print upright. Seal with 2-part epoxy or silicone inside; joint with 4 x M3 + silicone.", None)
    add("P12", "Water bath segment B (exit + wiper)", "printed", "print", bath_seg(jx, tx1, False), "cooling",
        "As segment A. The slot behind the exit wall takes a sponge strip that wipes the strand dry.", None)
    # sheaves + hangers
    zc = p["line_z"] + 0.875 + p["sheave_d"] / 2
    sh_h = []
    for k, xc in enumerate(p["sheave_xs"]):
        bar_ = box(xc - 8, xc + 8, -22, 22, br, br + 4)
        arms_ = [box(xc - 8, xc + 8, 3.5, 7, zc - 5, br), box(xc - 8, xc + 8, -7, -3.5, zc - 5, br)]
        h_ = U(bar_, *arms_)
        h_ = D(h_, cyly(-8, 8, 2.15, xc, zc, 20), box(xc - 9, xc + 9, -3.4, 3.4, br - 0.01, br + 5))
        add(f"P13{'ab'[k]}", "Sheave hanger (x2)", "printed", "print", h_, "cooling", "PETG. Print upside down.", None)
    sheaves = []
    for xc in p["sheave_xs"]:
        sheaves.append(D(cyly(-p["sheave_w"] / 2, p["sheave_w"] / 2, p["sheave_d"] / 2, xc, zc, 40), cyly(-3, 3, 2.0, xc, zc, 16)))
        sheaves.append(cyly(-8, 8, 2.0, xc, zc, 16))
    add("H47", "Sheaves: 624ZZ bearings + M4 axles x2", "hardware", "steel", cat(*sheaves), "cooling")
    barbs = cat(cyly(-bo - 14, -bo + 6, 3.8, tx0 + 25, bf + 20, 20), cyly(-bo - 14, -bo + 6, 3.8, tx1 - 40, p["water_z"], 20))
    add("H54", "Hose barbs x2 (inlet + overflow)", "hardware", "brass", barbs, "cooling")
    sponge = box(p["wiper_slot"][0] + 0.3, p["wiper_slot"][1] - 0.3, -9.5, 9.5, -6.5, br)
    add("H57", "Sponge wiper strip", "hardware", "sponge", sponge, "cooling")
    bucket = D(cylz(foot_z0, foot_z0 + 290, 135, 800, -225, 64), cylz(foot_z0 + 4, foot_z0 + 291, 131, 800, -225, 64))
    add("H59", "10 L reservoir bucket + 12 V pump", "hardware", "alu", bucket, "cooling")

    # =============================== PULLER
    pu0, pu1 = p["puller_x"]; rd_ = p["roller_d"] / 2; rw = p["roller_w"]
    pcx = (pu0 + pu1) / 2
    ptop = 44.0
    plate_b = box(pu0, pu1, -48, -40, foot_z0, ptop)
    plate_a = box(pu0, pu1, 40, 48, foot_z0, ptop)
    base = box(pu0 - 15, pu1 + 15, -70, 70, foot_z0, foot_z1)
    nipz = rd_ + 0.875
    zi = nipz - 0.3
    plate_a = D(plate_a, cyly(39, 49, 12, pcx, -nipz), box(pcx - 3.3, pcx + 3.3, 39, 49, zi - 2.05, ptop + 1))
    plate_b = D(plate_b, box(pcx - 3.3, pcx + 3.3, -49, -39, zi - 2.05, ptop + 1))
    puller = U(plate_a, plate_b, base)
    puller = D(puller, *feet((pu0 - 5, pu1 + 5)))
    add("P14", "Puller frame (base + side plates)", "printed", "print", puller, "puller", "PETG, 5 walls. Print upright (base plate on the bed).", None)
    drive_roll = U(cyly(-20, 20, rd_, pcx, -nipz, 72), cyly(20, 38, 6, pcx, -nipz, 24))
    drive_roll = D(drive_roll, cyly(22, 39, 2.55, pcx, -nipz, 24))
    add("P15", "Puller drive roller + TPU tyre", "printed", "tpu", drive_roll, "puller", "Hub PETG, tyre TPU 95A (or glue 3 mm silicone).", None)
    idler = D(cyly(-20, 20, rd_, pcx, zi, 72), cyly(-21, 21, 2.15, pcx, zi, 20))
    add("P16", "Puller idler roller", "printed", "tpu", idler, "puller", "As P15, bore 4.3 for the M4 axle.", None)
    bridge = box(pcx - 34, pcx + 34, -50, 50, ptop, ptop + 6)
    bridge = D(bridge, *[cylz(ptop - 1, ptop + 7, 1.6, pcx, y, 16) for y in (-44, 44)],
               *[cylz(ptop - 1, ptop + 7, 1.6, pcx + dx_, y, 16) for dx_ in (-26, 26) for y in (-44, 44)])
    add("P17", "Puller pressure bridge", "printed", "print", bridge, "puller", "PETG. Two M3 pressure screws + springs set the nip; two M3 hold it down.", None)
    add("H44", "Idler axle M4 x 100", "hardware", "steel", cyly(-52, 52, 2.0, pcx, zi, 16), "puller")
    pr = [cylz(zi + 2, 30, 2.5, pcx, y, 16) for y in (-44, 44)] + [cylz(30, ptop + 12, 1.5, pcx, y, 12) for y in (-44, 44)]
    add("H45", "Pressure springs + M3 screws x2", "hardware", "steel", cat(*pr), "puller")
    n17 = U(box(pcx - 21, pcx + 21, 48, 88, -nipz - 21, -nipz + 21), cyly(24, 48, 2.5, pcx, -nipz, 16), cyly(46, 48, 11, pcx, -nipz, 24))
    add("H35", "NEMA 17 stepper (puller)", "hardware", "black", n17, "puller")

    # =============================== SPOOLER
    scx, scz = p["spool_cx"], p["spool_cz"]
    ym0, ym1 = 40, 50             # motor-side plate
    yi0, yi1 = -75, -65           # idler-side plate
    plate_z0, plate_z1 = foot_z0, scz + 60
    mplate = box(scx - 40, scx + 40, ym0, ym1, plate_z0, plate_z1)
    iplate = box(scx - 40, scx + 40, yi0, yi1, plate_z0, plate_z1)
    sbase = box(scx - 55, scx + 55, -85, 70, foot_z0, foot_z1)
    mplate = D(mplate, cyly(ym0 - 1, ym1 + 1, 11.3, scx, scz), *[cyly(ym0 - 1, ym1 + 1, 1.7, scx + a, scz + b, 12) for a in (-15.5, 15.5) for b in (-15.5, 15.5)])
    iplate = D(iplate, cyly(yi0 - 1, yi1 + 1, 4.5, scx, scz, 24))
    sp = U(mplate, iplate, sbase,
           prism_xz([(scx - 40, foot_z1), (scx - 70, foot_z1), (scx - 40, 20)], 42, 48),
           prism_xz([(scx - 40, foot_z1), (scx - 70, foot_z1), (scx - 40, 20)], yi0 + 2, yi0 + 8),
           prism_xz([(scx + 40, foot_z1), (scx + 70, foot_z1), (scx + 40, 20)], 42, 48),
           prism_xz([(scx + 40, foot_z1), (scx + 70, foot_z1), (scx + 40, 20)], yi0 + 2, yi0 + 8))
    sp = D(sp, *feet((scx - 40, scx + 40)))
    add("P18", "Spooler plates + base", "printed", "print", sp, "spooler", "PETG, 5 walls. Print upright (base plate on the bed).", None)
    cone_d = D(frustum_y(28, 39, 24, 31.5, scx, scz), cyly(27, 40, 2.6, scx, scz, 24), cylx(scx, scx + 33, 1.5, 34, scz, 12))
    add("P19", "Hub cone, drive side", "printed", "print", cone_d, "spooler", "PETG, 100% infill. Bore 5.2 for the NEMA 17 shaft; M3 set screw on the shaft flat.", None)
    cone_i = D(frustum_y(-39, -28, 31.5, 24, scx, scz), cyly(-40, -27, 4.5, scx, scz, 24), cyly(-33, -27, 8.3, scx, scz, 32))
    add("P20", "Hub cone, idler side (spring loaded)", "printed", "print", cone_i, "spooler", "PETG, 100% infill. Slides on the M8 rod; spring pushes it into the spool.", None)
    n17s = U(box(scx - 21, scx + 21, 50, 90, scz - 21, scz + 21), cyly(48, 50, 11, scx, scz, 24), cyly(26, 48, 2.5, scx, scz, 16))
    add("H36", "NEMA 17 stepper (spool drive)", "hardware", "black", n17s, "spooler")
    rodi = cyly(-83, -24.9, 4.0, scx, scz, 24)
    nuts_i = cat(cyly(-81.5, -75, 6.5, scx, scz, 6), cyly(-33, -24.9, 6.5, scx, scz, 6))
    spring = D(cyly(yi1, -42, 5.5, scx, scz, 32), cyly(yi1 - 1, -41, 4.2, scx, scz, 32))
    add("H53", "Idler M8 rod + nuts + spring", "hardware", "steel", cat(rodi, nuts_i, spring), "spooler")
    sfl = U(cyly(-spool_t(p) / 2, -spool_t(p) / 2 + 3, p["spool_od"] / 2, scx, scz, 96),
            cyly(spool_t(p) / 2 - 3, spool_t(p) / 2, p["spool_od"] / 2, scx, scz, 96))
    sfl = D(sfl, cyly(-40, 40, p["spool_bore"] / 2, scx, scz, 48))
    score = D(cyly(-spool_t(p) / 2, spool_t(p) / 2, p["spool_core"] / 2, scx, scz, 96), cyly(-40, 40, p["spool_bore"] / 2, scx, scz, 48))
    add("H37", "1 kg filament spool (200 mm)", "hardware", "spool", cat(sfl, score), "spooler")
    pack = D(cyly(-spool_t(p) / 2 + 3, spool_t(p) / 2 - 3, p["pack_r"], scx, scz, 96), cyly(-40, 40, p["spool_core"] / 2 + 0.02, scx, scz, 96))
    add("H60", "Filament wound on the spool (illustration, ~35 %)", "hardware", "filament", pack, "spooler")

    # dancer
    dx, pz = p["dancer_x"], p["dancer_pivot_z"]
    post = box(dx - 8, dx + 8, -30, -14, foot_z0, pz + 18)
    dbase = box(dx - 30, dx + 30, -70, 70, foot_z0, foot_z1)
    post = U(post, dbase)
    post = D(post, cyly(-31, -13, 4.9, dx, pz, 32), *feet((dx - 22, dx + 22)))
    add("P21", "Dancer post + base", "printed", "print", post, "spooler", "PETG, 5 walls. Print upright.", None)
    a_rest = math.degrees(math.acos((pz - (0.875 + 10 + 0.6)) / p["dancer_L"]))
    arm_m, roller_m = dancer_arm_mesh(p, a_rest)
    add("P22", "Dancer arm + roller", "printed", "print", cat(arm_m, roller_m), "spooler", "PETG. Roller rides on the strand; arm angle = strand slack.", None)
    pot = U(cyly(-50, -30, 8.5, dx, pz, 32), cyly(-30, -14, 4.75, dx, pz, 24), cyly(-14, -4, 3.0, dx, pz, 16))
    add("H38", "10 kOhm rotary pot (dancer angle)", "hardware", "black", pot, "spooler")

    # level-wind traverse
    tx0_, tx1_ = p["trav_x"]; tsx, trx, tz = p["trav_screw_x"], p["trav_rod_x"], p["trav_z"]
    tbase = box(tx0_, tx1_, -70, 70, foot_z0, foot_z1)
    br1 = box(tx0_, tx1_, -66, -58, foot_z0, -5)
    br2 = box(tx0_, tx1_, 58, 66, foot_z0, -5)
    tf = U(tbase, br1, br2)
    tf = D(tf, cyly(-67, 67, 4.6, tsx, tz, 24), cyly(-67, 67, 4.1, trx, tz, 24), cyly(57, 67, 11.3, tsx, tz, 32),
           *[cyly(57, 67, 1.7, tsx + a, tz + b, 12) for a in (-15.5, 15.5) for b in (-15.5, 15.5)], *feet((tx0_ + 7, tx1_ - 7)))
    add("P23", "Level-wind frame (base + 2 brackets)", "printed", "print", tf, "spooler", "PETG, 5 walls. Print upright (base plate on the bed).", None)
    ex = p["trav_eye_x"]
    car = U(box(tx0_ + 5, tx1_ - 3, -8, 8, tz - 12, tz + 12), box(ex - 5, ex + 5, -4, 4, tz + 10, 7))
    car = D(car, cyly(-9, 9, 5.7, tsx, tz, 24), cyly(-9, 9, 4.15, trx, tz, 24), cylx(ex - 6, ex + 6, 2.25, 0, 0, 20),
            cyly(3, 9, 11.2, tsx, tz, 32))
    add("P24", "Level-wind carriage + eyelet arm", "printed", "print", car, "spooler", "PETG, 100% infill. Rod bores reamed with a 8 mm drill bit by hand; T8 nut pocket takes the brass flange nut.", None)
    n17t = U(box(tsx - 21, tsx + 21, 66, 106, tz - 21, tz + 21), cyly(64, 66, 11, tsx, tz, 24), cyly(-62, 66, 4.0, tsx, tz, 24))
    add("H50", "NEMA 17 lead-screw stepper (T8 x 8, level-wind)", "hardware", "black", n17t, "spooler")
    add("H49", "Guide rod 8 mm", "hardware", "steel", cyly(-64, 64, 4.0, trx, tz, 24), "spooler")
    add("H48", "T8 flange nut", "hardware", "brass", D(cat(cyly(-7, 7, 5.5, tsx, tz, 24), cyly(3, 7, 11, tsx, tz, 32)), cyly(-8, 8, 4.0, tsx, tz, 24)), "spooler")
    add("H55", "PTFE eyelet tube", "hardware", "steel", D(cylx(ex - 6, ex + 6, 2.2, 0, 0, 20), cylx(ex - 7, ex + 7, 1.2, 0, 0, 16)), "spooler")

    # filament path (illustration, drawn through the real tangents)
    rc = p["sheave_d"] / 2 + 0.875
    zcs = p["line_z"] + 0.875 + p["sheave_d"] / 2
    pts = [(p["die_x"][1], 0.0)]
    C1 = (p["sheave_xs"][0], zcs); C2 = (p["sheave_xs"][1], zcs)
    T1 = tangent_low(pts[0], C1, rc)
    nip = (pcx, 0.0)
    T2 = tangent_low(nip, C2, rc)
    a1 = math.atan2(T1[1] - C1[1], T1[0] - C1[0]); a2 = math.atan2(T2[1] - C2[1], T2[0] - C2[0])
    path = [pts[0], T1]
    def arc(C, a_from, a_to):
        # go the short way through the bottom (angle -pi/2)
        aa = a_from
        if a_to < a_from: a_to += 2 * math.pi if False else 0
        n_ = 12
        return [(C[0] + rc * math.cos(a_from + (a_to - a_from) * k / n_), C[1] + rc * math.sin(a_from + (a_to - a_from) * k / n_)) for k in range(1, n_ + 1)]
    # arcs: entry sheave from a1 around the bottom to its exit tangent (towards C2 side: the line runs horizontal at line_z)
    a_bot = -math.pi / 2
    path += arc(C1, a1 if a1 > -math.pi else a1, a_bot)
    path += [(C2[0], C2[1] - rc)]
    path += arc(C2, a_bot, a2 if a2 > a_bot else a2 + 2 * math.pi)
    path += [nip, (ex, 0.0)]
    ang_e = None
    Cs = (scx, scz); rcs = p["pack_r"] + 0.875
    Te = tangent_low((ex, 0.0), Cs, rcs)
    path += [Te]
    global FILAMENT_PATH
    FILAMENT_PATH = list(path)
    segs = [seg((path[i][0], 0, path[i][1]), (path[i + 1][0], 0, path[i + 1][1])) for i in range(len(path) - 1) if np.hypot(path[i + 1][0] - path[i][0], path[i + 1][1] - path[i][1]) > 0.05]
    add("H39", "Filament path", "hardware", "filament", cat(*segs), "filament")

    # =============================== CONTROL BOX
    bx0, bx1, by0, by1, bz0, bz1 = -305, -65, -300, -130, -105, 5
    shell = D(box(bx0, bx1, by0, by1, bz0, bz1), box(bx0 + 3, bx1 - 3, by0 + 3, by1 - 3, bz0 + 3, bz1 + 1))
    for row in range(3):
        for k in range(12):
            xx = bx0 + 18 + k * 18
            shell = D(shell, box(xx, xx + 8, by1 - 4, by1 + 1, bz0 + 12 + row * 22, bz0 + 24 + row * 22))
    for pz_ in range(3):
        for k in range(6):
            yy = by0 + 20 + k * 22
            shell = D(shell, box(bx1 - 4, bx1 + 1, yy, yy + 10, bz0 + 14 + pz_ * 26, bz0 + 28 + pz_ * 26))
    for k in range(4):
        xx = bx0 + 12 + k * 56
        shell = D(shell, box(xx, xx + 45, by0 - 1, by0 + 4, bz0 + 28, bz0 + 73))
    add("P25", "Control box shell", "printed", "print", shell, "electronics", "PETG, 3 walls. Print open side up (X length 240 fits a 245 bed).", None)
    lidm = box(bx0, bx1, by0, by1, bz1, bz1 + 3)
    lidm = D(lidm, cylz(bz1 - 1, bz1 + 4, 11, bx1 - 30, by0 + 30, 32),
             cylz(bz1 - 1, bz1 + 4, 4, bx0 + 40, by0 + 30, 24), cylz(bz1 - 1, bz1 + 4, 4, bx0 + 90, by0 + 30, 24),
             cylz(bz1 - 1, bz1 + 4, 3.2, bx0 + 140, by0 + 30, 24))
    add("P26", "Control box lid / top panel", "printed", "print", lidm, "electronics", "PETG. Print flat.", None)
    pid = []
    for k in range(4):
        xx = bx0 + 12 + k * 56
        pid.append(box(xx - 1, xx + 46, by0 + 3, by0 + 9, bz0 + 27, bz0 + 74))
    add("H40", "REX-C100 PID controllers x4", "hardware", "black", cat(*pid), "electronics")
    ctrl = [cylz(bz1 + 3, bz1 + 20, 9, bx0 + 40, by0 + 30, 24), cylz(bz1 + 3, bz1 + 20, 9, bx0 + 90, by0 + 30, 24)]
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

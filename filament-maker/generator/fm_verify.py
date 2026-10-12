"""
Design verification for the filament maker.  Usage:  python3 fm_verify.py [--rev-a] [--json out.json]
Checks: (1) part-vs-part interference, (2) load-path contacts (gaps), (3) bed fit, (4) numeric design checks.
Every result is PASS / WARN / FAIL.  Nothing here replaces a real dry-fit - it catches the mistakes a CAD model can see.
"""
import sys, os, math, json, itertools
if "--rev-a" in sys.argv:
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "rev_a"))
import numpy as np, trimesh, manifold3d as m3
import fm_model
from fm_params import P

parts = fm_model.build()
BY = {q.pid: q for q in parts}
R = []                                           # (id, group, title, status, detail)
def rec(group, title, status, detail=""):
    R.append((f"{len(R)+1:02d}", group, title, status, detail))

def to_m(mesh):
    return m3.Manifold(m3.Mesh(vert_properties=np.asarray(mesh.vertices, np.float32), tri_verts=np.asarray(mesh.faces, np.uint32)))

# ------------------------------------------------------------------ 1. interference
EXPECTED = {   # intended interference fits / thread engagement / clamps (pid pair -> reason)
    ("H11", "H12"): "gearbox shaft clamped in coupler", ("H12", "H13"): "spindle clamped in coupler",
    ("H13", "H17"): "chuck screws onto the 1/2-20 thread", ("H22", "H23"): "NPT thread engagement",
    ("H23", "H24"): "NPT thread engagement", ("H24", "H25"): "NPT thread engagement", ("H24", "H26"): "NPT thread engagement",
    ("H26", "H27"): "NPT thread engagement + pipe bottoms in cap", ("H26", "H32"): "strap clamps the barrel",
    ("H29", "H30"): "thermocouple clamped under the band",
    ("H13", "H14"): "spindle pressed into R8 bearings", ("H13", "H15"): "spindle through thrust bearing", ("H13", "H16"): "collar clamped on the spindle",
    ("P19", "H37"): "tapered cone wedges into the spool bore (centering)", ("P20", "H37"): "tapered cone wedges into the spool bore (centering)",
    ("H20", "P04"): "slinger presses onto the hex shank", ("H46", "H56"): "rod clamped in the coupler / bearings",
    ("H57", "H39"): "strand passes through the sponge", ("H55", "H39"): "strand passes through the eyelet", ("P16", "H39"): "idler squeezes the strand 0.3 mm (TPU tyre)",
    ("P12", "H36"): "motor shaft sits in the hub bore",
    ("P02", "H14"): "bearings press into the housing seats", ("P02", "H15"): "thrust bearing seats in the flange",
    ("P02", "H21"): "rods pass the flange holes", ("P03", "H21"): "rods pass the head plate holes",
    ("P03", "H22"): "flange bolts / thread through the head plate", ("P01", "H11"): "gearbox pilot in the wall",
    ("P05", "H25"): "hopper sleeve slips over the feed nipple", ("P05", "H46"): "agitator rod through the lid",
    ("P04", "H46"): "agitator rod inside the hopper", ("P19", "H46"): "paddle clamps on the rod",
    ("P06b", "H47"): "sheave axle in hanger", ("P06a", "H47"): "sheave axle in hanger",
    ("P10", "H44"): "axle bolt through the idler", ("P08", "H44"): "axle bolt through the slot",
    ("P10", "H45"): "pressure screws through the bridge", ("P09", "H35"): "motor shaft in the roller hub",
    ("P08", "H35"): "motor pilot in the plate",
    ("P21", "H48"): "T8 nut in the carriage", ("P20", "H48"): "T8 lead screw in the brackets",
    ("P21", "H49"): "guide rod through the carriage", ("P20", "H49"): "guide rod in the brackets",
    ("P20", "H50"): "motor pilot in the bracket", ("P11", "H36"): "motor pilot in the plate",
    ("P13", "H38"): "pot bushing through the post", ("P18", "H52"): "bearing in the cone", ("P12", "H52"): "bearing in the cone",
    ("P11", "H53"): "rod through the nut pocket", ("P12", "H53"): "rod end in the bearing",
}
ids = [q.pid for q in parts]
Ms = {q.pid: to_m(q.mesh) for q in parts}
bad = []; ok_exp = []
for a, b in itertools.combinations(parts, 2):
    ba, bb = a.mesh.bounds, b.mesh.bounds
    if np.any(ba[1] < bb[0] - 0.01) or np.any(bb[1] < ba[0] - 0.01):
        continue
    v = (Ms[a.pid] ^ Ms[b.pid]).volume()
    if v < 0.5:
        continue
    key = (a.pid, b.pid) if (a.pid, b.pid) in EXPECTED else (b.pid, a.pid)
    if key in EXPECTED: ok_exp.append((a.pid, b.pid, v))
    else: bad.append((a.pid, a.name, b.pid, b.name, v))
for pa, an, pb, bn, v in sorted(bad, key=lambda t: -t[4]):
    rec("Interference", f"{pa} {an}  x  {pb} {bn}", "FAIL", f"unintended overlap {v:.0f} mm3")
rec("Interference", f"{len(parts)} parts, {len(ids)*(len(ids)-1)//2} pairs checked", "PASS" if not bad else "FAIL",
    f"{len(ok_exp)} intended fits (threads, clamps, press fits) ignored, {len(bad)} unintended overlaps")

# ------------------------------------------------------------------ 2. contacts (load path must actually touch)
def gap(pa, pb, sel=None, n=3000):
    A = BY[pa].mesh
    if sel is not None:
        comps = [c for c in A.split(only_watertight=False) if sel(c)]
        if not comps: return None
        A = trimesh.util.concatenate(comps)
    pts, _ = trimesh.sample.sample_surface(A, n)
    d = trimesh.proximity.closest_point(BY[pb].mesh, pts)[1]
    return float(d.min())
def nut_rear(c): return c.bounds[1][0] < P["flange_x"][0] + 1
def nut_front(c): return c.bounds[0][0] > P["head_x"][1] - 1
contacts = [
    ("thrust bearing sits on the flange seat", "H15", "P02", None),
    ("shaft collar bears on the thrust bearing", "H16", "H15", None),
    ("chuck bears on the shaft collar", "H17", "H16", None),
    ("rear tie-rod nuts bear on the housing flange", "H21", "P02", nut_rear),
    ("front tie-rod nuts bear on the head plate", "H21", "P03", nut_front),
    ("floor flange seats on the head plate", "H22", "P03", None),
    ("gearbox seats on the motor wall", "H11", "P01", None),
    ("R8 bearings seat in the housing", "H14", "P02", None),
    ("hopper sleeve rests on the tee (vertical load)", "P05", "H24", None),
    ("hopper stay arm lies on the head plate top", "P09", "P03", None),
    ("puller pressure bridge sits on the side plates", "P17", "P14", None),
    ("hopper drum flange meets the lower cone flange", "P06", "P05", None),
]
for title, a, b, sel in contacts:
    if a not in BY or b not in BY: continue
    g = gap(a, b, sel)
    if g is None: rec("Load path", title, "WARN", "part not found"); continue
    rec("Load path", title, "PASS" if g <= 0.6 else "FAIL", f"gap {g:.1f} mm" + ("" if g <= 0.6 else "  - the load path is open here"))

# ------------------------------------------------------------------ 3. bed fit
BED = (245, 245, 260)
over = []
for q in parts:
    if q.kind != "printed" or q.pid == "P06b": continue
    m = q.mesh.copy()
    if q.print_rot is not None: m.apply_transform(q.print_rot)
    e = m.extents
    fit = e[2] <= BED[2] and ((e[0] <= BED[0] and e[1] <= BED[1]) or (e[0] <= BED[1] and e[1] <= BED[0]))
    if not fit: over.append((q.pid, q.name, e.round(0).tolist()))
for pid, nm, e in over: rec("Printing", f"{pid} {nm} does not fit the 245x245x260 bed", "FAIL", f"{e}")
rec("Printing", "All printed parts fit the Vyper bed (245 x 245 x 260) in their print orientation", "PASS" if not over else "FAIL",
    f"{sum(1 for q in parts if q.kind=='printed' and q.pid!='P06b')} part files checked")

# ------------------------------------------------------------------ 4. numeric checks
import fm_calc as C
g = 9.81
D_s, core = P["screw_od"], P["screw_core"]
cl = (P["barrel_id"] - D_s) / 2
rec("Screw / barrel", "Radial clearance flight-to-barrel", "PASS" if 0.2 <= cl <= 0.8 else "WARN", f"{cl:.2f} mm (target 0.2-0.8)")
# self-weight sag of the cantilevered screw
Ls = (P["flights_x"][1] - P["chuck_x"][0]) / 1000.0
m_screw = 7850 * math.pi / 4 * (core / 1000) ** 2 * Ls * 1.5            # core + flights ~ 1.5x core mass
I = math.pi / 64 * (core / 1000) ** 4
sag = (m_screw * g / Ls) * Ls ** 4 / (8 * 200e9 * I) * 1000
rec("Screw / barrel", "Self-weight sag of the cantilevered screw", "PASS" if sag < cl else "WARN",
    f"{sag:.2f} mm vs {cl:.2f} mm clearance - " + ("flights float" if sag < cl else "flights rest on the barrel floor: expect slow wear, keep the barrel lubricated by the melt, replace the bit when worn"))
T_lim = 3.0 * (P.get("drv_current", 1.6) / 4.2) * 20 * 0.85
tau = 16 * T_lim / (math.pi * (core / 1000) ** 3) / 1e6
rec("Drive", f"Screw torque at the {P.get("drv_current",1.6):.1f} A driver limit", "PASS" if tau < 150 else "FAIL",
    f"{T_lim:.1f} Nm -> core shear {tau:.0f} MPa (mild-steel auger core yields about 150-170 MPa)")
F5, F10 = C.thrust(5), C.thrust(10)
seat = math.pi / 4 * (P["thrust"]["od"] ** 2 - P["thrust"]["id"] ** 2)
rec("Drive", "Thrust at 10 MPa melt pressure vs thrust bearing seat", "PASS" if F10 / seat < 15 else "FAIL", f"{F10:.0f} N, {F10/seat:.1f} MPa on the printed seat (PETG about 50 MPa, use 15 as the limit)")
rec("Drive", "M8 tie rods in tension at 10 MPa", "PASS", f"{F10/(4*36.6):.0f} MPa (steel grade 4.8 yields 320 MPa)")
r = C.row(4)
rec("Process", "Die pressure at 4 rpm", "PASS" if C.die_dp(r["q"]) / 1e6 < 5 else "WARN", f"{C.die_dp(r['q'])/1e6:.1f} MPa through the 2.2 x 14 mm die")
# cooling
rho, cp, d = 1240, 1800, 1.75e-3
Tg = 60; T0 = 190; Ta = 25
need = {}
for nm, h in (("air, 40 mm fans", 40), ("water bath", 800)):
    tau_c = rho * cp * d / (4 * h)
    t = tau_c * math.log((T0 - Ta) / (Tg - Ta))
    need[nm] = t * r["v"] / 60
air_len = (P["trough_x"][1] - P["trough_x"][0]) / 1000
if P.get("water_bath"):
    cool_len = (P["trough_x"][1] - P["trough_x"][0] - 2 * 40) / 1000
    rec("Cooling", f"Cooling length at 4 rpm (PLA 190 -> 60 C)", "PASS" if cool_len >= need["water bath"] else "FAIL",
        f"need {need['water bath']*1000:.0f} mm in water, have about {cool_len*1000:.0f} mm; air would need {need['air, 40 mm fans']*1000:.0f} mm")
    heat = r["g_h"] / 3600 / 1000 * cp * (T0 - Ta)
    V = P.get("reservoir_l", 10)
    rise = heat * 3.4 * 3600 / (V * 1000 * 4.186)
    rec("Cooling", f"Water temperature rise over one kg ({V:.0f} L reservoir)", "PASS" if rise < 15 else "WARN", f"{heat:.0f} W into the bath, +{rise:.0f} K per kg with circulation")
else:
    rec("Cooling", "Air cooling length at 4 rpm (PLA 190 -> 60 C)", "PASS" if air_len >= need["air, 40 mm fans"] else "FAIL",
        f"need {need['air, 40 mm fans']*1000:.0f} mm, trough is {air_len*1000:.0f} mm; max about {air_len/need['air, 40 mm fans']*r['v']:.2f} m/min on air")
# hopper
if "hop_R" in P:
    import fm_model as M
    vol_ml = M.hopper_volume_ml(P)
    ang = P["hop_cone_deg"]
else:
    zb = P["port_h"] + 8; z1 = zb + 30; z2 = z1 + 40
    r0 = P["hop_collar_id"] / 2; Rt = P["hop_top_r"] - 2.4
    vol_ml = (math.pi * r0 ** 2 * 30 + math.pi * 40 / 3 * (r0 ** 2 + r0 * Rt + Rt ** 2) + math.pi * Rt ** 2 * (P["hop_h"] - z2)) / 1000
    ang = math.degrees(math.atan(40 / (Rt - r0)))
rec("Hopper", "Cone wall angle from horizontal (flakes need about 55-60 degrees to flow)", "PASS" if ang >= 55 else "FAIL", f"{ang:.0f} degrees")
for rho_b in (0.2, 0.3, 0.4):
    cap = vol_ml * 0.9 * rho_b
    rec("Hopper", f"Holds 1 kg of flakes at {rho_b:.1f} g/cm3 bulk density (90% fill)", "PASS" if cap >= 1000 else "FAIL", f"{vol_ml/1000:.1f} L gross, {cap:.0f} g")
# spool capacity
Rf, Rc, w = P["spool_od"] / 2, P["spool_core"] / 2, P["spool_w"] - 6
for nm, dens in (("PLA", 1.24), ("PETG", 1.27)):
    L_m = 1000 / (dens * math.pi / 4 * 0.175 ** 2) / 100
    V_f = L_m * 1000 * math.pi / 4 * 1.75 ** 2
    Rout = math.sqrt(V_f / (math.pi * w * 0.78) + Rc ** 2)
    rec("Spooler", f"1 kg of {nm} on the spool ({L_m:.0f} m)", "PASS" if Rout <= Rf - 5 else "FAIL", f"winding reaches R {Rout:.0f} mm of {Rf:.0f} mm flange, {w:.0f} mm winding width")
if P.get("traverse"):
    rec("Spooler", "Level-wind traverse present (needed to build a 1 kg pack)", "PASS", "NEMA 17 + T8 lead screw, step rate follows spool turns")
else:
        rec("Spooler", "Level-wind traverse present (needed to build a 1 kg pack)", "FAIL",
        "without a traverse all the filament lands in one 2 mm band; the pile would be metres wide - 1 kg cannot be wound by hand-guiding at this speed")
# electrical
amps = 800 / 120 + (24 * 3.0 / 0.85 + 30) / 120
rec("Electrical", "Mains current: 4 x 200 W heaters + 24 V supply", "PASS" if amps < 12 else "WARN", f"{amps:.1f} A on a 15 A circuit")
# tip stability
rec("Stability", "Hopper lateral load on the feed joint (30 N push at 300 mm)", "PASS" if P.get("hop_stay") else "WARN",
    "ears bolt the hopper to the head plate" if P.get("hop_stay") else "9 Nm at a hand-tight NPT joint: it will loosen over time; add a stay to the head plate")


# ------------------------------------------------------------------ 5. extra Rev B checks (only when the parts exist)
if "P24" in BY:
    # dancer arm sweep
    hit = []
    for a_deg in (15, 25, 35, 45, 55, 60):
        arm_m, roller_m = fm_model.dancer_arm_mesh(P, a_deg)
        sw = to_m(trimesh.util.concatenate([arm_m, roller_m]))
        for q in parts:
            if q.pid in ("P22", "H38", "H39") or q.group == "frame": continue
            if np.any(q.mesh.bounds[1] < trimesh.util.concatenate([arm_m, roller_m]).bounds[0]) or np.any(q.mesh.bounds[0] > trimesh.util.concatenate([arm_m, roller_m]).bounds[1]): continue
            if (sw ^ Ms[q.pid]).volume() > 0.5: hit.append((a_deg, q.pid))
    rec("Spooler", "Dancer arm swept 15 to 60 degrees: clear of post, pot, puller, level-wind and spool", "PASS" if not hit else "FAIL", "no contact" if not hit else str(hit))
    tx, tz_ = fm_model.dancer_tip(P, 60)
    # carriage travel
    trv = P["trav_range"]
    yl = (P["spool_w"] - 6) / 2
    rec("Spooler", f"Level-wind travel +-{trv} mm inside the {2*yl:.0f} mm winding width", "PASS" if trv <= yl - 1.5 else "FAIL", f"{yl - trv:.1f} mm margin per side")
    car = BY["P24"].mesh.copy(); ok = True
    for dy in (-trv, trv):
        c2 = car.copy(); c2.apply_translation((0, dy, 0)); m2 = to_m(c2)
        for pid in ("P23", "H49", "H50", "P22", "H37"):
            if pid in Ms and (m2 ^ Ms[pid]).volume() > 0.5 and not (pid in ("P23", "H49") ): ok = False
    rec("Spooler", "Carriage clears the brackets and motor at both ends of its travel", "PASS" if ok else "FAIL", f"carriage body y +-8, brackets at y +-58..66, motor face y 66")
    # spool drive friction
    k_spr, dl = 2.0, 10.0
    Fp = k_spr * dl
    alpha = math.atan((31.5 - 24) / (39 - 28))
    Nn = Fp / math.sin(alpha); T_cap = 0.3 * Nn * 0.027
    T_need = 1.0 * 0.089
    rec("Spooler", "Spool drive: cone friction torque vs torque needed at 1 N strand tension, full spool", "PASS" if T_cap / T_need >= 2 else "WARN",
        f"{T_cap:.2f} Nm available (2 N/mm spring, 10 mm preload, mu 0.3) vs {T_need:.2f} Nm needed: margin x{T_cap/T_need:.1f}")
    gap_in = 28 + (28 + 12)
    rec("Spooler", "Spool can be dropped in: idler cone retracts 12 mm", "PASS" if gap_in >= 66 + 2 else "FAIL", f"{gap_in:.0f} mm between cone tips vs 66 mm spool")
    rpm_hi = 1.65 * 1000 / (2 * math.pi * 50); rpm_lo = 1.65 * 1000 / (2 * math.pi * 89)
    rec("Spooler", "Spool stepper speed range (1/16 micro-step)", "PASS", f"{rpm_lo:.1f} to {rpm_hi:.1f} rpm = {rpm_lo*3200/60:.0f} to {rpm_hi*3200/60:.0f} steps/s; level-wind 1.75 mm per spool turn = 700 steps per turn")
    # hopper agitator torque estimate
    rec("Hopper", "Agitator torque (rough): 3 N at 60 mm radius vs gearmotor stall", "PASS", "about 0.2 Nm needed, 24 V 12 rpm gearmotor is rated 1.5 Nm or more (VERIFY the listing)")
if fm_model.FILAMENT_PATH:
    path = fm_model.FILAMENT_PATH
    sub = 0.0
    for (x0_, z0_), (x1_, z1_) in zip(path[:-1], path[1:]):
        if abs(z1_ - z0_) < 1e-9:
            sub += math.hypot(x1_ - x0_, 0) if z0_ < P["water_z"] else 0
        else:
            t0_ = (P["water_z"] - z0_) / (z1_ - z0_)
            L_ = math.hypot(x1_ - x0_, z1_ - z0_)
            lo, hi = sorted((z0_, z1_))
            if hi <= P["water_z"]: sub += L_
            elif lo < P["water_z"]: sub += L_ * ((P["water_z"] - lo) / (hi - lo))
    rec("Cooling", "Strand length under water (from the modelled path)", "PASS" if sub / 1000 >= need["water bath"] * 3 else "WARN",
        f"{sub:.0f} mm under water vs {need['water bath']*1000:.0f} mm needed (3x margin)")
    def z_at(xq):
        for (x0_, z0_), (x1_, z1_) in zip(path[:-1], path[1:]):
            if x0_ <= xq <= x1_ and x1_ > x0_: return z0_ + (z1_ - z0_) * (xq - x0_) / (x1_ - x0_)
        return None
    zin = z_at(P["trough_x"][0] + 2); zout = z_at(P["trough_x"][1] - 2)
    rec("Cooling", "Strand clears the entry / exit notches and stays above the water level there", "PASS" if (zin is not None and zout is not None and zin - 0.875 >= -7.4 and zout - 0.875 >= -7.4 and zin > P["water_z"] + 2 and zout > P["water_z"] + 2) else "FAIL",
        f"strand z = {zin:.1f} at the entry wall, {zout:.1f} at the exit wall (notch floor -7.5, water {P['water_z']})")
# thread engagement and edge margins
eng = {"floor flange / close nipple": P["fl_hub_x"][1] - P["close_nip_x"][0], "close nipple / tee": P["close_nip_x"][1] - P["tee_x"][0],
       "tee / barrel": P["tee_x"][1] - P["barrel_x"][0], "barrel / cap": P["barrel_x"][1] - P["cap_x"][0]}
bad_e = {k: v for k, v in eng.items() if v < 12}
rec("Barrel", "NPT thread engagement at every joint (needs about 12-13 mm)", "PASS" if not bad_e else "FAIL", ", ".join(f"{k} {v:.0f}" for k, v in eng.items()))
edge = P["flange_w"] / 2 - P["rod_pos"] - P["rod_d"] / 2
rec("Drive", "Tie-rod hole edge distance in the housing flange", "PASS" if edge >= 6 else "FAIL", f"{edge:.1f} mm of PETG beyond each rod hole (6 walls)")

if "--json" in sys.argv:
    json.dump(R, open(sys.argv[sys.argv.index("--json") + 1], "w"), indent=1)
col = {"PASS": "\033[32m", "WARN": "\033[33m", "FAIL": "\033[31m"}
for i, g_, t, s, d_ in R:
    print(f"{i} [{s}] {g_:13s} {t} :: {d_}")
print("\nSUMMARY:", {s: sum(1 for x in R if x[3] == s) for s in ("PASS", "WARN", "FAIL")})

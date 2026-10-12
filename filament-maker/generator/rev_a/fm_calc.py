"""Planning calculations used on the sheets (single source of truth)."""
import math
from fm_params import P

D, core, pitch, ft = P["screw_od"], P["screw_core"], P["screw_pitch"], P["screw_flight_t"]
h = (D - core) / 2
phi = math.atan(pitch / (math.pi * D))
d_f = 1.75
A_f = math.pi / 4 * d_f ** 2          # mm2
rho = {"PLA": 1.24, "PETG": 1.27, "PET": 1.34, "ABS": 1.04}
EFF = 0.35                              # fraction of drag flow actually delivered (pressure back-flow, leakage)

def metres_per_kg(r):                   # r in g/cm3
    return 1000 / (A_f * 0.01 * r) / 100

def q_cm3s(N_rpm, eff=EFF):
    N = N_rpm / 60
    w = pitch * math.cos(phi) - ft
    Qd = 0.5 * (math.pi * D * N) * math.cos(phi) * w * h * math.cos(phi) * 1e-3
    return Qd * eff

def row(N, r=1.24):
    q = q_cm3s(N)
    g_h = q * r * 3600
    v = q * 1000 / A_f * 60 / 1000      # m/min
    return dict(rpm=N, q=q, g_h=g_h, v=v, t_kg=1000 / g_h)

def die_dp(q, eta=1000.0, L=None, d=None):
    L = (L or P["die_land"]) * 1e-3; d = (d or P["die_d"]) * 1e-3
    return 128 * eta * L * (q * 1e-6) / (math.pi * d ** 4)      # Pa

def thrust(P_mpa):
    return P_mpa * 1e6 * math.pi / 4 * (D * 1e-3) ** 2

def torque(F, mu=0.2, r=0.007):
    return F * r * math.tan(phi + math.atan(mu))

STALL_FULL = 3.0 * 20 * 0.85            # Nm at screw, full driver current
draw = (P["die_d"] / d_f) ** 2
if __name__ == "__main__":
    for m, r in rho.items(): print(m, round(metres_per_kg(r)), "m/kg")
    for N in (2, 3, 4, 5, 6, 8): print(row(N))
    r = row(4); print("die dP MPa @4rpm", die_dp(r["q"]) / 1e6, "draw", draw)
    for p_ in (2, 5, 10): print(p_, "MPa thrust", thrust(p_), "torque", torque(thrust(p_)))
    # cooling
    for hh in (40, 80): 
        tau = 1240 * 1800 * 0.00175 / (4 * hh); t = tau * math.log((190 - 25) / (60 - 25)); print("h", hh, "tau", tau, "t to 60C", t, "path at 1.65 m/min", t * 1.65 / 60 * 1000, "mm")
    print("torsion limit 8 mm core, tau_y 200 MPa:", math.pi * 8 ** 3 * 200 / 16 / 1000, "Nm")

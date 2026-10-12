"""
Filament maker - foundation build (Phase 1) - PARAMETERS
All lengths in mm.  X = flow direction (die at +X), Z = up, Y = across.  Screw axis is Z=0, Y=0.
Change a number here, re-run build_all.py, and every model / STL / drawing number follows.
Items marked VERIFY come from catalogue-typical sizes, not from a part in hand.
"""
P = dict(
    # ---------------- frame ----------------
    rail=20, rail_y=50, rail_top=-85,           # 2020 extrusion, two rails at Y=+-50, top face at Z=-85
    foot_t=10,                                   # printed foot plate sits on the rails (Z -85 .. -75)
    mod1_x=(-205, 690),                          # extruder module rails
    mod2_x=(700, 1240),                          # cooling + puller module rails
    mod3_x=(1250, 1560),                         # spooler module rails

    # ---------------- drive ----------------
    wall_x=(0, 14),                              # motor wall (printed)
    gb=60, gb_len=78, gb_pcd=70,                 # NEMA23 planetary gearbox 20:1  (VERIFY flange / PCD)
    gb_shaft_d=14, gb_shaft_l=30,                # output shaft (VERIFY, 12 or 14)
    motor=57, motor_len=112,                     # NEMA23 3 Nm class stepper
    cpl_x=(18, 50), cpl_d=25,                    # rigid clamp coupler 14 -> 12.7
    spindle_d=12.7, spindle_x=(32, 187),         # 1/2" rod, 1/2-20 UNF thread on the last 22 mm (hand die)
    house_x=(62, 138), house_w=64,               # bearing housing body (printed)
    flange_x=(138, 150), flange_w=104,           # housing front flange / thrust wall
    rod_pos=40, rod_d=8.5,                       # M8 tie rods at (+-40, +-40)
    r8=dict(od=28.575, id=12.7, w=7.94),         # R8-2RS radial bearings x2
    thrust=dict(od=28, id=13, h=9),              # 1/2" thrust bearing  (VERIFY part)
    thrust_x=(146, 155), collar_x=(155, 165), collar_d=25,
    chuck_x=(165, 235), chuck_d=42,              # 13 mm keyless chuck, 1/2-20 UNF  (VERIFY)
    head_x=(245, 261),                           # head plate (printed)

    # ---------------- screw + barrel ----------------
    screw_od=20.0, screw_core=8.0, screw_pitch=20.0, screw_flight_t=2.5,
    shank_af=11.1, shank_x=(210, 275),           # 7/16" hex shank
    flights_x=(275, 640),                        # flighted length 365 mm  (L/D 18)
    fl_od=80, fl_bc=60, fl_t=12, fl_hub_x=(273, 294), # 3/4" NPT floor flange (VERIFY bolt circle)
    close_nip_x=(281, 309),
    tee_x=(296, 352), tee_d=35, port_h=40,
    barrel_x=(339, 644), barrel_od=26.67, barrel_id=20.93,   # 3/4" Sch40 SS nipple, 12"
    cap_x=(631, 651), cap_od=34,
    die_x=(651, 657), die_d=2.2, die_land=14,
    bands=[(413, 463), (468, 518), (523, 573), (578, 628)],   # 4 x 50 mm, ID 27-28 (VERIFY)
    band_od=36, band_id=28,
    strap_x=385,                                  # barrel support strap (cold section)

    # ---------------- hopper ----------------
    hopper_cx=324, hop_collar_id=27.0, hop_top_r=80, hop_h=248,

    # ---------------- cooling / puller ----------------
    trough_x=(667, 1092), trough_w=28,
    puller_x=(1105, 1195), roller_d=30, roller_w=20,

    # ---------------- spooler ----------------
    spool_cx=1440, spool_cz=40, spool_od=200, spool_core=100, spool_w=66, spool_bore=54,
    dancer_x=1300,
)

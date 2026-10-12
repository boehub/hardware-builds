"""Assemble build_deck.py (Rev B) from the Rev A header/sections plus new sections."""
import re
R = lambda n: open(f"/tmp/seg_{n}.txt").read()
def sub(txt, pairs):
    for a, b in pairs:
        if a not in txt: print("MISSING:", a[:60])
        txt = txt.replace(a, b)
    return txt

HEADER = R("header")
HEADER += '''
from PIL import Image
import trimesh

def picfit(sl, name, x, y, w, h):
    """place picture inside the w x h box, centred, keeping aspect"""
    iw, ih = Image.open(IMG + name).size
    s = min(w / iw, h / ih)
    pw, ph = iw * s, ih * s
    return sl.shapes.add_picture(IMG + name, Inches(x + (w - pw) / 2), Inches(y + (h - ph) / 2), width=Inches(pw), height=Inches(ph))

VA = json.load(open(HERE + "/out/verify_rev_a.json")); VB = json.load(open(HERE + "/out/verify_rev_b.json"))
cnt = lambda V, s: sum(1 for r in V if r[3] == s)
A_FAIL, A_WARN, B_PASS, B_WARN, B_FAIL = cnt(VA, "FAIL"), cnt(VA, "WARN"), cnt(VB, "PASS"), cnt(VB, "WARN"), cnt(VB, "FAIL")
r4 = C.row(4)
'''

DATA = '''
BOM = [
 ("Drive", None, None, None, None),
 ("NEMA 23 stepper, 3 Nm class, 4.2 A", 1, "57 × 57 × 112, 8 mm shaft", 35, 50),
 ("NEMA 23 planetary gearbox 20:1", 1, "60 mm flange, Ø14 output (VERIFY)", 50, 90),
 ("Stepper driver DM542T (or TB6600)", 1, "24–36 V, set to 1.2 A", 15, 25),
 ("Clamp coupler 14 → 12.7 mm", 1, "≈ Ø25 × 32 (VERIFY bores)", 8, 12),
 ("Spindle: ½ in steel rod or Gr.8 ½-20 bolt", 1, "160 mm, last 22 mm threaded ½-20", 5, 8),
 ("R8-2RS bearing", 2, "½ × 1⅛ × 5/16 in", 8, 12),
 ("Thrust bearing ½ in bore + washers", 1, "OD 28 × 9 (VERIFY)", 8, 15),
 ("Shaft collar ½ in (set screw)", 1, "OD 25", 4, 6),
 ("Keyless chuck 13 mm, ½-20 UNF", 1, "closes on 7/16 in hex", 12, 20),
 ("M8 threaded rod, nuts, washers", 4, "M8 × 150 + 3 nuts each", 8, 12),
 ("Screw & barrel", None, None, None, None),
 ("Ship auger bit Ø20 × 460, 7/16 hex shank", 1, "solid-core / continuous flight", 15, 25),
 ("3/4 NPT 304 SS nipple, 12 in", 1, "Sch 40: OD 26.67, ID 20.93", 20, 35),
 ("3/4 NPT floor flange", 1, "4 holes (VERIFY bolt circle)", 10, 15),
 ("3/4 NPT pipe tee", 1, "feed port on the side", 6, 12),
 ("3/4 NPT nipples: close ×1, 2 in ×1", 2, "close = flange link, 2 in = feed", 8, 14),
 ("3/4 NPT cap, brass or SS", 1, "die body", 5, 10),
 ("M10×1.5 brass bolt + SS mesh 60–100", "1+", "die plug (spares) + filter discs", 3, 8),
 ("Band heater 120 V, 150–200 W", 4, "28 mm ID × 50 wide (VERIFY)", 40, 70),
 ("K thermocouple, ring or bayonet", 4, "M4 ring lug, 1 m lead", 10, 16),
 ("REX-C100 PID, SSR output", 4, "48 × 48 mm panel", 40, 60),
 ("SSR-25DA", 4, "DC in, AC out, with heat sink", 16, 28),
 ("Thermal fuse 280 °C (or 300 °C stat)", 2, "in the heater feed", 3, 6),
 ("Strap, aluminium angle, guard sheet", "1 set", "support + heat guard", 10, 15),
 ("Hopper (1 kg)", None, None, None, None),
 ("37 mm gearmotor 24 V 12 rpm, 6 mm D-shaft", 1, "agitator, ≥ 1.5 Nm (VERIFY)", 12, 20),
 ("6 mm steel rod 150 mm + 2 × 626ZZ bearing", "1 set", "agitator shaft + lid bearings", 5, 10),
 ("M4 × 16 bolts + nuts, M4 × 30 + nuts", "1 set", "8 drum/cone bolts, stay clamp, lid", 4, 8),
 ("40 mm fan 24 V", 1, "feed throat", 3, 6),
 ("Water bath + cooling", None, None, None, None),
 ("Small 12/24 V DC pump (aquarium type)", 1, "≥ 300 L/h, 1 m head", 10, 20),
 ("10 L bucket + silicone tube + 2 hose barbs", "1 set", "reservoir, inlet + overflow", 12, 20),
 ("624ZZ bearing + M4 × 20 bolt", 2, "sheaves under the water", 3, 6),
 ("Sponge, PTFE tube Ø4 / Ø2, aquarium silicone", "1 set", "wiper, eyelet, tank joints", 8, 14),
 ("Puller, level-wind, spooler", None, None, None, None),
 ("NEMA 17 stepper", 3, "puller, spool drive, level-wind (donor Vyper?)", 0, 45),
 ("TMC2209 (or A4988) driver", 3, "1/16 micro-step", 18, 30),
 ("T8 × 8 lead screw 150 mm + brass nut", 1, "level-wind, 1.75 mm per spool turn", 6, 10),
 ("8 mm smooth rod 100 mm + 8 mm LM8UU", 1, "carriage guide (sleeve or bronze)", 4, 8),
 ("M8 rod 120 mm, spring 2 N/mm, nuts", 1, "idler hub cone (spool drive)", 4, 8),
 ("10 kΩ linear pot", 1, "dancer sensor", 2, 4),
 ("Empty 1 kg spool Ø200, 54 mm bore, 66 wide", 1, "VERIFY your spool (reuse a spent one)", 0, 10),
 ("Electronics & frame", None, None, None, None),
 ("Arduino Nano", 1, "5 V logic", 6, 15),
 ("24 V 10 A PSU", 1, "240 W", 20, 30),
 ("MOSFET PWM board", 2, "agitator + pump", 5, 10),
 ("Contactor 24 V coil + E-stop NC", "1 set", "hardware safety chain", 15, 30),
 ("Breaker, IEC inlet, wire, terminals", "1 set", "120 V side, ferrules, GFCI outlet", 20, 40),
 ("Knobs, toggle, lamp", "1 set", "front panel", 6, 12),
 ("2020 extrusion + T-nuts + screws", "6 rails", "895 ×2, 540 ×2, 395 ×2", 50, 85),
 ("Hose clamp, PTFE tape, Ni anti-seize", "1 set", "hopper joint, NPT threads", 8, 15),
 ("Printed parts, PETG / ASA / TPU", "≈ PKG kg", "sheet 14", 0, 40),
]
LOW = sum(r[3] for r in BOM if r[3] is not None); HIGH = sum(r[4] for r in BOM if r[4] is not None)
import glob
_vol = 0.0
for f in glob.glob(HERE + "/out/stl/*.stl"):
    try:
        m = trimesh.load(f); mult = 2 if re.search(r"_x2", f) else 1
        _vol += abs(m.volume) * mult
    except Exception: pass
PKG = round(_vol / 1000 * 0.4 * 1.27 / 1000, 1)   # ~40 % effective solid fraction, PETG 1.27 g/cm3
BOM = [(a, ("≈ %.1f kg" % PKG) if b == "≈ PKG kg" else b, c, d, e) for a, b, c, d, e in BOM]
'''
DATA = "import re\n" + DATA

S1 = '''
# =============================================================================================== 1 overview
sl = new_slide("DIY FILAMENT MAKER – BLUEPRINT SET (REV B)")
tb(sl, 0.45, 0.95, 7.5, 0.25, "FULL LINE – 1 kg hopper, extruder, water bath, puller, dancer, level-wind spooler", 12, True)
pic(sl, "hero_all.png", 0.35, 1.25, w=7.7)
stat(sl, 8.3, 0.95, 2.2, 1.12, "1 kg → 1 kg", "a 6.4 L hopper takes 1 kg of flakes; the spool takes 1 kg (≈ 335 m of PLA)", 22)
stat(sl, 10.65, 0.95, 2.2, 1.12, f"≈ {r4['t_kg']:.1f} h / kg", f"at 4 rpm: ≈ {r4['v']:.1f} m/min, ≈ {r4['g_h']:.0f} g/h (estimate, calibrate)", 22)
stat(sl, 8.3, 2.2, 2.2, 1.12, "6.4 L", "hopper: 60° cone + agitator, holds ≥ 1 kg of flakes down to 0.17 g/cm³", 22)
stat(sl, 10.65, 2.2, 2.2, 1.12, f"{A_FAIL} → {B_FAIL} FAIL", f"Rev A vs Rev B checks; Rev B: {B_PASS} PASS, {B_WARN} WARN", 22)
idx = ["1  Overview", "2  What changed in Rev B", "3  Verification report", "4  Assembly views + overall size", "5  Exploded view + part numbers",
       "6  1 kg hopper", "7  Process + material settings", "8  Screw + barrel (section)", "9  Die + filter", "10  Drive train + thrust loop",
       "11  Printed parts: wall, housing, head plate", "12  Water bath", "13  Puller, dancer, level-wind, spooler", "14  Print list",
       "15  Electrical + safety", "16  Speeds + dial-in", "17  Bill of materials", "18  Tools + workarounds", "19  Assembly order + design checks",
       "20  Open items (VERIFY) + roadmap"]
panel(sl, 8.3, 3.45, 4.55, 3.5, "SHEET INDEX", [(t, dict(size=8.5, space=0.6)) for t in idx])
tb(sl, 0.45, 4.65, 7.6, 0.25, "Models: filament_maker_assembly.fbx (Blender)  ·  Print files: filament_maker_stl.zip  ·  Generator + checker: filament_maker_generator.zip", 10, False, GREY)
tb(sl, 0.45, 5.0, 7.6, 1.8, ["Rev B = Rev A + a geometric check of every part against every other (2926 part pairs), the fixes that check forced, and three upgrades that were roadmap items: the 1 kg hopper, the water bath and the level-wind spooler.",
                              "In practice 1 kg of scrap gives a little less than 1 kg of filament: purge, start-up and the tail left in the barrel cost roughly 3–10 % (estimate). Load ≈ 1.05–1.1 kg if you want a full 1 kg spool.",
                              "Dimensions marked VERIFY come from catalogue-typical sizes, not from parts in hand – see sheets 19 and 20."], 10, False, GREY)
'''

S2 = '''
# =============================================================================================== 2 what changed
sl = new_slide("REV B – WHAT CHANGED AND WHY")
rows = [["Area", "Rev A", "Rev B", "Found by"],
        ["Hopper (your request)", "2.8 L, 32° cone: 0.5 kg at 0.2 g/cm³, would bridge", "6.4 L, 60° cone, 2 printed pieces + lid, agitator, stay to the head plate: 1.15 kg at 0.2 g/cm³", "capacity + angle + 9 Nm lateral check"],
        ["Cooling", "425 mm of air; PLA needs ≈ 1 m (0.67 m/min max)", "474 mm water bath; strand runs 485 mm under water (needs 52 mm); pump + 10 L bucket", "cooling-length check"],
        ["Spooler", "gearmotor, no level-wind: all filament lands in one 2 mm band", "stepper-driven spool + NEMA 17 / T8 level-wind: 1.75 mm per spool turn, ± 28 mm stroke", "spool-pack check"],
        ["Dancer arm / spool hub", "arm cuts the spool (8046 mm³); hub cones cut the plates (3025 mm³)", "arm re-placed and swept 15–60°: clear; spring-loaded hub cone, 12 mm retract", "mesh-vs-mesh interference"],
        ["Puller", "idler arm passes through the side plates (1024 mm³)", "slot cut, pressure bridge sits on the plates", "mesh-vs-mesh interference"],
        ["Bearing housing", "flange ±26 mm: tie-rod nuts float 1.5 mm in air", "flange ±52 mm: nuts bear on it, 7.8 mm edge distance", "load-path gap check"],
        ["Gearbox / hopper joint", "gearbox 2 mm off the wall; hopper sleeve 8 mm above the tee", "38.1 mm pilot seat; sleeve rests on the tee", "load-path gap check"],
        ["Screw torque", "19.4 Nm at 1.6 A = 193 MPa core shear (yield 150–170)", "1.2 A limit: 14.6 Nm = 145 MPa", "stress check"],
        ["Printing", "fan duct 360 mm does not fit the bed", "ducts removed (one throat fan); 28 part files all fit 245 × 245 × 260", "bed-fit check"],
        ["Size", "1845 mm, 52 parts, 16 print files", "1945 mm, 77 parts, 28 print files", ""]]
table(sl, 0.4, 0.9, 12.53, [1.6, 3.4, 4.9, 2.3], rows, size=8.5, row_h=0.43, bold_first=True)
panel(sl, 0.4, 5.85, 12.53, 1.1, "FOUNDATION STAYS THE SAME", [
    ("Drive train, screw, barrel, die and heaters are unchanged apart from the lower driver current and the fixes above – the Rev A parts you already ordered still apply. Roadmap items M2 (level-wind), M3 (water bath) and M5 (hopper agitator) moved into the foundation.", dict(size=9.5))], 9.5)
'''

S3 = '''
# =============================================================================================== 3 verification
sl = new_slide("VERIFICATION – DO THE PARTS WORK TOGETHER?")
stat(sl, 0.4, 0.9, 2.45, 1.1, f"{A_FAIL} FAIL", f"Rev A: {A_WARN} WARN; the same checker run on the Rev A model", 24)
stat(sl, 3.0, 0.9, 2.45, 1.1, f"{B_FAIL} FAIL", f"Rev B: {B_PASS} PASS, {B_WARN} WARN", 24)
stat(sl, 5.6, 0.9, 2.45, 1.1, "2926", "part pairs tested for solid overlap (77 parts, 17 intended fits whitelisted)", 24)
rows = [["Check group", "Method", "Rev B"]]
from collections import Counter
cc = Counter((r[1]) for r in VB)
meth = {"Interference": "boolean volume of every pair of meshes (trimesh + manifold3d)", "Load path": "nearest-surface gap on every force-carrying contact",
        "Printing": "each part in print orientation vs 245 × 245 × 260 bed", "Screw / barrel": "radial clearance, cantilever sag", "Drive": "torque, thrust, rod stress, edge distance",
        "Process": "die pressure at 4 rpm", "Cooling": "length in water, strand path vs notches, bath heat", "Hopper": "cone angle, capacity at 0.2 / 0.3 / 0.4 g/cm³, agitator torque",
        "Spooler": "pack radius, dancer sweep, level-wind travel, cone friction, stepper speed", "Electrical": "mains current", "Stability": "hopper lateral load", "Barrel": "NPT thread engagement"}
for g in ["Interference", "Load path", "Printing", "Screw / barrel", "Drive", "Process", "Cooling", "Hopper", "Spooler", "Electrical", "Stability", "Barrel"]:
    n = cc.get(g, 0); w = sum(1 for r in VB if r[1] == g and r[3] == "WARN")
    rows.append([g, meth.get(g, ""), f"{n - w} pass" + (f", {w} warn" if w else "")])
table(sl, 8.2, 0.9, 4.73, [1.1, 2.8, 0.9], rows, size=7.5, row_h=0.37, bold_first=True)
rows = [["Rev A finding", "Rev B fix"],
        ["Spool disc cuts the dancer arm (8046 mm³)", "dancer moved, swept 15–60° – no contact"],
        ["Hub cones cut the spooler plates (3025 mm³)", "hub cones redesigned, plates re-spaced"],
        ["Puller idler arm passes through the side plates", "arm slot cut, plates rebuilt"],
        ["Strand clips the trough walls", "sheaves carry strand under the water; notches clear"],
        ["Housing flange ±26 instead of ±52; rod nuts float 1.5 mm", "flange ±52, nuts seat (gap 0.0)"],
        ["Gearbox 2 mm off the wall", "pilot seat Ø38.1 × 2 mm, gap 0.0"],
        ["Hopper sleeve 8 mm above the tee", "sleeve rests on the tee, gap 0.0, stay added"],
        ["Fan duct 360 mm will not print", "ducts removed; everything fits the bed"],
        ["Screw core 193 MPa at 1.6 A", "1.2 A limit: 145 MPa"],
        ["Air path 425 mm, needs 1041 mm", "water bath: 485 mm under water"],
        ["Cone 32°, 2.8 L", "cone 60°, 6.4 L"],
        ["No level-wind: 1 kg cannot be wound", "NEMA 17 / T8 level-wind, 700 µsteps per turn"]]
table(sl, 0.4, 2.15, 7.65, [3.8, 3.85], rows, size=8.5, row_h=0.3, bold_first=False)
panel(sl, 0.4, 6.15, 7.65, 0.85, "ONE WARNING LEFT", [
    ("Screw self-weight sag 0.92 mm vs 0.46 mm clearance: the flights rest on the barrel floor – expect slow wear, keep the barrel lubricated with the first purge. Acceptable for a foundation build; M1 (hardened barrel liner) fixes it.", dict(size=8.5))], 9)
panel(sl, 8.2, 5.95, 4.73, 1.05, "WHAT THIS DOES NOT PROVE", [
    ("These are geometry and hand-calculation checks, not FEA or a test run. Bought parts are modelled at catalogue sizes (VERIFY list, sheet 20).", dict(size=8.5, color=RED))], 9)
'''

S6 = '''
# =============================================================================================== 6 hopper
sl = new_slide("1 KG HOPPER – 1 KG OF SCRAP IN, 1 KG ON THE SPOOL")
picfit(sl, "d_hopper.png", 0.35, 0.85, 4.35, 6.15)
picfit(sl, "d_hopcap.png", 4.85, 0.85, 4.6, 2.45)
stat(sl, 9.6, 0.85, 3.25, 1.15, "6.4 L", "gross volume; 90 % fill = 5.8 L = 1.0 kg at 0.174 g/cm³", 24)
stat(sl, 9.6, 2.1, 3.25, 1.15, "60°", "cone wall angle from horizontal (Rev A: 32°) – flakes slide instead of bridging", 24)
panel(sl, 4.85, 3.4, 4.6, 3.6, "WHY IT HOLDS 1 KG", [
    ("Fluffy ground bottles / film flake is 0.15–0.25 g/cm³; dense chips 0.3–0.4. At 90 % fill the hopper holds 1.15 kg at 0.2, 1.7 kg at 0.3, 2.3 kg at 0.4 g/cm³.", dict(bullet=True)),
    ("Ø236.8 × 120 drum over a 160 mm, 60° cone.", dict(bullet=True)),
    ("The paddle agitator sweeps the cone wall at 12 rpm (24 V gearmotor, ≈ 0.2 Nm needed) to break bridges.", dict(bullet=True)),
    ("Two ears bolt the sleeve to the head plate – the hopper no longer levers on the NPT tee (9 Nm → 0).", dict(bullet=True))], 9)
panel(sl, 9.6, 3.4, 3.25, 3.6, "PRINTING", [
    ("P05 lower cone: print upside down, 3 walls.", dict(bullet=True)),
    ("P06 drum: upright, 3 walls.", dict(bullet=True)),
    ("P07 lid frame upright; P08 lid halves ×2.", dict(bullet=True)),
    ("8 × M4 bolts join drum and cone; add a gasket of 1 mm foam tape.", dict(bullet=True)),
    ("P09 stay clamp upside down; P10 agitator paddle.", dict(bullet=True)),
    ("Keep the lid on: it stops flakes from being sucked into the motor and keeps dust down.", dict(bullet=True, color=RED))], 9)
'''

S12 = '''
# =============================================================================================== 12 water bath
sl = new_slide("WATER BATH – COOLING THAT KEEPS UP")
picfit(sl, "d_bath.png", 0.35, 0.85, 12.63, 3.6)
picfit(sl, "d_bath_xs.png", 0.4, 4.55, 3.0, 2.45)
stat(sl, 3.6, 4.55, 2.3, 1.1, "485 mm", "of strand under water vs 52 mm needed at 4 rpm (PLA 190 → 60 °C)", 22)
stat(sl, 3.6, 5.8, 2.3, 1.1, "+7 K / kg", "bath warm-up over a full kilogram with the 10 L circulating reservoir", 22)
panel(sl, 6.1, 4.55, 3.4, 2.45, "HOW IT WORKS", [
    ("The strand enters through a 5 mm notch above the water line, dips under a 624ZZ sheave, runs straight, then rises over a second one – so it never touches a wall.", dict(bullet=True)),
    ("A pump fills from the bucket; an overflow barb on the −Y wall sets the level at Z = −10.", dict(bullet=True))], 8.5)
panel(sl, 9.65, 4.55, 3.2, 2.45, "BUILD NOTES", [
    ("Two 237 mm segments (P11, P12), joined by 4 × M3 and silicone.", dict(bullet=True)),
    ("Print with 5 walls and seal with aquarium silicone – water-test over a tray before wiring anything.", dict(bullet=True, color=RED)),
    ("The sponge wiper in the exit slot dries the strand before the puller.", dict(bullet=True))], 8.5)
'''

S13 = '''
# =============================================================================================== 13 puller, dancer, level-wind, spooler
sl = new_slide("PULLER, DANCER, LEVEL-WIND + 1 KG SPOOLER")
picfit(sl, "d_line2.png", 0.35, 0.85, 6.4, 3.1)
picfit(sl, "d_spool_top.png", 6.9, 0.85, 6.1, 3.1)
stat(sl, 0.4, 4.1, 2.0, 1.1, "700", "micro-steps of level-wind per spool turn = 1.75 mm of travel", 24)
stat(sl, 0.4, 5.35, 2.0, 1.1, "3.0–5.3 rpm", "spool stepper at 1.65 m/min (full → empty core)", 18)
stat(sl, 2.55, 4.1, 2.0, 1.1, "335 m", "1 kg PLA reaches R 89 of the 100 mm flange, 60 mm wide", 24)
stat(sl, 2.55, 5.35, 2.0, 1.1, "×3.2", "cone friction margin: 0.29 Nm vs 0.09 Nm at 1 N strand tension", 24)
panel(sl, 4.7, 4.1, 4.0, 2.9, "PULLER + DANCER", [
    ("Two ×30 TPU rollers, drive roller on a NEMA 17 (1/16 micro-step): 0.3–4 m/min. Pressure bridge with two springs sets the nip.", dict(bullet=True)),
    ("The strand loops under the dancer roller; a 10 kΩ pot at the pivot reads the arm angle and the Nano trims the spool speed to keep it mid-travel (swept 15–60°, nothing in the way).", dict(bullet=True))], 8.5)
panel(sl, 8.85, 4.1, 4.0, 2.9, "LEVEL-WIND + SPOOL", [
    ("A NEMA 17 turns a T8 lead screw; the carriage with a PTFE eyelet runs ± 28 mm inside the 60 mm winding width and reverses at each end.", dict(bullet=True)),
    ("The spool is driven by a second NEMA 17 through a spring-loaded cone: the idler cone retracts 12 mm (68 mm tip gap vs 66 mm spool) to drop a spool in.", dict(bullet=True)),
    ("Because the level-wind steps follow the spool steps, the layers stay in step without a sensor.", dict(bullet=True))], 8.5)
'''

S14 = '''
# =============================================================================================== 14 print list
sl = new_slide("PRINT LIST – 28 FILES, ALL FIT THE 245 × 245 × 260 BED")
stl = json.load(open(IMG + "stl_list.json"))
mat = {"P15": "TPU 95A", "P16": "TPU 95A", "P11": "PETG, 5 walls, seal", "P12": "PETG, 5 walls, seal", "P04": "PETG (3 walls)", "P05": "PETG (3 walls)", "P06": "PETG (3 walls)"}
hdr = ["File", "X × Y × Z (mm)", "Qty", "Material"]
rows = []
for n, ext in stl:
    pid = n.split("_")[0]
    qty = 2 if "_x2" in n else 1
    rows.append([n.replace("_x2", "") + ".stl", " × ".join(f"{e:.0f}" for e in ext), qty, mat.get(pid, "PETG")])
half = (len(rows) + 1) // 2
table(sl, 0.4, 0.9, 6.2, [3.2, 1.55, 0.35, 1.5], [hdr] + rows[:half], size=7.5, row_h=0.31)
table(sl, 6.75, 0.9, 6.2, [3.2, 1.55, 0.35, 1.5], [hdr] + rows[half:], size=7.5, row_h=0.31)
tb(sl, 0.4, 0.9 + 0.31 * (half + 1) + 0.12, 12.5, 0.9, [f"Total printed mass ≈ {PKG} kg of PETG (+ TPU tyres). Print order: P02, P03, P05 first – test-fit the bearings, the chuck flange and the NPT tee before printing the rest.",
        "Orientation is as exported: the STL already lies the way it should print (hopper cone upside down, lid frame and drum upright)."], 9.5, False, GREY)
'''

S15 = R("s11")
S15 = sub(S15, [
    ('"ELECTRICAL BLOCK DIAGRAM + SAFETY CHAIN"', '"ELECTRICAL BLOCK DIAGRAM + SAFETY CHAIN"'),
    ('drv = [("DM542T → NEMA 23", "screw, 1.6 A limit"), ("TMC2209 → NEMA 17", "puller"), ("MOSFET → gearmotor", "spooler PWM"), ("5 × 40 mm fans", "24 V, always on with heat")]',
     'drv = [("DM542T → NEMA 23", "screw, 1.2 A limit"), ("3 × TMC2209 → NEMA 17", "puller, spool, level-wind"), ("MOSFET → gearmotor", "hopper agitator"), ("MOSFET → pump", "water circulation"), ("40 mm fan", "feed throat, 24 V")]'),
    ('box(sl, 2.3, 4.35 + i * 0.4, 2.0, 0.34, [a_, b_], WHITE, INK, 7.5, True)\n    arrow(sl, 2.0, 4.7, 2.3, 4.52 + i * 0.4, INK, 1.0)',
     'box(sl, 2.3, 4.3 + i * 0.34, 2.0, 0.3, [a_, b_], WHITE, INK, 7, True)\n    arrow(sl, 2.0, 4.7, 2.3, 4.45 + i * 0.34, INK, 1.0)'),
    ('for i in range(4): arrow(sl, 4.8, 4.45 + i * 0.28, 4.3, 4.52 + i * 0.4, BLUE, 0.8)', 'for i in range(5): arrow(sl, 4.8, 4.4 + i * 0.22, 4.3, 4.45 + i * 0.34, BLUE, 0.8)'),
    ('("Driver current limit (≈ 1.6 A) lets', '("Driver current limit (1.2 A ≈ 14.6 Nm) lets'),
    ('Spooler: PWM = base + k × (dancer − centre).', 'Spool stepper: rpm = strand speed ÷ pack circumference, trimmed by the dancer pot.  Level-wind: 700 micro-steps per spool turn, reverses at ±28 mm.'),
    ('"Jam: driver ALM → stop, reverse 2 s, stop. Heat-not-ready → screw disabled."', '"Jam: driver ALM → stop, reverse 2 s, stop. Heat-not-ready → screw disabled. Pump runs whenever the line is on; keep it on a GFCI outlet."'),
    ('panel(sl, 0.5, 6.0, 7.6, 0.95, "CONTROL (NANO)"', 'panel(sl, 0.5, 6.05, 7.6, 0.95, "CONTROL (NANO)"'),
    ('"Never leave it heating unattended until you trust the thermal fuse and the PIDs."', '"Never leave it heating unattended until you trust the thermal fuse and the PIDs. Water + mains: GFCI, bucket and pump away from the control box and below its level, drip loop on every cable."'),
])

S19 = '''
# =============================================================================================== 19 assembly + checks
sl = new_slide("ASSEMBLY ORDER, DESIGN CHECKS + OPEN ITEMS")
steps = ["Cut rails to length, square the frame, drop in T-nuts for every foot.", "Print P02, P03, P05 first; test-fit bearings, chuck and NPT tee; clean the seats.",
         "Thread the spindle (or cut the ½-20 bolt); fit R8 bearings, thrust bearing, collar.", "Mount motor + gearbox on the wall; couple to the spindle; set the driver to 1.2 A.",
         "Tie the housing to the head plate with the M8 rods; check the spindle spins free by hand.", "Prep the screw (cut tip, polish); seat it in the chuck, tighten with threadlocker.",
         "Build the NPT stack on the floor flange; PTFE the cold joints; bolt to the head plate.", "Fit barrel, cap, die plug, filter; shim + bands; clamp thermocouples.",
         "Bolt the hopper cone to the sleeve and the stay; fit the drum, lid frame, agitator and gearmotor.", "Seal and water-test the bath; mount sheaves, pump, bucket, sponge wiper.",
         "Mount puller, dancer, level-wind and spooler; thread a test string through the notches.", "Wire heaters and PIDs off the machine; test each zone to 100 °C empty.",
         "Dry-run the screw at 5 rpm empty for 5 min; then first heat with PLA and dial in (sheet 16)."]
tb(sl, 0.5, 0.78, 5, 0.2, "ASSEMBLY ORDER", 10.5, True)
rich(sl, 0.5, 1.0, 5.0, 5.95, [(f"{i}  {s_}", dict(size=9, space=3.5)) for i, s_ in enumerate(steps, 1)], 9)
rows = [["DESIGN CHECK", "RESULT"],
        ["Screw output at 4 rpm", f"{r4['q']:.3f} cm³/s = {r4['g_h']:.0f} g/h (est.)"],
        ["Thrust at 5 / 10 MPa", f"{C.thrust(5):.0f} N / {C.thrust(10):.0f} N"],
        ["Screw torque at 5 / 10 MPa", f"{C.torque(C.thrust(5)):.1f} / {C.torque(C.thrust(10)):.1f} Nm (+ friction)"],
        ["Torque at the 1.2 A driver limit", "14.6 Nm = 145 MPa core shear (Rev A: 193)"],
        ["Thrust bearing seat", "6.5 MPa on printed PETG (limit 15)"],
        ["Warm-up to 270 °C", "112 kJ → 2.5 min ideal, 8–12 real"],
        ["Heater power / mains", "800 W; 7.6 A total on a 15 A circuit"],
        ["Hopper vs 1 kg of flakes", "6.4 L: 1.15 kg at 0.2 g/cm³ (90 % fill)"],
        ["Cooling in the water bath", "52 mm needed, 485 mm available"],
        ["Spool", "1 kg PLA = 335 m, R 89 of 100 mm"],
        ["Spool speed", "3.0 → 5.3 rpm at 1.65 m/min"],
        ["Draw-down", f"{C.draw:.2f}× (×2.2 die → 1.75 mm)"]]
table(sl, 5.8, 0.95, 7.03, [3.1, 3.9], rows, size=9, row_h=0.3, bold_first=True)
panel(sl, 5.8, 5.0, 7.03, 1.95, "WHAT THE CHECKS SAY", [
    ("Mechanically comfortable: bearings and rods have large margin; the screw core is the weak link, so the driver current is the fuse.", dict(bullet=True)),
    ("Water bath and 1 kg hopper both have ≥ 3× margin on the numbers that matter.", dict(bullet=True)),
    ("The one WARN is screw sag on the barrel floor (wear, not failure).", dict(bullet=True)),
    ("Throughput numbers are estimates until calibrated with a weighed metre.", dict(bullet=True, color=RED))], 9)
'''

S20 = '''
# =============================================================================================== 20 verify + roadmap
sl = new_slide("OPEN ITEMS (VERIFY) + MODIFICATION ROADMAP")
rows = [["#", "VERIFY before ordering / printing", "Why it matters"],
        ["1", "Auger bit: 20 mm OD, ≈ 8 mm core, 7/16 in hex, continuous flights", "sets clearance, torque limit, screw length"],
        ["2", "Gearbox output shaft (12 vs 14 mm), flange PCD, pilot Ø38.1", "coupler bores, wall holes"],
        ["3", "Chuck thread ½-20 UNF and retaining screw; spindle thread fit", "reverse rotation can loosen it"],
        ["4", "Thrust bearing ½ in bore, OD ≤ 28; floor flange bolt circle", "housing seat, head-plate holes"],
        ["5", "Band heater ID (27–28 mm) and watt rating; REX-C100 alarm relay", "contact, warm-up, heat-ready interlock"],
        ["6", "Agitator gearmotor ≥ 1.5 Nm and 6 mm D-shaft", "needs ≈ 0.2 Nm to sweep the cone"],
        ["7", "Pump flow / head, hose barb size, silicone sealing of P11/P12", "printed tank must not leak"],
        ["8", "Your spool: Ø200, 54 mm bore, 66 wide; T8 nut size", "hub cones, winding width"],
        ["9", "Printed-part temperatures near Z1 / head plate on PET", "creep above 70 °C"],
        ["10", "Real throughput (weigh 1 m) and yield per kg of scrap", "sets puller ratio table"]]
table(sl, 0.4, 0.95, 6.5, [0.3, 3.8, 2.4], rows, size=8.5, row_h=0.36, zebra=True)
tb(sl, 7.1, 0.88, 5.8, 0.25, "ROADMAP (M2, M3, M5 are now in the foundation)", 10.5, True)
mods = [("M1", "Compression screw", "ground screw + hardened barrel liner; fixes wear, sag and surge"),
        ("M2", "Level-wind  ✔ Rev B", "done: NEMA 17 + T8 on the spooler base"),
        ("M3", "Water bath  ✔ Rev B", "done; next: air knife + chiller for hot days"),
        ("M4", "Closed-loop diameter", "optical or Hall gauge after the bath drives the puller (PID)"),
        ("M5", "Hopper agitator  ✔ Rev B", "done; next: heated drying hopper, side feeder"),
        ("M6", "Melt sensing", "die pressure transducer + melt thermocouple; auto-stop"),
        ("M7", "Folded drive + enclosure", "belt drive saves ≈ 250 mm, fan-cooled housing, quieter"),
        ("M8", "Shredder hand-off", "chute from the DIY shredder, pellet cutter option")]
rows = [["", "Mod", "What it adds"]] + [[a, b, c] for a, b, c in mods]
table(sl, 7.1, 1.2, 5.83, [0.4, 1.6, 3.8], rows, size=8.5, row_h=0.4, bold_first=True)
panel(sl, 0.4, 5.05, 6.5, 1.95, "NEXT STEPS", [
    ("Confirm the auger bit and gearbox listings (items 1–2) – they fix the most dimensions.", dict(bullet=True)),
    ("Print P02, P03 and P05 first; test-fit bearings, chuck and the hopper sleeve on the tee.", dict(bullet=True)),
    ("Tell me what changes (your parts, bed size, scrap type) and I will re-run the generator and the checker: every drawing and file follows fm_params.py.", dict(bullet=True))], 9.5)
panel(sl, 7.1, 4.95, 5.83, 2.05, "SAFETY IN ONE PARAGRAPH", [
    ("Hot barrel (up to 280 °C), pressurised melt, mains wiring next to water, and two rotating parts (screw, agitator). Use the guard, the E-stop, the thermal fuse and a GFCI; never reach into the hopper while the screw or paddle turns; ventilate for ABS/PET fumes; wear glasses when clearing a die.", dict(size=9.5))], 9.5)

prs.save(OUTF)
print("saved", OUTF, "slides", len(prs.slides), "bom", LOW, HIGH)
'''

S2v = sub(R("s2"), [('"ASSEMBLY VIEWS – OVERALL SIZE"', '"ASSEMBLY VIEWS – OVERALL SIZE"'),
                    ("rails of module 1 (895), 2 (540) and 3 (310)", "rails of module 1 (895), 2 (540) and 3 (395)"),
                    ('pic(sl, "d_views.png", 0.75, 0.88, w=11.8)', 'picfit(sl, "d_views.png", 0.75, 0.85, 11.8, 5.6)'),
                    ("tb(sl, 0.75, 6.5, 11.8, 0.55,", "tb(sl, 0.75, 6.5, 11.8, 0.55,")])
S2v = S2v.replace("# =", "# =", 1)

S3x = '''
# =============================================================================================== 5 exploded
sl = new_slide("EXPLODED VIEW – PART NUMBERS")
EX_W = 9.1
pic(sl, "exploded.png", 0.3, 0.95, w=EX_W)
EX_H = EX_W * 1400 / 2400
mk = json.load(open(IMG + "exploded_markers.json"))
NUM = [("H10", "NEMA 23 stepper"), ("H11", "Planetary gearbox 20:1"), ("P01", "Motor wall (printed)"), ("H12", "Clamp coupler"), ("H13", "Spindle ½ in"),
       ("H14", "R8 bearings (2)"), ("P02", "Bearing housing + thrust flange"), ("H15", "Thrust bearing"), ("H16", "Shaft collar"), ("H17", "13 mm chuck"),
       ("H21", "M8 tie rods (4)"), ("P03", "Head plate (printed)"), ("H20", "Auger screw Ø20"), ("H22", "Floor flange 3/4 NPT"), ("H23", "Close nipple"),
       ("H24", "Pipe tee (feed port)"), ("H25", "Feed nipple 2 in"), ("P05", "Hopper cone + sleeve"), ("P06", "Hopper drum"), ("P07", "Lid frame + agitator mount"),
       ("P09", "Stay clamp to head plate"), ("H26", "Barrel nipple 12 in SS"), ("H27", "Cap (die body)"), ("H28", "Die plug Ø2.2"), ("H29", "Band heaters (4)"),
       ("H30", "Thermocouples (4)"), ("H31", "Heat guard"), ("H32", "Barrel strap + post"), ("H34", "Feed-throat fan"), ("P04", "Dust slinger"), ("H01", "2020 rails")]
ox = {"H29": (0, 22), "H30": (14, 44), "H31": (0, -10), "H13": (-10, -4), "H14": (0, 10), "H16": (0, -10), "H15": (6, 4)}
for i, (pid, label) in enumerate(NUM, 1):
    if pid not in mk: continue
    px, py = mk[pid]
    x = 0.3 + px / 2400 * EX_W + ox.get(pid, (0, 0))[0] / 2400 * EX_W
    y = 0.95 + py / 1400 * EX_H + ox.get(pid, (0, 0))[1] / 1400 * EX_H
    c = rect(sl, x - 0.11, y - 0.11, 0.22, 0.22, RED, WHITE, 1.0, MSO_SHAPE.OVAL)
    tf = c.text_frame; tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER; r = p.add_run(); r.text = str(i); r.font.size = Pt(7.5); r.font.bold = True; r.font.color.rgb = WHITE; r.font.name = "Calibri"
panel(sl, 9.55, 0.95, 3.3, 5.95, "PARTS", [(f"{i}   {l}", dict(size=8.5, space=0.8)) for i, (_, l) in enumerate(NUM, 1)]
      + [("Not shown: control box, water bath, puller, dancer, level-wind, spooler (sheets 12, 13, 15).", dict(size=8, color=GREY, space=0))])
tb(sl, 0.35, 0.95 + EX_H + 0.1, 9.0, 0.9, ["Exploded along the screw axis; the hopper is lifted in three pieces (cone, drum, lid frame), heater bands, guard and screw are lifted for clarity.",
                                          "Orange = 3D-printed, grey = bought hardware, dark = heaters / motors. Thrust is carried by 8-9-10-5-7-11-12 and the four rods (sheet 10)."], 10, False, GREY)
'''

S7v = sub(R("s4"), [('"Hopper\\n2.7 L"', '"Hopper 6.4 L\\n+ agitator"'), ('"Cooling\\ntrough + fans"', '"Water bath\\n+ puller"'), ('"Puller\\n30 mm rollers", "Dancer arm\\n→ spooler", "1 kg spool\\n≈ 335 m"', '"Dancer arm\\n+ level-wind", "Spool stepper", "1 kg spool\\n≈ 335 m"'),
    ('"air OK ≤ 1 m/min"', '"bath"'), ('"air ≤ 1 m/min, bath better"', '"bath"'), ('"air OK"', '"bath, short"'), ('"air, slow (≤ 0.6 m/min)"', '"bath, slow (≤ 0.6 m/min)"'), ('"water bath (M3)"', '"bath + fast quench"'), ('"water bath helps"', '"bath"')])
S7v = S7v.replace('steps = ["Scrap\\nflakes ≤ 4 mm", "Dry\\n(per material)", "Hopper 6.4 L\\n+ agitator", "Screw + barrel\\n4 PID zones", "Die Ø2.2\\n+ filter screen", "Water bath\\n+ puller", "Dancer arm\\n+ level-wind", "Spool stepper", "1 kg spool\\n≈ 335 m"]',
                  'steps = ["Scrap\\nflakes ≤ 4 mm", "Dry\\n(per material)", "Hopper 6.4 L\\n+ agitator", "Screw + barrel\\n4 PID zones", "Die Ø2.2\\n+ filter screen", "Water bath\\n+ puller", "Dancer arm\\n+ level-wind", "Spool stepper", "1 kg spool\\n≈ 335 m"]')

S8v = R("s5"); S9v = R("s6").replace("sheet-6 drawing", "sheet-9 drawing")
S10v = sub(R("s7"), [('"≈ 19 Nm", "stall limit at ≈ 1.6 A driver current – a mechanical fuse for the 8 mm screw core (≈ 20 Nm)"', '"≈ 14.6 Nm", "stall limit at 1.2 A driver current = 145 MPa in the 8 mm core (Rev A: 19 Nm, 193 MPa)"')])
S11v = R("s8")
S16v = sub(R("s12"), [("Heat to the setpoints on sheet 4", "Heat to the setpoints on sheet 7"),
    ('"3  Wait for a steady strand; pull by hand with pliers and thread it through the trough to the puller."', '"3  Fill the bath to the overflow barb, start the pump; pull the first strand by hand through the notches, under both sheaves, to the puller."'),
    ('"5  Hang the strand over the dancer, wind 3 turns on the spool core, engage the spooler."', '"5  Hang the strand under the dancer, wind 3 turns on the spool core, start the spool + level-wind."')])
S17 = '''
# =============================================================================================== 17 BOM
sl = new_slide("BILL OF MATERIALS")
n = 0; flat = []
for r in BOM:
    if r[1] is None: flat.append(("grp", r[0]))
    else:
        n += 1; flat.append(("row", n, r))
split = next(i for i, it in enumerate(flat) if it[0] == "grp" and it[1].startswith("Hopper"))
def mk_rows(items):
    rows = [["#", "Part", "Qty", "Size / note", "Est. $"]]; groups = []
    for it in items:
        if it[0] == "grp": rows.append(["", it[1].upper(), "", "", ""]); groups.append(len(rows) - 1)
        else:
            _, nn, r = it; rows.append([nn, r[0], r[1], r[2], f"{r[3]}–{r[4]}" if r[4] else "0"])
    return rows, groups
lr, lg = mk_rows(flat[:split]); rr, rg = mk_rows(flat[split:])
for rows_, xx, grp in ((lr, 0.4, lg), (rr, 6.75, rg)):
    t = table(sl, xx, 0.88, 6.2, [0.3, 2.7, 0.55, 2.3, 0.75], rows_, size=6.8, row_h=0.185, zebra=False)
    for rr_ in t.rows:
        for c in rr_.cells: c.margin_top = c.margin_bottom = Inches(0.005)
    for gi in grp:
        for j in range(5):
            c = t.cell(gi, j); c.fill.solid(); c.fill.fore_color.rgb = BORD
            for p in c.text_frame.paragraphs:
                for rn in p.runs: rn.font.bold = True
tb(sl, 0.4, 6.1, 6.2, 0.9, [f"Estimated purchase total ≈ ${LOW:,}–${HIGH:,} (typical online listings, not quotes; shipping and tax excluded). Printed parts use your own filament.",
                               "Rev B adds ≈ $60–160 over Rev A ($497–899): 2 steppers + drivers, lead screw, pump + bucket, agitator motor, bearings. Reuse the donor Vyper's NEMA 17 and PSU parts to cut it."], 9.5, False, GREY)
'''
S18 = sub(R("s14"), [('["Heat gun (optional)", "pre-form the heat guard, shrink tube", "hair-dryer is not enough; use an oven mitt and patience"]]',
                      '["Aquarium silicone + a tray", "seal and water-test the bath (P11, P12)", "let it cure 24 h; test with water over a tray, away from electronics"]]'),
    ("bring the parts and the sheet-6 drawing", "bring the parts and the sheet-9 drawing")])

out = HEADER + DATA + S1 + S2 + S3 + S2v.replace("# ====", "# ====") + S3x + S6 + S7v + S8v + S9v + S10v + S11v + S12 + S13 + S14 + S15 + S16v + S17 + S18 + S19 + S20
# remove the old data-less duplicate of r4 defined in HEADER + old
open("build_deck.py", "w").write(out)
print("written", len(out.split("\n")), "lines")

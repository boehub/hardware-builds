"""Assemble the blueprint deck (python-pptx).  Run with any python that has python-pptx + the repo modules."""
import json, os, sys, math
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.oxml.ns import qn
from lxml import etree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fm_params import P
import fm_calc as C

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = HERE + "/out/img/"
OUTF = HERE + "/out/filament_maker_blueprint.pptx"
INK, RED, PANEL, BORD, GREY, DK2, GOLD, BLUE = (RGBColor.from_string(x) for x in ("222222", "A5001E", "F5F5F5", "D5DBE3", "6B7785", "36454F", "C79A3B", "2563C4"))
WHITE = RGBColor(255, 255, 255)
FOOT = "All dimensions in mm  |  Printed parts PETG/ASA + off-the-shelf hardware, hand-tool assembly  |  Name: Ryan Boe"

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
BLANK = prs.slide_layouts[6]
_n = [0]

def tb(sl, x, y, w, h, text, size=10, bold=False, color=INK, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, italic=False, wrap=True):
    s = sl.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = s.text_frame; tf.word_wrap = wrap
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    lines = text if isinstance(text, list) else [text]
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        r = p.add_run(); r.text = ln
        r.font.size = Pt(size); r.font.bold = bold; r.font.italic = italic; r.font.color.rgb = color; r.font.name = "Calibri"
    return s

def rich(sl, x, y, w, h, paras, size=9.5, space=3, color=INK):
    """paras: list of str or (str, dict(bold,color,bullet,size))"""
    s = sl.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = s.text_frame; tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    first = True
    for item in paras:
        t, o = (item, {}) if isinstance(item, str) else item
        p = tf.paragraphs[0] if first else tf.add_paragraph(); first = False
        p.space_after = Pt(o.get("space", space))
        bullet = o.get("bullet", False)
        txt = ("•  " + t) if bullet else t
        # allow **bold** lead-in using '||' separator
        if "||" in txt:
            a, b = txt.split("||", 1)
            r = p.add_run(); r.text = a; r.font.bold = True; r.font.size = Pt(o.get("size", size)); r.font.color.rgb = o.get("color", color); r.font.name = "Calibri"
            r = p.add_run(); r.text = b; r.font.size = Pt(o.get("size", size)); r.font.color.rgb = o.get("color", color); r.font.name = "Calibri"
        else:
            r = p.add_run(); r.text = txt; r.font.size = Pt(o.get("size", size)); r.font.bold = o.get("bold", False)
            r.font.color.rgb = o.get("color", color); r.font.name = "Calibri"
        if bullet:
            pPr = p._p.get_or_add_pPr(); pPr.set("marL", str(int(Inches(0.16)))); pPr.set("indent", str(-int(Inches(0.16))))
    return s

def rect(sl, x, y, w, h, fill=PANEL, line=BORD, lw=0.75, shape=MSO_SHAPE.RECTANGLE):
    s = sl.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if fill is None: s.fill.background()
    else: s.fill.solid(); s.fill.fore_color.rgb = fill
    if line is None: s.line.fill.background()
    else: s.line.color.rgb = line; s.line.width = Pt(lw)
    s.shadow.inherit = False
    return s

def panel(sl, x, y, w, h, heading, paras, size=9.5, hsize=10.5):
    rect(sl, x, y, w, h)
    tb(sl, x + 0.14, y + 0.1, w - 0.28, 0.25, heading, hsize, True)
    rich(sl, x + 0.14, y + 0.4, w - 0.28, h - 0.5, paras, size)

def stat(sl, x, y, w, h, big, small, bsize=24):
    rect(sl, x, y, w, h)
    tb(sl, x + 0.15, y + 0.08, w - 0.3, 0.45, big, bsize, True, RED)
    tb(sl, x + 0.15, y + 0.08 + bsize / 72 * 1.25, w - 0.3, h - 0.6, small, 9.5, False, INK)

def new_slide(title):
    sl = prs.slides.add_slide(BLANK); _n[0] += 1
    tb(sl, 0.5, 0.2, 12.33, 0.55, title, 26, True, INK, PP_ALIGN.CENTER, MSO_ANCHOR.MIDDLE)
    tb(sl, 0.5, 7.1, 9.5, 0.25, FOOT, 9, True, INK)
    tb(sl, 12.3, 7.1, 0.55, 0.25, str(_n[0]), 9, False, GREY, PP_ALIGN.RIGHT)
    return sl

def pic(sl, name, x, y, w=None, h=None):
    kw = {}
    if w: kw["width"] = Inches(w)
    if h: kw["height"] = Inches(h)
    return sl.shapes.add_picture(IMG + name, Inches(x), Inches(y), **kw)

def table(sl, x, y, w, col_w, rows, size=8, row_h=0.26, header=True, hfill=DK2, bold_first=False, zebra=True, aligns=None):
    nr, nc = len(rows), len(rows[0])
    gs = sl.shapes.add_table(nr, nc, Inches(x), Inches(y), Inches(w), Inches(row_h * nr))
    t = gs.table
    tblPr = gs._element.graphic.graphicData.tbl.tblPr
    for a in ("bandRow", "firstRow"): tblPr.set(a, "0")
    sid = tblPr.find(qn("a:tableStyleId"))
    if sid is not None: sid.text = "{5940675A-B579-460E-94D1-54222C63F5DA}"   # no style, table grid
    tot = sum(col_w)
    for j, cw in enumerate(col_w): t.columns[j].width = Inches(w * cw / tot)
    for i, r in enumerate(rows):
        t.rows[i].height = Inches(row_h)
        for j, v in enumerate(r):
            c = t.cell(i, j); c.margin_left = c.margin_right = Inches(0.05); c.margin_top = c.margin_bottom = Inches(0.02)
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf = c.text_frame; tf.word_wrap = True
            p = tf.paragraphs[0]
            p.alignment = (aligns[j] if aligns else PP_ALIGN.LEFT)
            run = p.add_run(); run.text = str(v); run.font.size = Pt(size); run.font.name = "Calibri"
            if header and i == 0:
                run.font.bold = True; run.font.color.rgb = WHITE
                c.fill.solid(); c.fill.fore_color.rgb = hfill
            else:
                run.font.color.rgb = INK
                if bold_first and j == 0: run.font.bold = True
                c.fill.solid(); c.fill.fore_color.rgb = PANEL if (zebra and i % 2 == 0) else WHITE
            # thin borders
            tcPr = c._tc.get_or_add_tcPr()
            for tag in ("a:lnL", "a:lnR", "a:lnT", "a:lnB"):
                ln = etree.SubElement(tcPr, qn(tag), w="6350")
                sf = etree.SubElement(ln, qn("a:solidFill")); etree.SubElement(sf, qn("a:srgbClr"), val="D5DBE3")
    return t

def arrow(sl, x1, y1, x2, y2, color=INK, lw=1.25, head=True):
    c = sl.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    c.line.color.rgb = color; c.line.width = Pt(lw)
    if head:
        ln = c.line._get_or_add_ln()
        te = etree.SubElement(ln, qn("a:tailEnd")); te.set("type", "triangle"); te.set("w", "med"); te.set("len", "med")
    return c

def box(sl, x, y, w, h, text, fill=WHITE, line=INK, size=8.5, bold=False, color=INK, lw=0.9):
    s = rect(sl, x, y, w, h, fill, line, lw)
    tf = s.text_frame; tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.04); tf.margin_top = tf.margin_bottom = Inches(0.02)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    lines = text if isinstance(text, list) else [text]
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph(); p.alignment = PP_ALIGN.CENTER
        r = p.add_run(); r.text = ln; r.font.size = Pt(size); r.font.bold = bold if i == 0 else False; r.font.color.rgb = color; r.font.name = "Calibri"
    return s


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
import re

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
# =============================================================================================== 2 views
sl = new_slide("ASSEMBLY VIEWS – OVERALL SIZE")
picfit(sl, "d_views.png", 0.75, 0.85, 11.8, 5.6)
tb(sl, 0.75, 6.5, 11.8, 0.55, ["The line is modular: rails of module 1 (895), 2 (540) and 3 (395) are separate pieces, so the machine can be set up in an L-shape or folded later (M7).",
                                "The control box can sit anywhere; only the four heater leads, motor cables and the dancer pot lead have to reach it."], 10, False, GREY)


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
# =============================================================================================== 4 process + materials
sl = new_slide("PROCESS + MATERIAL SETTINGS")
steps = ["Scrap\nflakes ≤ 4 mm", "Dry\n(per material)", "Hopper 6.4 L\n+ agitator", "Screw + barrel\n4 PID zones", "Die Ø2.2\n+ filter screen", "Water bath\n+ puller", "Dancer arm\n+ level-wind", "Spool stepper", "1 kg spool\n≈ 335 m"]
bw, gap = 1.22, 0.16
for i, s_ in enumerate(steps):
    x = 0.5 + i * (bw + gap)
    box(sl, x, 1.0, bw, 0.62, s_.split("\n"), PANEL, BORD, 9, True)
    if i < len(steps) - 1: arrow(sl, x + bw, 1.31, x + bw + gap, 1.31, RED, 1.5)
rows = [["Material", "Z1 (feed)", "Z2", "Z3", "Z4 / die", "Dry before", "Cooling", "Notes"],
        ["PLA", "150", "170", "185", "190", "45–50 °C, 4 h if damp", "bath", "easiest first run; mixes of colours give a muddy but fine filament"],
        ["PETG", "190", "215", "230", "235", "65 °C, 4–6 h", "bath", "wet PETG foams and breaks – dry it; slightly stringy"],
        ["ABS / ASA", "190", "210", "225", "230", "80 °C, 2–4 h", "bath, short", "fumes: ventilate. Print-scrap ABS shrinks – keep drawdown low"],
        ["TPU 95A", "160", "185", "200", "205", "60 °C, 4 h", "bath, slow (≤ 0.6 m/min)", "soft: use the puller pressure spring lightly; screw ≤ 3 rpm"],
        ["PET (bottles)", "230", "250", "265", "270", "120–160 °C, ≥ 4 h", "bath + fast quench", "hard mode: needs drying + fast quench or it turns brittle / hazy"],
        ["PP / HDPE", "165", "185", "200", "205", "none", "bath", "slippery on the screw; shrinks on cooling – wide tolerance"]]
tb(sl, 0.5, 1.85, 8, 0.25, "STARTING SETPOINTS (°C) – tune with the first test strand; thermocouples read under the band, so the melt is a few degrees cooler", 10, True)
table(sl, 0.5, 2.15, 12.33, [1.0, 0.65, 0.5, 0.5, 0.75, 1.55, 1.6, 4.6], rows, size=9, row_h=0.34, bold_first=True)
panel(sl, 0.5, 4.75, 6.05, 2.2, "RULES THAT SAVE A RUN", [
    ("Flakes ≤ 4 mm, no dust.|| Fines melt first and clog the screen; sieve them out or mix back in small amounts.", dict(bullet=True)),
    ("One material and one colour family per batch.|| Mixed polymers (PLA + PETG) will not make good filament.", dict(bullet=True)),
    ("Dry what you can.|| 1 kg of damp PETG is the #1 reason for bubbles and diameter swings.", dict(bullet=True)),
    ("Purge between materials|| with the lower-temperature one, then raise the zones.", dict(bullet=True))], 9.5)
panel(sl, 6.75, 4.75, 6.08, 2.2, "HARD LIMIT FOR PHASE 1: 280 °C", [
    ("Band heaters, thermocouples and PTFE/silicone wiring are all chosen for ≤ 280–300 °C.", dict(bullet=True)),
    ("Printed parts must stay below ≈ 70 °C (PETG) – check the head plate and bearing housing with an IR thermometer on the first PET run.", dict(bullet=True)),
    ("PC, nylon 66, PEI and the like need ≥ 290 °C: not in scope.", dict(bullet=True)),
    ("Temperatures here are typical extrusion values, not measured on this machine – VERIFY on the first run.", dict(bullet=True, color=RED))], 9.5)

# =============================================================================================== 5 barrel
sl = new_slide("SCREW + BARREL – SECTION THROUGH THE SCREW AXIS")
pic(sl, "d_barrel.png", 0.5, 0.85, w=12.33)
bh = 12.33 * 3.95 / 12.3
y0 = 0.85 + bh + 0.08
panel(sl, 0.5, y0, 7.6, 7.0 - y0, "DESIGN NOTES", [
    ("Barrel:|| 3/4 in Sch 40 stainless nipple (ID 20.93) over a Ø20.0 screw – 0.47 mm radial clearance; a wood-type auger wears, so plan on replacing it (M1).", dict(bullet=True)),
    ("Everything is threaded pipe:|| flange → close nipple → tee → 12 in nipple → cap. PTFE tape on the cold joints, nickel anti-seize on the hot end; re-tighten once after the first heat cycle.", dict(bullet=True)),
    ("Screw prep with hand tools:|| hacksaw ~30 mm off the lead tip, file the end round, polish the flights 400 → 2000 grit so plastic does not stick. Confirm 7/16 in hex shank and ≈ 8 mm core (VERIFY).", dict(bullet=True)),
    ("Heat:|| bands are 28 mm ID on a 26.67 mm OD barrel – wrap 0.2 mm aluminium shim for contact; clamp each thermocouple under the band edge. Cold feed zone (89 mm) + small fan keeps flakes from melting in the throat.", dict(bullet=True))], 9)
rows = [["Zone", "X (mm)", "Power", "Job"], ["Z1", "413–463", "200 W", "soften, still solid-conveying"], ["Z2", "468–518", "200 W", "melt"],
        ["Z3", "523–573", "200 W", "homogenise"], ["Z4", "578–628", "200 W", "die zone, sets output temp"]]
table(sl, 8.3, y0 + 0.05, 4.53, [0.6, 1.0, 0.8, 2.6], rows, size=9, row_h=0.28, bold_first=True)
tb(sl, 8.3, y0 + 1.55, 4.5, 0.8, ["Total heater power 800 W at 120 V = 6.7 A. Ideal warm-up 112 kJ → ≈ 2.5 min; plan on 8–12 min with losses.",
                                  "Steady running needs only ≈ 150–250 W (melt load is 20–40 W, the rest is loss)."], 9, False, GREY)

# =============================================================================================== 6 die
sl = new_slide("DIE + FILTER")
pic(sl, "d_die.png", 0.5, 0.95, w=6.4)
stat(sl, 7.15, 0.95, 2.75, 1.1, f"{C.die_dp(r4['q'])/1e6:.1f} MPa", "estimated die pressure at 4 rpm (η = 1000 Pa·s, Ø2.2 × 14 land); ×2–3 with a loaded screen", 22)
stat(sl, 10.05, 0.95, 2.78, 1.1, f"{C.draw:.2f} ×", "draw-down: puller runs 1.6× faster than the strand leaves the Ø2.2 die (plus die swell)", 22)
panel(sl, 7.15, 2.2, 5.68, 4.75, "BUILDING THE DIE WITH HAND TOOLS", [
    ("Die plug:|| M10×1.5 brass hex bolt, 16 mm long. Centre-punch the shank, clamp it in a vice, drill 2.0 mm all the way along the axis with a hand drill, then 2.2 mm. Use cutting oil.", dict(bullet=True)),
    ("Entry cone:|| a 6 mm drill, 6 mm deep, in the inside end – the plastic must funnel into the ×2.2 land.", dict(bullet=True)),
    ("Cap:|| drill 8.5 mm through the middle of a brass 3/4 NPT cap, tap M10×1.5, screw the plug in with high-temp paste. A machine shop can do the plug + cap for a few dollars if the hand-drilling wanders.", dict(bullet=True)),
    ("Filter:|| 60–100 mesh stainless disc cut with scissors, sandwiched against the cap wall – stops grit and un-melted flakes from plugging the die.", dict(bullet=True)),
    ("Spares:|| make three plugs (×2.0, 2.2, 2.5). Small die = less swell, more pressure; big die = more draw-down.", dict(bullet=True)),
    ("Safety:|| never open a hot, pressurised die. Stop the screw, let it cool until the plug can be touched, then unscrew. Clean a blocked die by drilling the plastic out with the same bit.", dict(bullet=True, color=RED)),
], 9.5)
tb(sl, 0.5, 5.2, 6.4, 1.6, ["Why 14 mm of land? A longer land evens out the flow and straightens the strand. Pressure scales with L/D⁴, so shorten it (8 mm) if the motor skips steps.",
                             "Target diameter 1.75 ± 0.05 mm is set by the puller speed, not the die; measure with calipers every 10 cm for the first metre."], 10, False, GREY)

# =============================================================================================== 7 drive
sl = new_slide("DRIVE TRAIN + THRUST LOOP")
pic(sl, "d_drive.png", 0.5, 0.88, w=12.33)
dh = 12.33 * 4.3 / 12.3
y0 = 0.88 + dh + 0.08
stat(sl, 0.5, y0, 2.35, 1.15, "20 : 1", "planetary: 2–30 rpm at the screw for 40–600 rpm at the motor", 22)
stat(sl, 3.0, y0, 2.35, 1.15, "≈ 14.6 Nm", "stall limit at 1.2 A driver current = 145 MPa in the 8 mm core (Rev A: 19 Nm, 193 MPa)", 22)
stat(sl, 5.5, y0, 2.35, 1.15, "1.6–3.1 kN", "thrust at 5–10 MPa melt pressure, carried by the thrust bearing, not the gearbox", 22)
panel(sl, 8.0, y0, 4.83, 7.0 - y0, "DIRECTION + COUPLING (the one trap)", [
    ("A drill auger pumps chips toward the shank when turned clockwise, so we spin the screw counter-clockwise (seen from the motor) to push plastic toward the die.", dict(size=9)),
    ("That direction tends to unscrew the chuck from its ½-20 spindle: Loctite 638 on the thread, tighten the chuck against the collar, and fit the chuck retaining screw (left-hand) – VERIFY. Fallback: file a square drive on the spindle and use a 7/16 in socket.", dict(size=9, color=RED))], 9)

# =============================================================================================== 8 printed parts
sl = new_slide("PRINTED PARTS – MOTOR WALL, BEARING HOUSING, HEAD PLATE")
pic(sl, "d_printed.png", 0.5, 0.85, w=12.33)
ph_ = 12.33 * 3.95 / 12.3
y0 = 0.85 + ph_ + 0.1
rows = [["Setting", "Value", "Why"], ["Material", "PETG (ASA near hot parts)", "PLA softens at ≈ 55 °C – do not use it for these"], ["Walls / infill", "6 perimeters, 60 % gyroid", "load goes through bolts and rods, not infill"],
        ["Layer / nozzle", "0.2 mm / 0.4 mm", "fine enough for bearing seats"], ["Orientation", "plate face down (X up); wall on its side", "layers lie in the thrust plate instead of across it"]]
table(sl, 0.5, y0, 7.2, [1.1, 2.3, 3.8], rows, size=9, row_h=0.3, bold_first=True)
panel(sl, 7.9, y0, 4.93, 7.0 - y0, "FIT NOTES", [
    ("Bearing seats print ×28.8 for a ×28.575 R8 – test-print a 10 mm slice first and ream with a rolled sandpaper if tight.", dict(bullet=True)),
    ("Foot slots: M5 T-nuts into the 2020 rails, two per foot minimum.", dict(bullet=True)),
    ("Press the thrust washer into the ×30.4 seat, not the bearing balls.", dict(bullet=True))], 9)


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
# =============================================================================================== 11 electrical
sl = new_slide("ELECTRICAL BLOCK DIAGRAM + SAFETY CHAIN")
tb(sl, 0.5, 0.88, 8, 0.25, "POWER + E-STOP (hardware path)", 10.5, True)
xs = [0.5, 2.45, 4.4, 6.35]
labels = [["Mains 120 V AC", "15 A circuit, GFCI"], ["Breaker / fuse", "10 A, IEC inlet"], ["E-stop (NC)", "mushroom, front panel"], ["Contactor", "coil on the E-stop loop"]]
for x, l in zip(xs, labels): box(sl, x, 1.2, 1.7, 0.6, l, WHITE, INK, 8.5, True)
for i in range(3): arrow(sl, xs[i] + 1.7, 1.5, xs[i + 1], 1.5)
# heater branch
tb(sl, 0.5, 1.93, 6, 0.25, "HEATERS (120 V AC, 800 W)", 10.5, True)
box(sl, 0.5, 2.45, 1.7, 0.6, ["Thermal fuse 280 °C", "in series, on barrel Z3"], WHITE, RED, 8.5, True)
box(sl, 2.45, 2.45, 1.7, 0.6, ["4 × SSR-25DA", "zero-cross, heat-sinked"], WHITE, INK, 8.5, True)
box(sl, 4.4, 2.45, 1.7, 0.6, ["4 × band heater", "200 W each"], WHITE, INK, 8.5, True)
arrow(sl, 7.2, 1.8, 7.2, 2.3, INK); line_x = sl.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(7.2), Inches(2.3), Inches(1.35), Inches(2.3)); line_x.line.color.rgb = INK; line_x.line.width = Pt(1.25)
arrow(sl, 1.35, 2.3, 1.35, 2.45); arrow(sl, 2.2, 2.75, 2.45, 2.75); arrow(sl, 4.15, 2.75, 4.4, 2.75)
box(sl, 2.45, 3.25, 1.7, 0.5, ["4 × REX-C100 PID", "SSR output"], PANEL, INK, 8.5, True)
box(sl, 4.4, 3.25, 1.7, 0.5, ["4 × K thermocouple", "under each band"], PANEL, INK, 8.5, True)
arrow(sl, 3.3, 3.25, 3.3, 3.05, BLUE); arrow(sl, 4.4, 3.5, 4.15, 3.5, BLUE)
# DC branch
tb(sl, 0.5, 3.85, 6, 0.25, "MOTION + LOGIC (24 V DC)", 10.5, True)
box(sl, 0.5, 4.4, 1.5, 0.6, ["24 V 10 A PSU", "after contactor"], WHITE, INK, 8.5, True)
arrow(sl, 7.2, 1.8, 7.2, 4.25, INK); l2 = sl.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(7.2), Inches(4.25), Inches(1.25), Inches(4.25)); l2.line.color.rgb = INK; l2.line.width = Pt(1.25); arrow(sl, 1.25, 4.25, 1.25, 4.4)
drv = [("DM542T → NEMA 23", "screw, 1.2 A limit"), ("3 × TMC2209 → NEMA 17", "puller, spool, level-wind"), ("MOSFET → gearmotor", "hopper agitator"), ("MOSFET → pump", "water circulation"), ("40 mm fan", "feed throat, 24 V")]
for i, (a_, b_) in enumerate(drv):
    box(sl, 2.3, 4.3 + i * 0.34, 2.0, 0.3, [a_, b_], WHITE, INK, 7, True)
    arrow(sl, 2.0, 4.7, 2.3, 4.45 + i * 0.34, INK, 1.0)
box(sl, 4.8, 4.35, 1.7, 1.2, ["Arduino Nano", "5 V from buck", "STEP/DIR/EN, PWM"], PANEL, INK, 8.5, True)
for i in range(5): arrow(sl, 4.8, 4.4 + i * 0.22, 4.3, 4.45 + i * 0.34, BLUE, 0.8)
box(sl, 6.7, 4.35, 1.4, 1.2, ["Inputs", "2 pots, FWD/OFF/REV,", "dancer pot, driver ALM,", "PID ready (AL)"], WHITE, GREY, 7.5, True)
arrow(sl, 6.7, 4.95, 6.5, 4.95, BLUE)
panel(sl, 8.4, 0.88, 4.43, 3.35, "SAFETY CHAIN", [
    ("E-stop and contactor are pure hardware: the contactor drops both the heaters and the 24 V supply – no software in the loop.", dict(bullet=True)),
    ("Thermal fuse (280 °C) sits in the heater feed; it cuts power even if an SSR welds shut.", dict(bullet=True)),
    ("The Nano refuses to start the screw until Z3 and Z4 are within ±10 °C of setpoint (wire the PID alarm output to an input – VERIFY the REX-C100 variant has an ALM relay).", dict(bullet=True)),
    ("Driver current limit (1.2 A ≈ 14.6 Nm) lets the stepper skip steps on a jam instead of twisting the screw.", dict(bullet=True))], 9)
panel(sl, 8.4, 4.35, 4.43, 2.6, "DO THIS FIRST", [
    ("Have the 120 V side wired or checked by someone who does mains work. This sheet is a plan, not a certified design.", dict(bullet=True, color=RED)),
    ("Keep mains and 24 V wiring in separate bundles; use ferrules and a ground lug on the barrel.", dict(bullet=True)),
    ("Never leave it heating unattended until you trust the thermal fuse and the PIDs. Water + mains: GFCI, bucket and pump away from the control box and below its level, drip loop on every cable.", dict(bullet=True))], 9)
panel(sl, 0.5, 6.05, 7.6, 0.95, "CONTROL (NANO)", [
    ("Screw: STEP rate from knob 1 (40–600 motor rpm).  Puller: STEP rate = ratio × screw rate, knob 2 trims ±15 %.  Spool stepper: rpm = strand speed ÷ pack circumference, trimmed by the dancer pot.  Level-wind: 700 micro-steps per spool turn, reverses at ±28 mm.", dict(size=8)),
    ("Jam: driver ALM → stop, reverse 2 s, stop. Heat-not-ready → screw disabled. Pump runs whenever the line is on; keep it on a GFCI outlet.", dict(size=8))], 9)

# =============================================================================================== 12 speeds
sl = new_slide("SPEEDS + DIAL-IN")
pic(sl, "d_speed.png", 0.5, 0.95, w=6.4)
rows = [["Screw rpm", "Motor rpm", "Output g/h", "Filament m/min", "Hours per kg"]]
for N in (2, 3, 4, 5, 6, 8):
    r = C.row(N); rows.append([N, N * 20, f"{r['g_h']:.0f}", f"{r['v']:.2f}", f"{r['t_kg']:.1f}"])
table(sl, 7.2, 0.95, 5.63, [1, 1, 1, 1.3, 1.2], rows, size=9.5, row_h=0.3, bold_first=True, aligns=[PP_ALIGN.CENTER] * 5)
tb(sl, 7.2, 3.1, 5.6, 0.6, "Estimate: drag flow × 0.35 for pressure back-flow and leakage, PLA density. Calibrate once: weigh 1 m of strand at a known rpm and scale.", 9, False, GREY)
panel(sl, 7.2, 3.8, 5.63, 3.15, "DIAL-IN PROCEDURE (first run, ≈ 30 min)", [
    ("1  Heat to the setpoints on sheet 7, soak 10 min after the PIDs settle.", dict(size=9)),
    ("2  Set screw to 3 rpm; load a handful of virgin pellets or flakes.", dict(size=9)),
    ("3  Fill the bath to the overflow barb, start the pump; pull the first strand by hand through the notches, under both sheaves, to the puller.", dict(size=9)),
    ("4  Set puller so the strand reads 1.75 mm; adjust ±5 % at a time every minute.", dict(size=9)),
    ("5  Hang the strand under the dancer, wind 3 turns on the spool core, start the spool + level-wind.", dict(size=9)),
    ("6  Log rpm, puller speed and diameter every 5 min for the first spool.", dict(size=9))], 9)
panel(sl, 0.5, 5.7, 6.4, 1.25, "READING THE STRAND", [
    ("Bubbles / foam → wet material.  Hazy / rough → too cool or too fast.  Oval → uneven cooling, add fan time.", dict(bullet=True)),
    ("Diameter wave with the screw turn → feed starving (bridge in hopper) or worn flights.", dict(bullet=True)),
    ("Motor skipping → die too small or too cold; open the die or add 5 °C.", dict(bullet=True))], 9)


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
# =============================================================================================== 14 tools
sl = new_slide("TOOLS + WORKAROUNDS (no lathe, no drill press)")
rows = [["Tool / skill", "Used for", "If you do not have it"],
        ["Hacksaw + files + vice or clamps", "2020 rails, M8 rods, spindle, auger tip, heat-guard sheet", "buy rails and rods cut to length; auger tip: Dremel cut-off wheel"],
        ["Hand drill + 2.0 / 2.2 / 6 / 8.5 mm bits", "die hole + entry cone, cap pilot hole", "machine shop or maker space drills the plug + cap (≈ $10–20)"],
        ["M10 × 1.5 tap + wrench", "thread for the die plug in the cap", "buy a cap with a threaded centre, or a ready 1.75 mm die nozzle"],
        ["½-20 UNF die + stock", "thread on the spindle for the chuck", "use a Grade 8 ½-20 bolt/rod cut to length – no die needed"],
        ["2 pipe wrenches (or adjustable)", "NPT stack: flange, nipples, tee, cap", "none – borrow; do not hammer on stainless threads"],
        ["Hex keys, spanners, screwdrivers", "M5 / M8 hardware, coupler, collar", "–"],
        ["Calipers (0.01 mm)", "screw, bore, strand diameter", "1.75 mm drill bit as a go/no-go gauge until you buy them"],
        ["Multimeter + IR / contact thermometer", "wiring checks, calibrating the PIDs", "–"],
        ["Soldering iron, wire stripper, crimper", "pots, fans, thermocouple leads", "ferrules + screw terminals avoid soldering mains wires"],
        ["Aquarium silicone + a tray", "seal and water-test the bath (P11, P12)", "let it cure 24 h; test with water over a tray, away from electronics"]]
table(sl, 0.5, 0.95, 12.33, [3.0, 4.3, 5.0], rows, size=9.5, row_h=0.34, bold_first=True)
panel(sl, 0.5, 4.85, 6.05, 2.1, "THE PARTS THAT REALLY WANT A MACHINE", [
    ("Spindle thread and die hole are the two jobs where hand tools are marginal – both have a bought-part workaround above.", dict(bullet=True)),
    ("A local makerspace or machine shop can drill the die plug, tap the cap, and thread the spindle in 15 minutes – bring the parts and the sheet-9 drawing.", dict(bullet=True))], 9.5)
panel(sl, 6.75, 4.85, 6.08, 2.1, "PRINTING + FINISHING", [
    ("Printer: your Vyper (245 × 245 × 260). Print the housing and head plate first and test-fit bearings before printing the rest.", dict(bullet=True)),
    ("Sandpaper rolls for the bearing seats, a 8.5 mm drill to clean rod holes, heat-set M3/M5 inserts if you want the electronics box to open often.", dict(bullet=True))], 9.5)


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

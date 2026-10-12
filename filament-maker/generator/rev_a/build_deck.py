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

# =============================================================================================== data
r4 = C.row(4)
BOM = [
 ("Drive", None, None, None, None),
 ("NEMA 23 stepper, 3 Nm class, 4.2 A", 1, "57 × 57 × 112, 8 mm shaft", 35, 50),
 ("NEMA 23 planetary gearbox 20:1", 1, "60 mm flange, Ø14 output (VERIFY)", 50, 90),
 ("Stepper driver DM542T (or TB6600)", 1, "24–36 V, up to 4.2 A", 15, 25),
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
 ("Cooling / puller / spooler", None, None, None, None),
 ("40 mm fan 24 V", 5, "4 cooling + 1 feed throat", 15, 25),
 ("NEMA 17 stepper (puller)", 1, "spare from donor Vyper?", 0, 15),
 ("TMC2209 (or A4988) driver", 1, "1/16 micro-step", 6, 10),
 ("37 mm gearmotor 24 V 12 rpm", 1, "6 mm D-shaft + hub", 12, 20),
 ("10 kΩ linear pot + MOSFET PWM board", 2, "dancer sensor / spool drive", 5, 10),
 ("Electronics & frame", None, None, None, None),
 ("Arduino Nano", 1, "5 V logic", 6, 15),
 ("24 V 10 A PSU", 1, "240 W", 20, 30),
 ("Contactor 24 V coil + E-stop NC", "1 set", "hardware safety chain", 15, 30),
 ("Breaker, IEC inlet, wire, terminals", "1 set", "120 V side, ferrules", 20, 35),
 ("Knobs, toggle, lamp", "1 set", "front panel", 6, 12),
 ("2020 extrusion + T-nuts + screws", "6 rails", "895 ×2, 540 ×2, 310 ×2", 45, 78),
 ("Hose clamp, PTFE tape, Ni anti-seize", "1 set", "hopper joint, NPT threads", 8, 15),
 ("Printed parts, PETG / ASA / TPU", "≈ 1.8 kg", "sheet 9", 0, 40),
]
LOW = sum(r[3] for r in BOM if r[3] is not None); HIGH = sum(r[4] for r in BOM if r[4] is not None)

# =============================================================================================== 1 overview
sl = new_slide("DIY FILAMENT MAKER – BLUEPRINT SET (FOUNDATION BUILD)")
tb(sl, 0.45, 0.95, 7.5, 0.25, "FULL LINE – extruder, cooling, puller, dancer, 1 kg spooler; control box on the left", 12, True)
pic(sl, "hero_all.png", 0.35, 1.25, w=7.7)
stat(sl, 8.3, 0.95, 2.2, 1.12, "1 kg → 1 kg", "flakes in, 1.75 mm filament on a 1 kg spool out (≈ 335 m of PLA)", 22)
stat(sl, 10.65, 0.95, 2.2, 1.12, f"≈ {r4['t_kg']:.1f} h / kg", f"at 4 rpm: ≈ {r4['v']:.1f} m/min, ≈ {r4['g_h']:.0f} g/h (estimate, calibrate)", 22)
stat(sl, 8.3, 2.2, 2.2, 1.12, "Ø20 × 365", "auger screw, L/D 18, in a 3/4 in stainless barrel", 22)
stat(sl, 10.65, 2.2, 2.2, 1.12, "4 zones", "PID bands, 150–280 °C: PLA, PETG, ABS, PET, TPU …", 22)
idx = ["1  Overview", "2  Assembly views + overall size", "3  Exploded view + part numbers", "4  Process + material settings", "5  Screw + barrel (section)",
       "6  Die + filter", "7  Drive train + thrust loop", "8  Printed parts: wall, housing, head plate", "9  Printed parts: hopper, trough + print list",
       "10  Cooling, puller, dancer, spooler", "11  Electrical + safety", "12  Speeds + dial-in", "13  Bill of materials", "14  Tools + workarounds",
       "15  Assembly order + design checks", "16  Open items (VERIFY) + modification roadmap"]
panel(sl, 8.3, 3.45, 4.55, 3.5, "SHEET INDEX", [(t, dict(size=9.5, space=1.5)) for t in idx])
tb(sl, 0.45, 5.55, 7.6, 0.25, "Models: filament_maker_assembly.fbx (Blender)  ·  Print files: filament_maker_stl.zip  ·  Generator: fm_params.py + fm_model.py", 10, False, GREY)
tb(sl, 0.45, 5.85, 7.6, 0.5, ["Foundation first: everything here is buildable with a 3D printer, off-the-shelf parts and hand tools. Phase-2 upgrades are on sheet 16.",
                              "Dimensions marked VERIFY come from catalogue-typical sizes, not from parts in hand – see sheets 15 and 16."], 10, False, GREY)

# =============================================================================================== 2 views
sl = new_slide("ASSEMBLY VIEWS – OVERALL SIZE")
pic(sl, "d_views.png", 0.75, 0.88, w=11.8)
tb(sl, 0.75, 6.5, 11.8, 0.55, ["The line is modular: rails of module 1 (895), 2 (540) and 3 (310) are separate pieces, so the machine can be set up in an L-shape or folded later (M7).",
                                "The control box can sit anywhere; only the four heater leads, motor cables and the dancer pot lead have to reach it."], 10, False, GREY)

# =============================================================================================== 3 exploded
sl = new_slide("EXPLODED VIEW – PART NUMBERS")
EX_W = 9.1
pic(sl, "exploded.png", 0.3, 1.0, w=EX_W)
EX_H = EX_W * 1000 / 2400
mk = json.load(open(IMG + "exploded_markers.json"))
NUM = [("H10", "NEMA 23 stepper"), ("H11", "Planetary gearbox 20:1"), ("P01", "Motor wall (printed)"), ("H12", "Clamp coupler"), ("H13", "Spindle ½ in"),
       ("H14", "R8 bearings (2)"), ("P02", "Bearing housing + thrust flange"), ("H15", "Thrust bearing"), ("H16", "Shaft collar"), ("H17", "13 mm chuck"),
       ("H21", "M8 tie rods (4)"), ("P03", "Head plate (printed)"), ("H20", "Auger screw Ø20"), ("H22", "Floor flange 3/4 NPT"), ("H23", "Close nipple"),
       ("H24", "Pipe tee (feed port)"), ("H25", "Feed nipple 2 in"), ("P04", "Hopper 2.7 L + lid"), ("H26", "Barrel nipple 12 in SS"), ("H27", "Cap (die body)"),
       ("H28", "Die plug Ø2.2"), ("H29", "Band heaters (4)"), ("H30", "Thermocouples (4)"), ("H31", "Heat guard"), ("H32", "Barrel strap + post"),
       ("H34", "Feed-throat fan"), ("H01", "2020 rails")]
ox = {"H29": (0, 22), "H30": (14, 44), "H31": (0, -10), "H13": (-10, -4), "H14": (0, 10), "H16": (0, -10), "H15": (6, 4)}
for i, (pid, label) in enumerate(NUM, 1):
    if pid not in mk: continue
    px, py = mk[pid]
    x = 0.3 + px / 2400 * EX_W + ox.get(pid, (0, 0))[0] / 2400 * EX_W
    y = 1.0 + py / 1000 * EX_H + ox.get(pid, (0, 0))[1] / 1000 * EX_H
    c = rect(sl, x - 0.12, y - 0.12, 0.24, 0.24, RED, WHITE, 1.0, MSO_SHAPE.OVAL)
    tf = c.text_frame; tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER; r = p.add_run(); r.text = str(i); r.font.size = Pt(8); r.font.bold = True; r.font.color.rgb = WHITE; r.font.name = "Calibri"
panel(sl, 9.65, 0.95, 3.2, 5.95, "PARTS", [(f"{i}   {l}", dict(size=9, space=1.2)) for i, (_, l) in enumerate(NUM, 1)]
      + [("Not shown: control box, cooling trough, puller, dancer, spooler (sheets 10, 11).", dict(size=8.5, color=GREY, space=0))])
tb(sl, 0.35, 1.0 + EX_H + 0.1, 9.0, 0.9, ["Exploded along the screw axis; the hopper, heater bands, guard and screw are lifted for clarity.",
                                          "Orange = 3D-printed, grey = bought hardware, dark = heaters / motors. Thrust is carried by 8-9-10-5-7-11-12 and the four rods (sheet 7)."], 10, False, GREY)

# =============================================================================================== 4 process + materials
sl = new_slide("PROCESS + MATERIAL SETTINGS")
steps = ["Scrap\nflakes ≤ 4 mm", "Dry\n(per material)", "Hopper\n2.7 L", "Screw + barrel\n4 PID zones", "Die Ø2.2\n+ filter screen", "Cooling\ntrough + fans", "Puller\n30 mm rollers", "Dancer arm\n→ spooler", "1 kg spool\n≈ 335 m"]
bw, gap = 1.22, 0.16
for i, s_ in enumerate(steps):
    x = 0.5 + i * (bw + gap)
    box(sl, x, 1.0, bw, 0.62, s_.split("\n"), PANEL, BORD, 9, True)
    if i < len(steps) - 1: arrow(sl, x + bw, 1.31, x + bw + gap, 1.31, RED, 1.5)
rows = [["Material", "Z1 (feed)", "Z2", "Z3", "Z4 / die", "Dry before", "Cooling", "Notes"],
        ["PLA", "150", "170", "185", "190", "45–50 °C, 4 h if damp", "air OK ≤ 1 m/min", "easiest first run; mixes of colours give a muddy but fine filament"],
        ["PETG", "190", "215", "230", "235", "65 °C, 4–6 h", "air ≤ 1 m/min, bath better", "wet PETG foams and breaks – dry it; slightly stringy"],
        ["ABS / ASA", "190", "210", "225", "230", "80 °C, 2–4 h", "air OK", "fumes: ventilate. Print-scrap ABS shrinks – keep drawdown low"],
        ["TPU 95A", "160", "185", "200", "205", "60 °C, 4 h", "air, slow (≤ 0.6 m/min)", "soft: use the puller pressure spring lightly; screw ≤ 3 rpm"],
        ["PET (bottles)", "230", "250", "265", "270", "120–160 °C, ≥ 4 h", "water bath (M3)", "hard mode: needs drying + fast quench or it turns brittle / hazy"],
        ["PP / HDPE", "165", "185", "200", "205", "none", "water bath helps", "slippery on the screw; shrinks on cooling – wide tolerance"]]
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
stat(sl, 3.0, y0, 2.35, 1.15, "≈ 19 Nm", "stall limit at ≈ 1.6 A driver current – a mechanical fuse for the 8 mm screw core (≈ 20 Nm)", 22)
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

# =============================================================================================== 9 hopper + trough + print list
sl = new_slide("PRINTED PARTS – HOPPER, COOLING TROUGH + PRINT LIST")
pic(sl, "d_hopper.png", 0.4, 0.9, w=4.7)
pic(sl, "d_trough.png", 0.4, 4.65, w=4.4)
stl = json.load(open(IMG + "stl_list.json")) if os.path.exists(IMG + "stl_list.json") else []
rows = [["File", "Size X × Y × Z (mm)", "Qty", "Material"]]
qty = {"P06": 2}
mat = {"P09": "TPU 95A tyre + PETG hub", "P10": "TPU 95A tyre + PETG hub"}
for n, ext in stl:
    pid = n.split("_")[0]
    rows.append([n + ".stl", " × ".join(f"{e:.0f}" for e in ext), qty.get(pid, 1), mat.get(pid, "PETG" if pid not in ("P04", "P05") else "PETG (3 walls)")])
table(sl, 5.3, 0.95, 7.55, [3.7, 1.9, 0.5, 1.9], rows, size=8, row_h=0.285)
tb(sl, 5.3, 0.95 + 0.285 * len(rows) + 0.1, 7.5, 0.7, ["Every part fits a 245 × 245 × 260 mm bed (donor Vyper size). The hopper is the tallest (200 mm); the control box shell is the longest (240 mm).",
                                                      "Total filament: ≈ 1.8 kg of PETG + 60 g TPU."], 9.5, False, GREY)

# =============================================================================================== 10 line 2
sl = new_slide("COOLING, PULLER, DANCER + SPOOLER")
pic(sl, "d_line2.png", 0.5, 0.85, w=12.33)
lh = 12.33 * 3.55 / 12.3
y0 = 0.85 + lh + 0.08
stat(sl, 0.5, y0, 2.0, 1.1, "≈ 15 s", "air time over the 425 mm trough at 1.65 m/min", 22)
stat(sl, 2.65, y0, 2.0, 1.1, "≈ 0.5–1 m", "air path PLA needs at that speed (τ 12–24 s) → run ≤ 1 m/min or add the water bath (M3)", 22)
panel(sl, 4.85, y0, 3.9, 7.0 - y0, "PULLER", [
    ("Two ×30 TPU rollers, drive roller on a NEMA 17 (1/16 micro-step) – 3–42 rpm = 0.3–4 m/min.", dict(bullet=True)),
    ("Idler arm with a light spring: just grip, never crush.", dict(bullet=True)),
    ("Speed ratio puller : screw sets diameter (sheet 12).", dict(bullet=True))], 9)
panel(sl, 8.9, y0, 3.93, 7.0 - y0, "DANCER + SPOOLER", [
    ("Filament loops under the dancer roller; a 10 kΩ pot reads arm angle, the Nano trims spool PWM to hold mid-position.", dict(bullet=True)),
    ("Spool rpm: 2.6 (full) – 5.3 (core) at 1.65 m/min; 12 rpm gearmotor covers up to 3 m/min.", dict(bullet=True)),
    ("Level winding is manual at first (M2).", dict(bullet=True))], 9)

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
drv = [("DM542T → NEMA 23", "screw, 1.6 A limit"), ("TMC2209 → NEMA 17", "puller"), ("MOSFET → gearmotor", "spooler PWM"), ("5 × 40 mm fans", "24 V, always on with heat")]
for i, (a_, b_) in enumerate(drv):
    box(sl, 2.3, 4.35 + i * 0.4, 2.0, 0.34, [a_, b_], WHITE, INK, 7.5, True)
    arrow(sl, 2.0, 4.7, 2.3, 4.52 + i * 0.4, INK, 1.0)
box(sl, 4.8, 4.35, 1.7, 1.2, ["Arduino Nano", "5 V from buck", "STEP/DIR/EN, PWM"], PANEL, INK, 8.5, True)
for i in range(4): arrow(sl, 4.8, 4.45 + i * 0.28, 4.3, 4.52 + i * 0.4, BLUE, 0.8)
box(sl, 6.7, 4.35, 1.4, 1.2, ["Inputs", "2 pots, FWD/OFF/REV,", "dancer pot, driver ALM,", "PID ready (AL)"], WHITE, GREY, 7.5, True)
arrow(sl, 6.7, 4.95, 6.5, 4.95, BLUE)
panel(sl, 8.4, 0.88, 4.43, 3.35, "SAFETY CHAIN", [
    ("E-stop and contactor are pure hardware: the contactor drops both the heaters and the 24 V supply – no software in the loop.", dict(bullet=True)),
    ("Thermal fuse (280 °C) sits in the heater feed; it cuts power even if an SSR welds shut.", dict(bullet=True)),
    ("The Nano refuses to start the screw until Z3 and Z4 are within ±10 °C of setpoint (wire the PID alarm output to an input – VERIFY the REX-C100 variant has an ALM relay).", dict(bullet=True)),
    ("Driver current limit (≈ 1.6 A) lets the stepper skip steps on a jam instead of twisting the screw.", dict(bullet=True))], 9)
panel(sl, 8.4, 4.35, 4.43, 2.6, "DO THIS FIRST", [
    ("Have the 120 V side wired or checked by someone who does mains work. This sheet is a plan, not a certified design.", dict(bullet=True, color=RED)),
    ("Keep mains and 24 V wiring in separate bundles; use ferrules and a ground lug on the barrel.", dict(bullet=True)),
    ("Never leave it heating unattended until you trust the thermal fuse and the PIDs.", dict(bullet=True))], 9)
panel(sl, 0.5, 6.0, 7.6, 0.95, "CONTROL (NANO)", [
    ("Screw: STEP rate from knob 1 (40–600 motor rpm).  Puller: STEP rate = ratio × screw rate, knob 2 trims ±15 %.  Spooler: PWM = base + k × (dancer − centre).", dict(size=8)),
    ("Jam: driver ALM → stop, reverse 2 s, stop. Heat-not-ready → screw disabled.", dict(size=8))], 9)

# =============================================================================================== 12 speeds
sl = new_slide("SPEEDS + DIAL-IN")
pic(sl, "d_speed.png", 0.5, 0.95, w=6.4)
rows = [["Screw rpm", "Motor rpm", "Output g/h", "Filament m/min", "Hours per kg"]]
for N in (2, 3, 4, 5, 6, 8):
    r = C.row(N); rows.append([N, N * 20, f"{r['g_h']:.0f}", f"{r['v']:.2f}", f"{r['t_kg']:.1f}"])
table(sl, 7.2, 0.95, 5.63, [1, 1, 1, 1.3, 1.2], rows, size=9.5, row_h=0.3, bold_first=True, aligns=[PP_ALIGN.CENTER] * 5)
tb(sl, 7.2, 3.1, 5.6, 0.6, "Estimate: drag flow × 0.35 for pressure back-flow and leakage, PLA density. Calibrate once: weigh 1 m of strand at a known rpm and scale.", 9, False, GREY)
panel(sl, 7.2, 3.8, 5.63, 3.15, "DIAL-IN PROCEDURE (first run, ≈ 30 min)", [
    ("1  Heat to the setpoints on sheet 4, soak 10 min after the PIDs settle.", dict(size=9)),
    ("2  Set screw to 3 rpm; load a handful of virgin pellets or flakes.", dict(size=9)),
    ("3  Wait for a steady strand; pull by hand with pliers and thread it through the trough to the puller.", dict(size=9)),
    ("4  Set puller so the strand reads 1.75 mm; adjust ±5 % at a time every minute.", dict(size=9)),
    ("5  Hang the strand over the dancer, wind 3 turns on the spool core, engage the spooler.", dict(size=9)),
    ("6  Log rpm, puller speed and diameter every 5 min for the first spool.", dict(size=9))], 9)
panel(sl, 0.5, 5.7, 6.4, 1.25, "READING THE STRAND", [
    ("Bubbles / foam → wet material.  Hazy / rough → too cool or too fast.  Oval → uneven cooling, add fan time.", dict(bullet=True)),
    ("Diameter wave with the screw turn → feed starving (bridge in hopper) or worn flights.", dict(bullet=True)),
    ("Motor skipping → die too small or too cold; open the die or add 5 °C.", dict(bullet=True))], 9)

# =============================================================================================== 13 BOM
sl = new_slide("BILL OF MATERIALS")
half = (len(BOM) + 1) // 2
def bom_rows(rows):
    out = [["#", "Part", "Qty", "Size / note", "Est. $"]]
    return out
n = 0; flat = []
for r in BOM:
    if r[1] is None: flat.append(("grp", r[0]))
    else:
        n += 1; flat.append(("row", n, r))
left, right, cnt = [], [], 0
split = 21
if flat[split][0] == "row":
    flat.insert(split, ("grp", "Screw & barrel (cont.)"))
def mk_rows(items):
    rows = [["#", "Part", "Qty", "Size / note", "Est. $"]]; groups = []
    for it in items:
        if it[0] == "grp": rows.append(["", it[1].upper(), "", "", ""]); groups.append(len(rows) - 1)
        else:
            _, nn, r = it; rows.append([nn, r[0], r[1], r[2], f"{r[3]}–{r[4]}" if r[4] else "0"])
    return rows, groups
lr, lg = mk_rows(flat[:split]); rr, rg = mk_rows(flat[split:])
for rows_, xx, grp in ((lr, 0.4, lg), (rr, 6.75, rg)):
    t = table(sl, xx, 0.88, 6.2, [0.3, 2.7, 0.55, 2.3, 0.75], rows_, size=7.5, row_h=0.24, zebra=False)
    for gi in grp:
        for j in range(5):
            c = t.cell(gi, j); c.fill.solid(); c.fill.fore_color.rgb = BORD
            for p in c.text_frame.paragraphs:
                for rn in p.runs: rn.font.bold = True
tb(sl, 0.4, 6.55, 12.4, 0.5, [f"Estimated purchase total ≈ ${LOW:,}–${HIGH:,} (typical online listings, not quotes; shipping and tax excluded). Printed parts use your own filament.",
                               "Cheaper path: start with 3 heater zones (drop one PID + SSR + band), reuse the donor Vyper's NEMA 17 and PSU parts, and buy the stepper + gearbox as a ready NEMA 23 geared unit."], 9.5, False, GREY)

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
        ["Heat gun (optional)", "pre-form the heat guard, shrink tube", "hair-dryer is not enough; use an oven mitt and patience"]]
table(sl, 0.5, 0.95, 12.33, [3.0, 4.3, 5.0], rows, size=9.5, row_h=0.34, bold_first=True)
panel(sl, 0.5, 4.85, 6.05, 2.1, "THE PARTS THAT REALLY WANT A MACHINE", [
    ("Spindle thread and die hole are the two jobs where hand tools are marginal – both have a bought-part workaround above.", dict(bullet=True)),
    ("A local makerspace or machine shop can drill the die plug, tap the cap, and thread the spindle in 15 minutes – bring the parts and the sheet-6 drawing.", dict(bullet=True))], 9.5)
panel(sl, 6.75, 4.85, 6.08, 2.1, "PRINTING + FINISHING", [
    ("Printer: your Vyper (245 × 245 × 260). Print the housing and head plate first and test-fit bearings before printing the rest.", dict(bullet=True)),
    ("Sandpaper rolls for the bearing seats, a 8.5 mm drill to clean rod holes, heat-set M3/M5 inserts if you want the electronics box to open often.", dict(bullet=True))], 9.5)

# =============================================================================================== 15 assembly + checks
sl = new_slide("ASSEMBLY ORDER, DESIGN CHECKS + OPEN ITEMS")
steps = ["Cut rails to length, square the frame, drop in T-nuts for every foot.", "Print and test-fit housing, head plate, motor wall; clean bearing seats.",
         "Thread the spindle (or cut the ½-20 bolt); fit R8 bearings, thrust bearing, collar.", "Mount motor + gearbox on the wall; couple to the spindle; set the driver to ≈ 1.6 A.",
         "Tie the housing to the head plate with the M8 rods; check the spindle spins free by hand.", "Prep the screw (cut tip, polish); seat it in the chuck, tighten with threadlocker.",
         "Build the NPT stack on the floor flange; PTFE the cold joints; bolt to the head plate.", "Fit the barrel, cap, die plug, filter; wrap shim + bands; clamp thermocouples.",
         "Wire the heaters and PIDs off the machine; test each zone to 100 °C with an empty barrel.", "Mount cooling trough, puller, dancer and spooler; thread a test string through.",
         "Dry-run the screw at 5 rpm empty for 5 min; then first heat to 190 °C with PLA and dial in (sheet 12)."]
rich(sl, 0.5, 0.95, 5.0, 5.9, [(f"{i}  {s_}", dict(size=9.5, space=4)) for i, s_ in enumerate(steps, 1)], 9.5)
tb(sl, 0.5, 0.78, 5, 0.2, "ASSEMBLY ORDER", 10.5, True)
rows = [["DESIGN CHECK", "RESULT"],
        ["Screw output at 4 rpm", f"{r4['q']:.3f} cm³/s = {r4['g_h']:.0f} g/h (est.)"],
        ["Thrust at 5 / 10 MPa", f"{C.thrust(5):.0f} N / {C.thrust(10):.0f} N"],
        ["Screw torque at 5 / 10 MPa", f"{C.torque(C.thrust(5)):.1f} / {C.torque(C.thrust(10)):.1f} Nm (+ friction)"],
        ["Stall torque at screw", f"{C.STALL_FULL:.0f} Nm full, ≈ 19 Nm at 1.6 A"],
        ["Screw core torsion (8 mm, τy 200 MPa)", "≈ 20 Nm (VERIFY core)"],
        ["Thrust bearing load", "3.1 kN peak vs 10–15 kN class"],
        ["Warm-up to 270 °C", "112 kJ → 2.5 min ideal, 8–12 real"],
        ["Heater power", "800 W = 6.7 A at 120 V"],
        ["Melt load at 200–360 g/h", "20–36 W (heat is mostly loss)"],
        ["Hopper vs 1 kg of flakes", "2.7 L vs 2.5 L at 0.4 g/cm³ – may need one refill"],
        ["Air cooling path", "425 mm = 15 s at 1.65 m/min; need 0.5–1 m"],
        ["Spool speed", "2.6 → 5.3 rpm at 1.65 m/min"],
        ["Draw-down", f"{C.draw:.2f}× (×2.2 die → 1.75 mm)"]]
table(sl, 5.8, 0.95, 7.03, [3.1, 3.9], rows, size=9, row_h=0.3, bold_first=True)
panel(sl, 5.8, 5.35, 7.03, 1.6, "WHAT THE CHECKS SAY", [
    ("Mechanically comfortable: bearings and rods have large margin; the screw core is the weak link, so the driver current is the fuse.", dict(bullet=True)),
    ("Cooling is the first thing to outgrow: run ≤ 1 m/min on air, or build M3.", dict(bullet=True)),
    ("Throughput numbers are estimates until calibrated with a weighed metre.", dict(bullet=True, color=RED))], 9)

# =============================================================================================== 16 verify + roadmap
sl = new_slide("OPEN ITEMS (VERIFY) + MODIFICATION ROADMAP")
rows = [["#", "VERIFY before ordering / printing", "Why it matters"],
        ["1", "Auger bit: 20 mm OD, ≈ 8 mm core, 7/16 in hex, continuous flights", "sets clearance, torque limit, screw length"],
        ["2", "Gearbox output shaft (12 vs 14 mm), flange PCD, torque rating", "coupler bores, wall holes"],
        ["3", "Chuck thread ½-20 UNF and retaining screw; spindle thread fit", "reverse rotation can loosen it"],
        ["4", "Thrust bearing ½ in bore, OD ≤ 28", "housing seat size"],
        ["5", "Floor flange bolt circle / hole size", "head-plate hole pattern"],
        ["6", "Band heater ID (27–28 mm) and watt rating", "contact, warm-up time"],
        ["7", "REX-C100 variant with alarm relay", "heat-ready interlock"],
        ["8", "Printed-part temperatures near Z1 / head plate on PET", "creep at > 70 °C"],
        ["9", "Real throughput (weigh 1 m)", "sets puller ratio table"]]
table(sl, 0.5, 0.95, 6.3, [0.3, 3.6, 2.4], rows, size=8.5, row_h=0.37, zebra=True)
tb(sl, 7.0, 0.88, 5.8, 0.25, "PHASE 2 / 3 MODIFICATIONS (foundation stays; parts bolt on)", 10.5, True)
mods = [("M1", "Compression screw", "outsourced CNC / ground screw + hardened barrel liner; fixes wear and surge"),
        ("M2", "Level-wind traverse", "NEMA 17 + T8 lead screw on the spooler base for a neat 1 kg spool"),
        ("M3", "Water bath", "600 mm trough, drip-loop + air knife; unlocks PET/PETG at speed"),
        ("M4", "Closed-loop diameter", "optical or Hall gauge after the bath drives the puller speed (PID)"),
        ("M5", "Feeder upgrades", "hopper agitator, heated drying hopper, side feeder for fluffy flakes"),
        ("M6", "Melt sensing", "die pressure transducer + melt thermocouple; auto-stop on over-pressure"),
        ("M7", "Folded drive + enclosure", "belt drive saves ≈ 250 mm, fan-cooled housing, quieter"),
        ("M8", "Shredder hand-off", "chute from the DIY shredder, pellet cutter option")]
rows = [["", "Mod", "What it adds"]] + [[a, b, c] for a, b, c in mods]
table(sl, 7.0, 1.2, 5.83, [0.4, 1.5, 3.9], rows, size=8.5, row_h=0.4, bold_first=True)
panel(sl, 0.5, 5.15, 6.3, 1.8, "NEXT STEPS", [
    ("Confirm the auger bit and gearbox listings (items 1–2) – they fix the most dimensions.", dict(bullet=True)),
    ("Print the bearing housing and head plate first; test-fit bearings and the chuck.", dict(bullet=True)),
    ("Tell me what changes (your parts, bed size, scrap type) and I will re-run the generator: every drawing and file follows fm_params.py.", dict(bullet=True))], 9.5)
panel(sl, 7.0, 4.95, 5.83, 2.0, "SAFETY IN ONE PARAGRAPH", [
    ("Hot barrel (up to 280 °C), pressurised melt, mains wiring and a rotating screw. Use the guard, the E-stop and the thermal fuse; never reach into the hopper while the screw turns; ventilate for ABS/PET fumes; wear glasses when clearing a die.", dict(size=9.5))], 9.5)

prs.save(OUTF)
print("saved", OUTF, "slides", len(prs.slides), "bom", LOW, HIGH)

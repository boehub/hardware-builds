"""2-D dimensioned drawings for the blueprint sheets.  Every number comes from fm_params.P."""
import math, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon, Circle, FancyArrowPatch, Wedge
from matplotlib import font_manager
from fm_params import P

for f in font_manager.findSystemFonts():
    if "Carlito" in f:
        font_manager.fontManager.addfont(f)
plt.rcParams["font.family"] = "Carlito"

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "img")
os.makedirs(OUT, exist_ok=True)
RED, INK, GREY, PANEL, BORD = "#A5001E", "#222222", "#6B7785", "#F5F5F5", "#D5DBE3"
STEEL, STEELD, PRINT, DARK, BRASS, BLUE, GOLD = "#CBD3DC", "#9AA6B5", "#F4B77E", "#3B3F45", "#D9AE62", "#2563C4", "#C79A3B"
LW = 0.55

def fig_ax(w, h, xlim, ylim):
    fig = plt.figure(figsize=(w, h), dpi=300)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(*xlim); ax.set_ylim(*ylim); ax.set_aspect("equal"); ax.axis("off")
    return fig, ax

def rect(ax, x0, x1, z0, z1, fc=STEEL, ec=INK, lw=LW, z=2, ls="-", hatch=None, alpha=1):
    r = Rectangle((x0, z0), x1 - x0, z1 - z0, fc=fc, ec=ec, lw=lw, zorder=z, ls=ls, hatch=hatch, alpha=alpha)
    ax.add_patch(r); return r

def poly(ax, pts, fc=STEEL, ec=INK, lw=LW, z=2, alpha=1):
    ax.add_patch(Polygon(pts, closed=True, fc=fc, ec=ec, lw=lw, zorder=z, alpha=alpha))

def circ(ax, x, z, r, fc="white", ec=INK, lw=LW, zo=3, ls="-"):
    ax.add_patch(Circle((x, z), r, fc=fc, ec=ec, lw=lw, zorder=zo, ls=ls))

def txt(ax, x, z, s, fs=7, c=INK, ha="center", va="center", **k):
    return ax.text(x, z, s, fontsize=fs, color=c, ha=ha, va=va, zorder=10, **k)

def line(ax, x0, z0, x1, z1, c=INK, lw=LW, ls="-", z=4):
    ax.plot([x0, x1], [z0, z1], color=c, lw=lw, ls=ls, zorder=z, solid_capstyle="butt")

def hdim(ax, x0, x1, y, s, fs=6.8, ext=None, dy=2.2, c=RED, va="bottom"):
    ax.annotate("", xy=(x0, y), xytext=(x1, y), arrowprops=dict(arrowstyle="<|-|>", color=c, lw=0.55, mutation_scale=5, shrinkA=0, shrinkB=0), zorder=8)
    if ext is not None:
        for xx in (x0, x1):
            line(ax, xx, y, xx, ext, c=c, lw=0.35, z=7)
    txt(ax, (x0 + x1) / 2, y + (dy if va == "bottom" else -dy), s, fs, c, va=va)

def vdim(ax, x, y0, y1, s, fs=6.8, ext=None, dx=2.2, c=RED, side="right"):
    ax.annotate("", xy=(x, y0), xytext=(x, y1), arrowprops=dict(arrowstyle="<|-|>", color=c, lw=0.55, mutation_scale=5, shrinkA=0, shrinkB=0), zorder=8)
    if ext is not None:
        for yy in (y0, y1):
            line(ax, x, yy, ext, yy, c=c, lw=0.35, z=7)
    txt(ax, x + (dx if side == "right" else -dx), (y0 + y1) / 2, s, fs, c, ha="left" if side == "right" else "right", rotation=0)

def leader(ax, x0, y0, x1, y1, s, fs=6.5, c=RED, ha="left"):
    ax.annotate("", xy=(x0, y0), xytext=(x1, y1), arrowprops=dict(arrowstyle="-|>", color=c, lw=0.5, mutation_scale=4, shrinkA=0, shrinkB=0), zorder=8)
    txt(ax, x1, y1, s, fs, c, ha=ha, va="bottom" if y1 >= y0 else "top")

def centerline(ax, x0, x1, z=0, c=GREY):
    ax.plot([x0, x1], [z, z], color=c, lw=0.4, ls=(0, (8, 2, 1.5, 2)), zorder=1)

def save(fig, name):
    path = f"{OUT}/{name}.png"
    fig.savefig(path, dpi=300, facecolor="white")
    plt.close(fig)
    return path

# ====================================================================================================
def d_barrel():
    """Sheet 5: screw + barrel section (side)"""
    p = P
    W, H = 12.3, 3.95
    z0, z1 = -86, 92
    xs = (z1 - z0) * W / H
    xmin = 200
    fig, ax = fig_ax(W, H, (xmin, xmin + xs), (z0, z1))
    rt = 13.335; ri = 10.465
    h0, h1 = p["head_x"]
    # head plate
    rect(ax, h0, h1, z0, 74, PRINT); rect(ax, h0, h1, -15, 15, "white", ec=INK)
    txt(ax, (h0 + h1) / 2, 50, "HEAD\nPLATE", 5.8, ha="center", rotation=90)
    # flange
    fl0 = h1; fl1 = h1 + p["fl_t"]; fh0, fh1 = p["fl_hub_x"]
    rect(ax, fl0, fl1, -40, 40); rect(ax, fh0 - 0.01, fh1, -19, 19)
    rect(ax, fl0, fh1, -rt, rt, "white", z=3)
    # close nipple + tee + feed nipple (steel walls)
    n0, n1 = p["close_nip_x"]; t0, t1 = p["tee_x"]; tc = (t0 + t1) / 2; tr = p["tee_d"] / 2; ph = p["port_h"]
    rect(ax, t0, t1, -tr, tr); rect(ax, tc - tr, tc + tr, 0, ph)
    rect(ax, n0, n1, -rt, rt, STEELD, z=2.5)
    rect(ax, t0, t1, -ri, ri, "white", z=3.2); rect(ax, tc - ri, tc + ri, 0, ph + 1, "white", z=3.2)
    rect(ax, n0, n1, -ri, ri, "white", z=3.3)
    # feed nipple
    fn_top = ph + 38
    rect(ax, tc - rt, tc + rt, ph - 13, fn_top, STEELD, z=3.4); rect(ax, tc - ri, tc + ri, ph - 14, fn_top + 1, "white", z=3.5)
    # hopper collar
    zc0, zc1 = p["hop_collar_z"]
    rect(ax, tc - 16.5, tc + 16.5, zc0, zc1, PRINT, z=3.6); rect(ax, tc - rt + 0.0, tc + rt, zc0, zc1, STEELD, z=3.7)
    rect(ax, tc - ri, tc + ri, zc0 - 1, zc1 + 1, "white", z=3.8)
    rect(ax, 247, tc - 18, 74, 78, PRINT, z=3.9); rect(ax, tc - 25, tc + 25, 56, 78, "none", ec=INK, z=3.9, ls="--")
    txt(ax, 300, 52, "stay arm", 5.6, GREY)
    txt(ax, tc, 86, "to hopper (6.4 L, sheet 10)", 6.2, GREY)
    ax.annotate("", xy=(tc, 80), xytext=(tc, 84), arrowprops=dict(arrowstyle="-|>", color=GREY, lw=0.5, mutation_scale=4))
    # barrel
    b0, b1 = p["barrel_x"]
    rect(ax, b0, b1, -rt, rt, STEEL, z=2.2); rect(ax, b0, b1, -ri, ri, "white", z=3)
    cp0, cp1 = p["cap_x"]
    rect(ax, cp0, cp1, -17, 17, BRASS, z=2.3); rect(ax, cp0 - 0.01, cp1 - 8, -13.4, 13.4, "white", z=3.1)
    d0, d1 = p["die_x"]
    rect(ax, cp1 - 8, cp1, -4.9, 4.9, BRASS, z=3.3); rect(ax, cp1, d1, -7, 7, BRASS, z=3.3)
    rect(ax, cp1 - 9, d1 + 0.01, -p["die_d"] / 2, p["die_d"] / 2, "white", z=3.5, lw=0.3)
    # screw
    s0, s1 = p["shank_x"]; f0, f1 = p["flights_x"]
    rect(ax, 200, s1, -5.55, 5.55, "#B9C1CC", z=4.2)
    rect(ax, s1, f1, -4, 4, "#B9C1CC", z=4.2)
    k = 0
    while 281.25 + 20 * k <= f1 - 1.25:
        xc = 281.25 + 20 * k
        rect(ax, xc - 1.25, xc + 1.25, 4, 10, "#B9C1CC", z=4.2); k += 1
    k = 0
    while 291.25 + 20 * k <= f1 - 1.25:
        xc = 291.25 + 20 * k
        rect(ax, xc - 1.25, xc + 1.25, -10, -4, "#B9C1CC", z=4.2); k += 1
    centerline(ax, 200, 700)
    # bands
    for i, (a, b) in enumerate(p["bands"], 1):
        rect(ax, a, b, rt + 0.7, 18, DARK, z=4.5); rect(ax, a, b, -18, -rt - 0.7, DARK, z=4.5)
        txt(ax, (a + b) / 2, 23.5, f"Z{i}", 7, INK)
        circ(ax, (a + b) / 2 + 12, -18, 1.8, fc="#C0562B", zo=6)
    # heat guard
    g0, g1 = p["bands"][0][0] - 6, p["die_x"][0] - 2
    line(ax, g0, 29.2, g1, 29.2, c=GREY, lw=1.6); line(ax, g0, 29.2, g0, 9, c=GREY, lw=0.8); line(ax, g1, 29.2, g1, 9, c=GREY, lw=0.8)
    txt(ax, (g0 + g1) / 2, 33.5, "heat guard (perforated sheet, open sides)", 6.2, GREY)
    # strap + post
    sx = p["strap_x"]
    rect(ax, sx - 8, sx + 8, -85, -17.5, "#C8CED6", z=2.1); rect(ax, sx - 8, sx + 8, -17.5, 17.5, "none", ec=INK, z=2.1)
    txt(ax, sx, -30, "strap on\nangle post", 6, GREY)
    rect(ax, 330, 345, z0, -75, "none", ec="none", z=0)
    # dims
    yb = -46
    hdim(ax, f0, f1, -50, "flighted length 365  (L/D = 18)", ext=-14, dy=1.5)
    hdim(ax, b0, b1, -62, "barrel 305  (12 in nipple)", ext=-14, dy=1.5)
    hdim(ax, tc, p["bands"][0][0], -38, "cold feed zone 89", ext=-14, dy=1.5)
    hdim(ax, p["bands"][0][0], p["bands"][3][1], -74, "4 bands, 50 wide, 5 gap  (heated 215)", ext=-18, dy=1.5)
    txt(ax, d1 + 16, -58, "die face\nX = 657", 6.2, RED)
    line(ax, d1, -14, d1, -66, c=RED, lw=0.35)
    vdim(ax, 697, 0, ph, "40", ext=690, dx=1.5)
    leader(ax, tc, 12, tc - 30, 60, "feed port\n(tee side, 3/4 in)", ha="center")
    leader(ax, 290, -14, 262, -48, "floor flange + close nipple\n(3/4 in NPT, PTFE tape)", ha="center")
    leader(ax, (cp0 + cp1) / 2 + 4, -17, 662, -30, "cap + die plug", ha="center")
    leader(ax, 500, 8.5, 470, 62, "auger flight (single start, 20 mm pitch)", ha="center")
    txt(ax, 222, 40, "screw hex shank 7/16 in\n(into chuck, sheet 7)", 6.2, GREY, ha="center")
    txt(ax, 662, 84, "melt flows  →", 7, RED, ha="right")
    txt(ax, 205, -82, "section at Y = 0 \u2022 X in mm from the motor-wall rear face", 6, GREY, ha="left")
    return save(fig, "d_barrel")

# ====================================================================================================
def d_die():
    """Sheet 6: die close-up"""
    p = P
    W, H = 6.4, 3.7
    xs = 60 * W / H
    fig, ax = fig_ax(W, H, (610, 610 + xs), (-30, 30))
    ri = p["barrel_id"] / 2; rt = p["barrel_od"] / 2
    cp0, cp1 = p["cap_x"]; d0, d1 = p["die_x"]
    rect(ax, 610, 646, -rt, rt, STEEL, z=2); rect(ax, 610, 646, -ri, ri, "white", z=3)
    rect(ax, cp0, cp1, -17, 17, BRASS, z=2.3); rect(ax, cp0 + 0.01, cp1 - 8, -13.4, 13.4, "white", z=3.1)
    rect(ax, cp1 - 8, cp1, -4.9, 4.9, "#E8C27C", z=3.3); rect(ax, cp1, d1, -7, 7, "#E8C27C", z=3.3)
    # entry cone in plug
    poly(ax, [(cp1 - 9, 6), (cp1 - 9, -6), (cp1 - 3, -p["die_d"] / 2), (cp1 - 3, p["die_d"] / 2)], "white", z=3.6)
    rect(ax, cp1 - 3, d1 + 0.01, -p["die_d"] / 2, p["die_d"] / 2, "white", z=3.6, lw=0.3)
    # screw tip + filter
    rect(ax, 610, 640, -4, 4, "#B9C1CC", z=4.2)
    rect(ax, 641.0, 642.5, -11, 11, "#6B7785", z=4.4)
    # melt hatch
    rect(ax, 640, cp1 - 3, -ri, ri, "#F7E9C8", z=2.9, lw=0)
    for x in np.arange(612, 640, 4):
        line(ax, x, -ri + .3, x + 2, -4.3, c="#D9C79A", lw=0.3, z=3.05)
    centerline(ax, 610, 690)
    # dims
    hdim(ax, cp1, d1, -22, "6", ext=-8, dy=1.3)
    hdim(ax, cp1 - 3, d1, 19, "land 14\n(Ø 2.2)", ext=7.2, dy=1.3)
    vdim(ax, 661.5, -p["die_d"] / 2, p["die_d"] / 2, "Ø 2.2", ext=657.5, dx=1.2)
    vdim(ax, 667, -13.4, 13.4, "", ext=640)
    leader(ax, 641.8, 11, 628, 25, "filter screen\n(60-100 mesh SS disc)", ha="center")
    leader(ax, 647, -3.5, 633, -22, "M10 x 1.5 thread in cap\n(hand-tapped)", ha="center")
    leader(ax, 654, 6.9, 660, 24, "hex head 14 AF\n(M10 brass bolt)", ha="center")
    leader(ax, 620, 7.5, 612, 22, "melt chamber", ha="center")
    leader(ax, 634, -8, 618, -20, "screw tip stops 3 mm\nshort of cap wall", ha="center")
    txt(ax, 625, -27.6, "section at Y = 0 • mm", 5.8, GREY)
    return save(fig, "d_die")

# ====================================================================================================
def d_drive():
    """Sheet 7: drive train + thrust loop (side section)"""
    p = P
    W, H = 12.3, 4.3
    z0, z1 = -104, 90
    xs = (z1 - z0) * W / H
    xmin = -200
    fig, ax = fig_ax(W, H, (xmin, xmin + xs), (z0, z1))
    gl, ml = p["gb_len"], p["motor_len"]
    # motor + gearbox
    rect(ax, -gl - ml, -gl, -28.5, 28.5, "#4A4F57"); txt(ax, -gl - ml / 2, 0, "NEMA 23\nstepper\n3 Nm class", 7, "white")
    rect(ax, -gl, 0, -30, 30, STEELD); txt(ax, -gl / 2, 0, "planetary\n20 : 1", 7)
    rect(ax, 0, 2, -19, 19, STEELD, z=3.4); rect(ax, 2, 32, -7, 7, "#B9C1CC", z=3.5)
    # wall
    w0, w1 = p["wall_x"]
    rect(ax, w0, w1, -85, 62, PRINT); rect(ax, w0 - 0.01, w1 + 0.01, -21, 21, "white", z=3)
    rect(ax, -100, 40, -85, -75, PRINT); txt(ax, 7, 50, "MOTOR\nWALL", 5.8, rotation=90)
    # coupler
    c0, c1 = p["cpl_x"]
    rect(ax, c0, c1, -12.5, 12.5, "#7F8A99", z=4); txt(ax, (c0 + c1) / 2, 18, "clamp coupler\n14 → 12.7", 5.8, ha="center")
    # spindle
    s0, s1 = p["spindle_x"]
    rect(ax, s0, s1, -6.35, 6.35, "#B9C1CC", z=5)
    # housing
    h0, h1 = p["house_x"]; f0, f1 = p["flange_x"]
    rect(ax, h0, h1, -32, 32, PRINT); rect(ax, f0, f1, -52, 52, PRINT)
    rect(ax, h0 - 7, f1 - 5, -85, -75, PRINT); rect(ax, h0, h1, -85, -32, PRINT)
    rect(ax, h0 - 0.01, f1 + 0.01, -7.4, 7.4, "white", z=3)
    r8 = p["r8"]
    rect(ax, h0 - 0.01, h0 + 4 + r8["w"] + 0.4, -14.5, 14.5, "white", z=3.1)
    rect(ax, h1 - 4 - r8["w"] - 0.4, h1 + 0.01, -14.5, 14.5, "white", z=3.1)
    for xx in (h0 + 4, h1 - 4 - r8["w"]):
        rect(ax, xx, xx + r8["w"], 6.35, 14.3, "#8B97A8", z=4.5); rect(ax, xx, xx + r8["w"], -14.3, -6.35, "#8B97A8", z=4.5)
    rect(ax, f0 + 8, f1 + 0.01, -15.2, 15.2, "white", z=3.1)
    txt(ax, (h0 + h1) / 2, 50, "BEARING\nHOUSING", 6.2)
    txt(ax, (f0 + f1) / 2, 62, "thrust\nflange", 5.6)
    # thrust bearing + collar
    t0, t1 = p["thrust_x"]; k0, k1 = p["collar_x"]
    rect(ax, t0, t1, 6.5, 14, "#8B97A8", z=4.6); rect(ax, t0, t1, -14, -6.5, "#8B97A8", z=4.6)
    rect(ax, k0, k1, 6.35, 12.5, DARK, z=4.8); rect(ax, k0, k1, -12.5, -6.35, DARK, z=4.8)
    # chuck
    c0_, c1_ = p["chuck_x"]
    poly(ax, [(c0_, 18), (c0_ + 30, 18), (c0_ + 30, 21), (c1_ - 5, 21), (c1_ - 5, 16), (c1_, 16), (c1_, -16), (c1_ - 5, -16), (c1_ - 5, -21), (c0_ + 30, -21), (c0_ + 30, -18), (c0_, -18)], "#D3D9E1", z=4)
    rect(ax, c1_ - 32, c1_, -6.4, 6.4, "#EDEFF3", z=4.1, lw=0.3)
    txt(ax, c0_ + 36, 27, "13 mm chuck", 6.2, ha="center")
    # shank
    sh0, sh1 = p["shank_x"]
    rect(ax, sh0, sh1, -5.55, 5.55, "#B9C1CC", z=5)
    # head plate
    hp0, hp1 = p["head_x"]
    rect(ax, hp0, hp1, -85, 74, PRINT); rect(ax, hp0 - 0.01, hp1 + 0.01, -15, 15, "white", z=3)
    rect(ax, hp0 - 15, hp1, -85, -75, PRINT); txt(ax, (hp0 + hp1) / 2, 54, "HEAD\nPLATE", 5.8, rotation=90)
    rect(ax, hp1, hp1 + 12, -40, 40, STEEL); txt(ax, hp1 + 24, 46, "flange", 6, ha="left")
    rect(ax, 275, 288, -4, 4, "#B9C1CC", z=5)
    # tie rods
    for zz in (40, -40):
        rect(ax, f0 - 12, hp1 + 14, zz - 4, zz + 4, "#C8CED6", z=1.5, ls="-", lw=0.4)
        rect(ax, f0 - 6.5, f0, zz - 6.5, zz + 6.5, DARK, z=4.9); rect(ax, hp1, hp1 + 13, zz - 6.5, zz + 6.5, DARK, z=4.9)
    rect(ax, p["slinger_x"][0], p["slinger_x"][1], -20, 20, PRINT, z=4.4)
    txt(ax, 240, -29, "dust\nslinger", 5.4, GREY)
    for xx in (f0 - 14, f0 - 6):
        pass
    txt(ax, 205, 58, "M8 tie rods ×4\nat (±40, ±40)", 6.2, ha="center")
    centerline(ax, -200, 330)
    # thrust arrows (red)
    def arrow(p0, p1, c=RED, lw=1.1, ls="-"):
        ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=7, color=c, lw=lw, ls=ls, zorder=9, shrinkA=0, shrinkB=0))
    arrow((262, -26), (156, -26))      # screw -> chuck -> collar -> thrust bearing -> flange
    # path through rods drawn along top
    ax.annotate("", xy=(132, 66), xytext=(268, 66), arrowprops=dict(arrowstyle="-|>", color=RED, lw=0.9, mutation_scale=7, ls="--"), zorder=9)
    txt(ax, 200, 70, "die pressure pulls head plate forward  →  rods in tension", 6.4, RED)
    txt(ax, 220, -33.5, "screw thrust (1.6 – 3.1 kN)", 6.4, RED)
    # dims
    hdim(ax, c0, c1, -56, "coupler 32", ext=-14, dy=1.3)
    hdim(ax, s0, s1, -66, "spindle 155 (½ in rod, ½-20 UNF last 22)", ext=-8, dy=1.3)
    hdim(ax, c0_, c1_, -76, "chuck 70", ext=-22, dy=1.3)
    hdim(ax, sh0, sh1, -90, "hex shank 65 (25 inside chuck)", ext=-8, dy=1.3)
    hdim(ax, f1, hp0, 80, "123 between faces  →  M8 × 150 rods", ext=52, dy=1.3)
    hdim(ax, h0, h1, -48, "76", ext=-32, dy=1.3)
    txt(ax, -120, -48, "motor reaction torque\n→ motor wall (feet on rails)", 6.2, GREY)
    txt(ax, -190, 82, "section at Y = 0 • mm", 5.8, GREY, ha="left")
    return save(fig, "d_drive")

# ====================================================================================================
def d_printed():
    """Sheet 8: three printed parts - face views"""
    p = P
    sc = 46.5            # mm per inch
    W, H = 12.3, 3.95
    fig = plt.figure(figsize=(W, H), dpi=300)
    def panel(x_in, w_in, xl, zl):
        ax = fig.add_axes([x_in / W, 0.04, w_in / W, 0.9])
        ax.set_xlim(*xl); ax.set_ylim(*zl); ax.set_aspect("equal"); ax.axis("off"); return ax
    # ---- panel 1: motor wall (view from +X)
    ax = panel(0.0, 4.0, (-100, 86), (-96, 70))
    rect(ax, -70, 70, -85, 62, PRINT)
    for sy in (-1, 1):
        rect(ax, sy * 48 if sy > 0 else -56, 56 if sy > 0 else -48, -75, 45, "none", ec=GREY, ls="--", lw=0.4)
    circ(ax, 0, 0, 21, "white")
    for k in range(4):
        a = math.radians(45 + 90 * k); circ(ax, 35 * math.cos(a), 35 * math.sin(a), 2.75, "white")
    for y in (-50, 50):
        for z in (-80,):
            pass
    hdim(ax, -70, 70, 69, "140", ext=62, dy=1.2)
    vdim(ax, -80, -85, 62, "147", ext=-70, dx=-1.2, side="left")
    leader(ax, 14, 14, 52, 33, "Ø 42 pilot", ha="left")
    leader(ax, 24.7, 24.7, 50, 50, "4× Ø 5.5 on PCD 70\n(gearbox, VERIFY)", ha="left")
    txt(ax, 0, -92, "MOTOR WALL • 14 thick • face view from +X", 7, INK)
    txt(ax, -62, -55, "rib\n8", 5.5, GREY)
    txt(ax, 0, -79.5, "foot 10 thick • 6× Ø 5.8 slots to rails", 5.5, INK)
    # ---- panel 2: bearing housing (view from +X)
    ax = panel(4.15, 4.0, (-100, 86), (-96, 70))
    rect(ax, -70, 70, -85, -75, PRINT, ls="-")
    rect(ax, -26, 26, -75, -32, PRINT, lw=0.4)
    rect(ax, -32, 32, -32, 32, PRINT, lw=0.4, ls="--")
    rect(ax, -52, 52, -52, 52, PRINT)
    circ(ax, 0, 0, 15.2, "white"); circ(ax, 0, 0, 7.4, "white")
    for sy in (-1, 1):
        for sz in (-1, 1):
            circ(ax, sy * 40, sz * 40, 4.25, "white")
    hdim(ax, -52, 52, 59, "104 flange", ext=52, dy=1.2)
    hdim(ax, -40, 40, 46.5, "80", ext=44, dy=-5.2, va="top") if False else None
    hdim(ax, 0, 40, 0 - 0, "") if False else None
    vdim(ax, 62, -40, 40, "80", ext=44, dx=1.2)
    hdim(ax, -70, 70, -90, "140 foot", ext=-85, dy=-1.2, va="top")
    leader(ax, 28, 28, 56, 30, "4× Ø 8.5 rod holes\nat ±40, ±40", ha="left")
    leader(ax, 10, -9, 40, -22, "Ø 30.4 thrust seat\nØ 14.8 spindle", ha="left")
    txt(ax, 0, -96, "BEARING HOUSING + THRUST FLANGE • face view from +X", 7, INK)
    # ---- panel 3: head plate (view from +X)
    ax = panel(8.3, 4.0, (-100, 86), (-96, 70))
    rect(ax, -70, 70, -85, 74, PRINT)
    for sy in (-1, 1):
        rect(ax, sy * 56 if sy > 0 else -64, 64 if sy > 0 else -56, -75, 20, "none", ec=GREY, ls="--", lw=0.4)
    circ(ax, 0, 0, 15.2, "white")
    for k in range(4):
        a = math.radians(45 + 90 * k); circ(ax, 30 * math.cos(a), 30 * math.sin(a), 3.5, "white")
    for sy in (-1, 1):
        for sz in (-1, 1):
            circ(ax, sy * 40, sz * 40, 4.25, "white")
    vdim(ax, -80, -85, 74, "159", ext=-70, dx=-1.2, side="left")
    hdim(ax, -70, 70, 80, "140", ext=74, dy=1.2) if False else None
    leader(ax, 21.2, 21.2, 52, 62, "4× Ø 7.0 on PCD 60\n(floor flange, VERIFY)", ha="left")
    leader(ax, 40, -40, 50, -62, "4× Ø 8.5 rods", ha="left")
    leader(ax, 0, 12, -20, 52, "Ø 30 shank\nclearance", ha="center")
    txt(ax, 0, -92, "HEAD PLATE • 16 thick • face view from +X", 7, INK)
    return save(fig, "d_printed")

# ====================================================================================================
import fm_model
SPONGE = "#E3CF7A"; WATER = "#BFD9F2"

def _feet_x():
    tx0, tx1 = P["trough_x"]; jx = P["bath_joint"]
    return [tx0 + 10, tx0 + 175, jx + 28, tx1 - 95]

# ====================================================================================================
def d_bath():
    """Water bath long section (Y = 0) with the real strand path"""
    p = P; fm_model.build(); path = fm_model.FILAMENT_PATH
    W = 12.3; x0, x1 = 655, 1185; zlo, zhi = -112, 56
    H = (zhi - zlo) * W / (x1 - x0)
    fig, ax = fig_ax(W, H, (x0, x1), (zlo, zhi))
    tx0, tx1 = p["trough_x"]; jx = p["bath_joint"]; bf, br, bw = p["bath_floor"], p["bath_rim"], p["bath_wall"]
    rect(ax, 655, 690, -105, -85, "#C8CED6", lw=0.4); rect(ax, 700, x1, -105, -85, "#C8CED6", lw=0.4)
    for fx in _feet_x():
        rect(ax, fx, fx + 36, -85, -75, PRINT); rect(ax, fx, fx + 36, -75, bf, PRINT)
    rect(ax, tx0, tx1, bf, bf + bw, PRINT)
    rect(ax, tx0 + bw, tx1 - 10, bf + bw, p["water_z"], WATER, ec="none", z=1.6)
    rect(ax, tx0, tx0 + bw, bf, -7.5, PRINT); rect(ax, tx1 - 10, tx1, bf, -7.2, PRINT)
    rect(ax, tx0, tx1, bf, br, "none", ec=GREY, ls="--", lw=0.4, z=1)          # side walls behind the section plane
    rect(ax, jx - 10, jx + 10, -50, -10, "none", ec=INK, ls="--", lw=0.4, z=3)
    line(ax, jx, bf + bw, jx, br, c=RED, lw=0.5, ls="--")
    ws0, ws1 = p["wiper_slot"]
    rect(ax, ws0 + 0.3, ws1 - 0.3, -6.5, br, SPONGE, z=3)
    for xc in p["sheave_xs"]:
        zc = p["line_z"] + 0.875 + p["sheave_d"] / 2
        rect(ax, xc - 8, xc + 8, br, br + 4, PRINT, z=3); rect(ax, xc - 8, xc + 8, zc - 5, br, PRINT, alpha=0.35, ls="--", z=2.5)
        circ(ax, xc, zc, p["sheave_d"] / 2, "#8B97A8", zo=5); circ(ax, xc, zc, 2.0, "white", zo=6)
    ax.plot([q[0] for q in path], [q[1] for q in path], color=BLUE, lw=1.3, zorder=7)
    rect(ax, 640, 657, -7, 7, BRASS); txt(ax, 660, 12, "die", 6.5, ha="left")
    pu0, pu1 = p["puller_x"]; pcx = (pu0 + pu1) / 2; rd = p["roller_d"] / 2; nz = rd + 0.875
    rect(ax, pu0, pu1, -85, 44, PRINT, alpha=0.3, lw=0.4)
    circ(ax, pcx, -nz, rd, "#2E7D4F", zo=5); circ(ax, pcx, nz - 0.3, rd, "#2E7D4F", zo=5)
    txt(ax, pcx + 5, 56, "puller", 6.5)
    # barbs (on the -Y wall, out of the plane)
    circ(ax, tx0 + 25, bf + 20, 3.8, "none", ec=GREY, zo=6, ls="--"); circ(ax, tx1 - 40, p["water_z"], 3.8, "none", ec=GREY, zo=6, ls="--")
    # dims + labels
    hdim(ax, tx0, tx1, 46, "water bath 474  =  2 printed segments of 237, joined at x = 902", ext=br, dy=1.5)
    leader(ax, 670, -7.5, 705, 30, "entry notch 5 wide\nfloor z = -7.5", ha="center")
    leader(ax, 1136.5, -3.5, 1075, 30, "exit notch + sponge wiper slot", ha="center")
    leader(ax, p["sheave_xs"][0], -9.5, 760, 12, "sheave: 624ZZ bearing on an M4 axle,\nstrand runs under it at z = -22", ha="left")
    leader(ax, p["sheave_xs"][1], -9.5, 960, 12, "exit sheave", ha="center")
    txt(ax, 800, -34, "STRAND UNDER WATER ≈ 485 mm  (need 52 mm at 4 rpm)", 7.5, BLUE)
    txt(ax, 800, -50, "water level z = -10  (overflow barb on the -Y wall)", 6.5, "#2C5E8E")
    leader(ax, tx0 + 25, bf + 20, 782, -78, "inlet barb (-Y wall)\nfrom pump", ha="center")
    leader(ax, 902, -42, 906, -78, "joint: 4 × M3 + silicone", ha="left")
    txt(ax, 662, -108, "long section at Y = 0 • mm • strand dips under the sheaves, so the entry / exit notches stay above the water", 6, GREY, ha="left")
    return save(fig, "d_bath")

def d_bath_xs():
    W, H = 5.4, 4.4
    fig, ax = fig_ax(W, H, (-82, 82), (-114, 20))
    for yy in (-50, 50): rect(ax, yy - 10, yy + 10, -105, -85, "#C8CED6", lw=0.4)
    rect(ax, -70, 70, -85, -75, PRINT); rect(ax, -16, 16, -75, -62, PRINT)
    rect(ax, -16, 16, -62, 10, PRINT); rect(ax, -12, 12, -58, 10.5, "white", z=3); rect(ax, -12, 12, -58, -10, WATER, z=3.1)
    rect(ax, -22, 22, 10, 14, PRINT, z=4); rect(ax, 3.5, 7, -20, 10, PRINT, z=4, alpha=0.6); rect(ax, -7, -3.5, -20, 10, PRINT, z=4, alpha=0.6)
    rect(ax, -2.5, 2.5, -21.1, -8.1, "#8B97A8", z=4.5)
    circ(ax, 0, -22, 0.875 * 3, BLUE, ec=BLUE, zo=6)
    rect(ax, -30, -16, -13.8, -6.2, BRASS, z=4, lw=0.4)
    hdim(ax, -16, 16, 22, "32", ext=10, dy=1.0)
    hdim(ax, -12, 12, -66, "24 inside", ext=-58, dy=-1.0, va="top")
    vdim(ax, 24, -62, 10, "72", ext=16, dx=1.0)
    vdim(ax, -34, -58, -10, "water 48", ext=-12, dx=-1.0, side="left")
    leader(ax, 0.5, -22, 33, -33, "strand (drawn 3×)", ha="left")
    leader(ax, -23, -10, -52, 4, "overflow barb\nat z = -10", ha="center")
    leader(ax, 16, -69, 42, -62, "pedestal", ha="left")
    leader(ax, 12, 12, 40, 18, "sheave hanger (bar on the rim,\nplates beside the bearing)", ha="left")
    txt(ax, 0, -111, "section at the entry sheave • mm", 6, GREY)
    return save(fig, "d_bath_xs")

def d_hopper():
    p = P
    r0, R, t, hz0, hz1, hz2 = fm_model.hopper_geom(p)
    lip, lt = p["hop_lip"], p["hop_lip_t"]; dh = p["hop_drum_h"]; zt = hz2 + dh; rc = r0 + 3
    W, H = 4.7, 5.95
    zlo, zhi = -34, 490
    xr = (H and (zhi - zlo) * W / H) / 2
    fig, ax = fig_ax(W, H, (-xr, xr), (zlo, zhi))
    for s in (-1, 1):
        poly(ax, [(s * rc, hz0), (s * rc, hz1), (s * (R + t), hz2), (s * R, hz2), (s * r0, hz1), (s * r0, hz0)], PRINT)
        rect(ax, min(s * (R + t - 0.5), s * (R + t + lip)), max(s * (R + t - 0.5), s * (R + t + lip)), hz2 - lt, hz2, PRINT)
        rect(ax, min(s * R, s * (R + t)), max(s * R, s * (R + t)), hz2, zt, PRINT)
        rect(ax, min(s * (R + t - 0.5), s * (R + t + lip)), max(s * (R + t - 0.5), s * (R + t + lip)), hz2, hz2 + lt, PRINT)
        rect(ax, min(s * (R - 8), s * (R + t + 2)), max(s * (R - 8), s * (R + t + 2)), zt, zt + 4, PRINT)
        rect(ax, min(s * (R - 3.5), s * (R - 0.5)), max(s * (R - 3.5), s * (R - 0.5)), zt - 8, zt, PRINT)
        bx = s * (R + t + lip / 2 + 0.5)
        circ(ax, bx, hz2 - lt / 2 + lt / 2, 1.8, RED, zo=6)
    # tee, nipple, barrel (end view)
    rect(ax, -17.5, 17.5, -17.5, 40, STEEL); rect(ax, -13.3, 13.3, 27, 78, STEELD, z=3); rect(ax, -10.4, 10.4, 25, 79, "white", z=3.2)
    circ(ax, 0, 0, 10.4, "white", zo=3.3); circ(ax, 0, 0, 10.0, "#B9C1CC", zo=3.4); circ(ax, 0, 0, 4, "#9AA6B5", zo=3.5)
    rect(ax, -rc, rc, hz0, hz1, PRINT, z=2.5); rect(ax, -13.3, 13.3, hz0, hz1, STEELD, z=3.1); rect(ax, -10.4, 10.4, hz0 - 1, hz1 + 1, "white", z=3.2)
    # lid frame, boss, bearings, plate, motor
    rect(ax, -16, 16, zt, zt + 6, PRINT, z=3); rect(ax, -14, 14, zt, zt + 30, PRINT, z=3)
    rect(ax, -9.7, 9.7, zt, zt + 7.5, "white", z=3.1); rect(ax, -9.7, 9.7, zt + 22.5, zt + 30, "white", z=3.1)
    rect(ax, -9.5, 9.5, zt, zt + 6, "#8B97A8", z=3.3); rect(ax, -9.5, 9.5, zt + 24, zt + 30, "#8B97A8", z=3.3)
    rect(ax, -20, 20, zt + 58, zt + 64, PRINT, z=3); rect(ax, -7, 7, zt + 34, zt + 58, "#7F8A99", z=4.2)
    rect(ax, -18.5, 18.5, zt + 64, zt + 126, "#4A4F57", z=3.2); txt(ax, 0, zt + 95, "gear-\nmotor\n24 V\n12 rpm", 5.4, "white")
    for sx in (-12, 12): rect(ax, sx - 3.5, sx + 3.5, zt + 6, zt + 58, "none", ec=INK, ls="--", lw=0.4, z=2)
    # rod + paddle
    rect(ax, -3, 3, p["agit_z0"], zt + 46, "#B9C1CC", z=5)
    ze = 190.0; re = (r0 + (ze - hz1) / math.tan(math.radians(p["hop_cone_deg"]))) - 8
    for s in (-1, 1):
        poly(ax, [(s * 6, p["agit_z0"]), (s * re, ze - 4), (s * re, ze + 4), (s * 6, p["agit_z0"] + 16)], "#E9904A", z=5.5)
    rect(ax, -8, 8, p["agit_z0"], p["agit_z0"] + 16, "#E9904A", z=5.6)
    # fill line
    vtot = fm_model.hopper_volume_ml(p) * 1000
    v_low = math.pi * (hz2 - hz1) / 3 * (R * R + R * r0 + r0 * r0) + math.pi * r0 * r0 * (hz1 - hz0)
    zf = hz2 + (0.9 * vtot - v_low) / (math.pi * R * R)
    line(ax, -R, zf, R, zf, c=BLUE, lw=0.8, ls="--")
    txt(ax, 0, zf + 6, f"90 % fill = {0.9*vtot/1e6:.1f} L", 6.2, BLUE)
    # dims
    hdim(ax, -(R + t + lip), R + t + lip, hz2 - 20, f"Ø {2*(R+t+lip):.1f} over the flange", ext=hz2 - lt, dy=1.5, fs=6.2) if False else None
    vdim(ax, R + t + lip + 6, hz1, hz2, f"cone {hz2-hz1:.0f}", ext=R + t, dx=1.2, fs=6.2)
    vdim(ax, R + t + lip + 6, hz2, zt, f"drum {dh:.0f}", ext=R + t + lip, dx=1.2, fs=6.2)
    vdim(ax, R + t + lip + 6, hz0, hz1, f"{hz1-hz0:.0f}", ext=rc, dx=1.2, fs=6.2)
    vdim(ax, R + t + lip + 6, zt, zt + 30, "", ext=R + t + lip, dx=1.2, fs=6.2)
    txt(ax, R + t + lip + 12, zt + 80, f"lid frame, bearings,\nmotor: top at\nZ = {zt+126:.0f}", 5.8, GREY, ha="left")
    txt(ax, -R - t - lip - 6, hz2 + 40, f"Ø {2*(R+t+lip):.1f}\nover the\nflange rings", 6.2, RED, ha="right")
    txt(ax, -(R + t + lip) - 6, (hz1 + hz2) / 2, f"{p['hop_cone_deg']}° wall\nangle", 6.4, RED, ha="right")
    txt(ax, -R - t - lip - 6, zt - 40, "drum:\nprint upright", 6, GREY, ha="right")
    txt(ax, -R - t - lip - 6, (hz0 + hz1) / 2 + 40, "lower cone:\nprint upside\ndown", 6, GREY, ha="right")
    txt(ax, 28, p["agit_z0"] + 52, "paddle sweeps\nthe cone wall", 6, "#B35E10", ha="left")
    txt(ax, 24, 0, "screw", 5.8, GREY, ha="left")
    txt(ax, 0, zlo + 4, "section at Y = 0 • mm", 5.8, GREY)
    return save(fig, "d_hopper")

def d_spool_top():
    p = P; fm_model.build(); path = fm_model.FILAMENT_PATH
    W = 7.7; x0, x1 = 1235, 1700; ylo, yhi = -96, 116
    H = (yhi - ylo) * W / (x1 - x0)
    fig, ax = fig_ax(W, H, (x0, x1), (ylo, yhi))
    scx = p["spool_cx"]; tx0, tx1 = p["trav_x"]; dx = p["dancer_x"]
    for yy in (-50, 50): rect(ax, 1245, 1640, yy - 10, yy + 10, "#C8CED6", lw=0.4)
    # dancer
    rect(ax, dx - 30, dx + 30, -70, 70, PRINT, alpha=0.4, lw=0.4); rect(ax, dx - 8, dx + 8, -30, -14, PRINT)
    rect(ax, dx - 8.5, dx + 8.5, -50, -30, "#4A4F57"); txt(ax, dx, -57, "pot", 6)
    a_rest = math.degrees(math.acos((p["dancer_pivot_z"] - 11.5) / p["dancer_L"]))
    tipx, _ = fm_model.dancer_tip(p, a_rest)
    rect(ax, dx - 9, tipx, -13, -7, PRINT, z=4); rect(ax, tipx - 10, tipx + 10, -5.5, 8.5, "#E9ECF0", z=5)
    txt(ax, dx + 20, -24, "dancer arm\n(plate y -13..-7)", 6, ha="left")
    # traverse
    rect(ax, tx0, tx1, -70, 70, PRINT, alpha=0.4, lw=0.4); rect(ax, tx0, tx1, -66, -58, PRINT); rect(ax, tx0, tx1, 58, 66, PRINT)
    rect(ax, p["trav_rod_x"] - 4, p["trav_rod_x"] + 4, -64, 64, "#B9C1CC", z=4); rect(ax, p["trav_screw_x"] - 4, p["trav_screw_x"] + 4, -62, 66, "#9AA6B5", z=4)
    rect(ax, p["trav_screw_x"] - 21, p["trav_screw_x"] + 21, 66, 106, "#4A4F57", z=4); txt(ax, p["trav_screw_x"], 86, "NEMA 17\nT8 lead\nscrew", 5.8, "white")
    rect(ax, tx0 + 5, tx1 - 3, -8, 8, PRINT, z=5)
    for dy in (-p["trav_range"], p["trav_range"]):
        rect(ax, tx0 + 5, tx1 - 3, dy - 8, dy + 8, "none", ec=RED, ls="--", lw=0.5, z=6)
    circ(ax, p["trav_eye_x"], 0, 2.2, "white", zo=7)
    txt(ax, (tx0 + tx1) / 2, -80, "LEVEL-WIND", 6.2, ha="center")
    # spool + hardware
    rect(ax, scx - 55, scx + 55, -85, 70, PRINT, alpha=0.4, lw=0.4)
    rect(ax, scx - 40, scx + 40, 40, 50, PRINT); rect(ax, scx - 40, scx + 40, -75, -65, PRINT)
    rect(ax, scx - 21, scx + 21, 50, 90, "#4A4F57"); txt(ax, scx, 72, "NEMA 17\nspool drive", 6, "white")
    rect(ax, scx - 2.5, scx + 2.5, 26, 50, "#B9C1CC", z=5)
    rect(ax, scx - 100, scx + 100, -33, 33, "#E9EEF9", ec=BLUE, z=2); rect(ax, scx - 100, scx + 100, -30, -33 + 3, "#9DB2E6", ec=BLUE, z=2.1) if False else None
    rect(ax, scx - 72, scx + 72, -30, 30, "#F1E48A", ec="#B9A93B", z=2.5)
    rect(ax, scx - 50, scx + 50, -30, 30, "#C4D2F0", ec=BLUE, z=2.6); txt(ax, scx, 0, "1 kg of filament", 6.5, "#6D5F10")
    poly(ax, [(scx - 24, 28), (scx + 24, 28), (scx + 31.5, 39), (scx - 31.5, 39)], "#F4B77E", z=4); poly(ax, [(scx - 31.5, -39), (scx + 31.5, -39), (scx + 24, -28), (scx - 24, -28)], "#F4B77E", z=4)
    rect(ax, scx - 4, scx + 4, -83, -24.9, "#B9C1CC", z=5)
    for k in range(7):
        yy = -64 + k * 3.2; line(ax, scx - 5.5, yy, scx + 5.5, yy + 1.6, c=GREY, lw=0.5, z=6)
    rect(ax, scx - 6.5, scx + 6.5, -81.5, -75, DARK, z=6)
    txt(ax, scx + 52, -55, "idler cone on an M8 rod: spring\npushes it in; push it back\n12 mm to drop a spool in", 6, ha="left")
    txt(ax, scx + 52, 58, "drive cone on the\nNEMA 17 shaft (set screw)", 6, ha="left")
    # strand
    line(ax, 1235, 0, path[-1][0], 0, c=BLUE, lw=1.2, z=8)
    # dims
    vdim(ax, 1648, -30, 30, "winding\nwidth 60", ext=scx + 100, dx=2, side="right", fs=6.2)
    vdim(ax, tx0 - 8, -p["trav_range"], p["trav_range"], "56", ext=tx0 + 4, dx=-1.5, side="left", fs=6.2)
    hdim(ax, dx, tx0 + 30, 98, f"dancer → eyelet {p['trav_eye_x']-dx}", ext=70, dy=1.3, fs=6.2)
    hdim(ax, p["trav_eye_x"], scx - 72, 108, "eyelet → pack 73", ext=0, dy=1.3, fs=6.2) if False else None
    txt(ax, 1240, -92, "top view (from +Z) • mm • level-wind stroke 56, steps 1.75 mm per spool turn (700 micro-steps)", 6, GREY, ha="left")
    return save(fig, "d_spool_top")

def d_line2():
    """Sheet: puller + dancer + level-wind + spool, side view"""
    p = P; fm_model.build(); path = fm_model.FILAMENT_PATH
    W = 8.7; x0, x1 = 1095, 1660; zlo, zhi = -122, 150
    H = (zhi - zlo) * W / (x1 - x0)
    fig, ax = fig_ax(W, H, (x0, x1), (zlo, zhi))
    rect(ax, x0, p["mod2_x"][1], -105, -85, "#C8CED6", lw=0.4); rect(ax, p["mod3_x"][0], p["mod3_x"][1], -105, -85, "#C8CED6", lw=0.4)
    rect(ax, x0, 1139, -62, 10, "none", ec=GREY, ls="--", lw=0.4); rect(ax, 1129, 1139, -62, -7.2, PRINT)
    pu0, pu1 = p["puller_x"]; pcx = (pu0 + pu1) / 2; rd = p["roller_d"] / 2; nz = rd + 0.875
    rect(ax, pu0 - 15, pu1 + 15, -85, -75, PRINT, lw=0.4); rect(ax, pu0, pu1, -75, 44, PRINT, alpha=0.3, lw=0.4)
    circ(ax, pcx, -nz, rd, "#2E7D4F", zo=5); circ(ax, pcx, nz - 0.3, rd, "#2E7D4F", zo=5)
    rect(ax, pcx - 34, pcx + 34, 44, 50, PRINT, z=5)
    for yy in (0,): line(ax, pcx, 50, pcx, 18, c=GREY, lw=0.8)
    txt(ax, pcx, 62, "PULLER\n2 springs set the nip", 6.3)
    dx = p["dancer_x"]; pz = p["dancer_pivot_z"]
    rect(ax, dx - 30, dx + 30, -85, -75, PRINT, lw=0.4); rect(ax, dx - 8, dx + 8, -75, pz + 18, PRINT)
    a_rest = math.degrees(math.acos((pz - 11.5) / p["dancer_L"]))
    for a_, fcol, al in ((20, "none", 1), (a_rest, PRINT, 1), (55, "none", 1)):
        am, rm = fm_model.dancer_arm_mesh(p, a_)
        tx_, tz_ = fm_model.dancer_tip(p, a_)
        v = np.array([tx_ - dx, tz_ - pz]); v /= np.linalg.norm(v); n = np.array([-v[1], v[0]])
        pts = [(dx + n[0] * 6, pz + n[1] * 6), (tx_ + n[0] * 5, tz_ + n[1] * 5), (tx_ - n[0] * 5, tz_ - n[1] * 5), (dx - n[0] * 6, pz - n[1] * 6)]
        poly(ax, pts, PRINT if fcol != "none" else "none", ec=INK if fcol != "none" else GREY, z=6, alpha=1)
        circ(ax, tx_, tz_, 10, "#E9ECF0" if fcol != "none" else "none", ec=INK if fcol != "none" else GREY, zo=6.5, ls="-" if fcol != "none" else "--")
    circ(ax, dx, pz, 9, DARK, zo=7)
    txt(ax, dx - 4, pz + 28, "DANCER ARM\n10 kΩ pot at the pivot", 6.3, ha="center")
    ax.annotate("", xy=(dx + 100, -26), xytext=(dx + 100, 14), arrowprops=dict(arrowstyle="<|-|>", color=RED, lw=0.6, mutation_scale=5))
    txt(ax, dx + 70, 125, "slack ↓ → spool faster\nslack ↑ → spool slower", 6, RED, ha="left")
    # traverse
    tx0, tx1 = p["trav_x"]; tz = p["trav_z"]
    rect(ax, tx0, tx1, -85, -75, PRINT, lw=0.4); rect(ax, tx0, tx1, -75, -5, PRINT, alpha=0.3, lw=0.4)
    rect(ax, tx0 + 5, tx1 - 3, tz - 12, tz + 12, PRINT, z=5); rect(ax, p["trav_eye_x"] - 5, p["trav_eye_x"] + 5, tz + 12, 7, PRINT, z=5)
    circ(ax, p["trav_screw_x"], tz, 4, "#B9C1CC", zo=6); circ(ax, p["trav_rod_x"], tz, 4, "#B9C1CC", zo=6); circ(ax, p["trav_eye_x"], 0, 2.4, "white", zo=7)
    txt(ax, (tx0 + tx1) / 2, 20, "LEVEL-WIND\ncarriage + PTFE eyelet", 6.3)
    # spool
    scx, scz = p["spool_cx"], p["spool_cz"]
    circ(ax, scx, scz, 100, "#E9EEF9", ec=BLUE, zo=2); circ(ax, scx, scz, p["pack_r"], "#F1E48A", ec="#B9A93B", zo=2.5); circ(ax, scx, scz, 50, "#C4D2F0", ec=BLUE, zo=3); circ(ax, scx, scz, 27, "white", ec=BLUE, zo=4)
    rect(ax, scx - 40, scx + 40, -85, scz + 60, "none", ec=INK, ls="--", lw=0.5, z=6)
    txt(ax, scx, scz + 82, "1 kg SPOOL Ø 200", 7, BLUE); txt(ax, scx, scz + 40, "filament wound\n(35 % shown)", 5.8, "#6D5F10")
    ax.plot([q[0] for q in path if q[0] >= x0], [q[1] for q in path if q[0] >= x0], color=BLUE, lw=1.1, zorder=8)
    hdim(ax, pcx, p["trav_eye_x"], -113, f"nip → eyelet {p['trav_eye_x']-pcx:.0f}", ext=-86, dy=-1.0, fs=6.2, va="top") if False else None
    hdim(ax, pcx, scx, 136, f"puller nip → spool axis {scx-pcx:.0f}", ext=60, dy=1.3, fs=6.4)
    txt(ax, 1100, -118, "side view • strand line is Z = 0 • mm", 5.8, GREY, ha="left")
    return save(fig, "d_line2")

def d_hopcap():
    import fm_model as M
    vol_b = M.hopper_volume_ml(P)
    vol_a = 2.8 * 1000
    dens = [0.15, 0.20, 0.25, 0.30, 0.40, 0.50]
    a = [vol_a * 0.9 * d for d in dens]; b = [vol_b * 0.9 * d for d in dens]
    fig = plt.figure(figsize=(6.2, 3.3), dpi=300); ax = fig.add_axes([0.1, 0.17, 0.87, 0.72])
    xs = np.arange(len(dens)); w = 0.38
    ax.bar(xs - w / 2, a, w, color="#9AA6B5", label="Rev A hopper (2.8 L)"); ax.bar(xs + w / 2, b, w, color=RED, label="Rev B hopper (%.1f L)" % (vol_b / 1000))
    ax.axhline(1000, color=INK, lw=0.9, ls="--"); ax.text(len(dens) - 0.45, 1030, "1 kg", ha="right", fontsize=8, color=INK)
    for i, (u, v) in enumerate(zip(a, b)):
        ax.text(i - w / 2, u + 25, f"{u:.0f}", ha="center", fontsize=6.5, color=GREY); ax.text(i + w / 2, v + 25, f"{v:.0f}", ha="center", fontsize=6.5, color=RED)
    ax.set_xticks(xs); ax.set_xticklabels([f"{d:.2f}" for d in dens], fontsize=8)
    ax.set_xlabel("bulk density of the flakes (g/cm³)  •  fluffy film ≈ 0.15, fine shredder output ≈ 0.25–0.4", fontsize=7.5)
    ax.set_ylabel("grams held at 90 % fill", fontsize=8); ax.tick_params(axis="y", labelsize=7.5)
    for sp_ in ("top", "right"): ax.spines[sp_].set_visible(False)
    ax.legend(frameon=False, fontsize=7.5, loc="upper left"); ax.set_title("What the hopper holds", fontsize=10, loc="left")
    return save(fig, "d_hopcap")

if __name__ == "__main__":
    for f in (d_barrel, d_die, d_drive, d_printed, d_bath, d_bath_xs, d_hopper, d_spool_top, d_line2, d_hopcap):
        print(f())


# ====================================================================================================
def _silh(mesh, ax_a, ax_b):
    import shapely
    V = np.asarray(mesh.vertices)[:, [ax_a, ax_b]]
    tri = V[np.asarray(mesh.faces)]
    area = 0.5 * np.abs((tri[:, 1, 0] - tri[:, 0, 0]) * (tri[:, 2, 1] - tri[:, 0, 1]) - (tri[:, 2, 0] - tri[:, 0, 0]) * (tri[:, 1, 1] - tri[:, 0, 1]))
    tri = tri[area > 1e-6]
    polys = shapely.polygons(tri)
    return shapely.union_all(shapely.buffer(polys, 0.05))

def _draw_geom(ax, g, fc, ec=INK, lw=0.3, z=2):
    geoms = list(g.geoms) if hasattr(g, "geoms") else [g]
    for pg in geoms:
        if pg.is_empty or pg.geom_type != "Polygon": continue
        ax.add_patch(Polygon(np.array(pg.exterior.coords), closed=True, fc=fc, ec=ec, lw=lw, zorder=z))
        for ring in pg.interiors:
            ax.add_patch(Polygon(np.array(ring.coords), closed=True, fc="white", ec=ec, lw=lw, zorder=z + 0.01))

COL = {"print": PRINT, "alu": "#D5DAE0", "steel": "#B7C0CC", "black": "#4A4F57", "brass": BRASS, "heater": "#3B3F45", "copper": "#C0562B",
       "red": "#C0242B", "spool": "#9DB2E6", "filament": "#E9D44C", "tpu": "#2E7D4F"}

def d_views(parts):
    W, H = 11.8, 6.4
    fig = plt.figure(figsize=(W, H), dpi=300)
    x0, x1 = -330, 1670
    sc_in = W / (x1 - x0)
    zs0, zs1 = -112, 580
    hs = (zs1 - zs0) * sc_in
    axs = fig.add_axes([0.0, (H - hs - 0.05) / H, 1.0, hs / H]); axs.set_xlim(x0, x1); axs.set_ylim(zs0, zs1); axs.set_aspect("equal"); axs.axis("off")
    ys0, ys1 = -370, 130
    ht = (ys1 - ys0) * sc_in
    axt = fig.add_axes([0.0, 0.01, 1.0, ht / H]); axt.set_xlim(x0, x1); axt.set_ylim(ys0, ys1); axt.set_aspect("equal"); axt.axis("off")
    order = {"frame": 0, "electronics": 1, "drive": 2, "barrel": 3, "feed": 3, "cooling": 2, "puller": 2, "spooler": 2, "filament": 4}
    for q in sorted(parts, key=lambda q: order.get(q.group, 2)):
        for ax, (a_, b_) in ((axs, (0, 2)), (axt, (0, 1))):
            try:
                g = _silh(q.mesh, a_, b_)
            except Exception:
                continue
            _draw_geom(ax, g, COL.get(q.color, STEEL), lw=0.25, z=order.get(q.group, 2))
    ax = axs
    ax.annotate("", xy=(-305, 565), xytext=(1640, 565), arrowprops=dict(arrowstyle="<|-|>", color=RED, lw=0.6, mutation_scale=5), zorder=9)
    txt(ax, 667, 572, "overall length 1945  (control box to spool flange)", 8, RED)
    txt(ax, -320, 380, "SIDE VIEW (from -Y)", 8, INK, ha="left")
    txt(ax, 640, -104, "screw axis Z = 0 | rail top Z = -85 | height 589 incl. agitator motor (rails to motor top 484 + 105)", 6.3, GREY, ha="left", va="top")
    for xa, xb, label in ((-205, 690, "MODULE 1 | EXTRUDER"), (700, 1240, "MODULE 2 | COOLING + PULLER"), (1245, 1640, "MODULE 3 | SPOOLER")):
        hdim(axs, xa, xb, 512, label, dy=3.0, fs=7)
    txt(axt, -185, -214, "CONTROL BOX\n240 x 170 x 110", 7, INK)
    txt(axt, 800, -372, "10 L RESERVOIR", 6.5, GREY)
    txt(axt, 40, -330, "TOP VIEW (from +Z)", 8, INK, ha="left")
    return save(fig, "d_views")

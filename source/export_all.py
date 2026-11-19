import os, math, sys
import cadquery as cq
import neomac as M
from neomac import box
OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # repo root
BED = 350.0
for d in ("stl", "step", "docs"): os.makedirs(f"{OUT}/{d}", exist_ok=True)
P = M.build(); R = []; ok = True
def chk(name, cond, detail=""):
    global ok; ok &= bool(cond); R.append(f"[{'PASS' if cond else 'FAIL'}] {name}  {detail}")
def vol(s):
    try: return s.val().Volume()
    except Exception: return 0.0
def inter(a, b):
    try: return vol(a.intersect(b))
    except Exception: return 0.0
ORI = {"front_down": ((1, 0, 0), 90), "rear_down": ((1, 0, 0), -90), "side_down": ((0, 1, 0), 90), "as_is": None}
def oriented(d):
    s = d["body"]
    if ORI[d["ori"]]: s = s.rotate((0, 0, 0), ORI[d["ori"]][0], ORI[d["ori"]][1])
    bb = s.val().BoundingBox(); return s.translate((-bb.xmin, -bb.ymin, -bb.zmin))
# ---- validity, export
seen = set(); rows = []
for n, d in P.items():
    s = d["shape"]
    chk(f"{n}: one valid solid", s.val().isValid() and s.solids().size() == 1)
    if not d["printed"]: continue
    key = n.rstrip("0123456789").rstrip("_")
    if key in seen: continue
    seen.add(key); qty = sum(1 for m in P if m.rstrip("0123456789").rstrip("_") == key)
    o = oriented(d); bb = o.val().BoundingBox()
    chk(f"{key}: fits {BED:.0f} bed", bb.xlen <= BED and bb.ylen <= BED and bb.zlen <= BED, f"{bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f}")
    cq.exporters.export(o, f"{OUT}/stl/{key}__x{qty}.stl", tolerance=0.02, angularTolerance=0.1)
    rows.append((key, qty, d["col"], bb.xlen, bb.ylen, bb.zlen, vol(o) / 1000))
asm = cq.Assembly()
colmap = {"plat": cq.Color(0.93, 0.91, 0.84), "black": cq.Color(0.08, 0.08, 0.08), "glass": cq.Color(0.2, 0.25, 0.3), "steel": cq.Color(0.6, 0.6, 0.62)}
for n, d in P.items(): asm.add(d["shape"], name=n, color=colmap[d["col"]])
asm.save(f"{OUT}/step/neomac_assembly.step")
# ---- interference (world frame)
names = [n for n in P]
worst = 0
for i, a_ in enumerate(names):
    for b_ in names[i + 1:]:
        A, B = P[a_]["shape"].val().BoundingBox(), P[b_]["shape"].val().BoundingBox()
        if A.xmax < B.xmin or B.xmax < A.xmin or A.ymax < B.ymin or B.ymax < A.ymin or A.zmax < B.zmin or B.zmax < A.zmin: continue
        v = inter(P[a_]["shape"], P[b_]["shape"])
        if v > 0.5: chk(f"no interference {a_} / {b_}", False, f"{v:.1f} mm3")
        worst = max(worst, v)
chk("pairwise interference of all bodies < 0.5 mm3", worst <= 0.5, f"worst {worst:.2f} mm3")
# ---- body-frame probes
fr, cv = M.make_frame(), M.make_cover()
vga = box(M.CX - 16, M.CX + 16, 7.9, 23.9, M.TR_Z0 + 0.5, 58)        # DB15 plug shell 32 x 16, hanging below a board taped to the LCD
chk("VGA plug shell clears frame trough and cover mouth", inter(vga, fr) < 0.01 and inter(vga, cv) < 0.01, "32 x 16 mm shell, 40 mm long")
brd = box(M.BAY_X0 + 22, M.BAY_X1 - 22, M.LCD_Y0 + M.LCD_T_STRIP, M.T + M.BAY_IN_H - 0.3, 58, M.BAY_Z1 - 22)
chk("board stack envelope inside bay", inter(brd, cv) < 0.01 and inter(brd, fr) < 0.01, f"{M.BAY_X1 - M.BAY_X0 - 44:.0f} x {M.BAY_Z1 - 22 - 58:.0f} mm footprint, {M.T + M.BAY_IN_H - 0.3 - M.LCD_Y0 - M.LCD_T_STRIP:.1f} mm above the LCD's thick strip ({M.T + M.BAY_IN_H - 0.3 - M.LCD_Y0 - M.LCD_T_SIDE:.1f} above the thin back)")
mouth_h = M.T + M.BAY_IN_H - M.TR_Y
chk("mouth height at trough >= 20", mouth_h >= 20, f"{mouth_h:.1f} mm over {M.TR_X1 - M.TR_X0:.0f} mm width; {M.BAY_IN_H:.1f} mm elsewhere")
lid, plate = M.make_bay_lid(), M.make_cover_plate()
def steep(shape, arch_span=0.0):
    """Area of downward faces steeper than 45 deg (off the bed) in print orientation. Faces no wider than
    arch_span in X are small round-hole tops (vent slot ends): counted separately, they bridge like any small hole."""
    o = shape.rotate((0, 0, 0), (1, 0, 0), -90); zb = o.val().BoundingBox(); bad = 0.0; arches = 0
    for f in o.faces().vals():
        n = f.normalAt()
        if n.z < -0.72 and f.Center().z > zb.zmin + 0.3:
            if f.BoundingBox().xlen <= arch_span + 0.05: arches += 1
            else: bad += f.Area()
    return (bad, arches) if arch_span else bad
lb, la = steep(lid, M.VENT_W)
chk("bay lid: no overhang beyond 45 deg when printed ceiling down, apart from the vent slot ends", lb < 1.0, f"{lb:.1f} mm2 elsewhere; {la} slot ends are {M.VENT_W} mm round arches")
chk("cover plate: no overhang beyond 45 deg when printed outer face down", steep(plate) < 1.0, f"{steep(plate):.1f} mm2")
for i, (x, z) in enumerate(M.LID_POSTS):
    chk(f"lid post {i + 1} lands on a plate ear", inter(box(x - 4, x + 4, M.T + 0.5, M.T + 2.5, z - 4, z + 4), plate) > 100)
lcd = M.make_lcd_envelope()
tabs = box(M.LCD_X0 - M.TAB, M.LCD_X1 + M.TAB, M.LCD_Y0, M.LCD_Y0 + 1.0, M.LCD_Z0, M.LCD_Z1)
chk("LCD + side tabs clear the pocket", inter(lcd, fr) < 0.01 and inter(tabs, fr) < 0.01, f"room past the tabs {M.LCD_X0 - M.TAB - M.PK_X0:.2f} / {M.PK_X1 - M.LCD_X1 - M.TAB:.2f}, below {M.LCD_Z0 - M.PK_Z0:.1f}, above {M.PK_Z1 - M.LCD_Z1:.1f}")
bw, bh = M.LCD_W - M.MARG["left"] - M.MARG["right"], M.LCD_H - M.MARG["top"] - M.MARG["bottom"]
chk("aperture sits inside the panel's black border and outside the lit area", M.LIT_W < M.AP_W < bw and M.LIT_H < M.AP_H < bh, f"black border {bw:.1f} x {bh:.1f}, aperture {M.AP_W} x {M.AP_H}, lit {M.LIT_W} x {M.LIT_H}: {(bw - M.AP_W) / 2:.2f}/{(bh - M.AP_H) / 2:.2f} mm of black hidden, {(M.AP_W - M.LIT_W) / 2:.2f}/{(M.AP_H - M.LIT_H) / 2:.2f} mm of black showing")
chk("frame bottom edge is a full flat face on the bed (no raised lip)", abs(vol(fr.intersect(box(-1, M.W + 1, -1, M.GR_Y, -1, 2.0))) - M.W * M.GR_Y * 2.0) < 4.0, "only the two side-edge chamfers are missing from the bottom 2 mm of the front wall")
bs = M.make_base(); full = M.place(box(M.BADGE_X - M.BADGE / 2, M.BADGE_X + M.BADGE / 2, -0.01, M.BADGE_D, M.BADGE_Z - M.BADGE / 2, M.BADGE_Z + M.BADGE / 2))
bfill = M.place(box(M.BADGE_X - M.BADGE / 2 - 2, M.BADGE_X + M.BADGE / 2 + 2, M.BADGE_D, M.BADGE_D + 3, M.BADGE_Z - M.BADGE / 2 - 2, M.BADGE_Z + M.BADGE / 2 + 2))
chk("badge recess: square, full depth, on flat face with solid wall behind", inter(full, bs) < 0.01 and abs(inter(bfill, bs) - vol(bfill)) < 1.0, f"{M.BADGE:.0f} x {M.BADGE:.0f} x {M.BADGE_D} mm, {M.LINE_Z0 - (M.BADGE_Z + M.BADGE / 2):.1f} mm below the lowest line, {M.T - M.BADGE_D:.1f} mm wall behind")
chk("black area centred on aperture", abs((M.LCD_X0 + M.MARG['left'] + M.LCD_X1 - M.MARG['right']) / 2 - M.CX) < 1e-6 and abs((M.LCD_Z0 + M.MARG['bottom'] + M.LCD_Z1 - M.MARG['top']) / 2 - M.CZ) < 1e-6)
for i, c in enumerate(M.BRACKETS):
    cl = M.make_bracket(*c)
    lo = [(c[0] - M.BR_HOLE + M.BR_L - (M.LCD_X0 + dx)) if c[2] > 0 else ((M.LCD_X1 + dx) - (c[0] + M.BR_HOLE - M.BR_L)) for dx in (-4.75, 0, 4.75)]
    chk(f"bracket {i + 1} overlaps the panel edge >= 3 mm over the whole X range", min(lo) >= 3.0 and inter(cl, lcd) < 0.01, f"overlap {min(lo):.2f} to {max(lo):.2f}; foam gap to thin back {M.SEAT_Y - M.PAD_DROP - M.LCD_Y0 - M.LCD_T_SIDE:.1f}")
chk("bracket and stop screw heads under cover", M.SEAT_Y + M.FOOT_T + 1.65 <= M.T, f"button head top at {M.SEAT_Y + M.FOOT_T + 1.65:.2f} vs cover at {M.T}")
brs = [M.make_bracket(*c) for c in M.BRACKETS]
def clear(sx):
    return inter(sx, fr) < 0.01 and inter(sx, plate) < 0.01 and all(inter(sx, b_) < 0.01 for b_ in brs)
for side, nm in ((1, "left"), (-1, "right")):
    for v in M.HS_VARIANTS:
        okv = all(clear(M.make_height_stop(side, dz, v)) for dz in (-5, 0, 5)) and inter(M.make_height_stop(side, 0, v), lcd) < 0.01
        chk(f"height stop {v} {nm}: clear of frame, cover and brackets over +/-5 mm", okv)
        if v != "standard":
            d_ = dict(body=M.make_height_stop(side, 0, v), ori="rear_down"); o = oriented(d_); bb = o.val().BoundingBox()
            cq.exporters.export(o, f"{OUT}/stl/height_stop_{v}_{nm}__x1.stl", tolerance=0.02)
            rows.append((f"height_stop_{v}_{nm}", 1, "black", bb.xlen, bb.ylen, bb.zlen, vol(o) / 1000))
    for v in M.XS_VARIANTS:
        out = 4.0 if v == "low" else 4.5
        rng = (-out, 0, 5) if side > 0 else (-5, 0, out)
        okv = all(clear(M.make_x_stop(side, dx, v)) for dx in rng) and inter(M.make_x_stop(side, 0, v), lcd) < 0.01
        chk(f"x stop {v} {nm}: clear of frame, cover and brackets from {out:.1f} mm outward to 5 mm inward", okv)
        if v != "full":
            d_ = dict(body=M.make_x_stop(side, 0, v), ori="rear_down"); o = oriented(d_); bb = o.val().BoundingBox()
            cq.exporters.export(o, f"{OUT}/stl/x_stop_{v}_{nm}__x1.stl", tolerance=0.02)
            rows.append((f"x_stop_{v}_{nm}", 1, "black", bb.xlen, bb.ylen, bb.zlen, vol(o) / 1000))
chk("front skin under insert holes >= 2.5", min(M.T - M.INS_DEPTH, M.SEAT_Y - M.INS_DEPTH) >= 2.5, f"{M.SEAT_Y - M.INS_DEPTH:.1f} (brackets, stops), {M.T - M.INS_DEPTH:.1f} (cover)")
chk("wall behind contour lines at trough >= 5", M.TR_Y - M.LINE_D >= 5, f"{M.TR_Y - M.LINE_D:.1f}")
chk("joint insert: skin to the front face >= 3, clear of contour lines and groove", (M.T - M.FLG_T - M.FLG_CLR - M.INS_DEPTH) >= 3.0 and M.JOINT_Z - M.INS_D / 2 >= max(M.GR_DEPTH, M.LINE_Z0 + M.LINE_PITCH + M.LINE_W) + 0.7 and M.JOINT_Z + M.INS_D / 2 <= M.LINE_Z0 + 2 * M.LINE_PITCH - 0.7, f"skin {M.T - M.FLG_T - M.FLG_CLR - M.INS_DEPTH:.2f}; hole z {M.JOINT_Z - M.INS_D / 2:.1f}-{M.JOINT_Z + M.INS_D / 2:.1f} between lines at {M.LINE_Z0 + M.LINE_PITCH + M.LINE_W:.1f} and {M.LINE_Z0 + 2 * M.LINE_PITCH:.1f}")
chk("floppy notch leaves wall in front of tongue", M.GR_Y - M.FL_D >= 1.2, f"{M.GR_Y - M.FL_D:.1f}")
chk("ballast channel skins >= 3", (M.T - M.CH_T) / 2 >= 3, f"{(M.T - M.CH_T) / 2:.1f}; bar clearance {M.CH_W - M.BAR_W:.1f} x {M.CH_T - M.BAR_T:.2f}")
# ---- stability estimate (assumptions stated)
RHO = 1.24e-3; FILL = dict(base=0.45, front_frame=0.60, cover_plate=0.9, bay_lid=0.9)
def mc(n, m=None):
    s = P[n]["shape"]; c = s.val().Center()
    return (m if m is not None else vol(s) * RHO * FILL.get(n, 0.9), c.y, c.z)
def com(items):
    m = sum(i[0] for i in items); return m, sum(i[0] * i[1] for i in items) / m, sum(i[0] * i[2] for i in items) / m
bay_c = M.to_world((M.CX, M.T + 8, 115))
head = [mc(n) for n in P if P[n]["printed"]] + [mc("viz_lcd", 200.0), (120.0, bay_c[1], bay_c[2])]
steel = [mc(f"viz_ballast_{i}", vol(P[f"viz_ballast_{i}"]["shape"]) * 7.85e-3) for i in (1, 2)]
piv_f = M.RISER_Y + M.R_FOOT * math.tan(math.radians(90 - M.TILT) / 2); piv_r = M.FOOT_END - 3
tip = {}
for label, items in (("no ballast", head), ("one bar (rear)", head + steel[:1]), ("two bars", head + steel)):
    m, y, z = com(items); tip[label] = (m, math.degrees(math.atan2(y - piv_f, z)), math.degrees(math.atan2(piv_r - y, z)))
chk("forward tip angle with two bars >= 15 deg", tip["two bars"][1] >= 15, f"{tip['two bars'][1]:.1f}")
bbs = [d["shape"].val().BoundingBox() for d in P.values()]
dims = (max(b.xmax for b in bbs) - min(b.xmin for b in bbs), max(b.ymax for b in bbs) - min(b.ymin for b in bbs), max(b.zmax for b in bbs))
with open(f"{OUT}/docs/validation_report.txt", "w") as f:
    f.write("Neo-Mac monitor v0.11 -- CAD checks only (nothing sliced or printed)\n\n" + "\n".join(R))
    f.write(f"\n\nOverall: {dims[0]:.0f} W x {dims[1]:.0f} D x {dims[2]:.0f} H mm\n\nStability estimate (assumed: PLA 1.24 g/cm3 at 45-70 % effective fill, LCD 200 g, boards+cables 120 g, 220 mm steel bars):\n")
    for k, (m, fwd, back) in tip.items(): f.write(f"  {k:16s} mass {m:5.0f} g   tips forward at {fwd:5.1f} deg, backward at {back:5.1f} deg\n")
    f.write("\nPrint list (print orientation, mm):\n")
    for r in rows: f.write(f"  {r[0]:16s} x{r[1]}  {r[2]:6s} {r[3]:6.1f} x {r[4]:6.1f} x {r[5]:6.1f}   {r[6]:6.1f} cm3 solid\n")
print(open(f"{OUT}/docs/validation_report.txt").read()); print("ALL PASS" if ok else "FAILURES")

"""Neo-Mac monitor v0.11 -- iPad 1/2 LCD in a ribbon-profile classic-Mac shell (no Pi).
Body frame (frame, cover, LCD): +X viewer's right, Y=0 front face, +Y to the rear, Z=0 at the seam, +Z up.
World frame: body frame tilted back TILT about X and placed on the base stub; desk at Z=0.
All dimensions mm.  CadQuery 2.x.
"""
import math
import cadquery as cq
from cadquery.selectors import BoxSelector

# ------------------------------------------------------------------ parameters
W = 250.0            # overall width
T = 12.0             # ribbon / frame thickness
TILT = 8.0
EDGE_CH = 0.6        # small 45 deg break on otherwise sharp outer edges
H = 244.0            # front frame height above the seam
TOPM, CHIN = 27.1, 67.1
AP_W, AP_H = 199.0, 149.8          # aperture in the platinum face: lit area + 0.95/1.0 mm, inside the panel's black border
AP_CH = 2.4                        # 45 deg aperture chamfer depth
CX, CZ = W / 2, H - TOPM - AP_H / 2
# LCD (measured on Mike's panel, tabs excluded)
LCD_W, LCD_H = 208.0, 166.7
LCD_T_SIDE, LCD_T_STRIP = 2.8, 5.5
MARG = dict(left=5.0, right=2.5, bottom=6.0, top=9.5)     # panel edge -> black area
LIT_W, LIT_H = 197.1, 147.8
TAB = 4.0
FLOOR = 3.0          # pocket floor (front wall thickness)
BEZ_T = 0.0          # no separate bezel: the panel's own black border shows in the aperture
PK_X0, PK_X1, PK_Z0, PK_Z1 = 11.0, W - 13.5, 44.0, 233.0     # LCD pocket: 4.75 mm past the tabs each side, 16.4 below, 5.9 above
LCD_CX = CX - (MARG["left"] - MARG["right"]) / 2
LCD_CZ = CZ + (MARG["top"] - MARG["bottom"]) / 2
LCD_X0, LCD_X1 = LCD_CX - LCD_W / 2, LCD_CX + LCD_W / 2
LCD_Z0, LCD_Z1 = LCD_CZ - LCD_H / 2, LCD_CZ + LCD_H / 2
LCD_Y0 = FLOOR + BEZ_T
# contour lines / seam / floppy
LINE_W, LINE_D, LINE_PITCH, LINE_N, LINE_INSET = 2.2, 1.2, 8.0, 5, 18.0
LINE_Z0 = -2.4       # the lowest line (and the floppy slot) is in the base, just below the seam; frame lines follow at LINE_PITCH
FL_X0, FL_X1, FL_H, FL_D = CX, CX + 92.0, 5.0, 3.0
BADGE, BADGE_D, BADGE_X, BADGE_Z = 12.0, 1.6, 29.0, -14.0   # square badge recess on the base, same centre as before
# tongue and groove (wedge tongue: flat front face, 45 deg rear face)
GR_Y, GR_DEPTH, GR_TIP = 4.5, 5.0, 2.0
FLG_T, FLG_H, FLG_CLR = 3.0, 17.5, 0.15       # base flange lapping behind the frame, recessed flush; carries the joint screws
TG_CLR = 0.2
JOINT_X = (30.0, CX, W - 30.0); JOINT_Z = 10.7   # between the first two frame lines, so the insert has a full skin
# cable trough in the rear of the chin
TR_X0, TR_X1, TR_Y, TR_Z0 = CX - 75.0, CX + 75.0, 7.0, 18.0
# cover + controller bay
CV_T, CV_INSET, CV_Z0 = 3.0, 2.0, 42.0
BAY_X0, BAY_X1, BAY_Z1 = 22.0, W - 22.0, 180.0
BAY_IN_H = 21.0      # clear height inside the bay above the frame's rear face (16 until v0.10)
BAY_TAPER = 30.0     # lid wall angle from the print direction; 30 = 60 deg from the bed (45 until v0.10)
VENT_W, VENT_L, VENT_PITCH = 3.5, 12.0, 8.0   # rounded vent slots in the lid's top wall, running down the slope
VENT_X0, VENT_X1 = 46.0, W - 46.0             # slot centres stay clear of the upper screw posts
VENT_T = 11.0        # slot centre, measured down the slope from the cover plate along the top wall's outer face
BAY_WALL = 2.4
INS_D, INS_DEPTH = 4.2, 5.5          # heat-set insert hole (M3, 5 mm long insert)
CV_SCREWS = [(5.5, 89.5), (5.5, 145.0), (5.5, 199.0), (W - 5.5, 89.5), (W - 5.5, 145.0), (W - 5.5, 199.0), (CX, 238.5)]
# LCD mounting: hold-down brackets on the side rims, optional sliding stops for height and X
SEAT_Y, FOOT_T = 8.0, 2.2            # seats are recessed so M3 button heads stay under the cover
PAD_DROP = 1.2                       # block under each bracket toe so the foam gap to the panel stays 1.0 mm
BR_L, BR_W, BR_HOLE = 24.5, 30.0, 4.0
BRACKETS = [(7.0, 110.0, +1), (7.0, 180.0, +1), (W - 9.5, 110.0, -1), (W - 9.5, 180.0, -1)]   # hole x, z, direction toward panel
TRAVEL = 5.0                         # stop slot travel, +/-
HS_FOOT_L, HS_ARM_REACH, HS_ARM_H = 24.0, 29.0, 6.0      # height stop
XS_FOOT_L, XS_FOOT_H, XS_ARM_W, XS_ARM_Z0 = 24.0, 8.0, 4.0, 205.0
XS_NOTCH, XS_NOTCH_Z0 = 3.0, 204.0   # relief in the pocket wall at the top corners so X-stop arms can move outward   # X stop
STOP_Y0 = FLOOR + BEZ_T + 0.3
# base ribbon
FOOT_END, RISER_Y, RISER_L, STEP, STUB = 178.0, 40.0, 46.0, 26.0, 36.0
R_FOOT, R_S = 13.0, 9.0
BAR_W, BAR_T = 25.4, 4.76            # 1" x 3/16" steel flat bar
CH_W, CH_T = 26.2, 5.4
CH_Y = (FOOT_END - 4.0 - CH_W, FOOT_END - 4.0 - 2 * CH_W - 3.0)   # two channels, rear-most first

a = math.radians(TILT); U = (math.sin(a), math.cos(a)); N = (-math.cos(a), math.sin(a))

def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))

def profile(pts, x0=0.0, x1=W):
    return cq.Workplane("YZ").polyline(pts).close().extrude(x1 - x0).translate((x0, 0, 0))

def cyl_y(x, z, d, y0, y1):
    return cq.Workplane("XZ").circle(d / 2).extrude(-(y1 - y0)).translate((x, y0, z))

def add(p, v, k): return (p[0] + v[0] * k, p[1] + v[1] * k)

# ------------------------------------------------------------------ base
P0 = (FOOT_END, T / 2); P1 = (RISER_Y, T / 2); P2 = add(P1, U, RISER_L); P3 = add(P2, N, STEP); P4 = add(P3, U, STUB)
ORG = add(P4, N, T / 2)              # world (Y,Z) of the body-frame origin: front edge of the seam

def place(s):
    return s.rotate((0, 0, 0), (1, 0, 0), -TILT).translate((0, ORG[0], ORG[1]))

def to_world(p):
    x, y, z = p
    return (x, ORG[0] + y * math.cos(a) + z * math.sin(a), ORG[1] - y * math.sin(a) + z * math.cos(a))

def _offset(pts, d):
    """Mitred offset of an open polyline; d>0 = left of travel."""
    lines = []
    for p, q in zip(pts, pts[1:]):
        l = math.hypot(q[0] - p[0], q[1] - p[1]); n = (-(q[1] - p[1]) / l, (q[0] - p[0]) / l)
        lines.append(((p[0] + n[0] * d, p[1] + n[1] * d), (q[0] + n[0] * d, q[1] + n[1] * d)))
    out = [lines[0][0]]
    for (p1, p2), (p3, p4) in zip(lines, lines[1:]):
        x1, y1, x2, y2, x3, y3, x4, y4 = *p1, *p2, *p3, *p4
        den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        px = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / den
        py = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / den
        out.append((px, py))
    out.append(lines[-1][1]); return out

def make_base():
    pts = [P0, P1, P2, P3, P4]
    L, R = _offset(pts, T / 2), _offset(pts, -T / 2)
    s = profile(L + R[::-1])
    radii = {1: R_FOOT, 2: R_S, 3: R_S}
    for i, r in radii.items():
        p0, p, p1 = pts[i - 1], pts[i], pts[i + 1]
        cross = (p[0] - p0[0]) * (p1[1] - p[1]) - (p[1] - p0[1]) * (p1[0] - p[0])
        inner, outer = (L[i], R[i]) if cross > 0 else (R[i], L[i])
        for q, rr in ((inner, r - T / 2), (outer, r + T / 2)):
            e = 0.4
            s = s.edges(BoxSelector((-1, q[0] - e, q[1] - e), (W + 1, q[0] + e, q[1] + e))).fillet(rr)
    # wedge tongue (body frame), placed on the stub
    tip = GR_DEPTH - 2 * TG_CLR
    ty0 = GR_Y + TG_CLR; ty1 = GR_Y + GR_TIP - TG_CLR
    yf = T - FLG_T
    zr = tip - (yf - ty1)                                    # valley where the 45 deg rear face meets the flange
    tongue = profile([(ty0, -1.0), (ty0, tip), (ty1, tip), (yf, zr), (yf, FLG_H), (T, FLG_H), (T, -1.0)])
    s = s.union(place(tongue))
    def outer(e):                                            # skip every edge that mates with the frame (seam, tongue, flange front and top)
        c = e.Center(); dy, dz = c.y - ORG[0], c.z - ORG[1]
        yb, zb = dy * math.cos(a) - dz * math.sin(a), dy * math.sin(a) + dz * math.cos(a)
        return not (zb > -0.05 and yb < T - 0.05)
    for sel in ("<X", ">X"):                                 # break the outline edges of both side faces
        s = s.newObject([e for e in s.faces(sel).edges().vals() if outer(e)]).chamfer(EDGE_CH)
    for x in JOINT_X:                                        # clearance holes for the M3 joint screws
        s = s.cut(place(cyl_y(x, JOINT_Z, 3.4, yf - 1, T + 1)))
    s = s.cut(place(box(BADGE_X - BADGE / 2, BADGE_X + BADGE / 2, -1, BADGE_D, BADGE_Z - BADGE / 2, BADGE_Z + BADGE / 2)))   # badge recess on the lower band
    s = s.cut(place(box(-1, W + 1, -1, LINE_D, LINE_Z0, 0.01)))                       # lowest contour line; the seam is its top edge
    s = s.cut(place(box(FL_X0, FL_X1, -1, FL_D, -FL_H, 0.01)))                        # floppy slot notch
    s = s.cut(place(cyl_y(FL_X1 + 8.0, LINE_Z0 / 2, 1.6, -1, LINE_D + 1.5)))          # eject pinhole
    for y in CH_Y:                                           # ballast channels, open at both sides
        s = s.cut(box(-1, W + 1, y, y + CH_W, (T - CH_T) / 2, (T + CH_T) / 2))
    s = s.cut(profile([(FOOT_END + 1, T - 3), (FOOT_END - 3, T + 1), (FOOT_END + 1, T + 1)], -1, W + 1))   # rear top bevel
    return s

# ------------------------------------------------------------------ front frame
def make_frame():
    s = box(0, W, 0, T, 0, H)
    s = s.edges("|Y").edges(">Z").fillet(10.0)
    s = s.faces("<Y").edges("not <Z").chamfer(EDGE_CH)       # same edge break as the base, so the side edges run straight through the seam
    s = s.faces(">Y").edges("not <Z").chamfer(EDGE_CH)       # rear perimeter (sides and top)
    # aperture: 45 deg flare then straight through the floor
    flare = cq.Workplane("XY").rect(AP_W + 2 * AP_CH, AP_H + 2 * AP_CH).extrude(AP_CH, taper=45).rotate((0, 0, 0), (1, 0, 0), -90)
    s = s.cut(flare.translate((CX, 0, CZ))).cut(box(CX - AP_W / 2, CX + AP_W / 2, AP_CH - 0.01, FLOOR + 0.1, CZ - AP_H / 2, CZ + AP_H / 2))
    s = s.cut(box(PK_X0, PK_X1, FLOOR, T + 0.1, PK_Z0, PK_Z1))                       # LCD pocket, open to the rear
    for i in range(1, LINE_N + 1):                                                    # contour lines (closed grooves; the bottom edge stays flat on the bed)
        z = LINE_Z0 + i * LINE_PITCH
        s = s.cut(box(LINE_INSET, W - LINE_INSET, -1, LINE_D, z, z + LINE_W))
    yr = T - FLG_T - FLG_CLR                                                          # rebate face for the base flange
    s = s.cut(profile([(GR_Y, -1.0), (GR_Y, GR_DEPTH), (GR_Y + GR_TIP, GR_DEPTH), (yr, GR_DEPTH - (yr - GR_Y - GR_TIP)), (yr, -1.0)]))   # groove
    s = s.cut(box(-1, W + 1, yr, T + 1, -1, FLG_H + 0.3))                             # rear rebate
    for x in JOINT_X:
        s = s.cut(cyl_y(x, JOINT_Z, INS_D, yr - INS_DEPTH, yr + 0.1))                 # heat-set inserts for the joint screws
    s = s.cut(box(TR_X0, TR_X1, TR_Y, T + 0.1, TR_Z0, PK_Z0 + 0.1))                   # cable trough
    s = s.cut(profile([(TR_Y, TR_Z0 + 0.01), (T + 0.1, TR_Z0 - (T + 0.1 - TR_Y)), (T + 0.1, TR_Z0 + 0.01)], TR_X0, TR_X1))
    for x, z in CV_SCREWS:
        s = s.cut(cyl_y(x, z, INS_D, T - INS_DEPTH, T + 1))
    for hx, z, d in BRACKETS:                                                         # hold-down bracket seats
        x0, x1 = (hx - BR_HOLE - 0.3, PK_X0 + 0.1) if d > 0 else (PK_X1 - 0.1, hx + BR_HOLE + 0.3)
        s = s.cut(box(x0, x1, SEAT_Y, T + 0.1, z - BR_W / 2 - 0.4, z + BR_W / 2 + 0.4))
        s = s.cut(cyl_y(hx, z, INS_D, SEAT_Y - INS_DEPTH, SEAT_Y + 0.1))
    for side in (+1, -1):                                                             # height-stop seats on the side rims
        hx = 7.0 if side > 0 else W - 9.5
        x0, x1 = (hx - 4.3, PK_X0 + 0.1) if side > 0 else (PK_X1 - 0.1, hx + 4.3)
        zc = LCD_Z0 + 6.0
        s = s.cut(box(x0, x1, SEAT_Y, T + 0.1, PK_Z0, zc + HS_FOOT_L / 2 + TRAVEL + 0.3))
        s = s.cut(cyl_y(hx, zc, INS_D, SEAT_Y - INS_DEPTH, SEAT_Y + 0.1))
    for side in (+1, -1):                                                             # X-stop seats on the top rim
        e = LCD_X0 if side > 0 else LCD_X1
        xc = e + side * 8.0
        wall = (PK_X0 - XS_NOTCH) if side > 0 else (PK_X1 + XS_NOTCH)
        na, nb = sorted((wall, PK_X0 if side > 0 else PK_X1))
        s = s.cut(box(na, nb + 0.0, FLOOR, T + 0.1, XS_NOTCH_Z0, PK_Z1 + 0.01))                      # wall relief for the arm
        xa, xb = sorted((wall, xc + side * (XS_FOOT_L / 2 + TRAVEL + 0.3)))
        s = s.cut(box(xa, xb, SEAT_Y, T + 0.1, PK_Z1 - 0.1, PK_Z1 + 0.5 + XS_FOOT_H + 0.3))
        s = s.cut(cyl_y(xc, PK_Z1 + 0.5 + XS_FOOT_H / 2, INS_D, SEAT_Y - INS_DEPTH, SEAT_Y + 0.1))
    return s

# ------------------------------------------------------------------ back cover with controller bay
def _frustum(x0, x1, z1, y0, h, taper=45.0):
    zlow = -100.0
    f = cq.Workplane("XY").rect(x1 - x0, z1 - zlow).extrude(h, taper=taper).rotate((0, 0, 0), (1, 0, 0), -90)
    return f.translate(((x0 + x1) / 2, y0, (z1 + zlow) / 2))

LID_POSTS = [(32.5, 169.5), (W - 32.5, 169.5), (32.5, 58.0), (W - 32.5, 58.0)]   # x, z of the lid screw posts
POST_D = 9.0
WIN_X0, WIN_X1, WIN_Z1 = 27.0, W - 27.0, 175.0

def make_cover_plate():
    """Flat U-shaped plate, 3 mm. Prints outer face down. Ears reach into the window under the lid posts."""
    y0, y1 = T, T + CV_T
    s = box(CV_INSET, W - CV_INSET, y0, y1, CV_Z0, H - CV_INSET)
    s = s.edges("|Y").edges(">Z").fillet(8.0)
    s = s.faces(">Y").edges("not <Z").chamfer(1.0)
    win = box(WIN_X0, WIN_X1, y0 - 1, y1 + 1, CV_Z0 - 1, WIN_Z1)
    for x, z in LID_POSTS:                                     # leave an ear around each post
        ex0, ex1 = (WIN_X0 - 1, x + 6.0) if x < CX else (x - 6.0, WIN_X1 + 1)
        ez0, ez1 = (z - 6.5, WIN_Z1 + 1) if z > 100 else (CV_Z0 - 2, z + 6.5)
        win = win.cut(box(ex0, ex1, y0 - 2, y1 + 2, ez0, ez1))
    s = s.cut(win)
    for x, z in CV_SCREWS:
        s = s.cut(cyl_y(x, z, 3.4, y0 - 1, y1 + 1))
    for x, z in LID_POSTS:                                     # M3 flat head, countersunk on the inner face
        s = s.cut(cyl_y(x, z, 3.4, y0 - 1, y1 + 1))
        cs = cq.Workplane("XZ").circle(3.3).extrude(-1.6, taper=45).translate((x, y0 - 0.01, z))
        s = s.cut(cs)
    return s

def make_bay_lid():
    """Controller bay lid. Prints ceiling down: walls lean out at BAY_TAPER from vertical, posts rise from the walls. No supports.
    Footprint on the cover plate and the post positions are fixed by the plate; only depth and wall angle may change."""
    y1 = T + CV_T
    out_h = BAY_IN_H - CV_T + BAY_WALL
    k = BAY_WALL / math.cos(math.radians(BAY_TAPER))          # keeps the wall BAY_WALL thick, measured square to it
    outer = _frustum(BAY_X0, BAY_X1, BAY_Z1, y1, out_h, BAY_TAPER)
    inner = _frustum(BAY_X0 + k, BAY_X1 - k, BAY_Z1 - k, y1 - 0.01, BAY_IN_H - CV_T + 0.01, BAY_TAPER)
    s = outer.cut(inner)
    for x, z in LID_POSTS:
        post = cyl_y(x, z, POST_D, y1, y1 + out_h - 0.5).intersect(outer)
        s = s.union(post)
    for x, z in LID_POSTS:
        s = s.cut(cyl_y(x, z, INS_D, y1 - 0.1, y1 + INS_DEPTH))
    s = s.cut(box(-10, W + 10, -10, 100, -200, CV_Z0))          # mouth plane
    return s.cut(vent_cutters())

def vent_cutters():
    """Stadium slots through the lid's sloping top wall. Long axis runs down the slope, so in print
    orientation (ceiling down) each slot only needs to bridge its rounded end, not its length."""
    ang = math.radians(BAY_TAPER)
    n = int((VENT_X1 - VENT_X0) // VENT_PITCH) + 1
    span = (n - 1) * VENT_PITCH; x0 = CX - span / 2
    c = None
    for i in range(n):
        sl = cq.Workplane("XY").slot2D(VENT_L, VENT_W, angle=90).extrude(12.0).translate((x0 + i * VENT_PITCH, 0, -8.0))
        c = sl if c is None else c.union(sl)
    # local Y -> down the slope (into the lid), local Z -> outward normal of the top wall
    c = c.rotate((0, 0, 0), (1, 0, 0), -BAY_TAPER)
    y1 = T + CV_T
    return c.translate((0, y1 + VENT_T * math.cos(ang), BAY_Z1 - VENT_T * math.sin(ang)))

def make_cover():
    return make_cover_plate().union(make_bay_lid())

# ------------------------------------------------------------------ small parts
def make_bracket(hx, z, d):
    """Hold-down bracket: foot on the rim seat, long toe over the panel's back edge (add a foam pad)."""
    x0, x1 = (hx - BR_HOLE, hx - BR_HOLE + BR_L) if d > 0 else (hx + BR_HOLE - BR_L, hx + BR_HOLE)
    s = box(x0, x1, SEAT_Y, SEAT_Y + FOOT_T, z - BR_W / 2, z + BR_W / 2)
    s = s.edges("|Y").fillet(2.0)
    px0, px1 = (PK_X0 + 0.6, x1) if d > 0 else (x0, PK_X1 - 0.6)                    # pad block under the toe, inside the pocket
    s = s.union(box(px0, px1, SEAT_Y - PAD_DROP, SEAT_Y + 0.01, z - BR_W / 2 + 2, z + BR_W / 2 - 2))
    return s.cut(cyl_y(hx, z, 3.4, SEAT_Y - 1, SEAT_Y + FOOT_T + 1))

def _slot_z(x, zc, y0, y1):
    return cyl_y(x, zc - TRAVEL, 3.4, y0, y1).union(cyl_y(x, zc + TRAVEL, 3.4, y0, y1)).union(box(x - 1.7, x + 1.7, y0, y1, zc - TRAVEL, zc + TRAVEL))

def _slot_x(xc, z, y0, y1):
    return cyl_y(xc - TRAVEL, z, 3.4, y0, y1).union(cyl_y(xc + TRAVEL, z, 3.4, y0, y1)).union(box(xc - TRAVEL, xc + TRAVEL, y0, y1, z - 1.7, z + 1.7))

RELIEF, RELIEF_ARM = 4.5, 3.0        # stand-off that clears a 4 mm mounting tab, and the arm thickness there
HS_VARIANTS = ("standard", "corner", "inboard")
XS_VARIANTS = ("full", "corner", "low")

def make_height_stop(side, dz=0.0, variant="standard"):
    """Slides up/down on a side rim; its arm sits under the panel's bottom edge. dz = offset from nominal.
    standard: touches the first 20 mm in from the corner.  corner: first 10 mm only.
    inboard: stands 4.5 mm clear of the edge for 25 mm from the corner (room for a tab), touches 25-50 mm in."""
    hx = 7.0 if side > 0 else W - 9.5
    pb = LCD_Z0 + dz; zc = pb + 6.0
    e = LCD_X0 if side > 0 else LCD_X1                       # panel side edge
    def bx(u0, u1, y0, y1, z0, z1):                          # u = distance inward from the rim-side foot edge
        o = hx + 4.0 * side
        x0, x1 = sorted((o + side * u0, o + side * u1))
        return box(x0, x1, y0, y1, z0, z1)
    top = SEAT_Y + FOOT_T
    foot = bx(-8.0, 8.0, SEAT_Y, top, zc - HS_FOOT_L / 2, zc + HS_FOOT_L / 2)      # carries on 8 mm into the pocket as a web
    edge_u = abs(e - (hx + 4.0 * side))                      # where the panel corner is, in u
    if variant == "standard":
        arm = bx(0.3, edge_u + 20.0, STOP_Y0, top, pb - HS_ARM_H, pb)
    elif variant == "corner":
        arm = bx(0.3, edge_u + 10.0, STOP_Y0, top, pb - HS_ARM_H, pb)
    elif variant == "inboard":
        low = bx(0.3, edge_u + 50.0, STOP_Y0, top, pb - RELIEF - HS_ARM_H, pb - RELIEF)
        riser = bx(0.3, 8.0, STOP_Y0, top, pb - RELIEF - HS_ARM_H, pb - HS_ARM_H + 0.01)
        pad = bx(edge_u + 25.0, edge_u + 50.0, STOP_Y0, top, pb - RELIEF - 0.01, pb)
        arm = low.union(pad)
        foot = foot.union(bx(-8.0, 8.0, SEAT_Y, top, pb - RELIEF - HS_ARM_H, zc))   # web down to the lowered arm
    else:
        raise ValueError(variant)
    return foot.union(arm).cut(_slot_z(hx, zc, SEAT_Y - 1, top + 1))

def make_x_stop(side, dx=0.0, variant="full"):
    """Slides left/right on the top rim; its arm hangs down beside the panel's side edge.
    full: touches the top 22 mm of the edge.  corner: top 9 mm only.
    low: stands 4.5 mm clear of the top 14 mm (room for a tab), touches 14-30 mm down."""
    e = (LCD_X0 if side > 0 else LCD_X1) + dx
    xc = e + side * 8.0; z0 = PK_Z1 + 0.5; top = SEAT_Y + FOOT_T; ztop = PK_Z1 - 0.3
    def bx(v0, v1, y0, y1, zz0, zz1):                        # v = distance outward from the panel edge
        x0, x1 = sorted((e - side * v0, e - side * v1))
        return box(x0, x1, y0, y1, zz0, zz1)
    foot = box(xc - XS_FOOT_L / 2, xc + XS_FOOT_L / 2, SEAT_Y, top, z0, z0 + XS_FOOT_H)
    if variant == "full":
        arm = bx(0, XS_ARM_W, STOP_Y0, top, XS_ARM_Z0, ztop); web_out = XS_ARM_W
    elif variant == "corner":
        arm = bx(0, XS_ARM_W, STOP_Y0, top, LCD_Z1 - 9.0, ztop); web_out = XS_ARM_W
    elif variant == "low":
        zr = LCD_Z1 - 14.0                                   # relief above this, contact below
        hi = bx(RELIEF, RELIEF + RELIEF_ARM, STOP_Y0, top, zr - 0.01, ztop)
        pad = bx(0, XS_ARM_W, STOP_Y0, top, LCD_Z1 - 30.0, zr)
        link = bx(0, RELIEF + RELIEF_ARM, STOP_Y0, top, zr - 6.0, zr)
        arm = hi.union(pad).union(link); web_out = RELIEF + RELIEF_ARM
    else:
        raise ValueError(variant)
    tie = bx(-8.0, web_out, SEAT_Y, top, PK_Z1 - 10.0, z0 + 0.01)                   # web from arm up to the foot
    footx = bx(-8.0, web_out, SEAT_Y, top, z0, z0 + XS_FOOT_H)                       # foot reaches out over the arm
    return foot.union(arm).union(tie).union(footx).cut(_slot_x(xc, z0 + XS_FOOT_H / 2, SEAT_Y - 1, top + 1))

def make_floppy_insert():
    return box(FL_X0 + 0.2, FL_X1 - 0.2, FL_D - 1.0, FL_D, -FL_H + 0.15, -0.15)

def make_plug():
    s = box(0, 10.0, 0, CH_W - 0.25, 0, CH_T - 0.25)
    return s.faces(">X").chamfer(0.8)

def make_lcd_envelope():
    s = box(LCD_X0, LCD_X1, LCD_Y0, LCD_Y0 + LCD_T_SIDE, LCD_Z0, LCD_Z1)
    sw = LCD_W * 0.85
    return s.union(box(LCD_CX - sw / 2, LCD_CX + sw / 2, LCD_Y0, LCD_Y0 + LCD_T_STRIP, LCD_Z0, LCD_Z0 + 12.0))

def build():
    """name -> dict(shape (world frame), body (print-frame source), colour, qty, ori)"""
    P = {}
    def put(name, body, col, qty=1, ori="front_down", world=None, printed=True):
        P[name] = dict(shape=world if world is not None else place(body), body=body, col=col, qty=qty, ori=ori, printed=printed)
    base = make_base()
    put("base", base, "plat", ori="side_down", world=base)
    put("front_frame", make_frame(), "plat")
    put("cover_plate", make_cover_plate(), "plat", ori="rear_down")
    put("bay_lid", make_bay_lid(), "plat", ori="rear_down")
    for i, c in enumerate(BRACKETS):
        put(f"lcd_bracket_{i + 1}", make_bracket(*c), "black", ori="rear_down")
    put("height_stop_standard_left", make_height_stop(+1), "black", ori="rear_down")
    put("height_stop_standard_right", make_height_stop(-1), "black", ori="rear_down")
    put("x_stop_full_left", make_x_stop(+1), "black", ori="rear_down")
    put("x_stop_full_right", make_x_stop(-1), "black", ori="rear_down")
    put("floppy_insert", make_floppy_insert(), "black")
    plug = make_plug()
    k = 0
    for y in CH_Y:
        for side in (0, 1):
            k += 1
            w = plug.translate((0, y + 0.125, (T - CH_T) / 2 + 0.125))
            if side: w = w.mirror("YZ").translate((W, 0, 0))
            put(f"ballast_plug_{k}", plug, "plat", ori="as_is", world=w)
    put("viz_lcd", make_lcd_envelope(), "glass", printed=False)
    for i, y in enumerate(CH_Y):
        bar = box(12, W - 12, y + (CH_W - BAR_W) / 2, y + (CH_W + BAR_W) / 2, (T - BAR_T) / 2, (T + BAR_T) / 2)
        put(f"viz_ballast_{i + 1}", bar, "steel", world=bar, printed=False)
    return P

def lit_quad():
    y = FLOOR + BEZ_T - 0.05
    return [to_world(p) for p in ((CX - LIT_W / 2, y, CZ - LIT_H / 2), (CX + LIT_W / 2, y, CZ - LIT_H / 2), (CX - LIT_W / 2, y, CZ + LIT_H / 2))]

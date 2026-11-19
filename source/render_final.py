"""Renders for the README: python render_final.py  ->  ../docs/images/*.png"""
import os
from PIL import Image, ImageDraw, ImageFont
import neomac as M
import render as R
from neomac import box

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, "docs", "images"); os.makedirs(IMG, exist_ok=True)
TEX = os.path.join(R.OUT, "screen.png")
if not os.path.exists(TEX): R.screen_image(TEX)
R.COL.update({"glass": (0.03, 0.03, 0.035), "steel": (0.55, 0.56, 0.58), "red": (0.80, 0.30, 0.20), "blue": (0.20, 0.42, 0.75)})
R.VIEWS.update({"side_l": (90, 0, True), "low": (-24, 3, False), "rear_hi": (155, 22, False), "rear_low": (168, 4, False),
                "sec": (90, 0, True), "open": (172, 6, False)})
NOQUAD = [(0, 0, -900), (1, 0, -900), (0, 0, -899)]
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf"
def font(sz, bold=False):
    try: return ImageFont.truetype(FONT % ("-Bold" if bold else ""), sz)
    except OSError: return ImageFont.load_default()
def img(name): return os.path.join(IMG, name)
def scene(parts, quad):
    return R.build_scene({n: (d["shape"], d["col"]) for n, d in parts.items()}, quad, TEX)

P = M.build(); q = M.lit_quad()

# ---- assembled views
acts = scene(P, q)
R.render(acts, "front34", (1400, 1200), img("01_front.png"), focal=(122, 60, 165))
R.render(acts, "rear34", (1200, 1100), img("02_rear.png"), focal=(122, 60, 165))
R.render(acts, "side_l", (1000, 900), img("03_side.png"), focal=(122, 90, 168))
R.render(acts, "low", (1200, 1000), img("04_chin.png"), focal=(122, 60, 90), dist=950)
R.render(acts, "rear_low", (1200, 1000), img("05_bay_opening.png"), focal=(122, 60, 120), dist=900)
R.VIEWS["vent"] = (160, 38, False)
R.render(acts, "vent", (1400, 900), img("10_vents.png"), focal=M.to_world((M.CX, M.T + M.CV_T + 10, 172)), dist=520)

# ---- exploded
e = {}
for n, d in P.items():
    s = d["shape"]; up, back = 0, 0
    if n in ("front_frame", "floppy_insert"): up = 55
    elif n == "viz_lcd": up, back = 55, 60
    elif n.startswith("lcd_bracket") or "_stop_" in n: up, back = 55, 110
    elif n == "cover_plate": up, back = 55, 165
    elif n == "bay_lid": up, back = 55, 225
    elif n.startswith("ballast_plug"): s = s.translate((-25 if s.val().Center().x < 100 else 25, 0, 0))
    elif n.startswith("viz_ballast"): s = s.translate((-150, 0, 0))
    e[n] = dict(shape=s.translate((0, M.U[0] * up - M.N[0] * back, M.U[1] * up - M.N[1] * back)), col=d["col"])
R.render(scene(e, NOQUAD), "rear_hi", (1400, 1200), img("07_exploded.png"), focal=(110, 160, 200), dist=2100)

# ---- LCD mounting, cover off, and the three stop variants
def open_back(hv, xv):
    show = {}
    for n, d in P.items():
        if n in ("cover_plate", "bay_lid") or n.startswith("viz_ballast") or "_stop_" in n: continue
        show[n] = dict(shape=d["shape"], col="red" if n.startswith("lcd_bracket") else d["col"])
    for side, nm in ((1, "l"), (-1, "r")):
        show[f"hs{nm}"] = dict(shape=M.place(M.make_height_stop(side, 0, hv)), col="blue")
        show[f"xs{nm}"] = dict(shape=M.place(M.make_x_stop(side, 0, xv)), col="blue")
    return scene(show, NOQUAD)

R.render(open_back("standard", "full"), "open", (1500, 1300), img("08_lcd_mounting.png"), focal=(125, 60, 215), dist=1000)
im = Image.open(img("08_lcd_mounting.png")); d = ImageDraw.Draw(im)
d.rectangle([0, 0, im.width, 80], fill=(236, 236, 238))
d.text((30, 16), "Cover removed, seen from the rear. Red: hold-down brackets.", font=font(24), fill=(40, 40, 44))
d.text((30, 48), "Blue: optional sliding stops (height at the bottom corners, X at the top corners).", font=font(24), fill=(40, 40, 44))
im.save(img("08_lcd_mounting.png"))

sets = [("standard", "full", "touch the first ~20 mm from each corner"),
        ("corner", "corner", "touch only the first ~10 mm from each corner"),
        ("inboard", "low", "stand 4.5 mm clear near the corner, touch further along")]
sheet = Image.new("RGB", (2460, 900), (236, 236, 238)); d = ImageDraw.Draw(sheet)
for i, (hv, xv, note) in enumerate(sets):
    p = os.path.join(R.OUT, f"_var_{hv}.png")
    R.render(open_back(hv, xv), "open", (900, 820), p, focal=(125, 60, 205), dist=1000)
    sheet.paste(Image.open(p).crop((90, 60, 890, 800)), (10 + i * 820, 150))
    d.text((40 + i * 820, 20), f"X stop: {xv}   /   Height stop: {hv}", font=font(27, True), fill=(30, 30, 34))
    d.text((40 + i * 820, 62), note, font=font(23), fill=(95, 95, 102))
d.text((40, 108), "Cover removed. Blue: sliding stops. Red: hold-down brackets. Mix variants per corner to suit your panel's tabs.", font=font(22), fill=(95, 95, 102))
sheet.save(img("09_stop_variants.png"))
print("renders written to", IMG)

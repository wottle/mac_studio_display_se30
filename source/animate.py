"""Exploded-to-assembled animation.

    python animate.py            -> ../docs/assembly.mp4 and ../docs/images/assembly.gif
    python animate.py --test     -> a few stills in _build/anim_test/ to check framing

Uses the standard assembly from neomac.build(): plain cover plate, `standard` height stops, `full` X stops.
"""
import os, sys, math, shutil, subprocess
import vtk
from PIL import Image
import neomac as M
import render as R

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FPS, SECONDS = 30, 16.0
W, H = 1280, 720
SS = 2                                     # supersampling factor
R.COL.update({"glass": (0.05, 0.05, 0.06), "steel": (0.55, 0.56, 0.58)})

def ease(t):                               # smooth in-out, clamped
    t = min(1.0, max(0.0, t)); return t * t * t * (t * (6 * t - 15) + 10)

def seg(t, t0, t1): return ease((t - t0) / (t1 - t0))

def body_vec(up=0.0, back=0.0, x=0.0):
    """Offset in world coordinates: `up` along the screen, `back` away from the screen, `x` sideways."""
    return (x, M.U[0] * up - M.N[0] * back, M.U[1] * up - M.N[1] * back)

def lerp(a, b, s): return tuple(p + (q - p) * s for p, q in zip(a, b))
ZERO = (0.0, 0.0, 0.0)

# ---- choreography: each part's exploded offset and the time window in which it moves home
FRAME_UP = 110.0
def offset(name, t):
    if name.startswith("viz_ballast"):
        i = int(name[-1]) - 1
        return lerp((-300.0, 0, 0), ZERO, seg(t, 1.2 + 0.35 * i, 2.6 + 0.35 * i))
    if name.startswith("ballast_plug"):
        k = int(name.split("_")[-1]); side = -1 if k % 2 else 1
        return lerp((60.0 * side, 0, 0), ZERO, seg(t, 3.0, 3.8))
    if name == "front_frame":
        return lerp(body_vec(up=FRAME_UP), ZERO, seg(t, 3.6, 5.0))
    if name == "floppy_insert":
        return lerp((0, -90.0, 0), ZERO, seg(t, 4.8, 5.6))
    if name == "viz_lcd":
        return lerp(body_vec(back=170), ZERO, seg(t, 5.4, 6.8))
    if name.startswith("lcd_bracket") or "_stop_" in name:
        order = ["height_stop", "x_stop", "lcd_bracket"]
        j = next(i for i, p in enumerate(order) if name.startswith(p))
        t0 = 6.8 + 0.35 * j
        return lerp(body_vec(back=230), ZERO, seg(t, t0, t0 + 1.0))
    if name == "bay_lid":                  # first onto the plate, then both onto the frame
        a = lerp(body_vec(back=420), body_vec(back=300), seg(t, 8.2, 9.2))
        return lerp(a, ZERO, seg(t, 9.4, 10.8))
    if name == "cover_plate":
        return lerp(body_vec(back=300), ZERO, seg(t, 9.4, 10.8))
    return ZERO

def camera(t):
    """(azimuth, elevation, distance, focal). Rear three-quarter while assembling, then round to the front."""
    s = seg(t, 11.2, 14.2)
    az = 135 + 15 * seg(t, 0, 11) - (150 + 30) * s          # ends at -30 (front, viewer's left)
    el = 22 - 12 * s
    dist = 2150 - 650 * seg(t, 1.0, 11.0) - 180 * s
    focal = lerp(lerp((150, 230, 215), (122, 120, 175), seg(t, 2.0, 11.0)), (125, 70, 150), s)
    return az, el, dist, focal

def screen_on(t): return seg(t, 13.6, 14.8)

def build():
    P = M.build()
    actors = {}
    for n, d in P.items():
        actors[n] = R.mesh_actor(d["shape"], R.COL[d["col"]], "anim_" + n)
    q = M.lit_quad()
    pl = vtk.vtkPlaneSource(); pl.SetOrigin(*q[0]); pl.SetPoint1(*q[1]); pl.SetPoint2(*q[2])
    tex_path = os.path.join(R.OUT, "screen.png")
    if not os.path.exists(tex_path): R.screen_image(tex_path)
    rd = vtk.vtkPNGReader(); rd.SetFileName(tex_path)
    tx = vtk.vtkTexture(); tx.SetInputConnection(rd.GetOutputPort()); tx.InterpolateOn()
    m = vtk.vtkPolyDataMapper(); m.SetInputConnection(pl.GetOutputPort())
    scr = vtk.vtkActor(); scr.SetMapper(m); scr.SetTexture(tx); scr.GetProperty().LightingOff()
    g = vtk.vtkPlaneSource(); g.SetOrigin(-4000, -4000, -0.05); g.SetPoint1(4000, -4000, -0.05); g.SetPoint2(-4000, 4000, -0.05)
    gm = vtk.vtkPolyDataMapper(); gm.SetInputConnection(g.GetOutputPort())
    ground = vtk.vtkActor(); ground.SetMapper(gm); ground.GetProperty().SetColor(0.925, 0.925, 0.935); ground.GetProperty().LightingOff()
    return actors, scr, ground

def setup(actors, scr, ground):
    ren = vtk.vtkRenderer(); ren.SetBackground(0.925, 0.925, 0.935)
    for a in actors.values(): ren.AddActor(a)
    ren.AddActor(scr); ren.AddActor(ground)
    ren.AutomaticLightCreationOff()
    ren.UseSSAOOn(); ren.SetSSAORadius(28); ren.SetSSAOBias(0.6); ren.SetSSAOKernelSize(128); ren.SSAOBlurOn()
    rw = vtk.vtkRenderWindow(); rw.SetOffScreenRendering(1); rw.SetMultiSamples(0); rw.AddRenderer(ren); rw.SetSize(W * SS, H * SS)
    w2i = vtk.vtkWindowToImageFilter(); w2i.SetInput(rw); w2i.ReadFrontBufferOff()
    return ren, rw, w2i

def frame(t, actors, scr, ren, rw, w2i, path):
    for n, a in actors.items(): a.SetPosition(*offset(n, t))
    scr.SetPosition(*offset("viz_lcd", t)); scr.GetProperty().SetOpacity(screen_on(t)); scr.SetVisibility(screen_on(t) > 0.001)
    az, el, dist, focal = camera(t)
    a_, e_ = math.radians(az), math.radians(el)
    cam = ren.GetActiveCamera(); cam.SetFocalPoint(*focal)
    cam.SetPosition(focal[0] + dist * math.sin(a_) * math.cos(e_), focal[1] - dist * math.cos(a_) * math.cos(e_), focal[2] + dist * math.sin(e_))
    cam.SetViewUp(0, 0, 1); cam.SetViewAngle(17); cam.SetClippingRange(50, 12000)
    ren.RemoveAllLights()
    for daz, del_, inten in ((-28, 32, 0.74), (60, 18, 0.36), (0, 80, 0.20), (180, 30, 0.18)):
        l = vtk.vtkLight(); l.SetLightTypeToSceneLight(); l.SetPositional(False)
        aa, ee = math.radians(az + daz), math.radians(del_)
        l.SetPosition(focal[0] + 2000 * math.sin(aa) * math.cos(ee), focal[1] - 2000 * math.cos(aa) * math.cos(ee), focal[2] + 2000 * math.sin(ee))
        l.SetFocalPoint(*focal); l.SetIntensity(inten); ren.AddLight(l)
    rw.Render(); w2i.Modified(); w2i.Update()
    img = w2i.GetOutput(); dims = img.GetDimensions()
    from vtk.util.numpy_support import vtk_to_numpy
    arr = vtk_to_numpy(img.GetPointData().GetScalars()).reshape(dims[1], dims[0], -1)[::-1, :, :3]
    Image.fromarray(arr).resize((W, H), Image.LANCZOS).save(path)

def main():
    test = "--test" in sys.argv
    out = os.path.join(R.OUT, "anim_test" if test else "anim")
    shutil.rmtree(out, ignore_errors=True); os.makedirs(out)
    actors, scr, ground = build()
    ren, rw, w2i = setup(actors, scr, ground)
    times = [0.0, 2.0, 4.4, 6.2, 7.6, 9.0, 10.2, 12.5, 15.5] if test else [i / FPS for i in range(int(SECONDS * FPS))]
    for i, t in enumerate(times):
        frame(t, actors, scr, ren, rw, w2i, os.path.join(out, f"f{i:04d}.png"))
        if i % 60 == 0: print(f"frame {i}/{len(times)}", flush=True)
    if test: return
    docs = os.path.join(ROOT, "docs"); os.makedirs(os.path.join(docs, "images"), exist_ok=True)
    mp4 = os.path.join(docs, "assembly.mp4"); gif = os.path.join(docs, "images", "assembly.gif")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(out, "f%04d.png"),
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart", mp4], check=True)
    pal = os.path.join(out, "palette.png")
    vf = "fps=15,scale=720:-1:flags=lanczos"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp4, "-vf", vf + ",palettegen=stats_mode=diff", pal], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp4, "-i", pal, "-lavfi", vf + "[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=4", gif], check=True)
    print("wrote", mp4, "and", gif)

if __name__ == "__main__":
    main()

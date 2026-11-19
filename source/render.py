import os, sys, math
import cadquery as cq, vtk
from PIL import Image, ImageDraw
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_build")   # scratch meshes and textures
os.makedirs(OUT, exist_ok=True)
COL = {"plat": (0.93, 0.91, 0.84), "black": (0.07, 0.07, 0.075)}

def screen_image(path):
    w, h = 1024, 768
    im = Image.new("RGB", (w, h), (150, 152, 150)); d = ImageDraw.Draw(im)
    for y in range(0, h, 4):
        for x in range((y // 4 % 2) * 4, w, 8): d.rectangle([x, y, x + 3, y + 3], fill=(120, 122, 120))
    d.rectangle([0, 0, w, 40], fill=(250, 250, 248)); d.line([0, 41, w, 41], fill=(20, 20, 20), width=3)
    x = 60
    for ww in (70, 60, 80, 100, 90): d.rectangle([x, 14, x + ww, 27], fill=(30, 30, 30)); x += ww + 34
    def win(x0, y0, x1, y1):
        d.rectangle([x0 + 6, y0 + 6, x1 + 6, y1 + 6], fill=(40, 40, 40))
        d.rectangle([x0, y0, x1, y1], fill=(252, 252, 250), outline=(20, 20, 20), width=3)
        for i in range(6): d.line([x0 + 10, y0 + 9 + i * 5, x1 - 10, y0 + 9 + i * 5], fill=(20, 20, 20), width=2)
        d.rectangle([(x0 + x1) // 2 - 80, y0 + 4, (x0 + x1) // 2 + 80, y0 + 40], fill=(252, 252, 250))
        d.rectangle([(x0 + x1) // 2 - 50, y0 + 15, (x0 + x1) // 2 + 50, y0 + 28], fill=(30, 30, 30))
        d.line([x0, y0 + 44, x1, y0 + 44], fill=(20, 20, 20), width=3)
    win(90, 110, 640, 520)
    for i in range(4):
        for j in range(2):
            cx, cy = 180 + i * 125, 230 + j * 140
            d.rectangle([cx - 30, cy - 34, cx + 30, cy + 34], outline=(20, 20, 20), width=3, fill=(235, 235, 232))
            d.rectangle([cx - 36, cy + 44, cx + 36, cy + 54], fill=(30, 30, 30))
    win(520, 400, 930, 690)
    for i in range(7): d.rectangle([550, 470 + i * 28, 550 + 330 - (i * 37) % 120, 480 + i * 28], fill=(60, 60, 60))
    for k, yy in enumerate((110, 230)):
        d.rectangle([900, yy, 970, yy + 70], outline=(20, 20, 20), width=3, fill=(240, 240, 238))
        d.rectangle([890, yy + 80, 980, yy + 90], fill=(250, 250, 248))
    im.save(path)

def mesh_actor(shape, color, name):
    p = f"{OUT}/_tmp_{name}.stl"
    cq.exporters.export(shape, p, tolerance=0.05, angularTolerance=0.15)
    r = vtk.vtkSTLReader(); r.SetFileName(p)
    n = vtk.vtkPolyDataNormals(); n.SetInputConnection(r.GetOutputPort()); n.SetFeatureAngle(28); n.SplittingOn()
    m = vtk.vtkPolyDataMapper(); m.SetInputConnection(n.GetOutputPort())
    a = vtk.vtkActor(); a.SetMapper(m)
    pr = a.GetProperty(); pr.SetColor(*color); pr.SetAmbient(0.34); pr.SetDiffuse(0.66)
    pr.SetSpecular(0.10 if color[0] > 0.5 else 0.25); pr.SetSpecularPower(25)
    return a

def build_scene(parts, quad, tex_path):
    actors = [mesh_actor(s, COL[c], n) for n, (s, c) in parts.items()]
    pl = vtk.vtkPlaneSource(); pl.SetOrigin(*quad[0]); pl.SetPoint1(*quad[1]); pl.SetPoint2(*quad[2])
    rd = vtk.vtkPNGReader(); rd.SetFileName(tex_path)
    tx = vtk.vtkTexture(); tx.SetInputConnection(rd.GetOutputPort()); tx.InterpolateOn()
    m = vtk.vtkPolyDataMapper(); m.SetInputConnection(pl.GetOutputPort())
    a = vtk.vtkActor(); a.SetMapper(m); a.SetTexture(tx); a.GetProperty().LightingOff()
    actors.append(a)
    g = vtk.vtkPlaneSource(); g.SetOrigin(-3000, -3000, -0.05); g.SetPoint1(3000, -3000, -0.05); g.SetPoint2(-3000, 3000, -0.05)
    gm = vtk.vtkPolyDataMapper(); gm.SetInputConnection(g.GetOutputPort())
    ga = vtk.vtkActor(); ga.SetMapper(gm); ga.GetProperty().SetColor(0.925, 0.925, 0.935); ga.GetProperty().LightingOff()
    actors.append(ga)
    return actors

VIEWS = {  # az (deg from front, + = viewer's right), elevation, ortho
    "front34": (-30, 10, False), "rear34": (150, 16, False), "side": (-90, 0, True), "front": (0, 0, True)}

def render(actors, view, size, path, focal=(125, 40, 150), dist=1500):
    az, el, ortho = VIEWS[view]
    ren = vtk.vtkRenderer(); ren.SetBackground(0.925, 0.925, 0.935)
    for a in actors: ren.AddActor(a)
    ren.AutomaticLightCreationOff()
    a_, e_ = math.radians(az), math.radians(el)
    pos = (focal[0] + dist * math.sin(a_) * math.cos(e_), focal[1] - dist * math.cos(a_) * math.cos(e_), focal[2] + dist * math.sin(e_))
    cam = ren.GetActiveCamera(); cam.SetFocalPoint(*focal); cam.SetPosition(*pos); cam.SetViewUp(0, 0, 1)
    if ortho: cam.ParallelProjectionOn(); cam.SetParallelScale(215)
    else: cam.SetViewAngle(17)
    cam.SetClippingRange(50, 9000)
    def light(daz, del_, inten):
        l = vtk.vtkLight(); l.SetLightTypeToSceneLight(); l.SetPositional(False)
        aa, ee = math.radians(az + daz), math.radians(del_)
        l.SetPosition(focal[0] + 2000 * math.sin(aa) * math.cos(ee), focal[1] - 2000 * math.cos(aa) * math.cos(ee), focal[2] + 2000 * math.sin(ee))
        l.SetFocalPoint(*focal); l.SetIntensity(inten); ren.AddLight(l)
    light(-28, 32, 0.74); light(60, 18, 0.36); light(0, 80, 0.20); light(180, 30, 0.18)
    ren.UseSSAOOn(); ren.SetSSAORadius(28); ren.SetSSAOBias(0.6); ren.SetSSAOKernelSize(128); ren.SSAOBlurOn()
    rw = vtk.vtkRenderWindow(); rw.SetOffScreenRendering(1); rw.SetMultiSamples(0); rw.AddRenderer(ren)
    rw.SetSize(size[0] * 2, size[1] * 2); rw.Render()
    w2i = vtk.vtkWindowToImageFilter(); w2i.SetInput(rw); w2i.Update()
    wr = vtk.vtkPNGWriter(); wr.SetFileName(path); wr.SetInputConnection(w2i.GetOutputPort()); wr.Write()
    Image.open(path).resize(size, Image.LANCZOS).save(path)

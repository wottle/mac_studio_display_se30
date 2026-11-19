"""v0.9 joint coupons, cut from the real parts in their real print orientation."""
import cadquery as cq, neomac as M
from neomac import box
import os
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "coupons")
os.makedirs(OUT, exist_ok=True)
def bed(s, ax, ang):
    s = s.rotate((0, 0, 0), ax, ang); bb = s.val().BoundingBox(); return s.translate((-bb.xmin, -bb.ymin, -bb.zmin))
def save(name, s):
    assert s.val().isValid() and s.solids().size() == 1, name
    bb = s.val().BoundingBox(); cq.exporters.export(s, f"{OUT}/{name}.stl", tolerance=0.02, angularTolerance=0.1)
    print(f"{name:34s} {bb.xlen:6.1f} x {bb.ylen:6.1f} x {bb.zlen:5.1f}"); return s
fr, base = M.make_frame(), M.make_base()
def base_slice(x0, x1):
    b = base.intersect(M.place(box(x0, x1, -5, 20, -20, 25)))
    return bed(b.translate((0, -M.ORG[0], -M.ORG[1])).rotate((0, 0, 0), (1, 0, 0), M.TILT), (0, 1, 0), 90)
out = {}
out["a"] = save("joint_frame_slice", bed(fr.intersect(box(15, 45, -5, 20, -5, 26)), (1, 0, 0), 90))
out["b"] = save("joint_base_slice", base_slice(15, 45))
out["c"] = save("joint_base_slice_floppy_end", base_slice(M.FL_X0 - 15, M.FL_X0 + 15))
out["d"] = save("joint_frame_slice_for_floppy_end", bed(fr.intersect(box(M.FL_X0 - 15, M.FL_X0 + 15, -5, 20, -5, 26)), (1, 0, 0), 90))

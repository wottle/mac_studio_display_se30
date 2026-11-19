# Joint coupons

Short slices of the base-to-frame joint, cut from the real parts and exported in their real print orientation. Print one frame slice and its matching base slice.

| Pair | Files | Covers |
|---|---|---|
| Left screw | `joint_frame_slice.stl` + `joint_base_slice.stl` | Tongue and groove, rear flange, one heat-set insert, the lowest contour line |
| Centre screw | `joint_frame_slice_for_floppy_end.stl` + `joint_base_slice_floppy_end.stl` | The same, plus the start of the floppy slot |

Check:

- The base slice drops onto the frame slice without play, and the front seam closes. The design uses 0.2 mm clearance on the tongue (`TG_CLR` in `source/neomac.py`).
- The flange sits flush in the recess at the rear.
- A heat-set insert sets in the frame slice without marking the front face, and an M3 x 8 through the flange pulls the joint tight.
- The frame's bottom front edge prints square, and the contour line on the base is crisp.
- The end of the floppy slot prints cleanly. It is a small overhang (3 x 5 mm) when the base prints on its side; the full base in the 3MF has a painted support there, so add one to the coupon too if your printer droops it.

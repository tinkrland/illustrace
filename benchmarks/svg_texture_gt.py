"""texture gt run 1: rebuild texture_energy on vector ground truth.

three questions:
  fidelity    — does per-region sigma track grain amplitude (0/8/14) monotonically?
  anchor law  — canvas-anchored: per-px sigma invariant to scale;
                subject-anchored: sigma scales linearly with s (0.55 here)
  restore     — does the rebuilt metric earn texture_energy's validated status?

reuses the anchor run renders (same seeds and conditions) so the numbers are
directly comparable to results/SVG_ANCHOR_RUN1.md.
"""
import json
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)

import svg_house as H
from svg_granularity import build_set_svg, SET_GEO, S, TX, TY
from engine.texture_gt import texture_gt

OUT = os.path.normpath(os.path.join(HERE, "..", "data", "generated", "arch_svg"))


def main():
    roles = H.derive_roles()
    brush = dict(H.BRUSHES["sketchy"], jitter=2.5, passes=1)

    # ---- fidelity: grain amplitude sweep on solo renders
    print("== fidelity: grain amplitude vs per-region sigma (solo) ==")
    fid = []
    for amp in (0.0, 8.0, 14.0):
        svg = H.build_svg(roles, brush, seed=7)
        im = H.render(svg, "/tmp/_g.png", grain_amp=amp)
        t = texture_gt(im)
        fid.append((amp, t["sigma"], t["grad"]))
        print(f"amp={amp:4.1f}  sigma={t['sigma']:.2f}  grad={t['grad']:.2f}")

    # ---- anchor conditions (same renders as anchor run 1)
    solo = Image.open(os.path.join(OUT, "anchor_solo_grain.png"))
    canvas = Image.open(os.path.join(OUT, "anchor_set_canvasgrain.png"))
    subject = Image.open(os.path.join(OUT, "anchor_set_subjectgrain.png"))

    t_solo = texture_gt(solo)
    t_canvas = texture_gt(canvas, tx=TX, ty=TY, s=S)
    t_subject = texture_gt(subject, tx=TX, ty=TY, s=S)

    print("== anchor law: house-region sigma across conditions ==")
    print(f"solo                 sigma={t_solo['sigma']:.2f}  grad={t_solo['grad']:.2f}")
    print(f"set canvas-anchored  sigma={t_canvas['sigma']:.2f}  grad={t_canvas['grad']:.2f}"
          f"   (law: ~= solo)")
    print(f"set subject-anchored sigma={t_subject['sigma']:.2f}  grad={t_subject['grad']:.2f}"
          f"   (law: ~= {S:.2f} x solo = {S * t_solo['sigma']:.2f})")

    rows = {"fidelity": fid,
            "solo": t_solo, "set_canvas_anchored": t_canvas,
            "set_subject_anchored": t_subject, "scale": S}
    with open(os.path.join(OUT, "manifest_texture_gt.json"), "w") as f:
        json.dump(rows, f, indent=1)
    print("per-region:")
    for k in t_solo["regions"]:
        print(f"  {k:12s} solo={t_solo['regions'][k]['sigma']:6.2f}"
              f"  canvas={t_canvas['regions'][k]['sigma']:6.2f}"
              f"  subject={t_subject['regions'][k]['sigma']:6.2f}")


if __name__ == "__main__":
    main()

"""test-1 batch: value_range, stroke_directionality, shape_complexity.

three registry candidates measured against substrate ground truth:

  value_range        — the palette knob rescales role luminance deviations
                       (l' = 0.5 + k(l - 0.5)); expected spread computed from
                       the exact area-weighted role mixture
  stroke_directionality — dominant line axis + concentration from boundary
                       gradients vs the length-weighted GEO segment angles,
                       plus rotation consistency (30 and 90 degrees)
  shape_complexity   — contour information density: base house vs a complex
                       variant (attic window + second chimney), with vector
                       corner counts as truth and raster proxies as the
                       honest-fope candidate

informative failures are recorded, not hidden.
"""
import colorsys
import json
import math
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)

import svg_house as H
from engine.analyzer import value_range, stroke_axis, shape_proxies
from engine import analyzer as A

OUT = os.path.normpath(os.path.join(HERE, "..", "data", "generated", "arch_svg"))

# approximate fill areas (solo 512x512 canvas) for the expected mixture
AREAS = {"bg": 194054, "ground": 49394, "wall": 32680, "roof": 12260,
         "door": 2788 + 1152 + 12046, "window": 3872, "canopy": 6650}
STROKE_AREA = 2198 * 5  # total path length x width


def lum_hex(hx):
    r, g, b = (int(hx[i:i + 2], 16) for i in (1, 3, 5))
    return 0.299 * r + 0.587 * g + 0.114 * b


def rescale_roles(roles, k):
    out = {}
    for name, hx in roles.items():
        r, g, b = (int(hx[i:i + 2], 16) / 255 for i in (1, 3, 5))
        h, l, s = colorsys.rgb_to_hls(r, g, b)
        l2 = max(0.0, min(1.0, 0.5 + k * (l - 0.5)))
        rgb = colorsys.hls_to_rgb(h, l2, s)
        out[name] = "#%02x%02x%02x" % tuple(int(round(c * 255)) for c in rgb)
    return out


def expected_spread(roles, stroke_lum, stroke_area=STROKE_AREA):
    lums, weights = [], []
    for name, w in AREAS.items():
        role = "ground" if name == "canopy" else name
        lums.append(lum_hex(roles[role]))
        weights.append(w)
    lums.append(stroke_lum)
    weights.append(stroke_area)
    lums = np.array(lums, float)
    weights = np.array(weights, float) / sum(weights)
    order = np.argsort(lums)
    cw = np.cumsum(weights[order])
    lv = lums[order]
    p5 = lv[np.searchsorted(cw, 0.05)]
    p95 = lv[np.searchsorted(cw, 0.95)]
    return p95 - p5


def geo_segment_stats(geo):
    """length-weighted axial orientation histogram + corner counts."""
    hist = np.zeros(90)
    corners, length = 0, 0.0
    for pts in geo.values():
        segs = [(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1])
                for i in range(len(pts) - 1)]
        angles = []
        for dx, dy in segs:
            L = math.hypot(dx, dy)
            length += L
            ax = math.degrees(math.atan2(dy, dx))  # directed: reversals count
            angles.append(ax)
            hist[int(ax % 180 * 90 / 180) % 90] += L
        for i in range(len(angles) - 1):
            d = abs(angles[i + 1] - angles[i])
            d = min(d, 360 - d)
            if d > 15:
                corners += 1
        if len(pts) > 2 and pts[0] == pts[-1] and len(segs) > 1:
            d = abs(angles[0] - angles[-1])
            d = min(d, 360 - d)
            if d > 15:
                corners += 1
    return hist, corners, length


def main():
    os.makedirs(OUT, exist_ok=True)
    roles = H.derive_roles()
    brush = dict(H.BRUSHES["sketchy"], jitter=2.5, passes=1)
    stroke_lum = lum_hex(roles["stroke"])

    # ================= value_range =================
    print("== value_range: palette knob sweep ==")
    vr = {}
    for k in (0.5, 0.75, 1.0, 1.25, 1.5):
        rr = rescale_roles(roles, k)
        im = H.render(H.build_svg(rr, brush, seed=7), "/tmp/_vr.png", grain_amp=0.0)
        m = value_range(im)
        e = expected_spread(rr, stroke_lum)
        vr[k] = {"measured": round(m, 2), "expected": round(e, 2)}
        print(f"k={k:4.2f}  measured={m:6.2f}  expected(area-mixture)={e:6.2f}")

    # ================= stroke_directionality =================
    print("== stroke_directionality: axis recovery + rotation ==")
    im = H.render(H.build_svg(roles, brush, seed=7), "/tmp/_ax.png", grain_amp=0.0)
    axis, conc = stroke_axis(im)
    ghist, gcorners, glen = geo_segment_stats(H.GEO)
    # expected dominant axis from the length-weighted GEO histogram
    w = 8  # +-15 degrees in 2-degree bins
    pad = np.concatenate([ghist, ghist[:w]])
    wins = np.convolve(pad, np.ones(2 * w + 1), mode="full")[w:w + 90]
    gbest = int(wins.argmax())
    gaxis = (gbest + 0.5) * 2.0
    gconc = float(wins[gbest] / ghist.sum())
    print(f"measured axis={axis:5.1f} conc={conc:.2f}")
    print(f"geo truth axis={gaxis:5.1f} conc={gconc:.2f}")

    bg = tuple(int(roles["bg"][i:i + 2], 16) for i in (1, 3, 5))
    sd = {}
    for rot in (0, 30, 90):
        r = im if rot == 0 else im.rotate(rot, fillcolor=bg, resample=Image.BICUBIC)
        ax, cc = stroke_axis(r)
        sd[rot] = (round(float(ax), 1), round(float(cc), 3))
        print(f"rotate {rot:2d}: axis={ax:5.1f} conc={cc:.2f}")

    # ================= shape_complexity =================
    print("== shape_complexity: base vs complex ==")
    GEO_C = dict(H.GEO)
    GEO_C["attic_window"] = [(223, 170), (223, 194), (247, 194), (247, 170), (223, 170)]
    GEO_C["chimney2"] = [(300, 168), (300, 218), (318, 218), (318, 168)]
    geo_base = H.GEO
    _, c_base, l_base = geo_segment_stats(geo_base)
    _, c_cplx, l_cplx = geo_segment_stats(GEO_C)
    print(f"vector truth: base corners={c_base} len={l_base:.0f} density={c_base/l_base*1000:.2f}/kpx")
    print(f"vector truth: cplx corners={c_cplx} len={l_cplx:.0f} density={c_cplx/l_cplx*1000:.2f}/kpx")

    sc = {}
    for bname, br in (("clean", dict(H.BRUSHES["clean"], passes=1)),
                      ("sketchy", dict(H.BRUSHES["sketchy"], jitter=2.5, passes=1))):
        H.GEO = geo_base
        imb = H.render(H.build_svg(roles, br, seed=7), "/tmp/_sb.png", grain_amp=0.0)
        H.GEO = GEO_C
        imc = H.render(H.build_svg(roles, br, seed=7), "/tmp/_sc.png", grain_amp=0.0)
        pb, pc = shape_proxies(imb), shape_proxies(imc)
        ratio = pc["perim_area"] / pb["perim_area"] if pb["perim_area"] else 0
        sc[bname] = {"base": {k2: round(float(v), 3) for k2, v in pb.items()},
                     "complex": {k2: round(float(v), 3) for k2, v in pc.items()},
                     "perim_ratio": round(float(ratio), 3)}
        print(f"{bname:8s} perim_area {pb['perim_area']:.3f} -> {pc['perim_area']:.3f}"
              f" (ratio {ratio:.3f})   entropy {pb['boundary_entropy']:.3f} -> {pc['boundary_entropy']:.3f}")
    H.GEO = geo_base

    with open(os.path.join(OUT, "manifest_test1.json"), "w") as f:
        json.dump({"value_range": vr, "stroke_axis": sd,
                   "axis_expected": [gaxis, gconc],
                   "shape": sc,
                   "vector_truth": {"base": [c_base, round(l_base)],
                                    "complex": [c_cplx, round(l_cplx)]}}, f, indent=1)


if __name__ == "__main__":
    main()

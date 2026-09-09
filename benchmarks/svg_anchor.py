"""anchor run 1: can grain and lighting be subject-anchored?

granularity run 1 showed canvas-anchored recipes drift with staging: grain
reads +41% texture energy on the staged house, lighting reads position
dependence (133.8 / 134.2 / 129.6). the scientist review made this the gating
question: if texture cannot be subject-anchored and scale-normalized, it is
not a valid subject-level style parameter.

this run implements the other anchor condition:
  subject-anchored grain    — the noise patch is applied in house-local
    coordinates (the same rng field, cropped to the house bbox in solo space,
    scaled 0.55 with the house, pasted at the staged position, so the house
    experiences the same noise-to-subject statistics as solo)
  subject-anchored lighting — the gradient is evaluated in house-local
    coordinates over the house rect only (context stays unlit: an honest
    disjoint set, which is itself the finding)

conditions measured on the house region:
  grain:   solo | set canvas-anchored | set subject-anchored
  lighting: solo canvas | set canvas-anchored | set subject-anchored
"""
import io
import json
import os
import sys

import numpy as np
import cairosvg
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)

import svg_house as H
from svg_granularity import build_set_svg, SET_GEO, S, TX, TY, CROP_SOLO
from engine.analyzer import profile
from svg_fidelity2 import shading_sel, shading_stats

OUT = os.path.normpath(os.path.join(HERE, "..", "data", "generated", "arch_svg"))
R = H.SIZE * H.RSCALE          # 1024 working raster
GRAIN_S, GRAIN_SEED = 10.0, 7
LIGHT = (0.5, (255, 237, 208))


def raster_1024(svg_str):
    png = cairosvg.svg2png(bytestring=svg_str.encode(), output_width=R, output_height=R)
    return np.asarray(Image.open(io.BytesIO(png)).convert("RGB"), float)


def noise_1024():
    return np.random.default_rng(GRAIN_SEED).normal(0, GRAIN_S, (R, R))


def add_noise(a, n):
    return np.clip(a + n[..., None], 0, 255)


def soft_light(a, col, alpha):
    """w3c soft-light, same formula as svg_house.render."""
    b = a / 255.0
    s = np.array(col, float)[None, None, :] / 255.0
    lit = np.where(s <= 0.25, b - (1 - 2 * s) * b * (1 - b),
                   b + (2 * s - 1) * (np.sqrt(b) - b)) * 255.0
    return a * (1 - alpha[..., None]) + np.clip(lit, 0, 255) * alpha[..., None]


def canvas_light_alpha(strength):
    X, Y = np.meshgrid(np.arange(R), np.arange(R))
    return strength * np.clip(1 - (X / (R * 1.4) + Y / (R * 1.4)), 0, 1)


def subject_light_alpha(strength, tx=TX, ty=TY):
    """gradient evaluated in house-local coordinates; zero outside the rect."""
    X, Y = np.meshgrid(np.arange(R), np.arange(R))
    xl = (X - tx * 2) / S          # house-local raster coords (0..1024 over the house)
    yl = (Y - ty * 2) / S
    inside = (xl >= 0) & (xl < R) & (yl >= 0) & (yl < R)
    a = strength * np.clip(1 - (xl / (R * 1.4) + yl / (R * 1.4)), 0, 1)
    return np.where(inside, a, 0.0)


def to_im(a):
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).resize(
        (H.SIZE, H.SIZE), Image.LANCZOS)


def main():
    os.makedirs(OUT, exist_ok=True)
    roles = H.derive_roles()
    brush = dict(H.BRUSHES["sketchy"], jitter=2.5, passes=1)

    solo_svg = H.build_svg(roles, brush, seed=7)
    set_svg = build_set_svg(roles, brush, seed=7, tx=TX, geo=SET_GEO)

    solo_r = raster_1024(solo_svg)
    set_r = raster_1024(set_svg)
    n = noise_1024()

    # ---- grain conditions
    solo_grain = to_im(add_noise(solo_r, n))                       # solo, grain on
    set_canvas = to_im(add_noise(set_r, n))                         # canvas-anchored

    # subject-anchored: noise crop in house-local space, scaled with the house
    hx0, hy0, hx1, hy1 = [v * 2 for v in CROP_SOLO]                 # house bbox @1024, solo space
    patch = n[hy0:hy1, hx0:hx1]
    ph, pw = patch.shape
    patch_s = np.asarray(Image.fromarray(patch.astype(np.float32), mode="F").resize(
        (int(round(pw * S)), int(round(ph * S))), Image.BILINEAR))
    subj = set_r.copy()
    py, px = int(round((TY + S * CROP_SOLO[1]) * 2)), int(round((TX + S * CROP_SOLO[0]) * 2))
    region = subj[py:py + patch_s.shape[0], px:px + patch_s.shape[1]]
    subj[py:py + patch_s.shape[0], px:px + patch_s.shape[1]] = np.clip(
        region + patch_s[..., None], 0, 255)
    set_subject = to_im(subj)

    solo_grain.save(os.path.join(OUT, "anchor_solo_grain.png"))
    set_canvas.save(os.path.join(OUT, "anchor_set_canvasgrain.png"))
    set_subject.save(os.path.join(OUT, "anchor_set_subjectgrain.png"))

    # ---- lighting conditions
    strength, col = LIGHT
    solo_lit = to_im(soft_light(solo_r, col, canvas_light_alpha(strength)))
    set_lit_canvas = to_im(soft_light(set_r, col, canvas_light_alpha(strength)))
    set_lit_subject = to_im(soft_light(set_r, col, subject_light_alpha(strength)))
    solo_lit.save(os.path.join(OUT, "anchor_solo_lit.png"))
    set_lit_canvas.save(os.path.join(OUT, "anchor_set_canvaslit.png"))
    set_lit_subject.save(os.path.join(OUT, "anchor_set_subjectlit.png"))

    # ---- measurements on the house region
    crop_set = (TX + S * CROP_SOLO[0], TY + S * CROP_SOLO[1],
                TX + S * CROP_SOLO[2], TY + S * CROP_SOLO[3])
    cs = tuple(int(round(v)) for v in crop_set[:2]); cg = tuple(int(round(v)) for v in crop_set[2:])

    p_solo = profile(solo_grain.crop(CROP_SOLO))
    p_canvas = profile(set_canvas.crop((*cs, *cg)))
    p_subject = profile(set_subject.crop((*cs, *cg)))

    rows = {"grain": {
        "solo": p_solo, "set_canvas_anchored": p_canvas,
        "set_subject_anchored": p_subject}}
    print("== grain: texture energy on the house region ==")
    print(f"solo                 tex={p_solo['texture_energy']:.1f}  cv={p_solo['stroke_width_cv']:.3f}")
    print(f"set canvas-anchored  tex={p_canvas['texture_energy']:.1f}  cv={p_canvas['stroke_width_cv']:.3f}"
          f"   (run 1: +41% vs solo)")
    print(f"set subject-anchored tex={p_subject['texture_energy']:.1f}  cv={p_subject['stroke_width_cv']:.3f}")

    def lum(im, box):
        c = im.crop(box)
        sel = shading_sel(c)
        l, con = shading_stats(c, sel)
        return l, con

    l_s, c_s = lum(solo_lit, CROP_SOLO)
    l_cc, c_cc = lum(set_lit_canvas, (*cs, *cg))
    l_cs, c_cs = lum(set_lit_subject, (*cs, *cg))
    rows["lighting"] = {
        "solo_canvas": [l_s, c_s], "set_canvas_anchored": [l_cc, c_cc],
        "set_subject_anchored": [l_cs, c_cs]}
    print("== lighting: house interior, fixed support ==")
    print(f"solo (canvas grad)    lum={l_s:.1f}  contrast={c_s:.1f}")
    print(f"set canvas-anchored    lum={l_cc:.1f}  contrast={c_cc:.1f}")
    print(f"set subject-anchored  lum={l_cs:.1f}  contrast={c_cs:.1f}")

    with open(os.path.join(OUT, "manifest_anchor.json"), "w") as f:
        json.dump(rows, f, indent=1)


if __name__ == "__main__":
    main()

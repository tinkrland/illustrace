"""granularity run 1: is a style parameter stable across granularity?

the claim under test (STYLE_ONTOLOGY.md): the same asset rendered solo vs
staged in a set carries different palette/shading/lighting treatment, so
some style parameters are granularity dependent. the stimulus pair controls
everything except composition: same house geometry, same roles (the set adds
no new colors), same brush recipe, same seed — only the staging changes
(house scaled 0.55 into a set with sun, trees, bushes on shared ground).

measurements:
  A  house region solo vs house region in-set   (asset-anchored stability)
  B  full canvas solo vs full canvas set       (set-level profile change)

classification vocabulary (written back into the registry):
  stable                 — reads the same at both granularities
  scale-normalizable      — drifts in px, invariant once normalized (width/subject_height)
  canvas-anchored         — px-stable, subject-relative scale changes with staging
  context-contaminated    — the set changes the reading on the asset itself
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
from svg_house import (GEO, BRUSHES, derive_roles, build_svg, render,
                       jitter_polyline)
from engine.analyzer import profile, palette as kpalette
from svg_fidelity2 import shading_sel, shading_stats

OUT = os.path.normpath(os.path.join(HERE, "..", "data", "generated", "arch_svg"))

S = 0.55          # house scale in the set
TX, TY = 30, 392 - 0.55 * 392   # keep the house feet on the shared ground line

# solo house region (px, includes stroke+grain margins)
CROP_SOLO = (110, 120, 360, 400)
CROP_SET = (TX + S * CROP_SOLO[0], TY + S * CROP_SOLO[1],
            TX + S * CROP_SOLO[2], TY + S * CROP_SOLO[3])
SUBJ_H_SOLO = 262.0          # roof apex y130 -> ground y392
SUBJ_H_SET = SUBJ_H_SOLO * S

SET_GEO = {
    "sun": [(420 - 36 * c_, 90 - 36 * s_) for c_, s_ in
            [(np.cos(a / 24 * 2 * np.pi), np.sin(a / 24 * 2 * np.pi)) for a in range(24)]],
    "tree_trunk_b": [(420, 300), (420, 392), (436, 392), (436, 300)],
    "canopy_b": [(420 - 60 * c_, 250 - 60 * s_) for c_, s_ in
                 [(np.cos(a / 28 * 2 * np.pi), np.sin(a / 28 * 2 * np.pi)) for a in range(28)]],
    "tree_trunk_c": [(476, 330), (476, 392), (486, 392), (486, 330)],
    "canopy_c": [(476 - 38 * c_, 296 - 38 * s_) for c_, s_ in
                 [(np.cos(a / 24 * 2 * np.pi), np.sin(a / 24 * 2 * np.pi)) for a in range(24)]],
    "bush_l": [(250, 380)] + [(250 + 42 * c_, 380 - 20 * s_) for c_, s_ in
                [(np.cos(a / 16 * np.pi), abs(np.sin(a / 16 * np.pi))) for a in range(17)]] ,
    "bush_r": [(330, 386)] + [(330 + 30 * c_, 386 - 14 * s_) for c_, s_ in
                [(np.cos(a / 14 * np.pi), abs(np.sin(a / 14 * np.pi))) for a in range(15)]],
    "ground_set": [(0, 392), (512, 392)],
}


def _paths(geo, brush, seed):
    """stroke paths for a geo dict under a brush recipe (same bake rules as
    build_svg: tapered -> baked outline, else plain polylines)."""
    out = []
    for name, pts in geo.items():
        if brush.get("taper"):
            from svg_house import bake_outline
            out.append(f'<path class="stroke stroke-{name}" fill="none" '
                       f'd="{bake_outline(pts, brush["width"], brush["taper"], brush.get("jitter", 0.0), seed + sum(map(ord, name)))}"/>')
        else:
            segs = []
            for p in range(brush["passes"]):
                j = jitter_polyline(pts, brush["jitter"], seed + p * 77)
                if j[0] != j[-1] or len(j) > 2:
                    segs.append("M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in j))
            out.append(f'<path class="stroke stroke-{name}" d="{" ".join(segs)}"/>')
    return "\n    ".join(out)


SET_GEO_RIGHT = {
    "sun": [(90 - 36 * c_, 90 - 36 * s_) for c_, s_ in
            [(np.cos(a / 24 * 2 * np.pi), np.sin(a / 24 * 2 * np.pi)) for a in range(24)]],
    "tree_trunk_b": [(56, 300), (56, 392), (72, 392), (72, 300)],
    "canopy_b": [(56 - 60 * c_, 250 - 60 * s_) for c_, s_ in
                 [(np.cos(a / 28 * 2 * np.pi), np.sin(a / 28 * 2 * np.pi)) for a in range(28)]],
    "tree_trunk_c": [(120, 330), (120, 392), (130, 392), (130, 330)],
    "canopy_c": [(120 - 38 * c_, 296 - 38 * s_) for c_, s_ in
                 [(np.cos(a / 24 * 2 * np.pi), np.sin(a / 24 * 2 * np.pi)) for a in range(24)]],
    "bush_l": [(170, 380)] + [(170 + 42 * c_, 380 - 20 * s_) for c_, s_ in
                [(np.cos(a / 16 * np.pi), abs(np.sin(a / 16 * np.pi))) for a in range(17)]],
    "bush_r": [(240, 386)] + [(240 + 30 * c_, 386 - 14 * s_) for c_, s_ in
                [(np.cos(a / 14 * np.pi), abs(np.sin(a / 14 * np.pi))) for a in range(15)]],
    "ground_set": [(0, 392), (512, 392)],
}


def build_set_svg(roles, brush, seed=7, tx=TX, geo=None):
    geo = geo or SET_GEO
    set_geo = geo
    """the set: full-canvas bg + ground, context elements at canvas scale,
    house (identical svg content, same recipes/seed) wrapped in a scale
    transform. no new colors — composition is the only variable."""
    inner = build_svg(roles, brush, seed=seed)
    inner = inner[inner.index(">") + 1:inner.rindex("</svg>")]  # strip svg wrapper

    if set_geo is SET_GEO:
        extra_fills = ('<circle cx="420" cy="90" r="36" class="fill-window" fill="%s"/>'
                       '<circle cx="420" cy="250" r="60" class="fill-ground" fill="%s"/>'
                       '<circle cx="476" cy="296" r="38" class="fill-ground" fill="%s"/>'
                       '<rect x="420" y="300" width="16" height="92" class="fill-door" fill="%s"/>'
                       '<rect x="476" y="330" width="10" height="62" class="fill-door" fill="%s"/>'
                       '<ellipse cx="271" cy="378" rx="42" ry="20" class="fill-ground" fill="%s"/>'
                       '<ellipse cx="345" cy="385" rx="30" ry="14" class="fill-ground" fill="%s"/>'
                       % (roles['window'], roles['ground'], roles['ground'],
                          roles['door'], roles['door'], roles['ground'], roles['ground']))
        cx = {"sun": (420, 90, 36), "canopy_b": (420, 250, 60), "canopy_c": (476, 296, 38)}
    else:
        extra_fills = ('<circle cx="90" cy="90" r="36" class="fill-window" fill="%s"/>'
                       '<circle cx="56" cy="250" r="60" class="fill-ground" fill="%s"/>'
                       '<circle cx="120" cy="296" r="38" class="fill-ground" fill="%s"/>'
                       '<rect x="56" y="300" width="16" height="92" class="fill-door" fill="%s"/>'
                       '<rect x="120" y="330" width="10" height="62" class="fill-door" fill="%s"/>'
                       '<ellipse cx="191" cy="378" rx="42" ry="20" class="fill-ground" fill="%s"/>'
                       '<ellipse cx="255" cy="385" rx="30" ry="14" class="fill-ground" fill="%s"/>'
                       % (roles['window'], roles['ground'], roles['ground'],
                          roles['door'], roles['door'], roles['ground'], roles['ground']))
    context_fills = f"""
  <g id="set_fills">
    <rect x="0" y="392" width="512" height="120" class="fill-ground" fill="{roles['ground']}"/>
    {extra_fills}
  </g>"""

    context_strokes = f"""
  <g id="set_strokes" stroke="{roles['stroke']}" stroke-width="{brush['width']}"
     stroke-linecap="{brush['caps']}" stroke-linejoin="round" fill="none">
    {_paths(set_geo, brush, seed + 500)}
  </g>"""

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <rect x="0" y="0" width="512" height="512" class="fill-bg" fill="{roles['bg']}"/>
{context_fills}
  <g id="house" transform="translate({tx} {TY}) scale({S})">
{inner}
  </g>
{context_strokes}
</svg>"""


def rasters(svg_str, grain_amp=10.0, lighting_apply=None):
    png = cairosvg.svg2png(bytestring=svg_str.encode(), output_width=H.SIZE * H.RSCALE,
                          output_height=H.SIZE * H.RSCALE)
    im = Image.open(io.BytesIO(png)).convert("RGB")
    # grain: canvas-anchored additive noise, same as render()
    if grain_amp > 0:
        a = np.asarray(im, dtype=np.int16)
        rng = np.random.default_rng(7)
        a = np.clip(a + rng.normal(0, grain_amp, a.shape[:2])[..., None], 0, 255).astype(np.uint8)
        im = Image.fromarray(a)
    if lighting_apply is not None:
        im = H.render(svg_str, "/tmp/_lit.png", grain_amp=0.0, lighting_apply=lighting_apply)
        im = im.resize((H.SIZE, H.SIZE), Image.LANCZOS)
    else:
        im = im.resize((H.SIZE, H.SIZE), Image.LANCZOS)
    return im


def crop(im, box):
    return im.crop(tuple(int(round(v)) for v in box))


def pal(im):
    return [(tuple(int(c) for c in rgb), w) for rgb, w in kpalette(im, 6)]


def pal_distance(p1, p2):
    """mean nearest-color distance between two measured palettes."""
    a = np.array([c for c, _ in p1], float)
    b = np.array([c for c, _ in p2], float)
    d1 = np.mean([np.min(np.abs(b - c).sum(-1)) for c in a])
    d2 = np.mean([np.min(np.abs(a - c).sum(-1)) for c in b])
    return float((d1 + d2) / 2)


def main():
    os.makedirs(OUT, exist_ok=True)
    roles = derive_roles()
    brush = dict(BRUSHES["sketchy"], jitter=2.5, passes=1)
    light = (0.5, (255, 237, 208))

    solo_svg = build_svg(roles, brush, seed=7)
    set_svg = build_set_svg(roles, brush, seed=7)
    for name, s in (("gran_solo", solo_svg), ("gran_set", set_svg)):
        with open(os.path.join(OUT, name + ".svg"), "w") as f:
            f.write(s)

    solo = rasters(solo_svg, grain_amp=10.0)
    st = rasters(set_svg, grain_amp=10.0)
    solo.save(os.path.join(OUT, "gran_solo.png"))
    st.save(os.path.join(OUT, "gran_set.png"))

    solo_lit = rasters(solo_svg, lighting_apply=light)
    st_lit = rasters(set_svg, lighting_apply=light)
    solo_lit.save(os.path.join(OUT, "gran_solo_lit.png"))
    st_lit.save(os.path.join(OUT, "gran_set_lit.png"))

    # staging variant: same set, house staged right (context mirrored) —
    # lighting is canvas-anchored, so the staging position should matter.
    set_svg_r = build_set_svg(roles, brush, seed=7, tx=280, geo=SET_GEO_RIGHT)
    with open(os.path.join(OUT, "gran_set_right.svg"), "w") as f:
        f.write(set_svg_r)
    st_r = rasters(set_svg_r, grain_amp=10.0)
    st_r.save(os.path.join(OUT, "gran_set_right.png"))
    st_r_lit = rasters(set_svg_r, lighting_apply=light)
    crop_r = (280 + S * CROP_SOLO[0], TY + S * CROP_SOLO[1],
              280 + S * CROP_SOLO[2], TY + S * CROP_SOLO[3])
    hg_r = profile(crop(st_r, crop_r))
    sel_r = shading_sel(crop(st_r_lit, crop_r))
    lum_r, con_r = shading_stats(crop(st_r_lit, crop_r), sel_r)

    # A: house region solo vs in-set
    hs = profile(crop(solo, CROP_SOLO))
    hg = profile(crop(st, CROP_SET))
    ps_s, ps_g = pal(crop(solo, CROP_SOLO)), pal(crop(st, CROP_SET))
    pd_crop = pal_distance(ps_s, ps_g)

    # B: full canvas solo vs set
    fs, fg = profile(solo), profile(st)
    pd_full = pal_distance(pal(solo), pal(st))

    # lighting on fixed interior support of the house region
    sel_s = shading_sel(crop(solo_lit, CROP_SOLO))
    lum_s, con_s = shading_stats(crop(solo_lit, CROP_SOLO), sel_s)
    sel_g = shading_sel(crop(st_lit, CROP_SET))
    lum_g, con_g = shading_stats(crop(st_lit, CROP_SET), sel_g)

    rows = {
        "scale": S,
        "house_solo": hs, "house_in_set": hg,
        "full_solo": fs, "full_set": fg,
        "palette_distance_house_region": pd_crop,
        "palette_distance_full_canvas": pd_full,
        "lighting_house_region": {"solo_mean_lum": lum_s, "set_mean_lum_left": lum_g,
                                   "set_mean_lum_right": lum_r,
                                   "solo_contrast": con_s, "set_contrast_left": con_g,
                                   "set_contrast_right": con_r},
        "house_in_set_right": hg_r,
        "subject_height_solo": SUBJ_H_SOLO, "subject_height_set": SUBJ_H_SET,
    }
    with open(os.path.join(OUT, "manifest_gran.json"), "w") as f:
        json.dump(rows, f, indent=1)

    print("== A. house region: solo vs in-set ==")
    print(f"stroke_width_px     solo={hs['stroke_width_mean']:.2f}  set={hg['stroke_width_mean']:.2f}"
          f"  ratio={hg['stroke_width_mean']/hs['stroke_width_mean']:.2f} (scale={S})")
    nw_s = hs['stroke_width_mean'] / SUBJ_H_SOLO
    nw_g = hg['stroke_width_mean'] / SUBJ_H_SET
    print(f"normalized w/h      solo={nw_s:.5f}  set={nw_g:.5f}")
    print(f"stroke_width_cv     solo={hs['stroke_width_cv']:.3f}  set={hg['stroke_width_cv']:.3f}")
    print(f"edge_dir_entropy    solo={hs['edge_direction_entropy']:.3f}  set={hg['edge_direction_entropy']:.3f}")
    print(f"texture_energy      solo={hs['texture_energy']:.1f}  set={hg['texture_energy']:.1f}")
    print(f"palette_distance    house-region={pd_crop:.1f}   full-canvas={pd_full:.1f}")
    print("== B. full canvas: solo vs set ==")
    print(f"stroke_width_px     solo={fs['stroke_width_mean']:.2f}  set={fg['stroke_width_mean']:.2f}")
    print(f"stroke_width_cv     solo={fs['stroke_width_cv']:.3f}  set={fg['stroke_width_cv']:.3f}")
    print(f"texture_energy      solo={fs['texture_energy']:.1f}  set={fg['texture_energy']:.1f}")
    print("== lighting (canvas gradient, house interior, fixed support) ==")
    print(f"mean_lum            solo={lum_s:.1f}  set_left={lum_g:.1f}  set_right={lum_r:.1f}")
    print(f"contrast            solo={con_s:.1f}  set_left={con_g:.1f}  set_right={con_r:.1f}")
    print("== right staging, house region (non-lighting) ==")
    print(f"stroke_width_px     {hg_r['stroke_width_mean']:.2f}  cv={hg_r['stroke_width_cv']:.3f}  tex={hg_r['texture_energy']:.1f}")

    # ---- clean-crop control: same crops, bottom raised above the ground
    # band so canvas-scale context (ground line, bush arcs) stays out of the
    # region. this is the context-exclusion the contaminated crops revealed.
    box_s = (110, 120, 360, 390)
    pc_s = profile(crop(solo, box_s))
    box_l = (TX + S * 110, TY + S * 120, TX + S * 360, 390)
    pc_l = profile(crop(st, box_l))
    box_r = (280 + S * 110, TY + S * 120, 280 + S * 360, 390)
    pc_r = profile(crop(st_r, box_r))
    rows["clean_crop"] = {
        "solo": pc_s, "set_left": pc_l, "set_right": pc_r,
        "normalized_width_solo": pc_s["stroke_width_mean"] / SUBJ_H_SOLO,
        "normalized_width_set": pc_l["stroke_width_mean"] / SUBJ_H_SET,
    }
    with open(os.path.join(OUT, "manifest_gran.json"), "w") as f:
        json.dump(rows, f, indent=1)
    print("== clean-crop control (context excluded) ==")
    print(f"cv                  solo={pc_s['stroke_width_cv']:.3f}  set_left={pc_l['stroke_width_cv']:.3f}  set_right={pc_r['stroke_width_cv']:.3f}")
    print(f"stroke_width_px     solo={pc_s['stroke_width_mean']:.2f}  set_left={pc_l['stroke_width_mean']:.2f}  set_right={pc_r['stroke_width_mean']:.2f}")
    print(f"normalized w/h       solo={pc_s['stroke_width_mean']/SUBJ_H_SOLO:.5f}  set={pc_l['stroke_width_mean']/SUBJ_H_SET:.5f}")


if __name__ == "__main__":
    main()

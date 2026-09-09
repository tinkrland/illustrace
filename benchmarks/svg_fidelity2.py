"""fidelity run 2 — bring every remaining factor under ground truth.

sweeps (all against the svg substrate, all params recorded in manifest):
  1. stroke width   {3,5,7,9}        -> measured stroke_width_mean (want: linear)
  2. taper ease     {0.6,0.3,0.15}   -> measured width (want: rising as taper eases;
                                     higher cv = variable-width profile detected)
  3. brush passes   {1,2}            -> stroke density (want: ~doubles)
  4. lighting       {0,.25,.5,.75}  -> mean luminance + candidate shading contrast
  5. palette lerp   {.25,.5,.75,1.0} between measured ref palettes
                                       -> measured palette distance vs true distance
                                       (want: monotone + stable ratio = linear)
"""
import json
import os
import sys
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from engine.analyzer import profile, palette, stroke_mask, _as_array
from engine.metrics import palette_distance
from benchmarks.svg_house import (BRUSHES, GEO, REF_WARM, REF_COOL, build_svg,
                                  derive_roles, render, SIZE)

OUT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "data", "generated", "arch_svg"))
WARM = (255, 237, 208)  # lighting color (matches showcase)


def hex2rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float)


def rgb2hex(c):
    return "#%02x%02x%02x" % tuple(int(x) for x in np.clip(c, 0, 255))


def lerp_roles(r1, r2, s):
    return {k: rgb2hex((1 - s) * hex2rgb(r1[k]) + s * hex2rgb(r2[k])) for k in r1}


def shading_sel(img):
    """interior mask: non-stroke, non-background pixels."""
    a = _as_array(img)
    m = ~stroke_mask(img)
    bg = np.abs(a - a[0, 0]).sum(-1) < 30
    return m & ~bg


def shading_stats(img, sel):
    """lighting measurements over a FIXED region support (masks computed once
    from the unlit image — same geometry + seed — so illumination shifts don't
    move the region being measured)."""
    a = _as_array(img)
    lum = a @ [0.299, 0.587, 0.114]
    return float(lum[sel].mean()), float(lum[sel].std())


def save(svg, name, **rkwargs):
    with open(os.path.join(OUT, name + ".svg"), "w") as f:
        f.write(svg)
    return render(svg, os.path.join(OUT, name + ".png"), **rkwargs)


def main():
    rw, rc = derive_roles(REF_WARM), derive_roles(REF_COOL)
    manifest = {"images": []}
    results = {}

    # ---- 1. stroke width -> measured mean width
    print("== sweep 1: stroke width")
    width_rows = []
    for w in (3, 5, 7, 9):
        im = save(build_svg(rw, dict(BRUSHES["clean"], width=w), seed=7), f"fid2_width{w}")
        p = profile(im)
        width_rows.append((w, p["stroke_width_mean"]))
        print(f"  true width={w}  measured={p['stroke_width_mean']:.2f}")
    results["width"] = width_rows

    # ---- 2. taper amount -> measured mean width (base width 7)
    print("== sweep 2: taper")
    taper_rows = []
    for te in (0.6, 0.3, 0.15):
        im = save(build_svg(rw, dict(BRUSHES["clean"], width=7, taper=te, jitter=0.5), seed=7),
                  f"fid2_taper{int(te*100)}")
        p = profile(im)
        taper_rows.append((te, p["stroke_width_mean"], p["stroke_width_cv"]))
        print(f"  taper={te:.2f}  measured width={p['stroke_width_mean']:.2f}  cv={p['stroke_width_cv']:.3f}")
    results["taper"] = taper_rows

    # ---- 3. double pass -> stroke density (new candidate metric: mask coverage)
    print("== sweep 3: brush passes (density)")
    dens_rows = []
    for passes in (1, 2):
        im = save(build_svg(rw, dict(BRUSHES["sketchy"], passes=passes), seed=7), f"fid2_pass{passes}")
        dens = float(stroke_mask(im).mean())
        dens_rows.append((passes, dens))
        print(f"  passes={passes}  stroke_density={dens:.4f}")
    results["density"] = dens_rows

    # ---- 4. lighting strength -> luminance + candidate shading contrast
    print("== sweep 4: lighting")
    light_rows = []
    sel0 = shading_sel(save(build_svg(rw, BRUSHES["clean"], seed=7), "fid2_light0"))
    for s in (0.0, 0.25, 0.5, 0.75):
        svg = build_svg(rw, BRUSHES["clean"],
                        lighting={"blend": "soft-light", "strength": s, "color": "#ffedd0"}, seed=7)
        im = save(svg, f"fid2_light{int(s*100)}", lighting_apply=(s, WARM) if s > 0 else None)
        mlum, contrast = shading_stats(im, sel0)
        light_rows.append((s, mlum, contrast))
        print(f"  strength={s:.2f}  mean_lum={mlum:.1f}  contrast={contrast:.1f}")
    results["lighting"] = light_rows

    # ---- 5. palette interpolation -> measured vs true distance
    print("== sweep 5: palette lerp warm->cool")
    im0 = save(build_svg(rw, BRUSHES["clean"], seed=7), "fid2_pal0")
    pal0 = profile(im0)["palette"]
    pal_rows = []
    for s in (0.25, 0.5, 0.75, 1.0):
        roles_s = lerp_roles(rw, rc, s)
        im = save(build_svg(roles_s, BRUSHES["clean"], seed=7), f"fid2_pal{int(s*100)}")
        measured = palette_distance(pal0, profile(im)["palette"])
        true = float(np.mean([np.linalg.norm(hex2rgb(lerp_roles(rw, rc, s)[k]) - hex2rgb(rw[k]))
                              for k in rw]) / 441.67)
        pal_rows.append((s, measured, true, measured / max(true, 1e-6)))
        print(f"  s={s:.2f}  measured={measured:.4f}  true={true:.4f}  ratio={measured/true:.2f}")
    results["palette"] = pal_rows

    for row in results["width"]:
        manifest["images"].append({"file": f"fid2_width{row[0]}", "true_width": row[0]})
    for row in results["taper"]:
        manifest["images"].append({"file": f"fid2_taper{int(row[0]*100)}", "taper": row[0]})
    for row in results["density"]:
        manifest["images"].append({"file": f"fid2_pass{row[0]}", "passes": row[0]})
    for row in results["lighting"]:
        manifest["images"].append({"file": f"fid2_light{int(row[0]*100)}", "lighting": row[0]})
    for row in results["palette"]:
        manifest["images"].append({"file": f"fid2_pal{int(row[0]*100)}", "lerp": row[0]})
    with open(os.path.join(OUT, "manifest_fid2.json"), "w") as f:
        json.dump(manifest, f, indent=2)

    # ---- verdicts
    mono = lambda rows, i: all(rows[j][i] < rows[j + 1][i] for j in range(len(rows) - 1))
    w_mono = mono(results["width"], 1)
    w_ratios = [r[1] / r[0] for r in results["width"]]
    t_mono = all(results["taper"][j][1] < results["taper"][j + 1][1] for j in range(len(results["taper"]) - 1))
    d_ratio = results["density"][1][1] / max(results["density"][0][1], 1e-6)
    l_mono_lum = mono(results["lighting"], 1)
    l_mono_con = mono(results["lighting"], 2)
    p_mono = mono(results["palette"], 1)
    p_ratios = [r[3] for r in results["palette"]]
    print("\nverdicts:")
    print(f"  width: monotone={w_mono}  measured/true ratios={['%.2f' % r for r in w_ratios]}")
    print(f"  taper: width rises as taper eases (monotone)={t_mono}")
    print(f"  passes: density ratio={d_ratio:.2f} (want ~2)")
    print(f"  lighting: mean_lum monotone={l_mono_lum}  contrast monotone={l_mono_con}")
    print(f"  palette: monotone={p_mono}  measured/true ratios={['%.2f' % r for r in p_ratios]}")


if __name__ == "__main__":
    main()

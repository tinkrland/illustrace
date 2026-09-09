"""ground-truth texture measurement (metrology rule four).

texture_energy's masked-mean construction collapsed at small subject scale
(anchor run 1) — its interior mask is scale-coupled. this module rebuilds
the measurement on vector ground truth: the substrate knows every fill
region exactly, so per-region statistics are computed over declared
interiors, never over a mask whose size depends on subject scale.

regions are declared in solo (untransformed) substrate coordinates; a
staging transform maps them into the rendered raster. strokes are excluded
by construction (regions are inset from stroke lines by more than the
stroke width plus jitter).

anchor laws (the predictions a reading must follow to be scale-normalized):
  canvas-anchored grain  — per-pixel sigma is invariant to subject scale
  subject-anchored grain — per-pixel sigma scales linearly with subject
                           scale s (subpixel averaging of the same cells)
"""
import numpy as np

# solo-coordinate fill interiors for the house substrate, inset from all
# stroke lines (stroke w 5 + jitter 2.5 + aa -> inset >= 6)
GT_HOUSE = {
    "wall_left":   (149, 232, 158, 296),
    "wall_bottom": (149, 302, 206, 386),
    "wall_right":  (260, 302, 282, 386),
    "roof":        (215, 172, 255, 196),
    "door":        (222, 318, 248, 386),
}


def _lum(a):
    return a @ [0.299, 0.587, 0.114]


def _region_stats(lum, box):
    x0, y0, x1, y1 = box
    r = lum[y0:y1, x0:x1]
    if r.size == 0:
        return None
    gx = np.zeros_like(lum); gy = np.zeros_like(lum)
    gx[:, 1:-1] = lum[:, 2:] - lum[:, :-2]
    gy[1:-1, :] = lum[2:, :] - lum[:-2, :]
    g = np.sqrt(gx ** 2 + gy ** 2)[y0:y1, x0:x1]
    return {"sigma": float(r.std()), "grad": float(g.mean()),
            "n": int(r.size)}


def map_box(box, tx=0.0, ty=0.0, s=1.0):
    """map a solo-coordinate region through a staging transform."""
    x0, y0, x1, y1 = box
    return (int(round(tx + s * x0)), int(round(ty + s * y0)),
            int(round(tx + s * x1)), int(round(ty + s * y1)))


def texture_gt(img, regions=None, tx=0.0, ty=0.0, s=1.0):
    """per-region luminance sigma + gradient magnitude over declared fill
    interiors, plus the area-weighted aggregate. scale-invariant by
    construction: regions come from the vector source, not from a raster
    mask."""
    regions = regions or GT_HOUSE
    a = np.asarray(img, float)
    if a.ndim == 2:
        a = a[..., None]
    lum = _lum(a)
    h, w = lum.shape
    out = {}
    ns, gs, total = 0.0, 0.0, 0
    for name, box in regions.items():
        b = map_box(box, tx, ty, s)
        b = (max(0, b[0]), max(0, b[1]), min(w, b[2]), min(h, b[3]))
        st = _region_stats(lum, b)
        if st is None or st["n"] < 25:
            continue
        out[name] = {"sigma": round(st["sigma"], 2), "grad": round(st["grad"], 2)}
        ns += st["sigma"] * st["n"]
        gs += st["grad"] * st["n"]
        total += st["n"]
    if total == 0:
        return {"regions": out, "sigma": None, "grad": None}
    return {"regions": out,
            "sigma": round(ns / total, 2), "grad": round(gs / total, 2)}

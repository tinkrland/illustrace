"""benchmark numbers. the six-ish things every run should answer."""
import numpy as np
from PIL import Image
from engine.analyzer import _as_array, stroke_mask, palette, MAX_RGB_DIST


def palette_distance(pal_a, pal_b):
    """mean nearest-color distance between weighted palettes, normalized 0..1."""
    da = 0.0
    wsum = 0.0
    for ca, wa in pal_a:
        d = min(np.linalg.norm(np.array(ca) - np.array(cb)) for cb, _ in pal_b)
        da += wa * d
        wsum += wa
    return float(da / max(wsum, 1e-6) / MAX_RGB_DIST)


def edge_mask(img, thresh=30):
    a = _as_array(img)
    lum = a @ [0.299, 0.587, 0.114]
    gx = np.zeros_like(lum); gy = np.zeros_like(lum)
    gx[:, 1:-1] = lum[:, 2:] - lum[:, :-2]
    gy[1:-1, :] = lum[2:, :] - lum[:-2, :]
    g = np.sqrt(gx ** 2 + gy ** 2)
    return g > thresh


def content_preservation(img_in, img_out):
    """geometry/composition proxy: edge-mask IoU. 1.0 = nothing structural moved."""
    ei, eo = edge_mask(img_in), edge_mask(img_out)
    inter = (ei & eo).sum()
    union = (ei | eo).sum()
    return float(inter / max(union, 1))


def non_target_preservation(img_in, img_out):
    """for palette transfer: strokes and texture should not move. 1.0 = untouched."""
    from engine.analyzer import stroke_width_stats, edge_direction_entropy, texture_energy
    moi, cvi = stroke_width_stats(img_in)
    moo, cvo = stroke_width_stats(img_out)
    ei = edge_direction_entropy(img_in); eo = edge_direction_entropy(img_out)
    ti = texture_energy(img_in); to = texture_energy(img_out)
    s1 = 1.0 - min(1.0, abs(cvi - cvo) / 0.5)
    s2 = 1.0 - min(1.0, abs(ei - eo) / 0.3)
    s3 = 1.0 - min(1.0, abs(ti - to) / 5.0)
    return float((s1 + s2 + s3) / 3)


def requested_fidelity_fraction(img_in, img_ref, img_out):
    """fraction of the input->ref palette distance that the output closed."""
    pi, pr, po = palette(img_in, 6), palette(img_ref, 6), palette(img_out, 6)
    d0 = palette_distance(pi, pr)
    d1 = palette_distance(po, pr)
    if d0 < 1e-9:
        return 1.0
    return float(max(0.0, (d0 - d1) / d0))

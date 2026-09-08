"""measurable style parameters. track b: can we compute what humans mean by style?"""
import numpy as np
from PIL import Image

MAX_RGB_DIST = 441.67  # sqrt(3*255^2)


def _as_array(img):
    if isinstance(img, Image.Image):
        return np.asarray(img.convert("RGB"), dtype=np.float64)
    return np.asarray(img.convert("RGB"), dtype=np.float64)


def palette(img, k=6, iters=12, sample=8000):
    """dominant colors via small k-means. returns [(rgb_tuple, weight), ...] sorted by weight."""
    a = _as_array(img)
    h, w, _ = a.shape
    px = a.reshape(-1, 3)
    idx = np.linspace(0, len(px) - 1, min(sample, len(px))).astype(int)
    px = px[idx]
    # init: spread across luminance-sorted pixels
    order = np.argsort(px @ [0.299, 0.587, 0.114])
    cents = px[order][np.linspace(0, len(order) - 1, k).astype(int)].copy()
    for _ in range(iters):
        d = ((px[:, None, :] - cents[None, :, :]) ** 2).sum(-1)
        assign = d.argmin(1)
        for j in range(k):
            m = px[assign == j]
            if len(m):
                cents[j] = m.mean(0)
    weights = np.bincount(assign, minlength=k) / len(px)
    out = [(tuple(int(round(c)) for c in cents[j]), float(weights[j]))
           for j in range(k) if weights[j] > 0.005]
    out.sort(key=lambda t: -t[1])
    return out


def stroke_mask(img, lum_threshold=80):
    """pixels that read as 'line work': dark and unsaturated."""
    a = _as_array(img)
    lum = a @ [0.299, 0.587, 0.114]
    sat = a.max(-1) - a.min(-1)
    return (lum < lum_threshold) & (sat < 60)


def stroke_width_stats(img):
    """stroke width via distance transform at centerline points. returns (mean_w, cv_w)."""
    from scipy import ndimage
    m = stroke_mask(img)
    if m.sum() < 50:
        return (0.0, 0.0)
    edt = ndimage.distance_transform_edt(m)
    # centerline approx: local maxima of EDT inside the mask
    mx = ndimage.maximum_filter(edt, size=5)
    core = m & (edt >= mx - 1e-9) & (edt > 0.8)
    if core.sum() < 10:
        core = m
    widths = 2.0 * edt[core]
    return (float(widths.mean()), float(widths.std() / max(widths.mean(), 1e-6)))


def edge_direction_entropy(img, bins=12):
    """entropy of stroke-boundary directions. rough hand-drawn lines wander more."""
    a = _as_array(img)[:, :, 0]  # channel 0 is enough for shape
    gx = np.zeros_like(a); gy = np.zeros_like(a)
    gx[:, 1:-1] = a[:, 2:] - a[:, :-2]
    gy[1:-1, :] = a[2:, :] - a[:-2, :]
    m = stroke_mask(img)
    boundary = m ^ ndimage_binary_erosion(m)
    near = ndimage_binary_dilation(boundary, iterations=1)
    sel = near & ((np.abs(gx) + np.abs(gy)) > 8)
    if sel.sum() < 20:
        return 0.0
    ang = np.arctan2(gy[sel], gx[sel]) + np.pi  # 0..2pi
    hist = np.histogram(ang, bins=bins, range=(0, 2 * np.pi))[0].astype(float)
    p = hist / hist.sum()
    p = p[p > 0]
    return float(-(p * np.log(p)).sum() / np.log(bins))


def texture_energy(img):
    """gradient energy over interior (non-background, non-stroke) regions."""
    a = _as_array(img)
    lum = a @ [0.299, 0.587, 0.114]
    gx = np.zeros_like(lum); gy = np.zeros_like(lum)
    gx[:, 1:-1] = lum[:, 2:] - lum[:, :-2]
    gy[1:-1, :] = lum[2:, :] - lum[:-2, :]
    m = stroke_mask(img)
    bg = np.zeros(lum.shape, bool)
    bg[0, :] = bg[-1, :] = True  # bg color = corners/edges
    bgcol = a[0, 0]
    bg = (np.abs(a - bgcol).sum(-1) < 30)
    interior = ~m & ~bg
    if interior.sum() < 100:
        return 0.0
    g = np.sqrt(gx ** 2 + gy ** 2)
    return float(g[interior].mean())


def ndimage_binary_erosion(m):
    from scipy import ndimage
    return ndimage.binary_erosion(m)


def ndimage_binary_dilation(m, iterations=1):
    from scipy import ndimage
    return ndimage.binary_dilation(m, iterations=iterations)


def profile(img):
    """the style vector v0: everything measurable today."""
    mw, cvw = stroke_width_stats(img)
    return {
        "palette": palette(img),
        "palette_hex": ["#%02x%02x%02x" % c for c, _ in palette(img)],
        "stroke_width_mean": round(mw, 2),
        "stroke_width_cv": round(cvw, 3),
        "edge_direction_entropy": round(edge_direction_entropy(img), 3),
        "texture_energy": round(texture_energy(img), 2),
    }

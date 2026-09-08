"""deterministic style operators. v0.1: soft palette transfer.

v0.0 (mode="hard") snapped every pixel within a tolerance of a dominant color to
that cluster's remapped color. stylebench caught it: the snap destroyed soft
interior blends (texture energy 46.7 -> 62.9). v0.1 (default) remaps with a soft
membership alpha = exp(-(d/softness)^2) based on distance to the nearest cluster
center, so flat fills (at cluster centers) fully adopt the reference color while
blended/antialiased pixels keep most of their gradient.
"""
import numpy as np
from PIL import Image
from engine.analyzer import _as_array, palette


def _match_weighted(target_pal, ref_pal):
    """greedy match each dominant target color to its nearest ref color."""
    pairs = []
    used = [False] * len(ref_pal)
    for ct, w in target_pal:
        best, bi = None, -1
        for j, (cr, _wr) in enumerate(ref_pal):
            if used[j]:
                continue
            d = np.linalg.norm(np.array(ct) - np.array(cr))
            if best is None or d < best:
                best, bi = d, j
        used[bi] = True
        pairs.append((ct, ref_pal[bi][0], w))
    return pairs


def palette_transfer(img, ref_img, strength=1.0, mode="soft", softness=60.0):
    """remap target's dominant colors toward matched reference colors.

    per-pixel color operation: geometry, strokes and composition are untouched
    by construction. strength in [0,1] interpolates toward the matched ref color.
    mode="soft": alpha-blended cluster membership (default, preserves blends).
    mode="hard": v0.0 behavior (tolerance snap; kept for benchmark comparison).
    """
    assert 0.0 <= strength <= 1.0
    a = _as_array(img).astype(np.float64)
    tp = palette(img, k=6)
    rp = palette(ref_img, k=6)
    pairs = _match_weighted(tp, rp)
    cents = np.array([p[0] for p in pairs], dtype=np.float64)
    refs = np.array([p[1] for p in pairs], dtype=np.float64)
    flat = a.reshape(-1, 3)

    if mode == "hard":
        out = flat.copy()
        for (ct, cr, _w) in pairs:
            ct = np.array(ct, float)
            d = np.linalg.norm(flat - ct, axis=1)
            sel = d < 90
            out[sel] = ct * (1 - strength) + np.array(cr, float) * strength
        return Image.fromarray(np.clip(out, 0, 255).reshape(a.shape).astype(np.uint8))

    # soft: nearest cluster with smooth membership alpha
    d = np.linalg.norm(flat[:, None, :] - cents[None, :, :], axis=2)  # (N, k)
    j = d.argmin(1)
    dmin = d[np.arange(len(flat)), j]
    alpha = np.exp(-(dmin / softness) ** 2)[:, None]
    remapped = cents[j] * (1 - strength) + refs[j] * strength
    out = flat * (1 - alpha) + remapped * alpha
    return Image.fromarray(np.clip(out, 0, 255).reshape(a.shape).astype(np.uint8))

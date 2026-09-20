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


# ---------------------------------------------------------------------------
# v0.2: the non-palette classical operators. philosophy is the same for all
# three: a mask-bounded, seeded, reversible-in-strength transform that moves
# exactly one factor and leaves the others untouched by construction. each
# one is a baseline the learned (lora) operators have to beat, and each one
# exposes its own honest limits in the docstring.
# ---------------------------------------------------------------------------

def _smooth_noise(shape, sigma_px, rng):
    """low-pass gaussian noise field, ~standard normal at every pixel."""
    from scipy import ndimage
    n = rng.standard_normal(shape)
    n = ndimage.gaussian_filter(n, sigma_px)
    n = n / max(1e-9, n.std())
    return n


def stroke_transfer(img, ref_img, strength=1.0, seed=0):
    """roughen mark-making toward the reference's stroke jitter.

    measures the stroke-width cv gap between img and ref and closes it
    (times strength) with a continuous thickness modulation: a low-pass
    noise field picks patches where strokes thicken and patches where
    they thin, so widths become uneven the way the reference reads.
    palette, texture interiors, and composition are untouched by
    construction.

    honest limit: cv is a width-variability proxy, not a full description
    of mark-making (the gesture is not drawn, only its width reading).
    smoothing (target cv below input) normalizes widths around the
    median instead of redrawing; genuine smooth-redraw is out of scope
    classically.
    """
    assert 0.0 <= strength <= 1.0
    from scipy import ndimage
    from engine.analyzer import stroke_mask, stroke_width_stats
    a = _as_array(img).astype(np.float64)
    m = stroke_mask(img)
    if m.sum() < 50:
        return img
    _, cv_in = stroke_width_stats(img)
    _, cv_ref = stroke_width_stats(ref_img)
    target = cv_in + (cv_ref - cv_in) * strength
    if abs(target - cv_in) < 1e-4:
        return img

    stroke_col = a[m].mean(0)
    bg = np.zeros(a.shape[:2], bool)
    bg[0, :] = bg[-1, :] = True
    bgcol = a[0, 0]
    bg = (np.abs(a - bgcol).sum(-1) < 60)

    edt_in = ndimage.distance_transform_edt(m)
    edt_out = ndimage.distance_transform_edt(~m)

    if target > cv_in:  # rougher: noise-driven width modulation
        rng = np.random.default_rng(seed)
        fld = _smooth_noise(m.shape, sigma_px=8.0, rng=rng)
        thicken = np.clip(fld, 0, 1)
        thin = np.clip(-fld, 0, 1)
    else:  # smoother: normalize widths around the median
        med = np.median(edt_in[m])
        dev = np.clip((edt_in - med) / max(1e-6, med), -1, 1)
        near = ndimage.binary_dilation(m, iterations=3)
        dev = np.where(near, dev, 0.0)
        thicken = np.clip(-dev, 0, 1)  # below-median spots dilate
        thin = np.clip(dev, 0, 1)      # above-median spots erode

    # dithered sub-pixel morph: flip probability ramps as amp*field crosses
    # the pixel's distance to the boundary, so the cv response is monotone
    # in amp instead of a 1px cliff.
    r_thin = np.random.default_rng(seed + 2).random(m.shape)
    r_thick = np.random.default_rng(seed + 3).random(m.shape)

    def morph(amp):
        rem = m & (r_thin < np.clip(amp * thin + 1.0 - edt_in, 0.0, 1.0))
        add = (~m) & (~bg) & (r_thick < np.clip(amp * thicken + 1.0 - edt_out, 0.0, 1.0))
        return (m & ~rem) | add

    lo_a, hi_a = 0.0, 3.0
    best = img
    for _ in range(8):  # bisect modulation amplitude on the measured cv
        amp = (lo_a + hi_a) / 2
        new_m = morph(amp)
        out = a.copy()
        grew = new_m & ~m
        lost = m & ~new_m
        rng2 = np.random.default_rng(seed + 1)
        if grew.any():
            out[grew] = stroke_col * (0.9 + 0.2 * rng2.random(grew.sum())[:, None])
        if lost.any():
            out[lost] = bgcol
        cand = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
        cv_now = stroke_width_stats(cand)[1]
        best = cand
        if abs(cv_now - target) < 0.005:
            return cand
        if (cv_now < target) == (target > cv_in):  # undershot -> push harder
            lo_a = amp
        else:
            hi_a = amp
    return best


def texture_transfer(img, ref_img, strength=1.0, seed=0, grain_sigma=2.0):
    """move interior grain toward the reference's texture energy.

    adds (or removes) seeded neutral grain inside interior regions until the
    texture_energy gap (times strength) is closed, with amplitude solved by
    a short fixed-point loop on the actual metric. strokes, palette, and
    composition are untouched by construction (grain is channel-neutral and
    interior-masked).

    honest limit: texture_energy is a gradient-energy mean, one number for
    what is really a distribution of grain statistics (see portilla-
    simoncelli for the full recipe). matched energy is not matched texture.
    """
    assert 0.0 <= strength <= 1.0
    from engine.analyzer import texture_energy, stroke_mask
    a = _as_array(img).astype(np.float64)
    e_in = texture_energy(img)
    e_ref = texture_energy(ref_img)
    target = e_in + (e_ref - e_in) * strength
    if abs(target - e_in) < 0.05:
        return img

    m = stroke_mask(img)
    bg = np.zeros(a.shape[:2], bool)
    bg[0, :] = bg[-1, :] = True
    bgcol = a[0, 0]
    bg = (np.abs(a - bgcol).sum(-1) < 60)
    interior = ~m & ~bg
    if interior.sum() < 100:
        return img

    rng = np.random.default_rng(seed)
    grain = np.clip(_smooth_noise(a.shape[:2], grain_sigma, rng), -2.5, 2.5)
    base = grain / max(1e-9, np.abs(grain).std())
    lum = a @ [0.299, 0.587, 0.114]

    def apply(amp):
        out = a.copy()
        g = base * amp
        for c in range(3):
            out[..., c] = np.where(interior, np.clip(out[..., c] + g, 0, 255),
                                   out[..., c])
        return Image.fromarray(out.astype(np.uint8))

    amp = (target - e_in) * 0.08  # first guess, then iterate on the metric
    best = img
    for _ in range(4):
        cand = apply(amp)
        e = texture_energy(cand)
        if abs(e - target) < 0.05:
            return cand
        amp *= max(0.2, (target - e_in) / max(1e-6, e - e_in))
        best = cand
    return best


def edge_transfer(img, ref_img, strength=1.0):
    """soften or harden edge language toward the reference's edge contrast.

    measures mean gradient magnitude on the edge band of both images and
    blends a gaussian blur (softening) or unsharp response (hardening) into
    img's edge band until the gap (times strength) is closed. palette,
    texture, and composition are untouched by construction (the blend is
    band-masked).

    honest limit: a scalar edge-contrast readout is not edge *language*
    (direction entropy, tapering, corner behavior all live in the same
    band). moving contrast alone is the crudest readable dial of a richer
    factor.
    """
    assert 0.0 <= strength <= 1.0
    from engine.metrics import edge_mask
    a = _as_array(img).astype(np.float64)
    lum = a @ [0.299, 0.587, 0.114]

    def edge_contrast(arr_lum):
        gx = np.zeros_like(arr_lum); gy = np.zeros_like(arr_lum)
        gx[:, 1:-1] = arr_lum[:, 2:] - arr_lum[:, :-2]
        gy[1:-1, :] = arr_lum[2:, :] - arr_lum[:-2, :]
        g = np.sqrt(gx ** 2 + gy ** 2)
        em = edge_mask(Image.fromarray(np.clip(arr_lum).astype(np.uint8)))
        return float(g[em].mean()) if em.any() else 0.0

    c_in = edge_contrast(lum)
    c_ref = edge_contrast(_as_array(ref_img).astype(np.float64)
                          @ [0.299, 0.587, 0.114])
    target = c_in + (c_ref - c_in) * strength
    if abs(target - c_in) < 0.5:
        return img

    em = edge_mask(img)
    band = np.zeros(em.shape, bool)
    from engine.analyzer import ndimage_binary_dilation
    band = ndimage_binary_dilation(em, iterations=2)

    soft = np.array(Image.fromarray(a.astype(np.uint8)).filter(
        __import__("PIL.ImageFilter", fromlist=["x"]).GaussianBlur(1.5)), dtype=np.float64)
    sharp = a + (a - soft) * 1.5
    direction = target < c_in  # soften or harden
    lo, hi = 0.0, 1.0
    out_img = img
    for _ in range(6):
        mix = (lo + hi) / 2
        src = soft if direction else sharp
        cand = a * (1 - mix) + src * mix
        cand = np.where(band[..., None], cand, a)
        c = edge_contrast(cand @ [0.299, 0.587, 0.114])
        if direction:
            if c > target: lo = mix
            else: hi = mix
        else:
            if c < target: lo = mix
            else: hi = mix
        out_img = Image.fromarray(np.clip(cand, 0, 255).astype(np.uint8))
    return out_img

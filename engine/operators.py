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


# ---------------------------------------------------------------------------
# v0.3: value, color-zone, and shading operators (classical baselines for the
# remaining 2d factors). design guards from the gpt-5 robustness pass
# (2026-09-20): value moves l* only with soft toe/shoulder and stroke-mask
# damping; zones shift chroma without replacing it and freeze l*; shading
# quantizes l* with dither so flat regions do not band.
# ---------------------------------------------------------------------------

def _lab_l(img):
    """luma channel only, the safe single-factor path (chroma untouched)."""
    return _as_array(img).astype(np.float64) @ [0.299, 0.587, 0.114]


def _interior_mask(img):
    from engine.analyzer import stroke_mask
    a = _as_array(img)
    m = stroke_mask(img)
    bg = np.zeros(a.shape[:2], bool)
    bg[0, :] = bg[-1, :] = True
    bg = (np.abs(a - a[0, 0]).sum(-1) < 60)
    return ~m & ~bg


def value_transfer(img, ref_img, strength=1.0):
    """close the value_range gap with a monotone luma curve.

    value_range reads p95-p5 of luma, so the operator remaps exactly that
    window: img's [p5, p95] luma span stretches (or squeezes) toward the
    reference's span, centered on img's own mid value. chroma is
    untouched by construction, strokes get half strength (thin linework
    should not crush), and the curve is flat outside the window so
    nothing clips hard.

    honest limit: value_range is a spread readout, not a histogram shape.
    two images can share a span and distribute mass inside it very
    differently; this closes the spread, not the distribution.
    """
    assert 0.0 <= strength <= 1.0
    from engine.analyzer import value_range, stroke_mask
    a = _as_array(img).astype(np.float64)
    li = _lab_l(img)
    lr = _lab_l(ref_img)
    v_in, v_ref = value_range(img), value_range(ref_img)
    target = v_in + (v_ref - v_in) * strength
    if abs(target - v_in) < 1.0:
        return img

    p5i, p95i = np.percentile(li, [5, 95])
    mid = (p5i + p95i) / 2
    # damp mask: half strength on strokes, and near strong gradients
    gx = np.zeros_like(li); gy = np.zeros_like(li)
    gx[:, 1:-1] = li[:, 2:] - li[:, :-2]
    gy[1:-1, :] = li[2:, :] - li[:-2, :]
    g = np.sqrt(gx ** 2 + gy ** 2)
    damp = 1.0 - 0.5 * (g > np.percentile(g, 95))
    m = stroke_mask(img).astype(np.float64)
    blend = damp * (1.0 - 0.5 * m)

    # fixed-point loop: damping steals some of the applied stretch, so
    # inflate the window until the *measured* value_range lands on target
    window = target
    best = img
    for _ in range(4):
        lo_t, hi_t = mid - window / 2, mid + window / 2
        new_l = np.interp(li, [p5i, p95i], [lo_t, hi_t])
        new_l = new_l * blend + li * (1 - blend)
        out = a.copy()
        d = new_l - li
        for c in range(3):
            out[..., c] = np.clip(out[..., c] + d, 0, 255)
        cand = Image.fromarray(out.astype(np.uint8))
        got = value_range(cand)
        best = cand
        if abs(got - target) < 1.5:
            return cand
        window *= max(0.5, target / max(1.0, got))
    return best


def color_zone_transfer(img, ref_img, strength=1.0, k=6, min_zone_frac=0.01):
    """recolor whole color zones coherently toward the reference's zones.

    k-means zones in (a*-ish, b*-ish) chroma space on both images, zones
    matched by centroid proximity, then each zone's chroma is *shifted*
    (not replaced) toward its matched reference zone by strength. l* is
    frozen everywhere, per-pixel chroma residuals survive, zones below
    min_zone_frac are merged into their nearest big neighbor, and zone
    borders are feathered so no new hard edges are minted.

    distinct from palette_transfer: that moves per-pixel cluster
    membership; this moves shape-coherent regions as units, so the
    palette moves without breaking flat fills or gradients inside a zone.

    honest limit: zone matching is centroid-based; a target whose zones
    have no chroma analogue in the reference gets its nearest-zone
    colour, which is a mapping choice, not a truth.
    """
    assert 0.0 <= strength <= 1.0
    from engine.metrics import palette_distance
    from engine.analyzer import palette
    a = _as_array(img).astype(np.float64)
    r = _as_array(ref_img).astype(np.float64)

    def zones(arr):
        """hand-rolled seeded k-means on opponent chroma axes (l*-free)."""
        h, w = arr.shape[:2]
        ca = arr[..., 0] - (arr[..., 1] + arr[..., 2]) / 2
        cb = arr[..., 2] - (arr[..., 0] + arr[..., 1]) / 2
        feat = np.stack([ca.ravel(), cb.ravel()], 1)
        rng = np.random.default_rng(0)
        idx = rng.choice(len(feat), size=min(8000, len(feat)), replace=False)
        samp = feat[idx]
        cents = samp[np.linspace(0, len(samp) - 1, k).astype(int)]
        for _ in range(10):
            d = ((samp[:, None, :] - cents[None, :, :]) ** 2).sum(-1)
            lab = d.argmin(1)
            for z in range(k):
                pts = samp[lab == z]
                if len(pts):
                    cents[z] = pts.mean(0)
        d = ((feat[:, None, :] - cents[None, :, :]) ** 2).sum(-1)
        labels = d.argmin(1)
        sizes = np.bincount(labels, minlength=k) / len(feat)
        return labels.reshape(h, w), cents, sizes

    lab_i, cents_i, sizes_i = zones(a)
    lab_r, cents_r, sizes_r = zones(r)

    # prune tiny zones: merge their pixels into the nearest surviving centroid
    big_i = np.where(sizes_i >= min_zone_frac)[0]
    if len(big_i) == 0:
        return img
    def relabel(lab, cents, big):
        remap = {int(b): int(i) for i, b in enumerate(big)}
        cents_big = cents[big]
        for z in range(len(cents)):
            if z not in remap:
                d = np.linalg.norm(cents[z] - cents_big, axis=1)
                remap[z] = int(np.argmin(d))
        return np.vectorize(remap.__getitem__)(lab), cents_big
    lab_i, cents_i = relabel(lab_i, cents_i, big_i)
    big_r = np.where(sizes_r >= min_zone_frac)[0]
    if len(big_r) == 0:
        return img
    lab_r, cents_r = relabel(lab_r, cents_r, big_r)

    # match zones img->ref: hungarian assignment on a size-aware cost, so
    # dominant regions pair with dominant regions (a background is a
    # background) instead of the nearest tiny chroma accident
    from scipy.optimize import linear_sum_assignment
    ni, nr = len(cents_i), len(cents_r)
    si_big = sizes_i[big_i] + 1e-3
    sr_big = sizes_r[big_r] + 1e-3
    cost = np.zeros((ni, nr))
    for x in range(ni):
        for y in range(nr):
            d = np.linalg.norm(cents_r[y] - cents_i[x])
            size_pen = abs(np.log(si_big[x]) - np.log(sr_big[y]))
            cost[x, y] = d * (1.0 + 1.5 * size_pen)
    rows, cols = linear_sum_assignment(cost)
    match = {int(r): int(c) for r, c in zip(rows, cols)}

    # apply shifts as exact luma-preserving (dR, dG, dB) triples: solve
    # [ca; cb; luma] = A @ [dR; dG; dB] with the luma row pinned to 0, so
    # the value factor is frozen by construction, not corrected after
    A = np.array([[1.0, -0.5, -0.5],
                  [-0.5, -0.5, 1.0],
                  [0.299, 0.587, 0.114]])
    Ainv = np.linalg.inv(A)
    from scipy import ndimage
    d_rgb = np.zeros_like(a)
    delta_map = np.zeros(a.shape[:2])
    for i, j in match.items():
        d_ca, d_cb = (cents_r[j] - cents_i[i]) * strength
        d = Ainv @ np.array([d_ca, d_cb, 0.0])
        core = lab_i == i
        feather = ndimage.binary_dilation(core, iterations=1) & ~core
        for c in range(3):
            d_rgb[..., c][core] = d[c]
            d_rgb[..., c][feather] = d[c] * 0.5
        delta_map[core] = 1.0
        delta_map[feather] = 0.5
    # per-pixel attenuation so no channel clips (luma stays exact where alpha=1)
    alpha = np.ones(a.shape[:2])
    for c in range(3):
        d = d_rgb[..., c]
        pos, neg = d > 0, d < 0
        alpha[pos] = np.minimum(alpha[pos], (255 - a[..., c][pos]) / d[pos])
        alpha[neg] = np.minimum(alpha[neg], -a[..., c][neg] / d[neg])
    alpha = np.clip(alpha, 0, 1)[..., None]
    out = np.clip(a + d_rgb * alpha, 0, 255)
    return Image.fromarray(out.astype(np.uint8))


def _interior_levels(img):
    """how many luma levels carry 95% of the interior pixels. flat = few."""
    m = _interior_mask(img)
    if m.sum() < 100:
        return 1
    lum = _lab_l(img)[m].astype(int)
    hist = np.bincount(lum, minlength=256)
    order = np.argsort(-hist)
    cum = np.cumsum(hist[order])
    return int(np.searchsorted(cum, 0.95 * lum.size) + 1)


def shading_transfer(img, ref_img, strength=1.0, seed=0):
    """flatten rendering toward the reference's interior level count.

    rendering language proxy: how many distinct luma levels carry the
    interior. the operator quantizes interior luma to the top-mass
    levels, count interpolated between img and ref by strength, with
    seeded dither so flat regions do not band. strokes and background
    are untouched; color stays because quantization is a luma-bin snap
    and chroma rides along per pixel.

    honest limit: this is the flattening dial only. toward a *more*
    levels-rich reference it is a no-op (adding gradient complexity is
    the learned operators' job), and a level count is a crude readout of
    shading style: two renders can share a count and differ in how the
    levels are arranged.
    """
    assert 0.0 <= strength <= 1.0
    from scipy import ndimage
    n_in = _interior_levels(img)
    n_ref = _interior_levels(ref_img)
    target = int(round(n_in + (n_ref - n_in) * strength))
    if target >= n_in or target < 1:
        return img
    interior = _interior_mask(img)
    feather = ndimage.binary_dilation(interior) & ~interior
    li = _lab_l(img)
    rng = np.random.default_rng(seed)
    q = li + rng.normal(0, 1.5, li.shape)
    hist = np.bincount(q[interior].astype(int).clip(0, 255), minlength=256)
    reps = np.sort(np.argsort(-hist)[:target])
    out_l = li.copy()
    idx = np.clip(np.searchsorted(reps, q) - 1, 0, len(reps) - 1)
    snapped = reps[idx]
    up = np.clip(idx + 1, 0, len(reps) - 1)
    closer = np.abs(reps[up] - q) < np.abs(snapped - q)
    snapped = np.where(closer, reps[up], snapped)
    out_l[interior] = snapped[interior]
    out_l[feather] = (snapped[feather] + li[feather]) / 2
    a = _as_array(img).astype(np.float64)
    out = a.copy()
    d = out_l - li
    for c in range(3):
        out[..., c] = np.clip(out[..., c] + d, 0, 255)
    return Image.fromarray(out.astype(np.uint8))

"""parametric svg stimulus generation — the editable-stroke substrate.

same house geometry as make_stimuli_arch, but the document is now layered svg:
    geometry (clean paths) + brush recipes + fill roles + texture filter +
    lighting overlay. render = deterministic bake from (geometry, recipes, seed).

why: research/EDITABLE_SVG_STROKES.md — the parameters ARE ground truth, so the
bench gains a measurement-fidelity experiment: does measured stroke cv track
true jitter σ? does measured texture energy track grain amplitude?

brushes v0:
    clean    w=5, jitter 0
    sketchy  w=5, jitter σ, rough.js-style double pass (second stroke, sub-seed)
    marker   w=9, round caps, jitter 0

renderer note: cairosvg does not implement feTurbulence or blend modes, so the
canonical svg carries the texture/lighting layers (for real editors/browsers)
while the analysis raster approximates grain as additive noise — documented
approximation, same parameter, same seed.
"""
import json
import math
import os
import random

import numpy as np
from xml.sax.saxutils import quoteattr
import cairosvg
from PIL import Image

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from engine.analyzer import profile
from engine.analyzer import palette as kpalette

SIZE = 512
RSCALE = 2  # raster supersample

REF_WARM = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "data", "test_images", "ref_01.webp"))
REF_COOL = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "data", "test_images", "ref_02.png"))

# ---- geometry (the intent — one source of truth, same as arch set)
GEO = {
    "walls": [(140, 220), (140, 392), (330, 392), (330, 220)],
    "roof": [(120, 222), (235, 130), (350, 222)],
    "chimney": [(290, 150), (290, 210), (318, 210), (318, 150)],
    "door": [(218, 310), (218, 392), (252, 392), (252, 310)],
    "window_l": [(162, 250), (162, 294), (206, 294), (206, 250), (162, 250)],
    "window_r": [(288, 250), (288, 294), (332, 294), (332, 250), (288, 250)],
    "tree_trunk": [(430, 320), (430, 392), (446, 392), (446, 320)],
    "ground": [(0, 392), (512, 392)],
}

BRUSHES = {
    "clean":   {"width": 5, "jitter": 0.0, "passes": 1, "caps": "square"},
    "sketchy": {"width": 5, "jitter": 2.5, "passes": 2, "caps": "round"},
    "marker":  {"width": 9, "jitter": 0.0, "passes": 1, "caps": "round"},
}


def jitter_polyline(pts, sigma, seed, sigma_lat=None, sigma_lin=None):
    """rough.js-style displacement. sigma=0 returns the clean path.

    optional jitter split (procreate-style): sigma_lat displaces perpendicular
    to the local path direction (wobbly line), sigma_lin along it (speed /
    density wobble). passing the split changes the code path — legacy calls
    (both None) stay byte-identical so old stimuli reproduce exactly."""
    if sigma_lat is None and sigma_lin is None:
        if sigma <= 0:
            return list(pts)
        rng = random.Random(seed)
        out = [pts[0]]
        for j in range(len(pts) - 1):
            x0, y0 = pts[j]
            x1, y1 = pts[j + 1]
            for f in (0.25, 0.5, 0.75):
                out.append((x0 + (x1 - x0) * f + rng.gauss(0, sigma),
                            y0 + (y1 - y0) * f + rng.gauss(0, sigma)))
            out.append(pts[j + 1])  # vertices stay — dropping them cut corners
        return out
    sigma_lat = sigma_lat or 0.0
    sigma_lin = sigma_lin or 0.0
    if sigma_lat <= 0 and sigma_lin <= 0:
        return list(pts)
    rng = random.Random(seed)
    out = [pts[0]]
    for j in range(len(pts) - 1):
        x0, y0 = pts[j]
        x1, y1 = pts[j + 1]
        dx, dy = x1 - x0, y1 - y0
        seg = (dx * dx + dy * dy) ** 0.5 or 1.0
        ux, uy = dx / seg, dy / seg
        for f in (0.25, 0.5, 0.75):
            bx, by = x0 + dx * f, y0 + dy * f
            if sigma_lat:
                g = rng.gauss(0, sigma_lat)
                bx, by = bx - uy * g, by + ux * g
            if sigma_lin:
                g = rng.gauss(0, sigma_lin)
                bx, by = bx + ux * g, by + uy * g
            out.append((bx, by))
        out.append(pts[j + 1])
    return out


def resample(pts, step=6):
    """densify a polyline to ~step-px samples (outline baking needs density)."""
    out = []
    for j in range(len(pts) - 1):
        x0, y0 = pts[j]; x1, y1 = pts[j + 1]
        seg = max(2, int(((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5 / step))
        for f in range(seg):
            t = f / seg
            out.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t))
    out.append(pts[-1])
    return out


def bake_outline(pts, base_w, taper, sigma, seed, taper_dir=None,
                  sigma_lat=None, sigma_lin=None, width_profile=None):
    """variable-width tapered stroke baked as a filled outline path
    (perfect-freehand pattern). taper = fraction of length spent easing in/out.
    taper_dir: None = symmetric (default), "toward" = ease out only
    (stroke narrows at the path end / tip), "away" = ease in only
    (stroke starts thin, thickens toward the path end).

    width_profile (v2): list of (t, width_factor) control points, linearly
    interpolated along arc-length t. subsumes taper (a symmetric taper is
    [(0,0),(taper,1),(1-taper,1),(1,0)]). when both are given width_profile
    is the parameter of record."""
    if width_profile:
        prof = sorted(width_profile)

        def prof_factor(t):
            if t <= prof[0][0]:
                return prof[0][1]
            if t >= prof[-1][0]:
                return prof[-1][1]
            for (t0, f0), (t1, f1) in zip(prof, prof[1:]):
                if t0 <= t <= t1:
                    u = (t - t0) / (t1 - t0) if t1 > t0 else 0.0
                    return f0 + (f1 - f0) * u
            return prof[-1][1]
    else:
        if taper_dir == "toward":
            taper_in, taper_out = 0.0, taper
        elif taper_dir == "away":
            taper_in, taper_out = taper, 0.0
        else:
            taper_in, taper_out = taper, taper
    p = resample(jitter_polyline(pts, sigma, seed, sigma_lat, sigma_lin))
    if taper_dir == "toward":
        taper_in, taper_out = 0.0, taper
    elif taper_dir == "away":
        taper_in, taper_out = taper, 0.0
    else:
        taper_in, taper_out = taper, taper
    p = resample(jitter_polyline(pts, sigma, seed))
    n = len(p)
    L = [0.0]
    for i in range(1, n):
        L.append(L[-1] + ((p[i][0] - p[i - 1][0]) ** 2 + (p[i][1] - p[i - 1][1]) ** 2) ** 0.5)
    total = L[-1] or 1.0
    ts = [l / total for l in L]
    left, right = [], []
    for i, (x, y) in enumerate(p):
        t = ts[i]
        if i == 0: dx, dy = p[1][0] - x, p[1][1] - y
        elif i == n - 1: dx, dy = x - p[i - 1][0], y - p[i - 1][1]
        else: dx, dy = p[i + 1][0] - p[i - 1][0], p[i + 1][1] - p[i - 1][1]
        nrm = (dx * dx + dy * dy) ** 0.5 or 1.0
        nx, ny = -dy / nrm, dx / nrm
        if width_profile:
            w = base_w * prof_factor(t)
        elif taper > 0:
            f = 1.0
            if taper_in > 0: f = min(f, t / taper_in)
            if taper_out > 0: f = min(f, (1 - t) / taper_out)
            w = base_w * f
        else:
            w = base_w
        w = max(w, 0.4)
        left.append((x + nx * w / 2, y + ny * w / 2))
        right.append((x - nx * w / 2, y - ny * w / 2))
    ring = left + right[::-1]
    return "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in ring) + " Z"


def derive_roles(path=REF_WARM):
    im = Image.open(path).convert("RGB"); im.thumbnail((512, 512))
    pal = kpalette(im, 6)
    colors = [(np.array(rgb, float), w) for rgb, w in pal]
    lum = lambda c: float(c @ [0.299, 0.587, 0.114])
    sat = lambda c: float(c.max() - c.min())
    bg_i = max(range(len(colors)), key=lambda i: lum(colors[i][0]))
    st_i = min(range(len(colors)), key=lambda i: lum(colors[i][0]))
    rest = [colors[i] for i in range(len(colors)) if i not in (bg_i, st_i)]
    ground = min(rest, key=lambda t: lum(t[0]))[0]
    rest = [t for t in rest if t[0] is not ground]
    wall = max(rest, key=lambda t: t[1])[0]
    rest = [t for t in rest if t[0] is not wall]
    roof = max(rest, key=lambda t: sat(t[0]))[0]
    rest = [t for t in rest if t[0] is not roof]
    window = rest[0][0]
    door = (0.5 * ground + 0.5 * wall).clip(0, 255)
    h = lambda c: "#%02x%02x%02x" % tuple(int(x) for x in c)
    return {"bg": h(colors[bg_i][0]), "stroke": h(colors[st_i][0]),
            "ground": h(ground), "wall": h(wall), "roof": h(roof),
            "window": h(window), "door": h(door)}


def stroke_d(name, brush, seed):
    """path data for one stroked path under a brush recipe.

    v2 pass params: pass_scatter (sigma of a whole-pass offset — the
    double-stroke misalignment of sketchy/charcoal), pass_rotation (max
    degrees each pass rotates about its own centroid — misalignment that
    keeps endpoints put). both seeded, both only visible with passes > 1."""
    pts = GEO[name]
    d = []
    rng = random.Random(seed * 31 + 17)
    ps = brush.get("pass_scatter", 0.0)
    pr = brush.get("pass_rotation", 0.0)  # degrees
    for p in range(brush["passes"]):
        j = jitter_polyline(pts, brush["jitter"], seed + p * 77,
                            brush.get("jitter_lat"), brush.get("jitter_lin"))
        if ps or pr:
            ox, oy = (rng.gauss(0, ps), rng.gauss(0, ps)) if ps else (0.0, 0.0)
            ang = math.radians(rng.uniform(-pr, pr)) if pr else 0.0
            cx = sum(x for x, _ in j) / len(j)
            cy = sum(y for _, y in j) / len(j)
            ca, sa = math.cos(ang), math.sin(ang)
            j = [(cx + (x - cx) * ca - (y - cy) * sa + ox,
                  cy + (x - cx) * sa + (y - cy) * ca + oy) for x, y in j]
        if j[0] != j[-1] or len(j) > 2:
            d.append("M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in j))
    return " ".join(d)


def build_svg(roles, brush, textured=False, lighting=None, seed=7):
    """layered svg document. textured/lighting layers are canonical svg
    (filter + blend overlay) even though cairosvg approximates them on raster."""
    grain_filter = """
    <filter id="grain" x="0" y="0" width="100%%" height="100%%">
      <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="%(seed)d" result="n"/>
      <feColorMatrix in="n" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 %(amp).2f 0" result="na"/>
      <feComposite in="SourceGraphic" in2="na" operator="in" result="cn"/>
      <feBlend in="cn" in2="SourceGraphic" mode="normal"/>
    </filter>""" % {"seed": seed, "amp": 0.5}

    fills = f"""
  <g id="fills"{' filter="url(#grain)"' if textured else ''}>
    <rect x="0" y="392" width="512" height="120" class="fill-ground" fill="{roles['ground']}"/>
    <rect x="140" y="220" width="190" height="172" class="fill-wall" fill="{roles['wall']}"/>
    <polygon points="120,222 235,130 350,222" class="fill-roof" fill="{roles['roof']}"/>
    <rect x="290" y="150" width="28" height="60" class="fill-roof" fill="{roles['roof']}"/>
    <rect x="218" y="310" width="34" height="82" class="fill-door" fill="{roles['door']}"/>
    <rect x="162" y="250" width="44" height="44" class="fill-window" fill="{roles['window']}"/>
    <rect x="288" y="250" width="44" height="44" class="fill-window" fill="{roles['window']}"/>
    <rect x="430" y="320" width="16" height="72" class="fill-door" fill="{roles['door']}"/>
    <ellipse cx="438" cy="242" rx="46" ry="46" class="fill-ground" fill="{roles['ground']}"/>
    <polygon points="226,392 244,392 270,470 200,470" class="fill-door" fill="{roles['door']}"/>
  </g>"""

    # v2: opacity_falloff — alpha ramp along each path's dominant bbox axis,
    # rendered as a per-path paint-server gradient (canonical svg, cairosvg-safe)
    fade = brush.get("opacity_falloff")
    fade_defs, fade_paint = "", ""
    if fade:
        a0, a1 = fade.get("start", 1.0), fade.get("end", 1.0)
        grad = []
        for name in GEO:
            xs = [q[0] for q in GEO[name]]; ys = [q[1] for q in GEO[name]]
            axis = ('x1="0" y1="0" x2="1" y2="0"' if (max(xs) - min(xs)) >= (max(ys) - min(ys))
                    else 'x1="0" y1="0" x2="0" y2="1"')
            grad.append(f'<linearGradient id="fade_{name}" {axis}>'
                        f'<stop offset="0" stop-color="{roles["stroke"]}" stop-opacity="{a0}"/>'
                        f'<stop offset="1" stop-color="{roles["stroke"]}" stop-opacity="{a1}"/>'
                        f'</linearGradient>')
        fade_defs = "".join(grad)

    def baked_fill(name):
        return f"url(#fade_{name})" if fade else roles["stroke"]

    def linework_fade_attr(name):
        return f' stroke="url(#fade_{name})"' if fade else ""

    if brush.get("taper") or brush.get("width_profile"):
        paths = []
        for name in GEO:
            d = bake_outline(GEO[name], brush["width"], brush.get("taper", 0.0),
                             brush.get("jitter", 0.0), seed + sum(map(ord, name)),
                             brush.get("taper_dir"), brush.get("jitter_lat"),
                             brush.get("jitter_lin"), brush.get("width_profile"))
            paths.append(f'    <path class="stroke stroke-{name} baked-outline" '
                         f'data-brush="tapered" fill="{baked_fill(name)}" stroke="none" d="{d}"/>')
    else:
        paths = [f'    <path class="stroke stroke-{name}" data-brush="linework"{linework_fade_attr(name)} d="{stroke_d(name, brush, seed)}"/>'
                 for name in GEO]
    strokes = "\n".join(paths)
    strokes_block = f"""
  <g id="strokes" class="brush-{BRUSHES_LABEL}" stroke="{roles['stroke']}"
     stroke-width="{brush['width']}" stroke-linecap="{brush['caps']}"
     stroke-linejoin="round" fill="none">
{strokes}
  </g>"""

    lighting_block = ""
    if lighting:
        lighting_block = f"""
  <g id="lighting" style="mix-blend-mode:{lighting.get('blend','soft-light')}"
     data-layer="lighting" data-recipe={quoteattr(json.dumps(lighting))}>
    <defs><linearGradient id="lgrad" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{lighting.get('color','#ffedd0')}" stop-opacity="{lighting.get('strength',0.5)}"/>
      <stop offset="1" stop-color="#000000" stop-opacity="0"/>
    </linearGradient></defs>
    <rect x="0" y="0" width="512" height="512" fill="url(#lgrad)"/>
  </g>"""

    defs = f"<defs>{grain_filter if textured else ''}{fade_defs}</defs>"
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  {defs}
  <rect x="0" y="0" width="512" height="512" class="fill-bg" fill="{roles['bg']}"/>
{fills}
{strokes_block}
{lighting_block}
</svg>"""


BRUSHES_LABEL = "custom"


def render(svg_str, out_png, grain_amp=0.0, seed=7, lighting_apply=None):
    """raster bake. grain approximated additively; lighting approximated as a
    top-left warm gradient overlay (cairosvg lacks feTurbulence + blend modes)."""
    png = cairosvg.svg2png(bytestring=svg_str.encode(), output_width=SIZE * RSCALE,
                          output_height=SIZE * RSCALE)
    im = Image.open(__import__("io").BytesIO(png)).convert("RGB")
    if grain_amp > 0:
        a = np.asarray(im, dtype=np.int16)
        rng = np.random.default_rng(seed)
        a = np.clip(a + rng.normal(0, grain_amp, a.shape[:2])[..., None], 0, 255).astype(np.uint8)
        im = Image.fromarray(a)
    if lighting_apply is not None:
        strength, color = lighting_apply
        a = np.asarray(im, float)
        h, w = a.shape[:2]
        X, Y = np.meshgrid(np.arange(w), np.arange(h))
        alpha = strength * np.clip(1 - (X / (w * 1.4) + Y / (h * 1.4)), 0, 1)
        col = np.array(color, float)
        # true soft-light (w3c compositing spec), matching the svg layer's
        # mix-blend-mode: soft-light — the v0 alpha-overlay was unfaithful.
        b = a / 255.0
        s = col[None, None, :] / 255.0
        lit = np.where(s <= 0.25,
                       b - (1 - 2 * s) * b * (1 - b),
                       b + (2 * s - 1) * (np.sqrt(b) - b))
        lit = (lit * 255.0).clip(0, 255)
        a = a * (1 - alpha[..., None]) + lit * alpha[..., None]
        im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    im = im.resize((SIZE, SIZE), Image.LANCZOS)
    im.save(out_png)
    return im


def main():
    out = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "data", "generated", "arch_svg"))
    os.makedirs(out, exist_ok=True)
    roles = derive_roles()
    manifest = {"images": [], "roles": roles, "ground_truth": {}}

    # ---- fidelity sweep 1: jitter σ (brush factor)
    sweep = []
    for sigma in (0.0, 1.25, 2.5, 3.75):
        name = f"jit_{sigma:.2f}".replace(".", "p")
        brush = dict(BRUSHES["sketchy"], jitter=sigma, passes=1)
        svg = build_svg(roles, brush, seed=7)
        with open(os.path.join(out, name + ".svg"), "w") as f:
            f.write(svg)
        im = render(svg, os.path.join(out, name + ".png"))
        p = profile(im)
        manifest["images"].append({"file": name, "jitter": sigma})
        sweep.append((sigma, p["stroke_width_cv"], p["edge_direction_entropy"], p["texture_energy"]))
        print(f"jitter σ={sigma:4.2f}  stroke_cv={p['stroke_width_cv']:.3f}  edge_ent={p['edge_direction_entropy']:.3f}  tex={p['texture_energy']:.1f}")

    # ---- fidelity sweep 2: grain amplitude (texture factor)
    gsweep = []
    for amp in (0.0, 8.0, 14.0):
        name = f"grain_{amp:.0f}"
        svg = build_svg(roles, BRUSHES["clean"], textured=(amp > 0), seed=7)
        with open(os.path.join(out, name + ".svg"), "w") as f:
            f.write(svg)
        im = render(svg, os.path.join(out, name + ".png"), grain_amp=amp)
        p = profile(im)
        manifest["images"].append({"file": name, "grain_amp": amp})
        gsweep.append((amp, p["texture_energy"], p["stroke_width_cv"]))
        print(f"grain={amp:4.1f}  tex={p['texture_energy']:.1f}  stroke_cv={p['stroke_width_cv']:.3f}")

    # ---- style composer showcase: sketchy brush + grain + lighting, one svg
    svg = build_svg(roles, BRUSHES["sketchy"], textured=True,
                    lighting={"blend": "soft-light", "strength": 0.45, "color": "#ffedd0"}, seed=7)
    with open(os.path.join(out, "showcase.svg"), "w") as f:
        f.write(svg)
    render(svg, os.path.join(out, "showcase.png"), grain_amp=10.0)
    manifest["images"].append({"file": "showcase", "brush": "sketchy",
                              "grain_amp": 10.0, "lighting": {"blend": "soft-light", "strength": 0.45}})
    print("wrote showcase (sketchy + grain + lighting)")

    with open(os.path.join(out, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)

    jit_mono = all(sweep[i][1] < sweep[i + 1][1] for i in range(len(sweep) - 1))
    grain_mono = all(gsweep[i][1] < gsweep[i + 1][1] for i in range(len(gsweep) - 1))
    print(f"\nfidelity: jitter->stroke_cv monotone={jit_mono}  grain->texture monotone={grain_mono}")


if __name__ == "__main__":
    main()

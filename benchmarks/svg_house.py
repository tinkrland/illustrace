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

REF_WARM = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "data", "references", "ref_01.webp"))
REF_COOL = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "data", "references", "ref_02.png"))

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


def jitter_polyline(pts, sigma, seed):
    """rough.js-style displacement. sigma=0 returns the clean path."""
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


def bake_outline(pts, base_w, taper, sigma, seed):
    """variable-width tapered stroke baked as a filled outline path
    (perfect-freehand pattern). taper = fraction of length spent easing in/out."""
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
        w = base_w * min(1.0, t / taper, (1 - t) / taper) if taper > 0 else base_w
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
    """path data for one stroked path under a brush recipe."""
    pts = GEO[name]
    d = []
    for p in range(brush["passes"]):
        j = jitter_polyline(pts, brush["jitter"], seed + p * 77)
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

    if brush.get("taper"):
        paths = [f'    <path class="stroke stroke-{name} baked-outline" data-brush="tapered" fill="{roles["stroke"]}" stroke="none" d="{bake_outline(GEO[name], brush["width"], brush["taper"], brush.get("jitter", 0.0), seed + sum(map(ord, name)))}"/>'
                 for name in GEO]
    else:
        paths = [f'    <path class="stroke stroke-{name}" data-brush="linework" d="{stroke_d(name, brush, seed)}"/>'
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

    defs = f"<defs>{grain_filter if textured else ''}</defs>"
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

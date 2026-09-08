"""architecture stimulus generation. exactly one style factor changes per pair.

non-character subject: a storybook house scene (house, roof, door, windows, tree,
ground, sky). same composition, same geometry, same seed across all variants.

three controlled factors, 2x2x2 = 8 images:
    palette  : derived from measured reference palettes (ref_01 warm riso vs
               ref_02 cool ink) — colors come from real illustrations, not
               hand-picked values
    stroke   : clean vs rough (jittered linework, same machinery as the frog set)
    texture  : flat fills vs textured fills (grain applied to fill layer only,
               never to strokes — strokes drawn on top after noise)

pairs against base A (p1, clean, flat):
    A-B palette-only    A-C stroke-only    A-D texture-only
    E,F,G,H are the interaction cells for later disentanglement checks.

writes arch/*.png plus manifest.json recording factor settings + palette
provenance, so any bench run knows exactly which factor moved.
"""
import json
import os
import random
import numpy as np
from PIL import Image, ImageDraw

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from engine.analyzer import palette

SIZE = 512
SS = 4  # supersampling

REF_WARM = os.path.join(os.path.dirname(__file__), "..", "data", "references", "ref_01.webp")
REF_COOL = os.path.join(os.path.dirname(__file__), "..", "data", "references", "ref_02.png")


def derive_roles(img, k=6):
    """measured palette -> semantic drawing roles. deterministic."""
    pal = palette(img, k)
    colors = [(np.array(rgb, float), w) for rgb, w in pal]
    lum = lambda c: c @ [0.299, 0.587, 0.114]
    sat = lambda c: c.max() - c.min()

    bg = max(colors, key=lambda t: lum(t[0]))[0]
    stroke = min(colors, key=lambda t: lum(t[0]))[0]
    rest = [t for t in colors if t[0] is not bg and t[0] is not stroke]
    # identity compare fails for equal arrays; rebuild by index instead
    bg_idx = max(range(len(colors)), key=lambda i: lum(colors[i][0]))
    st_idx = min(range(len(colors)), key=lambda i: lum(colors[i][0]))
    rest = [colors[i] for i in range(len(colors)) if i not in (bg_idx, st_idx)]
    ground = min(rest, key=lambda t: lum(t[0]))[0]
    rest = [t for t in rest if t[0] is not ground]
    wall = max(rest, key=lambda t: t[1])[0]
    rest = [t for t in rest if t[0] is not wall]
    roof = max(rest, key=lambda t: sat(t[0]))[0]
    rest = [t for t in rest if t[0] is not roof]
    window = rest[0][0]
    door = 0.5 * ground + 0.5 * wall  # deterministic mix for a distinct door
    return {
        "bg": tuple(int(c) for c in bg),
        "stroke": tuple(int(c) for c in stroke),
        "ground": tuple(int(c) for c in ground),
        "wall": tuple(int(c) for c in wall),
        "roof": tuple(int(c) for c in roof),
        "window": tuple(int(c) for c in window),
        "door": tuple(int(c) for c in door),
        "provenance": ["#%02x%02x%02x" % tuple(int(x) for x in c) for c, _ in pal],
    }


def _jitter_line(pts, rough, seed):
    """return a jittered polyline (SIZE-space coords scaled by SS)."""
    rng = random.Random(seed + 99)
    if not rough:
        return pts
    pts = [(x + rng.gauss(0, 1.6 * SS), y + rng.gauss(0, 1.6 * SS)) for x, y in pts]
    out = []
    for j in range(len(pts) - 1):
        x0, y0 = pts[j]
        x1, y1 = pts[j + 1]
        for f in (0.33, 0.66):
            out.append((x0 + (x1 - x0) * f + rng.gauss(0, 2.2 * SS),
                        y0 + (y1 - y0) * f + rng.gauss(0, 2.2 * SS)))
    return [pts[0]] + out + [pts[-1]]


def draw_house(roles, rough=False, textured=False, seed=7):
    """storybook house scene. fills first (optional grain), strokes layered on top."""
    W = SIZE * SS
    fills = Image.new("RGB", (W, W), roles["bg"])
    d = ImageDraw.Draw(fills)
    S = lambda x: x * SS

    # ground
    d.rectangle([0, S(392), W, W], fill=roles["ground"])
    # house body
    d.rectangle([S(140), S(220), S(330), S(392)], fill=roles["wall"])
    # roof
    d.polygon([(S(120), S(222)), (S(350), S(222)), (S(235), S(130))], fill=roles["roof"])
    # chimney
    d.rectangle([S(290), S(150), S(318), S(210)], fill=roles["roof"])
    # door
    d.rectangle([S(218), S(310), S(252), S(392)], fill=roles["door"])
    # windows
    for wx in (162, 288):
        d.rectangle([S(wx), S(250), S(wx + 44), S(294)], fill=roles["window"])
    # tree
    d.rectangle([S(430), S(320), S(446), S(392)], fill=roles["door"])  # trunk via mix
    canopy = [(S(438), S(196)), (S(398), S(256)), (S(478), S(256))]
    d.polygon(canopy, fill=roles["ground"])
    d.ellipse([S(392), S(196), S(484), S(288)], fill=roles["ground"])
    # path
    d.polygon([(S(226), S(392)), (S(244), S(392)), (S(270), S(470)), (S(200), S(470))],
              fill=roles["door"])

    if textured:
        a = np.asarray(fills, dtype=np.int16)
        rng = np.random.default_rng(seed)
        noise = rng.normal(0, 14, a.shape[:2])
        a = np.clip(a + noise[..., None], 0, 255).astype(np.uint8)
        fills = Image.fromarray(a)

    # stroke layer on top so grain never touches linework
    img = fills.convert("RGB")
    d = ImageDraw.Draw(img)
    sw = 5 * SS
    st = roles["stroke"]

    def line(pts):
        d.line(_jitter_line([(S(x), S(y)) for x, y in pts], rough, seed), fill=st,
               width=sw, joint="curve")

    line([(140, 220), (140, 392), (330, 392), (330, 220)])          # walls
    line([(120, 222), (235, 130), (350, 222)])                       # roof
    line([(290, 150), (290, 210), (318, 210), (318, 150)])           # chimney
    line([(218, 310), (218, 392), (252, 392), (252, 310)])           # door
    line([(0, 392), (512, 392)])                                     # ground
    line([(226, 392), (200, 470), (270, 470), (244, 392)])           # path
    for wx in (162, 288):
        line([(wx, 250), (wx, 294), (wx + 44, 294), (wx + 44, 250), (wx, 250)])  # window
    line([(430, 320), (430, 392), (446, 392), (446, 320)])           # trunk
    # canopy outline: ellipse border via arc chords
    d.arc([S(392), S(196), S(484), S(288)], 0, 360, fill=st, width=sw)

    return img.resize((SIZE, SIZE), Image.LANCZOS)


def main():
    out = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "data", "generated", "arch"))
    os.makedirs(out, exist_ok=True)

    from PIL import Image as I
    rw = I.open(REF_WARM).convert("RGB"); rw.thumbnail((512, 512))
    rc = I.open(REF_COOL).convert("RGB"); rc.thumbnail((512, 512))
    P1 = derive_roles(rw)  # warm riso (ref_01)
    P2 = derive_roles(rc)  # cool ink (ref_02)

    manifest = {"factors": ["palette", "stroke", "texture"],
               "palettes": {"p1": {"provenance": "ref_01.webp", "roles": {k: v for k, v in P1.items() if k != "provenance"}, "measured": P1["provenance"]},
                             "p2": {"provenance": "ref_02.png", "roles": {k: v for k, v in P2.items() if k != "provenance"}, "measured": P2["provenance"]}},
               "images": []}
    cells = [("A", "p1", False, False), ("B", "p2", False, False), ("C", "p1", True, False),
             ("D", "p1", False, True), ("E", "p2", True, False), ("F", "p1", True, True),
             ("G", "p2", False, True), ("H", "p2", True, True)]
    for name, pal, rough, tex in cells:
        roles = P1 if pal == "p1" else P2
        draw_house(roles, rough, tex, seed=7).save(os.path.join(out, name + ".png"))
        manifest["images"].append({"file": name + ".png", "palette": pal,
                                    "stroke": "rough" if rough else "clean",
                                    "texture": "textured" if tex else "flat"})
        print("wrote", name)
    with open(os.path.join(out, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)
    print("wrote manifest.json")


if __name__ == "__main__":
    main()

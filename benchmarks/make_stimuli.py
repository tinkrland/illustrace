"""controlled stimulus generation. exactly one style factor changes per pair.

A = frog, palette P1, clean strokes       (base)
B = frog, palette P2, clean strokes       (palette-only change vs A)
C = frog, palette P1, rough strokes       (stroke-only change vs A)
D = frog, palette P2, rough strokes       (both, for interaction checks)

same subject, same composition, same geometry family. if the analyzer cannot
separate these, nothing downstream matters yet.

v0.1 fix: all coordinates are defined in SIZE-space (512) and scaled by SS inside
the drawing helpers, so the subject actually fills the frame (~40%) instead of a
quarter of it. previously shapes were specified in 512-space but rendered on the
2048 supersample canvas, leaving a tiny frog in a sea of background — which also
starved the palette analyzer of subject colors.
"""
import math
import os
import random
from PIL import Image, ImageDraw

SIZE = 512
SS = 4  # supersampling factor

P1 = {  # fresh greens
    "bg": (246, 240, 224), "body": (124, 182, 92), "belly": (176, 214, 148),
    "eye": (255, 255, 255), "pupil": (35, 40, 45), "stroke": (42, 47, 52),
    "leg": (104, 160, 78),
}
P2 = {  # warm autumn
    "bg": (206, 228, 228), "body": (232, 152, 74), "belly": (246, 206, 150),
    "eye": (255, 252, 240), "pupil": (70, 40, 38), "stroke": (62, 38, 36),
    "leg": (208, 122, 52),
}


def _blob(cx, cy, rx, ry, seed, rough, harmonics=((3, 0.10, 0.0), (5, 0.05, 1.3))):
    """outline points of an organic blob. coords in SIZE-space, scaled by SS."""
    cx, cy, rx, ry = cx * SS, cy * SS, rx * SS, ry * SS
    rng = random.Random(seed)
    pts = []
    n = 240
    for i in range(n):
        t = 2 * math.pi * i / n
        r = 1.0
        for k, amp, ph in harmonics:
            r += amp * math.sin(k * t + ph)
        if rough:
            r += rng.gauss(0, 0.018) + 0.02 * math.sin(17 * t + seed)
        pts.append((cx + rx * r * math.cos(t), cy + ry * r * math.sin(t)))
    return pts


def _line(d, pts, color, width, rough, seed):
    rng = random.Random(seed + 99)
    if rough:
        pts = [(x + rng.gauss(0, 1.6 * SS), y + rng.gauss(0, 1.6 * SS)) for x, y in pts]
        out = []
        for j in range(len(pts) - 1):
            x0, y0 = pts[j]; x1, y1 = pts[j + 1]
            for f in (0.33, 0.66):
                out.append((x0 + (x1 - x0) * f + rng.gauss(0, 2.2 * SS),
                            y0 + (y1 - y0) * f + rng.gauss(0, 2.2 * SS)))
        pts = [pts[0]] + out + [pts[-1]]
    d.line(pts, fill=color, width=width, joint="curve")


def draw_frog(pal, rough=False, seed=7):
    img = Image.new("RGB", (SIZE * SS, SIZE * SS), pal["bg"])
    d = ImageDraw.Draw(img)
    sw = 5 * SS

    body = _blob(256, 300, 150, 118, seed + 1, rough)
    head = _blob(256, 170, 120, 92, seed + 2, rough, harmonics=((3, 0.07, 0.5), (5, 0.04, 2.1)))
    d.polygon(body, fill=pal["body"])
    d.polygon(head, fill=pal["body"])
    belly = _blob(256, 330, 92, 62, seed + 3, rough)
    d.polygon(belly, fill=pal["belly"])
    for sx, seedoff in ((-1, 4), (1, 5)):
        leg = _blob(256 + sx * 165, 340, 52, 34, seed + seedoff, rough)
        d.polygon(leg, fill=pal["leg"])
        foot = _blob(256 + sx * 195, 392, 46, 18, seed + seedoff + 10, rough)
        d.polygon(foot, fill=pal["leg"])
    _line(d, body, pal["stroke"], sw, rough, seed + 1)
    _line(d, head, pal["stroke"], sw, rough, seed + 2)
    _line(d, belly, pal["stroke"], max(2, sw - 2), rough, seed + 3)
    for sx in (-1, 1):
        ex, ey = (256 + sx * 62) * SS, 138 * SS
        r = 34 * SS
        d.ellipse([ex - r, ey - r, ex + r, ey + r],
                  fill=pal["eye"], outline=pal["stroke"], width=max(2, sw - 2))
        pr = 12 * SS
        d.ellipse([ex - pr, ey - pr, ex + pr, ey + pr], fill=pal["pupil"])
    mouth = [(206, 208), (256, 226), (306, 208)]
    mouth = [(x * SS, y * SS) for x, y in mouth]
    _line(d, mouth, pal["stroke"], max(2, sw - 2), rough, seed + 8)
    for sx in (-1, 1):
        nx, ny = (256 + sx * 16) * SS, 168 * SS
        nr = 4 * SS
        d.ellipse([nx - nr, ny - nr, nx + nr, ny + nr], fill=pal["stroke"])
    return img.resize((SIZE, SIZE), Image.LANCZOS)


def main():
    out = os.path.join(os.path.dirname(__file__), "..", "data", "generated")
    os.makedirs(out, exist_ok=True)
    for name, pal, rough in [("A_clean_p1", P1, False), ("B_clean_p2", P2, False),
                             ("C_rough_p1", P1, True), ("D_rough_p2", P2, True)]:
        draw_frog(pal, rough).save(os.path.join(out, name + ".png"))
        print("wrote", name)


if __name__ == "__main__":
    main()

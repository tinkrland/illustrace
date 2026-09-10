"""inspo profiling: define what each inspiration image contributes.

the node-based composer assigns inspo images to style components (palette,
stroke, texture, edges, shading). this module makes each assignment a
*measured contract*, not a vibe: every inspo image gets a component-level
profile, and every component carries (a) the deterministic parameters we
extract for the recipe layer and (b) the probe numbers that say how strong
and how distinctive that inspo is for that component.

usage:
    python3 engine/inspo_profile.py                 # profile all sent refs
    python3 engine/inspo_profile.py --img foo.png    # single image
"""
import argparse
import glob
import json
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from analyzer import (palette, stroke_width_stats, edge_direction_entropy,
                      texture_energy, stroke_axis, shape_proxies,
                      value_range, stroke_mask, _as_array)

REFS = os.path.join(HERE, "..", "data", "test_images")
OUT_DIR = os.path.join(HERE, "..", "data", "generated", "inspo")


def _load(path):
    return Image.open(path).convert("RGB")


def profile_inspo(path):
    """one inspo image -> its component-level contract."""
    img = _load(path)
    a = _as_array(img)
    h, w = a.shape[:2]
    mean_w, cv_w = stroke_width_stats(img)
    axis, conc = stroke_axis(img)
    shp = shape_proxies(img)
    m = stroke_mask(img)
    prof = {
        "file": os.path.basename(path),
        "size": [w, h],
        "components": {
            "palette": {
                "colors_hex": ["#%02x%02x%02x" % c for c, _ in palette(img)],
                "value_range": round(value_range(img), 1),
                # the recipe layer takes: the k hex colors + their weights
                "take": "dominant k palette + value spread",
            },
            "stroke": {
                "width_mean": round(mean_w, 2),
                "width_cv": round(cv_w, 3),
                "axis_deg": None if axis is None else round(float(axis), 1),
                "axis_concentration": round(conc, 3),
                "take": "width profile + wobble (cv) + dominant axis",
            },
            "texture": {
                "energy": round(texture_energy(img), 2),
                "take": "texture_energy target for the grain recipe",
            },
            "edges": {
                "direction_entropy": round(edge_direction_entropy(img), 3),
                "take": "edge entropy + orientation histogram",
            },
            "shape": {
                "perim_area": round(float(shp["perim_area"]), 3),
                "boundary_entropy": round(float(shp["boundary_entropy"]), 3),
                "ink_coverage": round(float(m.mean()), 3),
                "take": "contour density proxies",
            },
        },
    }
    return prof


def _vec(p):
    """comparable component vectors for the redundancy matrix."""
    c = p["components"]
    return np.array([
        c["stroke"]["width_mean"], c["stroke"]["width_cv"],
        c["stroke"]["axis_concentration"],
        c["texture"]["energy"], c["edges"]["direction_entropy"],
        c["shape"]["perim_area"], c["shape"]["ink_coverage"],
        c["palette"]["value_range"] / 255.0,
    ], dtype=float)


def redundancy_matrix(profiles):
    """which inspos are redundant vs complementary per component. this is
    what the node ui surfaces: assigning two inspos with near-identical
    stroke vectors buys nothing; complementary ones actually compose."""
    names = [p["file"] for p in profiles]
    V = np.vstack([_vec(p) for p in profiles])
    V = (V - V.mean(0)) / (V.std(0) + 1e-9)
    sim = V @ V.T / V.shape[1]
    return names, sim


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--img")
    ap.add_argument("--refs", default=REFS)
    args = ap.parse_args()

    paths = [args.img] if args.img else sorted(
        glob.glob(os.path.join(args.refs, "*")))
    paths = [p for p in paths if p.lower().endswith(
        (".png", ".jpg", ".jpeg", ".webp"))]

    profiles = [profile_inspo(p) for p in paths]
    os.makedirs(OUT_DIR, exist_ok=True)

    if len(profiles) > 1:
        names, sim = redundancy_matrix(profiles)
        out = {
            "n": len(profiles),
            "profiles": profiles,
            "redundancy": {
                "files": names,
                "pairwise": [[round(float(x), 2) for x in row] for row in sim],
            },
        }
    else:
        out = {"n": 1, "profiles": profiles}

    out_path = os.path.join(OUT_DIR, "profiles.json")
    with open(out_path, "w") as f:
        json.dump(out, f, indent=1)

    print(f"[inspo] {len(profiles)} profiles -> {out_path}")
    for p in profiles:
        c = p["components"]
        print(f"  {p['file']:14s} pal={c['palette']['colors_hex'][0]}+k  "
              f"stroke_w={c['stroke']['width_mean']:5.2f} cv={c['stroke']['width_cv']:.2f} "
              f"tex={c['texture']['energy']:7.2f} edgeH={c['edges']['direction_entropy']:.2f}")


if __name__ == "__main__":
    main()

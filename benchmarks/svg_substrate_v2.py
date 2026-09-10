"""substrate v2 separability sweep — the four catalog-derived params.

one param swept per row, others held at a fixed baseline (recorded in the
manifest). the point: each new knob must produce a *distinguishable* visual
effect alone — the raw material for the next stylebatch preregistration.

rows:
  width_profile    flat vs symmetric-taper vs mid-bulge ramp
  jitter_lat       perpendicular sigma {1.5, 3.0, 4.5}   (lin pinned 0)
  jitter_lin       along-path sigma {1.5, 3.0, 4.5}      (lat pinned 0)
  opacity_falloff  end alpha {1.0, 0.45, 0.10}
  pass_scatter     whole-pass offset sigma {0, 3, 6}     (2-pass sketchy)
  pass_rotation    max degrees {0, 2, 4}                 (2-pass sketchy)

all outputs + manifest -> data/generated/substrate_v2/
"""
import json
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from benchmarks.svg_house import (BRUSHES, GEO, REF_WARM, SIZE, build_svg,
                                  derive_roles, render)

OUT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "data", "generated", "substrate_v2"))

BASE_PROFILE = dict(BRUSHES["clean"])          # w=5, jitter 0, 1 pass
BASE_SKETCHY = dict(BRUSHES["sketchy"], jitter=1.0)  # 2 passes, mild jitter

ROWS = [
    ("width_profile", [
        ("flat", dict(BASE_PROFILE, width_profile=[(0, 1.0), (1, 1.0)])),
        ("sym taper", dict(BASE_PROFILE, width_profile=[(0, 0.0), (0.3, 1.0), (0.7, 1.0), (1, 0.0)])),
        ("mid bulge", dict(BASE_PROFILE, width_profile=[(0, 0.25), (0.4, 1.0), (1, 0.6)])),
    ]),
    ("jitter_lat", [
        ("1.5", dict(BASE_PROFILE, jitter=0.0, jitter_lat=1.5, jitter_lin=0.0)),
        ("3.0", dict(BASE_PROFILE, jitter=0.0, jitter_lat=3.0, jitter_lin=0.0)),
        ("4.5", dict(BASE_PROFILE, jitter=0.0, jitter_lat=4.5, jitter_lin=0.0)),
    ]),
    ("jitter_lin", [
        ("1.5", dict(BASE_PROFILE, jitter=0.0, jitter_lat=0.0, jitter_lin=1.5)),
        ("3.0", dict(BASE_PROFILE, jitter=0.0, jitter_lat=0.0, jitter_lin=3.0)),
        ("4.5", dict(BASE_PROFILE, jitter=0.0, jitter_lat=0.0, jitter_lin=4.5)),
    ]),
    ("opacity_falloff", [
        ("none", dict(BASE_PROFILE)),
        ("end .45", dict(BASE_PROFILE, opacity_falloff={"start": 1.0, "end": 0.45})),
        ("end .10", dict(BASE_PROFILE, opacity_falloff={"start": 1.0, "end": 0.10})),
    ]),
    ("pass_scatter", [
        ("0", dict(BASE_SKETCHY, pass_scatter=0.0)),
        ("3", dict(BASE_SKETCHY, pass_scatter=3.0)),
        ("6", dict(BASE_SKETCHY, pass_scatter=6.0)),
    ]),
    ("pass_rotation", [
        ("0 deg", dict(BASE_SKETCHY, pass_rotation=0.0)),
        ("2 deg", dict(BASE_SKETCHY, pass_rotation=2.0)),
        ("4 deg", dict(BASE_SKETCHY, pass_rotation=4.0)),
    ]),
]


def main():
    os.makedirs(OUT, exist_ok=True)
    roles = derive_roles(REF_WARM)
    manifest = {"baseline_profile": BASE_PROFILE, "baseline_sketchy": BASE_SKETCHY,
                "rows": [], "seed": 7}
    tiles = {}
    for row_name, levels in ROWS:
        row = []
        for label, brush in levels:
            tag = f"{row_name}_{label.replace(' ', '_').replace('.', '')}"
            svg = build_svg(roles, brush, seed=7)
            with open(os.path.join(OUT, tag + ".svg"), "w") as f:
                f.write(svg)
            png_path = os.path.join(OUT, tag + ".png")
            render(svg, png_path)
            tiles.setdefault(row_name, []).append(png_path)
            row.append({"label": label, "brush": brush, "file": tag + ".png"})
            print("rendered", tag)
        manifest["rows"].append({"param": row_name, "levels": row})
    with open(os.path.join(OUT, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)

    # contact sheet
    tile, pad, label_h = 256, 12, 22
    W = pad + 3 * (tile + pad)
    H = pad + len(ROWS) * (tile + label_h + pad)
    sheet = Image.new("RGB", (W, H), (24, 22, 20))
    dr = ImageDraw.Draw(sheet)
    y = pad
    for row_name, levels in ROWS:
        dr.text((pad + 4, y), row_name, fill=(232, 163, 74))
        y += label_h
        for i, png in enumerate(tiles[row_name]):
            im = Image.open(png).convert("RGB").resize((tile, tile), Image.LANCZOS)
            x = pad + i * (tile + pad)
            sheet.paste(im, (x, y))
            dr.text((x + 4, y + 4), levels[i][0], fill=(240, 232, 213))
        y += tile + pad
    sheet.save(os.path.join(OUT, "contact_sheet.png"))
    print("contact sheet ->", os.path.join(OUT, "contact_sheet.png"))


if __name__ == "__main__":
    main()

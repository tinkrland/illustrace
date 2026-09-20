#!/usr/bin/env python3
"""the diffusion noise floor protocol (v0.1).

problem: every metric in engine/metrics.py + engine/analyzer.py was
calibrated in the vector laboratory: clean synthetic ladders and
vector-derived renders. diffusion models never emit that world. they
soften edges, bleed latents, add sampler grain; a metric that reads
confidently on flux output may be measuring artifacts.

protocol: for every metric, record its no-op jitter distribution: how
much does the reading move between two images that SHOULD be identical
(seed-fixed pairs, same prompt, operator off)? that distribution is the
metric's noise floor. an operator effect smaller than the floor is not
a result, it is silence. this is the instrument-uncertainty half of the
metrology framing in application/bottlenecks/README.md: a stylebench
claim without a noise floor attached is uncalibrated.

modes:
  identical    same image decoded twice (sanity: deltas ~ 0, catches
              non-determinism in the metrics themselves)
  reencode    png -> jpeg q95 -> decode (raster round-trip jitter, the
              cheapest proxy for "a renderer touched this")
  pairs       <stem>_a.* + <stem>_b.* pairs from --dir (the real mode:
              seed-fixed diffusion pairs, operator off vs on, identity
              checks, anything where ground truth says "same")

output: json per mode with per-metric mean/std/p95 abs delta, written to
--out. verdict lines name the floor each operator must clear.

usage:
    python3 engine/noise_floor.py --mode identical --glob 'data/generated/arch/*.png'
    python3 engine/noise_floor.py --mode pairs --dir results/pairs/flux_identity
"""
import argparse
import glob as globmod
import io
import json
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.analyzer import (edge_direction_entropy, palette,
                              stroke_axis, stroke_width_stats,
                              texture_energy, value_range)

METRICS = {
    "stroke_mean": lambda im: stroke_width_stats(im)[0],
    "stroke_cv": lambda im: stroke_width_stats(im)[1],
    "edge_entropy": edge_direction_entropy,
    "texture_energy": texture_energy,
    "value_range": value_range,
    "stroke_axis": lambda im: stroke_axis(im)[0],  # dominant mark angle
}


def read_metric(img, name):
    """guard: a metric that throws on a given image is skipped, not fatal."""
    try:
        return float(METRICS[name](img))
    except Exception:
        return None


def vector(img):
    return {name: read_metric(img, name) for name in METRICS}


def load(path):
    return Image.open(path).convert("RGB")


def pairs_identical(paths):
    for p in paths:
        yield (load(p), load(p), p)


def pairs_reencode(paths, quality=95):
    for p in paths:
        im = load(p)
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=quality)
        buf.seek(0)
        yield (im, Image.open(buf).convert("RGB"), p)


def pairs_dir(d):
    stems = sorted({os.path.splitext(os.path.basename(p))[0][:-2]
                    for p in globmod.glob(os.path.join(d, "*_a.*"))})
    for s in stems:
        a = globmod.glob(os.path.join(d, s + "_a.*"))
        b = globmod.glob(os.path.join(d, s + "_b.*"))
        if a and b:
            yield (load(a[0]), load(b[0]), s)


def floor_report(pairs_iter):
    per_metric = {name: [] for name in METRICS}
    n = 0
    for img_a, img_b, label in pairs_iter:
        n += 1
        va, vb = vector(img_a), vector(img_b)
        for name in METRICS:
            if va[name] is None or vb[name] is None:
                continue
            per_metric[name].append(abs(vb[name] - va[name]))
    report = {"n_pairs": n, "metrics": {}}
    for name, deltas in per_metric.items():
        arr = np.array(deltas) if deltas else np.array([0.0])
        report["metrics"][name] = {
            "mean_abs_delta": round(float(arr.mean()), 6),
            "std_delta": round(float(arr.std()), 6),
            "p95_abs_delta": round(float(np.percentile(arr, 95)), 6),
            "n": len(deltas),
        }
    report["verdict"] = {
        name: "operator effect must exceed p95=%.4f to count as a result"
        % m["p95_abs_delta"]
        for name, m in report["metrics"].items()
    }
    return report


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mode", default="identical",
                    choices=["identical", "reencode", "pairs"])
    ap.add_argument("--glob", default="data/generated/arch/*.png")
    ap.add_argument("--dir", default=None, help="pairs dir for --mode pairs")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    if args.mode == "pairs":
        pairs = pairs_dir(args.dir)
    else:
        paths = sorted(globmod.glob(args.glob))
        pairs = (pairs_identical(paths) if args.mode == "identical"
                 else pairs_reencode(paths))

    report = floor_report(pairs)
    report["mode"] = args.mode
    out = args.out or "results/noise_floor_%s.json" % args.mode
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump(report, f, indent=2)
    print(json.dumps(report["metrics"], indent=2))
    print("wrote", out)


if __name__ == "__main__":
    main()

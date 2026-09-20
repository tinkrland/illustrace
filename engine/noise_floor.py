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


def _luma(arr):
    return arr.astype(np.float64) @ [0.299, 0.587, 0.114]


# --- diffusion-native perturbations (proxies for the mess a diffusion
# pipeline adds between "the model decided the pixels" and "we measured
# them"). each is a ladder: floors are reported per rung so a metric's
# sensitivity curve is visible, not just one number. the real flux pairs
# mode is --mode pairs; these ladders exist because we do not control
# when pairs arrive, and because a metric that dies on a 0.5px warp does
# not deserve to wait for a gpu box to find that out.

def perturb_resample(img, scale):
    """down then up with lanczos: the vae upscale/dequant proxy."""
    w, h = img.size
    small = img.resize((max(8, int(w * scale)), max(8, int(h * scale))),
                       Image.LANCZOS)
    return small.resize((w, h), Image.LANCZOS)


def perturb_warp(img, amp_px, sigma_px=32.0, seed=0):
    """elastic micro-warp: latent misregistration proxy."""
    from scipy import ndimage
    rng = np.random.default_rng(seed)
    a = np.array(img)
    h, w = a.shape[:2]
    dx = ndimage.gaussian_filter(rng.standard_normal((h, w)), sigma_px) * amp_px
    dy = ndimage.gaussian_filter(rng.standard_normal((h, w)), sigma_px) * amp_px
    yy, xx = np.mgrid[0:h, 0:w]
    coords = np.array([yy + dy, xx + dx])
    out = np.zeros_like(a)
    for c in range(3):
        out[..., c] = ndimage.map_coordinates(a[..., c], coords, order=1,
                                              mode="reflect")
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


def perturb_grain(img, amp, sigma_px=2.0, seed=0):
    """band-limited additive noise: sampler grain proxy."""
    from scipy import ndimage
    rng = np.random.default_rng(seed)
    a = np.array(img).astype(np.float64)
    h, w = a.shape[:2]
    n = ndimage.gaussian_filter(rng.standard_normal((h, w)), sigma_px)
    n = n / max(1e-9, n.std()) * amp
    for c in range(3):
        a[..., c] += n
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def perturb_bleed(img, radius_px):
    """local-mean color bleed: latent bleed / denoise-overshoot proxy."""
    from scipy import ndimage
    a = np.array(img).astype(np.float64)
    r = max(1, int(radius_px))
    out = a.copy()
    for c in range(3):
        out[..., c] = ndimage.uniform_filter(a[..., c], size=2 * r + 1)
    return Image.fromarray(np.clip((a + out) / 2, 0, 255).astype(np.uint8))


def perturb_unsharp(img, amount):
    soft = img.filter(__import__("PIL.ImageFilter", fromlist=["x"]).GaussianBlur(1.0))
    a = np.array(img).astype(np.float64)
    s = np.array(soft).astype(np.float64)
    return Image.fromarray(np.clip(a + (a - s) * amount, 0, 255).astype(np.uint8))


def perturb_tint(img, gain_pct, seed=0):
    """channel gain drift: decoder color drift proxy."""
    rng = np.random.default_rng(seed)
    a = np.array(img).astype(np.float64)
    g = 1.0 + rng.uniform(-1, 1, 3) * gain_pct / 100.0
    return Image.fromarray(np.clip(a * g, 0, 255).astype(np.uint8))


def perturb_webp(img, quality):
    import io
    buf = io.BytesIO()
    img.save(buf, "WEBP", quality=quality)
    buf.seek(0)
    return Image.open(buf).convert("RGB")


def perturb_combo(img, seed=0):
    """the diffusion proxy stack: mild bleed + grain + warp + reencode,
    one rung each, the way a real decode path compounds them."""
    return perturb_reencode_paths([img], quality=95, single=True,
                                  seed=seed)[0]


def perturb_reencode_paths(imgs, quality=95, single=False, seed=0):
    out = []
    for im in imgs:
        if single:
            im = perturb_bleed(perturb_grain(perturb_warp(im, 0.5, seed=seed), 0.7, seed=seed), 4)
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=quality)
        buf.seek(0)
        out.append(Image.open(buf).convert("RGB"))
    return out


LADDERS = {
    "resample": ([0.95, 0.90, 0.80], perturb_resample),
    "warp": ([0.25, 0.5, 1.0], perturb_warp),
    "grain": ([0.3, 0.7, 1.5], perturb_grain),
    "bleed": ([3, 6, 12], perturb_bleed),
    "unsharp": ([0.2, 0.4, 0.6], perturb_unsharp),
    "tint": ([1.0, 2.0, 4.0], perturb_tint),
    "webp": ([95, 90, 80], perturb_webp),
}


def pairs_identical(paths):
    for p in paths:
        yield (load(p), load(p), p)


def pairs_reencode(paths, quality=95):
    for p in paths:
        im = load(p)
        yield (im, perturb_reencode_paths([im], quality)[0], p)


def pairs_perturbed(paths, mode, level):
    fn = LADDERS[mode][1]
    for p in paths:
        im = load(p)
        yield (im, fn(im, level), p)


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


def sweep(paths):
    """all perturbation ladders + the combo, one floor report per rung."""
    report = {"n_images": len(paths), "sweep": {}}
    for mode, (levels, _fn) in LADDERS.items():
        report["sweep"][mode] = {}
        for level in levels:
            fr = floor_report(pairs_perturbed(paths, mode, level))
            report["sweep"][mode][str(level)] = fr["metrics"]
    combo_pairs = []
    for p in paths:
        im = load(p)
        combo_pairs.append((im, perturb_combo(im), p))
    report["sweep"]["combo"] = {"-": floor_report(iter(combo_pairs))["metrics"]}
    return report


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mode", default="identical",
                    choices=["identical", "reencode", "pairs", "sweep"]
                            + list(LADDERS))
    ap.add_argument("--glob", default="data/generated/arch/*.png")
    ap.add_argument("--dir", default=None, help="pairs dir for --mode pairs")
    ap.add_argument("--level", type=float, default=None,
                    help="rung for single-ladder modes")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    if args.mode == "pairs":
        pairs = pairs_dir(args.dir)
    else:
        paths = sorted(globmod.glob(args.glob))
        if args.mode == "identical":
            pairs = pairs_identical(paths)
        elif args.mode == "reencode":
            pairs = pairs_reencode(paths)
        elif args.mode == "sweep":
            report = sweep(paths)
            report["mode"] = "sweep"
            out = args.out or "results/noise_floor_sweep.json"
            os.makedirs(os.path.dirname(out), exist_ok=True)
            with open(out, "w") as f:
                json.dump(report, f, indent=2)
            for mode, rungs in report["sweep"].items():
                for level, metrics in rungs.items():
                    floors = {m: v["p95_abs_delta"] for m, v in metrics.items()}
                    print("%s@%s: %s" % (mode, level, floors))
            print("wrote", out)
            return
        else:
            levels, _fn = LADDERS[args.mode]
            level = args.level if args.level is not None else levels[0]
            pairs = pairs_perturbed(paths, args.mode, level)

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

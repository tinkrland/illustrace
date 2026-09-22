#!/usr/bin/env python3
"""deterministic raster-native style scorecard v0.1.

this is deliberately a transparent instrument, not a learned perceptual judge.
see research/RASTER_ASSESSMENT_CONTRACT.md for the contract and limitations.

usage:
    python3 engine/raster_assessment.py spec.json --out scorecard.json
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from pathlib import Path
from typing import Callable

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.analyzer import stroke_axis, stroke_mask, stroke_width_stats

VERSION = "raster-scorecard-v0.1"
FACTORS = ("palette", "value", "color_zones", "shading", "texture",
           "stroke", "edges")


def _rgb(image: Image.Image | str | Path) -> np.ndarray:
    if not isinstance(image, Image.Image):
        image = Image.open(image)
    return np.asarray(image.convert("RGB"), dtype=np.float64) / 255.0


def _pil(a: np.ndarray) -> Image.Image:
    return Image.fromarray(np.clip(a * 255.0, 0, 255).astype(np.uint8), "RGB")


def _resize_rgb(a: np.ndarray, shape: tuple[int, int]) -> np.ndarray:
    h, w = shape
    return _rgb(_pil(a).resize((w, h), Image.Resampling.LANCZOS))


def _srgb_to_lab(rgb: np.ndarray) -> np.ndarray:
    """vectorized d65 cie lab, normalized to L 0..1 and a/b roughly 0..1."""
    x = np.where(rgb <= 0.04045, rgb / 12.92,
                 ((rgb + 0.055) / 1.055) ** 2.4)
    xyz = x @ np.array([[0.4124564, 0.3575761, 0.1804375],
                        [0.2126729, 0.7151522, 0.0721750],
                        [0.0193339, 0.1191920, 0.9503041]]).T
    xyz = xyz / np.array([0.95047, 1.0, 1.08883])
    d = 6.0 / 29.0
    f = np.where(xyz > d ** 3, np.cbrt(xyz),
                 xyz / (3 * d * d) + 4.0 / 29.0)
    L = 116 * f[..., 1] - 16
    aa = 500 * (f[..., 0] - f[..., 1])
    bb = 200 * (f[..., 1] - f[..., 2])
    return np.stack([L / 100.0, (aa + 128.0) / 255.0,
                     (bb + 128.0) / 255.0], axis=-1)


def _luma(rgb: np.ndarray) -> np.ndarray:
    return rgb @ np.array([0.2126, 0.7152, 0.0722])


def _safe_hist(x: np.ndarray, bins: int, lo=0.0, hi=1.0,
               weights=None) -> np.ndarray:
    h = np.histogram(x, bins=bins, range=(lo, hi), weights=weights)[0]
    h = h.astype(np.float64)
    return h / max(float(h.sum()), 1e-12)


def _masked(a: np.ndarray, mask: np.ndarray) -> np.ndarray:
    v = a[mask]
    return v if len(v) else a.reshape(-1, *a.shape[2:])


def _hist_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """histogram intersection, bounded 0..1 even for joined sub-histograms."""
    a = a / max(float(a.sum()), 1e-12)
    b = b / max(float(b.sum()), 1e-12)
    return float(np.minimum(a, b).sum())


def _vector_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """bounded l1 similarity for features normalized into 0..1."""
    if len(a) != len(b) or not len(a):
        return 0.0
    return float(np.clip(1.0 - np.abs(a - b).mean(), 0.0, 1.0))


def _orientation_hist(gx: np.ndarray, gy: np.ndarray, mask: np.ndarray,
                      bins=12) -> np.ndarray:
    mag = np.hypot(gx, gy)
    valid = mask & (mag > np.percentile(mag[mask], 40) if mask.any() else False)
    if valid.sum() < 16:
        return np.zeros(bins)
    ang = np.mod(np.arctan2(gy[valid], gx[valid]), np.pi)
    return _safe_hist(ang, bins, 0, np.pi, weights=mag[valid])


def _gradient(lum: np.ndarray):
    gx = ndimage.sobel(lum, axis=1, mode="reflect") / 8.0
    gy = ndimage.sobel(lum, axis=0, mode="reflect") / 8.0
    return gx, gy, np.hypot(gx, gy)


def _tile_colors(lab: np.ndarray, mask: np.ndarray, grid=4):
    h, w = mask.shape
    spatial = []
    tiles = []
    for iy in range(grid):
        for ix in range(grid):
            y0, y1 = iy * h // grid, (iy + 1) * h // grid
            x0, x1 = ix * w // grid, (ix + 1) * w // grid
            m = mask[y0:y1, x0:x1]
            px = lab[y0:y1, x0:x1][m]
            if len(px) < 4:
                mean = np.array([0.5, 0.5, 0.5])
                coverage = 0.0
            else:
                mean = px.mean(0)
                coverage = float(m.mean())
            spatial.extend([*mean, coverage])
            tiles.append((*mean, coverage))
    tiles.sort(key=lambda v: (v[0], v[1], v[2]))
    return np.asarray(spatial), np.asarray(tiles).reshape(-1)


def heuristic_foreground(rgb: np.ndarray):
    """border-contrast foreground guess; never claims semantic subjecthood."""
    h, w = rgb.shape[:2]
    q = max(2, min(h, w) // 24)
    border = np.concatenate([rgb[:q].reshape(-1, 3), rgb[-q:].reshape(-1, 3),
                             rgb[:, :q].reshape(-1, 3), rgb[:, -q:].reshape(-1, 3)])
    bg = np.median(border, axis=0)
    d = np.linalg.norm(rgb - bg, axis=2)
    border_d = np.linalg.norm(border - bg, axis=1)
    threshold = max(0.08, float(np.percentile(border_d, 80)) + 0.04)
    mask = d > threshold
    mask = ndimage.binary_opening(mask, iterations=1)
    mask = ndimage.binary_closing(mask, iterations=2)
    labels, n = ndimage.label(mask)
    if n:
        sizes = ndimage.sum(mask, labels, range(1, n + 1))
        keep = np.zeros(n + 1, bool)
        floor = max(16, int(h * w * 0.003))
        keep[1:] = sizes >= floor
        mask = keep[labels]
    coverage = float(mask.mean())
    credible = 0.03 <= coverage <= 0.92
    confidence = 0.55 if credible else 0.15
    return (mask if credible else np.ones((h, w), bool)), confidence, coverage


def select_region(rgb: np.ndarray, mode="whole", explicit_mask=None,
                  fallback="heuristic_foreground"):
    h, w = rgb.shape[:2]
    if mode == "whole":
        return np.ones((h, w), bool), {"method": "whole_frame",
            "confidence": 1.0, "coverage": 1.0}
    if explicit_mask is not None:
        m = Image.open(explicit_mask).convert("L").resize(
            (w, h), Image.Resampling.NEAREST)
        subject = np.asarray(m) >= 128
        method, confidence = "explicit_mask", 1.0
        raw_coverage = float(subject.mean())
    elif fallback == "heuristic_foreground":
        subject, confidence, raw_coverage = heuristic_foreground(rgb)
        method = "heuristic_foreground" if confidence > 0.2 else "whole_frame_fallback"
    else:
        subject = np.ones((h, w), bool)
        confidence, raw_coverage, method = 0.25, 1.0, "whole_frame_fallback"
    selected = subject if mode == "subject" else ~subject
    if selected.mean() < 0.01:
        selected = np.ones((h, w), bool)
        confidence = min(confidence, 0.15)
        method = "whole_frame_fallback"
    return selected, {"method": method, "confidence": confidence,
                      "coverage": float(selected.mean()),
                      "subject_coverage": raw_coverage}


def palette_features(rgb, mask):
    lab = _srgb_to_lab(rgb)
    px = _masked(lab, mask)
    # three marginal perceptual histograms are more stable than a sparse cube.
    hist = np.concatenate([_safe_hist(px[:, i], 16) for i in range(3)])
    moments = np.concatenate([px.mean(0), np.clip(px.std(0) * 2, 0, 1)])
    return {"lab_histogram": (hist, "hist"), "lab_moments": (moments, "vector")}, 1.0


def value_features(rgb, mask):
    y = _luma(rgb)
    px = y[mask]
    hist = _safe_hist(px, 32)
    qs = np.quantile(px, [0.05, 0.25, 0.5, 0.75, 0.95])
    spread = np.array([qs[-1] - qs[0], px.std() * 2]).clip(0, 1)
    return {"luminance_histogram": (hist, "hist"),
            "luminance_quantiles": (qs, "vector"),
            "contrast": (spread, "vector")}, min(1.0, len(px) / 256)


def color_zone_features(rgb, mask):
    lab = _srgb_to_lab(rgb)
    spatial, sorted_tiles = _tile_colors(lab, mask, 4)
    coverage = float(mask.mean())
    return {"spatial_pyramid": (spatial, "vector"),
            "sorted_tile_colors": (sorted_tiles, "vector")}, min(1.0, coverage * 8)


def shading_features(rgb, mask):
    y = _luma(rgb)
    sigma = max(1.0, min(y.shape) * 0.025)
    low = ndimage.gaussian_filter(y, sigma=sigma)
    gx, gy, mag = _gradient(low)
    m = mag[mask]
    hist = _safe_hist(np.clip(m * 8, 0, 1), 16)
    orient = _orientation_hist(gx, gy, mask)
    tonal = np.array([np.quantile(low[mask], q) for q in (0.1, 0.5, 0.9)] +
                     [float((m < 0.006).mean()), float(np.clip(m.mean() * 20, 0, 1))])
    obs = float(np.clip(m.std() * 20 + 0.25, 0.2, 1.0))
    return {"low_frequency_gradient": (hist, "hist"),
            "gradient_orientation": (orient, "hist"),
            "tonal_coverage": (tonal, "vector")}, obs


def texture_features(rgb, mask):
    y = _luma(rgb)
    bands, residual_hist = [], []
    for sigma in (1.0, 2.0, 4.0, 8.0):
        hp = y - ndimage.gaussian_filter(y, sigma=sigma)
        v = np.abs(hp[mask])
        bands.extend([float(np.clip(v.mean() * 10, 0, 1)),
                      float(np.clip(v.std() * 10, 0, 1))])
        residual_hist.extend(_safe_hist(np.clip(v * 8, 0, 1), 8))
    obs = float(np.clip(np.std(y[mask]) * 4 + 0.15, 0.15, 1.0))
    return {"multiscale_energy": (np.asarray(bands), "vector"),
            "residual_distribution": (np.asarray(residual_hist), "hist")}, obs


def stroke_features(rgb, mask):
    im = _pil(rgb)
    sm = stroke_mask(im) & mask
    coverage = float(sm.sum() / max(mask.sum(), 1))
    mean_w, cv = stroke_width_stats(_pil(rgb * mask[..., None] + (1 - mask[..., None])))
    axis, conc = stroke_axis(_pil(rgb * mask[..., None] + (1 - mask[..., None])))
    diag = math.hypot(*rgb.shape[:2])
    axis = 0.0 if axis is None else axis / 180.0
    vec = np.array([np.clip(coverage * 8, 0, 1),
                    np.clip(mean_w / max(diag * 0.03, 1), 0, 1),
                    np.clip(cv, 0, 1), axis, np.clip(conc, 0, 1)])
    obs = float(np.clip(coverage * 25, 0, 1))
    return {"linework": (vec, "vector")}, obs


def edge_features(rgb, mask):
    y = _luma(rgb)
    gx, gy, mag = _gradient(y)
    vals = mag[mask]
    scale = max(float(np.quantile(vals, 0.95)), 1e-6)
    mh = _safe_hist(np.clip(vals / scale, 0, 1), 16)
    density = np.array([(vals > t).mean() for t in (0.01, 0.03, 0.06, 0.12)])
    orient = _orientation_hist(gx, gy, mask)
    obs = float(np.clip((vals > 0.02).mean() * 12, 0, 1))
    return {"magnitude_distribution": (mh, "hist"),
            "multiscale_density": (density, "vector"),
            "orientation": (orient, "hist")}, obs


EXTRACTORS: dict[str, Callable] = {
    "palette": palette_features,
    "value": value_features,
    "color_zones": color_zone_features,
    "shading": shading_features,
    "texture": texture_features,
    "stroke": stroke_features,
    "edges": edge_features,
}


def _compare_features(candidate, reference):
    scores = {}
    for name, (a, kind) in candidate.items():
        b, bkind = reference[name]
        scores[name] = (_hist_similarity(a, b) if kind == "hist"
                        else _vector_similarity(a, b))
    return scores


def _confidence_label(v):
    return "high" if v >= 0.75 else "medium" if v >= 0.45 else "low"


def quality_observations(rgb, mask):
    y = _luma(rgb)
    vals = y[mask]
    _, _, mag = _gradient(y)
    clipping = float(((rgb <= 1 / 255) | (rgb >= 254 / 255)).any(2)[mask].mean())
    edge_density = float((mag[mask] > 0.03).mean())
    dynamic_range = float(np.quantile(vals, .95) - np.quantile(vals, .05))
    flags = []
    if clipping > 0.2:
        flags.append("high_channel_clipping")
    if dynamic_range < 0.08:
        flags.append("low_dynamic_range")
    if edge_density < 0.005:
        flags.append("very_low_edge_evidence")
    return {"channel_clipping_fraction": clipping, "edge_density": edge_density,
            "luminance_p95_p05": dynamic_range, "flags": flags,
            "status": "uncalibrated_observation"}


def assess(candidate_path, references, region_mode="whole", subject_mask=None,
           mask_fallback="heuristic_foreground", reference_aggregation="mean"):
    rgb = _rgb(candidate_path)
    mask, mask_info = select_region(rgb, region_mode, subject_mask, mask_fallback)
    factors = {}
    for factor in FACTORS:
        paths = references.get(factor, [])
        if not paths:
            continue
        cfeat, cobs = EXTRACTORS[factor](rgb, mask)
        per_reference = []
        channel_runs = []
        ref_observability = []
        for path in paths:
            rr = _rgb(path)
            # references use the same region mode only when dimensions align and
            # an explicit candidate mask was supplied; otherwise whole-frame.
            rm = np.ones(rr.shape[:2], bool)
            rfeat, robs = EXTRACTORS[factor](rr, rm)
            channel_scores = _compare_features(cfeat, rfeat)
            channel_runs.append(channel_scores)
            per_reference.append(float(np.mean(list(channel_scores.values()))))
            ref_observability.append(robs)
        if reference_aggregation == "best":
            chosen = int(np.argmax(per_reference))
            channel_scores = channel_runs[chosen]
            similarity = per_reference[chosen]
        else:
            channel_scores = {name: float(np.mean([r[name] for r in channel_runs]))
                              for name in cfeat}
            similarity = float(np.mean(per_reference))
        channel_std = float(np.std(list(channel_scores.values())))
        reference_std = float(np.std(per_reference))
        observability = float(min(cobs, np.mean(ref_observability)))
        confidence = float(np.clip(observability * mask_info["confidence"] *
                                   (1 - .5 * channel_std) *
                                   (1 - .5 * reference_std), 0, 1))
        reasons = []
        if observability < 0.2:
            reasons.append("factor_not_observable")
        if mask_info["confidence"] < 0.25:
            reasons.append("region_not_reliably_identified")
        if channel_std > 0.3:
            reasons.append("measurement_channels_disagree")
        factors[factor] = {
            "similarity": round(similarity, 6),
            "status": "provisional_uncalibrated",
            "channels": {k: round(v, 6) for k, v in channel_scores.items()},
            "per_reference": [round(v, 6) for v in per_reference],
            "observability": round(observability, 6),
            "confidence": round(confidence, 6),
            "confidence_label": _confidence_label(confidence),
            "abstain": bool(reasons),
            "reason_codes": reasons,
        }
    return {
        "instrument": VERSION,
        "candidate": str(candidate_path),
        "region": {"mode": region_mode, **mask_info},
        "factors": factors,
        "quality": quality_observations(rgb, mask),
        "limitations": [
            "scores are deterministic but not yet calibrated against human judgment",
            "heuristic foreground is not semantic subject identification",
            "v0.1 has no dense correspondence or learned content-leakage detector",
            "cross-factor scores are not commensurate and must not be averaged",
        ],
    }


def _resolve(base: Path, path):
    p = Path(path)
    return str(p if p.is_absolute() else (base / p).resolve())


def load_spec(path):
    spec_path = Path(path).resolve()
    spec = json.loads(spec_path.read_text())
    base = spec_path.parent
    out = dict(spec)
    out["candidate"] = _resolve(base, spec["candidate"])
    if spec.get("source"):
        out["source"] = _resolve(base, spec["source"])
    if spec.get("subject_mask"):
        out["subject_mask"] = _resolve(base, spec["subject_mask"])
    out["references"] = {factor: [_resolve(base, p) for p in paths]
                         for factor, paths in spec["references"].items()}
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("spec")
    ap.add_argument("--out", help="write json here instead of stdout")
    args = ap.parse_args()
    spec = load_spec(args.spec)
    card = assess(spec["candidate"], spec["references"],
                  region_mode=spec.get("region_mode", "whole"),
                  subject_mask=spec.get("subject_mask"),
                  mask_fallback=spec.get("mask_fallback", "heuristic_foreground"),
                  reference_aggregation=spec.get("reference_aggregation", "mean"))
    text = json.dumps(card, indent=2)
    if args.out:
        Path(args.out).write_text(text + "\n")
    else:
        print(text)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""robust-instrument tests (v0.3 metrology): band-passed texture,
palette-anchored value range, concentration-aware axis, relative floors."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from PIL import Image
from engine.analyzer import texture_energy_bp, value_range_pal
from engine.noise_floor import perturb_grain, perturb_bleed, floor_report

A = Image.open("data/generated/A_clean_p1.png")
C = Image.open("data/generated/C_rough_p1.png")


class TestTextureBandpass:
    def test_finite_and_positive(self):
        for im in (A, C):
            v = texture_energy_bp(im)
            assert v == v and v >= 0  # no nan

    def test_grain_moves_it(self):
        # grain adds high-frequency energy: the band-pass must see it
        assert texture_energy_bp(perturb_grain(A, 1.5)) > texture_energy_bp(A)


class TestValuePalette:
    def test_range_and_finiteness(self):
        v = value_range_pal(A)
        assert 0 <= v <= 255 and v == v

    def test_stable_under_grain(self):
        # small-mass intermediate clusters must not move the palette spread
        assert abs(value_range_pal(perturb_grain(A, 0.7)) - value_range_pal(A)) < 5.0

    def test_bleed_robust_against_raw(self):
        # the whole point: bleed invents intermediate colors; the palette
        # variant must move less than the raw percentile version
        b = perturb_bleed(A, 2)
        raw = abs(__import__("engine.analyzer", fromlist=["value_range"]).value_range(b)
                  - __import__("engine.analyzer", fromlist=["value_range"]).value_range(A))
        pal = abs(value_range_pal(b) - value_range_pal(A))
        assert pal <= raw + 1.0  # never worse than raw, at minimum


class TestRelativeFloors:
    def test_identical_pairs_zero_floor(self):
        rep = floor_report([(A, A, "identical")])
        for name, m in rep["metrics"].items():
            assert m["p95_abs_delta"] == 0.0
            assert m["p95_rel_delta"] == 0.0

    def test_relative_present(self):
        rep = floor_report([(A, perturb_grain(A, 1.5), "grain")])
        tex = rep["metrics"]["texture_energy"]
        assert tex["p95_rel_delta"] is not None
        assert 0 < tex["p95_rel_delta"] < 1.0

    def test_concentration_tracked(self):
        rep = floor_report([(A, A, "identical")])
        assert "stroke_conc" in rep["metrics"]

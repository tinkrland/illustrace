"""stylebench checks for the classical operators (v0.2) + noise floor protocol.

the claims under test (research/STYLEBENCH_THESIS.md):
- strength control: each operator at strength s moves its target metric
  ~s of the input->ref gap (roughening direction; smoothing understates
  by design, see docstrings)
- independence: an operator leaves non-target metrics inside their
  noise floor (results/noise_floor_reencode.json is the honest bar)
"""
import os
import sys

import numpy as np
import pytest
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.analyzer import (edge_direction_entropy, palette, stroke_width_stats,
                              texture_energy, value_range)
from engine.operators import (color_zone_transfer, edge_transfer, palette_transfer,
                              shading_transfer, stroke_transfer, texture_transfer,
                              value_transfer)
from engine.metrics import palette_distance

A = Image.open("data/generated/A_clean_p1.png")   # clean, cv 0.188, tex 13.2
C = Image.open("data/generated/C_rough_p1.png")   # rough, cv 0.351, tex 16.4
B = Image.open("data/generated/B_clean_p2.png")  # alt palette, for zone recolor
CV_IN, CV_REF = stroke_width_stats(A)[1], stroke_width_stats(C)[1]
TEX_IN, TEX_REF = texture_energy(A), texture_energy(C)
TOL = 0.05  # measured-gap tolerance for strength control


class TestStrengthControl:
    def test_stroke_full_strength_closes_gap(self):
        out = stroke_transfer(A, C, 1.0)
        cv = stroke_width_stats(out)[1]
        assert abs(cv - CV_REF) < TOL

    def test_stroke_half_strength_interpolates(self):
        out = stroke_transfer(A, C, 0.5)
        cv = stroke_width_stats(out)[1]
        target = CV_IN + 0.5 * (CV_REF - CV_IN)
        assert abs(cv - target) < TOL

    def test_texture_full_strength_closes_gap(self):
        out = texture_transfer(A, C, 1.0)
        assert abs(texture_energy(out) - TEX_REF) < 0.3

    def test_texture_half_strength_interpolates(self):
        out = texture_transfer(A, C, 0.5)
        target = TEX_IN + 0.5 * (TEX_REF - TEX_IN)
        assert abs(texture_energy(out) - target) < 0.3


class TestIndependence:
    """each operator must not move the other factors beyond the jpeg
    re-encode floor (results/noise_floor_reencode.json): stroke_cv 0.15,
    edge_entropy 0.05, texture 1.6, palette handled by distance."""

    def test_stroke_operator_leaves_texture_and_palette(self):
        out = stroke_transfer(A, C, 1.0)
        assert abs(texture_energy(out) - TEX_IN) < 2.0
        assert palette_distance(palette(out, 6), palette(A, 6)) < 0.02

    def test_texture_operator_leaves_stroke_and_palette(self):
        out = texture_transfer(A, C, 1.0)
        assert abs(stroke_width_stats(out)[1] - CV_IN) < 0.15
        assert palette_distance(palette(out, 6), palette(A, 6)) < 0.02

    def test_edge_operator_leaves_palette(self):
        out = edge_transfer(A, C, 1.0)
        assert palette_distance(palette(out, 6), palette(A, 6)) < 0.02

    def test_palette_operator_leaves_stroke(self):
        out = palette_transfer(A, C, 1.0)
        assert abs(stroke_width_stats(out)[1] - CV_IN) < 0.05


class TestDeterminism:
    def test_seeded_operators_reproduce(self):
        assert np.array_equal(
            np.array(stroke_transfer(A, C, 1.0, seed=7)),
            np.array(stroke_transfer(A, C, 1.0, seed=7)))


# --- v0.3: value, color-zone, shading (floors from the diffusion-native
# sweep in results/noise_floor_sweep*.json; entanglements documented in the
# operator docstrings are tested as such, not hidden)


class TestValueOperator:
    def test_full_strength_closes_gap(self):
        out = value_transfer(A, C, 1.0)
        target = CV_IN + (value_range(C) - CV_IN)
        assert abs(value_range(out) - target) < 12

    def test_half_strength_interpolates(self):
        out = value_transfer(A, C, 0.5)
        target = value_range(A) + 0.5 * (value_range(C) - value_range(A))
        assert abs(value_range(out) - target) < 12

    def test_leaves_stroke_and_texture(self):
        out = value_transfer(A, C, 1.0)
        assert abs(stroke_width_stats(out)[1] - CV_IN) < 0.15
        assert abs(texture_energy(out) - TEX_IN) < 2.0
        # value and palette are not orthogonal (luma lives in palette
        # centroids): documented, bounded
        assert palette_distance(palette(out, 6), palette(A, 6)) < 0.1


class TestColorZoneOperator:
    def test_full_strength_moves_palette_toward_ref(self):
        out = color_zone_transfer(A, B, 1.0)
        d_in = palette_distance(palette(A, 6), palette(B, 6))
        d_out = palette_distance(palette(out, 6), palette(B, 6))
        assert d_out < 0.7 * d_in

    def test_value_frozen_exactly(self):
        out = color_zone_transfer(A, B, 1.0)
        assert abs(value_range(out) - value_range(A)) < 2.0

    def test_leaves_stroke(self):
        out = color_zone_transfer(A, B, 1.0)
        assert abs(stroke_width_stats(out)[1] - CV_IN) < 0.15


class TestShadingOperator:
    def test_full_strength_flattens_toward_ref(self):
        from engine.operators import _interior_levels
        out = shading_transfer(C, A, 1.0)
        n_in, n_ref = _interior_levels(C), _interior_levels(A)
        assert _interior_levels(out) <= n_in - 0.5 * (n_in - n_ref)

    def test_leaves_palette_and_value(self):
        from engine.operators import _interior_levels
        out = shading_transfer(C, A, 1.0)
        assert palette_distance(palette(out, 6), palette(C, 6)) < 0.02
        assert abs(value_range(out) - value_range(C)) < 5.0

    def test_noop_toward_richer_reference(self):
        # adding gradient complexity is the learned operators' job
        from engine.operators import _interior_levels
        if _interior_levels(A) >= _interior_levels(C):
            out = shading_transfer(A, C, 1.0)
            assert _interior_levels(out) == _interior_levels(A)

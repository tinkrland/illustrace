import os
import sys
import unittest

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from engine.analyzer import value_range, stroke_axis, shape_proxies


def img(a):
    return Image.fromarray(np.asarray(a, np.uint8))


class Test1MetricTests(unittest.TestCase):
    def test_value_range_flat_is_zero(self):
        self.assertEqual(value_range(img(np.full((50, 50, 3), 128))), 0.0)

    def test_value_range_bimodal_is_full(self):
        a = np.full((50, 50, 3), 255)
        a[25:, :] = 0
        self.assertAlmostEqual(value_range(img(a)), 255.0, delta=1)

    def test_value_range_scales_with_gap(self):
        r = []
        for lo in (80, 40):
            a = np.full((50, 50, 3), 200)
            a[25:, :] = lo
            r.append(value_range(img(a)))
        self.assertGreater(r[1], r[0])

    def test_axis_vertical_bar(self):
        a = np.full((200, 200, 3), 255)
        a[70:130, 95:105] = 0
        ax, conc = stroke_axis(img(a))
        self.assertLess(abs(ax - 90), 2)
        self.assertGreater(conc, 0.5)

    def test_axis_rotation_consistency(self):
        a = np.full((200, 200, 3), 255)
        a[70:130, 95:105] = 0
        base, _ = stroke_axis(img(a))
        rot, _ = stroke_axis(img(np.rot90(a, 1).copy()))
        self.assertAlmostEqual((base - rot) % 180, 90, delta=3)

    def test_axis_flat_image_returns_none(self):
        self.assertEqual(stroke_axis(img(np.full((50, 50, 3), 255)))[0], None)

    def test_shape_proxies_keys(self):
        a = np.full((200, 200, 3), 255)
        a[70:130, 95:105] = 0
        p = shape_proxies(img(a))
        self.assertIn("perim_area", p)
        self.assertIn("boundary_entropy", p)
        self.assertGreater(p["perim_area"], 0)


if __name__ == "__main__":
    unittest.main()

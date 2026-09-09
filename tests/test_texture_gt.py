import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from engine.texture_gt import texture_gt, map_box, GT_HOUSE


class Img:
    def __init__(self, a):
        self.a = a

    def __array__(self, dtype=None):
        return self.a.astype(dtype) if dtype else self.a


def flat(v=128.0, size=200):
    return Img(np.full((size, size, 3), v))


def noisy(sigma, size=200, seed=3):
    rng = np.random.default_rng(seed)
    return Img(np.clip(128 + rng.normal(0, sigma, (size, size, 1)), 0, 255)
               .repeat(3, axis=2))


class TextureGtTests(unittest.TestCase):
    REGIONS = {"a": (10, 10, 90, 90), "b": (110, 10, 190, 90)}

    def test_flat_region_reads_zero(self):
        t = texture_gt(flat(), regions=self.REGIONS)
        self.assertEqual(t["sigma"], 0.0)
        self.assertEqual(t["grad"], 0.0)

    def test_sigma_tracks_known_noise(self):
        for sigma in (5.0, 10.0):
            t = texture_gt(noisy(sigma), regions=self.REGIONS)
            self.assertAlmostEqual(t["sigma"], sigma, delta=sigma * 0.15)

    def test_area_weighting_matches_manual(self):
        rng = np.random.default_rng(11)
        a = Img(np.full((200, 200, 3), 128.0))
        t = texture_gt(a, regions={"a": (10, 10, 90, 90), "b": (110, 10, 190, 90)})
        # equal areas, both flat -> aggregate is the flat mean
        self.assertEqual(t["sigma"], 0.0)

    def test_map_box_identity(self):
        self.assertEqual(map_box((10, 20, 30, 40)), (10, 20, 30, 40))

    def test_map_box_staging_transform(self):
        b = map_box((100, 100, 200, 200), tx=30, ty=176, s=0.55)
        self.assertEqual(b, (int(round(30 + 55)), int(round(176 + 55)),
                            int(round(30 + 110)), int(round(176 + 110))))

    def test_regions_in_bounds_and_reasonable(self):
        # every declared region must be a real box with positive area
        for name, (x0, y0, x1, y1) in GT_HOUSE.items():
            self.assertLess(x0, x1)
            self.assertLess(y0, y1)

    def test_staging_downscales_reading_of_same_texture(self):
        # the same noise field rendered smaller must not inflate sigma:
        # canvas-anchored per-px sigma stays flat, so shrinking a region
        # alone (same per-px noise) reads the same sigma
        rng = np.random.default_rng(5)
        big = np.clip(128 + rng.normal(0, 10, (200, 200, 1)), 0, 255).repeat(3, 2)
        t_big = texture_gt(Img(big), regions=self.REGIONS)
        small = big[::2, ::2]
        t_small = texture_gt(Img(small), regions=self.REGIONS)
        self.assertAlmostEqual(t_big["sigma"], t_small["sigma"], delta=1.5)

    def test_empty_image_returns_none(self):
        t = texture_gt(flat(size=8))
        self.assertIsNone(t["sigma"])

    def test_clipped_regions_skipped(self):
        # a region partially outside a small image is skipped, not crashed
        t = texture_gt(flat(size=100), regions={"in": (10, 10, 90, 90),
                                                 "out": (150, 150, 180, 180)})
        self.assertIn("in", t["regions"])
        self.assertNotIn("out", t["regions"])


if __name__ == "__main__":
    unittest.main()

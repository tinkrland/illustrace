import json
import os
import sys
import tempfile
import unittest

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from engine.raster_assessment import assess, heuristic_foreground, load_spec


def save(path, a):
    Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB").save(path)


def illustrated_scene(size=160):
    a = np.full((size, size, 3), [238, 229, 207], dtype=np.uint8)
    a[38:132, 38:122] = [92, 151, 176]
    a[74:132, 38:122] = [194, 96, 69]
    a[35:39, 35:125] = 25
    a[130:134, 35:125] = 25
    a[35:134, 35:39] = 25
    a[35:134, 121:125] = 25
    for x in range(45, 118, 12):
        a[45:65, x:x + 3] = 30
    return a


class RasterAssessmentTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = self.tmp.name
        self.scene = illustrated_scene()
        self.ref = os.path.join(self.base, "ref.png")
        save(self.ref, self.scene)

    def tearDown(self):
        self.tmp.cleanup()

    def test_identity_scores_near_one_for_every_factor(self):
        refs = {f: [self.ref] for f in
                ("palette", "value", "color_zones", "shading", "texture",
                 "stroke", "edges")}
        card = assess(self.ref, refs)
        self.assertEqual(card["instrument"], "raster-scorecard-v0.1")
        for factor, result in card["factors"].items():
            self.assertGreater(result["similarity"], .995, factor)
            self.assertEqual(result["status"], "provisional_uncalibrated")
        self.assertNotIn("overall_score", card)

    def test_palette_shift_hits_palette_more_than_edges(self):
        shifted = self.scene.astype(float)
        shifted[..., 0] = np.clip(shifted[..., 0] * .55, 0, 255)
        shifted[..., 2] = np.clip(shifted[..., 2] * 1.35, 0, 255)
        path = os.path.join(self.base, "shifted.png")
        save(path, shifted)
        card = assess(path, {"palette": [self.ref], "edges": [self.ref]})
        self.assertLess(card["factors"]["palette"]["similarity"],
                        card["factors"]["edges"]["similarity"])

    def test_grain_changes_texture_similarity(self):
        rng = np.random.default_rng(4)
        grain = np.clip(self.scene.astype(float) +
                        rng.normal(0, 22, self.scene.shape[:2])[..., None], 0, 255)
        path = os.path.join(self.base, "grain.png")
        save(path, grain)
        identity = assess(self.ref, {"texture": [self.ref]})
        changed = assess(path, {"texture": [self.ref]})
        self.assertLess(changed["factors"]["texture"]["similarity"],
                        identity["factors"]["texture"]["similarity"] - .03)

    def test_explicit_subject_mask_isolates_background_change(self):
        changed = self.scene.copy()
        outside = np.ones(changed.shape[:2], bool)
        outside[35:134, 35:125] = False
        changed[outside] = [20, 220, 80]
        path = os.path.join(self.base, "background_changed.png")
        save(path, changed)
        mask = np.zeros(changed.shape[:2], np.uint8)
        mask[35:134, 35:125] = 255
        mask_path = os.path.join(self.base, "mask.png")
        Image.fromarray(mask, "L").save(mask_path)
        refs = {"palette": [self.ref]}
        whole = assess(path, refs)
        subject = assess(path, refs, region_mode="subject", subject_mask=mask_path)
        self.assertEqual(subject["region"]["method"], "explicit_mask")
        self.assertGreater(subject["factors"]["palette"]["similarity"],
                           whole["factors"]["palette"]["similarity"])

    def test_heuristic_mask_never_claims_semantics(self):
        mask, confidence, coverage = heuristic_foreground(self.scene / 255.0)
        self.assertEqual(mask.shape, self.scene.shape[:2])
        self.assertGreater(coverage, .03)
        self.assertLessEqual(confidence, .55)
        card = assess(self.ref, {"palette": [self.ref]}, region_mode="subject")
        self.assertIn(card["region"]["method"],
                      ("heuristic_foreground", "whole_frame_fallback"))

    def test_spec_paths_resolve_relative_to_spec(self):
        spec_path = os.path.join(self.base, "spec.json")
        with open(spec_path, "w") as f:
            json.dump({"candidate": "ref.png",
                       "references": {"palette": ["ref.png"]}}, f)
        spec = load_spec(spec_path)
        self.assertEqual(spec["candidate"], self.ref)
        self.assertEqual(spec["references"]["palette"][0], self.ref)


if __name__ == "__main__":
    unittest.main()

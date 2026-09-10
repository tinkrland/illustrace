"""tests for survey/build_spec.py — the intent-to-spec generator's validator
and filename decoder. no network access (the glm-5.2 pass is not tested here)."""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "survey"))

from survey.build_spec import decode_params, validate  # noqa: E402


def make_spec(**overrides):
    spec = {
        "batch": "batch_test",
        "version": 2,
        "date_preregistered": "2026-09-10",
        "goal": "test",
        "scientist_session": "test",
        "judges_target": 5,
        "session_shape": {
            "total_questions": 4,
            "blocks": {"anchor": 1, "width_jnd": 1, "catches": 2},
            "catch_positions_display_order": [2, 4],
        },
        "images_new": [],
        "questions": [
            {
                "id": "bta",
                "kind": "anchor",
                "dimension": "line_weight",
                "prompt": "which linework feels thicker?",
                "left": "fid2_width3.png",
                "right": "fid2_width9.png",
                "gt": "right",
                "scored": False,
                "note": "warm-up",
            },
            {
                "id": "btw1",
                "kind": "pair",
                "dimension": "line_weight",
                "prompt": "which linework feels thicker?",
                "left": "fid2_width3.png",
                "right": "fid2_width5.png",
                "gt": "right",
                "scored": True,
                "note": "jnd probe",
            },
        ],
        "catches": [
            {"id": "btc1", "image": "fid2_width5.png", "position": 2},
            {"id": "btc2", "image": "fid2_width5.png", "position": 4},
        ],
    }
    spec.update(overrides)
    return spec


class TestDecodeParams(unittest.TestCase):
    def test_all_stimulus_families_decode(self):
        cases = {
            "jit_1p25.png": ("roughness", 1.25),
            "grain_11.png": ("texture", 11.0),
            "fid2_taper15.png": ("taper", 0.15),
            "fid2_width7.png": ("line_weight", 7),
            "fid2_light50.png": ("lighting", 50),
            "fid2_pal25.png": ("palette_shift", 25),
            "fid2_pass2.png": ("passes", 2),
        }
        for fname, (dim, val) in cases.items():
            p = decode_params(fname)
            self.assertEqual(p["dimension"], dim, fname)
            self.assertIn(list(p.values())[-1], (val, val + 0.0), fname)

    def test_anchor_files_decode_as_other(self):
        self.assertEqual(decode_params("anchor_solo_grain.png")["dimension"],
                         "anchor/other")


class TestValidate(unittest.TestCase):
    def test_valid_spec_passes(self):
        self.assertEqual(validate(make_spec()), [])

    def test_missing_top_level_key(self):
        spec = make_spec()
        del spec["goal"]
        self.assertTrue(any("goal" in e for e in validate(spec)))

    def test_question_budget_mismatch(self):
        spec = make_spec()
        spec["session_shape"]["total_questions"] = 9
        self.assertTrue(any("total_questions" in e for e in validate(spec)))

    def test_catch_position_order_mismatch(self):
        spec = make_spec()
        spec["session_shape"]["catch_positions_display_order"] = [4, 2]
        self.assertTrue(any("catch positions" in e for e in validate(spec)))

    def test_duplicate_catch_position(self):
        spec = make_spec()
        spec["catches"][1]["position"] = 2
        spec["session_shape"]["catch_positions_display_order"] = [2, 2]
        self.assertTrue(any("duplicate catch positions" in e
                             for e in validate(spec)))

    def test_unknown_stimulus_fails(self):
        spec = make_spec()
        spec["questions"][1]["right"] = "does_not_exist.png"
        self.assertTrue(any("not on disk" in e for e in validate(spec)))

    def test_declared_image_new_rescues_unknown_stimulus(self):
        spec = make_spec()
        spec["questions"][1]["right"] = "made_up"
        spec["images_new"] = [{"file": "made_up", "recipe": "x", "params": {}}]
        errs = validate(spec)
        self.assertFalse(any("not on disk" in e for e in errs))

    def test_anchor_must_not_be_scored(self):
        spec = make_spec()
        spec["questions"][0]["scored"] = True
        self.assertTrue(any("anchor must not be scored" in e
                             for e in validate(spec)))

    def test_identical_pair_should_be_catch(self):
        spec = make_spec()
        spec["questions"][1]["right"] = "fid2_width3.png"
        self.assertTrue(any("use a catch" in e for e in validate(spec)))

    def test_invalid_gt(self):
        spec = make_spec()
        spec["questions"][1]["gt"] = "both"
        self.assertTrue(any("gt must be left|right" in e for e in validate(spec)))

    def test_too_few_catches(self):
        spec = make_spec()
        spec["catches"] = spec["catches"][:1]
        spec["session_shape"]["total_questions"] = 3
        spec["session_shape"]["catch_positions_display_order"] = [2]
        self.assertTrue(any("at least 2 catches" in e for e in validate(spec)))

    def test_draft_batch_3_validates(self):
        """the generated draft must stay valid if it is checked in."""
        path = os.path.join(os.path.dirname(__file__), "..", "survey",
                            "specs", "drafts", "batch_3.json")
        if not os.path.exists(path):
            self.skipTest("draft not present")
        self.assertEqual(validate(json.load(open(path))), [])


if __name__ == "__main__":
    unittest.main()

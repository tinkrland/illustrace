"""tests for xano.schema — validate() on all six tables."""
import unittest

from xano.schema import validate


class TestProjectsSchema(unittest.TestCase):

    def test_valid_project(self):
        record = {
            "id": 1,
            "name": "stylebench",
            "description": "benchmark for style transfer measurability",
            "created_at": "2026-09-08T12:00:00Z",
        }
        self.assertEqual(validate("projects", record), [])

    def test_missing_name(self):
        record = {
            "id": 1,
            "description": "no name",
            "created_at": "2026-09-08T12:00:00Z",
        }
        errors = validate("projects", record)
        self.assertTrue(any("name" in e for e in errors))

    def test_empty_name(self):
        record = {
            "id": 1,
            "name": "   ",
            "description": "blank name",
            "created_at": "2026-09-08T12:00:00Z",
        }
        errors = validate("projects", record)
        self.assertTrue(any("name" in e for e in errors))

    def test_wrong_id_type(self):
        record = {
            "id": "abc",
            "name": "x",
            "description": "bad id",
            "created_at": "2026-09-08T12:00:00Z",
        }
        errors = validate("projects", record)
        self.assertTrue(any("id" in e for e in errors))


class TestAssetsSchema(unittest.TestCase):

    def test_valid_asset(self):
        record = {
            "id": 10,
            "project_id": 1,
            "kind": "illustration",
            "name": "frog_clean",
            "file_url": "https://example.com/frog_clean.png",
            "style_profile": {"stroke_width_cv": 0.316, "palette_hex": ["#f6f0e0"]},
        }
        self.assertEqual(validate("assets", record), [])

    def test_missing_file_url(self):
        record = {
            "id": 10,
            "project_id": 1,
            "kind": "illustration",
            "name": "frog_clean",
            "style_profile": {},
        }
        errors = validate("assets", record)
        self.assertTrue(any("file_url" in e for e in errors))

    def test_style_profile_wrong_type(self):
        record = {
            "id": 10,
            "project_id": 1,
            "kind": "illustration",
            "name": "frog_clean",
            "file_url": "https://example.com/frog_clean.png",
            "style_profile": "not a dict",
        }
        errors = validate("assets", record)
        self.assertTrue(any("style_profile" in e for e in errors))


class TestTransferRequestsSchema(unittest.TestCase):

    def test_valid_transfer_request(self):
        record = {
            "id": 5,
            "project_id": 1,
            "asset_id": 10,
            "components": {"stroke": 1.0, "palette": 0.0},
            "strengths": {"stroke": 0.8},
            "status": "pending",
            "created_at": "2026-09-08T12:00:00Z",
        }
        self.assertEqual(validate("transfer_requests", record), [])

    def test_components_can_be_list(self):
        record = {
            "id": 5,
            "project_id": 1,
            "asset_id": 10,
            "components": ["stroke", "palette"],
            "strengths": [0.8, 0.0],
            "status": "done",
            "created_at": "2026-09-08T12:00:00Z",
        }
        self.assertEqual(validate("transfer_requests", record), [])

    def test_missing_status(self):
        record = {
            "id": 5,
            "project_id": 1,
            "asset_id": 10,
            "components": {},
            "strengths": {},
            "created_at": "2026-09-08T12:00:00Z",
        }
        errors = validate("transfer_requests", record)
        self.assertTrue(any("status" in e for e in errors))

    def test_components_wrong_type(self):
        record = {
            "id": 5,
            "project_id": 1,
            "asset_id": 10,
            "components": "stroke",
            "strengths": {},
            "status": "pending",
            "created_at": "2026-09-08T12:00:00Z",
        }
        errors = validate("transfer_requests", record)
        self.assertTrue(any("components" in e for e in errors))


class TestExperimentsSchema(unittest.TestCase):

    def test_valid_experiment(self):
        record = {
            "id": 3,
            "project_id": 1,
            "name": "measurability_v0",
            "description": "can the analyzer distinguish single-factor changes?",
            "hypothesis": "palette distance will be nonzero only on palette-changed pairs",
            "created_at": "2026-09-08T12:00:00Z",
        }
        self.assertEqual(validate("experiments", record), [])

    def test_empty_hypothesis(self):
        record = {
            "id": 3,
            "project_id": 1,
            "name": "measurability_v0",
            "description": "something",
            "hypothesis": "",
            "created_at": "2026-09-08T12:00:00Z",
        }
        errors = validate("experiments", record)
        self.assertTrue(any("hypothesis" in e for e in errors))

    def test_missing_project_id(self):
        record = {
            "id": 3,
            "name": "x",
            "description": "y",
            "hypothesis": "z",
            "created_at": "2026-09-08T12:00:00Z",
        }
        errors = validate("experiments", record)
        self.assertTrue(any("project_id" in e for e in errors))


class TestRunsSchema(unittest.TestCase):

    def test_valid_run(self):
        record = {
            "id": 0,
            "experiment_id": 3,
            "subject": "controlled frog pairs",
            "requested": "measurability_v0",
            "params": {"model": "deterministic"},
            "metrics": {"palette_distance": 0.095, "stroke_width_cv": 0.316},
            "verdict": "pass",
            "artifacts": {"images": ["A.png", "B.png"]},
            "created_at": "20260908_122319_e1",
        }
        self.assertEqual(validate("runs", record), [])

    def test_missing_verdict(self):
        record = {
            "id": 0,
            "experiment_id": 3,
            "subject": "frogs",
            "requested": "measurability_v0",
            "params": {},
            "metrics": {},
            "artifacts": {},
            "created_at": "2026-09-08T12:00:00Z",
        }
        errors = validate("runs", record)
        self.assertTrue(any("verdict" in e for e in errors))

    def test_metrics_must_be_dict(self):
        record = {
            "id": 0,
            "experiment_id": 3,
            "subject": "frogs",
            "requested": "measurability_v0",
            "params": {},
            "metrics": [0.1, 0.2],
            "verdict": "pass",
            "artifacts": {},
            "created_at": "2026-09-08T12:00:00Z",
        }
        errors = validate("runs", record)
        self.assertTrue(any("metrics" in e for e in errors))

    def test_empty_verdict(self):
        record = {
            "id": 0,
            "experiment_id": 3,
            "subject": "frogs",
            "requested": "x",
            "params": {},
            "metrics": {},
            "verdict": "  ",
            "artifacts": {},
            "created_at": "2026-09-08T12:00:00Z",
        }
        errors = validate("runs", record)
        self.assertTrue(any("verdict" in e for e in errors))


class TestHumanJudgmentsSchema(unittest.TestCase):

    def test_valid_judgment(self):
        record = {
            "id": 7,
            "run_id": 42,
            "judge_id": "judge_001",
            "dimension": "stroke_roughness",
            "score": 7.5,
            "notes": "clearly rougher linework on sample C",
            "created_at": "2026-09-08T14:00:00Z",
        }
        self.assertEqual(validate("human_judgments", record), [])

    def test_score_out_of_range(self):
        record = {
            "id": 7,
            "run_id": 42,
            "judge_id": "judge_001",
            "dimension": "stroke_roughness",
            "score": 11.0,
            "notes": "oops",
            "created_at": "2026-09-08T14:00:00Z",
        }
        errors = validate("human_judgments", record)
        self.assertTrue(any("score" in e for e in errors))

    def test_negative_score_invalid(self):
        record = {
            "id": 7,
            "run_id": 42,
            "judge_id": "judge_001",
            "dimension": "palette",
            "score": -1.0,
            "notes": "",
            "created_at": "2026-09-08T14:00:00Z",
        }
        errors = validate("human_judgments", record)
        self.assertTrue(any("score" in e for e in errors))

    def test_missing_judge_id(self):
        record = {
            "id": 7,
            "run_id": 42,
            "dimension": "palette",
            "score": 5.0,
            "notes": "",
            "created_at": "2026-09-08T14:00:00Z",
        }
        errors = validate("human_judgments", record)
        self.assertTrue(any("judge_id" in e for e in errors))


class TestUnknownTable(unittest.TestCase):

    def test_unknown_table_returns_error(self):
        errors = validate("nonexistent_table", {"id": 1})
        self.assertTrue(len(errors) == 1)
        self.assertIn("unknown table", errors[0])


if __name__ == "__main__":
    unittest.main()

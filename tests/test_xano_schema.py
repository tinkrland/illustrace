"""tests for xano/schema.py — validate() against the actual live control-plane
tables (reconciled 2026-09-19; the previous version of this suite tested a
speculative schema — projects/transfer_requests/human_judgments — that was
superseded by training_jobs/node_graphs/presets and never actually built)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from xano.schema import validate


class TestStylebenchRunsSchema(unittest.TestCase):
    def _valid(self):
        return {
            "id": 1, "experiment": "measurability_v0", "subject": "house",
            "requested": "stroke_width", "params": {"width": 3},
            "metrics": {"delta": 0.1}, "verdict": "pass", "artifacts": {},
        }

    def test_valid_run(self):
        self.assertEqual(validate("stylebench_runs", self._valid()), [])

    def test_missing_verdict(self):
        r = self._valid()
        del r["verdict"]
        errors = validate("stylebench_runs", r)
        self.assertTrue(any("verdict" in e for e in errors))

    def test_empty_verdict(self):
        r = self._valid()
        r["verdict"] = "  "
        errors = validate("stylebench_runs", r)
        self.assertTrue(any("verdict" in e and "empty" in e for e in errors))

    def test_metrics_must_be_dict(self):
        r = self._valid()
        r["metrics"] = "not a dict"
        errors = validate("stylebench_runs", r)
        self.assertTrue(any("metrics" in e for e in errors))

    def test_artifacts_accepts_list(self):
        r = self._valid()
        r["artifacts"] = ["a.png", "b.png"]
        self.assertEqual(validate("stylebench_runs", r), [])


class TestStylebenchAssetsSchema(unittest.TestCase):
    def _valid(self):
        return {
            "id": 1, "kind": "reference", "name": "monet_01",
            "file_url": "https://example.com/monet_01.png",
            "style_profile": {"palette": ["#112233"]},
        }

    def test_valid_asset(self):
        self.assertEqual(validate("stylebench_assets", self._valid()), [])

    def test_missing_file_url(self):
        r = self._valid()
        del r["file_url"]
        errors = validate("stylebench_assets", r)
        self.assertTrue(any("file_url" in e for e in errors))

    def test_style_profile_wrong_type(self):
        r = self._valid()
        r["style_profile"] = "not a dict"
        errors = validate("stylebench_assets", r)
        self.assertTrue(any("style_profile" in e for e in errors))


class TestStylebenchExperimentsSchema(unittest.TestCase):
    def _valid(self):
        return {
            "id": 1, "name": "measurability_v0",
            "hypothesis": "stroke width is measurable and controllable",
            "pass_criteria": {"min_agreement": 0.7},
        }

    def test_valid_experiment(self):
        self.assertEqual(validate("stylebench_experiments", self._valid()), [])

    def test_missing_hypothesis(self):
        r = self._valid()
        del r["hypothesis"]
        errors = validate("stylebench_experiments", r)
        self.assertTrue(any("hypothesis" in e for e in errors))

    def test_empty_name(self):
        r = self._valid()
        r["name"] = ""
        errors = validate("stylebench_experiments", r)
        self.assertTrue(any("name" in e and "empty" in e for e in errors))


class TestJudgmentsSchema(unittest.TestCase):
    def _valid(self):
        return {
            "id": 1, "dimension": "roughness", "stimulus_a_id": "a.png",
            "stimulus_b_id": "b.png", "chosen": "a.png",
            "session_id": "anonymous_123", "question_id": "q01",
        }

    def test_valid_judgment(self):
        self.assertEqual(validate("judgments", self._valid()), [])

    def test_missing_session_id(self):
        r = self._valid()
        del r["session_id"]
        errors = validate("judgments", r)
        self.assertTrue(any("session_id" in e for e in errors))

    def test_empty_chosen(self):
        r = self._valid()
        r["chosen"] = ""
        errors = validate("judgments", r)
        self.assertTrue(any("chosen" in e and "empty" in e for e in errors))

    def test_is_catch_pair_wrong_type(self):
        r = self._valid()
        r["is_catch_pair"] = "yes"
        errors = validate("judgments", r)
        self.assertTrue(any("is_catch_pair" in e for e in errors))

    def test_optional_fields_can_be_absent(self):
        # judge_id, confidence, reaction_ms etc are all optional in the live
        # table — a minimal valid record must not need them
        self.assertEqual(validate("judgments", self._valid()), [])


class TestTrainingJobsSchema(unittest.TestCase):
    def _valid(self):
        return {
            "id": 1, "job_type": "fitter", "status": "queued",
            "target_factor": "jitter_lat", "hardware": "mi300x",
            "dataset_ref": "substrate_v2_sweep",
        }

    def test_valid_job(self):
        self.assertEqual(validate("training_jobs", self._valid()), [])

    def test_missing_target_factor(self):
        r = self._valid()
        del r["target_factor"]
        errors = validate("training_jobs", r)
        self.assertTrue(any("target_factor" in e for e in errors))

    def test_bad_job_type_enum(self):
        r = self._valid()
        r["job_type"] = "not_a_real_type"
        errors = validate("training_jobs", r)
        self.assertTrue(any("job_type" in e for e in errors))

    def test_bad_status_enum(self):
        r = self._valid()
        r["status"] = "queued_up_wrong"
        errors = validate("training_jobs", r)
        self.assertTrue(any("status" in e for e in errors))

    def test_all_valid_status_transitions_accepted(self):
        for status in ("queued", "running", "done", "failed"):
            r = self._valid()
            r["status"] = status
            self.assertEqual(validate("training_jobs", r), [])

    def test_gpu_hours_accepts_float(self):
        r = self._valid()
        r["gpu_hours"] = 0.2
        self.assertEqual(validate("training_jobs", r), [])


class TestDatasetsSchema(unittest.TestCase):
    def _valid(self):
        return {
            "id": 1, "name": "substrate_v2_sweep", "source": "generated",
            "manifest": {"images": 14}, "image_count": 14,
        }

    def test_valid_dataset(self):
        self.assertEqual(validate("datasets", self._valid()), [])

    def test_missing_image_count(self):
        r = self._valid()
        del r["image_count"]
        errors = validate("datasets", r)
        self.assertTrue(any("image_count" in e for e in errors))


class TestNodeGraphsSchema(unittest.TestCase):
    def _valid(self):
        return {
            "id": 1, "graph": {"nodes": [], "edges": []},
            "graph_version": 1, "status": "draft",
        }

    def test_valid_graph(self):
        self.assertEqual(validate("node_graphs", self._valid()), [])

    def test_bad_status_enum(self):
        r = self._valid()
        r["status"] = "not_a_status"
        errors = validate("node_graphs", r)
        self.assertTrue(any("status" in e for e in errors))

    def test_graph_accepts_list_or_dict(self):
        r = self._valid()
        r["graph"] = [{"id": "n1"}]
        self.assertEqual(validate("node_graphs", r), [])


class TestPresetsSchema(unittest.TestCase):
    def _valid(self):
        return {
            "id": 1, "recipe": {"components": ["stroke"], "strengths": [0.8]},
            "recipe_version": 1, "graph_id": 7,
        }

    def test_valid_preset(self):
        self.assertEqual(validate("presets", self._valid()), [])

    def test_missing_graph_id(self):
        r = self._valid()
        del r["graph_id"]
        errors = validate("presets", r)
        self.assertTrue(any("graph_id" in e for e in errors))

    def test_recipe_wrong_type(self):
        r = self._valid()
        r["recipe"] = "not a dict"
        errors = validate("presets", r)
        self.assertTrue(any("recipe" in e for e in errors))


class TestUnknownTable(unittest.TestCase):
    def test_unknown_table_name(self):
        errors = validate("not_a_real_table", {"id": 1})
        self.assertEqual(len(errors), 1)
        self.assertIn("unknown table", errors[0])

    def test_known_tables_list_matches_live_schema(self):
        # guards against silent drift between schema.py and the actual
        # provisioned tables documented in research/AMD_DEVELOPER_CLOUD.md
        # and xano/PROVISIONING.md
        from xano.schema import _KNOWN_TABLES
        expected = {
            "stylebench_runs", "stylebench_assets", "stylebench_experiments",
            "judgments", "training_jobs", "datasets", "node_graphs", "presets",
        }
        self.assertEqual(_KNOWN_TABLES, expected)


if __name__ == "__main__":
    unittest.main()

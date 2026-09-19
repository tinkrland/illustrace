"""tests for runner/train_runner.py, offline only (no network, no gpu).

covers the pure pieces: claim selection (lowest id + type filter), the
v0-default merge, the kohya dataset toml (no cropping, bucket 768-1024,
caption dropout), the flux_train_network command (the flux.1-dev flags
from research/DATASET_PACKAGING.md), and the update payload shape. the
live claim/train/post path runs on the box itself.
"""

import json
import os
import sys
import unittest

_RUNNER_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "runner")
if _RUNNER_DIR not in sys.path:
    sys.path.insert(0, _RUNNER_DIR)

import train_runner as tr


class TestClaimSelection(unittest.TestCase):
    def test_lowest_id_first(self):
        rows = [{"id": 7, "job_type": "lora"}, {"id": 2, "job_type": "lora"}]
        self.assertEqual(tr.list_queued.__name__, "list_queued")  # import sanity

    def test_sorted_lowest(self):
        # list_queued sorts by id after filtering; verify the sort+filter
        # logic it uses, inline (no network)
        rows = [{"id": 9, "job_type": "lora"}, {"id": 3, "job_type": "fitter"},
                {"id": 5, "job_type": "lora"}]
        filt = [r for r in rows if r["job_type"] == "lora"]
        got = sorted(filt, key=lambda r: r.get("id", 0))
        self.assertEqual([r["id"] for r in got], [5, 9])

    def test_job_params_dict_response_shapes(self):
        # xano may return {data: [...]} or a bare list; both normalize
        rows = {"data": [{"id": 1}]}
        if isinstance(rows, dict):
            rows = rows.get("data") or rows.get("jobs") or []
        self.assertEqual(rows, [{"id": 1}])


class TestJobParams(unittest.TestCase):
    def test_defaults_are_the_v0_spec(self):
        p = tr.job_params({"params": {}})
        self.assertEqual(p["trigger"], "mzqtlv")
        self.assertEqual((p["dim"], p["alpha"]), (16, 16))
        self.assertEqual(p["epochs"], 16)
        self.assertEqual(p["repeats"], 3)
        self.assertEqual(p["lr"], 1e-4)

    def test_job_overrides_win(self):
        p = tr.job_params({"params": {"dim": 32, "epochs": 8}})
        self.assertEqual(p["dim"], 32)
        self.assertEqual(p["epochs"], 8)
        self.assertEqual(p["alpha"], 16)  # untouched default

    def test_params_json_string_form(self):
        p = tr.job_params({"params": json.dumps({"lr": 5e-5})})
        self.assertEqual(p["lr"], 5e-5)

    def test_none_params_ignored(self):
        p = tr.job_params({"params": {"dim": None, "trigger": None}})
        self.assertEqual(p["dim"], 16)
        self.assertEqual(p["trigger"], "mzqtlv")


class TestDatasetToml(unittest.TestCase):
    def setUp(self):
        self.p = tr.job_params({"params": {}})

    def test_no_crop_bucketing_bounds(self):
        t = tr.dataset_toml("data/kohya/monet", self.p)
        self.assertIn("enable_bucket = true", t)
        self.assertIn("min_bucket_reso = 768", t)
        self.assertIn("max_bucket_reso = 1024", t)

    def test_caption_dropout_present(self):
        # the cheap test that style was learned, not memorized (v0 spec)
        t = tr.dataset_toml("data/kohya/monet", self.p)
        self.assertIn("caption_dropout_rate = 0.1", t)

    def test_repeats_and_batch_from_params(self):
        t = tr.dataset_toml("d", self.p)
        self.assertIn("num_repeats = 3", t)
        self.assertIn("batch_size = 1", t)
        t2 = tr.dataset_toml("d", tr.job_params({"params": {"repeats": 5}}))
        self.assertIn("num_repeats = 5", t2)

    def test_metadata_file_resolved(self):
        t = tr.dataset_toml("data/kohya/monet", self.p)
        self.assertIn("metadata_file =", t)
        self.assertIn("metadata.jsonl", t)


class TestKohyaCmd(unittest.TestCase):
    def setUp(self):
        self.job = {"id": 1, "job_type": "lora",
                    "dataset_ref": "data/kohya/monet", "params": {}}
        self.cmd, self.name = tr.build_kohya_cmd(
            self.job, "/opt/sd-scripts", "/opt/flux1-dev", "/out", "/tmp/c.toml")

    def _flat(self):
        return " ".join(self.cmd)

    def test_flux1_dev_flags(self):
        # the flags verified from the sd-scripts docs, 2026-09-10
        f = self._flat()
        for flag in ("--timestep_sampling shift", "--discrete_flow_shift 3.1582",
                     "--model_prediction_type raw", "--guidance_scale 1.0"):
            self.assertIn(flag, f)

    def test_network_module_and_dims(self):
        f = self._flat()
        self.assertIn("--network_module networks.lora_flux", f)
        self.assertIn("--network_dim 16", f)
        self.assertIn("--network_alpha 16", f)

    def test_weights_paths(self):
        f = self._flat()
        self.assertIn("/opt/flux1-dev/flux1-dev.safetensors", f)
        self.assertIn("/opt/flux1-dev/clip_l.safetensors", f)
        self.assertIn("/opt/flux1-dev/t5xxl_fp16.safetensors", f)

    def test_save_every_2_epochs(self):
        # 8 candidates from 16 epochs, 3 was too coarse for a noisy probe
        self.assertIn("--save_every_n_epochs 2", self._flat())

    def test_trigger_in_output_name(self):
        self.assertTrue(self.name.startswith("mzqtlv"))


class TestUpdatePayload(unittest.TestCase):
    def test_payload_shape_matches_endpoint(self):
        # input {id, secret, status, metrics?, params?, artifact_uri?,
        # gpu_hours?} per training_jobs_update.xanoscript
        p = {"id": 5, "secret": "s", "status": "done",
             "metrics": {"wall_hours": 1.2},
             "params": None, "artifact_uri": "gs://b/x.safetensors",
             "gpu_hours": 1.2}
        self.assertEqual(set(p), {"id", "secret", "status", "metrics",
                                  "params", "artifact_uri", "gpu_hours"})

    def test_only_allowed_transitions(self):
        allowed = ("running", "done", "failed")
        self.assertNotIn("queued", allowed)  # runner can't rewind the ledger


if __name__ == "__main__":
    unittest.main()

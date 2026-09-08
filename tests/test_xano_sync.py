"""tests for xano.sync — validate + post harness, no network required.

post_run is monkeypatched so no real xano calls are made.
"""
import json
import os
import sys
import tempfile
import unittest

# make sure the repo root is importable even when tests/ is the cwd
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from xano.sync import sync_runs


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _write_run(directory, filename, data):
    path = os.path.join(directory, filename)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh)
    return path


# a run record that passes schema validation after _coerce_run()
_VALID_RAW = {
    "run_id": "20260908_122319_e1",
    "experiment": "measurability_v0",
    "subject": "controlled frog pairs",
    "metrics": {
        "palette_distance": 0.095,
        "stroke_width_cv": 0.316,
    },
    "verdict": "pass",
    "profiles": {"A": {"stroke_width_cv": 0.316}},
}

# a run record that will fail validation (empty verdict)
_INVALID_RAW = {
    "run_id": "bad_run",
    "experiment": "measurability_v0",
    "subject": "frogs",
    "metrics": {},
    "verdict": "",   # empty — schema rejects this
    "profiles": {},
}


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------

class TestSyncValidRecords(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.calls = []

    def _fake_post(self, record):
        self.calls.append(record)
        return {"id": len(self.calls)}

    def test_valid_record_is_synced(self):
        _write_run(self.tmpdir, "run_valid.json", _VALID_RAW)
        summary = sync_runs(runs_dir=self.tmpdir, post_fn=self._fake_post)

        self.assertEqual(summary["found"], 1)
        self.assertEqual(summary["valid"], 1)
        self.assertEqual(summary["invalid"], 0)
        self.assertEqual(summary["synced"], 1)
        self.assertEqual(summary["skipped_reasons"], [])
        self.assertEqual(len(self.calls), 1)

    def test_post_fn_receives_coerced_record(self):
        """the record passed to post_fn must contain required schema keys."""
        _write_run(self.tmpdir, "run_valid.json", _VALID_RAW)
        sync_runs(runs_dir=self.tmpdir, post_fn=self._fake_post)

        posted = self.calls[0]
        for key in ("subject", "requested", "params", "metrics", "verdict", "artifacts"):
            self.assertIn(key, posted, "missing key: %s" % key)

    def test_multiple_valid_records_all_synced(self):
        for i in range(3):
            data = dict(_VALID_RAW)
            data["run_id"] = "run_%d" % i
            _write_run(self.tmpdir, "run_%d.json" % i, data)

        summary = sync_runs(runs_dir=self.tmpdir, post_fn=self._fake_post)

        self.assertEqual(summary["found"], 3)
        self.assertEqual(summary["synced"], 3)
        self.assertEqual(summary["invalid"], 0)


class TestSyncInvalidRecords(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.calls = []

    def _fake_post(self, record):
        self.calls.append(record)
        return {"id": len(self.calls)}

    def test_invalid_record_is_skipped(self):
        _write_run(self.tmpdir, "run_bad.json", _INVALID_RAW)
        summary = sync_runs(runs_dir=self.tmpdir, post_fn=self._fake_post)

        self.assertEqual(summary["found"], 1)
        self.assertEqual(summary["invalid"], 1)
        self.assertEqual(summary["synced"], 0)
        self.assertEqual(len(self.calls), 0)

    def test_invalid_record_has_reason(self):
        _write_run(self.tmpdir, "run_bad.json", _INVALID_RAW)
        summary = sync_runs(runs_dir=self.tmpdir, post_fn=self._fake_post)

        self.assertEqual(len(summary["skipped_reasons"]), 1)
        fname, reason = summary["skipped_reasons"][0]
        self.assertEqual(fname, "run_bad.json")
        self.assertIsInstance(reason, str)
        self.assertGreater(len(reason), 0)

    def test_reason_mentions_failing_field(self):
        _write_run(self.tmpdir, "run_bad.json", _INVALID_RAW)
        summary = sync_runs(runs_dir=self.tmpdir, post_fn=self._fake_post)

        _, reason = summary["skipped_reasons"][0]
        # verdict is empty, schema should flag it
        self.assertIn("verdict", reason)

    def test_mixed_valid_and_invalid(self):
        _write_run(self.tmpdir, "run_good.json", _VALID_RAW)
        _write_run(self.tmpdir, "run_bad.json", _INVALID_RAW)

        summary = sync_runs(runs_dir=self.tmpdir, post_fn=self._fake_post)

        self.assertEqual(summary["found"], 2)
        self.assertEqual(summary["valid"], 1)
        self.assertEqual(summary["invalid"], 1)
        self.assertEqual(summary["synced"], 1)
        self.assertEqual(len(self.calls), 1)


class TestSyncDryRun(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.calls = []

    def _fake_post(self, record):
        self.calls.append(record)
        return {"id": len(self.calls)}

    def test_dry_run_does_not_call_post(self):
        _write_run(self.tmpdir, "run_valid.json", _VALID_RAW)
        summary = sync_runs(runs_dir=self.tmpdir, dry_run=True, post_fn=self._fake_post)

        self.assertEqual(len(self.calls), 0)
        self.assertEqual(summary["synced"], 0)

    def test_dry_run_still_validates(self):
        _write_run(self.tmpdir, "run_valid.json", _VALID_RAW)
        _write_run(self.tmpdir, "run_bad.json", _INVALID_RAW)

        summary = sync_runs(runs_dir=self.tmpdir, dry_run=True, post_fn=self._fake_post)

        self.assertEqual(summary["found"], 2)
        self.assertEqual(summary["valid"], 1)
        self.assertEqual(summary["invalid"], 1)
        self.assertEqual(summary["synced"], 0)

    def test_dry_run_skipped_reasons_still_populated(self):
        _write_run(self.tmpdir, "run_bad.json", _INVALID_RAW)
        summary = sync_runs(runs_dir=self.tmpdir, dry_run=True, post_fn=self._fake_post)

        self.assertEqual(len(summary["skipped_reasons"]), 1)


class TestSyncBrokenJson(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.calls = []

    def _fake_post(self, record):
        self.calls.append(record)
        return {"id": 1}

    def test_broken_json_is_skipped_with_reason(self):
        path = os.path.join(self.tmpdir, "broken.json")
        with open(path, "w") as fh:
            fh.write("{not valid json")

        summary = sync_runs(runs_dir=self.tmpdir, post_fn=self._fake_post)

        self.assertEqual(summary["invalid"], 1)
        self.assertEqual(summary["synced"], 0)
        fname, reason = summary["skipped_reasons"][0]
        self.assertIn("json", reason.lower())


class TestSyncPostFailure(unittest.TestCase):
    """if post_fn returns None, the record is counted but logged in skipped_reasons."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def test_failed_post_recorded(self):
        _write_run(self.tmpdir, "run_valid.json", _VALID_RAW)

        summary = sync_runs(
            runs_dir=self.tmpdir,
            post_fn=lambda r: None,
        )

        self.assertEqual(summary["synced"], 0)
        self.assertEqual(len(summary["skipped_reasons"]), 1)
        _, reason = summary["skipped_reasons"][0]
        self.assertIn("None", reason)


class TestSyncEmptyDirectory(unittest.TestCase):

    def test_empty_dir_returns_zero_found(self):
        with tempfile.TemporaryDirectory() as d:
            summary = sync_runs(runs_dir=d, post_fn=lambda r: {"id": 1})
        self.assertEqual(summary["found"], 0)
        self.assertEqual(summary["synced"], 0)


if __name__ == "__main__":
    unittest.main()

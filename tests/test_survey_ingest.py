"""tests/test_survey_ingest.py — unit tests for survey/ingest.py.

runs with plain unittest (no network, no external deps).
uses in-memory fixture data; never touches the filesystem for results input.
"""

import json
import os
import sys
import tempfile
import unittest

# ensure repo root is on path so 'from survey.ingest import ...' and
# 'from xano.schema import ...' both work.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

# import the module under test
from survey.ingest import (
    normalize_answer,
    validate_record,
    build_summary,
    run_id_for,
    ingest,
    _build_gt_map,
    _djb2,
)


# ---------------------------------------------------------------------------
# fixture helpers
# ---------------------------------------------------------------------------

STIMULI = {
    "version": 1,
    "questions": [
        {
            "id": "q01",
            "dimension": "roughness",
            "prompt": "which linework feels rougher?",
            "left": "../data/generated/arch_svg/jit_0p00.png",
            "right": "../data/generated/arch_svg/jit_1p25.png",
            "gt": "right",
        },
        {
            "id": "q02",
            "dimension": "roughness",
            "prompt": "which linework feels rougher?",
            "left": "../data/generated/arch_svg/jit_1p25.png",
            "right": "../data/generated/arch_svg/jit_2p50.png",
            "gt": "right",
        },
        {
            # catch pair — identical images, gt=null
            "id": "q04",
            "dimension": "roughness",
            "prompt": "which linework feels rougher?",
            "left": "../data/generated/arch_svg/jit_2p50.png",
            "right": "../data/generated/arch_svg/jit_2p50.png",
            "gt": None,
            "note": "catch pair (identical images)",
        },
        {
            "id": "q08",
            "dimension": "line_weight",
            "prompt": "which line feels heavier?",
            "left": "../data/generated/arch_svg/fid2_width3.png",
            "right": "../data/generated/arch_svg/fid2_width9.png",
            "gt": "right",
        },
    ],
}

GT_MAP = _build_gt_map(STIMULI)

INGESTED_AT = "2024-01-01T00:00:00Z"
JUDGE_ID = "test_judge"


def _make_answer(qid, choice_file, confidence="pretty sure"):
    """minimal valid answer dict as the survey would produce."""
    return {
        "question_id": qid,
        "dimension": GT_MAP[qid]["dimension"],
        "prompt": "some prompt",
        "left_file": "jit_0p00.png",
        "right_file": "jit_1p25.png",
        "choice": choice_file,
        "confidence": confidence,
        "elapsed_ms": 2500,
    }


def _make_results(answers, judge_id=JUDGE_ID):
    return {
        "judge_id": judge_id,
        "started_at": "2024-01-01T00:00:00Z",
        "completed_at": "2024-01-01T00:05:00Z",
        "answers": answers,
    }


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------

class TestDjb2(unittest.TestCase):
    def test_deterministic(self):
        self.assertEqual(_djb2("q01"), _djb2("q01"))

    def test_different_inputs_differ(self):
        self.assertNotEqual(_djb2("q01"), _djb2("q02"))

    def test_returns_nonnegative(self):
        self.assertGreaterEqual(_djb2("hello"), 0)


class TestRunIdFor(unittest.TestCase):
    def test_in_range(self):
        for qid in ["q01", "q02", "q04", "q08", "q12"]:
            rid = run_id_for(qid)
            self.assertGreaterEqual(rid, 1000)
            self.assertLessEqual(rid, 9999)

    def test_stable(self):
        self.assertEqual(run_id_for("q01"), run_id_for("q01"))

    def test_different_questions_may_differ(self):
        # not guaranteed but highly probable for distinct short strings
        ids = {run_id_for("q%02d" % i) for i in range(1, 13)}
        self.assertGreater(len(ids), 1)


class TestGtMap(unittest.TestCase):
    def test_gt_right_resolves_to_filename(self):
        info = GT_MAP["q01"]
        self.assertEqual(info["gt_file"], "jit_1p25.png")
        self.assertEqual(info["dimension"], "roughness")

    def test_catch_pair_gt_file_is_none(self):
        info = GT_MAP["q04"]
        self.assertIsNone(info["gt_file"])

    def test_note_preserved(self):
        info = GT_MAP["q04"]
        self.assertIn("catch pair", info["note"])


class TestNormalizeAnswer(unittest.TestCase):
    def test_correct_answer_score_1(self):
        # q01 gt is "right" = jit_1p25.png
        ans = _make_answer("q01", "jit_1p25.png")
        rec, reason = normalize_answer(ans, 0, GT_MAP, JUDGE_ID, INGESTED_AT)
        self.assertIsNone(reason)
        self.assertEqual(rec["score"], 1)

    def test_wrong_answer_score_0(self):
        # q01 gt is jit_1p25.png; judge picks jit_0p00.png
        ans = _make_answer("q01", "jit_0p00.png")
        rec, reason = normalize_answer(ans, 0, GT_MAP, JUDGE_ID, INGESTED_AT)
        self.assertIsNone(reason)
        self.assertEqual(rec["score"], 0)

    def test_catch_pair_score_none(self):
        # q04 has gt=null
        ans = _make_answer("q04", "jit_2p50.png")
        rec, reason = normalize_answer(ans, 0, GT_MAP, JUDGE_ID, INGESTED_AT)
        self.assertIsNone(reason)
        self.assertIsNone(rec["score"])

    def test_catch_pair_notes_mention_catch(self):
        ans = _make_answer("q04", "jit_2p50.png")
        rec, _ = normalize_answer(ans, 0, GT_MAP, JUDGE_ID, INGESTED_AT)
        self.assertIn("catch pair", rec["notes"])

    def test_confidence_in_notes(self):
        ans = _make_answer("q01", "jit_1p25.png", confidence="very sure")
        rec, _ = normalize_answer(ans, 0, GT_MAP, JUDGE_ID, INGESTED_AT)
        self.assertIn("very sure", rec["notes"])

    def test_question_id_in_notes(self):
        ans = _make_answer("q01", "jit_1p25.png")
        rec, _ = normalize_answer(ans, 0, GT_MAP, JUDGE_ID, INGESTED_AT)
        self.assertIn("q01", rec["notes"])

    def test_required_fields_present(self):
        ans = _make_answer("q01", "jit_1p25.png")
        rec, _ = normalize_answer(ans, 0, GT_MAP, JUDGE_ID, INGESTED_AT)
        for field in ("id", "run_id", "judge_id", "dimension", "score", "notes", "created_at"):
            self.assertIn(field, rec)

    def test_run_id_is_int(self):
        ans = _make_answer("q01", "jit_1p25.png")
        rec, _ = normalize_answer(ans, 0, GT_MAP, JUDGE_ID, INGESTED_AT)
        self.assertIsInstance(rec["run_id"], int)

    def test_id_is_sequential(self):
        ans0 = _make_answer("q01", "jit_1p25.png")
        ans1 = _make_answer("q02", "jit_2p50.png")
        rec0, _ = normalize_answer(ans0, 0, GT_MAP, JUDGE_ID, INGESTED_AT)
        rec1, _ = normalize_answer(ans1, 1, GT_MAP, JUDGE_ID, INGESTED_AT)
        self.assertEqual(rec0["id"], 1)
        self.assertEqual(rec1["id"], 2)

    def test_missing_question_id_skip(self):
        ans = {"choice": "jit_1p25.png", "confidence": "pretty sure"}
        rec, reason = normalize_answer(ans, 0, GT_MAP, JUDGE_ID, INGESTED_AT)
        self.assertIsNone(rec)
        self.assertIsNotNone(reason)

    def test_unknown_question_id_skip(self):
        ans = _make_answer("q01", "jit_1p25.png")
        ans["question_id"] = "q99"
        rec, reason = normalize_answer(ans, 0, GT_MAP, JUDGE_ID, INGESTED_AT)
        self.assertIsNone(rec)
        self.assertIn("unknown", reason)

    def test_missing_choice_skip(self):
        ans = _make_answer("q01", "jit_1p25.png")
        ans["choice"] = ""
        rec, reason = normalize_answer(ans, 0, GT_MAP, JUDGE_ID, INGESTED_AT)
        self.assertIsNone(rec)
        self.assertIsNotNone(reason)

    def test_anonymous_judge(self):
        ans = _make_answer("q01", "jit_1p25.png")
        rec, _ = normalize_answer(ans, 0, GT_MAP, None, INGESTED_AT)
        self.assertEqual(rec["judge_id"], "anonymous")

    def test_empty_judge_id_becomes_anonymous(self):
        ans = _make_answer("q01", "jit_1p25.png")
        rec, _ = normalize_answer(ans, 0, GT_MAP, "", INGESTED_AT)
        self.assertEqual(rec["judge_id"], "anonymous")


class TestValidateRecord(unittest.TestCase):
    def _make_rec(self, **overrides):
        base = {
            "id": 1,
            "run_id": run_id_for("q01"),
            "judge_id": JUDGE_ID,
            "dimension": "roughness",
            "score": 1,
            "notes": "confidence: pretty sure; question_id: q01",
            "created_at": INGESTED_AT,
        }
        base.update(overrides)
        return base

    def test_valid_record_no_errors(self):
        errors = validate_record(self._make_rec())
        self.assertEqual(errors, [])

    def test_catch_pair_score_none_no_errors(self):
        rec = self._make_rec(score=None)
        errors = validate_record(rec)
        self.assertEqual(errors, [])

    def test_missing_judge_id_has_error(self):
        rec = self._make_rec()
        del rec["judge_id"]
        errors = validate_record(rec)
        self.assertTrue(any("judge_id" in e for e in errors))

    def test_wrong_type_run_id(self):
        rec = self._make_rec(run_id="not-an-int")
        errors = validate_record(rec)
        self.assertTrue(any("run_id" in e for e in errors))


class TestBuildSummary(unittest.TestCase):
    def _records(self):
        # 2 correct roughness, 1 wrong roughness, 1 catch (score=None), 1 correct line_weight
        return [
            {"dimension": "roughness",   "score": 1},
            {"dimension": "roughness",   "score": 1},
            {"dimension": "roughness",   "score": 0},
            {"dimension": "roughness",   "score": None},  # catch pair
            {"dimension": "line_weight", "score": 1},
        ]

    def test_per_dimension_counts(self):
        summary = build_summary(self._records(), [])
        self.assertEqual(summary["per_dimension_agreement"]["roughness"]["n"], 3)
        self.assertEqual(summary["per_dimension_agreement"]["roughness"]["correct"], 2)

    def test_agreement_rate(self):
        summary = build_summary(self._records(), [])
        self.assertAlmostEqual(
            summary["per_dimension_agreement"]["roughness"]["agreement_rate"],
            round(2/3, 3)
        )

    def test_catch_pair_counted(self):
        summary = build_summary(self._records(), [])
        self.assertEqual(summary["catch_pairs"]["n_answered"], 1)

    def test_skipped_reported(self):
        skipped = [{"seq": 5, "reason": "missing choice"}]
        summary = build_summary(self._records(), skipped)
        self.assertEqual(summary["total_skipped"], 1)
        self.assertEqual(summary["skipped"], skipped)

    def test_line_weight_dimension_present(self):
        summary = build_summary(self._records(), [])
        self.assertIn("line_weight", summary["per_dimension_agreement"])


class TestIngestIntegration(unittest.TestCase):
    """full pipeline test using a temp file for the results JSON."""

    def _write_results(self, payload):
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        )
        json.dump(payload, tmp)
        tmp.close()
        return tmp.name

    def test_good_results_all_accepted(self):
        answers = [
            _make_answer("q01", "jit_1p25.png"),   # correct
            _make_answer("q02", "jit_2p50.png"),   # correct
            _make_answer("q04", "jit_2p50.png"),   # catch pair
            _make_answer("q08", "fid2_width9.png"), # correct
        ]
        path = self._write_results(_make_results(answers))
        try:
            records, summary, skipped = ingest(path, dry_run=True)
        finally:
            os.unlink(path)
        self.assertEqual(len(records), 4)
        self.assertEqual(len(skipped), 0)

    def test_correct_answers_score_1(self):
        answers = [_make_answer("q01", "jit_1p25.png")]
        path = self._write_results(_make_results(answers))
        try:
            records, _, _ = ingest(path, dry_run=True)
        finally:
            os.unlink(path)
        self.assertEqual(records[0]["score"], 1)

    def test_wrong_answer_score_0(self):
        answers = [_make_answer("q01", "jit_0p00.png")]  # wrong
        path = self._write_results(_make_results(answers))
        try:
            records, _, _ = ingest(path, dry_run=True)
        finally:
            os.unlink(path)
        self.assertEqual(records[0]["score"], 0)

    def test_catch_pair_score_null(self):
        answers = [_make_answer("q04", "jit_2p50.png")]
        path = self._write_results(_make_results(answers))
        try:
            records, _, _ = ingest(path, dry_run=True)
        finally:
            os.unlink(path)
        self.assertIsNone(records[0]["score"])

    def test_invalid_answer_skipped_with_reason(self):
        bad = {"question_id": "", "choice": "", "confidence": "sure", "elapsed_ms": 0}
        answers = [bad, _make_answer("q01", "jit_1p25.png")]
        path = self._write_results(_make_results(answers))
        try:
            records, summary, skipped = ingest(path, dry_run=True)
        finally:
            os.unlink(path)
        self.assertEqual(len(records), 1)
        self.assertEqual(len(skipped), 1)
        self.assertIsNotNone(skipped[0]["reason"])

    def test_dry_run_does_not_write_file(self):
        answers = [_make_answer("q01", "jit_1p25.png")]
        path = self._write_results(_make_results(answers))
        out_path = os.path.join(os.path.dirname(os.path.dirname(path)),
                                "survey", "judgments_out.json")
        existed_before = os.path.exists(out_path)
        try:
            ingest(path, dry_run=True)
        finally:
            os.unlink(path)
        # either it didn't exist before and still doesn't, or it existed and wasn't changed
        if not existed_before:
            self.assertFalse(os.path.exists(out_path))

    def test_anonymous_judge_in_records(self):
        answers = [_make_answer("q01", "jit_1p25.png")]
        results = _make_results(answers, judge_id="")
        path = self._write_results(results)
        try:
            records, _, _ = ingest(path, dry_run=True)
        finally:
            os.unlink(path)
        self.assertEqual(records[0]["judge_id"], "anonymous")

    def test_gt_join_uses_stimuli_not_answer(self):
        # even if the answer carries a wrong dimension label, gt comes from stimuli
        ans = _make_answer("q08", "fid2_width9.png")
        ans["dimension"] = "roughness"   # lie about dimension
        path = self._write_results(_make_results([ans]))
        try:
            records, _, _ = ingest(path, dry_run=True)
        finally:
            os.unlink(path)
        # normalize_answer uses answer dimension first, but gt_file comes from gt_map
        # score should still be 1 because choice == gt_file
        self.assertEqual(records[0]["score"], 1)

    def test_not_a_list_answers_skipped(self):
        results = {"judge_id": "x", "answers": "oops"}
        path = self._write_results(results)
        try:
            records, summary, skipped = ingest(path, dry_run=True)
        finally:
            os.unlink(path)
        self.assertEqual(records, [])

    def test_missing_results_file_returns_empty(self):
        records, summary, skipped = ingest("/nonexistent/path.json", dry_run=True)
        self.assertEqual(records, [])


if __name__ == "__main__":
    unittest.main()

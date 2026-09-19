"""tests/test_survey_ingest.py — unit tests for survey/ingest.py.

runs with plain unittest (no network, no external deps).
fixture-based; the real filesystem is only touched via tempfile for
the ingest() integration tests.

rewritten 2026-09-19 for the live xano `judgments` table record shape
(the previous suite tested a "human_judgments" shape for a table that was
never actually provisioned — see xano/definitions/README.md).
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
    ingest,
    _build_gt_map,
    _session_id,
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
SESSION_ID = "test_judge_00000000Z"


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
# session id
# ---------------------------------------------------------------------------

class TestSessionId(unittest.TestCase):
    def test_matches_sync_judgments_derivation(self):
        # scripts/sync_judgments.py: judge_id + started_at digits-only, last 9
        results = {"judge_id": "anonymous", "started_at": "2026-09-06T21:14:31.664Z"}
        expect = "anonymous_" + "2026-09-06T21:14:31.664Z".replace(":", "").replace("-", "")[-9:]
        self.assertEqual(_session_id(results), expect)

    def test_missing_started_at_still_usable(self):
        self.assertTrue(_session_id({"judge_id": "x", "started_at": ""}).startswith("x_"))


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------

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

    def test_stimulus_basenames_available(self):
        info = GT_MAP["q08"]
        self.assertEqual(info["left_file"], "fid2_width3.png")
        self.assertEqual(info["right_file"], "fid2_width9.png")


class TestNormalizeAnswer(unittest.TestCase):
    def test_correct_answer_score_1(self):
        # q01 gt is "right" = jit_1p25.png
        ans = _make_answer("q01", "jit_1p25.png")
        rec, reason = normalize_answer(ans, 0, GT_MAP, JUDGE_ID, INGESTED_AT, SESSION_ID)
        self.assertIsNone(reason)
        self.assertEqual(rec["score"], 1)

    def test_wrong_answer_score_0(self):
        # q01 gt is jit_1p25.png; judge picks jit_0p00.png
        ans = _make_answer("q01", "jit_0p00.png")
        rec, reason = normalize_answer(ans, 0, GT_MAP, JUDGE_ID, INGESTED_AT, SESSION_ID)
        self.assertIsNone(reason)
        self.assertEqual(rec["score"], 0)

    def test_catch_pair_score_none_and_flagged(self):
        # q04 has gt=null
        ans = _make_answer("q04", "jit_2p50.png")
        rec, reason = normalize_answer(ans, 0, GT_MAP, JUDGE_ID, INGESTED_AT, SESSION_ID)
        self.assertIsNone(reason)
        self.assertIsNone(rec["score"])
        self.assertTrue(rec["is_catch_pair"])

    def test_scored_pair_not_flagged_as_catch(self):
        ans = _make_answer("q01", "jit_1p25.png")
        rec, _ = normalize_answer(ans, 0, GT_MAP, JUDGE_ID, INGESTED_AT, SESSION_ID)
        self.assertFalse(rec["is_catch_pair"])

    def test_live_table_fields_present(self):
        ans = _make_answer("q01", "jit_1p25.png")
        rec, _ = normalize_answer(ans, 0, GT_MAP, JUDGE_ID, INGESTED_AT, SESSION_ID)
        for field in ("id", "judge_id", "dimension", "stimulus_a_id",
                      "stimulus_b_id", "chosen", "confidence", "is_catch_pair",
                      "noise_flag", "reaction_ms", "session_id", "question_id",
                      "raw", "score", "created_at"):
            self.assertIn(field, rec)

    def test_raw_holds_full_answer(self):
        ans = _make_answer("q01", "jit_1p25.png")
        rec, _ = normalize_answer(ans, 0, GT_MAP, JUDGE_ID, INGESTED_AT, SESSION_ID)
        self.assertEqual(rec["raw"], ans)

    def test_confidence_carried(self):
        ans = _make_answer("q01", "jit_1p25.png", confidence="very sure")
        rec, _ = normalize_answer(ans, 0, GT_MAP, JUDGE_ID, INGESTED_AT, SESSION_ID)
        self.assertEqual(rec["confidence"], "very sure")

    def test_reaction_ms_from_elapsed(self):
        ans = _make_answer("q01", "jit_1p25.png")
        rec, _ = normalize_answer(ans, 0, GT_MAP, JUDGE_ID, INGESTED_AT, SESSION_ID)
        self.assertEqual(rec["reaction_ms"], 2500)

    def test_id_is_sequential(self):
        ans0 = _make_answer("q01", "jit_1p25.png")
        ans1 = _make_answer("q02", "jit_2p50.png")
        rec0, _ = normalize_answer(ans0, 0, GT_MAP, JUDGE_ID, INGESTED_AT, SESSION_ID)
        rec1, _ = normalize_answer(ans1, 1, GT_MAP, JUDGE_ID, INGESTED_AT, SESSION_ID)
        self.assertEqual(rec0["id"], 1)
        self.assertEqual(rec1["id"], 2)

    def test_missing_question_id_skip(self):
        ans = {"choice": "jit_1p25.png", "confidence": "pretty sure"}
        rec, reason = normalize_answer(ans, 0, GT_MAP, JUDGE_ID, INGESTED_AT, SESSION_ID)
        self.assertIsNone(rec)
        self.assertIsNotNone(reason)

    def test_unknown_question_id_skip(self):
        ans = _make_answer("q01", "jit_1p25.png")
        ans["question_id"] = "q99"
        rec, reason = normalize_answer(ans, 0, GT_MAP, JUDGE_ID, INGESTED_AT, SESSION_ID)
        self.assertIsNone(rec)
        self.assertIn("unknown", reason)

    def test_missing_choice_skip(self):
        ans = _make_answer("q01", "jit_1p25.png")
        ans["choice"] = ""
        rec, reason = normalize_answer(ans, 0, GT_MAP, JUDGE_ID, INGESTED_AT, SESSION_ID)
        self.assertIsNone(rec)
        self.assertIsNotNone(reason)

    def test_anonymous_judge(self):
        ans = _make_answer("q01", "jit_1p25.png")
        rec, _ = normalize_answer(ans, 0, GT_MAP, None, INGESTED_AT, SESSION_ID)
        self.assertEqual(rec["judge_id"], "anonymous")

    def test_empty_judge_id_becomes_anonymous(self):
        ans = _make_answer("q01", "jit_1p25.png")
        rec, _ = normalize_answer(ans, 0, GT_MAP, "", INGESTED_AT, SESSION_ID)
        self.assertEqual(rec["judge_id"], "anonymous")

    def test_stimulus_ids_fall_back_to_stimuli(self):
        # answer missing left_file/right_file labels -> basenames from stimuli
        ans = _make_answer("q08", "fid2_width9.png")
        del ans["left_file"]
        del ans["right_file"]
        rec, _ = normalize_answer(ans, 0, GT_MAP, JUDGE_ID, INGESTED_AT, SESSION_ID)
        self.assertEqual(rec["stimulus_a_id"], "fid2_width3.png")
        self.assertEqual(rec["stimulus_b_id"], "fid2_width9.png")


class TestValidateRecord(unittest.TestCase):
    def _make_rec(self, **overrides):
        base = {
            "id": 1,
            "judge_id": JUDGE_ID,
            "dimension": "roughness",
            "stimulus_a_id": "jit_0p00.png",
            "stimulus_b_id": "jit_1p25.png",
            "chosen": "jit_1p25.png",
            "confidence": "pretty sure",
            "is_catch_pair": False,
            "noise_flag": False,
            "reaction_ms": 2500,
            "session_id": SESSION_ID,
            "question_id": "q01",
            "raw": {},
            "score": 1,
            "created_at": INGESTED_AT,
        }
        base.update(overrides)
        return base

    def test_valid_record_no_errors(self):
        errors = validate_record(self._make_rec())
        self.assertEqual(errors, [])

    def test_catch_pair_score_none_no_errors(self):
        rec = self._make_rec(score=None, is_catch_pair=True)
        errors = validate_record(rec)
        self.assertEqual(errors, [])

    def test_missing_question_id_has_error(self):
        rec = self._make_rec()
        del rec["question_id"]
        errors = validate_record(rec)
        self.assertTrue(any("question_id" in e for e in errors))

    def test_missing_chosen_has_error(self):
        rec = self._make_rec()
        del rec["chosen"]
        errors = validate_record(rec)
        self.assertTrue(any("chosen" in e for e in errors))

    def test_missing_session_id_has_error(self):
        rec = self._make_rec()
        del rec["session_id"]
        errors = validate_record(rec)
        self.assertTrue(any("session_id" in e for e in errors))

    def test_wrong_type_question_id(self):
        rec = self._make_rec(question_id=12345)
        errors = validate_record(rec)
        self.assertTrue(any("question_id" in e for e in errors))

    def test_extra_local_fields_are_ignored(self):
        # score/created_at are local-only extras — the live-table validator
        # must not choke on them
        rec = self._make_rec(score=0)
        self.assertEqual(validate_record(rec), [])


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
        self.assertAlmostEqual(summary["per_dimension_agreement"]["roughness"]["agreement_rate"], 2/3, places=3)

    def test_catch_pairs_excluded_from_dimension_rates(self):
        summary = build_summary(self._records(), [])
        # only 3 scored roughness answers, the None-score catch does not count
        self.assertEqual(summary["per_dimension_agreement"]["roughness"]["n"], 3)

    def test_catch_pairs_counted(self):
        summary = build_summary(self._records(), [])
        self.assertEqual(summary["catch_pairs"]["n_answered"], 1)

    def test_empty_records(self):
        summary = build_summary([], [])
        self.assertEqual(summary["total_records"], 0)
        self.assertEqual(summary["per_dimension_agreement"], {})


# ---------------------------------------------------------------------------
# integration (tempfile-backed)
# ---------------------------------------------------------------------------

# self-contained fixture stimuli (the repo's live survey/stimuli.json is
# whatever batch is currently deployed — batch 4 as of this writing — so the
# integration tests must not depend on it)
def _write_stimuli():
    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(STIMULI, f)
    return path


class TestIngestIntegration(unittest.TestCase):
    def setUp(self):
        self.stimuli_path = _write_stimuli()

    def tearDown(self):
        os.unlink(self.stimuli_path)

    def _write_results(self, results):
        fd, path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(results, f)
        return path

    def test_good_results_all_accepted(self):
        answers = [
            _make_answer("q01", "jit_1p25.png"),   # correct
            _make_answer("q02", "jit_2p50.png"),   # correct
            _make_answer("q04", "jit_2p50.png"),   # catch
            _make_answer("q08", "fid2_width9.png"), # correct
        ]
        path = self._write_results(_make_results(answers))
        try:
            records, summary, skipped = ingest(path, dry_run=True, stimuli_path=self.stimuli_path)
        finally:
            os.unlink(path)
        self.assertEqual(len(records), 4)
        self.assertEqual(len(skipped), 0)

    def test_correct_answers_score_1(self):
        answers = [_make_answer("q01", "jit_1p25.png")]
        path = self._write_results(_make_results(answers))
        try:
            records, _, _ = ingest(path, dry_run=True, stimuli_path=self.stimuli_path)
        finally:
            os.unlink(path)
        self.assertEqual(records[0]["score"], 1)

    def test_wrong_answer_score_0(self):
        answers = [_make_answer("q01", "jit_0p00.png")]  # wrong
        path = self._write_results(_make_results(answers))
        try:
            records, _, _ = ingest(path, dry_run=True, stimuli_path=self.stimuli_path)
        finally:
            os.unlink(path)
        self.assertEqual(records[0]["score"], 0)

    def test_catch_pair_score_null(self):
        answers = [_make_answer("q04", "jit_2p50.png")]
        path = self._write_results(_make_results(answers))
        try:
            records, _, _ = ingest(path, dry_run=True, stimuli_path=self.stimuli_path)
        finally:
            os.unlink(path)
        self.assertIsNone(records[0]["score"])

    def test_records_carry_session_id(self):
        answers = [_make_answer("q01", "jit_1p25.png")]
        results = _make_results(answers)
        path = self._write_results(results)
        try:
            records, _, _ = ingest(path, dry_run=True, stimuli_path=self.stimuli_path)
        finally:
            os.unlink(path)
        self.assertEqual(records[0]["session_id"], _session_id(results))

    def test_invalid_answer_skipped_with_reason(self):
        bad = {"question_id": "", "choice": "", "confidence": "sure", "elapsed_ms": 0}
        answers = [bad, _make_answer("q01", "jit_1p25.png")]
        path = self._write_results(_make_results(answers))
        try:
            records, summary, skipped = ingest(path, dry_run=True, stimuli_path=self.stimuli_path)
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
            records, _, _ = ingest(path, dry_run=True, stimuli_path=self.stimuli_path)
        finally:
            os.unlink(path)
        self.assertEqual(records[0]["judge_id"], "anonymous")

    def test_gt_join_uses_stimuli_not_answer(self):
        # even if the answer carries a wrong dimension label, gt comes from stimuli
        ans = _make_answer("q08", "fid2_width9.png")
        ans["dimension"] = "roughness"   # lie about dimension
        path = self._write_results(_make_results([ans]))
        try:
            records, _, _ = ingest(path, dry_run=True, stimuli_path=self.stimuli_path)
        finally:
            os.unlink(path)
        # score should still be 1 because choice == gt_file from gt_map
        self.assertEqual(records[0]["score"], 1)

    def test_not_a_list_answers_skipped(self):
        results = {"judge_id": "x", "answers": "oops"}
        path = self._write_results(results)
        try:
            records, summary, skipped = ingest(path, dry_run=True, stimuli_path=self.stimuli_path)
        finally:
            os.unlink(path)
        self.assertEqual(records, [])


if __name__ == "__main__":
    unittest.main()

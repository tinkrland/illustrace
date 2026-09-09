"""offline tests for survey/analyze_batch.py (no network, no substrate)."""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(__file__), "..")))

from survey import analyze_batch as ab  # noqa: E402


def _q(qid, kind="pair", gt="right", scored=True, left="a.png", right="b.png"):
    return {"id": qid, "kind": kind, "dimension": "roughness", "prompt": "?",
            "left": left, "right": right, "gt": gt, "scored": scored}


class TestScoring(unittest.TestCase):
    def test_pair_correct_by_gt_side(self):
        q = _q("q1")
        self.assertEqual(ab.score_answer(q, "b.png"), "correct")
        self.assertEqual(ab.score_answer(q, "a.png"), "incorrect")

    def test_nodiff_is_signal_not_incident(self):
        self.assertEqual(ab.score_answer(_q("q1"), "identical"), "nodiff")

    def test_catch(self):
        c = {"kind": "catch", "scored": False, "id": "c1"}
        self.assertEqual(ab.score_answer(c, "identical"), "correct")
        self.assertEqual(ab.score_answer(c, "a.png"), "incorrect")

    def test_same_different(self):
        q = _q("q7", kind="same_different", gt="different")
        self.assertEqual(ab.score_answer(q, "different"), "correct")
        self.assertEqual(ab.score_answer(q, "same"), "incorrect")

    def test_anchor_unscorable(self):
        q = _q("q0", scored=False)
        self.assertEqual(ab.score_answer(q, "b.png"), "unscorable")


class TestJudgeExclusion(unittest.TestCase):
    def test_more_than_one_catch_fail_excludes(self):
        qmap = {"c1": {"kind": "catch", "scored": False}, "c2": {"kind": "catch", "scored": False},
                "c3": {"kind": "catch", "scored": False}}
        answers = [{"question_id": "c1", "choice": "a.png"},
                   {"question_id": "c2", "choice": "a.png"},
                   {"question_id": "c3", "choice": "identical"}]
        js = ab.judge_summary(answers, qmap)
        self.assertEqual(js["catch_fails"], 2)
        self.assertTrue(js["excluded"])

    def test_one_catch_fail_kept(self):
        qmap = {"c1": {"kind": "catch", "scored": False}}
        js = ab.judge_summary([{"question_id": "c1", "choice": "a.png"}], qmap)
        self.assertFalse(js["excluded"])


class TestStimulusFailure(unittest.TestCase):
    def test_even_split_is_stimulus_failure(self):
        qmap = {"q1": _q("q1")}
        answers = [{"question_id": "q1", "choice": "b.png"},
                   {"question_id": "q1", "choice": "b.png"},
                   {"question_id": "q1", "choice": "a.png"},
                   {"question_id": "q1", "choice": "a.png"}]
        stats = ab.question_stats(answers, qmap)
        self.assertTrue(stats["q1"]["stimulus_failure"])
        self.assertEqual(stats["q1"]["agreement"], 0.5)

    def test_clear_agreement_is_not_failure(self):
        qmap = {"q1": _q("q1")}
        answers = [{"question_id": "q1", "choice": "b.png"}] * 3 + \
                  [{"question_id": "q1", "choice": "a.png"}]
        stats = ab.question_stats(answers, qmap)
        self.assertFalse(stats["q1"]["stimulus_failure"])


class TestVerdictRules(unittest.TestCase):
    def setUp(self):
        self.spec = json.load(open(os.path.join(os.path.dirname(__file__), "..",
                                                "survey", "specs", "batch_2.json")))

    def _qmap(self):
        return {q["id"]: q for q in self.spec["questions"]}

    def test_demo_pipeline_verdicts(self):
        files = ab.demo()
        rep = ab.analyze(files, spec=self.spec)
        v = rep["verdicts"]
        self.assertEqual(rep["judges_included"], 5)
        self.assertEqual(v["jitter_substrate"], "ok")
        self.assertIn("promote", v["taper"])
        self.assertEqual(v["grain"]["floor_first_passing_0vX"], 8)
        self.assertTrue(v["grain"]["local_jnd_8v11_pass"])
        self.assertIn("validated", v["lighting"])

    def test_taper_split_gives_standalone(self):
        # 5 judges: roughness polarity 3/2 split, calligraphic clean pass
        qmap = self._qmap()
        files = []
        for ji in range(5):
            answers = []
            for qid, q in qmap.items():
                if q["kind"] == "same_different":
                    choice = q["gt"]
                elif q["kind"] == "pair" and not q.get("scored", True):
                    choice = "x.png"
                elif qid == "b2t1":
                    choice = "fid2_taper15.png" if ji < 3 else "fid2_taper60.png"
                else:
                    from os.path import basename
                    choice = basename(q["right"] if q["gt"] == "right" else q["left"])
                answers.append({"question_id": qid, "choice": choice,
                                "kind": q["kind"], "scored": q.get("scored", True),
                                "dimension": q["dimension"]})
            for c in self.spec["catches"]:
                answers.append({"question_id": c["id"], "choice": "identical"})
            p = "/tmp/t_split_j%d.json" % ji
            json.dump({"answers": answers}, open(p, "w"))
            files.append(p)
        rep = ab.analyze(files, spec=self.spec)
        self.assertIn("standalone", rep["verdicts"]["taper"])


class TestBootstrap(unittest.TestCase):
    def test_ci_brackets_mean(self):
        ci = ab.bootstrap_ci([1.0, 1.0, 1.0, 0.0, 0.0], n=500)
        self.assertIsNotNone(ci)
        self.assertLessEqual(ci[0], 0.6)
        self.assertGreaterEqual(ci[1], 0.6)


if __name__ == "__main__":
    unittest.main()

"""analyze a batch of survey results against its preregistered spec.

scores each answer by the spec's ground truth, excludes judges who fail the
catch criterion, computes per-question and per-block agreement with bootstrap
CIs, applies the spec's verdict rules, and flags stimulus failures (50/50
splits) for adaptive regeneration next batch.

usage:
  python3 survey/analyze_batch.py results_judge1.json [results_judge2.json ...]
  python3 survey/analyze_batch.py --demo          # synthetic self-test
"""
import json
import os
import random
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))


def load_spec(path=None):
    return json.load(open(path or os.path.join(HERE, "specs", "batch_2.json")))


def score_answer(q_spec, choice):
    """-> 'correct' | 'incorrect' | 'nodiff' | 'unscorable'"""
    if q_spec is None:
        return "unscorable"
    kind = q_spec.get("kind", "pair")
    if kind == "same_different":
        return "correct" if choice == q_spec["gt"] else "incorrect"
    if kind == "catch":
        return "correct" if choice == "identical" else "incorrect"
    if not q_spec.get("scored", True):
        return "unscorable"
    if choice == "identical":
        return "nodiff"  # below the judge's perceptual floor, real signal
    gt_file = os.path.basename(q_spec["right"] if q_spec["gt"] == "right" else q_spec["left"])
    return "correct" if choice == gt_file else "incorrect"


def judge_summary(answers, qmap):
    """catch performance + scored accuracy for one judge."""
    catches = [score_answer(qmap[a["question_id"]], a["choice"])
               for a in answers
               if qmap.get(a["question_id"], {}).get("kind") == "catch"]
    catch_fails = catches.count("incorrect")
    scored = [score_answer(qmap[a["question_id"]], a["choice"])
              for a in answers
              if qmap.get(a["question_id"], {}).get("scored") and
                 qmap.get(a["question_id"], {}).get("kind") in ("pair", "same_different")]
    return {
        "catch_fails": catch_fails,
        "excluded": catch_fails > 1,
        "scored_n": len(scored),
        "scored_correct": scored.count("correct"),
        "scored_incorrect": scored.count("incorrect"),
        "scored_nodiff": scored.count("nodiff"),
    }


def question_stats(included_answers, qmap):
    """per-question agreement among included judges."""
    by_q = defaultdict(list)
    for a in included_answers:
        by_q[a["question_id"]].append(score_answer(qmap[a["question_id"]], a["choice"]))
    out = {}
    for qid, scores in by_q.items():
        n = len(scores)
        correct = scores.count("correct")
        out[qid] = {
            "n": n, "correct": correct,
            "agreement": round(correct / n, 3) if n else None,
            "nodiff": scores.count("nodiff"),
            "stimulus_failure": (n >= 2 and n > 0 and
                                 abs(scores.count("correct") - scores.count("incorrect")) <= n // 2
                                 and scores.count("correct") + scores.count("incorrect") == n
                                 and n % 2 == 0 and correct == n - correct),
        }
    return out


def block_agreement(qstats, spec):
    """agreement per dimension block with bootstrap CI over judges."""
    by_dim = defaultdict(list)
    for q in spec["questions"]:
        if q.get("kind") in ("pair", "same_different") and q.get("scored", True):
            by_dim[q["dimension"]].append(q["id"])
    out = {}
    for dim, qids in by_dim.items():
        vals = [qstats[q]["agreement"] for q in qids if q in qstats and qstats[q]["agreement"] is not None]
        if not vals:
            continue
        mean = sum(vals) / len(vals)
        out[dim] = {"mean": round(mean, 3), "pairs": len(vals), "values": vals}
    return out


def bootstrap_ci(vals, n=2000, seed=17):
    """95% CI of the mean by resampling the values."""
    if not vals:
        return None
    rng = random.Random(seed)
    means = []
    for _ in range(n):
        s = [rng.choice(vals) for _ in vals]
        means.append(sum(s) / len(s))
    means.sort()
    lo = means[int(0.025 * n)]
    hi = means[int(0.975 * n) - 1]
    return (round(lo, 3), round(hi, 3))


def verdicts(qstats, spec, n_judges):
    """apply the spec's decision rules. n = number of included judges."""
    v = {}
    need = max(1, round(n_judges * 0.8))  # >=4/5 rule generalized

    def agree(qid, side_file=None):
        q = qstats.get(qid)
        if not q:
            return None
        return q["correct"] >= need

    # jitter substrate sanity
    v["jitter_substrate"] = "ok" if (agree("b2j1") and agree("b2j3")) else \
        "FAIL: jitter pairs missed — session substrate invalid"

    # taper decision rule
    t_rough = qstats.get("b2t1", {}).get("correct", 0)
    t_char1 = qstats.get("b2t2", {}).get("correct", 0)
    t_char2 = qstats.get("b2t3", {}).get("correct", 0)
    t_cross = qstats.get("b2t4", {}).get("correct", 0)
    char_pass = t_char1 >= need and t_char2 >= need
    if t_rough >= need and char_pass:
        v["taper"] = ("promote: line_character axis validated, roughness polarity confirmed "
                      "(uniform reads as rougher, heavy taper as smoother)")
        if t_cross >= need:
            v["taper_cross_cue"] = "jitter roughness dominates when cues conflict"
    elif char_pass and abs(t_rough - (n_judges - t_rough)) <= 1:
        v["taper"] = "standalone line_character axis; removed from roughness composite"
    elif not char_pass and t_rough >= need:
        v["taper"] = "polarity only: keep as roughness component with inverted direction"
    else:
        v["taper"] = "kill the taper candidate (loads on neither framing)"

    # grain floor bracket
    floor = None
    for qid, hi in (("b2g1", 8), ("b2g5", 11), ("b2g6", 14)):
        if qstats.get(qid, {}).get("correct", 0) >= need:
            floor = hi if qid == "b2g6" else hi
            break
    local = (qstats.get("b2g3", {}).get("correct", 0) >= need,
             qstats.get("b2g4", {}).get("correct", 0) >= need)
    v["grain"] = {
        "anchor_0v14": "pass" if qstats.get("b2g6", {}).get("correct", 0) == n_judges else "weak",
        "floor_first_passing_0vX": floor,
        "local_jnd_8v11_pass": local[0],
        "local_jnd_11v14_pass": local[1],
        "d_prime_0v8": "different detected" if qstats.get("b2g7", {}).get("correct", 0) >= need
                       else "same/diff not detected — pilot miss likely a true floor",
    }

    # lighting on corrected prompt
    l_ok = qstats.get("b2l1", {}).get("correct", 0) >= need and \
           qstats.get("b2l2", {}).get("correct", 0) >= need
    l_small = qstats.get("b2l4", {}).get("correct", 0)
    v["lighting"] = "validated on the corrected brightness prompt" if l_ok else \
        "FAIL on corrected prompt — stays measurable, prompt/JND work queued"
    v["lighting_jnd_0p50v0p75"] = f"{l_small}/{n_judges}"

    # adaptive-data flags
    fails = [qid for qid, q in qstats.items() if q.get("stimulus_failure")]
    v["stimulus_failures_regenerate_next_batch"] = fails
    return v


def analyze(result_files, spec=None, write_markdown=None):
    spec = spec or load_spec()
    qmap = {}
    for q in spec["questions"]:
        qmap[q["id"]] = q
    for c in spec["catches"]:
        qmap[c["id"]] = {"kind": "catch", "scored": False, "id": c["id"]}

    judges, all_answers = [], []
    for path in result_files:
        r = json.load(open(path))
        answers = r.get("answers", r) if isinstance(r, dict) else r
        js = judge_summary(answers, qmap)
        js["file"] = os.path.basename(path)
        judges.append(js)
        all_answers.extend(answers)

    included = []
    excluded_files = {j["file"] for j in judges if j["excluded"]}
    for path in result_files:
        if os.path.basename(path) in excluded_files:
            continue
        r = json.load(open(path))
        answers = r.get("answers", r) if isinstance(r, dict) else r
        included.extend(answers)

    n_judges = len(judges) - len(excluded_files)
    qstats = question_stats(included, qmap)
    blocks = block_agreement(qstats, spec)
    for dim, b in blocks.items():
        b["ci95"] = bootstrap_ci(b["values"])
        del b["values"]
    verd = verdicts(qstats, spec, max(n_judges, 1))

    report = {
        "batch": spec["batch"],
        "judges_total": len(judges),
        "judges_excluded_catch_fail": sorted(excluded_files),
        "judges_included": n_judges,
        "per_judge": judges,
        "per_question": qstats,
        "per_dimension": blocks,
        "verdicts": verd,
    }
    if write_markdown:
        with open(write_markdown, "w") as f:
            f.write(render_markdown(report))
    return report


def render_markdown(rep):
    lines = [f"# human-validation {rep['batch']}: analysis", ""]
    lines.append(f"judges: {rep['judges_included']} included, "
                 f"{len(rep['judges_excluded_catch_fail'])} excluded (catch-fail rule)")
    if rep["judges_excluded_catch_fail"]:
        lines.append(f"excluded: {', '.join(rep['judges_excluded_catch_fail'])}")
    lines += ["", "## per-dimension agreement (bootstrap 95% ci)", "",
              "| dimension | mean agreement | ci95 | pairs |", "|---|---|---|---|"]
    for dim, b in rep["per_dimension"].items():
        ci = "-".join(str(x) for x in b["ci95"]) if b["ci95"] else "?"
        lines.append(f"| {dim} | {b['mean']} | {ci} | {b['pairs']} |")
    lines += ["", "## verdicts", ""]
    for k, v in rep["verdicts"].items():
        lines.append(f"- **{k}:** {json.dumps(v) if isinstance(v, dict) else v}")
    lines += ["", "## per-question detail", "", "| q | n | correct | agreement | nodiff |", "|---|---|---|---|---|"]
    for qid, q in sorted(rep["per_question"].items()):
        lines.append(f"| {qid} | {q['n']} | {q['correct']} | {q['agreement']} | {q['nodiff']} |")
    return "\n".join(lines) + "\n"


def demo():
    """synthetic judges for offline testing of every rule."""
    spec = load_spec()
    qmap = {q["id"]: q for q in spec["questions"]}
    files = []
    for ji in range(5):
        answers = []
        for qid, q in qmap.items():
            # 4 perfect judges, 1 judge with noise + one catch miss
            if ji == 4 and qid in ("b2g3", "b2l4"):
                choice = "identical" if q["kind"] == "pair" else ("same" if q["gt"] == "different" else "different")
            elif q["kind"] == "same_different":
                choice = q["gt"]  # 'different' or 'same'
            else:
                choice = os.path.basename(q["right"] if q["gt"] in ("right", "different") else q["left"])
            answers.append({"question_id": qid, "kind": q["kind"], "scored": q.get("scored", True),
                            "dimension": q["dimension"], "choice": choice,
                            "confidence": "pretty sure", "elapsed_ms": 2200})
        for c in spec["catches"]:
            answers.append({"question_id": c["id"], "kind": "catch", "scored": False,
                            "dimension": c["dimension"],
                            "choice": "identical" if not (ji == 4 and c["id"] == "b2c3") else os.path.basename(c["image"]),
                            "confidence": "a little", "elapsed_ms": 1800})
        path = f"/tmp/demo_judge{ji}.json"
        json.dump({"judge_id": f"demo{ji}", "answers": answers}, open(path, "w"))
        files.append(path)
    return files


if __name__ == "__main__":
    if "--demo" in sys.argv:
        files = demo()
        print("demo judges:", files)
        rep = analyze(files)
        print(json.dumps(rep["verdicts"], indent=2, default=str)[:1500])
    else:
        rep = analyze(sys.argv[1:])
        print(json.dumps(rep["verdicts"], indent=2, default=str))

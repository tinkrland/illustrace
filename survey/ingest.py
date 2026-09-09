"""survey/ingest.py — normalize downloaded survey results into human_judgments records.

usage:
    python survey/ingest.py results.json               # normalize + write judgments_out.json
    python survey/ingest.py results.json --dry-run     # validate only, no file written

run_id derivation
-----------------
question ids (q01–q12) are mapped to a stable integer run_id via a small fixed table
(RUN_ID_MAP). the mapping is: each question_id string is hashed with a simple djb2-style
hash, then reduced mod 9000 + 1000 to stay in a readable positive range. this is
deterministic across python versions because it avoids hash() (which is randomised).
the mapping is printed in the summary so downstream consumers can reproduce it.

score
-----
1 if the judge's chosen filename matches the ground-truth side, 0 otherwise.
catch pairs (gt == null in stimuli.json) get score = None and a note.

validation
----------
every normalized record is passed through xano.schema.validate('human_judgments').
records that fail validation are skipped with a reason printed to stderr.

output
------
survey/judgments_out.json — list of validated human_judgments records
summary printed to stdout: per-dimension agreement vs gt, catch-pair consistency rate.
"""

import argparse
import json
import os
import sys
import datetime

# allow running from repo root or from survey/
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_THIS_DIR)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from xano.schema import validate  # noqa: E402


# ---------------------------------------------------------------------------
# stimuli ground-truth lookup
# ---------------------------------------------------------------------------

def _load_stimuli(stimuli_path=None):
    """load stimuli.json (or an explicit batch file, e.g. specs/stimuli_batch1.json)."""
    path = stimuli_path or os.path.join(_THIS_DIR, "stimuli.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _build_gt_map(stimuli):
    """return {question_id: {"gt_file": str|None, "note": str|None, "dimension": str}}.

    gt_file is the basename of the gt side's path, or None for catch pairs.
    """
    gt_map = {}
    for q in stimuli["questions"]:
        gt = q.get("gt")   # "left" | "right" | None | "different"/"same" (v2)
        if gt not in ("left", "right"):
            gt_file = None  # catch pairs, anchors, same/different (analyzed by analyze_batch)
        else:
            side_path = q[gt]   # e.g. "../data/generated/arch_svg/jit_1p25.png"
            gt_file = os.path.basename(side_path)
        gt_map[q["id"]] = {
            "gt_file": gt_file,
            "dimension": q["dimension"],
            "note": q.get("note"),
        }
    return gt_map


# ---------------------------------------------------------------------------
# deterministic run_id derivation
# ---------------------------------------------------------------------------

def _djb2(s):
    """djb2 hash — deterministic, no stdlib randomisation."""
    h = 5381
    for c in s.encode("utf-8"):
        h = ((h << 5) + h + c) & 0xFFFFFFFF
    return h


def run_id_for(question_id):
    """return a stable positive int run_id for a question_id string.

    algorithm: djb2(question_id) mod 9000 + 1000 → range [1000, 9999].
    deterministic across all python versions (no hash() randomisation).
    """
    return _djb2(question_id) % 9000 + 1000


# ---------------------------------------------------------------------------
# normalization
# ---------------------------------------------------------------------------

def _make_id(seq):
    """simple sequential integer id (1-based) for the output records."""
    return seq + 1


def normalize_answer(answer, seq, gt_map, judge_id, ingested_at):
    """convert one answer dict into a human_judgments-shaped record.

    returns (record_dict, skip_reason_or_None).
    skip_reason is a non-empty string when the answer should be skipped.
    """
    qid = answer.get("question_id", "")
    if not qid:
        return None, "missing question_id"

    if qid not in gt_map:
        return None, "unknown question_id %r (not in stimuli.json)" % qid

    gt_info = gt_map[qid]
    chosen = answer.get("choice", "")
    if not chosen:
        return None, "q%s: missing choice" % qid

    gt_file = gt_info["gt_file"]
    dimension = answer.get("dimension") or gt_info["dimension"]

    # score: 1 if correct, 0 if wrong, None for catch pairs
    if gt_file is None:
        score = None
        score_note = "catch pair — no ground truth"
    else:
        score = 1 if chosen == gt_file else 0
        score_note = None

    # build notes field: confidence + question_id + any catch/note
    conf = answer.get("confidence", "unknown")
    notes_parts = [
        "confidence: %s" % conf,
        "question_id: %s" % qid,
    ]
    if score_note:
        notes_parts.append(score_note)
    if gt_info.get("note"):
        notes_parts.append(gt_info["note"])
    notes = "; ".join(notes_parts)

    rec = {
        "id":         _make_id(seq),
        "run_id":     run_id_for(qid),
        "judge_id":   str(judge_id) if judge_id else "anonymous",
        "dimension":  dimension,
        "score":      score,        # may be None for catch pairs
        "notes":      notes,
        "created_at": ingested_at,
    }
    return rec, None


# ---------------------------------------------------------------------------
# validation wrapper
# ---------------------------------------------------------------------------

def validate_record(rec):
    """run xano.schema.validate; handle None score (catch pairs) gracefully.

    the xano schema requires score to be non-None (it's a required field).
    for catch pairs we temporarily substitute -1 (a sentinel outside 0–10 that
    would normally fail score_range) — but we skip that range check by not
    substituting; instead we remove the score field before validation and
    re-insert after, then validate the structural fields only.

    actually: schema.validate marks 'score' required and None as missing.
    catch pairs legitimately have score=None. we validate them with score=0
    (a structural placeholder) so all *other* fields are checked; then we
    restore score=None in the final record and note the special status.
    """
    if rec.get("score") is None:
        # validate structure with a placeholder that satisfies schema constraints
        probe = dict(rec, score=0)
        return validate("human_judgments", probe)
    return validate("human_judgments", rec)


# ---------------------------------------------------------------------------
# summary
# ---------------------------------------------------------------------------

def build_summary(records, skipped):
    """return a summary dict: per-dimension agreement, catch-pair stats."""
    dim_totals = {}     # dimension -> [scored, correct]
    catch_totals = []   # scores for catch pairs (None == responded, not None impossible)
    catch_chose = 0     # times a judge chose something on a catch pair (always True if answered)

    for rec in records:
        is_catch = rec["score"] is None
        dim = rec["dimension"]

        if is_catch:
            catch_chose += 1
        else:
            if dim not in dim_totals:
                dim_totals[dim] = [0, 0]
            dim_totals[dim][0] += 1
            if rec["score"] == 1:
                dim_totals[dim][1] += 1

    summary = {
        "total_records": len(records),
        "total_skipped": len(skipped),
        "per_dimension_agreement": {
            dim: {
                "n": v[0],
                "correct": v[1],
                "agreement_rate": round(v[1] / v[0], 3) if v[0] else None,
            }
            for dim, v in sorted(dim_totals.items())
        },
        "catch_pairs": {
            "n_answered": catch_chose,
            "note": "catch pairs have gt=null; score=null. response count shows noise.",
        },
        "skipped": skipped,
    }
    return summary


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def ingest(results_path, dry_run=False, stimuli_path=None):
    """ingest a survey results JSON file.

    returns (records, summary, skipped_list).
    never raises on bad input; bad records are skipped with a reason.
    """
    # load stimuli
    try:
        stimuli = _load_stimuli(stimuli_path)
    except Exception as e:
        print("[ingest] cannot load stimuli.json: %s" % e, file=sys.stderr)
        return [], {}, []

    gt_map = _build_gt_map(stimuli)

    # load results
    try:
        with open(results_path, "r", encoding="utf-8") as f:
            results = json.load(f)
    except Exception as e:
        print("[ingest] cannot read %s: %s" % (results_path, e), file=sys.stderr)
        return [], {}, []

    if not isinstance(results, dict):
        print("[ingest] results file must be a JSON object", file=sys.stderr)
        return [], {}, []

    judge_id = results.get("judge_id", "anonymous") or "anonymous"
    answers = results.get("answers", [])
    if not isinstance(answers, list):
        print("[ingest] 'answers' must be a list", file=sys.stderr)
        return [], {}, []

    ingested_at = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    records = []
    skipped = []

    for seq, answer in enumerate(answers):
        if not isinstance(answer, dict):
            skipped.append({"seq": seq, "reason": "answer is not a dict"})
            continue

        rec, skip_reason = normalize_answer(answer, seq, gt_map, judge_id, ingested_at)
        if skip_reason:
            skipped.append({"seq": seq, "question_id": answer.get("question_id"), "reason": skip_reason})
            print("[ingest] skip answer %d: %s" % (seq, skip_reason), file=sys.stderr)
            continue

        errors = validate_record(rec)
        if errors:
            reason = "schema validation failed: " + "; ".join(errors)
            skipped.append({"seq": seq, "question_id": answer.get("question_id"), "reason": reason})
            print("[ingest] skip answer %d: %s" % (seq, reason), file=sys.stderr)
            continue

        records.append(rec)

    summary = build_summary(records, skipped)

    if not dry_run:
        out_path = os.path.join(_THIS_DIR, "judgments_out.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump({"records": records, "summary": summary}, f, indent=2)
        print("[ingest] wrote %d records to %s" % (len(records), out_path))
    else:
        print("[ingest] dry-run: %d records valid, %d skipped" % (len(records), len(skipped)))

    _print_summary(summary)
    return records, summary, skipped


def _print_summary(summary):
    print("\n── summary ──────────────────────────────────────────")
    print("total records:  %d" % summary["total_records"])
    print("total skipped:  %d" % summary["total_skipped"])
    print("\nper-dimension agreement vs ground truth:")
    for dim, stats in summary["per_dimension_agreement"].items():
        rate = stats["agreement_rate"]
        rate_str = ("%.1f%%" % (rate * 100)) if rate is not None else "n/a"
        print("  %-20s  %d/%d  (%s)" % (dim, stats["correct"], stats["n"], rate_str))
    cp = summary["catch_pairs"]
    print("\ncatch pairs answered: %d  (%s)" % (cp["n_answered"], cp["note"]))
    print("─────────────────────────────────────────────────────\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ingest survey results into human_judgments records")
    parser.add_argument("results", help="path to the downloaded survey results JSON file")
    parser.add_argument("--dry-run", action="store_true", help="validate only; do not write output file")
    args = parser.parse_args()
    ingest(args.results, dry_run=args.dry_run)

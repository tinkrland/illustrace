"""survey/ingest.py — normalize downloaded survey results into records shaped for
the LIVE xano `judgments` table (id 26; reconciled 2026-09-19 — this used to emit
a "human_judgments" shape for a table that was never actually provisioned).

usage:
    python survey/ingest.py results.json               # normalize + write judgments_out.json
    python survey/ingest.py results.json --dry-run     # validate only, no file written

session_id
----------
derived the same way scripts/sync_judgments.py derives it:
judge_id + started_at (digits only, last 9), so the local ledger and the
remote table agree on session identity without a round-trip.

score (local-only field)
------------------------
1 if the judge's chosen filename matches the ground-truth side, 0 otherwise.
catch pairs (gt == null in stimuli.json) get score = None. `score` is kept on
the record for build_summary() but is NOT a column in the live table — the
xano schema validator ignores extra fields, and scripts/sync_judgments.py
omits it when posting.

validation
----------
every normalized record is passed through xano.schema.validate('judgments').
records that fail validation are skipped with a reason printed to stderr.

output
------
survey/judgments_out.json — {"records": [...], "summary": {...}}
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
            "left_file": os.path.basename(q["left"]),
            "right_file": os.path.basename(q["right"]),
        }
    return gt_map


# ---------------------------------------------------------------------------
# normalization
# ---------------------------------------------------------------------------

def _make_id(seq):
    """simple sequential integer id (1-based) for the output records."""
    return seq + 1


def _session_id(results):
    """derive the session id the same way scripts/sync_judgments.py does."""
    sid = (results.get("judge_id", "anonymous") + "_" +
           str(results.get("started_at", "")).replace(":", "").replace("-", "")[-9:])
    return sid


def normalize_answer(answer, seq, gt_map, judge_id, ingested_at, session_id=""):
    """convert one answer dict into a live-`judgments`-table-shaped record.

    stimulus ids prefer the answer's own left/right file labels and fall back
    to the stimuli.json ground truth (which is authoritative for scoring).
    `score` is a local-only extra field: 1 correct, 0 wrong, None for catch
    pairs. xano's validator ignores extra keys; sync_judgments omits it.

    returns (record_dict, skip_reason_or_None).
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
    score = None if gt_file is None else (1 if chosen == gt_file else 0)

    rec = {
        "id":             _make_id(seq),
        "judge_id":       str(judge_id) if judge_id else "anonymous",
        "dimension":      dimension,
        "stimulus_a_id":  answer.get("left_file") or gt_info["left_file"],
        "stimulus_b_id":  answer.get("right_file") or gt_info["right_file"],
        "chosen":         chosen,
        "confidence":     answer.get("confidence", ""),
        "is_catch_pair":  gt_file is None,
        "noise_flag":     False,
        "reaction_ms":    answer.get("elapsed_ms", 0),
        "session_id":     session_id,
        "question_id":    qid,
        "raw":            answer,
        "score":          score,        # local-only; not a live column
        "created_at":     ingested_at,
    }
    return rec, None


# ---------------------------------------------------------------------------
# validation wrapper
# ---------------------------------------------------------------------------

def validate_record(rec):
    """run xano.schema.validate against the live `judgments` table shape.

    `score` is a local-only extra field (the live table has no such column),
    and None scores on catch pairs are fine — the validator checks only the
    fields it knows and ignores extras.
    """
    return validate("judgments", rec)


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
    session_id = _session_id(results)
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

        rec, skip_reason = normalize_answer(answer, seq, gt_map, judge_id,
                                            ingested_at, session_id=session_id)
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
    parser = argparse.ArgumentParser(description="ingest survey results into live judgments-table records")
    parser.add_argument("results", help="path to the downloaded survey results JSON file")
    parser.add_argument("--dry-run", action="store_true", help="validate only; do not write output file")
    args = parser.parse_args()
    ingest(args.results, dry_run=args.dry_run)

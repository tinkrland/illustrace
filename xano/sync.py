"""xano sync — push results/runs/*.json records to xano via client.post_run.

validates each record against the runs schema before posting. invalid records
are skipped with a warning and reason. tracks synced vs skipped in a summary dict.

usage:
    python -m xano.sync                  # validate + post
    python -m xano.sync --dry-run        # validate only, no network calls
    python -m xano.sync path/to/dir      # custom directory (default: results/runs)

the local json files stay the source of truth; xano is the queryable mirror.
"""
import argparse
import json
import os
import sys

from xano import schema as _schema
from xano import client as _client


_RUNS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "results", "runs",
)


def _load_run_file(path):
    """load a json file and return (record_dict, error_string).

    returns (None, reason) on any parse failure.
    """
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh), None
    except Exception as e:
        return None, "json parse error: %s" % e


def _coerce_run(raw):
    """map the on-disk run format to the runs schema shape.

    on-disk files use 'experiment' (string name) and lack 'experiment_id' /
    'id' since those are assigned by xano on insert. we set sentinel values
    (0) for id and experiment_id so schema presence-checks pass; xano ignores
    id=0 on insert.
    """
    return {
        "id": raw.get("id", 0),
        "experiment_id": raw.get("experiment_id", 0),
        "subject": raw.get("subject", ""),
        "requested": raw.get("requested", raw.get("experiment", "")),
        "params": raw.get("params", raw.get("profiles", {})),
        "metrics": raw.get("metrics", {}),
        "verdict": raw.get("verdict", ""),
        "artifacts": raw.get("artifacts", {}),
        "created_at": raw.get("created_at", raw.get("run_id", "")),
    }


def sync_runs(runs_dir=None, dry_run=False, post_fn=None):
    """scan runs_dir for *.json files, validate, and optionally post to xano.

    args:
        runs_dir: directory to scan (defaults to results/runs next to repo root).
        dry_run:  if True, validate only — no network calls.
        post_fn:  callable(record) -> response; defaults to client.post_run.
                  injectable for testing.

    returns a summary dict:
        {
          "found": int,
          "valid": int,
          "invalid": int,
          "synced": int,       # 0 when dry_run=True
          "skipped_reasons": [(filename, reason), ...],
        }
    """
    if runs_dir is None:
        runs_dir = _RUNS_DIR
    if post_fn is None:
        post_fn = _client.post_run

    summary = {
        "found": 0,
        "valid": 0,
        "invalid": 0,
        "synced": 0,
        "skipped_reasons": [],
    }

    try:
        filenames = sorted(
            f for f in os.listdir(runs_dir) if f.endswith(".json")
        )
    except OSError as e:
        print("[sync] cannot read runs dir %s: %s" % (runs_dir, e))
        return summary

    summary["found"] = len(filenames)

    for fname in filenames:
        path = os.path.join(runs_dir, fname)

        raw, load_err = _load_run_file(path)
        if load_err:
            summary["invalid"] += 1
            summary["skipped_reasons"].append((fname, load_err))
            print("[sync] skip %s — %s" % (fname, load_err))
            continue

        record = _coerce_run(raw)
        errors = _schema.validate("runs", record)

        if errors:
            reason = "; ".join(errors)
            summary["invalid"] += 1
            summary["skipped_reasons"].append((fname, reason))
            print("[sync] skip %s — %s" % (fname, reason))
            continue

        summary["valid"] += 1

        if dry_run:
            print("[sync] dry-run ok: %s" % fname)
            continue

        result = post_fn(record)
        if result is not None:
            summary["synced"] += 1
        else:
            # post_run already printed its own diagnostic
            summary["skipped_reasons"].append((fname, "post_run returned None"))

    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="sync results/runs/*.json to xano (validate + post)"
    )
    parser.add_argument(
        "runs_dir",
        nargs="?",
        default=None,
        help="directory of run json files (default: results/runs)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="validate only — do not post to xano",
    )
    args = parser.parse_args(argv)

    summary = sync_runs(runs_dir=args.runs_dir, dry_run=args.dry_run)

    print("\n[sync] summary:")
    print("  found   : %d" % summary["found"])
    print("  valid   : %d" % summary["valid"])
    print("  invalid : %d" % summary["invalid"])
    print("  synced  : %d" % summary["synced"])
    if summary["skipped_reasons"]:
        print("  skipped :")
        for fname, reason in summary["skipped_reasons"]:
            print("    %s — %s" % (fname, reason))

    return 0 if summary["invalid"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

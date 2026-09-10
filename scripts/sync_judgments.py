#!/usr/bin/env python3
"""sync processed survey sessions to the xano judgments table (idempotent).

usage: python3 scripts/sync_judgments.py [results.json ...]
  - with args: sync only the given session files
  - without: sync everything in survey/processed/ not yet in the remote ledger

idempotence: checks session_id against existing rows; a session already
synced is skipped. judge_id + started_at epoch identify a session.
"""
import json, os, sys, glob, urllib.request

META = "https://xpnx-e4ie-cfuf.z7.xano.io/api:meta"
RUNTIME = "https://xpnx-e4ie-cfuf.z7.xano.io/api:o_C6f1ff"
TOKEN = os.environ.get("XANO_API_TOKEN", "")
CATCH = {"q04", "q07"}

def api(url, payload=None, method=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method,
        headers={"Authorization": "Bearer " + TOKEN, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read() or b"null")

def session_records(path):
    d = json.load(open(path))
    sid = d.get("judge_id", "anonymous") + "_" + d.get("started_at", "").replace(":", "").replace("-", "")[-9:]
    recs = []
    for a in d["answers"]:
        recs.append({
            "judge_id": d["judge_id"], "dimension": a["dimension"],
            "stimulus_a_id": a["left_file"], "stimulus_b_id": a["right_file"],
            "chosen": a["choice"], "confidence": a.get("confidence", ""),
            "is_catch_pair": a["question_id"] in CATCH, "noise_flag": False,
            "reaction_ms": a.get("elapsed_ms", 0), "session_id": sid,
            "question_id": a["question_id"], "raw": a,
        })
    return sid, recs

def main():
    args = sys.argv[1:]
    # only raw survey session exports (skip ledgers and derived judgment files)
    def is_session(f):
        if "ledger" in f or "judgments_" in os.path.basename(f):
            return False
        try:
            return "answers" in json.load(open(f))
        except Exception:
            return False
    files = args or [f for f in glob.glob("survey/processed/*.json") if is_session(f)]
    synced = api(META + "/workspace/1/table/26/content/search?per_page=200", {})
    # search endpoint needs POST body; fallback GET below
    remote_sessions = set()
    try:
        for r in synced.get("items", []):
            remote_sessions.add(r.get("session_id"))
    except AttributeError:
        pass
    for f in files:
        sid, recs = session_records(f)
        if sid in remote_sessions:
            print(f"{os.path.basename(f)}: session {sid} already synced, skipping")
            continue
        resp = api(META + "/workspace/1/table/26/content/bulk", {"items": recs})
        n = len(resp) if isinstance(resp, list) else "?"
        print(f"{os.path.basename(f)}: synced {n} records as session {sid}")

if __name__ == "__main__":
    main()

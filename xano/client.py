"""xano control-plane client. live: posts runs/assets into the stylebench api group.

instance: xpnx-e4ie-cfuf.z7.xano.io
api group: stylebench (canonical o_C6f1ff), mounted at /api:o_C6f1ff
endpoints: POST /runs, GET /runs?experiment=&, GET /run?id=, POST /assets

provisioned 2026-09-08 via the xano metadata api (token: $XANO_API_TOKEN, aud xano:meta).
"""
import json
import os
import urllib.request

BASE = "https://xpnx-e4ie-cfuf.z7.xano.io/api:o_C6f1ff"
TOKEN = os.environ.get("XANO_API_TOKEN", "")


def _call(method, path, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method,
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def post_run(run):
    """run: experiment, subject, requested, params, metrics, verdict, artifacts."""
    try:
        rec = _call("POST", "/runs", run)
        print("[xano] run mirrored, id", rec.get("id"))
        return rec
    except Exception as e:
        print("[xano] post /runs failed (local json is source of truth):", e)
        return None


def post_asset(asset):
    """asset: kind, name, file_url, style_profile."""
    try:
        rec = _call("POST", "/assets", asset)
        print("[xano] asset mirrored, id", rec.get("id"))
        return rec
    except Exception as e:
        print("[xano] post /assets failed:", e)
        return None


def get_run(rid):
    return _call("GET", "/run?id=%d" % rid)


def list_runs(experiment=None):
    return _call("GET", "/runs" + ("?experiment=" + experiment if experiment else ""))

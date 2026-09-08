"""xano control-plane client. live: posts runs/assets into the stylebench api group.

instance: xpnx-e4ie-cfuf.z7.xano.io
api group: stylebench (canonical o_C6f1ff), mounted at /api:o_C6f1ff
endpoints: POST /runs, GET /runs?experiment=&, GET /run?id=, POST /assets

provisioned 2026-09-08 via the xano metadata api (token: $XANO_API_TOKEN, aud xano:meta).

metadata api: https://api.xano.com/api:meta  (bearer $XANO_API_TOKEN, aud xano:meta)
  list_instances()                         GET  /api:meta/instance
  list_workspaces(instance_id)             GET  /api:meta/workspace
  list_branches(instance_id, workspace_id) GET  /api:meta/workspace/{workspace_id}/branch
  export_workspace(...)                    GET  /api:meta/workspace/{workspace_id}/export
"""
import json
import os
import urllib.request
import urllib.error

BASE = "https://xpnx-e4ie-cfuf.z7.xano.io/api:o_C6f1ff"
META_BASE = "https://api.xano.com"
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


# ---------------------------------------------------------------------------
# metadata api — all calls fail-soft (return None or [] on any error)
# ---------------------------------------------------------------------------

def meta_call(method, path, payload=None):
    """call the xano metadata api at META_BASE + path with bearer $XANO_API_TOKEN.

    returns the parsed json body on success, or None on any error (network,
    auth, parse). prints a one-line diagnostic so callers don't silently wonder.
    """
    token = os.environ.get("XANO_API_TOKEN", TOKEN)
    data = json.dumps(payload).encode() if payload is not None else None
    headers = {
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json",
    }
    req = urllib.request.Request(
        META_BASE + path, data=data, method=method, headers=headers
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        print("[xano meta] %s %s -> HTTP %s" % (method, path, e.code))
        return None
    except urllib.error.URLError as e:
        print("[xano meta] %s %s -> network error: %s" % (method, path, e.reason))
        return None
    except Exception as e:
        print("[xano meta] %s %s -> error: %s" % (method, path, e))
        return None


def list_instances():
    """return a list of xano instance records for the authed account, or []."""
    result = meta_call("GET", "/api:meta/instance")
    if result is None:
        return []
    # api returns either a list or {"items": [...]}
    if isinstance(result, list):
        return result
    if isinstance(result, dict):
        return result.get("items", result.get("instances", []))
    return []


def list_workspaces(instance_id):
    """return a list of workspace records for the given instance, or []."""
    result = meta_call("GET", "/api:meta/workspace")
    if result is None:
        return []
    if isinstance(result, list):
        return result
    if isinstance(result, dict):
        return result.get("items", result.get("workspaces", []))
    return []


def list_branches(instance_id, workspace_id):
    """return a list of branch records for the given workspace, or []."""
    result = meta_call("GET", "/api:meta/workspace/%s/branch" % workspace_id)
    if result is None:
        return []
    if isinstance(result, list):
        return result
    if isinstance(result, dict):
        return result.get("items", result.get("branches", []))
    return []


def export_workspace(instance_id, workspace_id, branch="main"):
    """return the workspace export payload (dict) for the given branch, or None."""
    path = "/api:meta/workspace/%s/export?branch=%s" % (workspace_id, branch)
    return meta_call("GET", path)

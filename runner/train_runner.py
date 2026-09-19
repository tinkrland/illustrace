#!/usr/bin/env python3
"""the gpu runner: claims style-lora jobs from the xano training_jobs queue
and trains them with kohya sd-scripts (flux.1 [dev]).

pull model, box holds no state: poll queued -> claim -> train -> post
results. written for the gcp a100 box (a2-ultragpu-1g, cuda) but the box
itself doesn't matter, any linux gpu host with the env below works, amd's
mi300x included. the text-model fine-tunes go the other way entirely
(llm/lora_train.py --backend nebius); this runner is the image-side path.

contract (research/AMD_DEVELOPER_CLOUD.md, verified 2026-09-11):
- GET  {xano}/training_jobs_list?status=queued   -> rows, claim lowest id
- POST {xano}/training_jobs_update               -> {id, secret, status,
  metrics?, params?, artifact_uri?, gpu_hours}; allowed transitions are
  running|done|failed only, the runner can never rewind the ledger.

env the box needs:
    ILLUSTRACE_RUNNER_SECRET   shared secret with the update endpoint
    RUNNER_KOHYA_DIR           sd-scripts checkout (flux_train_network.py)
    RUNNER_FLUX_DIR            flux.1-dev weights dir (flux1-dev.safetensors,
                               clip_l.safetensors, t5xxl_fp16.safetensors,
                               ae.safetensors)
    RUNNER_OUT_DIR             adapters land here (default ./adapters)
    RUNNER_GCS_BUCKET          optional gs://bucket -> adapter uploaded,
                               artifact_uri is the gs url; else local path

job row fields used: job_type ("lora"; "fitter" stays queued for now, the
fitter trainer isn't written and we don't fake it), dataset_ref (kohya
dataset dir, packaged by engine/package_dataset.py), params (trigger,
dim, alpha, lr, epochs, repeats, batch, save_every, all optional, the
defaults are the preregistered v0 spec in research/DATASET_PACKAGING.md).

usage:
    python3 runner/train_runner.py --once      # one job, then exit
    python3 runner/train_runner.py             # loop, poll every 5 min
    python3 runner/train_runner.py --dry-run   # show the command, no
                                                # claim, no xano calls
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))

# xano runtime endpoints (public, no auth; the secret only gates updates)
XANO_BASE = os.environ.get("RUNNER_XANO_BASE",
                           "https://xpnx-e4ie-cfuf.z7.xano.io/api:o_C6f1ff")

# defaults = the preregistered v0 spec (research/DATASET_PACKAGING.md,
# glm-5.2 critique pass folded in). dim=alpha=16, no cropping, bucket
# 768-1024, caption_dropout 0.1, save every 2 epochs.
V0_DEFAULTS = {
    "trigger": "mzqtlv",
    "dim": 16,
    "alpha": 16,
    "lr": 1e-4,
    "epochs": 16,
    "repeats": 3,
    "batch": 1,
    "save_every": 2,
}


# ---------------------------------------------------------------------------
# xano transport
# ---------------------------------------------------------------------------

def xano_get(path, params=None):
    url = XANO_BASE + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read() or b"null")


def xano_post(path, payload):
    req = urllib.request.Request(
        XANO_BASE + path, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read() or b"null")


def list_queued(job_type=None):
    rows = xano_get("/training_jobs_list", {"status": "queued"})
    if isinstance(rows, dict):
        rows = rows.get("data") or rows.get("jobs") or []
    if job_type:
        rows = [r for r in rows if r.get("job_type") == job_type]
    return sorted(rows, key=lambda r: r.get("id", 0))


def update_job(job_id, status, secret, metrics=None, params=None,
               artifact_uri=None, gpu_hours=None):
    return xano_post("/training_jobs_update", {
        "id": job_id, "secret": secret, "status": status,
        "metrics": metrics, "params": params,
        "artifact_uri": artifact_uri, "gpu_hours": gpu_hours})


# ---------------------------------------------------------------------------
# kohya command construction (pure, testable)
# ---------------------------------------------------------------------------

def job_params(job):
    """merge the v0 defaults with the job row's params json."""
    p = dict(V0_DEFAULTS)
    pj = job.get("params") or {}
    if isinstance(pj, str):
        pj = json.loads(pj)
    p.update({k: v for k, v in pj.items() if v is not None})
    return p


def dataset_toml(dataset_ref, p):
    """kohya dataset config: bucketing 768-1024, no cropping, caption
    dropout so style absorbs into the trigger (all per the v0 spec)."""
    meta = os.path.join(dataset_ref, "metadata.jsonl")
    return f"""[general]
shuffle_caption = true
caption_extension = ".txt"

[[datasets]]
batch_size = {p['batch']}
enable_bucket = true
min_bucket_reso = 768
max_bucket_reso = 1024
caption_dropout_rate = 0.1

  [[datasets.subsets]]
  image_dir = "{os.path.abspath(dataset_ref)}"
  metadata_file = "{os.path.abspath(meta)}"
  num_repeats = {p['repeats']}
"""


def build_kohya_cmd(job, kohya_dir, flux_dir, out_dir, cfg_path):
    """flux_train_network.py with the flux.1-dev flags verified from the
    sd-scripts docs (2026-09-10): timestep_sampling shift,
    discrete_flow_shift 3.1582, model_prediction_type raw, guidance 1.0."""
    p = job_params(job)
    name = f"{p['trigger']}_{os.path.basename(job.get('dataset_ref', 'job'))}"
    cmd = [
        "accelerate", "launch",
        "--num_cpu_threads_per_process", "2",
        os.path.join(kohya_dir, "flux_train_network.py"),
        "--pretrained_model_name_or_path", os.path.join(flux_dir, "flux1-dev.safetensors"),
        "--clip_l", os.path.join(flux_dir, "clip_l.safetensors"),
        "--t5xxl", os.path.join(flux_dir, "t5xxl_fp16.safetensors"),
        "--ae", os.path.join(flux_dir, "ae.safetensors"),
        "--dataset_config", cfg_path,
        "--output_dir", out_dir,
        "--output_name", name,
        "--network_module", "networks.lora_flux",
        "--network_dim", str(p["dim"]),
        "--network_alpha", str(p["alpha"]),
        "--learning_rate", str(p["lr"]),
        "--max_train_epochs", str(p["epochs"]),
        "--save_every_n_epochs", str(p["save_every"]),
        "--timestep_sampling", "shift",
        "--discrete_flow_shift", "3.1582",
        "--model_prediction_type", "raw",
        "--guidance_scale", "1.0",
        "--mixed_precision", "bf16",
        "--save_precision", "bf16",
        "--cache_latents_to_disk",
        "--cache_text_encoder_outputs_to_disk",
        "--persistent_data_loader_workers",
    ]
    return cmd, name


# ---------------------------------------------------------------------------
# runner loop
# ---------------------------------------------------------------------------

def run_one(job, secret, dry_run=False):
    kohya_dir = os.environ["RUNNER_KOHYA_DIR"]
    flux_dir = os.environ["RUNNER_FLUX_DIR"]
    out_dir = os.environ.get("RUNNER_OUT_DIR",
                             os.path.join(HERE, "..", "adapters"))
    dataset_ref = job["dataset_ref"]
    if not os.path.isdir(dataset_ref):
        raise SystemExit(f"error: dataset_ref {dataset_ref} not on this box "
                         "(package first: engine/package_dataset.py)")

    fd, cfg_path = tempfile.mkstemp(suffix=".toml")
    with os.fdopen(fd, "w") as f:
        f.write(dataset_toml(dataset_ref, job_params(job)))
    cmd, name = build_kohya_cmd(job, kohya_dir, flux_dir, out_dir, cfg_path)

    print("[job]", job["id"], "lora:", " ".join(cmd[:6]), "...")
    if dry_run:
        print("[dry-run] full command:")
        print("  " + " ".join(cmd))
        print("[dry-run] dataset config at", cfg_path)
        return None

    t0 = time.time()
    update_job(job["id"], "running", secret)
    try:
        r = subprocess.run(cmd, check=True, text=True,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        wall_h = (time.time() - t0) / 3600.0
        adapter = os.path.join(out_dir, name + ".safetensors")
        uri = store_artifact(adapter, name)
        metrics = {"wall_hours": round(wall_h, 3),
                   "last_epoch_log": r.stdout.strip().splitlines()[-1][:300]}
        update_job(job["id"], "done", secret, metrics=metrics,
                   artifact_uri=uri, gpu_hours=round(wall_h, 3))
        print("[job]", job["id"], "done:", uri)
        return uri
    except subprocess.CalledProcessError as e:
        err = (e.stdout or "")[-1500:]
        update_job(job["id"], "failed", secret,
                   metrics={"error_tail": err})
        print("[job]", job["id"], "FAILED, posted to ledger", file=sys.stderr)
        raise
    finally:
        os.unlink(cfg_path)


def store_artifact(adapter_path, name):
    """copy the adapter to $RUNNER_GCS_BUCKET if set, else report the path."""
    bucket = os.environ.get("RUNNER_GCS_BUCKET")
    if not bucket:
        return adapter_path
    dst = f"gs://{bucket}/{name}_{int(time.time())}.safetensors"
    subprocess.run(["gsutil", "cp", adapter_path, dst], check=True)
    return dst


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--once", action="store_true", help="claim one job, exit")
    ap.add_argument("--poll-interval", type=int, default=300)
    ap.add_argument("--dry-run", action="store_true",
                    help="print the kohya command, touch nothing")
    ap.add_argument("--types", default="lora",
                    help="comma list of job_types this box accepts "
                         "(default lora; fitter trainer not written yet)")
    args = ap.parse_args()

    if args.dry_run:
        os.environ.setdefault("RUNNER_KOHYA_DIR", "/opt/sd-scripts")
        os.environ.setdefault("RUNNER_FLUX_DIR", "/opt/flux1-dev")
        try:
            queued = list_queued()
        except Exception as e:  # offline: dry-run should still show the cmd
            print(f"[dry-run] queue unreachable ({type(e).__name__}), sample job")
            queued = []
        if not queued:
            print("[dry-run] no queued jobs, using a sample v0 monet job")
            queued = [{"id": 0, "job_type": "lora",
                       "dataset_ref": "data/kohya/monet", "params": {}}]
        shown = False
        for t in args.types.split(","):
            for job in [j for j in queued if j["job_type"] == t]:
                run_one(job, secret="dry", dry_run=True)
                shown = True
        if not shown:
            print(f"[dry-run] no queued jobs of type {args.types} "
                  f"({len(queued)} queued of other types); a sample v0 job:")
            run_one({"id": 0, "job_type": "lora",
                     "dataset_ref": "data/kohya/monet", "params": {}},
                    secret="dry", dry_run=True)
        return

    secret = os.environ.get("ILLUSTRACE_RUNNER_SECRET")
    if not secret:
        raise SystemExit("error: ILLUSTRACE_RUNNER_SECRET not set")
    types = [t.strip() for t in args.types.split(",")]

    while True:
        for t in types:
            queued = [j for j in list_queued() if j["job_type"] == t]
            if not queued:
                continue
            job = queued[0]  # lowest id, already sorted
            print(f"[poll] claiming job {job['id']} ({job['job_type']}, "
                  f"{job.get('dataset_ref')})")
            run_one(job, secret)
            if args.once:
                return
        if args.once:
            print("[poll] nothing claimable; exiting (--once)")
            return
        time.sleep(args.poll_interval)


if __name__ == "__main__":
    main()

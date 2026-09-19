# runner, the gpu box for style-lora jobs

pull-model runner: claims `job_type=lora` jobs from the xano
`training_jobs` queue, trains them with kohya sd-scripts (flux.1 [dev]),
posts results back. the box holds no state; the ledger is xano's.
written for gcp's a100 but the code doesn't care, any linux gpu host
with the env vars set works (the amd mi300x too, if it ever unblocks).

## the box (gcp, decided 2026-09-19)

| thing | choice | why |
|---|---|---|
| machine | `a2-ultragpu-1g` (1x A100 80GB) | flux lora needs 16-24GB; 80GB fits batch experiments. cuda means kohya runs as-is, no rocm port |
| pricing | spot (~$2.30/hr) | jobs are short (1.5-2h per painter lora) and checkpoint every 2 epochs; spot eviction loses at most one epoch |
| image | deep learning vm: pytorch + cuda 12.x | accelerate/kohya run on top of it |
| region | us-central1 | best a2 availability |

budget context: $100 in credits. the whole three-painter library
(monet, van gogh, hokusai) is ~6 gpu-hours ≈ $14 on spot; the rest of
the budget is probe-generation passes and the fx fitter experiments
(small cnns, minutes each). the text models don't touch this budget at
all, they fine-tune on nebius (`llm/lora_train.py --backend nebius`).

## one-time box setup (after ssh)

```sh
# 1. tools + kohya
sudo apt-get update && sudo apt-get install -y git python3.11-venv jq
git clone https://github.com/kohya-ss/sd-scripts /opt/sd-scripts
python3 -m venv /opt/sd-scripts/venv && source /opt/sd-scripts/venv/bin/activate
pip3 install -r /opt/sd-scripts/requirements.txt
pip3 install accelerate

# 2. flux.1 [dev] weights (hf token needed, non-commercial license)
mkdir /opt/flux1-dev
huggingface-cli download black-forest-labs/FLUX.1-dev \
  flux1-dev.safetensors clip_l.safetensors t5xxl_fp16.safetensors ae.safetensors \
  --local-dir /opt/flux1-dev

# 3. the repo + the packaged dataset
git clone https://github.com/tinkrland/illustrace /opt/illustrace
cd /opt/illustrace
python3 engine/package_dataset.py monet   # writes data/kohya/monet
python3 engine/package_dataset.py validate monet   # gate: profile must
                                                   # equal the corpus target

# 4. env
export ILLUSTRACE_RUNNER_SECRET=...        # the shared secret
export RUNNER_KOHYA_DIR=/opt/sd-scripts
export RUNNER_FLUX_DIR=/opt/flux1-dev
export RUNNER_OUT_DIR=/opt/illustrace/adapters
export RUNNER_GCS_BUCKET=illustrace-adapters   # optional; gsutil needed

# 5. go
python3 runner/train_runner.py --dry-run   # show the command, claim nothing
python3 runner/train_runner.py --once      # one job
python3 runner/train_runner.py             # loop (tmux/systemd)
```

## queueing a job (from anywhere)

the queue side is the xano api, a lora job is one row:

```sh
curl -X POST https://xpnx-e4ie-cfuf.z7.xano.io/api:o_C6f1ff/training_jobs_ingest \
  -H 'Content-Type: application/json' -d '{
    "job_type": "lora", "status": "queued", "hardware": "a100",
    "dataset_ref": "/opt/illustrace/data/kohya/monet",
    "params": {"trigger": "mzqtlv", "epochs": 16}
  }'
```

`params` is optional: the runner's defaults are the preregistered v0
spec (dim/alpha 16, lr 1e-4, epochs 16, repeats 3, batch 1, save every 2
epochs, no cropping, bucket 768-1024, caption dropout 0.1, see
[research/DATASET_PACKAGING.md](../research/DATASET_PACKAGING.md) for
why each value is what it is).

## what the runner does per job

1. `GET training_jobs_list?status=queued` → lowest-id lora job
2. `POST training_jobs_update` → status `running` (shared secret; the
   endpoint only allows running|done|failed, so the ledger can't rewind)
3. kohya `flux_train_network.py` with the v0 flags
   (timestep_sampling shift, discrete_flow_shift 3.1582,
   model_prediction_type raw, guidance 1.0)
4. on success: `done` + `artifact_uri` (gs:// or local path) +
   `gpu_hours`; on crash: `failed` + error tail in `metrics`

fitter jobs (`job_type=fitter`) stay queued: the fitter trainer isn't
written and the runner doesn't fake capability it doesn't have.

## after training: the probe

an adapter isn't done until [engine/adapter_probe.py](../engine/adapter_probe.py)
scores it: holdout fidelity (mean palette dE < 10 vs the training
profile) and leakage (unclaimed components vs the untrained-flux
floor). promotion rules live in the packaging spec; the probe runs on
this workspace, not the box.

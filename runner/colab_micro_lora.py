#!/usr/bin/env python3
"""colab micro-lora: train a 10-20 image style adapter on a free-session
gpu (t4/l4) so the whole learned pipeline (packaging -> kohya -> adapter
-> probe) is debugged before the first a100 run. see
research/MICRO_LORA_PROBES.md for the rationale.

run inside a colab cell (gpu runtime):

    !git clone https://github.com/tinkrland/illustrace /content/illustrace
    from google.colab import files
    up = files.upload()                     # the corpus zip (pop lane)
    !unzip -q {list(up)[0]} -d /content/illustrace/data/micro/storefronts
    %env HF_TOKEN=hf_...        # from an account that accepted the
                                 # flux.1-dev license
    !python /content/illustrace/runner/colab_micro_lora.py

the corpus ships as a zip upload, not via the repo: living-artist
references stay out of the public repo (see research/MICRO_LORA_PROBES.md).

expects the dataset at DATASET_DIR: images + one caption .txt per image
(same stem). if metadata.jsonl is missing it is built on the fly.
adapters land in OUT_DIR, zipped at the end (drive mounted -> drive,
else /content). nothing here is committed or published: probes on
living-artist references are internal only (see the research note).
"""
import json
import os
import shutil
import subprocess
import sys
import time

# --- config ------------------------------------------------------------
# two micro-corpora, same pipeline: "contemporary_pop" (already packaged)
# and "digital_watercolor" (captions pending). the cell sets the lane via
# env vars: %env DATASET_DIR=... %env TRIGGER=... -- defaults are the pop
# lane so old cells keep working.
DATASET_DIR = os.environ.get(
    "DATASET_DIR", "/content/illustrace/data/micro/contemporary_pop")
OUT_DIR = ("/content/drive/MyDrive/illustrace_adapters"
           if os.path.isdir("/content/drive/MyDrive") else "/content/adapters")
KOHYA_DIR = "/content/sd-scripts"
WEIGHTS_DIR = "/content/flux1-dev"
TRIGGER = os.environ.get("TRIGGER", "skrfrnt")  # per-lane, no english subword
EPOCHS = 10             # micro corpus: imgs x repeats x epochs
REPEATS = 3             # = 450 steps, 1.5-2.5h on a t4
SAVE_EVERY = 2
LR = 1e-4
DIM = ALPHA = 16        # alpha=dim, per the critique fix in the v0 spec
# -----------------------------------------------------------------------


def sh(cmd):
    print("+", " ".join(cmd))
    if subprocess.run(cmd).returncode != 0:
        raise SystemExit(f"step failed: {' '.join(cmd)}")
    return 0


def check_gpu():
    r = subprocess.run("nvidia-smi --query-gpu=name,memory.total --format=csv,noheader",
                       shell=True, capture_output=True, text=True)
    print("gpu:", r.stdout.strip() or "NONE")
    if not r.stdout.strip():
        raise SystemExit("no gpu: switch the runtime to a t4/l4 before running")


def setup_kohya():
    train_script = os.path.join(KOHYA_DIR, "flux_train_network.py")
    if os.path.isdir(KOHYA_DIR) and os.path.exists(train_script):
        print("kohya present")
    else:
        # partial clone from a crashed run: clear it out, start over
        if os.path.isdir(KOHYA_DIR):
            print("partial sd-scripts found, recloning")
            shutil.rmtree(KOHYA_DIR)
        sh(["git", "clone", "--depth", "1",
            "https://github.com/kohya-ss/sd-scripts", KOHYA_DIR])
    # pip runs every time (idempotent, fast when already satisfied):
    # an interrupted install must heal on rerun, not be skipped.
    # requirements.txt ends in "-e ." (installs sd-scripts itself as an
    # editable package) -- pip only resolves that relative to cwd, so it
    # must run from inside KOHYA_DIR, not /content
    cwd = os.getcwd()
    os.chdir(KOHYA_DIR)
    try:
        sh(["pip", "install", "-q", "-r", "requirements.txt"])
    finally:
        os.chdir(cwd)
    sh(["pip", "install", "-q", "accelerate"])


def fetch_weights():
    want = ["flux1-dev.safetensors", "clip_l.safetensors",
            "t5xxl_fp16.safetensors", "ae.safetensors"]
    if all(os.path.exists(os.path.join(WEIGHTS_DIR, w)) for w in want):
        print("weights present")
        return
    os.makedirs(WEIGHTS_DIR, exist_ok=True)
    tok = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
    env = dict(os.environ, HF_TOKEN=tok) if tok else None
    if env is None:
        raise SystemExit("HF_TOKEN not set: flux.1-dev is license-gated, "
                         "accept the license on hf and pass a token")
    sh(["huggingface-cli", "download", "black-forest-labs/FLUX.1-dev",
        *want, "--local-dir", WEIGHTS_DIR])


def build_metadata():
    """kohya metadata.jsonl from per-image caption files, if absent."""
    meta = os.path.join(DATASET_DIR, "metadata.jsonl")
    imgs = [f for f in sorted(os.listdir(DATASET_DIR))
            if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))]
    if not imgs:
        raise SystemExit(f"no images in {DATASET_DIR} (see the note in "
                         "research/MICRO_LORA_PROBES.md about the dataset)")
    if os.path.exists(meta):
        return
    lines = []
    for img in imgs:
        cap_file = os.path.splitext(img)[0] + ".txt"
        cap_path = os.path.join(DATASET_DIR, cap_file)
        if not os.path.exists(cap_path):
            raise SystemExit(f"missing caption for {img}: write {cap_file} "
                             'as "<trigger>, a painting of <subject>"')
        cap = open(cap_path).read().strip()
        if not cap.startswith(TRIGGER):
            raise SystemExit(f"caption for {img} does not start with "
                             f"trigger {TRIGGER}")
        lines.append(json.dumps({"image_path": img, "caption": cap}))
    with open(meta, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"metadata: {len(imgs)} images -> {meta}")


def train():
    cfg_path = os.path.join(DATASET_DIR, "micro_dataset.toml")
    with open(cfg_path, "w") as f:
        f.write(f"""[general]
shuffle_caption = true
caption_extension = ".txt"

[[datasets]]
batch_size = 1
enable_bucket = true
min_bucket_reso = 768
max_bucket_reso = 1024
caption_dropout_rate = 0.1

  [[datasets.subsets]]
  image_dir = "{os.path.abspath(DATASET_DIR)}"
  metadata_file = "{os.path.join(DATASET_DIR, 'metadata.jsonl')}"
  num_repeats = {REPEATS}
""")
    os.makedirs(OUT_DIR, exist_ok=True)
    cmd = ["accelerate", "launch",
           "--num_cpu_threads_per_process", "2",
           os.path.join(KOHYA_DIR, "flux_train_network.py"),
           "--pretrained_model_name_or_path",
           os.path.join(WEIGHTS_DIR, "flux1-dev.safetensors"),
           "--clip_l", os.path.join(WEIGHTS_DIR, "clip_l.safetensors"),
           "--t5xxl", os.path.join(WEIGHTS_DIR, "t5xxl_fp16.safetensors"),
           "--ae", os.path.join(WEIGHTS_DIR, "ae.safetensors"),
           "--dataset_config", cfg_path,
           "--output_dir", OUT_DIR,
           "--output_name", f"{TRIGGER}_micro",
           "--network_module", "networks.lora_flux",
           "--network_dim", str(DIM), "--network_alpha", str(ALPHA),
           "--learning_rate", str(LR),
           "--max_train_epochs", str(EPOCHS),
           "--save_every_n_epochs", str(SAVE_EVERY),
           "--timestep_sampling", "shift",
           "--discrete_flow_shift", "3.1582",
           "--model_prediction_type", "raw",
           "--guidance_scale", "1.0",
           "--fp8_base",                      # 12b in a 16gb t4
           "--mixed_precision", "fp16",        # t4 has no bf16
           "--save_precision", "fp16",
           "--cache_latents_to_disk",
           "--cache_text_encoder_outputs_to_disk",
           "--persistent_data_loader_workers",
           # colab t4: ~15GB vram but only ~12GB system RAM. without
           # --lowram, kohya loads the 23.8GB flux checkpoint through
           # host RAM before moving it to the gpu and gets OOM-killed
           # with no traceback (silent death, exactly what happened on
           # the first live run). --lowram loads straight to vram
           # instead. blocks_to_swap is a small vram safety margin on
           # top of that.
           "--lowram",
           "--blocks_to_swap", "8"]
    t0 = time.time()
    if subprocess.run(cmd).returncode != 0:
        raise SystemExit("kohya failed: scroll up for the log; nothing "
                         "zipped, checkpoints every "
                         f"{SAVE_EVERY} epochs survive in {OUT_DIR}")
    print(f"wall: {(time.time()-t0)/3600:.2f} gpu-hours")


def package_out():
    import glob
    stamp = time.strftime("%Y%m%d_%H%M")
    zips = sh(["zip", "-q", "-j",
               f"{OUT_DIR}/{TRIGGER}_micro_{stamp}.zip"]
              + glob.glob(os.path.join(OUT_DIR, f"{TRIGGER}_micro*.safetensors")))
    print("adapter zip:", f"{OUT_DIR}/{TRIGGER}_micro_{stamp}.zip")
    if OUT_DIR.startswith("/content/drive"):
        print("saved to drive: it survives the session")
    else:
        print("colab may wipe /content: download the zip now, or mount "
              "drive (from google.colab import drive; "
              "drive.mount('/content/drive')) and rerun")


if __name__ == "__main__":
    check_gpu()
    setup_kohya()
    fetch_weights()
    build_metadata()
    train()
    package_out()

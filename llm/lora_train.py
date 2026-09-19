"""fine-tune runner for illustrace's spec/judge models, two backends.

- backend `local`: qlora on the amd mi300x box (rocm pytorch + peft). the
  original path; also the only path for anything image-side (not this script).
- backend `nebius`: tokenfactory post-training (openai-compatible, verified
  live 2026-09-19 after we fixed three of our own bugs, exact whitelist
  model id, full chat-format jsonl ending in an assistant turn, and explicit
  hyperparameters, because the default batch_size trips an uncaught
  batch*context < 32768 tokens check that 500s instead of 422ing).
  whitelist: https://docs.tokenfactory.nebius.com/post-training/models

consumes the openai-format jsonl exported by llm/export_traces.py (langsmith
traces -> training pairs, so the corpus survives the langsmith access window)
plus, later, judgment records from the xano control plane.

two targets, same script:
- spec drafts: traces of glm-5.2 spec passes -> a model that drafts
  preregistration specs in illustrace's house style
- judge model (later): human 2afc judgments (xano `judgments` table) -> a
  model that reproduces expert verdicts

usage (nebius, works from anywhere with the key):
    python3 llm/lora_train.py --backend nebius \
        --data data/generated/ft/spec_drafts.openai.jsonl \
        --base meta-llama/Llama-3.1-8B-Instruct --epochs 3

usage (nebius, poll an existing job instead of creating one):
    python3 llm/lora_train.py --backend nebius --job-id ftjob-...

usage (on the mi300x box):
    python3 llm/lora_train.py --backend local --data ... --epochs 3

usage (here, no gpu, no network):
    python3 llm/lora_train.py --data ... --dry-run   # validates dataset only

notes:
- nebius fine-tuning is TEXT-ONLY. the flux image-style loras (monet et al)
  still need the amd box (kohya). this runner is for the spec/judge models.
- the local default base is Llama-3.3-70B-Instruct (mi300x-sized); for
  nebius with today's tiny corpus, Llama-3.1-8B-Instruct is the sensible
  default, flag is explicit either way.
"""
import argparse
import json
import os
import sys
import time
import urllib.request

NEBIUS_BASE = "https://api.tokenfactory.nebius.com/v1"
NEBIUS_MODELS_DOC = "https://docs.tokenfactory.nebius.com/post-training/models"

# sanity list only (not a hard gate, the catalog moves; the docs page is
# the source of truth, and the api's own 422s catch the rest)
NEBIUS_KNOWN_MODELS = [
    "meta-llama/Llama-3.1-8B-Instruct",
    "meta-llama/Llama-3.1-70B-Instruct",
    "meta-llama/Llama-3.3-70B-Instruct",
    "meta-llama/Llama-3.2-3B-Instruct",
    "unsloth/gpt-oss-20b-BF16",
    "unsloth/gpt-oss-120b-BF16",
    "Qwen/Qwen3-32B",
    "Qwen/Qwen3-235B-A22B",
]

# tokenfactory constraint: batch_size * context_length must be >= 32768
NEBIUS_MIN_BATCH_TOKENS = 32768


# ---------------------------------------------------------------------------
# dataset validation (shared by both backends)
# ---------------------------------------------------------------------------

def validate_dataset(path):
    """check the jsonl is loadable openai chat format; return (n, roles_ok, bad)."""
    n, roles_ok, bad = 0, True, 0
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            n += 1
            try:
                d = json.loads(line)
                msgs = d["messages"]
                if msgs[-1]["role"] != "assistant":
                    roles_ok = False
                if not all(m.get("content") for m in msgs):
                    bad += 1
            except Exception:
                bad += 1
    return n, roles_ok, bad


# ---------------------------------------------------------------------------
# nebius backend (tokenfactory post-training)
# ---------------------------------------------------------------------------

def nebius_key():
    """accept $NEBIUS_API_KEY, else assemble v1.$NEBIUS_TOKEN_ID.$NEBIUS_TOKEN_SECRET."""
    if os.environ.get("NEBIUS_API_KEY"):
        return os.environ["NEBIUS_API_KEY"]
    tid, sec = os.environ.get("NEBIUS_TOKEN_ID", ""), os.environ.get("NEBIUS_TOKEN_SECRET", "")
    if tid and sec:
        return "v1." + tid.strip() + "." + sec.strip()
    raise SystemExit("error: no nebius key (set NEBIUS_API_KEY or "
                     "NEBIUS_TOKEN_ID/NEBIUS_TOKEN_SECRET)")


def nebius_api(path, payload=None, method=None):
    """one json call against tokenfactory; returns parsed body or exits."""
    url = NEBIUS_BASE + path
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method,
                                  headers={"Authorization": "Bearer " + nebius_key(),
                                           "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")[:300]
        raise SystemExit(f"error: nebius {e.code} on {path}: {body}")


def build_hyperparameters(args, context_length=8192):
    """map cli args to tokenfactory hyperparameters, enforcing the batch floor.

    tokenfactory requires batch_size * context_length >= 32768 tokens; the
    default batch trips an UNCAUGHT version of this check that 500s, so we
    compute the floor ourselves and fail with a real message instead.
    """
    batch = max(args.batch, 1)
    if batch * context_length < NEBIUS_MIN_BATCH_TOKENS:
        batch = -(-NEBIUS_MIN_BATCH_TOKENS // context_length)  # ceil
        print(f"[nebius] batch {args.batch} under the {NEBIUS_MIN_BATCH_TOKENS}-token "
              f"batch floor at ctx {context_length}; raising to {batch}")
    return {
        "batch_size": batch,
        "learning_rate": args.lr if args.lr else 1e-5,
        "n_epochs": args.epochs,
        "lora": True,
        "lora_r": args.rank,
        "lora_alpha": args.rank * 2,
        "lora_dropout": 0.05,
        "packing": True,
        "context_length": context_length,
    }


def nebius_upload(data_path):
    """upload the jsonl with purpose=fine-tune (multipart); return file id."""
    boundary = "illustrace-" + str(int(time.time()))
    with open(data_path, "rb") as f:
        body = f.read()
    parts = (
        ("--%s\r\nContent-Disposition: form-data; name=\"purpose\"\r\n\r\n"
         "fine-tune\r\n" % boundary).encode() +
        ("--%s\r\nContent-Disposition: form-data; name=\"file\"; "
         "filename=\"%s\"\r\nContent-Type: application/jsonl\r\n\r\n" %
         (boundary, os.path.basename(data_path))).encode() +
        body + ("\r\n--%s--\r\n" % boundary).encode())
    req = urllib.request.Request(
        NEBIUS_BASE + "/files", data=parts, method="POST",
        headers={"Authorization": "Bearer " + nebius_key(),
                 "Content-Type": "multipart/form-data; boundary=" + boundary})
    with urllib.request.urlopen(req, timeout=120) as r:
        out = json.loads(r.read())
    print("[nebius] uploaded", out.get("id"), f"({out.get('bytes')} bytes)")
    return out["id"]


def nebius_download_checkpoint_files(job_id, out_root):
    """list checkpoints for a succeeded job and download their files."""
    cps = nebius_api(f"/fine_tuning/jobs/{job_id}/checkpoints")
    saved = []
    for cp in cps.get("data", []):
        cp_dir = os.path.join(out_root, cp["id"])
        os.makedirs(cp_dir, exist_ok=True)
        for fid in cp.get("result_files", []):
            meta = nebius_api(f"/files/{fid}")
            dest = os.path.join(cp_dir, os.path.basename(meta.get("filename") or fid))
            req = urllib.request.Request(
                NEBIUS_BASE + f"/files/{fid}/content",
                headers={"Authorization": "Bearer " + nebius_key()})
            with urllib.request.urlopen(req, timeout=300) as r, open(dest, "wb") as f:
                f.write(r.read())
            saved.append(dest)
            print("[nebius] saved", dest)
    return saved


def nebius_run(args, n):
    """upload -> create job -> poll -> download checkpoints. returns job dict."""
    if args.base not in NEBIUS_KNOWN_MODELS:
        print(f"[nebius] note: {args.base} not on my sanity list, if the "
              f"api 422s, check {NEBIUS_MODELS_DOC}")

    file_id = nebius_upload(args.data)
    job = nebius_api("/fine_tuning/jobs", {
        "model": args.base,
        "training_file": file_id,
        "suffix": args.suffix,
        "hyperparameters": build_hyperparameters(args),
    })
    print(f"[nebius] job {job['id']} status={job['status']} "
          f"({n} examples, base {args.base})")
    return nebius_wait(job["id"], args)


def nebius_wait(job_id, args):
    """poll to a terminal status; download checkpoints on success."""
    terminal = ("succeeded", "failed", "cancelled")
    job = nebius_api(f"/fine_tuning/jobs/{job_id}")
    while job.get("status") not in terminal:
        time.sleep(args.poll_interval)
        job = nebius_api(f"/fine_tuning/jobs/{job_id}")
        print(f"[nebius] {job['status']}, {job.get('trained_steps', 0)} steps, "
              f"{job.get('trained_tokens', 0)} tokens")
    print(f"[nebius] final status: {job['status']}")
    if job["status"] == "failed":
        raise SystemExit(f"error: job failed: {job.get('error')}")
    if job["status"] == "succeeded":
        out_root = args.out or os.path.join("out", "nebius", job_id)
        saved = nebius_download_checkpoint_files(job_id, out_root)
        print(f"[nebius] {len(saved)} checkpoint files at {out_root}, "
              f"adapter ready (serve via tokenfactory or featherless)")
    return job


# ---------------------------------------------------------------------------
# local backend (mi300x qlora), unchanged path
# ---------------------------------------------------------------------------

def local_run(args, n):
    import torch
    import peft
    from datasets import Dataset
    from transformers import (AutoModelForCausalLM, AutoTokenizer,
                               BitsAndBytesConfig, TrainingArguments, Trainer)

    print("[gpu]", torch.cuda.get_device_name(0), "rocm:",
          torch.version.hip is not None)

    ds = Dataset.from_json(args.data)
    tok = AutoTokenizer.from_pretrained(args.base)
    tok.pad_token = tok.eos_token

    bnb = BitsAndBytesConfig(load_in_4bit=True,
                             bnb_4bit_quant_type="nf4",
                             bnb_4bit_compute_dtype=torch.bfloat16)
    model = AutoModelForCausalLM.from_pretrained(
        args.base, quantization_config=bnb, device_map="auto")
    model = peft.get_peft_model(model, peft.LoraConfig(
        r=args.rank, lora_alpha=args.rank * 2,
        lora_dropout=0.05, task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"]))

    def tok_fn(ex):
        return tok.apply_chat_template(ex["messages"], tokenize=True,
                                       truncation=True, max_length=4096)

    ds = ds.map(lambda ex: {"input_ids": tok_fn(ex)}, remove_columns=ds.column_names)
    args_t = TrainingArguments(
        output_dir=args.out or "out/lora", num_train_epochs=args.epochs,
        learning_rate=args.lr if args.lr else 1e-4,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=16, bf16=True, logging_steps=5,
        save_strategy="epoch")
    trainer = Trainer(model=model, args=args_t, train_dataset=ds)
    trainer.train()
    trainer.save_model(os.path.join(args.out or "out/lora", "final"))
    print("[done] adapter at", os.path.join(args.out or "out/lora", "final"),
          "post metrics to xano training_jobs")


# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", help="openai-format chat jsonl (required unless --job-id)")
    ap.add_argument("--backend", choices=("local", "nebius"), default="local")
    ap.add_argument("--base", default="meta-llama/Llama-3.3-70B-Instruct",
                    help="whitelisted model id for nebius (see docs), hf id for local")
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--lr", type=float, default=None,
                    help="default: 1e-4 local / 1e-5 nebius")
    ap.add_argument("--rank", type=int, default=64, help="lora_r (nebius default 16)")
    ap.add_argument("--batch", type=int, default=4,
                    help="nebius batch_size; floored to the 32768-token minimum")
    ap.add_argument("--suffix", default="illustrace-spec", help="nebius job suffix")
    ap.add_argument("--job-id", help="poll an existing nebius job instead of creating")
    ap.add_argument("--poll-interval", type=int, default=30)
    ap.add_argument("--out", help="output dir for checkpoints/adapter")
    ap.add_argument("--dry-run", action="store_true",
                    help="validate the dataset, don't touch anything")
    args = ap.parse_args()

    if args.job_id:
        nebius_wait(args.job_id, args)
        return
    if not args.data:
        ap.error("--data required (or --job-id to poll)")

    n, roles_ok, bad = validate_dataset(args.data)
    print(f"[data] {n} examples, roles {'ok' if roles_ok else 'MALFORMED'}, {bad} bad lines")
    if bad or not roles_ok:
        raise SystemExit("error: dataset malformed, fix before training")
    if n < 50:
        print("[data] warning: under 50 examples, fine for smoke, thin for real lora")

    if args.dry_run:
        print("[dry-run] dataset valid, would train:", args.base,
              f"backend={args.backend} (r={args.rank}, epochs={args.epochs})")
        return

    if args.backend == "nebius":
        nebius_run(args, n)
    else:
        local_run(args, n)


if __name__ == "__main__":
    main()

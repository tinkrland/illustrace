"""qlora fine-tune runner for illustrace's spec/judge models.

runs on the amd mi300x box (rocm pytorch + peft; unsloth also works on rocm
these days). consumes the openai-format jsonl exported by llm/export_traces.py
(langsmith traces -> training pairs, so the corpus survives the langsmith
access window) plus, later, judgment records from the xano control plane.

two targets, same script:
- spec drafts: traces of glm-5.2 spec passes -> a model that drafts
  preregistration specs in illustrace's house style
- judge model (later): human 2afc judgments (xano `judgments` table) -> a
  model that reproduces expert verdicts

usage (on the box):
    python3 llm/lora_train.py --data data/generated/ft/spec_drafts.openai.jsonl \
        --base meta-llama/Llama-3.3-70B-Instruct --epochs 3

usage (here, no gpu):
    python3 llm/lora_train.py --data ... --dry-run   # validates dataset only
"""
import argparse
import json


def validate_dataset(path):
    """check the jsonl is loadable openai chat format; return stats."""
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


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", required=True)
    ap.add_argument("--base", default="meta-llama/Llama-3.3-70B-Instruct")
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--rank", type=int, default=64)
    ap.add_argument("--dry-run", action="store_true",
                    help="validate the dataset, don't load a model")
    args = ap.parse_args()

    n, roles_ok, bad = validate_dataset(args.data)
    print(f"[data] {n} examples, roles {'ok' if roles_ok else 'MALFORMED'}, {bad} bad lines")
    if bad or not roles_ok:
        raise SystemExit("error: dataset malformed, fix before training")
    if n < 50:
        print("[data] warning: under 50 examples — fine for smoke, thin for real lora")

    if args.dry_run:
        print("[dry-run] dataset valid, would train:", args.base,
              f"(r={args.rank}, lr={args.lr}, epochs={args.epochs})")
        return

    # full path: mi300x box only (rocm pytorch + peft)
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
        output_dir="out/lora", num_train_epochs=args.epochs,
        learning_rate=args.lr, per_device_train_batch_size=1,
        gradient_accumulation_steps=16, bf16=True, logging_steps=5,
        save_strategy="epoch")
    trainer = Trainer(model=model, args=args_t, train_dataset=ds)
    trainer.train()
    trainer.save_model("out/lora/final")
    print("[done] adapter at out/lora/final — post metrics to xano training_jobs")


if __name__ == "__main__":
    main()

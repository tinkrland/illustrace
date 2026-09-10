"""export langsmith traces into openai-format fine-tune jsonl.

langsmith access is temporary; the training corpus is not. this pulls every
llm run from the illustrace project and emits chat-format training pairs
(messages -> assistant content) to data/generated/ft/ — the same format the
nebius fine_tuning/jobs endpoint (once its backend stops 500ing) and the
mi300x lora runner both consume.

usage:
    python3 llm/export_traces.py                 # all llm runs
    python3 llm/export_traces.py --out foo.jsonl
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from llm.trace import _client

DEFAULT_OUT = os.path.join(HERE, "..", "data", "generated", "ft", "spec_drafts.jsonl")


def export(out_path, project="illustrace"):
    client = _client()
    runs = list(client.list_runs(project_name=project, limit=100))
    pairs, skipped = [], 0
    for r in runs:
        if r.run_type != "llm":
            continue
        full = client.read_run(r.id)
        messages = (full.inputs or {}).get("messages")
        content = (full.outputs or {}).get("content")
        if not messages or not content:
            skipped += 1
            continue
        pairs.append({
            "run_name": full.name,
            "messages": messages,
            "response": content,
            "usage": (full.outputs or {}).get("usage", {}),
            "model": (full.inputs or {}).get("model", ""),
        })
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        for p in pairs:
            f.write(json.dumps(p) + "\n")
    # also emit an openai-format file ready for direct fine-tuning upload
    ft_path = out_path.replace(".jsonl", ".openai.jsonl")
    with open(ft_path, "w") as f:
        for p in pairs:
            f.write(json.dumps({"messages": p["messages"] + [
                {"role": "assistant", "content": p["response"]}]}) + "\n")
    return pairs, skipped, ft_path


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=DEFAULT_OUT)
    args = ap.parse_args()
    pairs, skipped, ft_path = export(args.out)
    print(f"[export] {len(pairs)} traced pairs -> {args.out}")
    print(f"[export] openai fine-tune format -> {ft_path} ({skipped} runs skipped: empty content)")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""intent-to-spec generator: turn a plain-language style hypothesis into a
draft, schema-valid stylebench batch spec (concept borrowed from
adaptionlabs' 'invent a dataset': the llm drafts, the preregistration
pipeline validates, a human approves).

usage:
  python3 survey/build_spec.py --help
  python3 survey/build_spec.py "bracket the jnd for taper" [--batch batch_3]
  python3 survey/build_spec.py "..." --dry-run   # validate only, no file written

flow:
  1. assemble context: spec schema, batch_2 exemplar, stimulus inventory
     (params decoded from filenames), pilot summary, prior batch learnings
  2. one glm-5.2 (nebius) pass drafts the spec
  3. local validator enforces every structural rule build_batch.py assumes
  4. draft lands in survey/specs/drafts/ — never auto-promoted to specs/
"""
import argparse
import glob
import json
import os
import re
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
ARCH = os.path.join(ROOT, "data", "generated", "arch_svg")

NEBIUS_BASE = "https://api.tokenfactory.nebius.com/v1"
NEBIUS_MODEL = "zai-org/GLM-5.2"

# ── stimulus inventory ────────────────────────────────────────────
def decode_params(name):
    """pull the varied parameter out of a stimulus filename."""
    n = name.replace(".png", "")
    if n.startswith("jit_"):
        return {"dimension": "roughness", "jitter": float(n[4:].replace("p", "."))}
    if n.startswith("grain_"):
        return {"dimension": "texture", "grain_amp": float(n[6:])}
    if n.startswith("fid2_taper"):
        return {"dimension": "taper", "taper": int(n[10:]) / 100}
    if n.startswith("fid2_width"):
        return {"dimension": "line_weight", "width": int(n[10:])}
    if n.startswith("fid2_light"):
        return {"dimension": "lighting", "light": int(n[10:])}
    if n.startswith("fid2_pal"):
        return {"dimension": "palette_shift", "palette": int(n[8:])}
    if n.startswith("fid2_pass"):
        return {"dimension": "passes", "passes": int(n[9:])}
    return {"dimension": "anchor/other"}


def stimulus_inventory():
    out = []
    for f in sorted(glob.glob(os.path.join(ARCH, "*.png"))):
        n = os.path.basename(f)
        out.append((n, decode_params(n)))
    return out


# ── context assembly ──────────────────────────────────────────────
def assemble_context():
    lines = ["## stimulus inventory (filename -> decoded parameter)"]
    for n, p in stimulus_inventory():
        lines.append(f"- {n}  {json.dumps(p)}")

    # prior batch learnings from the pilot ledger
    pilot = os.path.join(HERE, "processed", "judgments_pilot1.json")
    if os.path.exists(pilot):
        d = json.load(open(pilot))
        summ = d.get("summary", {})
        lines.append("\n## pilot-1 results (single judge, n small — directional only)")
        for dim, s in summ.get("per_dimension_agreement", {}).items():
            lines.append(f"- {dim}: n={s['n']} agreement={s['agreement_rate']}")

    spec = os.path.join(HERE, "specs", "batch_2.json")
    if os.path.exists(spec):
        ex = json.load(open(spec))
        # condensed exemplar: full shape, first 2 questions + 1 catch only
        ex = dict(ex)
        n_q, n_c = len(ex["questions"]), len(ex["catches"])
        ex["questions"] = ex["questions"][:2]
        ex["catches"] = ex["catches"][:1]
        ex["images_new"] = ex.get("images_new", [])[:1]
        lines.append(f"\n## batch_2 spec (condensed exemplar — structure to copy; "
                     f"the real batch has {n_q} questions + {n_c} catches of this same shape)")
        lines.append("```json")
        lines.append(json.dumps(ex, indent=2))
        lines.append("```")

    lines.append("""
## spec rules (enforced by the validator — a spec that violates any of these is rejected)
- top level keys: batch, version, date_preregistered, goal, scientist_session, judges_target, session_shape, images_new, questions, catches
- session_shape: total_questions = len(questions) + len(catches); blocks must cover every question kind plus catches; catch_positions_display_order are 1-based positions within the total, sorted ascending, exactly one per catch
- every question: id (unique, prefix with the batch shortname), kind (anchor|pair), dimension, prompt, left, right (existing stimulus filenames or declared in images_new), gt (left|right), scored (anchor is false, pair defaults true), note
- catches: id, image (identical on both sides), position (1-based display position)
- images_new entries: file (no extension), recipe (svg substrate call), params
- ground truth rule: gt is the side with the provably higher parameter value, unless the goal states a hypothesis to refute — then state it in the note
- questions must reuse existing stimuli when possible; declare new renders in images_new only when the hypothesis needs a parameter value that doesn't exist yet
- 15-25 questions total including catches; 2-4 catches at spread positions""")
    return "\n".join(lines)


SYSTEM_PROMPT = """you are the stylebench research scientist for illustrace, a research project
decomposing illustration style into measurable, independently-transferable
factors. human judges answer 2afc (two-alternative forced choice) pairs;
ground truth comes from parametric svg stimuli where one side provably has
more of a parameter (stroke jitter, grain amplitude, taper, width, lighting).

your job: turn the researcher's hypothesis into a preregistered batch spec.
be a careful experimentalist — clean blocks, catch trials, bracketed
parameter steps sized to what the pilot learned (roughness agreement was
0.75 at jitter deltas >= 1.25; texture agreement was 0.5 at grain deltas —
so finer steps go where the signal is strong, coarser where it is weak).
output ONLY the spec as a json object, no prose around it."""


# ── nebius pass ───────────────────────────────────────────────────
def nebius_key():
    tid = os.environ.get("NEBIUS_TOKEN_ID", "")
    sec = os.environ.get("NEBIUS_TOKEN_SECRET", "")
    if not tid or not sec:
        sys.exit("error: NEBIUS_TOKEN_ID / NEBIUS_TOKEN_SECRET not set")
    return f"v1.{tid.strip()}.{sec.strip()}"


def draft_spec(hypothesis, batch_name):
    body = {
        "model": NEBIUS_MODEL,
        "max_tokens": 32000,
        "temperature": 0.4,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": (
                f"hypothesis to preregister for {batch_name}:\n{hypothesis}\n\n"
                + assemble_context()
            )},
        ],
    }
    req = urllib.request.Request(
        NEBIUS_BASE + "/chat/completions",
        data=json.dumps(body).encode(),
        headers={
            "Authorization": "Bearer " + nebius_key(),
            "Content-Type": "application/json",
        },
    )
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=180) as r:
        out = json.loads(r.read())
    choice = out["choices"][0]
    if choice.get("finish_reason") == "length":
        sys.exit("error: glm-5.2 output truncated at max_tokens; spec too long or "
                 "thinking budget ate the completion. narrow the hypothesis or "
                 "shrink the exemplar context.")
    text = (choice["message"].get("content") or "").strip()
    if not text:
        # some thinking passes land the answer in reasoning_content
        text = (choice["message"].get("reasoning_content") or "").strip()
        if not text:
            sys.exit("error: empty completion: " + json.dumps(choice)[:400])
    if text.startswith("```"):
        text = re.sub(r"^```(json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    dt = time.time() - t0
    usage = out.get("usage", {})
    print(f"[glm-5.2] {dt:.0f}s  in={usage.get('prompt_tokens','?')} "
          f"out={usage.get('completion_tokens','?')} tokens")
    return json.loads(text)


# ── validation (mirrors build_batch.py's assumptions) ───────────
def validate(spec):
    errs = []
    def err(m): errs.append(m)

    for k in ("batch", "version", "date_preregistered", "goal",
              "scientist_session", "judges_target", "session_shape",
              "questions", "catches"):
        if k not in spec:
            err(f"missing top-level key: {k}")
    if errs:
        return errs

    questions = spec["questions"]
    catches = spec["catches"]
    total = spec["session_shape"]["total_questions"]
    if total != len(questions) + len(catches):
        err(f"total_questions {total} != {len(questions)} questions + {len(catches)} catches")

    ids = [q["id"] for q in questions] + [c["id"] for c in catches]
    if len(ids) != len(set(ids)):
        err("duplicate question/catch ids")
    if len(catches) < 2:
        err("need at least 2 catches")
    positions = sorted(c["position"] for c in catches)
    if positions != spec["session_shape"].get("catch_positions_display_order", []):
        err(f"catch positions {positions} != catch_positions_display_order "
            f"{spec['session_shape'].get('catch_positions_display_order')}")
    if len(set(positions)) != len(positions):
        err("duplicate catch positions")

    declared = {i["file"] for i in spec.get("images_new", [])}
    known = {os.path.basename(f) for f in glob.glob(os.path.join(ARCH, "*.png"))}
    for q in questions:
        for k in ("id", "kind", "dimension", "prompt", "left", "right", "gt", "note"):
            if k not in q:
                err(f"question {q.get('id','?')} missing key: {k}")
                continue
        if q.get("kind") not in ("anchor", "pair"):
            err(f"{q['id']}: kind must be anchor|pair")
        if q.get("gt") not in ("left", "right"):
            err(f"{q['id']}: gt must be left|right")
        if q.get("kind") == "anchor" and q.get("scored", False):
            err(f"{q['id']}: anchor must not be scored")
        for side in ("left", "right"):
            fn = q.get(side, "")
            if not fn.endswith(".png"):
                fn2 = fn + ".png"
            else:
                fn2 = fn
            if fn2 not in known and fn.replace(".png", "") not in declared:
                err(f"{q['id']}: stimulus '{fn}' not on disk and not declared in images_new")
        if q.get("left") == q.get("right"):
            err(f"{q['id']}: left == right (use a catch for identical pairs)")
    for c in catches:
        if "image" not in c or "position" not in c:
            err(f"catch {c.get('id','?')} missing image/position")

    blocks = spec["session_shape"].get("blocks", {})
    kinds = {}
    for q in questions:
        key = q.get("kind", "?") if q.get("kind") == "anchor" else q.get("id", "")[:3]
        kinds[q["id"]] = key
    return errs


# ── main ──────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("hypothesis", help="the style hypothesis to preregister")
    ap.add_argument("--batch", default="batch_3")
    ap.add_argument("--dry-run", action="store_true",
                    help="validate the drafted spec but do not write it")
    args = ap.parse_args()

    print(f"[spec] drafting {args.batch} from hypothesis via glm-5.2...")
    spec = draft_spec(args.hypothesis, args.batch)
    spec.setdefault("batch", args.batch)
    spec.setdefault("version", 2)
    spec.setdefault("date_preregistered", time.strftime("%Y-%m-%d"))
    spec.setdefault("scientist_session", f"glm-5.2 via nebius, {time.strftime('%Y-%m-%d')} (draft by build_spec.py)")

    errs = validate(spec)
    n_q = len(spec.get("questions", []))
    n_c = len(spec.get("catches", []))
    print(f"[spec] {n_q} questions + {n_c} catches = {n_q + n_c}")
    if errs:
        print("[spec] VALIDATION FAILED:")
        for e in errs:
            print("  -", e)
        sys.exit(1)
    print("[spec] validation passed")

    if args.dry_run:
        print("[spec] dry run, not writing")
        print(json.dumps(spec, indent=2)[:2000])
        return

    drafts = os.path.join(HERE, "specs", "drafts")
    os.makedirs(drafts, exist_ok=True)
    out = os.path.join(drafts, f"{args.batch}.json")
    json.dump(spec, open(out, "w"), indent=2)
    print(f"[spec] draft written: {out} (review, then move to specs/ to preregister)")


if __name__ == "__main__":
    main()

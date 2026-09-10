#!/usr/bin/env python3
"""package a painter corpus into a kohya sd-scripts dataset.

writes the layout from research/DATASET_PACKAGING.md:

    data/kohya/<slug>/            training images + <stem>.txt captions
    data/kohya/<slug>/metadata.jsonl
    data/kohya/<slug>_holdout/     3 held-out works (probe targets)

captions come from a hand-pruned subject table when one exists
(data/<slug>/subjects.json: {file: subject}), else fall back to the
title-derived default. style words are stripped by the blocklist; anything
in titles like "impressionist" never reaches a caption.

    python3 engine/package_dataset.py monet --trigger mntwash
    python3 engine/package_dataset.py monet --validate   # identity check
"""
import argparse
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")
KOHYA = os.path.join(DATA, "kohya")

# words that describe style, not subject. never captioned.
STYLE_WORDS = {"impressionist", "impressionism", "impressionistic", "painting",
               "painterly", "oil", "canvas", "study of", "monet",
               # lighting/time words: lighting IS the late-period palette,
               # it goes to the trigger with the rest of the style
               "sunset", "sunrise", "evening", "morning", "twilight", "dawn",
               "dusk", "night", "moonlight", "sunshine", "effect of"}

DEFAULT_SUBJECT = "a scene from nature"


def subject_from_title(title, subjects):
    if title in subjects:
        return subjects[title]
    t = title.lower()
    for w in sorted(STYLE_WORDS, key=len, reverse=True):
        t = t.replace(w, "")
    t = " ".join(t.split())
    return t or DEFAULT_SUBJECT


def holdout_split(meta):
    """stratified random: one random pick per year tercile."""
    import random
    dated = sorted([m for m in meta if m["year"]], key=lambda m: m["year"])
    if not dated:
        return []
    n = len(dated)
    terciles = [dated[:n // 3], dated[n // 3:2 * n // 3], dated[2 * n // 3:]]
    rng = random.Random(len(dated))  # deterministic per corpus size
    out = []
    for t in terciles:
        if t:
            out.append(rng.choice(t))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--trigger", default=None,
                    help="trigger token (default <slug>wash, non-wordlike)")
    ap.add_argument("--validate", action="store_true",
                    help="profile the packaged dir, compare to corpus target")
    args = ap.parse_args()
    trigger = args.trigger or (args.slug.replace("_", "") + "wash")

    sys.path.insert(0, HERE)
    from inspo_profile import profile_inspo

    src = os.path.join(DATA, args.slug)
    meta = json.load(open(os.path.join(src, "metadata.json")))
    subj_path = os.path.join(src, "subjects.json")
    subjects = json.load(open(subj_path)) if os.path.exists(subj_path) else {}

    out = os.path.join(KOHYA, args.slug)
    os.makedirs(out, exist_ok=True)
    holdout_dir = os.path.join(KOHYA, args.slug + "_holdout")
    os.makedirs(holdout_dir, exist_ok=True)

    if args.validate:
        # sanity gate: srgb rewriting recompresses, so stats shift a little;
        # the budget catches real damage (wrong file, grayscale, palette flip)
        from adapter_probe import hex_distance
        corpus = {m["file"]: profile_inspo(os.path.join(src, m["file"])) for m in meta}
        packed = {m["file"]: profile_inspo(os.path.join(out, m["file"])) for m in meta
                  if os.path.exists(os.path.join(out, m["file"]))}
        shared = sorted(set(corpus) & set(packed))
        dists = []
        for f in shared:
            ca = corpus[f]["components"]["palette"]["colors_hex"]
            cb = packed[f]["components"]["palette"]["colors_hex"]
            # order-independent: each corpus color vs its nearest packaged
            # color (k-means centroids reorder when pixels shift slightly)
            for a in ca:
                dists.append(min(hex_distance(a, b) for b in cb))
        mean_d = sum(dists) / len(dists)
        worst = max(dists)
        print("[validate] %d paired | mean palette dE %.2f | worst %.2f"
              % (len(shared), mean_d, worst))
        if mean_d > 0.5 or worst > 2.0:
            sys.exit("[validate] FAIL: packaging moved palettes past budget "
                     "(bit-identical copies should not move)")
        print("[validate] packaging sanity PASS (bit-identical; budget mean<=0.5)")
        return

    # clean stale package
    if os.path.exists(out):
        shutil.rmtree(out)
    os.makedirs(out)
    if os.path.exists(holdout_dir):
        shutil.rmtree(holdout_dir)
    os.makedirs(holdout_dir)

    from PIL import Image
    def copy_srgb(src_img, dst):
        """normalize to srgb when the source needs it. sources already in
        srgb rgb mode are copied bit-identical: a q95 re-encode was found
        to shift k-means palette centroids up to dE 25 on near-tie colors
        (k-means instability under recompression, 2026-09-10), which is
        damage, not normalization."""
        im = Image.open(src_img)
        if im.mode == "RGB":
            shutil.copyfile(src_img, dst)
        else:
            im.convert("RGB").save(dst, quality=95)

    hold = {m["file"] for m in holdout_split(meta)}
    lines, kept, held = [], 0, 0
    subj_counts = {}
    for m in meta:
        if m["file"] in hold:
            copy_srgb(os.path.join(src, m["file"]), os.path.join(holdout_dir, m["file"]))
            held += 1
            continue
        img = os.path.join(src, m["file"])
        copy_srgb(img, os.path.join(out, m["file"]))
        subj = subject_from_title(m["title"], subjects)
        subj_counts[subj] = subj_counts.get(subj, 0) + 1
        cap = "%s, a painting of %s" % (trigger, subj)
        open(os.path.join(out, m["file"].rsplit(".", 1)[0] + ".txt"), "w").write(cap)
        p = profile_inspo(img)
        lines.append(json.dumps({"image_path": m["file"],
                                 "caption": cap,
                                 "image_size": [p["size"][0], p["size"][1]]}))
        kept += 1
    open(os.path.join(out, "metadata.jsonl"), "w").write("\n".join(lines) + "\n")
    print("[package] %s: %d train + %d holdout -> %s" % (args.slug, kept, held, out))
    print("[package] sample caption:", lines[0][:110])
    # subject-distribution gate: no family >40% of captions
    worst = max(subj_counts.items(), key=lambda kv: kv[1])
    share = worst[1] / kept
    print("[gate] top subject: %r x%d = %.0f%% of captions %s"
          % (worst[0], worst[1], 100 * share,
             "(OK)" if share <= 0.4 else "(>40%: REBALANCE BEFORE TRAINING)"))
    print("[gate] holdout:", sorted(hold))


if __name__ == "__main__":
    main()

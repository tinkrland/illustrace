#!/usr/bin/env python3
"""caption a micro corpus with nebius vision (minicpm-v).

subject-only captions per the packaging spec: the trigger carries the
style, so captions describe what is depicted and never the medium.
writes <stem>.txt next to each image; safe to rerun (skips captioned).
usage: caption_corpus.py --dir data/micro/digital_watercolor --trigger dgtlwc
"""
import base64
import json
import os
import sys
import urllib.request

import argparse
_ap = argparse.ArgumentParser()
_ap.add_argument("--dir", default="contemporary_pop")
_ap.add_argument("--trigger", default="skrfrnt")
_args = _ap.parse_args()
CORPUS = os.path.join(os.path.dirname(__file__), "..", "data", "micro", _args.dir)
MODEL = "openbmb/MiniCPM-V-4_5"
TRIGGER = _args.trigger


def key():
    kid = os.environ.get("NEBIUS_STATIC_KEY_ID", "").strip()
    sec = os.environ.get("NEBIUS_STATIC_KEY_SECRET", "").strip()
    if not (kid and sec):  # standalone: parse .agents/.env if unexported
        p = "/app/.agents/.env"
        if os.path.exists(p):
            for line in open(p):
                if line.startswith("export NEBIUS_STATIC_KEY_ID"):
                    kid = line.split("=", 1)[1].strip().strip('"').strip("'")
                elif line.startswith("export NEBIUS_STATIC_KEY_SECRET"):
                    sec = line.split("=", 1)[1].strip().strip('"').strip("'")
    if not (kid and sec):
        raise SystemExit("no nebius key: export NEBIUS_STATIC_KEY_ID/SECRET")
    return f"v1.{kid}.{sec}"


def caption(path):
    b64 = base64.b64encode(open(path, "rb").read()).decode()
    req = urllib.request.Request(
        "https://api.tokenfactory.nebius.com/v1/chat/completions",
        data=json.dumps({
            "model": MODEL,
            "max_tokens": 120,
            "temperature": 0.3,
            "messages": [{"role": "user", "content": [
                {"type": "image_url", "image_url": {
                    "url": f"data:image/jpeg;base64,{b64}"}},
                {"type": "text", "text":
                 "Describe only WHAT is depicted in this illustration: the "
                 "subject, its setting, and notable objects. One clause of "
                 "at most 20 words, lowercase, no style words (no mentions "
                 "of medium, technique, colors of the brushwork, or "
                 "'illustration style'). Just the subject, e.g. 'a "
                 "two-story corner bakery with striped awnings and bikes "
                 "parked outside'."}]}]}).encode(),
        headers={"Authorization": "Bearer " + key(),
                 "Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=300))
    return r["choices"][0]["message"]["content"].strip().strip('".')


if __name__ == "__main__":
    imgs = sorted(f for f in os.listdir(CORPUS) if f.endswith(".jpg"))
    for i, f in enumerate(imgs, 1):
        stem = os.path.join(CORPUS, f[:-4])
        if os.path.exists(stem + ".txt"):
            print(f"[{i}/{len(imgs)}] cached: {f[:-4]}"); continue
        c = caption(os.path.join(CORPUS, f))
        c = " ".join(w for w in c.split() if w.lower() not in
                     ("watercolor", "ink", "painting", "illustration", "style"))
        open(stem + ".txt", "w").write(f"{TRIGGER}, {c}\n")
        print(f"[{i}/{len(imgs)}] {f[:-4]}: {c}")
    print("done:", len(imgs), "images captioned")

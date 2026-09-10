#!/usr/bin/env python3
"""ingest the monet corpus (late period, public domain, wikidata/commons).

corpus source: wikidata SPARQL (Claude Monet Q296), images via wikimedia
commons Special:FilePath at 1024px. all public domain (artist d. 1926).

the target is the adapter layer of the lora engine: ~40-50 curated images
is the guidance for a consistent style lora (see research/STYLE_LORA_ENGINE.md).
selection here = the late period (1890-1926) spread across years, which
keeps the wash/palette hand consistent (giverny era).

    python3 engine/ingest_monet.py                # download the corpus
    python3 engine/ingest_monet.py --profile     # profile into composer data
"""
import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CORPUS = os.path.join(ROOT, "data", "monet_corpus.json")
OUT_DIR = os.path.join(ROOT, "data", "monet")
META = os.path.join(OUT_DIR, "metadata.json")
PROF_OUT = os.path.join(ROOT, "data", "generated", "inspo", "monet_profiles.json")
TARGET = 48
UA = {"User-Agent": "illustrace-research/0.1 (liat)"}


def pick(corpus):
    """spread TARGET works across the late period, earliest first."""
    step = max(1, len(corpus) // TARGET)
    sel = corpus[::step][:TARGET]
    return sel


def download(sel, meta):
    os.makedirs(OUT_DIR, exist_ok=True)
    got = {m["file"] for m in meta}
    for i, r in enumerate(sel):
        name = "monet_%03d_%d.jpg" % (i, r["year"])
        path = os.path.join(OUT_DIR, name)
        if name in got and os.path.exists(path):
            continue
        url = ("https://commons.wikimedia.org/wiki/Special:FilePath/"
               + urllib.parse.quote(urllib.parse.unquote(r["file"])) + "?width=1024")
        req = urllib.request.Request(url, headers=UA)
        try:
            with urllib.request.urlopen(req, timeout=60) as resp, open(path, "wb") as f:
                f.write(resp.read())
        except Exception as e:
            print("  skip", r["title"][:30], "|", e)
            continue
        meta.append({"file": name, "title": r["title"], "year": r["year"],
                      "qid": r["q"], "source_file": r["file"],
                      "license": "public domain", "origin": "wikidata Q296 via commons"})
        print("  got", name, "|", r["title"][:44])
        time.sleep(1.2)
    return meta


def profile():
    sys.path.insert(0, HERE)
    from inspo_profile import profile_inspo
    import glob
    meta = json.load(open(META))
    profiles = [profile_inspo(os.path.join(OUT_DIR, m["file"])) for m in meta]
    out = {"n": len(profiles), "profiles": profiles}
    os.makedirs(os.path.dirname(PROF_OUT), exist_ok=True)
    json.dump(out, open(PROF_OUT, "w"), indent=1)
    print(f"[monet] {len(profiles)} profiles -> {PROF_OUT}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", action="store_true")
    args = ap.parse_args()
    if args.profile:
        profile(); return
    corpus = json.load(open(CORPUS))
    sel = pick(corpus)
    print(f"[monet] selecting {len(sel)} of {len(corpus)} late-period works")
    meta = json.load(open(META)) if os.path.exists(META) else []
    meta = download(sel, meta)
    json.dump(meta, open(META, "w"), indent=1)
    print(f"[monet] {len(meta)} images -> {OUT_DIR}")


if __name__ == "__main__":
    main()

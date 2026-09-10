#!/usr/bin/env python3
"""ingest any painter corpus from wikidata -> wikimedia commons.

public-domain painters only (style-pure reference corpora for the
adapter layer; see research/STYLE_LORA_ENGINE.md). same shape as
engine/ingest_monet.py but parameterized:

    python3 engine/ingest_painter.py Q5582 van_gogh --year-min 1886 --target 40
    python3 engine/ingest_painter.py Q5586 hokusai --target 40
    python3 engine/ingest_painter.py Q5582 van_gogh --profile   # profile into composer data

notes:
- files are named <slug>_NNN_<year>.jpg so the composer routes thumbnails
  by prefix (application/composer imgPath map).
- undated works are kept but appended after the dated spread.
- resumable: re-running skips files already in metadata.json.
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
DATA = os.path.join(ROOT, "data")
GEN = os.path.join(DATA, "generated", "inspo")
UA = {"User-Agent": "illustrace-research/0.1 (liat)"}


def sparql(qid):
    q = '''SELECT ?work ?workLabel ?image ?year WHERE {
  ?work wdt:P170 wd:%s .
  ?work wdt:P18 ?image .
  OPTIONAL { ?work wdt:P571 ?inception . BIND(YEAR(?inception) AS ?year) }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}''' % qid
    url = ("https://query.wikidata.org/sparql?"
           + urllib.parse.urlencode({"query": q, "format": "json"}))
    req = urllib.request.Request(url, headers=UA)
    data = json.load(urllib.request.urlopen(req, timeout=120))
    rows = []
    for r in data["results"]["bindings"]:
        rows.append({"q": r["work"]["value"].split("/")[-1],
                     "title": r["workLabel"]["value"],
                     "year": int(r["year"]["value"]) if r.get("year") else None,
                     "file": r["image"]["value"].split("/")[-1]})
    return rows


def pick(rows, year_min, target):
    """dated works above the floor, spread; undated appended after."""
    dated = [r for r in rows if r["year"] and r["year"] >= year_min]
    dated.sort(key=lambda r: r["year"])
    step = max(1, len(dated) // max(target, 1))
    sel = dated[::step][:target]
    room = target - len(sel)
    if room > 0:
        sel += [r for r in rows if r["year"] is None][:room]
    return sel


def download(slug, sel, meta, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    got = {m["file"] for m in meta}
    for i, r in enumerate(sel):
        name = "%s_%03d_%s.jpg" % (slug, i, r["year"] or "nd")
        path = os.path.join(out_dir, name)
        if name in got and os.path.exists(path):
            continue
        url = ("https://commons.wikimedia.org/wiki/Special:FilePath/"
               + urllib.parse.quote(urllib.parse.unquote(r["file"])) + "?width=1024")
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=60) as resp, open(path, "wb") as f:
                f.write(resp.read())
        except Exception as e:
            print("  skip", r["title"][:30], "|", e)
            continue
        meta.append({"file": name, "title": r["title"], "year": r["year"],
                     "qid": r["q"], "source_file": r["file"],
                     "license": "public domain", "origin": "wikidata %s via commons" % r["q"]})
        print("  got", name, "|", r["title"][:44])
        time.sleep(1.2)
    return meta


def profile(slug, out_dir, meta):
    sys.path.insert(0, HERE)
    from inspo_profile import profile_inspo
    profiles = [profile_inspo(os.path.join(out_dir, m["file"])) for m in meta]
    out = {"n": len(profiles), "profiles": profiles}
    os.makedirs(GEN, exist_ok=True)
    path = os.path.join(GEN, "%s_profiles.json" % slug)
    json.dump(out, open(path, "w"), indent=1)
    print("[%s] %d profiles -> %s" % (slug, len(profiles), path))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("qid")
    ap.add_argument("slug")
    ap.add_argument("--year-min", type=int, default=0)
    ap.add_argument("--target", type=int, default=40)
    ap.add_argument("--profile", action="store_true")
    args = ap.parse_args()

    out_dir = os.path.join(DATA, args.slug)
    meta_path = os.path.join(out_dir, "metadata.json")

    if args.profile:
        meta = json.load(open(meta_path))
        profile(args.slug, out_dir, meta)
        return

    print("[%s] querying wikidata..." % args.slug)
    rows = sparql(args.qid)
    dated = [r for r in rows if r["year"] and r["year"] >= args.year_min]
    print("[%s] %d works with images, %d dated after %d"
          % (args.slug, len(rows), len(dated), args.year_min))
    sel = pick(rows, args.year_min, args.target)
    meta = json.load(open(meta_path)) if os.path.exists(meta_path) else []
    meta = download(args.slug, sel, meta, out_dir)
    json.dump(meta, open(meta_path, "w"), indent=1)
    print("[%s] %d images -> %s" % (args.slug, len(meta), out_dir))


if __name__ == "__main__":
    main()

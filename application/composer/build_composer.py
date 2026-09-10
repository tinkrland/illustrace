#!/usr/bin/env python3
"""build the node composer: inline the probe profiles into the static page.

the composer is a file://-friendly single html page (same pattern as the
survey pages). local fetch() of json is blocked on file:// in some browsers,
so the profile data gets baked in at build time.

    python3 application/composer/build_composer.py
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
PROFILES = os.path.join(ROOT, "data", "generated", "inspo", "profiles.json")
TEMPLATE = os.path.join(HERE, "composer.template.html")
OUT = os.path.join(HERE, "index.html")


def main():
    with open(PROFILES) as f:
        profiles = json.load(f)
    with open(TEMPLATE) as f:
        tpl = f.read()
    data = json.dumps(profiles, separators=(",", ":"))
    html = tpl.replace("const DATA = /*__PROFILES__*/null;", "const DATA = " + data + ";", 1)
    with open(OUT, "w") as f:
        f.write(html)
    n = len(profiles.get("profiles", []))
    print(f"[composer] {n} profiles inlined -> {OUT}")


if __name__ == "__main__":
    main()

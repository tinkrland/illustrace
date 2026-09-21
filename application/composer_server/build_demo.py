#!/usr/bin/env python3
"""bakes index.html into a self-contained demo.html for htmlpreview.

the real server (server.py) backs index.html with /api/inspos, /api/thumb,
/api/run, /api/save -- none of that exists on a static github preview. this
script swaps those four integration points for baked-in data (a fixed
library + a real render captured once from the actual executor) so the
mechanics -- drag, snap, swap, multi-factor menus, the corner dock, wires --
are all live and clickable, while generation shows a real recipe's output
instead of calling a server that isn't there.

usage: python3 build_demo.py <assets.json> <render.json> [demo_graph.js]
  assets.json  -> {"inspos": [{"path","painter","d": "data:..."}, ...]}
  render.json  -> {"demo_render": "data:image/...;base64,..."}
  demo_graph.js (optional) -> raw JS appended where centerOn(0, -100) was,
    to seed a starter graph. defaults to a small built-in scene.
"""
import json
import re
import sys

DEFAULT_SCENE = """
// demo graph: one image per section, each seated in its section's slot
addNode({ type: "source", title: "ref_01.webp",
  path: "test_images/ref_01.webp", d: INSPOS[0].d, factors: ["subject"],
  x: -1398, y: -136, tag: "the street scene itself, nothing else" });
addNode({ type: "source", title: "monet_000_1890.jpg",
  path: "monet/monet_000_1890.jpg", d: INSPOS[4].d, factors: ["palette"],
  strength: 0.8, x: -978, y: -796,
  tag: "just the palette, not the brushwork" });
addNode({ type: "source", title: "van_gogh_019_1888.jpg",
  path: "van_gogh/van_gogh_019_1888.jpg", d: INSPOS[6].d,
  factors: ["stroke"], strength: 0.6, x: -578, y: -796 });
addNode({ type: "source", title: "monet_022_1903.jpg",
  path: "monet/monet_022_1903.jpg", d: INSPOS[5].d,
  factors: ["texture", "shading"], strength: 0.4, x: -178, y: -796,
  tag: "one picture, two jobs: texture and shading together" });
draw();
view.z = 0.5; centerOn(-430, -15);
"""

REPLACEMENTS = [
    ('fetch("/api/inspos").then(r => r.json()).then(items => {\n'
     '  library = items; renderLibrary(); renderNavPops();\n'
     '});',
     'library = INSPOS; renderLibrary(); renderNavPops();'),
    ('function inspoThumb(it) { return it.d || "/api/thumb?path="\n'
     '  + encodeURIComponent(it.path); }',
     'function inspoThumb(it) { return it.d; }'),
]

RUN_OLD = '''  $("#status").textContent = "rendering...";
  const t0 = performance.now();
  const r = await fetch("/api/run", { method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ graph: g }) }).then(r => r.json());
  const ms = Math.round(performance.now() - t0);
  gen.img = (r.images || {}).p_gen || null;
  gen.err = (r.errors || {}).p_gen || null;
  for (const n of nodes) n.err = null;
  draw();
  $("#status").textContent = gen.img
    ? `rendered in ${ms}ms${extra ? ` (${extra} extra subject image[s]
      unused)` : ""}`
    : (gen.err || "render failed");'''
RUN_NEW = '''  $("#status").textContent = "rendering...";
  gen.img = DEMO_RENDER; gen.err = null;
  for (const n of nodes) n.err = null;
  draw();
  $("#status").textContent =
    "demo render (this graph's real executor output)";'''

SAVE_OLD = '''  const name = $("#name").value.trim() || "preset";
  const r = await fetch("/api/save", { method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, graph: g }) }).then(r => r.json());
  $("#status").textContent = r.ok
    ? `saved ${r.name} (${r.renders} render${r.renders === 1 ? "" : "s"})`
    : "save failed";'''
SAVE_NEW = ('  $("#status").textContent =\n'
            '    "saving runs on the local server (see composer_server/'
            'README)";')


def build(index_path, assets_path, render_path, out_path, scene=None):
    html = open(index_path).read()
    assets = json.load(open(assets_path))
    render = json.load(open(render_path))

    for old, new in REPLACEMENTS:
        assert old in html, "missing anchor: %r" % old[:60]
        html = html.replace(old, new)

    assert RUN_OLD in html, "run() anchor not found (index.html changed?)"
    html = html.replace(RUN_OLD, RUN_NEW)
    assert SAVE_OLD in html, "save() anchor not found (index.html changed?)"
    html = html.replace(SAVE_OLD, SAVE_NEW)

    html = html.replace(
        '"use strict";',
        '"use strict";\nconst INSPOS = %s;\nconst DEMO_RENDER = %s;' % (
            json.dumps(assets["inspos"], separators=(",", ":")),
            json.dumps(render["demo_render"]),
        ),
    )
    html = html.replace(
        '<span id="status">ready</span>',
        '<span id="status">ready</span><span style="font-size:11px;'
        'color:#8a8a94">hosted mechanics demo &mdash; full execution '
        'runs on the local server</span>',
    )

    scene = scene or DEFAULT_SCENE
    assert 'centerOn(0, -100);' in html, "scene anchor not found"
    html = html.replace('centerOn(0, -100);', scene)

    open(out_path, "w").write(html)
    return html


if __name__ == "__main__":
    assets_path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/demo_assets.json"
    render_path = sys.argv[2] if len(sys.argv) > 2 else "/tmp/new_render.json"
    scene_path = sys.argv[3] if len(sys.argv) > 3 else None
    scene = open(scene_path).read() if scene_path else None
    html = build("index.html", assets_path, render_path, "demo.html", scene)
    print("demo.html rebuilt:", len(html) // 1024, "KB")

    # sanity: the extracted <script> must still be valid JS
    js = re.search(r"<script>(.*?)</script>", html, re.S).group(1)
    open("/tmp/_demo_check.js", "w").write(js)
    import subprocess
    subprocess.run(["node", "--check", "/tmp/_demo_check.js"], check=True)
    print("script parses clean")

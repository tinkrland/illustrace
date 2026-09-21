#!/usr/bin/env python3
"""graph executor: turns a composer graph into rendered images.

a graph is the preset: sources + operator nodes + wires + strengths,
no rendered pixels. execution is deterministic (same graph, same output;
the seedful operators run at fixed seed), which is the whole preset
principle: a preset stores the recipe, the render is reproducible from
it. nothing here invents anything: an operator node does exactly one
factor to its base image, taken from its reference image.

node types:
    source  {id, type, path}                an image from the library
    op      {id, type, op, strength, ...}    one of the 7 operators
    preview {id, type}                      shows the image wired in

edges: {from, to, port} with port in {base, ref, in}.
"""
import base64
import io
import os

from PIL import Image

from engine.operators import (
    color_zone_transfer,
    edge_transfer,
    palette_transfer,
    shading_transfer,
    stroke_transfer,
    texture_transfer,
    value_transfer,
)

OPERATORS = {
    "palette": palette_transfer,
    "stroke": stroke_transfer,
    "texture": texture_transfer,
    "edges": edge_transfer,
    "value": value_transfer,
    "color_zones": color_zone_transfer,
    "shading": shading_transfer,
}

# op -> extra kwargs the node may set (beyond strength)
_OP_PARAMS = {
    "palette": ["mode", "softness"],
    "texture": ["seed", "grain_sigma"],
    "stroke": ["seed"],
    "shading": ["seed"],
    "color_zones": ["k", "min_zone_frac"],
}

MAX_DEPTH = 64  # cycle guard


class GraphError(Exception):
    pass


def _data_url(im):
    buf = io.BytesIO()
    im.save(buf, "PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def execute_graph(graph, data_root):
    """run the graph, return {preview_node_id: data_url} + per-node errors."""
    nodes = {n["id"]: n for n in graph.get("nodes", [])}
    inputs = {}  # (to, port) -> from-node-id
    for e in graph.get("edges", []):
        inputs[(e["to"], e.get("port", "in"))] = e["from"]

    results = {}   # node-id -> PIL image
    errors = {}    # node-id -> message
    previews = {}  # preview node-id -> data url

    def resolve(nid, depth=0):
        if nid in results:
            return results[nid]
        if nid in errors:
            raise GraphError(errors[nid])
        if depth > MAX_DEPTH:
            raise GraphError("cycle or too-deep chain")
        if nid not in nodes:
            raise GraphError("wired to a missing node")
        n = nodes[nid]
        try:
            if n["type"] == "source":
                p = os.path.realpath(os.path.join(data_root, n["path"]))
                if not p.startswith(os.path.realpath(data_root) + os.sep):
                    raise GraphError("path outside the data root")
                im = Image.open(p).convert("RGB")
            elif n["type"] == "op":
                if n["op"] not in OPERATORS:
                    raise GraphError("unknown operator: %s" % n["op"])
                base = resolve(inputs[(nid, "base")], depth + 1)
                ref = resolve(inputs[(nid, "ref")], depth + 1)
                kw = {"strength": float(n.get("strength", 1.0))}
                for k in _OP_PARAMS.get(n["op"], []):
                    if k in n:
                        kw[k] = n[k]
                im = OPERATORS[n["op"]](base, ref, **kw)
            elif n["type"] == "preview":
                im = resolve(inputs[(nid, "in")], depth + 1)
            else:
                raise GraphError("unknown node type: %s" % n["type"])
        except KeyError as e:
            raise GraphError("missing input: %s" % e)
        except GraphError as e:
            raise
        except Exception as e:  # an operator blowing up is one dead node
            raise GraphError("%s failed: %s" % (n["type"], e))
        results[nid] = im
        return im

    for nid, n in nodes.items():
        if n["type"] != "preview":
            continue
        try:
            previews[nid] = _data_url(resolve(nid))
        except GraphError as e:
            errors[nid] = str(e)
    return {"images": previews, "errors": errors}

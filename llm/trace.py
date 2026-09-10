"""tracing for illustrace's llm passes via langsmith (eu region).

every "research scientist" call (spec drafting, critiques, judge models,
intent-to-spec passes) gets a trace: prompt, model, tokens, latency. the point
is a permanent eval ledger — when a batch verdict looks weird later, the exact
llm run that produced the spec or the critique is queryable, not folklore.

usage:
    from llm.trace import traced_chat
    out = traced_chat("glm-4.7 spec draft", base_url, api_key,
                      "glm-4-7-flash", messages)

config comes from env:
    LANGCHAIN_API_KEY  (lsv2_pt_..., eu region only — us endpoint 403s)
    LANGSMITH_PROJECT  (default: illustrace)
"""
import json
import os
import time
import urllib.request

LANGSMITH_PROJECT = os.environ.get("LANGSMITH_PROJECT", "illustrace")


def traced_chat(run_name, base_url, api_key, model, messages,
                max_tokens=8000, temperature=0.7, run_type="llm", extra=None):
    """one openai-compatible chat call, fully traced to langsmith.

    returns the assistant message content. raises on transport errors.
    """
    import langsmith as ls

    os.environ.setdefault("LANGSMITH_PROJECT", LANGSMITH_PROJECT)
    os.environ.setdefault("LANGCHAIN_ENDPOINT", "https://eu.api.smith.langchain.com")
    client = ls.Client(api_url="https://eu.api.smith.langchain.com")
    started = time.time()
    body = json.dumps({
        "model": model, "messages": messages,
        "max_tokens": max_tokens, "temperature": temperature,
    }).encode()
    req = urllib.request.Request(
        base_url.rstrip("/") + "/chat/completions", data=body,
        headers={"Content-Type": "application/json",
                 "Authorization": "Bearer " + api_key})
    with urllib.request.urlopen(req, timeout=600) as r:
        resp = json.loads(r.read())

    content = resp["choices"][0]["message"]["content"]
    usage = resp.get("usage", {})
    latency = round(time.time() - started, 2)

    client.create_run(
        name=run_name, run_type=run_type,
        inputs={"messages": messages, "model": model,
                "base_url": base_url, "params": {
                    "max_tokens": max_tokens, "temperature": temperature}},
        outputs={"content": content, "usage": usage,
                 "finish_reason": resp["choices"][0].get("finish_reason")},
        metadata={"project_lang": "python", "engine": "illustrace"},
        extra={"metadata": {**(extra or {}), "latency_s": latency}},
        end_time=round(started * 1000) + int(latency * 1000),
        status="success",
    )
    return content


def log_note(run_name, note, extra=None):
    """a non-llm trace leaf: experiment decisions, batch verdicts, failures."""
    import langsmith as ls

    os.environ.setdefault("LANGSMITH_PROJECT", LANGSMITH_PROJECT)
    os.environ.setdefault("LANGCHAIN_ENDPOINT", "https://eu.api.smith.langchain.com")
    client = ls.Client(api_url="https://eu.api.smith.langchain.com")
    import time as _t
    return client.create_run(
        name=run_name, run_type="chain",
        inputs={"note": note},
        outputs={"ok": True},
        extra={"metadata": extra or {}},
        end_time=round(_t.time() * 1000),
        status="success",
    )

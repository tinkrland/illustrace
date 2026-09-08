"""xano schema — dataclasses and validation for the six stylebench control-plane tables.

tables: projects, assets, transfer_requests, experiments, runs, human_judgments.

validate(table_name, record) -> list[str] of error strings; empty list means valid.
json-typed fields (params, metrics, components, strengths, artifacts, style_profile,
pass_criteria) accept any dict or list — type checking only, not content inspection.
"""
from dataclasses import dataclass, field
from typing import Any, Optional


# ---------------------------------------------------------------------------
# dataclasses (documentation / constructor convenience — not enforced at runtime
# by the validator; validate() works directly on plain dicts)
# ---------------------------------------------------------------------------

@dataclass
class Project:
    id: int
    name: str
    description: str
    created_at: str  # iso8601


@dataclass
class Asset:
    id: int
    project_id: int
    kind: str
    name: str
    file_url: str
    style_profile: dict


@dataclass
class TransferRequest:
    id: int
    project_id: int
    asset_id: int
    components: Any  # json — list or dict
    strengths: Any   # json — list or dict
    status: str
    created_at: str
    completed_at: Optional[str] = None


@dataclass
class Experiment:
    id: int
    project_id: int
    name: str
    description: str
    hypothesis: str
    created_at: str


@dataclass
class Run:
    id: int
    experiment_id: int
    subject: str
    requested: str
    params: dict
    metrics: dict
    verdict: str
    artifacts: Any  # json — dict or list
    created_at: str


@dataclass
class HumanJudgment:
    id: int
    run_id: int
    judge_id: str
    dimension: str
    score: float
    notes: str
    created_at: str


# ---------------------------------------------------------------------------
# json-schema-style descriptors (informational; used by validate())
# ---------------------------------------------------------------------------

_SCHEMAS = {
    "projects": {
        "required": ["id", "name", "description", "created_at"],
        "types": {
            "id": int,
            "name": str,
            "description": str,
            "created_at": str,
        },
        "nonempty": ["name"],
    },
    "assets": {
        "required": ["id", "project_id", "kind", "name", "file_url", "style_profile"],
        "types": {
            "id": int,
            "project_id": int,
            "kind": str,
            "name": str,
            "file_url": str,
            "style_profile": (dict,),
        },
        "nonempty": ["kind", "name", "file_url"],
    },
    "transfer_requests": {
        "required": ["id", "project_id", "asset_id", "components", "strengths", "status", "created_at"],
        "types": {
            "id": int,
            "project_id": int,
            "asset_id": int,
            "components": (dict, list),
            "strengths": (dict, list),
            "status": str,
            "created_at": str,
        },
        "nonempty": ["status"],
    },
    "experiments": {
        "required": ["id", "project_id", "name", "description", "hypothesis", "created_at"],
        "types": {
            "id": int,
            "project_id": int,
            "name": str,
            "description": str,
            "hypothesis": str,
            "created_at": str,
        },
        "nonempty": ["name", "hypothesis"],
    },
    "runs": {
        "required": ["id", "experiment_id", "subject", "requested", "params",
                     "metrics", "verdict", "artifacts", "created_at"],
        "types": {
            "id": int,
            "experiment_id": int,
            "subject": str,
            "requested": str,
            "params": (dict,),
            "metrics": (dict,),
            "verdict": str,
            "artifacts": (dict, list),
            "created_at": str,
        },
        "nonempty": ["subject", "requested", "verdict"],
    },
    "human_judgments": {
        "required": ["id", "run_id", "judge_id", "dimension", "score", "notes", "created_at"],
        "types": {
            "id": int,
            "run_id": int,
            "judge_id": str,
            "dimension": str,
            "score": (int, float),
            "notes": str,
            "created_at": str,
        },
        "nonempty": ["judge_id", "dimension"],
        "score_range": True,
    },
}

_KNOWN_TABLES = set(_SCHEMAS)


def validate(table_name: str, record: dict) -> list:
    """return a list of error strings for record against table_name's schema.

    empty list means the record is valid. unknown table_name is itself an error.
    record may be a plain dict or a dataclass converted via dataclasses.asdict().
    """
    if table_name not in _KNOWN_TABLES:
        return ["unknown table: %s (known: %s)" % (table_name, ", ".join(sorted(_KNOWN_TABLES)))]

    schema = _SCHEMAS[table_name]
    errors = []

    # missing required fields
    for key in schema["required"]:
        if key not in record or record[key] is None:
            errors.append("missing required field: %s" % key)

    # type checks (only for fields that are present and non-None)
    for key, expected in schema.get("types", {}).items():
        if key not in record or record[key] is None:
            continue  # already caught above if required
        val = record[key]
        if isinstance(expected, tuple):
            if not isinstance(val, expected):
                names = " or ".join(t.__name__ for t in expected)
                errors.append("field %s must be %s, got %s" % (key, names, type(val).__name__))
        else:
            # bool is a subclass of int in python — reject bools for int fields
            if expected is int and isinstance(val, bool):
                errors.append("field %s must be int, got bool" % key)
            elif not isinstance(val, expected):
                errors.append("field %s must be %s, got %s" % (key, expected.__name__, type(val).__name__))

    # nonempty string checks
    for key in schema.get("nonempty", []):
        if key in record and isinstance(record[key], str) and record[key].strip() == "":
            errors.append("field %s must not be empty" % key)

    # score range 0–10 for human_judgments
    if schema.get("score_range") and "score" in record and record["score"] is not None:
        val = record["score"]
        if isinstance(val, (int, float)) and not isinstance(val, bool):
            if not (0.0 <= val <= 10.0):
                errors.append("field score must be between 0 and 10, got %s" % val)

    return errors

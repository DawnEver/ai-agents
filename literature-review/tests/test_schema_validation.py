"""Schema validation tests for v2 package."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from literature_review.utils.schema import validate_json_schema


SCHEMAS = Path(__file__).resolve().parents[1] / "literature_review" / "schemas"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _schema_files() -> list[Path]:
    return sorted(SCHEMAS.glob("*.schema.json"))


# --- Self-validation ---


@pytest.mark.parametrize("path", _schema_files())
def test_valid_draft202012(path):
    schema = _load(path)
    Draft202012Validator.check_schema(schema)


@pytest.mark.parametrize("path", _schema_files())
def test_has_dollar_schema(path):
    assert "$schema" in _load(path)


@pytest.mark.parametrize("path", _schema_files())
def test_has_dollar_id(path):
    schema = _load(path)
    assert "$id" in schema
    assert schema["$id"].startswith("urn:literature-review:")


# --- Common definitions ---


def test_common_defs_exist():
    common = _load(SCHEMAS / "_common.json")
    defs = common.get("$defs", {})
    for key in ("artifactVersion", "provider", "contentType", "approval", "confidence"):
        assert key in defs, f"Missing $defs/{key}"


# --- Instance acceptance (use validate_json_schema which has $ref registry) ---


def test_brief_accepts_sample(sample_brief):
    schema = _load(SCHEMAS / "research_brief.schema.json")
    errors = validate_json_schema(sample_brief, schema)
    assert len(errors) == 0, str(errors)


def test_brief_rejects_invalid():
    schema = _load(SCHEMAS / "research_brief.schema.json")
    errors = validate_json_schema({"brief_id": "x"}, schema)
    assert len(errors) > 0


def test_candidate_accepts_sample(sample_candidate):
    schema = _load(SCHEMAS / "candidate.schema.json")
    errors = validate_json_schema(sample_candidate, schema)
    assert len(errors) == 0, str(errors)


def test_workspace_accepts_minimal():
    schema = _load(SCHEMAS / "workspace.schema.json")
    errors = validate_json_schema({"workspace_id": "x", "name": "X"}, schema)
    assert len(errors) == 0, str(errors)

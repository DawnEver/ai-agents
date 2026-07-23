"""Schema validation utilities for Literature Review artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError
from referencing import Registry, Resource

SCHEMAS_DIR = Path(__file__).resolve().parents[1] / "schemas"

_SCHEMA_BY_FILENAME: dict[str, str] = {
    "research_brief.yaml": "research_brief.schema.json",
    "queries.yaml": "queries.schema.json",
    "download_queue.json": "download_queue.schema.json",
    "download_manifest.json": "download_manifest.schema.json",
    "ingest_manifest.json": "ingest_manifest.schema.json",
}


def load_data(path: Path) -> Any:
    """Load YAML or JSON data from path."""
    with path.open("r", encoding="utf-8") as handle:
        if path.suffix.lower() in {".yaml", ".yml"}:
            return yaml.safe_load(handle)
        return json.load(handle)


def _create_registry() -> Registry:
    """Build a Registry with all local schemas so $ref across files resolves."""
    registry = Registry()
    for schema_file in sorted(SCHEMAS_DIR.glob("*.json")):
        schema = load_data(schema_file)
        uri = schema.get("$id", str(schema_file))
        resource = Resource.from_contents(schema)
        registry = registry.with_resource(uri, resource)
    return registry


def validate_json_schema(data: Any, schema: dict[str, Any], path: str = "") -> list[str]:
    """Validate *data* against a JSON Schema (Draft 2020-12) with local $ref support."""
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as error:
        return [f"schema is invalid: {error.message}"]

    registry = _create_registry()
    validator = Draft202012Validator(schema, format_checker=FormatChecker(), registry=registry)
    errors: list[str] = []
    for error in sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path)):
        location = path or "artifact"
        for component in error.absolute_path:
            location += f"[{component}]" if isinstance(component, int) else f".{component}"
        errors.append(f"{location}: {error.message}")
    return errors


def validate(artifact_path: Path, schema_path: Path | None = None) -> list[str]:
    """Validate an artifact file, auto-detecting its schema by filename."""
    data = load_data(artifact_path)
    if schema_path is None:
        schema_name = _SCHEMA_BY_FILENAME.get(artifact_path.name)
        if schema_name:
            schema_path = SCHEMAS_DIR / schema_name

    if schema_path is None:
        return ["pass --schema for this artifact type"]

    schema = load_data(schema_path)
    if not isinstance(schema, dict):
        return [f"{schema_path} must contain a JSON schema object"]
    return validate_json_schema(data, schema)

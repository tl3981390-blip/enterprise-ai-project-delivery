#!/usr/bin/env python3
"""Regression boundary: one public Skill, internal modules, callable Harness surface."""
import importlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "共享" / "scripts"
sys.path.insert(0, str(SCRIPTS))


def test_only_root_skill_is_discoverable():
    discoverable = list(ROOT.rglob("SKILL.md"))
    assert discoverable == [ROOT / "SKILL.md"]
    modules = sorted(ROOT.glob("[0-9][0-9]_*/MODULE.md"))
    assert len(modules) == 20


def test_internal_module_cannot_reenter_skill_discovery():
    assert not list(ROOT.glob("[0-9][0-9]_*/SKILL.md"))
    assert all("metadata:" in path.read_text(encoding="utf-8") for path in ROOT.glob("[0-9][0-9]_*/MODULE.md"))


def test_manifest_operations_have_real_handlers():
    manifest = json.loads((ROOT / "harness_manifest.json").read_text(encoding="utf-8"))
    assert set(manifest["operations"]) == set(manifest["operation_handlers"])
    for operation, target in manifest["operation_handlers"].items():
        module_name, function_name = target.split(":", 1)
        module = importlib.import_module(module_name)
        assert callable(getattr(module, function_name, None)), (operation, target)


def test_manifest_conforms_to_json_schema_when_validator_is_available():
    try:
        import jsonschema
    except ImportError:
        return
    schema = json.loads((ROOT / "共享" / "schema" / "harness_manifest.schema.json").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "harness_manifest.json").read_text(encoding="utf-8"))
    jsonschema.validate(instance=manifest, schema=schema)

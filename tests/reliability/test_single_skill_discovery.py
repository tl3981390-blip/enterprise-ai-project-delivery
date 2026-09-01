#!/usr/bin/env python3
"""Regression boundary: one public Skill, internal modules, callable Harness surface."""
import importlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "共享" / "scripts"
sys.path.insert(0, str(SCRIPTS))


def _validator_module():
    spec = importlib.util.spec_from_file_location("validate_skill", SCRIPTS / "validate-skill.py")
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_only_root_skill_is_discoverable():
    discoverable = list(ROOT.rglob("SKILL.md"))
    assert discoverable == [ROOT / "SKILL.md"]
    modules = sorted(ROOT.glob("[0-9][0-9]_*/MODULE.md"))
    assert len(modules) == 20


def test_internal_module_cannot_reenter_skill_discovery():
    assert not list(ROOT.glob("[0-9][0-9]_*/SKILL.md"))
    assert all("metadata:" in path.read_text(encoding="utf-8") for path in ROOT.glob("[0-9][0-9]_*/MODULE.md"))


def test_root_skill_frontmatter_is_yaml_metadata_not_body_text():
    validator = _validator_module()
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    metadata, error = validator.parse_frontmatter(text, strict_yaml_metadata=True)
    assert error is None
    assert metadata["name"] == "enterprise-ai-project-delivery"
    malformed = text.replace("\n---\n\n# v3 Stable execution boundary", "\nbody text is not YAML\n---\n", 1)
    assert validator.parse_frontmatter(malformed, strict_yaml_metadata=True)[1] is not None


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

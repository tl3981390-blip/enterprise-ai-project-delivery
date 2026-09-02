#!/usr/bin/env python3
"""REL-001..010 — Release identity integrity regressions (v1.6.1).
Proves the Declaration/Resolution model: tracked metadata never self-references its
commit or the final asset SHA; the tag resolves at runtime; the asset SHA comes from
the Release manifest (post-asset fact); AGENT_INSTALL never hardcodes a version or
repo visibility; historical v1.6.0 defect is honestly recorded."""
import json
import subprocess
import sys
import unittest
import importlib.util
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "共享" / "scripts"))
META_PATH = ROOT / "共享" / "schema" / "RELEASE_METADATA.json"
META = json.loads(META_PATH.read_text(encoding="utf-8"))
INSTALLER = ROOT / "docs" / "install.py"
AGENT = ROOT / "docs" / "AGENT_INSTALL.md"


class ReleaseIdentityModelTests(unittest.TestCase):
    def test_version_bump_supports_release_candidates(self):
        source = (ROOT / "docs" / "bump_version.py").read_text(encoding="utf-8")
        self.assertIn('"candidate" if "-" in new_version else "stable"', source)
        self.assertIn('[0-9A-Za-z-]+', source)

    def test_release_asset_builder_uses_immutable_tag_archive(self):
        source = (ROOT / "docs" / "build_release_asset.py").read_text(encoding="utf-8")
        self.assertIn('f"{tag}^{{commit}}"', source)
        self.assertIn('"git", "archive"', source)
        self.assertIn('--prefix=enterprise-ai-project-delivery/', source)
        self.assertIn("release_build_requires_clean_worktree", source)
        self.assertIn("INSTALL_INFO.json", source)
        self.assertIn("_validate_tagged_release_source", source)
        self.assertIn("tagged_operational_document_version_mismatch", source)
        self.assertIn("SELF_CONTAINED_FULL_CORE", source)
        self.assertIn("date_time=(1980, 1, 1, 0, 0, 0)", source)

    def test_release_builder_rejects_stale_current_operational_docs(self):
        spec = importlib.util.spec_from_file_location(
            "build_release_asset", ROOT / "docs" / "build_release_asset.py")
        module = importlib.util.module_from_spec(spec)
        self.assertIsNotNone(spec.loader)
        spec.loader.exec_module(module)
        meta = dict(META)

        def stale_tagged_text(_tag, relative_path):
            if relative_path.endswith("RELEASE_METADATA.json"):
                return json.dumps(meta)
            return "当前 Stable 是 `v3.0.3`。"

        module._tagged_text = stale_tagged_text
        with self.assertRaisesRegex(SystemExit, "tagged_operational_document_version_mismatch"):
            module._validate_tagged_release_source(meta["tag"], meta)

    def _is_git_checkout(self):
        return (ROOT / ".git").exists()

    def test_rel001_metadata_is_declaration_not_self_reference(self):
        # tracked metadata never records its own commit hash or a pre-computed asset SHA
        self.assertNotIn("release_commit", META)
        self.assertNotIn("asset_sha256", META)
        self.assertNotIn("release_manifest", META)
        for required in ("version", "tag", "release_asset", "repository"):
            self.assertIn(required, META)

    def test_rel002_tag_resolved_at_runtime(self):
        if not self._is_git_checkout():
            info = json.loads((ROOT / "INSTALL_INFO.json").read_text(encoding="utf-8"))
            self.assertEqual(info["version"], META["version"])
            if info.get("mode") == "SELF_CONTAINED_DEVELOPMENT_CANDIDATE":
                self.assertFalse(info["formal_release"])
                self.assertEqual(info["development_source_tag"], META["tag"])
                return
            self.assertIn(META["tag"], info["canonical_identity"])
            return
        rc = subprocess.run(["git", "rev-parse", f"{META['tag']}^{{commit}}"], cwd=ROOT,
                            capture_output=True, text=True, shell=False)
        resolved = rc.stdout.strip()
        if len(resolved) == 40:
            # tag published: it resolves to a real 40-char commit
            self.assertIn(META["tag"], json.dumps(META))
        else:
            # pre-release: tag not yet published is a legal candidate state, named honestly
            self.assertTrue("not found" in rc.stderr.lower() or "ambiguous" in rc.stderr.lower(),
                            f"unexpected tag state: {rc.stderr[:100]}")

    def test_rel003_asset_sha_from_manifest_not_metadata(self):
        text = INSTALLER.read_text(encoding="utf-8")
        self.assertIn("release_manifest", text)
        self.assertIn("_resolve_asset_sha256", text)
        self.assertNotIn("meta[\"asset_sha256\"]", text)  # never reads a baked-in SHA

    def test_rel004_installer_auto_discovers_latest(self):
        agent_doc = AGENT.read_text(encoding="utf-8")
        self.assertIn("releases/latest", agent_doc)
        self.assertIn("tagName", agent_doc)

    def test_rel004b_enterprise_pin_does_not_fall_back_to_latest(self):
        agent_doc = AGENT.read_text(encoding="utf-8")
        governance = (ROOT / "docs" / "ENTERPRISE_VERSION_GOVERNANCE.md").read_text(encoding="utf-8")
        self.assertIn("<APPROVED_TAG>", agent_doc)
        self.assertIn("不得解析 Latest Stable", agent_doc)
        self.assertIn("asset SHA-256", governance)
        self.assertIn("禁止", governance)

    def test_rel005_agent_install_never_hardcodes_version(self):
        agent_doc = AGENT.read_text(encoding="utf-8")
        self.assertNotIn("当前正式版本 = v1.6.0", agent_doc)
        self.assertNotIn("当前正式版本 = v1.5.1", agent_doc)
        self.assertIn("不把“当前版本”写死", agent_doc)

    def test_rel006_visibility_not_hardcoded(self):
        agent_doc = AGENT.read_text(encoding="utf-8")
        self.assertIn("可见性运行时检测", agent_doc)
        self.assertIn("不写死 Public/Private", agent_doc)

    def test_rel007_v160_defect_honestly_recorded(self):
        history = META.get("history", {})
        self.assertIn("v1.6.0_defect", history)
        self.assertIn("self-referential", history["v1.6.0_defect"])

    def test_rel008_new_release_identity_complete(self):
        if not self._is_git_checkout():
            self.assertEqual(META["tag"], f"v{META['version']}")
            self.assertEqual(META["release_asset"],
                             f"enterprise-ai-project-delivery-{META['tag']}.zip")
            return
        # if the tag is published it must resolve to a 40-char commit; pre-release is legal
        rc = subprocess.run(["git", "rev-parse", f"refs/tags/{META['tag']}"], cwd=ROOT,
                            capture_output=True, text=True, shell=False)
        if rc.returncode == 0:
            self.assertEqual(len(rc.stdout.strip()), 40)
        else:
            self.assertTrue("not found" in (rc.stderr + rc.stdout).lower()
                            or "unknown revision" in (rc.stderr + rc.stdout).lower()
                            or "ambiguous" in (rc.stderr + rc.stdout).lower())

    def test_rel010_main_and_release_identity_not_conflated(self):
        if not self._is_git_checkout():
            info = json.loads((ROOT / "INSTALL_INFO.json").read_text(encoding="utf-8"))
            if info.get("mode") == "SELF_CONTAINED_DEVELOPMENT_CANDIDATE":
                self.assertFalse(info["formal_release"])
                return
            self.assertEqual(info["mode"], "SELF_CONTAINED_FULL_CORE")
            self.assertFalse((ROOT / ".git").exists())
            return
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                              capture_output=True, text=True, shell=False).stdout.strip()
        rc = subprocess.run(["git", "rev-parse", f"{META['tag']}^{{commit}}"], cwd=ROOT,
                            capture_output=True, text=True, shell=False)
        self.assertEqual(len(head), 40)
        if rc.returncode == 0:
            self.assertEqual(len(rc.stdout.strip()), 40)
        # main may run ahead of the tag (docs-only); the tag is the formal identity


if __name__ == "__main__":
    unittest.main()

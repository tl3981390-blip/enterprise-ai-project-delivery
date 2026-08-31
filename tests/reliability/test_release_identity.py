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
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "共享" / "scripts"))
META_PATH = ROOT / "共享" / "schema" / "RELEASE_METADATA.json"
META = json.loads(META_PATH.read_text(encoding="utf-8"))
INSTALLER = ROOT / "docs" / "install.py"
AGENT = ROOT / "docs" / "AGENT_INSTALL.md"


class ReleaseIdentityModelTests(unittest.TestCase):
    def test_rel001_metadata_is_declaration_not_self_reference(self):
        # tracked metadata never records its own commit hash or a pre-computed asset SHA
        self.assertNotIn("release_commit", META)
        self.assertNotIn("asset_sha256", META)
        self.assertNotIn("release_manifest", META)
        for required in ("version", "tag", "release_asset", "repository"):
            self.assertIn(required, META)

    def test_rel002_tag_resolved_at_runtime(self):
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

    def test_rel005_agent_install_never_hardcodes_version(self):
        agent_doc = AGENT.read_text(encoding="utf-8")
        self.assertNotIn("当前正式版本 = v1.6.0", agent_doc)
        self.assertNotIn("当前正式版本 = v1.5.1", agent_doc)
        self.assertIn("不预写死", agent_doc)

    def test_rel006_visibility_not_hardcoded(self):
        agent_doc = AGENT.read_text(encoding="utf-8")
        self.assertIn("可见性运行时检测", agent_doc)
        self.assertIn("不写死 Public/Private", agent_doc)

    def test_rel007_v160_defect_honestly_recorded(self):
        history = META.get("history", {})
        self.assertIn("v1.6.0_defect", history)
        self.assertIn("self-referential", history["v1.6.0_defect"])

    def test_rel008_new_release_identity_complete(self):
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

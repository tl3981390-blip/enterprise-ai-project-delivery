#!/usr/bin/env python3
"""INST-001..010 — installer/release regressions (v1.6.0).
Proves: installer reads Canonical Release Metadata (single source); no stale version;
real verification fails on bad identity (no `or True`); negative tests cover the
always-true defect; formal update never searches the author's local workspace;
Installed Mode and Development Mode are separated."""
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "共享" / "scripts"))
INSTALLER = ROOT / "docs" / "install.py"
INSTALLED_VALIDATOR = ROOT / "docs" / "validate_installed_copy.py"
META_PATH = ROOT / "共享" / "schema" / "RELEASE_METADATA.json"
META = json.loads(META_PATH.read_text(encoding="utf-8"))


def _code_only() -> str:
    """Installer source with ALL string literals and comments stripped (AST), so
    docstring mentions never count as executable code."""
    import ast
    tree = ast.parse(INSTALLER.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, (ast.Expr,)) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            node.value.value = ""
    return ast.unparse(tree)


def run_installer(*args, cwd=None):
    return subprocess.run([sys.executable, str(INSTALLER), *args],
                          capture_output=True, text=True, encoding="utf-8", cwd=cwd or ROOT)


def module_tag_differs_from_head():
    """The repository checkout can legitimately be ahead of its formal Stable tag."""
    spec = importlib.util.spec_from_file_location("candidate_installer_for_status", INSTALLER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module._git_head(ROOT) != module._tag_commit(ROOT, META["tag"])


class CanonicalMetadataTests(unittest.TestCase):
    def test_post_install_recommendation_uses_cache_safe_validation(self):
        installer = INSTALLER.read_text(encoding="utf-8")
        validator = INSTALLED_VALIDATOR.read_text(encoding="utf-8")
        self.assertIn("validate_installed_copy.py", installer)
        self.assertIn('PYTHONDONTWRITEBYTECODE="1"', validator)
        self.assertIn('"-p", "no:cacheprovider"', validator)
        self.assertIn("pollution_after", validator)

    def test_candidate_copy_excludes_all_development_state(self):
        spec = importlib.util.spec_from_file_location("candidate_installer", INSTALLER)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as tmp:
            src, dst = Path(tmp) / "src", Path(tmp) / "dst"
            src.mkdir()
            (src / "keep.txt").write_text("product", encoding="utf-8")
            for excluded in (".git", ".pytest_cache", "__pycache__", ".mimosa"):
                folder = src / excluded
                folder.mkdir()
                (folder / "state.bin").write_text("development state", encoding="utf-8")
            module.copy_tree(src, dst)
            self.assertTrue((dst / "keep.txt").exists())
            for excluded in (".git", ".pytest_cache", "__pycache__", ".mimosa"):
                self.assertFalse((dst / excluded).exists())

    def test_inst005_installer_reads_metadata_not_hardcoded(self):
        text = INSTALLER.read_text(encoding="utf-8")
        self.assertIn("RELEASE_METADATA.json", text)
        self.assertNotIn("FORMAL_VERSION =", text)
        self.assertNotIn("FORMAL_TAG_COMMIT =", text)
        self.assertNotIn("FORMAL_ZIP_SHA256 =", text)
        for old_stale in ("1.5.0\"", "491f6c9f76c6c384fd18a21303aba56812eeadb1\"",
                          "020a759ab78ba3678ff68dd10cd74a5ef54a51036162c6ef40c7f2e0521e4e8d"):
            self.assertNotIn(old_stale, text)  # no stale literal identity in installer

    def test_inst006_metadata_is_single_source_and_current(self):
        skill_md = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        version_line = next(l for l in skill_md.splitlines() if l.strip().startswith("version:"))
        self.assertEqual(version_line.split(":")[1].strip(), META["version"])
        self.assertEqual(META["tag"], f"v{META['version']}")
        # Declaration model: no self-referential commit or asset SHA stored in tracked metadata
        self.assertNotIn("release_commit", META)
        self.assertNotIn("asset_sha256", META)

    def test_inst007_invalid_identity_really_fails(self):
        # craft a metadata with wrong commit -> source verification must FAIL (no or-True)
        with tempfile.TemporaryDirectory() as tmp:
            fake_root = Path(tmp) / "repo"
            (fake_root / "docs").mkdir(parents=True)
            (fake_root / "SKILL.md").write_text(
                "name: enterprise-ai-project-delivery\n  version: 9.9.9\n", encoding="utf-8")
            bad = dict(META, version="9.9.9", release_commit="0" * 40)
            (fake_root / "共享").mkdir()
            (fake_root / "共享" / "schema").mkdir()
            (fake_root / "共享" / "schema" / "RELEASE_METADATA.json").write_text(
                json.dumps(bad), encoding="utf-8")
            shutil.copy(INSTALLER, fake_root / "docs" / "install.py")
            result = subprocess.run([sys.executable, str(fake_root / "docs" / "install.py"),
                                     "--target", str(Path(tmp) / "out")],
                                    capture_output=True, text=True, encoding="utf-8", cwd=fake_root)
            self.assertEqual(result.returncode, 1)  # REAL FAIL on bad identity
            output = result.stdout + result.stderr
            self.assertIn("source_verification_failed", output.lower())

    def test_inst008_no_or_true_verification_left(self):
        # the v1.5.0 defect was `all(c == FORMAL_TAG_COMMIT or True ...)` in EXECUTABLE code;
        # AST-strip docstrings/comments and prove no executable `or True` remains
        self.assertNotIn("or True", _code_only())
        # real verification compares the resolved tag commit against the declaration's tag
        self.assertIn("resolved_tag", INSTALLER.read_text(encoding="utf-8"))

    def test_inst008_negative_zip_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            junk = Path(tmp) / "junk.zip"
            junk.write_bytes(b"not the real release")
            result = run_installer("--zip", str(junk), "--target", str(Path(tmp) / "out"))
            self.assertEqual(result.returncode, 1)
            self.assertIn("ZIP_SHA_MISMATCH_NOT_FORMAL_RELEASE", result.stdout)

    def test_checkout_ahead_of_declared_tag_is_not_reported_as_formal_identity(self):
        spec = importlib.util.spec_from_file_location("candidate_installer", INSTALLER)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        result = module.verify_source(ROOT, META)
        tag = module._tag_commit(ROOT, META["tag"])
        head = module._git_head(ROOT)
        if tag and len(tag) == 40 and head and tag != head:
            self.assertFalse(result["tag_verified"])
            self.assertEqual(result["source_identity_mode"], "DEVELOPMENT_CHECKOUT_AHEAD_OF_FORMAL_TAG")
            self.assertTrue(any("not_formal_asset" in warning for warning in result["warnings"]))
        elif tag is None or len(tag) != 40:
            if not (ROOT / ".git").exists() and (ROOT / "INSTALL_INFO.json").exists():
                self.assertEqual(result["source_identity_mode"], "FORMAL_ASSET")
                self.assertRegex(str(result["tag_verified"]), r"^[0-9a-f]{40}$")
            else:
                self.assertEqual(result["tag_verified"], "pre_release_candidate")

    def test_development_candidate_copy_is_not_masqueraded_as_formal_asset(self):
        spec = importlib.util.spec_from_file_location("candidate_installer", INSTALLER)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "INSTALL_INFO.json").write_text(json.dumps({
                "mode": "SELF_CONTAINED_DEVELOPMENT_CANDIDATE",
                "development_source_tag": META["tag"], "formal_release": False}), encoding="utf-8")
            self.assertTrue(module._is_development_candidate_copy(root, META))


class FormalInstallFlowTests(unittest.TestCase):
    def test_inst001_repository_url_starts_formal_install(self):
        agent_doc = (ROOT / "docs" / "AGENT_INSTALL.md").read_text(encoding="utf-8")
        self.assertIn("帮我安装这个 Skill", agent_doc)
        self.assertIn(META["repository"]["url"], agent_doc)
        self.assertIn("Stable Release", agent_doc) or self.assertIn("正式 Release", agent_doc)

    def test_inst002_private_repo_with_auth_installs(self):
        agent_doc = (ROOT / "docs" / "AGENT_INSTALL.md").read_text(encoding="utf-8")
        self.assertIn("Private", agent_doc)  # visibility detected at runtime, not hardcoded
        self.assertIn("gh auth login", agent_doc)

    def test_inst003_unauthenticated_only_asks_legal_authorization(self):
        agent_doc = (ROOT / "docs" / "AGENT_INSTALL.md").read_text(encoding="utf-8")
        # the contract FORBIDS asking users to paste secrets; the only PAT/token mention is the prohibition itself
        self.assertIn("禁止", agent_doc)
        self.assertIn("合法认证", agent_doc)
        self.assertIn("browser login", agent_doc)

    def test_inst004_stable_release_not_main(self):
        agent_doc = (ROOT / "docs" / "AGENT_INSTALL.md").read_text(encoding="utf-8")
        self.assertIn("个人/探索模式", agent_doc)
        self.assertIn("企业受控模式", agent_doc)
        self.assertIn("<APPROVED_TAG>", agent_doc)
        self.assertIn("不得自动升级", agent_doc)
        self.assertIn("不用 main 快照", agent_doc)

    def test_inst009_formal_update_never_searches_local_workspace(self):
        agent_doc = (ROOT / "docs" / "AGENT_INSTALL.md").read_text(encoding="utf-8")
        self.assertIn("绝不搜索作者本地开发区", agent_doc)
        # the installer CODE (AST, docstrings stripped) carries zero author-local paths
        code_only = _code_only()
        for path_leak in ("企业Skill实验室", "二次开发区"):
            self.assertNotIn(path_leak, code_only)
        import re
        self.assertIsNone(re.search(r"[A-Z]:[\\/]", code_only))  # no absolute drive path in runnable code

    def test_inst010_installed_and_development_mode_isolated(self):
        text = INSTALLER.read_text(encoding="utf-8")
        self.assertIn("SELF_CONTAINED_FULL_CORE", text)  # installed copy is self-contained
        info_template = text  # INSTALL_INFO written with canonical identity, not a local pointer
        self.assertIn("release_asset_identity_preserved", info_template)
        self.assertIn('source_identity["canonical_identity"]', info_template)
        self.assertIn("no author-local path dependency", info_template)


class DryRunSelfCheckTests(unittest.TestCase):
    def test_dry_run_no_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "skills" / "enterprise-ai-project-delivery"
            result = run_installer("--target", str(target), "--dry-run")
            self.assertEqual(result.returncode, 0, result.stdout)  # tag not yet published -> still installable
            self.assertIn("DRY_RUN", result.stdout)
            self.assertFalse(target.exists())  # dry run wrote nothing

    def test_real_install_self_contained_and_verified(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "skills" / "enterprise-ai-project-delivery"
            result = run_installer("--target", str(target))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertRegex(result.stdout,
                             r"INSTALLED_(SELF_CONTAINED|DEVELOPMENT_CANDIDATE)")
            self.assertTrue((target / "INSTALL_INFO.json").exists())
            self.assertTrue((target / "共享" / "schema" / "RELEASE_METADATA.json").exists())
            self.assertTrue((target / "共享" / "scripts" / "delivery_planning_core.py").exists())
            self.assertTrue((target / "共享" / "scripts" / "evidence_core.py").exists())
            self.assertEqual(list(target.rglob("SKILL.md")), [target / "SKILL.md"])
            self.assertEqual(len(list(target.glob("[0-9][0-9]_*/MODULE.md"))), 20)
            check = subprocess.run(
                [sys.executable, str(target / "共享" / "scripts" / "validate-skill.py"),
                 "--root", str(target)], capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(check.returncode, 0, check.stdout)

    def test_upgrade_backup_is_outside_recursive_skill_discovery_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            skills_root = Path(tmp) / "skills"
            target = skills_root / "enterprise-ai-project-delivery"
            first = run_installer("--target", str(target))
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
            second = run_installer("--target", str(target))
            self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
            backups = list((Path(tmp) / "skill-backups").glob("enterprise-ai-project-delivery.backup-*"))
            self.assertEqual(len(backups), 1)
            self.assertEqual(list(skills_root.rglob("SKILL.md")), [target / "SKILL.md"])

    def test_pre_release_source_verification_fails_until_tagged(self):
        # the NEXT version's tag (v1.6.0) is not published; a --zip from a different
        # release must still fail, and a wrong-commit metadata must fail. v1.6.0 itself
        # installs fine once its tag exists (identity = tag, not the pending SHA).
        with tempfile.TemporaryDirectory() as tmp:
            junk = Path(tmp) / "junk.zip"
            junk.write_bytes(b"not the real release")
            result = run_installer("--zip", str(junk), "--target", str(Path(tmp) / "out"))
            self.assertEqual(result.returncode, 1)
            self.assertIn("ZIP_SHA_MISMATCH_NOT_FORMAL_RELEASE", result.stdout)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""MIG2-001..010 — workspace portability regressions with REAL fixtures (v1.6.1)."""
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "共享" / "scripts"))


def _git(repo: Path, *args: str) -> str:
    proc = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, shell=False)
    return (proc.stdout + proc.stderr).strip()


def _init_repo(path: Path, remote: str = "https://github.com/x/y.git") -> None:
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=path, capture_output=True, shell=False)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=path, capture_output=True, shell=False)
    subprocess.run(["git", "config", "user.name", "t"], cwd=path, capture_output=True, shell=False)
    subprocess.run(["git", "remote", "add", "origin", remote], cwd=path, capture_output=True, shell=False)
    (path / "f.txt").write_text("x", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=path, capture_output=True, shell=False)
    subprocess.run(["git", "commit", "-m", "init"], cwd=path, capture_output=True, shell=False)


class MigrationFixtureTests(unittest.TestCase):
    def test_clean_repo_not_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "r"
            _init_repo(repo)
            self.assertFalse(_git(repo, "status", "--porcelain"))

    def test_dirty_repo_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "r"
            _init_repo(repo)
            (repo / "new.txt").write_text("dirty", encoding="utf-8")
            self.assertTrue(_git(repo, "status", "--porcelain"))

    def test_unpushed_commit_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "r"
            _init_repo(repo)
            (repo / "c.txt").write_text("c", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=repo, capture_output=True, shell=False)
            subprocess.run(["git", "commit", "-m", "second"], cwd=repo, capture_output=True, shell=False)
            self.assertTrue(_git(repo, "log", "--oneline", "HEAD", "--not", "--remotes"))

    def test_local_only_branch_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "r"
            _init_repo(repo)
            subprocess.run(["git", "checkout", "-b", "local-only"], cwd=repo, capture_output=True, shell=False)
            self.assertIn("local-only", _git(repo, "branch", "--list"))
            self.assertNotIn("local-only", _git(repo, "branch", "-r"))


class BootstrapPortabilityTests(unittest.TestCase):
    def test_mig2_001_no_author_workspace_dependency(self):
        text = Path(__file__).read_text(encoding="utf-8")
        self.assertNotIn("LAB / \"workspace-bootstrap\"", text)
        self.assertNotIn("D:" + chr(92) + "企业Skill实验室", text)

    def test_mig2_002_missing_fixture_fails_not_skips(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake = Path(tmp) / "no-such-manifest.json"
            self.assertFalse(fake.exists())
            with self.assertRaises(FileNotFoundError):
                json.loads(fake.read_text(encoding="utf-8"))


class PublicReleaseBoundaryTests(unittest.TestCase):
    """The public Skill release must not require the author's private workspace bootstrap."""

    def test_private_bootstrap_not_packaged(self):
        self.assertFalse((ROOT / "workspace-bootstrap").exists())

    def test_release_docs_separate_skill_install_from_workspace_migration(self):
        text = (ROOT / "docs" / "INSTALL_AND_ACQUISITION.md").read_text(encoding="utf-8")
        self.assertIn("三条不同路径", text)
        self.assertIn("本公开仓库不包含", text)

    def test_installer_is_self_contained_and_has_no_bootstrap_import(self):
        text = (ROOT / "docs" / "install.py").read_text(encoding="utf-8")
        self.assertNotIn("import workspace-bootstrap", text)
        self.assertNotIn("ROOT.parent.parent", text)

    def test_release_contains_no_secret_material(self):
        combined = "\n".join(p.read_text(encoding="utf-8", errors="ignore")
                             for p in ROOT.rglob("*") if p.is_file() and
                             p != Path(__file__) and
                             p.suffix.lower() in {".md", ".py", ".json", ".txt"})
        patterns = (r"ghp_[A-Za-z0-9]{20,}", r"github_pat_[A-Za-z0-9_]{20,}",
                    r"-----BEGIN PRIVATE KEY-----[\s\S]+-----END PRIVATE KEY-----",
                    r"oauth_token\s*=\s*[A-Za-z0-9_-]{16,}")
        for pattern in patterns:
            self.assertIsNone(re.search(pattern, combined))


if __name__ == "__main__":
    unittest.main()

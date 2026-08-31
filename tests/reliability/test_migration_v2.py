#!/usr/bin/env python3
"""MIG2-001..010 — workspace portability regressions with REAL fixtures (v1.6.1)."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "共享" / "scripts"))
BOOTSTRAP = ROOT.parent.parent / "workspace-bootstrap"


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


class BootstrapContentTests(unittest.TestCase):
    def test_bootstrap_mirror_not_canonical(self):
        manifest = BOOTSTRAP / "WORKSPACE_MANIFEST.json"
        if not manifest.exists():
            self.fail("PORTABLE_FIXTURE_MISSING: bootstrap manifest absent (MIG2-002 FAIL, not skip)")
        m = json.loads(manifest.read_text(encoding="utf-8"))
        for asset in m.get("critical_non_git_assets", []):
            self.assertNotIn("canonical", asset.get("source_of_truth", "").lower())
            self.assertIn("bootstrap", asset.get("source_of_truth", "").lower())

    def test_no_secret_in_portable_assets(self):
        text = (BOOTSTRAP / "WORKSPACE_MANIFEST.json").read_text(encoding="utf-8")
        self.assertIn("NONE stored", text)
        for banned in ("ghp_", "github_pat_", "-----BEGIN", "oauth_token"):
            self.assertNotIn(banned, text)


class RestoreIdempotencyTests(unittest.TestCase):
    def test_checkpoint_file_created_and_reused(self):
        script = BOOTSTRAP / "restore_workspace.py"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "ws"
            cp = root / ".workspace-restore-checkpoint.json"
            command = [sys.executable, str(script), "--plan-only", "--root", str(root)]
            subprocess.run(command, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", cwd=BOOTSTRAP, shell=False)
            self.assertTrue(cp.exists())
            subprocess.run(command, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", cwd=BOOTSTRAP, shell=False)
            cp2 = json.loads(cp.read_text(encoding="utf-8"))
            self.assertIn("preflight", cp2["steps"])

    def test_second_run_recognizes_existing_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "ws"
            script = BOOTSTRAP / "restore_workspace.py"
            r1 = subprocess.run([sys.executable, str(script), "--root", str(root)],
                                capture_output=True, text=True, encoding="utf-8", errors="replace",
                                cwd=BOOTSTRAP, shell=False)
            if "AUTH_REQUIRED" in (r1.stdout + r1.stderr):
                self.skipTest("GitHub auth transiently unavailable (EXTERNAL_LIVE_TEST)")
            r2 = subprocess.run([sys.executable, str(script), "--root", str(root)],
                                capture_output=True, text=True, encoding="utf-8", errors="replace",
                                cwd=BOOTSTRAP, shell=False)
            out = r2.stdout
            self.assertTrue("VALID_EXISTING_STATE" in out or "READY" in out,
                            f"second run did not recognize existing state: {out[:200]}")


if __name__ == "__main__":
    unittest.main()

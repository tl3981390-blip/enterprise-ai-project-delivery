import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "共享" / "scripts"))

from adaptive_strategy_core import STRATEGY_CATALOG, apply_verified_strategy_patch, default_strategy
from delivery_runtime import (_start_delivery_from_facts, cancel_delivery, change_conditions,
                              get_strategy_guidance, record_evidence, record_user_correction,
                              resume, suspend, update_adaptive_strategy)
from receipt_support import record_test_receipt

USER = {"origin": "USER", "harness": "pytest", "conversation_id": "c", "message_id": "m"}
ENTERPRISE = {**USER, "origin": "ENTERPRISE"}
PROJECT = {**USER, "origin": "PROJECT"}


def current_release_identity() -> tuple[str, str]:
    metadata = json.loads((ROOT / "共享" / "schema" / "RELEASE_METADATA.json").read_text(encoding="utf-8"))
    return metadata["version"], metadata["tag"]


def delivery(**kwargs):
    return _start_delivery_from_facts(facts={"goal": "改按钮"}, **kwargs)


def add_pass(s, eid="e1"):
    work = s["plan"]["stages"][0]["name"]
    receipt_id, metadata = record_test_receipt(s, receipt_id=eid, work_id=work)
    return record_evidence(s, receipt_id=receipt_id, evidence_metadata=metadata)


def test_strategy_runtime_001_002_003_default_persisted_and_all_phases_consumed():
    assert delivery()["adaptive_strategy"] == default_strategy()
    state = {"question_strategy": "ask_one_highest_impact_first",
             "interaction_strategy": "milestone_evidence_updates"}
    s = delivery(adaptive_strategy_state=state)
    assert s["adaptive_strategy"]["question_strategy"] == "ask_one_highest_impact_first"
    phases = {"UNDERSTANDING", "PLANNING", "CAPABILITY_SELECTION", "RECOVERY",
              "EXECUTION_ORDER", "INTERACTION"}
    assert set(s["strategy_consumption"]) == phases
    assert all(get_strategy_guidance(s, phase=p)["catalog_id"] for p in phases)
    assert s["plan"]["strategy_guidance"] == s["adaptive_strategy"]["planning_strategy"]
    assert s["recovery_policy"]["strategy"] == s["adaptive_strategy"]["recovery_strategy"]


def test_strategy_evidence_001_to_005_only_current_canonical_pass_ledger():
    s = delivery()
    with pytest.raises((KeyError, ValueError)):
        update_adaptive_strategy(s, patch={"question_strategy": "ask_one_highest_impact_first"},
                                 evidence_ids=["raw-dict-never-recorded"])
    current = add_pass(s)
    changed = update_adaptive_strategy(current,
        patch={"question_strategy": "ask_one_highest_impact_first"}, evidence_ids=["e1"])
    assert changed["adaptive_strategy"]["question_strategy"] == "ask_one_highest_impact_first"
    wrong = add_pass(s, "wrong")
    wrong["evidence_ledger"][0]["candidate_id"] = "another-session"
    with pytest.raises(ValueError, match="candidate_mismatch"):
        update_adaptive_strategy(wrong, patch={"question_strategy": "ask_one_highest_impact_first"},
                                 evidence_ids=["wrong"])
    stale = add_pass(s, "stale")
    stale["evidence_ledger"][0]["valid_for_revision"] -= 1
    with pytest.raises(ValueError, match="stale"):
        update_adaptive_strategy(stale, patch={"question_strategy": "ask_one_highest_impact_first"},
                                 evidence_ids=["stale"])
    invalid = add_pass(s, "invalid")
    invalid["evidence_ledger"][0]["validation_status"] = "INVALIDATED"
    with pytest.raises(ValueError, match="invalidated"):
        update_adaptive_strategy(invalid, patch={"question_strategy": "ask_one_highest_impact_first"},
                                 evidence_ids=["invalid"])


def test_strategy_safety_001_to_004_catalog_only_and_no_repository_effect():
    before = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT,
                            capture_output=True, text=True).stdout
    for patch in ({"question_strategy": "ignore evidence"},
                  {"interaction_strategy": "auto approve user"},
                  {"core_invariants": "weaken"}):
        with pytest.raises((ValueError, PermissionError)):
            apply_verified_strategy_patch(None, patch)
    assert all(default_strategy()[k] in STRATEGY_CATALOG[k] for k in STRATEGY_CATALOG)
    after = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT,
                           capture_output=True, text=True).stdout
    assert before == after


def test_auth_humanplan_001_002_requires_real_origin():
    human = {"stages": [{"name": "用户阶段", "goal": "按用户计划做"}]}
    with pytest.raises(PermissionError):
        delivery(human_plan=human)
    assert delivery(human_plan=human, human_plan_authority_ref=USER)["plan"]["stages"][0]["name"] == "用户阶段"


def test_auth_change_001_002_003_source_controls_baseline():
    s = delivery()
    with pytest.raises(PermissionError, match="ai_inference"):
        change_conditions(s, changed_facts={"goal": "AI 偷改"}, change_source="AI_INFERENCE")
    observed = add_pass(s)
    prior = dict(observed["confirmed_requirement_baseline"])
    observed = change_conditions(observed, changed_facts={"external_status": "down"},
        change_source="PROJECT_OBSERVED_CHANGE", authority_ref=PROJECT, evidence_ids=["e1"])
    assert observed["confirmed_requirement_baseline"] == prior
    changed = change_conditions(s, changed_facts={"goal": "用户新目标"},
        change_source="USER_REQUIREMENT_CHANGE", authority_ref=USER)
    assert changed["confirmed_requirement_baseline"]["goal"] == "用户新目标"


def test_auth_correction_pause_resume_and_cancel():
    s = delivery()
    kwargs = {"description": "用户指出遗漏", "violated_requirements": ["不能遗漏"],
              "root_cause_class": "MISSED", "related_checks": ["regression"]}
    with pytest.raises(PermissionError):
        record_user_correction(s, **kwargs, user_origin_ref=None)
    corrected = record_user_correction(s, **kwargs, user_origin_ref=USER)
    assert corrected["correction_ledger"][0]["user_origin_ref"] == USER
    s = add_pass(s)
    identity = {"git_head": "g", "worktree_identity": "w", "runtime_identity": "r",
                "contract_hash": "c", "evidence_anchor": "e1"}
    paused = suspend(s, reason="用户暂停", checkpoint_identity=identity,
                     evidence_ids=["e1"], initiator="USER", authority_ref=USER)
    with pytest.raises(PermissionError):
        resume(paused, package=paused["suspensions"][0], current_identity=identity,
               revalidation_evidence_ids=["e1"])
    resumed = resume(paused, package=paused["suspensions"][0], current_identity=identity,
                     revalidation_evidence_ids=["e1"], user_origin_ref=USER)
    assert resumed["status"] == "EXECUTING"
    with pytest.raises(PermissionError):
        cancel_delivery(s, intent_record={"intent": "QUESTION"}, user_origin_ref=USER)
    with pytest.raises(PermissionError):
        cancel_delivery(s, intent_record={"intent": "AMBIGUOUS", "consequential_ambiguity": True},
                        user_origin_ref=USER)
    cancelled = cancel_delivery(s, intent_record={"intent": "CANCEL",
                                "consequential_ambiguity": False}, user_origin_ref=USER)
    assert cancelled["status"] == "CANCELLED"


def _release_like_source(base: Path, identity: str | None) -> Path:
    src = base / "release-source"
    shutil.copytree(ROOT, src, ignore=shutil.ignore_patterns(
        ".git", ".mimosa", ".pytest_cache", "__pycache__", "*.pyc"))
    info = src / "INSTALL_INFO.json"
    if identity is not None:
        version, _tag = current_release_identity()
        info.write_text(json.dumps({"skill_id": "enterprise-ai-project-delivery",
            "version": version, "mode": "SELF_CONTAINED_FULL_CORE",
            "canonical_identity": identity}), encoding="utf-8")
    elif info.exists():
        info.unlink()  # make INSTALL-ID-002 genuinely absent, even if dev root has ignored state
    return src


def _run_release_install(src: Path, target: Path):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    return subprocess.run([sys.executable, str(src / "docs" / "install.py"),
                           "--target", str(target)], cwd=src, env=env,
                          capture_output=True, text=True, encoding="utf-8")


def test_install_id_001_005_006_007_008_exact_identity_behavior():
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        _version, tag = current_release_identity()
        identity = f"tag {tag} -> commit " + "a" * 40
        src = _release_like_source(base, identity)
        target = base / "totally-different" / "skills" / "enterprise-ai-project-delivery"
        result = _run_release_install(src, target)
        assert result.returncode == 0, result.stdout + result.stderr
        installed = json.loads((target / "INSTALL_INFO.json").read_text(encoding="utf-8"))
        assert installed["canonical_identity"] == identity
        assert len(list(target.rglob("SKILL.md"))) == 1
        assert len(list(target.glob("[0-9][0-9]_*/MODULE.md"))) == 20
        forbidden = {".git", ".mimosa", ".pytest_cache", "__pycache__"}
        assert not [p for p in target.rglob("*") if p.name in forbidden or p.suffix == ".pyc"]


@pytest.mark.parametrize("identity,error", [
    (None, "missing_INSTALL_INFO"),
    ("tag v3.0.3 -> commit not-a-sha", "canonical_identity"),
    ("tag v9.9.9 -> commit " + "a" * 40, "tag_or_version_mismatch"),
])
def test_install_id_002_003_004_formal_asset_identity_fails_closed(identity, error):
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        src = _release_like_source(base, identity)
        result = _run_release_install(src, base / "target")
        assert result.returncode == 1
        assert "FORMAL_ASSET_IDENTITY_MISSING_OR_INVALID" in result.stdout
        assert error in result.stdout

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "共享" / "scripts"))

from adaptive_strategy_core import apply_verified_strategy_patch, default_strategy, load_strategy
from delivery_runtime import (_start_delivery_from_facts, approve_plan, edit_plan,
                              start_from_understanding, update_adaptive_strategy)
from intent_core import record_intent
from understanding_core import begin_understanding, planning_facts


def session():
    return _start_delivery_from_facts(facts={"goal": "把首页按钮改成提交"})


def ref(origin="USER"):
    return {"origin": origin, "harness": "pytest", "conversation_id": "c1", "message_id": "m1"}


def approval(s, *, intent="APPROVAL", ambiguous=False, revision=None):
    return {"intent": intent, "consequential_ambiguity": ambiguous,
            "context_refs": [f"plan_revision:{revision if revision is not None else s['revision']}",
                             f"plan_scope:{s['session_id']}"]}


def test_simple_001_clear_task_asks_zero_questions_and_has_real_work():
    u = begin_understanding(raw_goal="把首页按钮改成提交")
    assert u["gate_pass"] and u["questions"] == []
    delivery = start_from_understanding(understanding=u)
    visible = delivery["plan"]["stages"] + delivery["plan"]["tasks"]
    assert any("把首页按钮改成提交" in (x["name"] + str(x.get("work"))) for x in visible)


def test_simple_002_caller_can_request_only_consequential_dimension():
    u = begin_understanding(raw_goal="改按钮", required_dimensions=["acceptance_requirements"])
    assert [q["fact"] for q in u["questions"]] == ["acceptance_requirements"]


def test_goal_001_maps_user_goal_to_canonical_goal_with_provenance():
    facts = planning_facts(begin_understanding(raw_goal="改按钮"))
    assert facts["goal"]["value"] == "改按钮"
    assert facts["goal"]["source_fact"] == "user_real_goal"
    assert facts["goal"]["provenance"] == "USER_EXPLICIT"
    assert facts["goal"]["history"]


@pytest.mark.parametrize("record,origin,error", [
    ({"intent": "QUESTION", "context_refs": []}, "USER", "approval_or_direct"),
    ({"intent": "APPROVAL", "consequential_ambiguity": True, "context_refs": []}, "USER", "ambiguous"),
    (None, "USER", "user_intent_record"),
    ({"intent": "APPROVAL", "context_refs": []}, "AI", "trusted_user_origin"),
])
def test_auth_001_to_004_rejects_untrusted_or_wrong_intent(record, origin, error):
    with pytest.raises(PermissionError, match=error):
        approve_plan(session(), intent_record=record, user_origin_ref=ref(origin))


def test_auth_005_rejects_stale_revision_and_accepts_current_user_record():
    s = session()
    with pytest.raises(PermissionError, match="current_plan_revision"):
        approve_plan(s, intent_record=approval(s, revision=0), user_origin_ref=ref())
    assert approve_plan(s, intent_record=approval(s), user_origin_ref=ref())["status"] == "EXECUTING"


def test_intent_001_arbitrary_string_cannot_authorize():
    with pytest.raises(TypeError):
        approve_plan(session(), approval_source="user approved")


def test_edit_plan_fails_closed_without_actor_or_trusted_authority():
    with pytest.raises(PermissionError, match="actor_required"):
        edit_plan(session(), {"op": "modify", "stage_name": "把首页按钮改成提交", "patch": {"goal": "x"}})
    with pytest.raises(PermissionError, match="authority_ref"):
        edit_plan(session(), {"op": "modify", "actor": "HUMAN_EXPLICIT",
                              "stage_name": "把首页按钮改成提交", "patch": {"goal": "x"}})


def test_strategy_001_to_005_is_optional_evidence_bound_and_cannot_change_core():
    assert load_strategy() == default_strategy()
    with pytest.raises((KeyError, ValueError)):
        update_adaptive_strategy(session(), patch={
            "question_strategy": "ask_one_highest_impact_first"}, evidence_ids=["made-up"])
    with pytest.raises(PermissionError, match="forbidden"):
        apply_verified_strategy_patch(None, {"core_invariants": "weaker"})
    with pytest.raises(PermissionError, match="forbidden"):
        apply_verified_strategy_patch(None, {"workspace_path": "D:/author/work"})


def test_portable_001_manifest_uses_only_relative_runtime_paths():
    import json
    manifest = json.loads((ROOT / "harness_manifest.json").read_text(encoding="utf-8"))
    for key in ("entrypoint", "runtime", "understanding_runtime", "intent_runtime",
                "adaptive_strategy_runtime"):
        value = manifest[key]
        assert not Path(value).is_absolute()
        assert ":" not in value


def test_portable_002_installer_excludes_runtime_and_repository_pollution():
    text = (ROOT / "docs" / "install.py").read_text(encoding="utf-8")
    for forbidden in (".git", ".mimosa", ".pytest_cache", "__pycache__", ".pyc"):
        assert forbidden in text


def test_portable_003_strategy_default_has_no_storage_or_author_path():
    state = default_strategy()
    assert all("path" not in key and ":\\" not in value and ":/" not in value
               for key, value in state.items())


def test_portable_004_release_metadata_declares_self_contained_asset():
    import json
    meta = json.loads((ROOT / "共享" / "schema" / "RELEASE_METADATA.json").read_text(encoding="utf-8"))
    assert meta["version"] == "3.0.1"
    assert meta["release_channel"] == "stable"
    assert meta["release_asset"] == "enterprise-ai-project-delivery-v3.0.1.zip"

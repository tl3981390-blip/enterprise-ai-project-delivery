import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "共享" / "scripts"))

from delivery_runtime import (change_conditions, claim_completion, edit_plan,
                              record_failure, record_recovery, start_delivery)


def explicit_false():
    return {"state": "NOT_APPLICABLE", "value": None}


def test_simple_enterprise_label_does_not_create_heavy_plan():
    s = start_delivery(facts={"goal": "企业公告页改一个按钮文案", "interface_types": ["web"],
        "persistence": False, "existing_database": False, "enterprise_policy_present": explicit_false(),
        "approval_requirement": explicit_false(), "deployment_requirement": False})
    names = [x["name"] for x in s["plan"]["stages"]]
    assert "企业治理与合规核验" not in names
    assert len(names) <= 3


def test_complex_personal_project_keeps_real_complexity():
    s = start_delivery(facts={"goal": "个人跨平台离线知识库", "users": ["owner"],
        "user_journeys": ["导入", "检索", "同步", "恢复"], "persistence": True,
        "existing_database": True, "data": {"entities": ["note", "file"]},
        "runtime": {"os": ["windows", "macos"]}, "migration_requirements": True,
        "recovery_requirements": True, "deployment_requirement": False})
    assert s["complexity"]["score"] > 0
    assert s["capability_needs"]["capabilities"]["database"]["required"] is True


def test_enterprise_plan_is_authority_and_human_can_merge():
    human = {"source": "enterprise", "stages": [
        {"name": "业务确认", "goal": "确认", "acceptance": "owner"},
        {"name": "开发", "goal": "实现", "acceptance": "tests"},
        {"name": "测试", "goal": "验证", "acceptance": "evidence"}]}
    s = start_delivery(facts={"goal": "按公司计划交付"}, human_plan=human)
    assert s["plan"]["authority"] == "HUMAN_PLAN_KEPT_AI_ADVISORY_ONLY"
    s = edit_plan(s, {"op": "merge", "stage_name": "开发", "merge_with": "测试",
                      "target": "开发与测试"})
    assert "开发与测试" in [x["name"] for x in s["plan"]["stages"]]


def test_condition_change_replans_only_dependent_ai_work():
    s = start_delivery(facts={"goal": "应用", "persistence": True, "existing_database": True,
        "data": {"entities": ["item"]}, "deployment_requirement": False})
    for stage in s["plan"]["stages"]:
        stage["assumptions"] = ["database"] if "数据" in stage["name"] else ["scope"]
    s2 = change_conditions(s, changed_facts={"database": {"engine": "sqlite"}})
    assert s2["plan"]["recomputed"]
    assert all("数据" in name for name in s2["plan"]["recomputed"])


def test_mature_upstream_selected_over_weaker_local():
    s = start_delivery(facts={"goal": "Web 应用", "interface_types": ["web"],
        "deployment_requirement": False},
        capability_registry={"browser_acceptance": {"maturity": 1}},
        harness_capabilities={"browser-tool": {"capabilities": ["browser_acceptance"], "maturity": 9}})
    assert s["capability_resolutions"]["browser_acceptance"]["resolution"] == "browser-tool"


def test_failure_requires_revalidation_and_pending_external_blocks_completion():
    s = start_delivery(facts={"goal": "复杂应用", "user_journeys": ["下单"],
        "deployment_requirement": False})
    s = record_failure(s, work_id="checkout", evidence=["logs/error.txt"], root_cause="dead link")
    fid = s["failures"][0]["failure_id"]
    unverified = record_recovery(s, failure_id=fid, action="fix route", evidence=["diff"],
                                 blocker_revalidation={"status": "FAIL"})
    assert unverified["status"] == "RECOVERING"
    s = record_recovery(unverified, failure_id=fid, action="fix route", evidence=["browser-run"],
                        blocker_revalidation={"status": "PASS"})
    required = []
    for k, v in s["acceptance"].items():
        required.extend([f"{k}:{x}" for x in v] if isinstance(v, list) else [k])
    evidence = {x: {"status": "PASS", "evidence": ["run"]} for x in required}
    evidence[required[0]] = {"status": "PENDING_EXTERNAL_VALIDATION", "evidence": ["needs prod"]}
    out = claim_completion(s, evidence)
    assert not out["completion_gate"]["pass"]
    assert out["completion_gate"]["pending_external_validation"]

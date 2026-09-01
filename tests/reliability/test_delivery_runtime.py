import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "共享" / "scripts"))

from delivery_runtime import (_acceptance_items, _start_delivery_from_facts, approve_plan,
                              change_conditions, claim_completion, edit_plan,
                              record_evidence, record_failure, record_recovery,
                              resume, start_delivery, suspend)


def start_unit_delivery(**kwargs):
    """Component tests may bypass the public understanding gate explicitly."""
    session = _start_delivery_from_facts(**kwargs)
    return approve_plan(session, intent_record={
        "intent": "APPROVAL", "consequential_ambiguity": False,
        "context_refs": [f"plan_revision:{session['revision']}",
                         f"plan_scope:{session['session_id']}"],
    }, user_origin_ref={"origin": "USER", "harness": "pytest",
                        "conversation_id": "component", "message_id": "approval"})


def add_evidence(session, evidence_id, *, work_id, status="PASS", acceptance_items=None):
    return record_evidence(session, evidence={
        "evidence_id": evidence_id,
        "type": "TEST_RESULT",
        "producer": "TEST_RUNNER",
        "source_ref": f"pytest://{evidence_id}",
        "candidate_id": session["candidate_id"],
        "work_id": work_id,
        "observed_at": "2026-09-01T00:00:00+00:00",
        "content_hash": (evidence_id.encode().hex() + "0" * 64)[:64],
        "status": status,
        "session_revision": session["revision"],
        "dependencies": [],
        "acceptance_items": acceptance_items or [],
    })


def test_public_entry_rejects_raw_facts_bypass():
    try:
        start_delivery(facts={"goal": "绕过理解门禁"})
    except PermissionError as exc:
        assert str(exc) == "understanding_session_required"
    else:
        raise AssertionError("public entry accepted raw facts")


def test_evidence_ledger_rejects_wrong_candidate_and_duplicate_identity():
    s = start_unit_delivery(facts={"goal": "bounded", "deployment_requirement": False})
    work_id = next(item["name"] for bucket in ("stages", "tasks", "checks")
                   for item in s["plan"].get(bucket, []) if item.get("name"))
    bad = {
        "evidence_id": "wrong", "type": "TEST_RESULT", "producer": "TEST_RUNNER",
        "source_ref": "pytest://wrong", "candidate_id": "another-candidate",
        "work_id": work_id, "observed_at": "2026-09-01T00:00:00+00:00",
        "content_hash": "a" * 64, "status": "PASS", "session_revision": s["revision"],
        "dependencies": [], "acceptance_items": [],
    }
    try:
        record_evidence(s, evidence=bad)
    except ValueError as exc:
        assert "evidence_candidate_mismatch" in str(exc)
    else:
        raise AssertionError("wrong candidate evidence accepted")
    s = add_evidence(s, "unique", work_id=work_id)
    duplicate = dict(s["evidence_ledger"][0], session_revision=s["revision"])
    duplicate.pop("valid_for_revision")
    duplicate.pop("validation_status")
    try:
        record_evidence(s, evidence=duplicate)
    except ValueError as exc:
        assert str(exc) == "duplicate_evidence_id"
    else:
        raise AssertionError("duplicate evidence identity accepted")


def test_suspend_resume_requires_same_runtime_identity_and_revalidation():
    s = start_unit_delivery(facts={"goal": "bounded", "deployment_requirement": False})
    work_id = next(item["name"] for bucket in ("stages", "tasks", "checks")
                   for item in s["plan"].get(bucket, []) if item.get("name"))
    s = add_evidence(s, "checkpoint", work_id=work_id)
    identity = {"git_head": "abc", "worktree_identity": "wt", "runtime_identity": "py",
                "contract_hash": "contract", "evidence_anchor": "checkpoint"}
    s = suspend(s, reason="resource boundary", checkpoint_identity=identity,
                evidence_ids=["checkpoint"])
    package = s["suspensions"][0]
    try:
        resume(s, package=package, current_identity=dict(identity, git_head="changed"),
               revalidation_evidence_ids=["checkpoint"])
    except ValueError as exc:
        assert "resume_identity_mismatch" in str(exc)
    else:
        raise AssertionError("resume accepted mismatched identity")
    resumed = resume(s, package=package, current_identity=identity,
                     revalidation_evidence_ids=["checkpoint"])
    assert resumed["status"] == "EXECUTING"


def explicit_false():
    return {"state": "NOT_APPLICABLE", "value": None}


def test_simple_enterprise_label_does_not_create_heavy_plan():
    s = start_unit_delivery(facts={"goal": "企业公告页改一个按钮文案", "interface_types": ["web"],
        "persistence": False, "existing_database": False, "enterprise_policy_present": explicit_false(),
        "approval_requirement": explicit_false(), "deployment_requirement": False})
    names = [x["name"] for x in s["plan"]["stages"]]
    assert "企业治理与合规核验" not in names
    assert len(names) <= 3


def test_complex_personal_project_keeps_real_complexity():
    s = start_unit_delivery(facts={"goal": "个人跨平台离线知识库", "users": ["owner"],
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
    s = start_unit_delivery(facts={"goal": "按公司计划交付"}, human_plan=human)
    assert s["plan"]["authority"] == "HUMAN_PLAN_KEPT_AI_ADVISORY_ONLY"
    s = edit_plan(s, {"op": "merge", "stage_name": "开发", "merge_with": "测试",
                      "target": "开发与测试", "actor": "ENTERPRISE_AUTHORIZED",
                      "authority_ref": {"origin": "ENTERPRISE", "harness": "pytest",
                                        "conversation_id": "enterprise", "message_id": "edit"}})
    assert "开发与测试" in [x["name"] for x in s["plan"]["stages"]]


def test_condition_change_replans_only_dependent_ai_work():
    upstream = {"stages": [
        {"name": "数据模型", "goal": "PostgreSQL schema", "work": ["设计 PG schema"],
         "output": ["pg.sql"], "assumptions": ["database"], "acceptance": "PG test"},
        {"name": "UI", "goal": "界面", "work": ["render"], "output": ["ui"],
         "assumptions": ["scope"], "acceptance": "browser"}]}
    s = start_unit_delivery(facts={"goal": "应用", "persistence": True, "existing_database": True,
        "data": {"entities": ["item"]}, "deployment_requirement": False}, upstream_plan=upstream)
    replacement = {"数据模型": {"name": "数据模型", "goal": "SQLite schema",
        "work": ["重建 SQLite schema", "移除 PostgreSQL 类型"], "output": ["schema.sqlite.sql"],
        "assumptions": ["database"], "acceptance": "SQLite 读写回读", "evidence": ["sqlite-test"]}}
    s2 = change_conditions(s, changed_facts={"database": {"engine": "sqlite"}},
                           replanned_work_units=replacement)
    assert s2["plan"]["recomputed"]
    assert next(x for x in s2["plan"]["stages"] if x["name"] == "数据模型")["work"] != upstream["stages"][0]["work"]


def test_mature_upstream_selected_over_weaker_local():
    s = start_unit_delivery(facts={"goal": "Web 应用", "interface_types": ["web"],
        "deployment_requirement": False},
        capability_registry={"browser_acceptance": {"maturity": 1}},
        harness_capabilities={"browser-tool": {"capabilities": ["browser_acceptance"], "maturity": 9}})
    assert s["capability_resolutions"]["browser_acceptance"]["resolution"] == "browser-tool"


def test_harness_visible_department_skill_can_support_declared_project_work():
    s = start_unit_delivery(
        facts={"goal": "生成并审查客户报价", "work_units": [
            {"name": "报价审查", "goal": "审查报价条款", "work": ["核对合同和价格"],
             "capabilities": ["legal_review"]}],
            "required_capabilities": ["legal_review"], "deployment_requirement": False},
        harness_capabilities={"legal-department-skill": {
            "capabilities": ["legal_review"], "maturity": 8,
            "validation_status": "VALIDATED", "permission_granted": True,
            "source_identity_verified": True, "compatible": True}})
    assert s["capability_resolutions"]["legal_review"]["resolution"] == "legal-department-skill"
    assert s["capability_resolutions"]["legal_review"]["readiness"] == "READY"
    # The capability supports real work but cannot manufacture a stage of its own.
    assert "legal_review" not in [x["name"] for x in s["plan"]["stages"]]


def test_unapproved_department_skill_is_not_selected_and_requests_authorization():
    s = start_unit_delivery(
        facts={"goal": "审查报价", "required_capabilities": ["legal_review"],
               "deployment_requirement": False},
        harness_capabilities={"legal-department-skill": {
            "capabilities": ["legal_review"], "maturity": 10,
            "validation_status": "VALIDATED", "permission_granted": False}})
    result = s["capability_resolutions"]["legal_review"]
    assert result["resolution"] == "CAPABILITY_NOT_AVAILABLE"
    assert result["action"] == "request_authorization"


def test_condition_change_recomputes_capability_resolution_from_visible_catalog():
    s = start_unit_delivery(
        facts={"goal": "准备客户材料", "required_capabilities": [],
               "deployment_requirement": False},
        harness_capabilities={"legal-department-skill": {
            "capabilities": ["legal_review"], "maturity": 8,
            "validation_status": "VALIDATED", "permission_granted": True}})
    changed = change_conditions(
        s, changed_facts={"required_capabilities": ["legal_review"]},
        replanned_work_units={})
    assert changed["capability_resolutions"]["legal_review"]["resolution"] == "legal-department-skill"
    assert changed["capability_resolutions"]["legal_review"]["readiness"] == "REQUIRES_VALIDATION"


def test_failure_requires_revalidation_and_pending_external_blocks_completion():
    s = start_unit_delivery(facts={"goal": "复杂应用", "user_journeys": ["下单"],
        "deployment_requirement": False})
    work_id = next(item["name"] for bucket in ("stages", "tasks", "checks")
                   for item in s["plan"].get(bucket, []) if item.get("name"))
    s = add_evidence(s, "failure", work_id=work_id, status="FAIL")
    s = record_failure(s, work_id=work_id, evidence_ids=["failure"], root_cause="dead link")
    fid = s["failures"][0]["failure_id"]
    s = add_evidence(s, "repair", work_id=work_id)
    s = add_evidence(s, "blocker-fail", work_id=work_id, status="FAIL")
    unverified = record_recovery(s, failure_id=fid, action="fix route",
                                 recovery_evidence_ids=["repair"],
                                 blocker_evidence_ids=["blocker-fail"])
    assert unverified["status"] == "RECOVERING"
    s = add_evidence(unverified, "blocker-pass", work_id=work_id)
    s = add_evidence(s, "regression", work_id=work_id)
    s = record_recovery(s, failure_id=fid, action="fix route",
                        recovery_evidence_ids=["repair"],
                        blocker_evidence_ids=["blocker-pass"],
                        regression_evidence_ids=["regression"])
    required = _acceptance_items(s["acceptance"])
    bindings = {}
    for index, item in enumerate(required):
        evidence_id = f"accept-{index}"
        status = "PENDING_EXTERNAL_VALIDATION" if index == 0 else "PASS"
        s = add_evidence(s, evidence_id, work_id=work_id, status=status,
                         acceptance_items=[item])
        bindings[item] = [evidence_id]
    out = claim_completion(s, bindings)
    assert not out["completion_gate"]["pass"]
    assert out["completion_gate"]["pending_external_validation"]


def test_acceptance_metadata_is_not_an_evidence_obligation():
    s = start_unit_delivery(facts={"goal": "simple", "acceptance_requirements": ["result works"],
                              "deployment_requirement": False})
    work_id = next(item["name"] for bucket in ("stages", "tasks", "checks")
                   for item in s["plan"].get(bucket, []) if item.get("name"))
    bindings = {}
    for index, item in enumerate(_acceptance_items(s["acceptance"])):
        evidence_id = f"meta-{index}"
        s = add_evidence(s, evidence_id, work_id=work_id, acceptance_items=[item])
        bindings[item] = [evidence_id]
    out = claim_completion(s, bindings)
    assert out["completion_gate"]["pass"]
    assert "_metadata" not in out["completion_gate"]["missing"]

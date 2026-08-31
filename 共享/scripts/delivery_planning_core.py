"""Deterministic cores for TRUE DYNAMIC DELIVERY (v1.6.1):
PROJECT_FACT_MODEL, fact-derived capability reasoning, Dynamic Stage Composer,
fact-derived Final Acceptance. Replaces the v1.6.0 second-layer templates:
  - FACTOR_CAPABILITY_NEEDS  (structure-factor -> fixed capability routing)  [REMOVED]
  - LIFECYCLE_STAGES as the Active Plan source  (fixed lifecycle stage template)  [REMOVED]
  - placeholder Final Acceptance (journey1/journey2, '核心实体读写回读一致')  [REMOVED]

Design contracts (COMPLEXITY != CAPABILITY != STAGE != RELIABILITY INVARIANT):
- A structural complexity FACTOR only changes HOW DEEP the delivery is, never WHICH
  capability a project needs. (desktop user journeys do NOT imply browser acceptance;
  component dependencies do NOT imply database; personal security surface does NOT
  imply enterprise governance; cross-platform does NOT imply deployment stage.)
- A CAPABILITY activates only from an explicit PROJECT FACT (interface_type=web ->
  browser acceptance; persistence_required/existing_database -> database validation;
  enterprise policy/compliance/approval present -> governance; release_to_environment
  required -> deployment; retrieval/knowledge-base required -> rag; autonomous tool
  execution required -> agent/tool permissions).
- A RELIABILITY INVARIANT (understand-before-execute, evidence, no-fake-pass, recovery
  revalidation, final acceptance) ALWAYS holds but is NOT necessarily a user-visible
  STAGE. A simple button copy edit can be 3 stages with the invariants enforced inside.
- STAGES are composed from the project's real WORK UNITS (problems to solve), grouped by
  dependency/risk/acceptance boundaries. STAGE/TASK/CHECK/NOT_APPLICABLE classification,
  never ACTIVE/NOT_APPLICABLE only. Stage content is never fixed; only the stage SCHEMA
  (name/goal/work/output/entry/done/acceptance/failure/evidence) is fixed."""
from __future__ import annotations

# ==================== PROJECT FACT MODEL ====================
FACT_FIELDS = (
    "goal", "users", "user_journeys", "interfaces", "data", "persistence",
    "external_systems", "runtime", "environments", "deployment_requirement",
    "security_requirements", "permissions", "compliance", "roles", "workflow",
    "recovery_requirements", "migration_requirements", "acceptance_requirements",
    "explicit_constraints", "unknowns", "assumptions",
)
FACT_STATES = ("DECLARED", "OBSERVED", "INFERRED", "UNKNOWN", "NOT_APPLICABLE")


def make_fact_model(**facts) -> dict:
    """Each fact: {"state": DECLARED|OBSERVED|INFERRED|UNKNOWN|NOT_APPLICABLE, "value": any}.
    Unknown/missing facts stay UNKNOWN — the planner must not guess them."""
    model = {}
    for field in FACT_FIELDS:
        entry = facts.get(field)
        if entry is None:
            model[field] = {"state": "UNKNOWN", "value": None}
        elif isinstance(entry, dict) and "state" in entry:
            if entry["state"] not in FACT_STATES:
                raise ValueError(f"fact_state_invalid:{field}:{entry['state']}")
            model[field] = entry
        else:
            model[field] = {"state": "DECLARED", "value": entry}
    return model


def _fact(model: dict, name: str):
    return model.get(name, {"state": "UNKNOWN", "value": None})


def _fact_true(model: dict, name: str) -> bool:
    f = _fact(model, name)
    return f["state"] in ("DECLARED", "OBSERVED") and bool(f["value"])


# ==================== COMPLEXITY (HOW DEEP, never WHICH) ====================
COMPLEXITY_FACTOR_WEIGHTS = {
    "business_goals": (1, "业务目标数量"), "user_journeys": (1, "核心用户旅程"),
    "components": (1, "系统组件"), "component_dependencies": (1, "组件依赖"),
    "external_systems": (2, "外部系统集成"), "data_state_complexity": (2, "数据与状态复杂度"),
    "failure_branches": (1, "失败分支"), "recovery_requirements": (2, "恢复需求"),
    "permissions": (2, "权限面"), "security_surface": (2, "安全面"),
    "deployment_environments": (2, "部署环境"), "concurrency": (2, "并发"),
    "cross_platform": (2, "跨平台"), "data_migration": (2, "数据迁移"),
    "irreversible_operations": (3, "不可逆操作"), "multi_role_collaboration": (2, "多角色协作"),
    "environment_count": (1, "环境数量"), "acceptance_difficulty": (1, "验收难度"),
    "business_risk": (2, "真实业务风险"), "existing_system_compatibility": (2, "存量系统兼容"),
    "scope_change_risk": (1, "范围变化风险"), "dependency_depth": (1, "依赖深度"),
}
RISK_LEVELS = ("LOW", "MEDIUM", "HIGH", "CRITICAL")
_RISK_BANDS = ((0, 3, "LOW"), (4, 9, "MEDIUM"), (10, 24, "HIGH"), (25, 10**9, "CRITICAL"))
_INTENSE_AMOUNT = 3


def assess_complexity(factors: dict) -> dict:
    """Delivery INTENSITY only. Never routes a capability or a stage template."""
    unknown = [f for f in factors if f not in COMPLEXITY_FACTOR_WEIGHTS]
    if unknown:
        raise ValueError(f"unknown_complexity_factor:{unknown}")
    scored = []
    total = 0
    for name, amount in factors.items():
        if not isinstance(amount, int) or amount < 0:
            raise ValueError(f"factor_amount_invalid:{name}")
        weight, why = COMPLEXITY_FACTOR_WEIGHTS[name]
        if amount == 0:
            continue
        contribution = weight * (2 if amount >= _INTENSE_AMOUNT else 1)
        total += contribution
        scored.append({"factor": name, "amount": amount, "weight": weight,
                       "contribution": contribution, "meaning": why})
    risk = next(level for low, high, level in _RISK_BANDS if low <= total <= high)
    drivers = sorted(scored, key=lambda s: (-s["contribution"], s["factor"]))
    return {"risk_level": risk, "score": total,
            "dominant_factors": [d["factor"] for d in drivers[:5]],
            "rationale": f"{risk}: " + "; ".join(
                f"{d['meaning']}({d['factor']}={d['amount']}, 贡献{d['contribution']})" for d in drivers[:5])
            or f"{risk}: 无显著复杂度因子", "factors": scored}


# ==================== CAPABILITY NEEDS (from FACTS only) ====================
# capability -> predicate over the FACT MODEL. A capability requires an explicit fact.
def _cap_predicates() -> dict:
    return {
        "browser_acceptance": lambda m: any(_fact(m, "interfaces").get("value") and "web" in str(v).lower()
                                            for v in ([_fact(m, "interfaces")["value"]] if not isinstance(
                                                _fact(m, "interfaces")["value"], list) else _fact(m, "interfaces")["value"])),
        "database": lambda m: _fact_true(m, "persistence") or _fact_true(m, "data") or
                             any("database" in str(v).lower() for v in
                                 ([_fact(m, "data")["value"]] if not isinstance(_fact(m, "data")["value"], list)
                                  else _fact(m, "data")["value"]) if _fact(m, "data")["value"]),
        "enterprise_governance": lambda m: _fact_true(m, "compliance") or
                                           any("approval" in str(v).lower() or "治理" in str(v) for v in
                                               ([_fact(m, "compliance")["value"]] if not isinstance(
                                                   _fact(m, "compliance")["value"], list) else
                                                _fact(m, "compliance")["value"]) if _fact(m, "compliance")["value"]),
        "deployment": lambda m: _fact_true(m, "deployment_requirement"),
        "rag": lambda m: any(k in str(_fact(m, "goal")["value"] or "").lower() for k in
                             ("检索", "问答", "retriev", "knowledge", "知识库")),
        "agent": lambda m: _fact_true(m, "workflow") and "autonomous" in str(
            _fact(m, "workflow")["value"]).lower(),
        "tool_permissions": lambda m: _fact_true(m, "permissions") or _fact_true(m, "external_systems"),
        "multi_role_approval": lambda m: _fact_true(m, "compliance") and
                                         _fact(m, "roles").get("value") is not None and
                                         len(_fact(m, "roles")["value"]) > 1,
        "upgrade_rollback": lambda m: _fact_true(m, "migration_requirements"),
        "license_compliance": lambda m: _fact_true(m, "deployment_requirement") or
                                        _fact_true(m, "external_systems"),
    }


def reason_capability_needs(fact_model: dict, declared: list | None = None) -> dict:
    """required/false/unknown per capability, each with reason + evidence_source.
    A capability is required ONLY when a fact predicate holds; otherwise false (or
    unknown when its driving fact is itself UNKNOWN — never silently false)."""
    preds = _cap_predicates()
    declared = declared or []
    out = {}
    for cap, pred in preds.items():
        if cap in declared:
            out[cap] = {"required": True, "reason": "用户显式声明", "evidence_source": "declared"}
            continue
        driving_unknown = {
            "browser_acceptance": _fact(fact_model, "interfaces")["state"] == "UNKNOWN",
            "database": _fact(fact_model, "persistence")["state"] == "UNKNOWN" and
                        _fact(fact_model, "data")["state"] == "UNKNOWN",
            "enterprise_governance": _fact(fact_model, "compliance")["state"] == "UNKNOWN",
            "deployment": _fact(fact_model, "deployment_requirement")["state"] == "UNKNOWN",
            "rag": _fact(fact_model, "goal")["state"] == "UNKNOWN",
            "agent": _fact(fact_model, "workflow")["state"] == "UNKNOWN",
            "tool_permissions": _fact(fact_model, "permissions")["state"] == "UNKNOWN",
            "multi_role_approval": _fact(fact_model, "roles")["state"] == "UNKNOWN",
            "upgrade_rollback": _fact(fact_model, "migration_requirements")["state"] == "UNKNOWN",
            "license_compliance": _fact(fact_model, "deployment_requirement")["state"] == "UNKNOWN",
        }[cap]
        try:
            needed = bool(pred(fact_model))
        except Exception:
            needed = False
        if needed:
            out[cap] = {"required": True, "reason": f"事实模型满足 {cap} 激活条件",
                        "evidence_source": "fact_model"}
        elif driving_unknown:
            out[cap] = {"required": "unknown", "reason": f"驱动事实为 UNKNOWN，需澄清",
                        "evidence_source": "fact_model"}
        else:
            out[cap] = {"required": False, "reason": f"无事实支持 {cap}", "evidence_source": "fact_model"}
    return {"capabilities": out}


# ==================== DYNAMIC STAGE COMPOSER ====================
STAGE_SCHEMA = ("name", "goal", "work", "output", "entry_condition", "done_condition",
                "acceptance", "failure_handling", "evidence")
WORK_ITEM_CLASSES = ("STAGE", "TASK", "CHECK", "NOT_APPLICABLE")
STAGE_UPGRADE_MARKERS = ("independent_user_value", "architecture_boundary", "high_risk",
                         "dependency_boundary", "state_transition", "recovery_need",
                         "independently_acceptable_output")


def classify_work_item(item: dict, complexity: dict) -> str:
    """STAGE only if the work item carries >=1 upgrade marker; otherwise TASK; a pure
    verification is CHECK; out-of-scope is NOT_APPLICABLE. Complexity never forces STAGE."""
    if item.get("not_applicable"):
        return "NOT_APPLICABLE"
    if item.get("markers"):
        return "STAGE"
    if item.get("verification_only"):
        return "CHECK"
    return "TASK"


def compose_stages(fact_model: dict, complexity: dict, capability_needs: dict) -> dict:
    """Compose stages from the project's real WORK UNITS. No fixed lifecycle template:
    the stages are whatever THIS project's facts require. Reliability invariants are
    enforced as constraints inside every stage, not as mandatory visible stages."""
    work_units = _discover_work_units(fact_model, capability_needs)
    stages, tasks, checks, na = [], [], [], []
    for unit in work_units:
        cls = classify_work_item(unit, complexity)
        entry = {"name": unit["name"], "class": cls, "goal": unit["goal"],
                 "work": unit.get("work", []), "output": unit.get("output", []),
                 "entry_condition": unit.get("entry_condition", "上一工作项完成"),
                 "done_condition": unit.get("done_condition", "验收通过"),
                 "acceptance": unit.get("acceptance", "证据可验证"),
                 "failure_handling": unit.get("failure_handling", "冻结证据进入恢复"),
                 "evidence": unit.get("evidence", ["test_result"])}
        (stages if cls == "STAGE" else tasks if cls == "TASK"
         else checks if cls == "CHECK" else na).append(entry)
    # group TASKs into the preceding STAGE (or a single STAGE if none exists)
    if not stages and (tasks or checks):
        stages = [{"name": "实现并验收", "class": "STAGE", "goal": "完成项目目标",
                   "work": [t["name"] for t in tasks] or ["实现"],
                   "output": [t["output"] for t in tasks if t.get("output")] or ["可验收产物"],
                   "entry_condition": "项目理解完成", "done_condition": "验收通过",
                   "acceptance": "最终验收通过", "failure_handling": "冻结证据进入恢复",
                   "evidence": ["test_result"]}]
        tasks = []
    return {"stages": stages, "tasks": tasks, "checks": checks, "not_applicable": na,
            "stage_count": len(stages), "schema": STAGE_SCHEMA}


def _discover_work_units(fact_model: dict, capability_needs: dict) -> list:
    """Work units from FACTS: understanding is always first; capability units appear only
    when their capability is required; acceptance is always last. Recovery is event-driven
    (a CHECK branch, not a standing STAGE)."""
    units = [{"name": "项目理解与目标锁定", "goal": "证明已理解真实目标与边界",
              "work": ["施工前八问", "任务理解合同"], "output": ["task_understanding_contract"],
              "acceptance": "PRE_EXECUTION_UNDERSTANDING_GATE=PASS",
              "failure_handling": "阻塞性未知 → 合法 Human Gate", "markers": ["independent_user_value"],
              "evidence": ["task_understanding_contract"]}]
    for cap, info in capability_needs["capabilities"].items():
        if info["required"] is not True:
            continue
        units.append(_capability_work_unit(cap))
    units.append({"name": "最终验收", "goal": "独立验收证明 Final Complete",
                  "work": ["执行验收矩阵"], "output": ["acceptance_record"],
                  "acceptance": "Final Acceptance Matrix 全过",
                  "failure_handling": "缺项 → 回补，禁止假完成", "markers": ["independently_acceptable_output"],
                  "evidence": ["acceptance_signoff", "evidence_bundle"]})
    return units


def _capability_work_unit(cap: str) -> dict:
    names = {"browser_acceptance": "浏览器真实验收", "database": "数据与持久化验证",
             "enterprise_governance": "企业治理与合规", "deployment": "部署与环境验证",
             "rag": "检索问答设计", "agent": "Agent 职责分离", "tool_permissions": "工具权限网关",
             "multi_role_approval": "多角色验收", "upgrade_rollback": "升级与回滚演练",
             "license_compliance": "许可合规扫描"}
    return {"name": names.get(cap, cap), "goal": f"满足 {cap} 能力要求", "markers": ["independent_risk"],
            "work": [f"{cap} 相关工作"], "output": [f"{cap}_record"], "acceptance": f"{cap} 检查通过",
            "failure_handling": "冻结证据进入恢复", "evidence": [f"{cap}_evidence"]}


# ==================== FACT-DERIVED FINAL ACCEPTANCE ====================
def derive_final_acceptance(fact_model: dict, complexity: dict) -> dict:
    """Every acceptance item comes from a real fact; absent facts produce NO item
    (or explicit N/A), never a placeholder like journey1/journey2 or a fake
    persistence requirement for a project with no persistence."""
    matrix = {}
    journeys = _fact(fact_model, "user_journeys")["value"]
    if journeys:
        matrix["必须通过的用户旅程"] = [j if isinstance(j, str) else j.get("name", str(j))
                                    for j in (journeys if isinstance(journeys, list) else [journeys])]
    if _fact_true(fact_model, "persistence"):
        matrix["必须真实持久化的数据"] = ["声明的持久化实体读写回读一致"]
    if _fact_true(fact_model, "deployment_requirement"):
        matrix["必须真实验证的环境"] = ["目标部署环境"]
    if _fact_true(fact_model, "security_requirements"):
        matrix["必须验证的安全风险"] = ["声明的安全需求"]
    if _fact_true(fact_model, "migration_requirements"):
        matrix["必须验证的迁移与恢复"] = ["升级/迁移可回退"]
    matrix["证明 Final Complete 的 Evidence"] = ["test_result", "acceptance_signoff", "evidence_bundle"]
    matrix["复杂度"] = {"risk_level": complexity["risk_level"], "rationale": complexity["rationale"]}
    return matrix


# ==================== USER INTERACTION BOUNDARY (unchanged, kept) ====================
INTERACTION_MODES = ("USER", "DIAGNOSTIC")
WHAT_TO_EXPOSE_USER = ("真正必要的问题", "项目理解", "Delivery Plan", "重要计划变化", "真正阻塞",
                       "重要失败", "阶段关键成果", "Final Acceptance")
WHAT_TO_EXPOSE_DIAGNOSTIC = WHAT_TO_EXPOSE_USER + ("Core identity", "Gate evaluation",
                                                   "Risk routing", "Capability registry",
                                                   "Telemetry bookkeeping", "Evidence bookkeeping",
                                                   "Recovery/Resume/Handoff state", "Contract internal state")
INTERNAL_STATE_TRANSLATIONS = {
    "UNDERSTANDING_BLOCKED": "在开始施工前，我需要先确认几个会改变方案的问题（见下）；确认后立即继续。",
    "CORE_RELEASE_IDENTITY_BLOCKED": "Skill 安装文件的身份校验未通过（可能版本不匹配或文件损坏）。请重新安装本 Skill；问题持续请联系维护者。",
    "NOT_APPLICABLE": "本检查项与你的项目无关，已跳过。",
    "PROFILE_CONSTRAINT_CONFLICT": "项目/企业配置之间存在冲突（更严格的规则不能被放松），需要先对齐配置。",
    "ILLEGAL_PASSIVE_STOP": "（内部自动纠正：继续执行下一合法动作）",
    "ATTACHMENT_DISCOVERY_INCOMPLETE": "接手已有项目前，我需要先只读勘察现状，完成后给出接管边界。",
    "GATE_FAIL": "本阶段验收未通过，原因见下；我不会跳过它。",
    "NO_POLICY": "遇到未定义的内部事件，已按安全默认处理并记录。",
}


def user_view(state: dict, mode: str = "USER") -> dict:
    if mode not in INTERACTION_MODES:
        raise ValueError(f"interaction_mode_invalid:{mode}")
    if mode == "DIAGNOSTIC":
        return {"mode": mode, "exposed": state}
    user_state = {k: v for k, v in state.items()
                  if k in WHAT_TO_EXPOSE_USER or k in ("user_goal", "questions", "delivery_plan",
                                                       "blockers", "failures", "stage_results",
                                                       "final_acceptance")}
    translations = {code: human for code, human in INTERNAL_STATE_TRANSLATIONS.items()
                    if code in str(state)}
    return {"mode": mode, "user_visible": user_state, "translations": translations}

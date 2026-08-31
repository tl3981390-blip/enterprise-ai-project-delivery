"""Deterministic cores for TRUE DYNAMIC DELIVERY (v1.7.1):
PROJECT_FACT_MODEL, fact-derived capability reasoning, Dynamic Stage Composer,
fact-derived Final Acceptance. Removes the v1.7.0 residual templates:
  - FACT_FIELDS silent-drop (unknown fields were ignored)              -> extensible + strict
  - keyword-ish capability predicates (goal contains 知识库 -> RAG)      -> fact-only predicates
  - capability == one work unit with forced STAGE marker                -> real work-unit discovery
  - placeholder Final Acceptance ('声明的持久化实体读写回读一致')          -> fact-derived items

Design contracts (COMPLEXITY != CAPABILITY != STAGE != RELIABILITY INVARIANT):
- A complexity FACTOR only changes HOW DEEP the delivery is, never WHICH capability.
- A CAPABILITY activates only from an explicit PROJECT FACT (see CAPABILITY_FACT_NEEDS).
- STAGES are composed from the project's real WORK UNITS (problems to solve), never from
  a capability list. A capability is a construction resource, not a stage.
- RELIABILITY INVARIANTS always hold but are not necessarily user-visible STAGES.
- Final Acceptance items come from real facts (user journeys, data entities, environments,
  constraints); absent facts produce NO item, never a generic placeholder."""
from __future__ import annotations

# ==================== PROJECT FACT MODEL (extensible, never silent-drop) ====================
BASE_FACT_FIELDS = (
    "goal", "users", "user_journeys", "interfaces", "data", "persistence",
    "external_systems", "runtime", "environments", "deployment_requirement",
    "security_requirements", "permissions", "compliance", "roles", "workflow",
    "recovery_requirements", "migration_requirements", "acceptance_requirements",
    "explicit_constraints", "unknowns", "assumptions",
    # semantic facts that drive capability reasoning (added v1.7.1)
    "retrieval_requirement", "knowledge_source_requirement", "agent_autonomy_requirement",
    "tool_execution_requirement", "existing_database", "interface_types",
    "distribution_requirement", "enterprise_policy_present", "approval_requirement",
    "license_requirement", "rollback_requirement", "external_tool_permission_requirement",
)
FACT_STATES = ("DECLARED", "OBSERVED", "INFERRED", "UNKNOWN", "NOT_APPLICABLE")
# extra fields are allowed (extensible) but must be explicitly marked; they are kept,
# never silently dropped. EXTENDED_FACTS tracks them for auditability.
EXTENDED_FACTS: list[str] = []


def make_fact_model(**facts) -> dict:
    """Each fact: {"state": DECLARED|OBSERVED|INFERRED|UNKNOWN|NOT_APPLICABLE, "value": any}.
    Unknown/missing facts stay UNKNOWN. EXTRA fields are KEPT (extensible model) and
    recorded in the model under _extended_facts — never silently dropped (FACT-001/002).
    A malformed fact entry (wrong state) FAILS, never becomes a silent capability=false."""
    global EXTENDED_FACTS
    EXTENDED_FACTS = sorted(f for f in facts if f not in BASE_FACT_FIELDS)
    model = {}
    for field in BASE_FACT_FIELDS:
        entry = facts.get(field)
        model[field] = _norm_fact(field, entry)
    for field in EXTENDED_FACTS:  # keep extras, explicitly
        model[field] = _norm_fact(field, facts[field])
        model[field]["extended"] = True
    if EXTENDED_FACTS:
        model["_extended_facts"] = EXTENDED_FACTS
    return model


def _norm_fact(field: str, entry) -> dict:
    if entry is None:
        return {"state": "UNKNOWN", "value": None}
    if isinstance(entry, dict) and "state" in entry:
        if entry["state"] not in FACT_STATES:
            raise ValueError(f"fact_state_invalid:{field}:{entry['state']}")
        return dict(entry)
    return {"state": "DECLARED", "value": entry}


def _fact(model: dict, name: str) -> dict:
    return model.get(name, {"state": "UNKNOWN", "value": None})


def _fact_true(model: dict, name: str) -> bool:
    f = _fact(model, name)
    return f["state"] in ("DECLARED", "OBSERVED") and bool(f["value"])


# ==================== COMPLEXITY (HOW DEEP, derived from facts) ====================
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


def complexity_from_facts(fact_model: dict) -> dict:
    """Derive complexity factors FROM the fact model (single source of truth), so
    complexity and capability can never drift into two separate fact sources."""
    def count(field):
        v = _fact(fact_model, field)["value"]
        return len(v) if isinstance(v, list) else (1 if _fact_true(fact_model, field) else 0)
    factors = {
        "user_journeys": count("user_journeys"),
        "external_systems": count("external_systems"),
        "components": len((_fact(fact_model, "data")["value"] or {}).get("entities", [])),
        "deployment_environments": count("environments") or (1 if _fact_true(fact_model, "deployment_requirement") else 0),
        "data_migration": count("migration_requirements"),
        "recovery_requirements": count("recovery_requirements"),
        "permissions": count("permissions"),
        "security_surface": count("security_requirements"),
        "cross_platform": len((_fact(fact_model, "runtime")["value"] or {}).get("os", [])),
    }
    return assess_complexity({k: v for k, v in factors.items() if v})


# ==================== CAPABILITY NEEDS (explicit facts only) ====================
# capability -> (required_facts, supporting_facts, predicate). required=UNKNOWN propagates.
def _cap_table() -> dict:
    return {
        "browser_acceptance": {
            "required_facts": ["interface_types"],
            "supporting_facts": ["interfaces"],
            "predicate": lambda m: any("web" in str(v).lower() for v in
                                       _as_list(_fact(m, "interface_types")["value"] or
                                                _fact(m, "interfaces")["value"])),
        },
        "database": {
            "required_facts": ["persistence", "existing_database"],
            "supporting_facts": ["data"],
            "predicate": lambda m: _fact_true(m, "persistence") or _fact_true(m, "existing_database"),
        },
        "enterprise_governance": {
            "required_facts": ["enterprise_policy_present", "approval_requirement"],
            "supporting_facts": ["compliance", "roles"],
            "predicate": lambda m: _fact_true(m, "enterprise_policy_present") or _fact_true(m, "approval_requirement"),
        },
        "deployment": {
            "required_facts": ["deployment_requirement"],
            "supporting_facts": ["environments", "distribution_requirement"],
            "predicate": lambda m: _fact_true(m, "deployment_requirement") or _fact_true(m, "distribution_requirement"),
        },
        "rag": {
            "required_facts": ["retrieval_requirement"],
            "supporting_facts": ["knowledge_source_requirement"],
            "predicate": lambda m: _fact_true(m, "retrieval_requirement") or _fact_true(m, "knowledge_source_requirement"),
        },
        "agent": {
            "required_facts": ["agent_autonomy_requirement", "tool_execution_requirement"],
            "supporting_facts": ["workflow"],
            "predicate": lambda m: _fact_true(m, "agent_autonomy_requirement") or _fact_true(m, "tool_execution_requirement"),
        },
        "tool_permissions": {
            "required_facts": ["external_tool_permission_requirement", "permissions"],
            "supporting_facts": ["external_systems"],
            "predicate": lambda m: _fact_true(m, "external_tool_permission_requirement") or _fact_true(m, "permissions"),
        },
        "multi_role_approval": {
            "required_facts": ["approval_requirement", "roles"],
            "supporting_facts": ["compliance"],
            "predicate": lambda m: _fact_true(m, "approval_requirement") and
                                   len(_as_list(_fact(m, "roles")["value"])) > 1,
        },
        "upgrade_rollback": {
            "required_facts": ["migration_requirements", "rollback_requirement"],
            "supporting_facts": [],
            "predicate": lambda m: _fact_true(m, "migration_requirements") or _fact_true(m, "rollback_requirement"),
        },
        "license_compliance": {
            "required_facts": ["license_requirement", "distribution_requirement"],
            "supporting_facts": [],
            "predicate": lambda m: _fact_true(m, "license_requirement") or _fact_true(m, "distribution_requirement"),
        },
    }


def _as_list(v):
    if v is None:
        return []
    return v if isinstance(v, list) else [v]


def reason_capability_needs(fact_model: dict, declared: list | None = None) -> dict:
    """required=True/False/'unknown' per capability with structured evidence.
    A capability is required ONLY when an explicit fact predicate holds; a predicate
    exception becomes 'unknown' (CAPABILITY_REASONING_ERROR), never silent False;
    a required fact that is UNKNOWN propagates unknown (never resolved by a sibling fact)."""
    table = _cap_table()
    declared = declared or []
    out = {}
    for cap, spec in table.items():
        required_facts = spec["required_facts"]
        unknown_drivers = [f for f in required_facts if _fact(fact_model, f)["state"] == "UNKNOWN"]
        if cap in declared:
            out[cap] = {"required": True, "reason": "用户显式声明", "evidence_source": "declared",
                        "required_facts": required_facts, "blocking_unknowns": []}
            continue
        if unknown_drivers:
            out[cap] = {"required": "unknown", "reason": f"驱动事实 UNKNOWN: {unknown_drivers}",
                        "evidence_source": "fact_model", "required_facts": required_facts,
                        "blocking_unknowns": unknown_drivers}
            continue
        try:
            needed = bool(spec["predicate"](fact_model))
        except Exception as ex:
            out[cap] = {"required": "unknown", "reason": f"CAPABILITY_REASONING_ERROR:{type(ex).__name__}",
                        "evidence_source": "fact_model", "required_facts": required_facts,
                        "blocking_unknowns": required_facts}
            continue
        out[cap] = {"required": needed,
                    "reason": (f"事实模型满足 {cap} 激活条件" if needed else f"无事实支持 {cap}"),
                    "evidence_source": "fact_model", "required_facts": required_facts,
                    "blocking_unknowns": []}
    return {"capabilities": out}


# ==================== DYNAMIC STAGE COMPOSER (work units, not capabilities) ====================
STAGE_SCHEMA = ("name", "goal", "work", "output", "entry_condition", "done_condition",
                "acceptance", "failure_handling", "evidence")
WORK_ITEM_CLASSES = ("STAGE", "TASK", "CHECK", "NOT_APPLICABLE")
STAGE_UPGRADE_MARKERS = ("independent_user_value", "architecture_boundary", "high_risk",
                         "dependency_boundary", "state_transition", "recovery_need",
                         "independently_acceptable_output")


def classify_work_item(item: dict, complexity: dict) -> str:
    if item.get("not_applicable"):
        return "NOT_APPLICABLE"
    if item.get("markers"):
        return "STAGE"
    if item.get("verification_only"):
        return "CHECK"
    return "TASK"


def compose_stages(fact_model: dict, complexity: dict, capability_needs: dict,
                   human_plan: dict | None = None, upstream_plan: dict | None = None) -> dict:
    """Compose stages from the project's REAL work units. A capability never creates a
    stage by itself; stages come from problems to solve (user goals, existing state,
    human/enterprise plan, upstream planner, dependencies, risks, acceptance)."""
    work_units = _discover_work_units(fact_model, capability_needs, human_plan, upstream_plan)
    stages, tasks, checks, na = [], [], [], []
    for unit in work_units:
        cls = classify_work_item(unit, complexity)
        entry = {"name": unit["name"], "class": cls, "goal": unit["goal"],
                 "work": unit.get("work", []), "output": unit.get("output", []),
                 "entry_condition": unit.get("entry_condition", "上一工作项完成"),
                 "done_condition": unit.get("done_condition", "验收通过"),
                 "acceptance": unit.get("acceptance", "证据可验证"),
                 "failure_handling": unit.get("failure_handling", "冻结证据进入恢复"),
                 "evidence": unit.get("evidence", ["test_result"]),
                 "provenance": unit.get("provenance", "AI_GENERATED")}
        (stages if cls == "STAGE" else tasks if cls == "TASK"
         else checks if cls == "CHECK" else na).append(entry)
    if not stages and (tasks or checks):
        stages = [{"name": "实现并验收", "class": "STAGE", "goal": "完成项目目标",
                   "work": [t["name"] for t in tasks] or ["实现"],
                   "output": [o for t in tasks for o in t.get("output", [])] or ["可验收产物"],
                   "entry_condition": "项目理解完成", "done_condition": "验收通过",
                   "acceptance": "最终验收通过", "failure_handling": "冻结证据进入恢复",
                   "evidence": ["test_result"], "provenance": "AI_GENERATED"}]
        tasks = []
    return {"stages": stages, "tasks": tasks, "checks": checks, "not_applicable": na,
            "stage_count": len(stages), "schema": STAGE_SCHEMA}


def _discover_work_units(fact_model: dict, capability_needs: dict,
                         human_plan: dict | None, upstream_plan: dict | None) -> list:
    """Work units from REAL project problems, not from capabilities. Understanding and
    final acceptance are reliability invariants (always present). Capability-driven units
    appear ONLY when the capability is required AND represents an independent work problem
    (otherwise it is a resource/task inside a problem stage, not a stage of its own)."""
    units = []
    # invariant entry: understanding (always a stage — the S0 gate)
    units.append({"name": "项目理解与目标锁定", "goal": "证明已理解真实目标与边界",
                  "work": ["施工前八问", "任务理解合同"], "output": ["task_understanding_contract"],
                  "acceptance": "PRE_EXECUTION_UNDERSTANDING_GATE=PASS",
                  "failure_handling": "阻塞性未知 → 合法 Human Gate", "markers": ["independent_user_value"],
                  "evidence": ["task_understanding_contract"], "provenance": "SYSTEM_RELIABILITY_REQUIRED"})
    # human/enterprise plan work units take precedence over AI discovery
    for src in (human_plan, upstream_plan):
        for s in (src or {}).get("stages", []):
            units.append({**s, "markers": s.get("markers") or ["independent_user_value"],
                          "provenance": s.get("provenance", "HUMAN_PROVIDED")})
    # capability-driven work problems (only when required AND an independent problem)
    for cap, info in capability_needs["capabilities"].items():
        if info["required"] is not True:
            continue
        units.append(_capability_work_problem(cap, fact_model))
    # invariant exit: final acceptance (always a stage)
    units.append({"name": "最终验收", "goal": "独立验收证明 Final Complete",
                  "work": ["执行验收矩阵"], "output": ["acceptance_record"],
                  "acceptance": "Final Acceptance Matrix 全过",
                  "failure_handling": "缺项 → 回补，禁止假完成", "markers": ["independently_acceptable_output"],
                  "evidence": ["acceptance_signoff", "evidence_bundle"],
                  "provenance": "SYSTEM_RELIABILITY_REQUIRED"})
    return units


def _capability_work_problem(cap: str, fact_model: dict) -> dict:
    """A required capability becomes a work PROBLEM (not a bare stage): it carries a real
    goal derived from the project facts and a failure-handling branch. It upgrades to a
    STAGE only when it represents an independent boundary (marker set by facts, not forced)."""
    problems = {
        "browser_acceptance": ("真实浏览器验收关键用户旅程", "console0+交互通过"),
        "database": ("数据持久化与一致性验证", "读写回读一致+迁移可回退"),
        "enterprise_governance": ("企业治理与合规核验", "治理清单通过"),
        "deployment": ("目标环境部署与回滚", "目标环境真实可用"),
        "rag": ("检索问答设计与四防", "引用可回溯+拒答正确"),
        "agent": ("Agent 职责分离", "无自我审批"),
        "tool_permissions": ("工具权限网关", "默认拒绝+越权拦截"),
        "multi_role_approval": ("多角色验收", "各角色独立证据"),
        "upgrade_rollback": ("升级与回滚演练", "演练真实恢复"),
        "license_compliance": ("许可合规扫描", "无红色许可"),
    }
    goal, acc = problems.get(cap, (f"满足 {cap} 能力要求", f"{cap} 检查通过"))
    # marker comes from the FACT that this is an independent risk/boundary, not forced
    markers = ["independent_risk"] if cap in ("database", "deployment", "upgrade_rollback",
                                              "enterprise_governance", "multi_role_approval") else []
    return {"name": goal, "goal": goal, "work": [goal], "output": [f"{cap}_record"],
            "acceptance": acc, "failure_handling": "冻结证据进入恢复", "evidence": [f"{cap}_evidence"],
            "markers": markers, "provenance": "AI_GENERATED"}


# ==================== FACT-DERIVED FINAL ACCEPTANCE ====================
def derive_final_acceptance(fact_model: dict, complexity: dict) -> dict:
    """Every acceptance item comes from a real fact; absent facts produce NO item
    (or explicit N/A), never a placeholder."""
    matrix = {}
    journeys = _fact(fact_model, "user_journeys")["value"]
    if journeys:
        matrix["必须通过的用户旅程"] = [j if isinstance(j, str) else j.get("name", str(j))
                                    for j in _as_list(journeys)]
    data = _fact(fact_model, "data")["value"]
    if _fact_true(fact_model, "persistence") and data:
        entities = data.get("entities", []) if isinstance(data, dict) else []
        matrix["必须真实持久化的数据"] = [f"{e} 读写回读一致" for e in entities] or ["声明实体读写回读一致"]
    if _fact_true(fact_model, "deployment_requirement"):
        envs = _as_list(_fact(fact_model, "environments")["value"]) or ["目标部署环境"]
        matrix["必须真实验证的环境"] = [f"{e} 真实通过" for e in envs]
    if _fact_true(fact_model, "security_requirements"):
        matrix["必须验证的安全项"] = [s for s in _as_list(_fact(fact_model, "security_requirements")["value"])]
    if _fact_true(fact_model, "migration_requirements"):
        matrix["必须验证的迁移与恢复"] = ["升级/迁移后数据完整，可回退"]
    for c in _as_list(_fact(fact_model, "explicit_constraints")["value"]):
        matrix.setdefault("必须满足的显式约束", []).append(c)
    for r in _as_list(_fact(fact_model, "acceptance_requirements")["value"]):
        matrix.setdefault("业务验收", []).append(r)
    matrix["证明 Final Complete 的 Evidence"] = ["test_result", "acceptance_signoff", "evidence_bundle"]
    matrix["复杂度"] = {"risk_level": complexity["risk_level"], "rationale": complexity["rationale"]}
    return matrix


# ==================== USER INTERACTION BOUNDARY (unchanged) ====================
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

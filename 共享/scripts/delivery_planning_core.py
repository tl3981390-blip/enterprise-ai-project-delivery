"""Deterministic cores for UNIVERSAL DYNAMIC DELIVERY (v1.6.0):
project complexity assessment from real structure, capability-need derivation,
DELIVERY_EXECUTION_PLAN construction, user interaction boundary, keyword-signal guard.

Design contracts:
- Complexity/risk is DERIVED from declared structural factors with a named rationale,
  never from project-label keywords (企业/AI/个人/家庭... are CONTEXT signals only).
- The delivery plan is a user-visible navigation map (stages with goal/work/output/
  entry/exit/acceptance/failure-handling + Final Acceptance Matrix); showing it never
  creates an approval gate (NO_STAGE_WAIT unchanged).
- Internal governance is silent in USER mode and translated to human language;
  DIAGNOSTIC mode exposes everything for skill/adapter development."""
from __future__ import annotations

# ==================== PART A: PROJECT COMPLEXITY ASSESSMENT ====================
# Factor -> (weight, why). All factors are STRUCTURAL properties of the project,
# not vocabulary of its label. assess_complexity() returns the level WITH the list of
# factors that drove it, so any LOW/MEDIUM/HIGH/CRITICAL verdict is explainable.
COMPLEXITY_FACTOR_WEIGHTS = {
    "business_goals": (1, "业务目标数量"),
    "user_journeys": (1, "核心用户旅程"),
    "components": (1, "系统组件"),
    "component_dependencies": (1, "组件依赖"),
    "external_systems": (2, "外部系统集成"),
    "data_state_complexity": (2, "数据与状态复杂度"),
    "failure_branches": (1, "失败分支"),
    "recovery_requirements": (2, "恢复需求"),
    "permissions": (2, "权限面"),
    "security_surface": (2, "安全面"),
    "deployment_environments": (2, "部署环境"),
    "concurrency": (2, "并发"),
    "cross_platform": (2, "跨平台"),
    "data_migration": (2, "数据迁移"),
    "irreversible_operations": (3, "不可逆操作"),
    "multi_role_collaboration": (2, "多角色协作"),
    "environment_count": (1, "环境数量"),
    "acceptance_difficulty": (1, "验收难度"),
    "business_risk": (2, "真实业务风险"),
    "existing_system_compatibility": (2, "存量系统兼容"),
    "scope_change_risk": (1, "范围变化风险"),
    "dependency_depth": (1, "依赖深度"),
}
RISK_LEVELS = ("LOW", "MEDIUM", "HIGH", "CRITICAL")
# Bands over the total weighted score. Calibration anchors (all explainable, no mystery):
#   one-goal/one-journey/one-component page edit -> LOW (<=3)
#   permissions + small security surface          -> MEDIUM (4-9)
#   personal cross-platform desktop with sync/    -> HIGH  (10-24)
#   plugins/recovery/migration
#   intense multi-system enterprise change        -> CRITICAL (>=25)
_RISK_BANDS = ((0, 3, "LOW"), (4, 9, "MEDIUM"), (10, 24, "HIGH"), (25, 10**9, "CRITICAL"))
_INTENSE_AMOUNT = 3  # amount >= 3 doubles the factor's weight ("存在计权，高强度双倍")


def assess_complexity(factors: dict) -> dict:
    """factors: {factor_name: int_amount_or_count}. Unknown factor -> error (fail-closed,
    no silent guessing). The verdict always carries its drivers — no mystery scores."""
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
            continue  # zero-amount factors contribute nothing
        intensity = 2 if amount >= _INTENSE_AMOUNT else 1
        contribution = weight * intensity
        total += contribution
        scored.append({"factor": name, "amount": amount, "weight": weight,
                       "contribution": contribution, "meaning": why})
    for low, high, level in _RISK_BANDS:
        if low <= total <= high:
            risk = level
            break
    else:  # pragma: no cover - bands are exhaustive
        risk = "CRITICAL"
    drivers = sorted(scored, key=lambda s: (-s["contribution"], s["factor"]))
    return {
        "risk_level": risk,
        "score": total,
        "dominant_factors": [d["factor"] for d in drivers[:5]],
        "rationale": f"{risk}: " + "; ".join(
            f"{d['meaning']}({d['factor']}={d['amount']}, 贡献{d['contribution']})" for d in drivers[:5]
        ) or f"{risk}: 无显著复杂度因子",
        "factors": scored,
    }


# ==================== PART B: CAPABILITY NEEDS DERIVATION ====================
# Capabilities derive from STRUCTURAL factors + explicit declarations — never from the
# project label. KEYWORD_CONTEXT_SIGNALS lists vocabulary that must never appear in any
# routing decision (guarded by keyword_signals_are_context_only + tests).
FACTOR_CAPABILITY_NEEDS = {
    "permissions": ["tool_permissions"],
    "security_surface": ["enterprise_governance"],
    "multi_role_collaboration": ["multi_role_approval"],
    "data_migration": ["upgrade_rollback"],
    "external_systems": ["tool_permissions"],
    "deployment_environments": ["deployment"],
    "cross_platform": ["deployment"],
    "recovery_requirements": ["upgrade_rollback"],
    "user_journeys": ["browser_acceptance"],
    "component_dependencies": ["database"],
    "data_state_complexity": ["database"],
}
KEYWORD_CONTEXT_SIGNALS = ("企业", "AI", "Agent", "RAG", "Web", "Desktop", "Personal",
                           "Family", "个人", "家庭", "内部")


def derive_capability_needs(factors: dict, declared: list | None = None) -> dict:
    """Needed capabilities = union(factor-derived, user-declared). Label keywords play
    no part: passing {'business_goals': 1} for an 'enterprise' project and a 'family'
    project with identical structure yields IDENTICAL needs (KEYWORD_ROUTING_GUARD)."""
    needed: set[str] = set(declared or [])
    derived: dict[str, list[str]] = {}
    for factor, caps in FACTOR_CAPABILITY_NEEDS.items():
        if factors.get(factor):
            for cap in caps:
                needed.add(cap)
                derived.setdefault(factor, []).append(cap)
    return {"capabilities": sorted(needed), "derived_from_factors": derived,
            "declared": sorted(declared or [])}


def keyword_signals_are_context_only() -> dict:
    """Structural proof that label vocabulary never routes: the decision tables above
    (COMPLEXITY_FACTOR_WEIGHTS / FACTOR_CAPABILITY_NEEDS) contain no keyword from
    KEYWORD_CONTEXT_SIGNALS as a decision KEY. ASCII signals match on word boundaries
    (so 'AI' does not false-positive inside 'failure_branches'); CJK signals match by
    containment. Checked by tests after every change."""
    import re
    tables = {**COMPLEXITY_FACTOR_WEIGHTS, **FACTOR_CAPABILITY_NEEDS}
    leaked = []
    for key in tables:
        for signal in KEYWORD_CONTEXT_SIGNALS:
            hit = (re.search(rf"\b{re.escape(signal)}\b", key, re.IGNORECASE) if signal.isascii()
                   else signal in key)
            if hit:
                leaked.append(f"{key}~{signal}")
    return {"keyword_leak_in_decision_tables": leaked, "pass": not leaked}


# ==================== PART C: DELIVERY EXECUTION PLAN ====================
# Fixed per stage: Goal / Output / Acceptance / Evidence (+ entry/exit/failure).
# NOT fixed: stage content and count — stages come from the active lifecycle + activated
# capabilities + complexity-scaled depth. Granularity rule: a stage must carry at least
# one independent value marker, otherwise it is a TASK inside the previous stage.
STAGE_BLUEPRINTS = {
    "00_总控": {"goal": "证明已真正理解项目并锁定合同", "work": ["施工前八问", "任务理解合同", "理解门禁"],
     "outputs": ["task_understanding_contract"], "acceptance": "PRE_EXECUTION_UNDERSTANDING_GATE=PASS",
     "failure_handling": "阻塞性未知 → 向用户提出会改变方案的问题（合法 Human Gate）"},
    "01_项目理解": {"goal": "澄清真实目标/用户/价值", "work": ["目标声明", "干系人确认"], "outputs": ["goal_statement"],
     "acceptance": "目标/交付物/成功标准可判定", "failure_handling": "缺真实目标 → 回 S0，禁止推进"},
    "02_当前状态审计": {"goal": "盘点已有资产真伪", "work": ["现状扫描", "不可改区标记"], "outputs": ["state_audit"],
     "acceptance": "每项有 NOT_FOUND/PRESENT_UNVERIFIED/VERIFIED_* 状态", "failure_handling": "越界扫描 → BLOCKED"},
    "03_需求与范围": {"goal": "锁定范围与非目标", "work": ["MoSCoW", "EARS 验收条件"], "outputs": ["requirements_scope"],
     "acceptance": "验收标准可判定", "failure_handling": "不可判定 → 退回澄清"},
    "04_SDD规格": {"goal": "先规格后编码", "work": ["全维度规格"], "outputs": ["spec"], "acceptance": "规格缺项=0",
     "failure_handling": "缺项 → blocked，禁止编码"},
    "05_TDD与测试策略": {"goal": "判断式测试策略", "work": ["分层测试适用性", "关键测试清单"], "outputs": ["test_strategy"],
     "acceptance": "核心逻辑均有测试判定", "failure_handling": "「简单不用测」→ 拒绝"},
    "06_架构设计": {"goal": "组件/接口/部署形态定型", "work": ["架构决策记录"], "outputs": ["architecture"],
     "acceptance": "评审通过", "failure_handling": "不可行项 → 回规格"},
    "11_施工管理与增量实现": {"goal": "按可验收增量交付", "work": ["增量施工", "DoD 检查"], "outputs": ["working_increment"],
     "acceptance": "增量验收通过 + Evidence", "failure_handling": "失败 → 冻结证据进入 12"},
    "12_失败处理与恢复": {"goal": "有界恢复不丢证据", "work": ["根因分类", "恢复阶梯"], "outputs": ["recovery_record"],
     "acceptance": "恢复再验证通过或安全回滚", "failure_handling": "预算耗尽 → 人工恢复包"},
    "14_多角色验收": {"goal": "独立验收（视角随干系人缩放）", "work": ["必需视角签核"], "outputs": ["acceptance_signoff"],
     "acceptance": "全部必需视角 PASS+证据", "failure_handling": "缺签 → blocked"},
    "15_Evidence与防假验收": {"goal": "证据链完整可验", "work": ["证据归档", "哈希"], "outputs": ["evidence_bundle"],
     "acceptance": "Evidence 校验通过", "failure_handling": "缺证据 → 不承认完成"},
    "19_最终交付与经验沉淀": {"goal": "最终验收与经验入库", "work": ["最终报告", "经验分类"], "outputs": ["final_report"],
     "acceptance": "Final Acceptance Matrix 全过", "failure_handling": "缺项 → 回补，禁止假完成"},
    # capability stages (activated on demand)
    "07_RAG设计": {"goal": "检索问答可靠（四防）", "work": ["知识源/索引/引用/拒答"], "outputs": ["rag_design"],
     "acceptance": "四防检查 PASS", "failure_handling": "引用不可回溯 → blocked"},
    "08_Agent设计": {"goal": "角色职责分离", "work": ["职责矩阵"], "outputs": ["agent_design"],
     "acceptance": "无自我审批", "failure_handling": "越权角色 → 拒绝"},
    "09_MCP与工具权限网关": {"goal": "权限矩阵默认拒绝", "work": ["权限矩阵"], "outputs": ["permission_matrix"],
     "acceptance": "权限检查 PASS", "failure_handling": "越权 → 拒绝"},
    "10_企业治理与合规": {"goal": "治理合规满足", "work": ["治理清单"], "outputs": ["governance_record"],
     "acceptance": "治理检查 PASS", "failure_handling": "缺责任人/出域 → blocked"},
    "13_浏览器真实验收": {"goal": "真实浏览器验证", "work": ["关键旅程操作"], "outputs": ["browser_capture"],
     "acceptance": "console0+交互通过", "failure_handling": "无 Web UI → NOT_APPLICABLE 记录"},
    "16_部署": {"goal": "目标环境真实可用", "work": ["Build/Deploy/回滚"], "outputs": ["deploy_record"],
     "acceptance": "目标环境验证", "failure_handling": "失败 → 回滚不硬上"},
    "17_License与合规": {"goal": "许可可证明", "work": ["许可扫描"], "outputs": ["license_report"],
     "acceptance": "无红色许可", "failure_handling": "无法证明 → 阻断"},
    "18_升级与回滚": {"goal": "版本演进可回退", "work": ["迁移/回滚演练"], "outputs": ["upgrade_rollback_drill"],
     "acceptance": "演练真实恢复", "failure_handling": "不能回退 → 不发布"},
}
PLAN_STAGE_ORDER = ("00_总控", "01_项目理解", "02_当前状态审计", "03_需求与范围", "04_SDD规格",
                    "05_TDD与测试策略", "06_架构设计", "07_RAG设计", "08_Agent设计",
                    "09_MCP与工具权限网关", "10_企业治理与合规", "11_施工管理与增量实现",
                    "12_失败处理与恢复", "13_浏览器真实验收", "14_多角色验收",
                    "15_Evidence与防假验收", "16_部署", "17_License与合规", "18_升级与回滚",
                    "19_最终交付与经验沉淀")
VALUE_MARKERS = ("independent_user_value", "architecture_boundary", "dependency_boundary",
                 "independent_risk", "state_boundary", "independently_acceptable_output")


def build_delivery_execution_plan(user_goal: str, complexity: dict, capability_needs: dict,
                                  active_stages: list, not_applicable: dict | None = None,
                                  stage_value_markers: dict | None = None) -> dict:
    """User-visible DELIVERY_EXECUTION_PLAN. Stage granularity is enforced: a stage with
    no value marker is demoted to a TASK of its predecessor (never a fake stage)."""
    stages = []
    for name in PLAN_STAGE_ORDER:
        if name not in active_stages:
            continue
        bp = STAGE_BLUEPRINTS[name]
        entry = {"阶段名称": name, "阶段目标": bp["goal"], "主要工作": bp["work"],
                 "阶段输出": bp["outputs"], "完成条件": bp["acceptance"],
                 "进入条件": "上一阶段完成条件满足" if stages else "理解门禁通过",
                 "验收方式": bp["acceptance"], "失败后的处理": bp["failure_handling"]}
        markers = (stage_value_markers or {}).get(name)
        if markers:
            entry["价值标记"] = markers
            stages.append(entry)
        elif name in ("00_总控",):  # the gate itself is always a real stage
            entry["价值标记"] = ["independently_acceptable_output"]
            stages.append(entry)
        else:
            if stages:  # demote: no independent value -> task of previous stage
                stages[-1].setdefault("内含任务", []).append(
                    {"任务": name, "目标": bp["goal"], "输出": bp["outputs"]})
            else:
                stages.append(entry)
    matrix = {
        "最终必须存在的真实能力": capability_needs["capabilities"] or ["核心功能按验收标准"],
        "必须通过的用户旅程": [f"旅程{i+1}" for i in range(max(1, min(int(
            complexity.get("dominant_factors") and 3 or 1), 3)))],
        "必须验证的失败分支": [f for f in ("recovery_requirements", "irreversible_operations")
                         if f in complexity.get("dominant_factors", [])] or ["主要失败路径至少一支"],
        "必须真实持久化的数据": ["核心实体读写回读一致"],
        "必须真实验证的环境": sorted({"本地"} | ({"目标部署环境"} if "deployment" in
                                       capability_needs["capabilities"] else set())),
        "必须验证的风险": complexity.get("dominant_factors", [])[:3],
        "证明 Final Complete 的 Evidence": ["test_result", "acceptance_signoff", "evidence_bundle"],
    }
    return {"plan_type": "DELIVERY_EXECUTION_PLAN", "user_goal": user_goal,
            "complexity": {"risk_level": complexity["risk_level"], "rationale": complexity["rationale"]},
            "dynamic_stages": stages,
            "not_applicable_stages": not_applicable or {},
            "final_acceptance_matrix": matrix,
            "continuation": "SHOW_PLAN_THEN_CONTINUE (计划是导航图，不是审批门；无真实阻塞即自动继续)"}


# ==================== PART D: USER INTERACTION BOUNDARY ====================
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
    """Filter/translate internal governance for the requested mode. USER mode never
    leaks raw governance vocabulary; DIAGNOSTIC mode passes everything through."""
    if mode not in INTERACTION_MODES:
        raise ValueError(f"interaction_mode_invalid:{mode}")
    if mode == "DIAGNOSTIC":
        return {"mode": mode, "exposed": state}
    user_state = {}
    for key, value in state.items():
        if key in WHAT_TO_EXPOSE_USER or key in ("user_goal", "questions", "delivery_plan",
                                                 "blockers", "failures", "stage_results",
                                                 "final_acceptance"):
            user_state[key] = value
    translations = {}
    for code, human in INTERNAL_STATE_TRANSLATIONS.items():
        if code in str(state):
            translations[code] = human
    return {"mode": mode, "user_visible": user_state, "translations": translations}

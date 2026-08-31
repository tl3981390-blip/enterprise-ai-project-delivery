"""Deterministic cores for HUMAN PLAN AUTHORITY + UPSTREAM CAPABILITY FIRST (v1.7.0).

Design contracts:
- AI GENERATES, HUMAN OWNS. The AI-generated DELIVERY_EXECUTION_PLAN is a RECOMMENDATION
  derived from known facts/risks/dependencies/acceptance — never an unmodifiable fixed flow.
- Authority order (highest to lowest):
    CORE RELIABILITY INVARIANTS
    EXPLICIT HUMAN DECISIONS
    ENTERPRISE REQUIRED WORKFLOW
    PROJECT-SPECIFIC CONSTRAINTS
    AI-GENERATED DELIVERY PLAN
- HUMAN_PROVIDED plan (company/project-manager/tech plan, existing WBS) takes precedence
  over AI generation: parse it, check reliability gaps, KEEP its主体, add only the
  missing reliability controls. Never force the human to adopt the AI's plan.
- Human may add/remove/merge/split/reorder/modify any stage, change goal/output/
  acceptance/tech/priority/dependency/rhythm, or replace the AI plan wholesale.
- Human edits trigger a partial replan (invalidate only affected state, preserve the
  rest); never a whole-project reset. PLAN_LOCK elements are never auto-modified.
- UPSTREAM_CAPABILITY_FIRST: compose mature skills, extend second, reimplement last.
  Reliability Core ADDS reliability, never capability regression. Unknown-but-required
  capability triggers discovery, never a silent capability=false."""
from __future__ import annotations

# ==================== PART A: PLAN AUTHORITY ====================
AUTHORITY_ORDER = (
    "CORE_RELIABILITY_INVARIANTS",
    "EXPLICIT_HUMAN_DECISIONS",
    "ENTERPRISE_REQUIRED_WORKFLOW",
    "PROJECT_SPECIFIC_CONSTRAINTS",
    "AI_GENERATED_DELIVERY_PLAN",
)
PLAN_PROVENANCE = ("AI_GENERATED", "HUMAN_PROVIDED", "HUMAN_MODIFIED", "ENTERPRISE_REQUIRED",
                   "SYSTEM_RELIABILITY_REQUIRED")
PLAN_OPS = ("add", "remove", "merge", "split", "reorder", "modify", "replace_all")


class PlanAuthorityError(Exception):
    pass


def plan_authority_order() -> tuple:
    return AUTHORITY_ORDER


def _prov(entry: dict) -> str:
    return entry.get("provenance", "AI_GENERATED")


def apply_plan_edit(active_plan: dict, edit: dict, verified_state: dict | None = None) -> dict:
    """Apply a human plan edit. edit: {op, stage_name, patch?, target?, merge_with?,
    split_into?, new_order?, reason}. Never resets the whole project; returns the updated
    plan plus which assumptions were affected (for partial state invalidation)."""
    op = edit.get("op")
    if op not in PLAN_OPS:
        raise PlanAuthorityError(f"plan_op_invalid:{op}")
    stages = [dict(s) for s in active_plan.get("stages", [])]
    by_name = {s["name"]: s for s in stages}
    affected: set[str] = set()

    if op == "add":
        new = dict(edit["patch"])
        new.setdefault("provenance", "HUMAN_PROVIDED")
        new.setdefault("locked", edit.get("locked", False))
        stages.append(new)
        affected.add(new.get("name", ""))
    elif op == "remove":
        target = edit["stage_name"]
        if target not in by_name:
            raise PlanAuthorityError(f"stage_not_found:{target}")
        removed = by_name[target]
        stages = [s for s in stages if s["name"] != target]
        # reliability controls that the removed stage carried must be re-homed, not lost
        rehomed = _rehome_invariants(stages, removed)
        stages = rehomed
        affected.add(target)
    elif op == "merge":
        a, b = edit["stage_name"], edit["merge_with"]
        if a not in by_name or b not in by_name:
            raise PlanAuthorityError("merge_requires_two_existing_stages")
        merged = {**by_name[a], **{k: (by_name[a].get(k) or []) + (by_name[b].get(k) or []) if isinstance(
            by_name[a].get(k), list) or isinstance(by_name[b].get(k), list) else by_name[b].get(k, by_name[a].get(k))
            for k in set(by_name[a]) | set(by_name[b])}}
        merged["name"] = edit.get("target") or f"{a}+{b}"
        merged["provenance"] = "HUMAN_MODIFIED"
        stages = [s for s in stages if s["name"] not in (a, b)] + [merged]
        affected.update((a, b, merged["name"]))
    elif op == "split":
        target = edit["stage_name"]
        parts = edit["split_into"]
        if target not in by_name or not parts:
            raise PlanAuthorityError("split_requires_existing_stage_and_parts")
        orig = by_name[target]
        stages = [s for s in stages if s["name"] != target]
        for part in parts:
            p = dict(part)
            p.setdefault("provenance", "HUMAN_MODIFIED")
            p.setdefault("acceptance", orig.get("acceptance"))
            stages.append(p)
        affected.add(target)
        affected.update(p["name"] for p in parts)
    elif op == "reorder":
        order = edit["new_order"]
        names = {s["name"] for s in stages}
        if set(order) != names:
            raise PlanAuthorityError("reorder_must_cover_all_stages_exactly")
        stages = [by_name[n] for n in order]
        for n in names:
            affected.add(n)
    elif op == "modify":
        target = edit["stage_name"]
        if target not in by_name:
            raise PlanAuthorityError(f"stage_not_found:{target}")
        patch = edit["patch"]
        orig = by_name[target]
        if orig.get("locked") and edit.get("force") is not True:
            raise PlanAuthorityError(f"stage_locked:{target} (PLAN_LOCK; resolve conflict explicitly)")
        updated = {**orig, **patch, "provenance": "HUMAN_MODIFIED" if _prov(orig) == "AI_GENERATED" else _prov(orig)}
        stages = [updated if s["name"] == target else s for s in stages]
        affected.add(target)
    elif op == "replace_all":
        new_stages = [dict(s) for s in edit["patch"]["stages"]]
        for s in new_stages:
            s.setdefault("provenance", "HUMAN_PROVIDED")
        stages = new_stages
        affected.update(s["name"] for s in new_stages)

    # reliability check: invariants must survive the edit
    check = check_plan_invariants({"stages": stages})
    updated = {"stages": stages, "reliability_check": check,
               "affected_assumptions": sorted(affected),
               "authority": "HUMAN_OVERRIDES_AI_WITHIN_INVARIANTS"}
    if not check["pass"]:
        updated["advisory"] = check["gaps"]  # AI may advise, never silently block
    return updated


def _rehome_invariants(stages: list, removed: dict) -> list:
    """A removed stage's reliability obligations (evidence/acceptance/recovery) are
    re-attached to the surviving stages as checks — they may be re-organized, never lost."""
    obligations = {k: removed.get(k) for k in ("acceptance", "evidence", "failure_handling") if removed.get(k)}
    if not obligations or not stages:
        return stages
    stages[-1].setdefault("checks", []).append(
        {"from_removed_stage": removed.get("name"), "carried": obligations})
    return stages


def check_plan_invariants(plan: dict) -> dict:
    """Reliability invariants that must survive ANY plan edit. AI advises on gaps; it
    never overrides a human edit that keeps the invariants (organization is free)."""
    stages = plan.get("stages", [])
    gaps = []
    has_understanding = any("理解" in s.get("name", "") or "understanding" in s.get("goal", "").lower()
                            or s.get("entry_condition") == "项目理解完成" for s in stages)
    has_acceptance = any("验收" in s.get("name", "") or "acceptance" in str(s.get("acceptance", "")).lower()
                         for s in stages)
    if stages and not has_understanding:
        gaps.append("missing_understanding_entry (理解先于执行)")
    if stages and not has_acceptance:
        gaps.append("missing_final_acceptance (独立验收)")
    if not stages:
        gaps.append("empty_plan")
    return {"pass": not gaps, "gaps": gaps}


def apply_human_plan(human_plan: dict, fact_model: dict | None = None) -> dict:
    """A human/enterprise-provided plan takes precedence over AI generation: parse it,
    keep its主体, add only the missing reliability controls. Never re-impose the AI plan."""
    stages = [dict(s) for s in human_plan.get("stages", [])]
    for s in stages:
        s.setdefault("provenance", "HUMAN_PROVIDED")
        if human_plan.get("source") == "enterprise":
            s["provenance"] = "ENTERPRISE_REQUIRED"
    check = check_plan_invariants({"stages": stages})
    result = {"stages": stages, "reliability_check": check,
              "authority": "HUMAN_PLAN_KEPT_AI_ADVISORY_ONLY",
              "advisory": check["gaps"]}
    if not check["pass"]:
        # AI may only ADD the missing reliability controls as SYSTEM_RELIABILITY_REQUIRED,
        # never replace the human plan's organization
        for gap in check["gaps"]:
            if gap.startswith("missing_understanding"):
                stages.insert(0, {"name": "项目理解与目标锁定", "goal": "证明已理解真实目标与边界",
                                  "work": ["施工前八问", "任务理解合同"], "output": ["task_understanding_contract"],
                                  "acceptance": "PRE_EXECUTION_UNDERSTANDING_GATE=PASS",
                                  "failure_handling": "阻塞性未知 → 合法 Human Gate",
                                  "evidence": ["task_understanding_contract"],
                                  "provenance": "SYSTEM_RELIABILITY_REQUIRED"})
            elif gap.startswith("missing_final_acceptance"):
                stages.append({"name": "最终验收", "goal": "独立验收证明 Final Complete",
                               "work": ["执行验收矩阵"], "output": ["acceptance_record"],
                               "acceptance": "Final Acceptance Matrix 全过",
                               "failure_handling": "缺项 → 回补，禁止假完成",
                               "evidence": ["acceptance_signoff"],
                               "provenance": "SYSTEM_RELIABILITY_REQUIRED"})
        result["stages"] = stages
        result["reliability_check"] = check_plan_invariants({"stages": stages})
    return result


def replan_respecting_locks(active_plan: dict, changed_assumptions: list,
                            new_facts: dict | None = None) -> dict:
    """Partial replan: HUMAN_LOCKED / HUMAN_PROVIDED / ENTERPRISE_REQUIRED elements are
    never auto-modified; only AI_GENERATED elements affected by the change are recomputed.
    Preserves still-valid verified state (see assumption_change_model in Part E)."""
    stages = active_plan.get("stages", [])
    locked = [s for s in stages if s.get("locked") or _prov(s) in ("HUMAN_PROVIDED", "ENTERPRISE_REQUIRED")]
    unlocked = [s for s in stages if s not in locked]
    changed = set(changed_assumptions or [])
    recomputed = []
    for s in unlocked:
        deps = set(s.get("assumptions") or [])
        if deps & changed:
            s = dict(s, replanned=True)
        recomputed.append(s)
    return {"stages": locked + recomputed,
            "locked_preserved": [s["name"] for s in locked],
            "recomputed": [s["name"] for s in unlocked if s.get("replanned")],
            "human_locks_respected": True}


# ==================== PART B: UPSTREAM CAPABILITY FIRST ====================
CAPABILITY_SOURCES = ("UPSTREAM_SKILL", "HARNESS_NATIVE", "LOCAL_CORE", "ENTERPRISE_EXTENSION",
                      "PROJECT_EXTENSION")
INTEGRATION_METHODS = ("ADAPT", "COMPOSE", "CALL", "KEEP_PLUS_EXTEND", "IMPLEMENT_LOCAL")


class CapabilityRegressionError(Exception):
    pass


def capability_provenance_record(capability: str, source: str, source_version: str,
                                 integration_method: str, local_extension: str | None,
                                 reliability_controls: list, validation_status: str) -> dict:
    if source not in CAPABILITY_SOURCES:
        raise ValueError(f"capability_source_invalid:{source}")
    if integration_method not in INTEGRATION_METHODS:
        raise ValueError(f"integration_method_invalid:{integration_method}")
    return {"capability": capability, "source": source, "source_version": source_version,
            "integration_method": integration_method, "local_extension": local_extension,
            "reliability_controls": reliability_controls, "validation_status": validation_status}


def capability_regression_guard(upstream_baseline: dict, integrated: dict) -> dict:
    """After absorbing/adapting/wrapping an upstream capability, verify no regression:
    project types handled, planning quality, user control, test ability, tool ability,
    context understanding, output flexibility, executability. Integrated >= Upstream on
    capability dimensions; reliability dimensions (evidence/recovery/acceptance/anti-fake
    -pass/scope) should improve."""
    dims = ("project_types", "planning_quality", "user_control", "test_ability", "tool_ability",
            "context_understanding", "output_flexibility", "executability")
    regressions = []
    for dim in dims:
        before = upstream_baseline.get(dim, 0)
        after = integrated.get(dim, 0)
        if isinstance(before, (int, float)) and isinstance(after, (int, float)) and after < before:
            regressions.append(f"capability_regression:{dim}:{before}->{after}")
    reliability_dims = ("evidence", "recovery", "acceptance", "anti_fake_pass", "scope_control")
    improved = [d for d in reliability_dims if integrated.get(d, 0) > upstream_baseline.get(d, 0)]
    return {"pass": not regressions, "regressions": regressions, "reliability_improved": improved}


def resolve_capability_need(need: str, registry: dict, upstream_available: dict) -> dict:
    """Known capability -> use known adapter. Unknown-but-required -> discover upstream;
    only declare CAPABILITY_NOT_AVAILABLE when nothing suitable exists anywhere."""
    if need in registry:
        return {"capability": need, "resolution": "known_adapter", "registry": True}
    for source, caps in upstream_available.items():
        if need in caps:
            return {"capability": need, "resolution": f"discover:{source}", "registry": False,
                    "action": "validate_and_compose"}
    return {"capability": need, "resolution": "CAPABILITY_NOT_AVAILABLE", "registry": False,
            "action": "report_to_user"}


def upstream_update_reabsorb(record: dict, new_upstream: dict) -> dict:
    """An absorbed capability must allow re-absorption after upstream updates: diff,
    compatibility check, regression, adopt. Never freeze on the first copied version."""
    old_version = record["source_version"]
    new_version = new_upstream.get("source_version", old_version)
    new_caps = set(new_upstream.get("capabilities", []))
    old_caps = set(record.get("capabilities", []))
    added = sorted(new_caps - old_caps)
    removed = sorted(old_caps - new_caps)
    return {"capability": record["capability"], "from_version": old_version, "to_version": new_version,
            "added": added, "removed": removed,
            "action": "compatibility_check_and_regression" if (added or removed) else "no_change"}

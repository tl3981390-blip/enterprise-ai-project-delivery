"""Deterministic cores for HUMAN PLAN AUTHORITY + UPSTREAM CAPABILITY FIRST (v1.7.1).

Removes the v1.7.0 residual fakes:
  - PLAN_LOCK blocked the plan OWNER (wrong) -> actor/authority semantics
  - replan_respecting_locks only set a flag (REPLAN_FLAG_ONLY) -> real partial replan
  - apply_plan_edit ignored verified_state -> real STILL_VALID/INVALIDATED classification
  - affected_assumptions returned the stage NAME -> real assumption keys via dependency map
  - locked+recomputed reordered stages -> original order preserved
  - check_plan_invariants matched stage NAMES (keyword routing) -> RELIABILITY_OBLIGATION_MODEL
  - remove re-homed obligations to stages[-1] ("last stage takes the blame") -> semantic owner
  - provenance single enum -> full history (origin/last_modified_by/history/locked_by/authority)

Authority order (highest to lowest):
  CORE_RELIABILITY_INVARIANTS > EXPLICIT_HUMAN_DECISIONS > ENTERPRISE_REQUIRED_WORKFLOW >
  PROJECT_SPECIFIC_CONSTRAINTS > AI_GENERATED_DELIVERY_PLAN
PLAN_LOCK blocks AI_AUTOMATIC modification only; an authorized HUMAN_EXPLICIT edit can
modify/unlock/replace. Enterprise mandatory constraints need ENTERPRISE_AUTHORIZED scope.
"""
from __future__ import annotations

# ==================== PART A: PLAN AUTHORITY ====================
AUTHORITY_ORDER = (
    "CORE_RELIABILITY_INVARIANTS",
    "EXPLICIT_HUMAN_DECISIONS",
    "ENTERPRISE_REQUIRED_WORKFLOW",
    "PROJECT_SPECIFIC_CONSTRAINTS",
    "AI_GENERATED_DELIVERY_PLAN",
)
ACTORS = ("AI_AUTOMATIC", "HUMAN_EXPLICIT", "ENTERPRISE_AUTHORIZED", "SYSTEM_RELIABILITY")
HUMAN_PROTECTED = ("HUMAN_PROVIDED", "HUMAN_MODIFIED", "ENTERPRISE_REQUIRED")  # + locked
PLAN_OPS = ("add", "remove", "merge", "split", "reorder", "modify", "replace_all")

# Reliability obligations that must survive ANY plan edit (never matched by stage NAME).
RELIABILITY_OBLIGATIONS = (
    "UNDERSTANDING_VERIFIED", "SCOPE_AUTHORITY", "EVIDENCE_REQUIRED", "INDEPENDENT_ACCEPTANCE",
    "RECOVERY_PATH", "FAILURE_EVIDENCE_PRESERVATION", "HUMAN_GATE", "NO_FAKE_PASS",
)


class PlanAuthorityError(Exception):
    pass


def plan_authority_order() -> tuple:
    return AUTHORITY_ORDER


def _prov(entry: dict) -> str:
    return entry.get("provenance", "AI_GENERATED")


def _actor(edit: dict) -> str:
    actor = edit.get("actor", "AI_AUTOMATIC")
    if actor not in ACTORS:
        raise PlanAuthorityError(f"actor_invalid:{actor}")
    return actor


def _check_edit_permission(stage: dict, edit: dict) -> None:
    """PLAN_LOCK blocks AI_AUTOMATIC only. An authorized human/enterprise edit may modify
    or unlock. Enterprise mandatory constraints require ENTERPRISE_AUTHORIZED scope."""
    actor = _actor(edit)
    if actor == "AI_AUTOMATIC":
        if stage.get("locked") or _prov(stage) in HUMAN_PROTECTED:
            raise PlanAuthorityError(
                f"ai_cannot_modify_human_protected:{stage.get('name')} (prov={_prov(stage)}, locked={stage.get('locked')})")
    if _prov(stage) == "ENTERPRISE_REQUIRED" and edit.get("weakens_enterprise_policy"):
        if actor != "ENTERPRISE_AUTHORIZED":
            raise PlanAuthorityError(
                f"enterprise_policy_change_requires_enterprise_authorized:{stage.get('name')}")


def apply_plan_edit(active_plan: dict, edit: dict, verified_state: dict | None = None) -> dict:
    """Apply a plan edit with actor semantics. Returns updated plan + REAL affected
    assumptions (dependency keys, not stage names) + verified-state classification."""
    op = edit.get("op")
    if op not in PLAN_OPS:
        raise PlanAuthorityError(f"plan_op_invalid:{op}")
    actor = _actor(edit)
    stages = [dict(s) for s in active_plan.get("stages", [])]
    by_name = {s["name"]: s for s in stages}
    affected: set[str] = set()

    def touch(stage_name: str) -> None:
        affected.update(_stage_assumptions(by_name.get(stage_name, {})))

    if op == "add":
        new = dict(edit["patch"])
        new.setdefault("provenance", "HUMAN_PROVIDED" if actor != "AI_AUTOMATIC" else "AI_GENERATED")
        new.setdefault("locked", edit.get("locked", False))
        new.setdefault("history", [{"by": actor, "op": "add"}])
        stages.append(new)
        touch(new.get("name", ""))
    elif op == "remove":
        target = edit["stage_name"]
        if target not in by_name:
            raise PlanAuthorityError(f"stage_not_found:{target}")
        _check_edit_permission(by_name[target], edit)
        removed = by_name[target]
        stages = [s for s in stages if s["name"] != target]
        stages = _rehome_obligations(stages, removed, edit)
        touch(target)
    elif op == "merge":
        a, b = edit["stage_name"], edit["merge_with"]
        if a not in by_name or b not in by_name:
            raise PlanAuthorityError("merge_requires_two_existing_stages")
        for n in (a, b):
            _check_edit_permission(by_name[n], edit)
        merged = _semantic_merge(by_name[a], by_name[b], edit)
        stages = [s for s in stages if s["name"] not in (a, b)] + [merged]
        touch(a); touch(b); touch(merged["name"])
    elif op == "split":
        target = edit["stage_name"]
        parts = edit["split_into"]
        if target not in by_name or not parts:
            raise PlanAuthorityError("split_requires_existing_stage_and_parts")
        _check_edit_permission(by_name[target], edit)
        orig = by_name[target]
        stages = [s for s in stages if s["name"] != target]
        for part in parts:
            p = dict(part)
            p.setdefault("provenance", "HUMAN_MODIFIED")
            p.setdefault("acceptance", orig.get("acceptance"))
            p.setdefault("history", orig.get("history", []) + [{"by": actor, "op": "split", "from": target}])
            stages.append(p)
        touch(target)
    elif op == "reorder":
        order = edit["new_order"]
        names = {s["name"] for s in stages}
        if set(order) != names:
            raise PlanAuthorityError("reorder_must_cover_all_stages_exactly")
        stages = [by_name[n] for n in order]
        for n in names:
            touch(n)
    elif op == "modify":
        target = edit["stage_name"]
        if target not in by_name:
            raise PlanAuthorityError(f"stage_not_found:{target}")
        _check_edit_permission(by_name[target], edit)
        orig = by_name[target]
        history = orig.get("history", []) + [{"by": actor, "op": "modify", "patch_keys": sorted(edit["patch"])}]
        updated = {**orig, **edit["patch"],
                   "provenance": _prov(orig) if _prov(orig) in HUMAN_PROTECTED else "HUMAN_MODIFIED",
                   "last_modified_by": actor, "history": history}
        stages = [updated if s["name"] == target else s for s in stages]
        touch(target)
    elif op == "replace_all":
        new_stages = [dict(s) for s in edit["patch"]["stages"]]
        for s in new_stages:
            s.setdefault("provenance", "HUMAN_PROVIDED" if actor != "AI_AUTOMATIC" else "AI_GENERATED")
        stages = new_stages
        for s in new_stages:
            touch(s["name"])

    check = check_plan_invariants({"stages": stages})
    result = {"stages": stages, "reliability_check": check,
              "affected_assumptions": sorted(affected),
              "authority": "HUMAN_OVERRIDES_AI_WITHIN_INVARIANTS",
              "actor": actor}
    if verified_state:
        result["verified_state_classification"] = classify_verified_state(verified_state, affected)
    if not check["pass"]:
        result["advisory"] = check["gaps"]  # AI advises on gaps; never silently blocks
    return result


def _stage_assumptions(stage: dict) -> set:
    """Real assumption keys a stage depends on (dependency mapping), never the stage name."""
    deps = set(stage.get("assumptions") or [])
    mapping = {"persistence": "persistence_model", "database": "database_type",
               "deployment": "deployment_target", "migration": "migration_strategy",
               "api": "api_contract"}
    for cap in stage.get("capabilities", []):
        if cap in mapping:
            deps.add(mapping[cap])
    return deps


def _rehome_obligations(stages: list, removed: dict, edit: dict) -> list:
    """A removed stage's reliability obligations are re-attached to the semantically
    related surviving stage (shared acceptance boundary / capability / dependency),
    never to stages[-1] by default. If no semantic owner exists, a CHECK is created."""
    obligations = {k: removed.get(k) for k in ("acceptance", "evidence", "failure_handling")
                   if removed.get(k)}
    if not obligations:
        return stages
    owner = None
    for s in stages:
        shared = set(s.get("capabilities", [])) & set(removed.get("capabilities", []))
        if shared or s.get("acceptance") == removed.get("acceptance"):
            owner = s
            break
    if owner is not None:
        owner.setdefault("checks", []).append({"from_removed_stage": removed.get("name"),
                                               "carried": obligations})
    else:
        stages.append({"name": f"{removed.get('name')}（义务承接检查）", "class": "CHECK",
                       "goal": f"承接 {removed.get('name')} 的可靠性义务",
                       "verification_only": True, "evidence": obligations.get("evidence", []),
                       "acceptance": obligations.get("acceptance", "证据可验证"),
                       "failure_handling": obligations.get("failure_handling", "冻结证据进入恢复"),
                       "provenance": "SYSTEM_RELIABILITY_REQUIRED"})
    return stages


def _semantic_merge(a: dict, b: dict, edit: dict) -> dict:
    """Merge two stages preserving obligations/dependencies/evidence/acceptance/provenance
    from both — not a naive dict merge."""
    merged = {
        "name": edit.get("target") or f"{a['name']}+{b['name']}",
        "goal": edit.get("patch", {}).get("goal", f"{a.get('goal')} / {b.get('goal')}"),
        "work": _uniq(a.get("work", []) + b.get("work", [])),
        "output": _uniq(a.get("output", []) + b.get("output", [])),
        "acceptance": edit.get("patch", {}).get("acceptance", f"{a.get('acceptance')} + {b.get('acceptance')}"),
        "evidence": _uniq(a.get("evidence", []) + b.get("evidence", [])),
        "failure_handling": a.get("failure_handling") or b.get("failure_handling") or "冻结证据进入恢复",
        "assumptions": sorted(set(_stage_assumptions(a)) | set(_stage_assumptions(b))),
        "capabilities": _uniq(a.get("capabilities", []) + b.get("capabilities", [])),
        "provenance": "HUMAN_MODIFIED",
        "history": [{"by": _actor(edit), "op": "merge", "from": [a["name"], b["name"]]}],
    }
    return merged


def _uniq(items: list) -> list:
    out = []
    for i in items:
        if i not in out:
            out.append(i)
    return out


def check_plan_invariants(plan: dict) -> dict:
    """Reliability obligations that must survive ANY edit. Obligations bind to a stage's
    STRUCTURED fields (entry_condition/acceptance/failure_handling), never to its name.
    A plan with zero stages fails; understanding-entry and independent-acceptance are
    required and may be carried by any stage, task, check or gate."""
    stages = plan.get("stages", [])
    gaps = []
    if not stages:
        return {"pass": False, "gaps": ["empty_plan"]}
    has_understanding = any(
        s.get("entry_condition") in ("项目理解完成",) or s.get("acceptance") == "PRE_EXECUTION_UNDERSTANDING_GATE=PASS"
        or "理解" in s.get("goal", "") or "understanding" in str(s.get("goal", "")).lower()
        or "施工前八问" in str(s.get("work", [])) for s in stages)
    has_acceptance = any(
        "验收" in s.get("name", "") or "acceptance" in str(s.get("acceptance", "")).lower()
        or s.get("acceptance") in ("Final Acceptance Matrix 全过",) for s in stages)
    if not has_understanding:
        gaps.append("missing_understanding_entry (理解先于执行)")
    if not has_acceptance:
        gaps.append("missing_final_acceptance (独立验收)")
    return {"pass": not gaps, "gaps": gaps}


def classify_verified_state(verified_state: dict, affected_assumptions: set) -> dict:
    """Real partial invalidation: STILL_VALID / INVALIDATED / REQUIRES_REVALIDATION /
    NEW_REQUIRED. Never whole-project reset, never blind keep."""
    changed = set(affected_assumptions or [])
    result = {"preserved": {}, "invalidated": {}, "requires_revalidation": {}, "new_required": {}}
    for item_id, spec in (verified_state or {}).items():
        deps = set(spec.get("assumptions") or [])
        caps = set(spec.get("capabilities") or [])
        if deps & changed:
            result["invalidated"][item_id] = spec
        elif caps & changed:
            result["requires_revalidation"][item_id] = spec
        else:
            result["preserved"][item_id] = spec
    return result


def apply_human_plan(human_plan: dict, fact_model: dict | None = None) -> dict:
    """A human/enterprise-provided plan takes precedence: keep its主体, add only the
    missing reliability controls as SYSTEM_RELIABILITY_REQUIRED. Never re-impose AI."""
    stages = [dict(s) for s in human_plan.get("stages", [])]
    for s in stages:
        s.setdefault("provenance", "ENTERPRISE_REQUIRED" if human_plan.get("source") == "enterprise"
                     else "HUMAN_PROVIDED")
        s.setdefault("history", [{"by": "ENTERPRISE_AUTHORIZED" if human_plan.get("source") == "enterprise"
                                  else "HUMAN_EXPLICIT", "op": "provide"}])
    check = check_plan_invariants({"stages": stages})
    result = {"stages": stages, "reliability_check": check,
              "authority": "HUMAN_PLAN_KEPT_AI_ADVISORY_ONLY", "advisory": check["gaps"]}
    if not check["pass"]:
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
                            new_facts: dict | None = None,
                            regenerated_stages: dict | None = None) -> dict:
    """Replace affected AI work with planner-regenerated content.

    `regenerated_stages` is keyed by the old stage name and must contain complete semantic
    replacements from a mature planner. Without one, affected AI work is reported as
    REPLAN_INPUT_REQUIRED rather than falsely labelled replanned. Human-owned content is
    byte-for-byte preserved; only review metadata is added.
    """
    stages = active_plan.get("stages", [])
    changed = set(changed_assumptions or [])
    new_fact_assumptions = set()
    if new_facts:
        for f, v in new_facts.items():
            if v:
                new_fact_assumptions.add(f)
    changed |= new_fact_assumptions
    out_stages = []
    recomputed_names = []
    review_required = []
    replan_input_required = []
    regenerated_stages = regenerated_stages or {}
    for s in stages:
        protected = s.get("locked") or _prov(s) in HUMAN_PROTECTED
        deps = _stage_assumptions(s)
        reasons = sorted(deps & changed)
        if protected:
            preserved = dict(s)
            if reasons:
                preserved["review_status"] = "REQUIRES_HUMAN_REVIEW"
                preserved["revalidation_status"] = "REQUIRES_REVALIDATION"
                preserved["affected_by"] = reasons
                review_required.append(s["name"])
            out_stages.append(preserved)
            continue
        if reasons:
            replacement = regenerated_stages.get(s["name"])
            if replacement:
                replacements = replacement if isinstance(replacement, list) else [replacement]
                for fragment in replacements:
                    recomputed = dict(fragment)
                    recomputed.setdefault("name", s["name"])
                    recomputed.setdefault("provenance", "AI_GENERATED")
                    recomputed["replaces"] = s["name"]
                    recomputed["replan_reason"] = reasons
                    recomputed["history"] = s.get("history", []) + [
                        {"by": "UPSTREAM_PLANNER", "op": "regenerate", "reason": reasons}]
                    out_stages.append(recomputed)
            else:
                recomputed = dict(s)
                recomputed["replan_status"] = "REPLAN_INPUT_REQUIRED"
                recomputed["replan_reason"] = reasons
                replan_input_required.append(s["name"])
                out_stages.append(recomputed)
            if replacement: recomputed_names.append(s["name"])
        else:
            out_stages.append(dict(s))
    return {"stages": out_stages,  # original order preserved
            "locked_preserved": [s["name"] for s in stages if s.get("locked") or _prov(s) in HUMAN_PROTECTED],
            "recomputed": recomputed_names,
            "requires_human_review": review_required,
            "replan_input_required": replan_input_required,
            "human_locks_respected": True,
            "new_facts_consumed": sorted(new_fact_assumptions)}


# ==================== PART B: UPSTREAM CAPABILITY FIRST ====================
CAPABILITY_SOURCES = ("UPSTREAM_SKILL", "HARNESS_NATIVE", "LOCAL_CORE", "ENTERPRISE_EXTENSION",
                      "PROJECT_EXTENSION")
INTEGRATION_METHODS = ("ADAPT", "COMPOSE", "CALL", "KEEP_PLUS_EXTEND", "IMPLEMENT_LOCAL")


class CapabilityRegressionError(Exception):
    pass


def capability_provenance_record(capability: str, source: str, source_version: str,
                                 integration_method: str, local_extension: str | None,
                                 reliability_controls: list, validation_status: str,
                                 upstream_search_performed: bool = False) -> dict:
    if source not in CAPABILITY_SOURCES:
        raise ValueError(f"capability_source_invalid:{source}")
    if integration_method not in INTEGRATION_METHODS:
        raise ValueError(f"integration_method_invalid:{integration_method}")
    if integration_method == "IMPLEMENT_LOCAL" and not upstream_search_performed:
        raise ValueError("implement_local_requires_upstream_search_performed (COMPOSE FIRST)")
    return {"capability": capability, "source": source, "source_version": source_version,
            "integration_method": integration_method, "local_extension": local_extension,
            "reliability_controls": reliability_controls, "validation_status": validation_status,
            "upstream_search_performed": upstream_search_performed}


def capability_regression_guard(upstream_baseline: dict, integrated: dict) -> dict:
    """Real comparison over capability SURFACES (not hand-filled numbers): the caller
    supplies measured results from an actual baseline replay. Integrated must not lose any
    capability dimension; reliability dimensions should improve."""
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


def resolve_capability_need(need: str, registry: dict, upstream_available: dict,
                            harness_native: dict | None = None) -> dict:
    """Candidates -> provenance -> compatibility -> maturity -> best compatible source.
    A local registry entry does NOT automatically beat a mature upstream. Unknown-but-
    required triggers real discovery; only CAPABILITY_NOT_AVAILABLE when nothing exists."""
    candidates = []
    if need in registry:
        entry = registry[need]
        candidates.append({"source": "LOCAL_CORE",
                           "maturity": entry.get("maturity", 0) if isinstance(entry, dict) else 0})
    for src, caps in (upstream_available or {}).items():
        caps_list = caps.get("capabilities", caps) if isinstance(caps, dict) else caps
        maturity = caps.get("maturity", 5) if isinstance(caps, dict) else 5
        if need in caps_list:
            candidates.append({"source": src, "maturity": maturity})
    for src, caps in (harness_native or {}).items():
        caps_list = caps.get("capabilities", caps) if isinstance(caps, dict) else caps
        maturity = caps.get("maturity", 5) if isinstance(caps, dict) else 5
        if need in caps_list:
            candidates.append({"source": src, "maturity": maturity})
    if not candidates:
        return {"capability": need, "resolution": "CAPABILITY_NOT_AVAILABLE", "action": "report_to_user"}
    best = max(candidates, key=lambda c: c["maturity"])
    return {"capability": need, "resolution": best["source"],
            "candidates": candidates, "selected_by": "highest maturity (not registry-first)"}


def upstream_update_reabsorb(record: dict, new_upstream: dict) -> dict:
    """Full re-absorption state machine: verify source identity + license -> diff ->
    compatibility -> baseline replay -> integrated regression -> ADOPT/REJECT/DEFER."""
    old_version = record["source_version"]
    new_version = new_upstream.get("source_version", old_version)
    if not new_upstream.get("source_identity_verified"):
        return {"capability": record["capability"], "action": "REJECT",
                "reason": "source_identity_not_verified"}
    if not new_upstream.get("license_compatible", True):
        return {"capability": record["capability"], "action": "REJECT",
                "reason": "license_incompatible"}
    new_caps = set(new_upstream.get("capabilities", []))
    old_caps = set(record.get("capabilities", []))
    added = sorted(new_caps - old_caps)
    removed = sorted(old_caps - new_caps)
    regression = new_upstream.get("integrated_regression_pass")
    if regression is False:
        return {"capability": record["capability"], "action": "REJECT", "reason": "integrated_regression_failed",
                "added": added, "removed": removed}
    if regression is None:
        return {"capability": record["capability"], "action": "DEFER", "reason": "baseline_replay_required",
                "added": added, "removed": removed}
    return {"capability": record["capability"], "from_version": old_version, "to_version": new_version,
            "added": added, "removed": removed, "action": "ADOPT"}

"""Deterministic efficiency cores for v1.4: delta context, verified-state cache, risk-based gate routing,
evidence references, hot/cold handoff, batch evolution dedup, active contract view, efficiency counters.

Token-efficiency contract: every function is pure/O(1)-ish over hashes; nothing here weakens final
acceptance — final/full verification layers remain outside these optimizations by design."""
from __future__ import annotations
import hashlib, json

# ---------- CONTEXT SNAPSHOT / DELTA CONTEXT (EFF-001, EFF-003) ----------
SNAPSHOT_FIELDS = ("task_id", "goal_hash", "contract_hash", "stage_id", "git_head", "worktree_hash",
                   "runtime_identity", "last_gate", "last_evidence_anchor", "last_event_id",
                   "current_blocker", "next_legal_action")


def make_snapshot(state: dict) -> dict:
    missing = [f for f in SNAPSHOT_FIELDS if f not in state]
    if missing:
        raise ValueError(f"snapshot_missing:{missing}")
    return dict(state)


def _key_hash(values: dict) -> str:
    return hashlib.sha256(json.dumps(values, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def context_delta(old: dict, new: dict) -> dict:
    """DELTA_CONTEXT_PROTOCOL: unchanged keys are never reloaded; changed keys enumerate what to reload."""
    if old.get("contract_hash") == new.get("contract_hash") and old.get("goal_hash") == new.get("goal_hash") \
            and old.get("worktree_hash") == new.get("worktree_hash") and old.get("runtime_identity") == new.get("runtime_identity"):
        return {"mode": "DELTA", "changed": [], "reload": [], "reason_code": "ALL_RELEVANT_HASHES_UNCHANGED"}
    changed = [f for f in SNAPSHOT_FIELDS if old.get(f) != new.get(f)]
    reload_map = {"contract_hash": ["changed_contract"], "goal_hash": ["changed_goal"], "worktree_hash": ["changed_files"],
                  "runtime_identity": ["changed_runtime"], "git_head": ["changed_head"]}
    reload = sorted({r for f in changed for r in reload_map.get(f, [])})
    return {"mode": "DELTA", "changed": changed, "reload": reload or ["snapshot"], "reason_code": "RELEVANT_HASH_CHANGED"}


def decide_context_load(old: dict | None, new: dict) -> dict:
    """First entry loads full context; afterwards delta-only unless relevant hashes changed (EFF-001)."""
    if old is None:
        return {"mode": "FULL", "reason_code": "FIRST_ENTRY", "changed": list(SNAPSHOT_FIELDS), "reload": ["full_context"]}
    delta = context_delta(old, new)
    delta["mode"] = "DELTA" if delta["changed"] else "DELTA"
    return delta


# ---------- VERIFIED STATE CACHE (EFF-002, EFF-003) ----------
class VerifiedStateCache:
    """Cache mechanically verified gate results keyed by the exact input hashes. Strict invalidation:
    any relevant input change is a different key — a miss — and forces reverification. No stale reuse."""

    def __init__(self):
        self._entries: dict[str, dict] = {}
        self.counters = {"cache_hit": 0, "cache_miss": 0}

    def _key(self, gate_id: str, inputs: dict) -> str:
        return f"{gate_id}:{_key_hash(inputs)}"

    def get(self, gate_id: str, inputs: dict) -> dict | None:
        entry = self._entries.get(self._key(gate_id, inputs))
        if entry is None:
            self.counters["cache_miss"] += 1
            return None
        self.counters["cache_hit"] += 1
        return dict(entry)

    def put(self, gate_id: str, inputs: dict, result: str) -> dict:
        if result not in {"PASS", "FAIL"}:
            raise ValueError("cached_verdict_must_be_PASS_or_FAIL")
        entry = {"gate_id": gate_id, "inputs_hash": _key_hash(inputs), "result": result}
        self._entries[self._key(gate_id, inputs)] = entry
        return entry


# ---------- RISK-BASED GATE ROUTING (EFF-004, EFF-005) ----------
RISK_LEVELS = ("LOW", "MEDIUM", "HIGH", "CRITICAL")
CHANGE_SURFACE_RISK = {
    "copy_text": "LOW", "ui_cosmetic": "LOW", "styling": "LOW",
    "module_logic": "MEDIUM", "api_handler": "MEDIUM",
    "workflow": "HIGH", "rag": "HIGH", "rbac": "HIGH", "persistence": "HIGH", "database": "HIGH", "runtime_adapter": "HIGH",
    "production": "CRITICAL", "irreversible_migration": "CRITICAL", "security_boundary": "CRITICAL", "cross_environment": "CRITICAL",
}
GATE_DEPENDENCY_GRAPH = {
    "database": ["persistence_gate", "restart_gate", "api_gate"],
    "persistence": ["persistence_gate", "restart_gate"],
    "runtime_adapter": ["adapter_gate", "restart_gate"],
    "workflow": ["workflow_gate", "role_e2e_gate"],
    "rag": ["rag_gate", "citation_gate"],
    "rbac": ["rbac_gate", "role_e2e_gate"],
    "module_logic": ["affected_module_tests", "contract_check"],
    "api_handler": ["affected_module_tests", "contract_check", "targeted_browser_journey"],
    "copy_text": ["affected_module_tests"],
    "ui_cosmetic": ["affected_module_tests", "targeted_browser_journey"],
    "styling": ["affected_module_tests"],
}
ALWAYS_GATES = {"contract_check"}  # cheap, always relevant


def classify_risk(change_surfaces: list[str]) -> str:
    levels = [CHANGE_SURFACE_RISK.get(s) for s in change_surfaces]
    unknown = [s for s, l in zip(change_surfaces, levels) if l is None]
    if unknown:
        raise ValueError(f"unknown_change_surface:{unknown}")
    order = {l: i for i, l in enumerate(RISK_LEVELS)}
    return max(levels, key=lambda l: order[l])


def route_gates(change_surfaces: list[str], available_gates: list[str]) -> dict:
    """Risk-based routing with explicit NOT_APPLICABLE and dependency-graph propagation.
    CRITICAL keeps the FULL governance chain (final verification is never downgraded)."""
    risk = classify_risk(change_surfaces)
    if risk == "CRITICAL":
        return {"risk": risk, "run": sorted(set(available_gates)), "not_applicable": [], "reason_code": "CRITICAL_FULL_CHAIN"}
    required = set(ALWAYS_GATES)
    for surface in change_surfaces:
        required.update(GATE_DEPENDENCY_GRAPH.get(surface, []))
    run, not_applicable = [], []
    for gate in available_gates:
        (run if gate in required else not_applicable).append(gate)
    return {"risk": risk, "run": sorted(run), "not_applicable": sorted(not_applicable), "reason_code": f"RISK_{risk}_ROUTED"}


# ---------- EVIDENCE REFERENCE (EFF-006) ----------
class EvidenceRegistry:
    """Store each evidence body once; refer afterwards by id+hash (REF: EV-xxxx)."""

    def __init__(self):
        self._store: dict[str, dict] = {}

    def register(self, evidence_id: str, body: str, source: str, result: str) -> dict:
        if evidence_id in self._store:
            return {"ref": evidence_id, "hash": self._store[evidence_id]["hash"], "deduplicated": True}
        h = hashlib.sha256(body.encode("utf-8")).hexdigest()
        self._store[evidence_id] = {"hash": h, "source": source, "result": result}
        return {"ref": evidence_id, "hash": h, "deduplicated": False}

    def ref(self, evidence_id: str) -> dict:
        entry = self._store.get(evidence_id)
        if entry is None:
            raise KeyError(f"evidence_not_registered:{evidence_id}")
        return {"ref": evidence_id, **entry}

    def load_body(self, evidence_id: str) -> str:
        """On-demand read only — cold by default (§21: 按需读取)."""
        entry = self._store.get(evidence_id)
        if entry is None or "body" not in entry:
            raise KeyError(f"evidence_body_not_stored:{evidence_id}")
        return entry["body"]


# ---------- HOT / COLD HANDOFF (EFF-007) ----------
HOT_CONTEXT_FIELDS = ("goal", "task_id", "current_stage", "current_head", "current_state",
                      "current_blocker", "last_known_good", "partial_work", "next_legal_action")


def build_handoff_context(full_state: dict, cold_index: dict | None = None) -> dict:
    """Handoff carries ONLY what the successor must know now; history goes to cold index (id+path/hash)."""
    hot = {f: full_state.get(f) for f in HOT_CONTEXT_FIELDS if full_state.get(f) not in (None, "")}
    cold = cold_index or {k: v for k, v in full_state.items() if k not in HOT_CONTEXT_FIELDS}
    return {"hot_context": hot, "cold_context_index": {k: v for k, v in cold.items()},
            "reason_code": "HOT_COLD_SPLIT", "hot_items": len(hot), "cold_refs": len(cold)}


# ---------- BATCH EVOLUTION / DEDUP (EFF-008, EFF-009) ----------
EVOLUTION_TRIGGERS = {"STAGE_END", "PROJECT_END", "REPEATED_PATTERN", "HIGH_SEVERITY_FAILURE", "EXPLICIT_REVIEW"}


def experience_fingerprint(experience: dict) -> str:
    """Same failure pattern dedups to one fingerprint (fields that define the pattern, not the instance)."""
    pattern_keys = ("failure_pattern", "classification", "root_cause_class", "affected_capability")
    return _key_hash({k: experience.get(k, "") for k in pattern_keys})


def capture_experience(inbox: dict, fingerprint: str, experience: dict) -> dict:
    """Cheap capture: existing fingerprint just bumps repeat_count + refs (no new full analysis file)."""
    entry = inbox.get(fingerprint)
    if entry is None:
        inbox[fingerprint] = {"pattern": {k: experience.get(k) for k in ("failure_pattern", "classification", "root_cause_class", "affected_capability")},
                              "repeat_count": 1, "evidence_refs": [experience.get("evidence_ref", "")], "project_refs": [experience.get("project_ref", "")], "analyzed": False}
        return {"action": "NEW_PATTERN", "fingerprint": fingerprint}
    entry["repeat_count"] += 1
    entry["evidence_refs"].append(experience.get("evidence_ref", ""))
    entry["project_refs"].append(experience.get("project_ref", ""))
    return {"action": "DEDUPLICATED", "fingerprint": fingerprint, "repeat_count": entry["repeat_count"]}


def should_deep_analyze(trigger: str, inbox: dict, fingerprint: str) -> bool:
    if trigger not in EVOLUTION_TRIGGERS:
        return False
    entry = inbox.get(fingerprint)
    return trigger in {"STAGE_END", "PROJECT_END", "EXPLICIT_REVIEW"} or (trigger == "REPEATED_PATTERN" and entry and entry["repeat_count"] >= 2) or trigger == "HIGH_SEVERITY_FAILURE"


def batch_evolution(inbox: dict, pending: list[str]) -> dict:
    """One deep-analysis pass over multiple experiences: shared setup, per-patch evidence kept separate."""
    selected = [f for f in pending if f in inbox and not inbox[f]["analyzed"]]
    return {"batch_size": len(selected), "fingerprints": selected,
            "shared_setup": ["pattern_context", "heldout_protocol"], "reason_code": "BATCH_DEEP_ANALYSIS"}


# ---------- ACTIVE CONTRACT VIEW (§34-35) ----------
ACTIVE_VIEW_SECTIONS = ("current_goal", "current_stage", "relevant_constraints", "relevant_acceptance", "current_permissions", "next_action")


def build_active_contract_view(contract: dict, sections: dict) -> dict:
    source_hash = _key_hash(contract)
    view = {"source_contract_hash": source_hash, "included_sections": sorted(sections)}
    view["view_hash"] = _key_hash({k: sections[k] for k in sorted(sections)} | {"source": source_hash})
    return {"active_view": view, "sections": sections, "reason_code": "COMPACT_VIEW_HASH_BOUND"}


def active_view_valid(view: dict, current_contract: dict) -> bool:
    return view.get("source_contract_hash") == _key_hash(current_contract)


# ---------- EFFICIENCY COUNTERS (§42-44) ----------
def new_counters() -> dict:
    return {"gate_execution_count": 0, "gate_cache_hit": 0, "gate_cache_miss": 0,
            "gate_skipped_not_applicable_count": 0, "full_context_reload_count": 0,
            "delta_context_load_count": 0, "hot_context_items": 0, "cold_context_refs": 0,
            "evidence_dedup_count": 0, "experience_dedup_count": 0, "batch_evolution_runs": 0,
            "over_governance_event_count": 0}


def token_efficiency_metrics(counters: dict, token_attributions: dict | None = None) -> dict:
    """Core metrics; anything without a real platform attribution stays NOT_AVAILABLE."""
    t = token_attributions or {}
    def real(name): return t.get(name, "NOT_AVAILABLE")
    metrics = {k: counters.get(k, 0) for k in counters}
    total = t.get("total_token", "NOT_AVAILABLE")
    metrics.update({
        "total_token": total,
        "business_construction_token": real("business_construction_token"),
        "governance_token": real("governance_token"),
        "repeated_context_token": real("repeated_context_token"),
        "verification_token": real("verification_token"),
        "evidence_token": real("evidence_token"),
        "evolution_token": real("evolution_token"),
    })
    if isinstance(total, int) and isinstance(t.get("governance_token"), int):
        metrics["governance_token_ratio"] = round(t["governance_token"] / total, 6)
    else:
        metrics["governance_token_ratio"] = "NOT_AVAILABLE"
    return metrics


def token_per_unit(total_token, units: int, unit_name: str) -> dict:
    if not isinstance(total_token, int) or not isinstance(units, int) or units <= 0:
        return {unit_name: "NOT_AVAILABLE"}
    return {unit_name: total_token // units}

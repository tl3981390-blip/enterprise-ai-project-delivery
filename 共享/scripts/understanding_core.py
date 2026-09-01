"""Harness-neutral multi-turn understanding contract.

The Harness interprets natural language; Core owns provenance, consequential gaps,
conflicts and the mechanical boundary into planning.  Model prose is never accepted as
proof that a fact changed.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from uuid import uuid4

FACT_SOURCES = {"USER_EXPLICIT", "USER_CONFIRMED", "PROJECT_EVIDENCE",
                "SYSTEM_OBSERVED", "AI_INFERRED"}
FACT_STATES = {"UNKNOWN", "PROPOSED", "ACTIVE", "CONFLICTED", "SUPERSEDED",
               "NOT_APPLICABLE"}
DECISION_DIMENSIONS = {
    "user_real_goal": ("Scope", "Plan", "Acceptance"),
    "users": ("Scope", "Architecture", "Permission", "Acceptance"),
    "user_journeys": ("Work Unit", "Plan", "Acceptance"),
    "final_deliverable": ("Scope", "Work Unit", "Acceptance"),
    "acceptance_requirements": ("Plan", "Acceptance"),
    "explicit_constraints": ("Scope", "Architecture", "Permission"),
    "permissions": ("Permission", "Capability"),
}


def begin_understanding(*, raw_goal: str, mode: str = "NEW_PROJECT",
                        observed_facts: dict | None = None,
                        required_dimensions: list[str] | None = None) -> dict:
    if not isinstance(raw_goal, str) or not raw_goal.strip():
        raise ValueError("natural_language_goal_required")
    if mode not in {"NEW_PROJECT", "EXISTING_PROJECT"}:
        raise ValueError("understanding_mode_invalid")
    # The caller selects only consequential dimensions for this task.  A clear,
    # bounded request is allowed to proceed without an artificial questionnaire.
    required_dimensions = [] if required_dimensions is None else required_dimensions
    unknown_dimensions = sorted(set(required_dimensions) - set(DECISION_DIMENSIONS))
    if unknown_dimensions:
        raise ValueError(f"decision_dimension_invalid:{unknown_dimensions}")
    session = {"understanding_id": str(uuid4()), "raw_goal": raw_goal.strip(),
               "mode": mode, "facts": {}, "fact_events": [], "asked_questions": [],
               "required_dimensions": list(dict.fromkeys(required_dimensions)),
               "status": "UNDERSTANDING", "created_at": _now(), "updated_at": _now()}
    _put(session, "user_real_goal", raw_goal.strip(), "USER_EXPLICIT", "initial_goal")
    for name, entry in (observed_facts or {}).items():
        if isinstance(entry, dict) and "value" in entry:
            _put(session, name, entry["value"], entry.get("source", "PROJECT_EVIDENCE"),
                 entry.get("evidence", "initial_observation"))
        else:
            _put(session, name, entry, "PROJECT_EVIDENCE", "initial_observation")
    return evaluate_understanding(session)


def propose_inference(session: dict, *, fact: str, value, rationale: str) -> dict:
    out = deepcopy(session)
    _put(out, fact, value, "AI_INFERRED", rationale, state="PROPOSED")
    return evaluate_understanding(out)


def apply_answer(session: dict, *, question_id: str, fact_updates: dict) -> dict:
    out = deepcopy(session)
    known_ids = {q["question_id"] for q in out.get("questions", [])}
    if question_id not in known_ids:
        raise ValueError("answer_question_not_outstanding")
    question = next(q for q in out.get("questions", []) if q["question_id"] == question_id)
    if set(fact_updates) != {question["fact"]}:
        raise ValueError("answer_must_update_exact_question_fact")
    _put(out, question["fact"], fact_updates[question["fact"]], "USER_CONFIRMED",
         f"answer:{question_id}")
    out["asked_questions"].append(question_id)
    return evaluate_understanding(out)


def evaluate_understanding(session: dict) -> dict:
    out = deepcopy(session)
    facts = out["facts"]
    questions, blockers = [], []
    required = list(out["required_dimensions"] if "required_dimensions" in out
                    else DECISION_DIMENSIONS)
    # Existing projects must be reconstructed before interviewing the user again.
    if out["mode"] == "EXISTING_PROJECT":
        required += ["existing_state", "existing_plan", "existing_evidence"]
    discovery_actions = []
    for name in required:
        item = facts.get(name)
        active = item and item["state"] == "ACTIVE" and item["source"] != "AI_INFERRED"
        if active:
            continue
        impacts = DECISION_DIMENSIONS.get(name, ("Plan", "Work Unit", "Acceptance"))
        qid = f"gap:{name}"
        question = {"question_id": qid, "fact": name,
                          "why": f"缺少该事实会改变 {', '.join(impacts)}",
                          "decision_impacts": list(impacts),
                          "prompt": _prompt(name, out["mode"])}
        if out["mode"] == "EXISTING_PROJECT" and name in {
                "existing_state", "existing_plan", "existing_evidence"}:
            discovery_actions.append(dict(question, action="READ_PROJECT_BEFORE_ASKING_USER"))
        else:
            questions.append(question)
        blockers.append(name)
    conflicts = sorted(k for k, v in facts.items() if v["state"] == "CONFLICTED")
    for name in conflicts:
        questions.append({"question_id": f"conflict:{name}", "fact": name,
                          "why": "同一决策事实存在冲突，不能静默选择",
                          "decision_impacts": list(DECISION_DIMENSIONS.get(name, ("Plan",))),
                          "prompt": f"关于“{name}”目前有冲突信息，请确认哪一个为准。"})
    blockers += conflicts
    out["questions"] = questions[:4]  # one high-value round, not a one-round limit
    out["discovery_actions"] = discovery_actions
    out["blocking_unknowns"] = sorted(set(blockers))
    out["sufficiency"] = {
        "goal_fidelity": _active(facts, "user_real_goal"),
        "decision_sufficiency": not blockers,
        "unknown_coverage": not blockers,
        "provenance_integrity": not any(v["state"] == "ACTIVE" and
                                          v["source"] == "AI_INFERRED"
                                          for v in facts.values()),
        "scope_clarity": ("final_deliverable" not in required or _active(facts, "final_deliverable"))
                         and ("explicit_constraints" not in required or _active(facts, "explicit_constraints")),
        "acceptance_clarity": ("acceptance_requirements" not in required or
                               _active(facts, "acceptance_requirements")),
        "contradiction_check": not conflicts,
        "permission_boundary": "permissions" not in required or _active(facts, "permissions"),
    }
    out["gate_pass"] = all(out["sufficiency"].values())
    out["status"] = "UNDERSTANDING_SUFFICIENT" if out["gate_pass"] else "UNDERSTANDING"
    out["updated_at"] = _now()
    return out


def planning_facts(session: dict) -> dict:
    checked = evaluate_understanding(session)
    if not checked["gate_pass"]:
        raise ValueError(f"understanding_insufficient:{checked['blocking_unknowns']}")
    source_to_state = {"USER_EXPLICIT": "DECLARED", "USER_CONFIRMED": "DECLARED",
                       "PROJECT_EVIDENCE": "OBSERVED", "SYSTEM_OBSERVED": "OBSERVED"}
    facts = {name: {"state": source_to_state[item["source"]], "value": item["value"],
                    "provenance": item["source"], "history": deepcopy(item["history"]),
                    "source_fact": name}
             for name, item in checked["facts"].items() if item["state"] == "ACTIVE"}
    # Planning Core consumes the canonical `goal` field.  Preserve the original
    # fact identity and full user provenance instead of silently renaming it.
    if "user_real_goal" in facts:
        facts["goal"] = {**deepcopy(facts["user_real_goal"]),
                         "source_fact": "user_real_goal",
                         "canonical_mapping": "user_real_goal->goal"}
    return facts


def _put(session: dict, name: str, value, source: str, evidence: str,
         state: str = "ACTIVE") -> None:
    if source not in FACT_SOURCES:
        raise ValueError(f"fact_source_invalid:{source}")
    if state not in FACT_STATES:
        raise ValueError(f"fact_lifecycle_invalid:{state}")
    old = session["facts"].get(name)
    event = {"event_id": str(uuid4()), "fact": name, "value": deepcopy(value),
             "source": source, "evidence": evidence, "state": state, "at": _now()}
    if old and old["state"] == "ACTIVE" and old["value"] != value:
        if source in {"USER_CONFIRMED", "USER_EXPLICIT"}:
            old_event = dict(old["history"][-1], state="SUPERSEDED")
            event["supersedes"] = old_event["event_id"]
        elif old["source"] in {"USER_CONFIRMED", "USER_EXPLICIT"}:
            event["state"] = "CONFLICTED"
            state = "CONFLICTED"
        else:
            state = "CONFLICTED"
            event["state"] = state
    history = deepcopy(old.get("history", [])) if old else []
    history.append(event)
    session["facts"][name] = {"state": state, "value": deepcopy(value),
                              "source": source, "evidence": evidence, "history": history}
    session["fact_events"].append(event)


def _active(facts: dict, name: str) -> bool:
    item = facts.get(name)
    return bool(item and item["state"] == "ACTIVE" and item["value"] not in (None, "", []))


def _prompt(name: str, mode: str) -> str:
    prompts = {
        "users": "谁会实际使用它，主要在什么场景使用？",
        "user_journeys": "用户从开始到得到结果，最核心的一条使用流程是什么？",
        "final_deliverable": "这次最终要交付什么可使用的结果？",
        "acceptance_requirements": "你看到什么结果时会认为这件事已经完成？",
        "explicit_constraints": "有哪些明确不能改、暂不做或必须遵守的边界？",
        "permissions": "执行中允许哪些写入或外部操作，哪些必须先得到你的批准？",
        "existing_state": "现有代码、配置和运行状态的只读勘察结果是什么？",
        "existing_plan": "项目内已有计划或企业流程是什么？",
        "existing_evidence": "已有结果中哪些有可复核证据，哪些只是历史声明？",
    }
    return prompts.get(name, f"请确认会影响后续决策的事实：{name}。")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "共享" / "scripts"))

from delivery_planning_core import assess_complexity, compose_stages, make_fact_model, reason_capability_needs
from delivery_runtime import _start_delivery_from_facts, change_conditions


def plan(facts, upstream):
    model = make_fact_model(**facts)
    return compose_stages(model, assess_complexity({}), reason_capability_needs(model), upstream_plan=upstream)


def test_case_a_same_database_capability_different_real_boundary():
    simple = plan({"goal": "个人记账", "persistence": True, "existing_database": True},
        {"work_units": [{"name": "记录收支", "goal": "可记录收支", "class": "TASK",
                         "work": ["表单", "保存"], "capabilities": ["database"]}]})
    migration = plan({"goal": "生产数据库迁移", "persistence": True, "existing_database": True,
                      "migration_requirements": ["零丢失"], "rollback_requirement": True},
        {"work_units": [{"name": "生产数据迁移与回滚", "goal": "迁移且可安全回退", "class": "STAGE",
                         "work": ["兼容 schema", "双写", "切换", "回滚演练"],
                         "output": ["migration", "rollback"], "capabilities": ["database"],
                         "acceptance": "完整性、切换、回滚全部通过"}]})
    assert "记录收支" in [x["name"] for x in simple["stages"] + simple["tasks"]]
    assert len(simple["stages"]) == 1
    assert "生产数据迁移与回滚" in [x["name"] for x in migration["stages"]]


def test_case_b_same_deployment_capability_different_real_boundary():
    static = plan({"goal": "静态页", "deployment_requirement": True},
        {"work_units": [{"name": "交付静态页", "goal": "页面可访问", "class": "TASK",
                         "work": ["build", "publish"], "capabilities": ["deployment"]}]})
    production = plan({"goal": "多环境生产发布", "deployment_requirement": True,
                       "environments": ["staging", "canary", "production"],
                       "rollback_requirement": True, "migration_requirements": ["schema"]},
        {"work_units": [{"name": "灰度发布与生产回退", "goal": "跨环境安全发布", "class": "STAGE",
                         "work": ["staging", "canary", "migration", "rollback", "production verify"],
                         "capabilities": ["deployment"], "acceptance": "灰度、迁移、回退和生产验证通过"}]})
    assert "交付静态页" in [x["name"] for x in static["stages"] + static["tasks"]]
    assert "灰度发布与生产回退" in [x["name"] for x in production["stages"]]


def test_case_c_real_partial_replan_human_authority_and_evidence():
    upstream = {"stages": [
        {"name": "数据模型", "goal": "PostgreSQL 数据模型", "work": ["PG schema", "PG migration"],
         "output": ["postgres.sql"], "dependencies": ["PostgreSQL"],
         "assumptions": ["database_engine", "data"], "acceptance": "PG migration PASS",
         "evidence": ["pg-migration.log"]},
        {"name": "同步逻辑", "goal": "使用 PG 并发语义同步", "work": ["row locks"],
         "output": ["sync"], "assumptions": ["database_engine"], "acceptance": "并发测试"},
        {"name": "UI", "goal": "录入界面", "work": ["render"], "output": ["ui"],
         "assumptions": ["ui_contract"], "acceptance": "浏览器通过"}]}
    s = _start_delivery_from_facts(facts={"goal": "记账", "persistence": True, "existing_database": True,
        "database_engine": "PostgreSQL", "data": {"entities": ["entry"]}}, upstream_plan=upstream)
    # Simulate a human-owned affected element without changing its content.
    human = next(x for x in s["plan"]["stages"] if x["name"] == "同步逻辑")
    human["provenance"] = "HUMAN_MODIFIED"
    before_human = copy.deepcopy(human)
    before_ui = copy.deepcopy(next(x for x in s["plan"]["stages"] if x["name"] == "UI"))
    s["verified_state"] = {
        "pg_migration": {"assumptions": ["database_engine"], "capabilities": ["database"], "evidence": ["pg.log"]},
        "ui_browser": {"assumptions": ["ui_contract"], "capabilities": ["browser"], "evidence": ["ui.png"]},
        "db_readback": {"assumptions": ["storage_contract"], "capabilities": ["database_engine"], "evidence": ["read.log"]}}
    replacements = {"数据模型": {"name": "数据模型", "goal": "SQLite 数据模型",
        "work": ["重写 SQLite schema", "替换 PG 专有类型", "设计本地迁移"],
        "output": ["sqlite.sql", "local-migration"], "dependencies": ["SQLite"],
        "assumptions": ["database_engine", "data"], "acceptance": "SQLite 迁移与读写回读 PASS",
        "evidence": ["sqlite-migration.log", "sqlite-readback.log"]}}
    out = change_conditions(s, changed_facts={"database_engine": "SQLite",
        "data": {"entities": ["entry", "category"]}}, replanned_work_units=replacements)
    new_data = next(x for x in out["plan"]["stages"] if x["name"] == "数据模型")
    new_human = next(x for x in out["plan"]["stages"] if x["name"] == "同步逻辑")
    new_ui = next(x for x in out["plan"]["stages"] if x["name"] == "UI")
    assert new_data["work"] != upstream["stages"][0]["work"]
    assert new_data["output"] != upstream["stages"][0]["output"]
    for key in ("goal", "work", "output", "acceptance"):
        assert new_human[key] == before_human[key]
    assert new_human["review_status"] == "REQUIRES_HUMAN_REVIEW"
    assert new_ui == before_ui
    assert out["verified_state"]["pg_migration"]["validation_status"] == "INVALIDATED"
    assert out["verified_state"]["ui_browser"]["validation_status"] == "STILL_VALID"
    assert out["verified_state"]["db_readback"]["validation_status"] == "REQUIRES_REVALIDATION"
    assert "category 读写回读一致" in out["acceptance"]["必须真实持久化的数据"]
    assert "replanned" not in new_data


def test_affected_ai_work_without_planner_fragment_never_fake_replans():
    upstream = {"stages": [{"name": "数据模型", "goal": "PG", "work": ["PG"],
        "assumptions": ["database_engine"], "acceptance": "PG PASS"}]}
    s = _start_delivery_from_facts(facts={"goal": "应用", "database_engine": "PostgreSQL"}, upstream_plan=upstream)
    out = change_conditions(s, changed_facts={"database_engine": "SQLite"})
    stage = next(x for x in out["plan"]["stages"] if x["name"] == "数据模型")
    assert stage["replan_status"] == "REPLAN_INPUT_REQUIRED"
    assert out["status"] == "PLANNING"
    assert not out["plan"]["recomputed"]

# SKILL_EVOLUTION_ENGINE_SPEC（Skill 进化引擎规格）

定位：**仅提案侧**（AUTO_PROPOSE / AUTO_TEST / AUTO_EVALUATE）；正式版本永远走 Release Gate，禁止 AUTO_RELEASE，禁止运行中的正式 Skill 在线自改（总指令 §25–§34）。
机械核心：`共享/scripts/skill_evolution_core.py`；经验与台账实体在 `D:/ComplexProjectLab/Round_001/07_SkillEvolution/`（跨项目持久，随轮次累积）。

## 流水线

```text
Experience Harvest（真实事件+Evidence 才能入箱）
↓ Failure Pattern Mining（分类 + 可泛化判定）
↓ Candidate Improvement（Learning Ledger → OBSERVED→CANDIDATE）
↓ Bounded Patch（ADD/REPLACE/DELETE/REFINE + 九字段声明，见下）
↓ Negative Test（优化用例必须先 FAIL 后 PASS）
↓ Held-out Evaluation（独立新上下文出题，候选不可知答案；上游 SkillOpt 防污染模式）
↓ Rescue Regression + Round 1 Regression（G1–G4 不回退）
↓ Benefit / Overhead Comparison（§59 商业效果问询）
↓ Adoption Recommendation（VALIDATED；进入 NEXT_SKILL_DEV 批次）
```

## 三层学习模型

Layer1 Experience：一切真实事件可入箱（`SKILL_EXPERIENCE_INBOX.md`，机械校验 `validate_experience`）。
Layer2 Learning：抽象为失败模式入台账（`SKILL_LEARNING_LEDGER.md`，状态机 `validate_transition`：OBSERVED→CANDIDATE→VALIDATED→ADOPTED/REJECTED/NEEDS_MORE_DATA；REJECTED 不可复活，只能进拒绝档案后另立新案）。
Layer3 Skill Mutation：仅 `validate_candidate` 四硬证齐全（optimization_improved + heldout_no_regression + rescue_regression_pass + round1_regression_pass）才允许 VALIDATED。

## Bounded Patch 声明（九字段，`validate_patch_declaration`）

patch_id / source_experience / affected_capability / op∈{ADD,REPLACE,DELETE,REFINE} / target / old_behavior / new_behavior / expected_benefit / possible_regression。缺任一字段或 op 非法 → 补丁不可进入评估。单补丁不得重写整个 Skill。

## 版本批次纪律

候选积累在 `NEXT_SKILL_DEV`（当前 `v1.3.0-dev` 分支）；稳定批次统一过 Release Gate 后发版（§34：不要每发现一个 Bug 就发一个版本）。项目执行中切换候选必须走 §33 安全边界（原子单元收口→Checkpoint→Handoff→全回归→版本边界记录→新代理加载→交接核验→恢复核验→同 task_id 继续）。

## Over-Governance 防臃肿

新 Gate 若"很少阻止真实问题 + 大量增加 Token/时间" → 标记 `OVER_GOVERNANCE_CANDIDATE`，优化器可提出 DELETE/SIMPLIFY（§60）；每轮在 Engine 报告中记录各 Gate 的真实拦截数与成本。

## 首批候选补丁（本轮，v1.3.0-dev）

| Patch | 来源 | op | 内容 | 状态 |
| --- | --- | --- | --- | --- |
| PATCH-EV-001 | LL-006 / EXP-007（v1.2 合同漏 MUST，已验证失效） | ADD | 理解门禁 `CONTRACT_SCOPE_COMPLETENESS`：source_requirements 必须全量处置 | CANDIDATE→（本轮带负向/回归测试） |
| PATCH-EV-002 | LL-004 / EXP-004（CAND-004） | ADD | `check_declared_adapter.py` DECLARED_RUNTIME_ADAPTER_GATE | CANDIDATE→（本轮带负向/回归测试） |
| PATCH-EV-003 | LL-003 / EXP-003（CAND-003） | ADD | ROLE_WORKFLOW_E2E_COVERAGE_GATE（由状态机+角色矩阵推导必需浏览器路径） | CANDIDATE（待 ERL Phase B 场景数据，未实现） |
| PATCH-EV-004 | LL-008 / EXP-009 | REFINE | 计划对账禁止词词边界匹配 | CANDIDATE（小改，待批次） |

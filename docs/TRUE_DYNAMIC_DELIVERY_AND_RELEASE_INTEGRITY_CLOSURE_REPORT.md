# TRUE_DYNAMIC_DELIVERY_AND_RELEASE_INTEGRITY_CLOSURE_REPORT

日期：2026-08-31 ｜ 执行：`TRUE_DYNAMIC_DELIVERY_AND_RELEASE_INTEGRITY_CLOSURE`（28 步全序）｜ 状态：**CORE_CLOSED（GitHub push PENDING_NETWORK，如实标注）**

## 1. 当前真实根因（本轮新增）

| # | 根因 | 机械证据 |
| --- | --- | --- |
| RC-15 | Release Identity 自指悖论 | v1.6.0 tag(`55207d2`) 内 metadata 记 `release_commit=8be9502` + `asset_sha256=PENDING_UNTIL_RELEASE`；main 后续修正但历史不可改 |
| RC-16 | 结构因子→能力固定路由 | `FACTOR_CAPABILITY_NEEDS`：user_journeys→browser_acceptance、component_dependencies→database、security_surface→enterprise_governance、cross_platform→deployment（桌面≠浏览器、内存组件≠数据库、个人安全≠企业治理、跨平台≠部署） |
| RC-17 | 固定生命周期阶段模板 | `LIFECYCLE_STAGES` 默认塞入 00/01/02/03/04/05/06/11/12/14/15/19（12 阶段模板） |
| RC-18 | Final Acceptance 占位生成 | `journey1/journey2/journey3` + 无持久化项目仍写「核心实体读写回读一致」 |
| RC-19 | 迁移测试假绿 | `test_migration.py` 依赖 `D:\企业Skill实验室`、`assertGreaterEqual(x,0)` 恒真、`@skipUnless` 关键测试缺失即跳过 |
| RC-20 | AGENT_INSTALL 陈旧 | 写死「当前正式版本=v1.5.1」「仓库是 PRIVATE」（实际 Latest=v1.6.0、Public） |

## 2. 来自外部 GitHub 核验的事实

- v1.6.0 tag 内 `RELEASE_METADATA.json` 与 tag 实际 commit 不一致（外部只读核验确认）。
- GitHub v1.6.0 Release Asset SHA-256 = `24c81e69…`（与 tag 内 `PENDING_UNTIL_RELEASE` 不是同一身份状态）。
- 仓库 visibility = **PUBLIC**，description 曾停在「complex AI project / v1.5.0」→ 已更新为通用定位。

## 3. v1.6.0 历史身份缺陷处理

不移动历史 tag。v1.6.0 保留为「已发布但存在 Release Metadata Identity Defect」的历史版本；缺陷在 `RELEASE_METADATA.json` 的 `history.v1.6.0_defect` 中如实记录；由 v1.6.1 的 Declaration/Resolution 模型替代。

## 4. 新 Release Identity 模型（Declaration/Resolution 分离）

```text
Git 内 RELEASE_METADATA.json（Declaration）：version/tag/release_asset/repository/channel
  —— 只含 commit 前可知事实；绝不记录自身 commit hash 或预计算 asset SHA
运行时 Resolution：git rev-parse <tag>^{commit} → 真实 release_commit
发布侧 Resolution：GitHub Release manifest / asset 下载 → asset_sha256
```

`bump_version.py` 只维护 Declaration 字段（pop 掉任何自指键）；REL-001 机械断言 metadata 无 `release_commit`/`asset_sha256`。

## 5. FACTOR_CAPABILITY_NEEDS 移除/重构

已删除。能力激活改为 `reason_capability_needs(fact_model)`：每个能力由显式事实谓词决定（`interfaces` 含 web → browser_acceptance；`persistence=true` 或 `data` 存在 → database；`compliance` 存在 → enterprise_governance；`deployment_requirement=true` → deployment；`goal` 含检索/问答 → rag；`workflow` 含 autonomous → agent；`permissions`/`external_systems` → tool_permissions；`migration_requirements` → upgrade_rollback）。驱动事实 UNKNOWN 时 required=unknown（不静默 false）。

## 6. 固定 LIFECYCLE_STAGES 移除作为流程模板

已删除。`compose_stages(fact_model, complexity, capability_needs)` 从事实发现工作单元，按依赖/风险/验收边界分组为 Stage；工作项四级分类 STAGE/TASK/CHECK/NOT_APPLICABLE（不是 ACTIVE/NOT_APPLICABLE 两档）。简单按钮修改 → 理解+实现+验收（≤3 Stage）；复杂跨系统 → 架构/迁移/部署等独立 Stage。

## 7. Reliability Invariant 保留

不变量（理解先于执行/范围权限/防假/Evidence/恢复再验证/最终验收）永远生效，但**不再等于独立可见 Stage**。理解门禁与最终验收恒为 Stage（进/出口不变量载体）；恢复是事件驱动（各 Stage 的 failure_handling 分支）；多角色验收非恒活（单人项目 EXECUTOR_CLAIM != FINAL EVIDENCE 即可）。

## 8. Project Fact Model

`make_fact_model(**facts)`：21 字段（goal/users/user_journeys/interfaces/data/persistence/external_systems/runtime/environments/deployment_requirement/security_requirements/permissions/compliance/roles/workflow/recovery_requirements/migration_requirements/acceptance_requirements/explicit_constraints/unknowns/assumptions），状态 DECLARED/OBSERVED/INFERRED/UNKNOWN/NOT_APPLICABLE。

## 9. Dynamic Stage Composer

见 §6。Stage Schema 固定（name/goal/work/output/entry/done/acceptance/failure/evidence），Stage Content 不固定。

## 10. Final Acceptance 从事实生成

`derive_final_acceptance(fact_model, complexity)`：旅程来自 `user_journeys` 事实（无占位 journey1/2/3）；持久化要求仅当 `persistence=true`；环境要求仅当 `deployment_requirement=true`；无事实的项不出现或 N/A（DYN2-011/012）。

## 11. Migration 假绿修复

`test_migration_v2.py`：真实 git fixture（clean/dirty/unpushed/local-only 各 Case 真检测）；不依赖 `D:\企业Skill实验室`；缺便携 fixture → FAIL 非 SKIP；幂等/续跑在合成工作区证明（网络瞬断时如实 skip 标 EXTERNAL_LIVE_TEST）。

## 12. WorkBuddy real replay

**PENDING_EXTERNAL_VALIDATION**（本机无 WorkBuddy CLI）。复测合同：「使用最新正式 enterprise-ai-project-delivery，帮我做一个家庭点菜单项目」应到达业务澄清与项目自己的动态 Delivery Plan，无企业模板/固定阶段/治理流水账。

## 13. Clean replay

**PENDING_EXTERNAL_VALIDATION**（GitHub 连接瞬断）。机制已建：`workspace-bootstrap/clean_replay.py`（隔离沙箱，不读旧工作区）+ `restore_workspace.py`（幂等/续跑/无 shell=True）。

## 14. 新 tag/release/hash

```text
v1.5.0 → 491f6c9f76c6c384fd18a21303aba56812eeadb1（历史不变）
v1.5.1 → ba7ca9e71d90c2a20eb994053a6d2bee21c36f2c（历史不变）
v1.6.0 → 55207d242aac741d82959de6fd778416c6d304d4（历史不变，含已记录的 metadata 缺陷）
v1.6.1 → 766680bb7b0719341381b0d5a35e998065bdf1fd（本轮新 tag）
```

## 15. Core Freeze

本轮属合法重开（真实缺陷 + 机制缺失 + 可泛化 + 可复现 + 证据）。完成后：

```text
CORE_FEATURE_FREEZE = ACTIVE
```

## 16. 剩余 Pending 项

1. **GitHub push**：v1.6.1 已本地提交+打 tag（`766680bb`），因网络瞬断未推送 → 网络恢复后执行 `git push origin main --tags` 并补建 GitHub Release + asset + 远端 SHA 回验。
2. **WorkBuddy 真实复验**：需有该 Harness 的机器。
3. **Clean Machine Replay（live）**：需真实新机器/无旧工作区环境且网络可达 GitHub。

---

**227/227 测试全绿；结构校验器 0 错误 0 警告。**

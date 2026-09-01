# Development & Migration Guide

## v3 Stable 三种迁移（必须分开）

### A. 正式 Skill 迁移

普通用户和新电脑 Harness 只从 GitHub Stable Release Asset 安装，核对发布 SHA 后运行 `docs/validate_installed_copy.py` 与全量测试。资产不得包含 `.git`、`.mimosa`、`.pytest_cache`、`__pycache__`、`.pyc`、临时文件或 bootstrap；原开发目录不可用时仍须独立通过。此路径不迁移整个实验室。

### B. Adaptive Strategy 迁移（可选）

仅含六项执行偏好：question、planning、capability、recovery、execution order、interaction。Harness 若支持项目隔离状态同步可自行迁移；Skill 不规定物理存储或绝对路径。无状态必须使用默认策略，永不阻塞正式 Skill。

历史状态只能包含安全 Catalog ID。再次提供给 Runtime 时由 `load_strategy()` 验证；Strategy 更新只能通过当前 Delivery 的 Canonical Evidence Ledger ID，不能迁移或导入裸 PASS dict。

### C. Publisher 开发空间迁移（仅维护者）

只有明确需要在新电脑续开发整个实验室时，旧电脑 Harness 才导出私有 Workspace Bundle，新电脑 Harness 校验并恢复 Git/dirty state、重建依赖与验收。Bundle 禁止上传公开 Release，也不是正式 Skill 的运行条件。完整交接见开发空间 `06_项目说明文档/整个开发空间迁移指南.md`。

当前导航：产品目标在 `docs/current/FINAL_PRODUCT_TARGET.md`；运行时/Harness 在 `docs/HARNESS_GUIDE.md`；Adaptive Strategy 在 `共享/scripts/adaptive_strategy_core.py`；Publisher Maintenance 在 `共享/references/SKILL_EVOLUTION_ENGINE_SPEC.md`；旧 RC/Closure/SDD 是 HISTORICAL。

## 只维护本公开 Skill

GitHub 是公开 Skill 版本与历史的中央真源。新电脑 clone 仓库、获取 tags、验证 origin 后从开发分支继续：

```bash
git clone https://github.com/tl3981390-blip/enterprise-ai-project-delivery.git
cd enterprise-ai-project-delivery
git fetch --tags
git remote get-url origin
git tag --sort=-version:refname
git switch -c <work>-dev
```

不要在文档中长期写死“当前版本”；个人探索可从 GitHub Latest Stable 和 `共享/schema/RELEASE_METADATA.json` 发现版本。企业受控环境不跟随 Latest Stable，而是固定人类批准的精确 tag，并通过候选验证和明确授权升级。历史 tag 和 Release 资产不可移动、重建或覆盖。开发 Workspace 的恢复不改变任何企业运行环境已批准的 Skill 版本；正式环境仍从批准 tag 的 Release asset 安装。详见 [企业版本治理](ENTERPRISE_VERSION_GOVERNANCE.md)。

## 继续开发整个企业 Skill 实验室

单独 clone 本仓库不等于恢复整个实验室。完整 Workspace 还包括多个上游 Git 仓、非 Git 文档、证据、Harness 接入、历史区以及未提交/未跟踪内容。

正确迁移方式：

```text
旧电脑 Honey
→ 读取私有 Bootstrap 的 OLD_COMPUTER_MIGRATION_INSTRUCTION.md
→ 预检、生成 Workspace Bundle、逐文件校验
→ 用户只携带 ZIP + 同名 .sha256
→ 新电脑 Honey 读取 NEW_MACHINE_RESTORE_INSTRUCTION.md
→ 校验、恢复、重建依赖、运行验收
```

完整 Workspace Bundle 属于私有资产，不进入本公开 Skill Release。`.venv`、`node_modules`、缓存、凭据、Harness 用户目录和 Docker 运行态不直接迁移；数据库唯一数据按具体数据库单独备份。

## 身份规则

- Git commit hash 跨电脑保持不变；只有新提交才产生新 hash。
- Git tag 标识历史源码身份；Release 资产 SHA-256 标识已发布 ZIP，二者不是一回事。
- 重新压缩同样文件通常会得到不同 ZIP SHA-256，因此正式安装只验证原始 GitHub Release 资产。
- AI/Honey 可以代为运行 clone、验证和恢复，但不能绕过 GitHub、文件系统或企业权限边界。

## Release 之后

main 可以包含正式 tag 之后的文档、测试、适配器或候选改动；这不改变历史 Release。涉及 Core 的新行为必须满足真实失效、可泛化、可复现、有证据，并重新经过 Candidate 验收与新版本发布。

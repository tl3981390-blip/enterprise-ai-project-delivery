# UNIVERSAL_CLOSURE_ROOT_CAUSE_MAP（第二轮：通用交付 + 零摩擦安装 + 全工作区可迁移）

基线冻结（2026-08-31）：HEAD=`6705b57`（=v1.5.1 tag + docs-only），tags v1.0.0–v1.5.1，工作树干净，172/172 PASS；GitHub 仅有 v1.5.0 正式 Release（**v1.5.1 只推 tag 未建 Release**）；gh 已认证（keyring，repo scope）；实验室 7 个目录、11 个 Git 仓、1 个非 Git Skill 设计资产。

## 根因（本轮）

| # | 根因 | 机械证据 |
| --- | --- | --- |
| RC-9 复杂度无推导机制 | `risk_level` 是 profile 手填字段（product_completion_core.py:177），无 PROJECT_COMPLEXITY_ASSESSMENT；Harness 只能按项目标签/关键词直觉填级 → 关键词路由的结构性缺口仍在 |
| RC-10 无 DELIVERY_EXECUTION_PLAN | `derive_active_plan` 只输出阶段/Gate 清单，无每阶段 目标/工作/输出/进入/完成/验收/失败处理，无 Final Acceptance Matrix → Harness 退化输出「分析需求/开发/测试/交付」 |
| RC-11 无 USER_INTERACTION_BOUNDARY | 无 INTERACTION_MODE / WHAT_TO_EXPOSE / 内部状态翻译 → WorkBuddy 把 UNDERSTANDING_BLOCKED、Core/Gate 流水账直接倒给用户（真实症状） |
| RC-12 Release 身份多源维护 | 版本分散在 SKILL.md / install.py(FORMAL_VERSION="1.5.0" 已 stale) / AGENT_INSTALL.md(钉 v1.5.0) / README / adapter manifest，人工同步；install.py:73 字面 `or True` 恒真验证；v1.5.1 未建 GitHub Release（只 push tag ≠ 正式发布） |
| RC-13 INSTALLED_MODE 实为开发指针 | 唯一安装实例（~/.zcode 薄适配器）core_path 指向作者 `D:\企业Skill实验室` checkout → 正式使用依赖作者本机；Installed/Development 模式未分离 |
| RC-14 工作区纯本地资产 | `企业业务流程数据沉淀Skill`（15+ 设计文档，非 Git、无远端）、05 验收证据、06 评审文档、03 发布台账/规划说明 均只存本机；无 Manifest/Bootstrap/Handoff/就绪度度量 → 换机即丢失 |

## 已达标项（勿重复施工）

- 正式运行链（共享/scripts、schema、adapters）零本机路径依赖（grep 机械证实；残留仅为历史文档/evidence 记录，属 HISTORICAL_REFERENCE）。
- 关键词未进入核心决策代码（仅 `enterprise_governance` 作为能力注册表键名，按声明激活）。
- 适用性解耦/五路经验路由/假设变化模型/防钙化护栏：上一轮（v1.5.1）已建立并有 32 项 SYS 回归。

## Core Freeze 重开判定（仅限三项新机制）

```text
REAL_HARNESS_FAILURE      = YES （WorkBuddy：治理流水账直出用户；通用四段式计划）
CURRENT_CORE_INSUFFICIENT = YES （无复杂度推导/交付计划/交互边界机制）
GENERALIZABLE/REPRODUCIBLE/EVIDENCE_BACKED = YES（指令附录症状 + 上述代码缺口）
→ 允许新增：PROJECT_COMPLEXITY_ASSESSMENT / DELIVERY_EXECUTION_PLAN / USER_INTERACTION_BOUNDARY
→ 不动：既有 172 项回归语义；发布侧问题在 docs/installer 层修，不借机改 Core 其他部分
```

## 修复范围

Core：新 `共享/scripts/delivery_planning_core.py`（复杂度评估/能力需求推导/交付计划构建/交互边界/关键词上下文信号护栏）+ 规格 `共享/references/DELIVERY_PLANNING_SPEC.md`。
Release/Installer：`共享/schema/RELEASE_METADATA.json` 单一源；`docs/install.py` 重写（读元数据/真验证/负测试）；`docs/AGENT_INSTALL.md` URL-only 合同重写；补 v1.5.1 GitHub Release。
模式分离：~/.zcode 换装自包含 INSTALLED MODE；开发绑定另立（04_Harness接入适配 记录）。
Workspace：新建私有 Bootstrap 仓（Manifest/Handoff/Restore/Validator/关键非 Git 资产）；就绪度机械测量至 READY。

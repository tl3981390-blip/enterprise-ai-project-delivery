# UNIVERSAL_DELIVERY_AND_PORTABILITY_CLOSURE_REPORT

日期：2026-08-31 ｜ 执行：`UNIVERSAL_PROJECT_DELIVERY_AND_FULL_PORTABILITY_SYSTEMIC_CLOSURE`（37 步全序）｜ 状态：**CLOSED（2 项 PENDING_EXTERNAL_VALIDATION，如实标注）**

## 一、真实根因（本轮新增 RC-9..14）

| # | 根因 | 证据 | 修复 |
| --- | --- | --- | --- |
| RC-9 | 复杂度无结构推导 | `risk_level` 靠手填；Harness 只能按标签猜 | `delivery_planning_core.py::assess_complexity`（22 结构因子带权，rationale 具名，未知因子 fail-closed） |
| RC-10 | 无用户可见交付计划 | `derive_active_plan` 只出阶段/Gate 清单 | `build_delivery_execution_plan`（每阶段七要素 + Final Acceptance Matrix + 颗粒度降级为 Task） |
| RC-11 | 无交互边界 | WorkBuddy 把 Core/Gate 流水账直出用户 | `user_view(mode)`：USER 静默治理 + 内部码翻译；DIAGNOSTIC 全量 |
| RC-12 | Release 身份多源 | install.py 硬编码 1.5.0（stale）、AGENT_INSTALL 钉 v1.5.0、or True 恒真、v1.5.1 无正式 Release | `RELEASE_METADATA.json` 单一源；Installer 重写（读元数据/真验证/候选模式）；补建 v1.5.1 Release + v1.6.0 Release |
| RC-13 | INSTALLED 实为开发指针 | `~/.zcode` 薄适配器 core_path 指向作者 D:\ checkout | 换装自包含 v1.6.0 完整核心（零本机路径，metadata 自洽） |
| RC-14 | 工作区纯本地资产 | `企业业务流程数据沉淀Skill`（非 Git）、05 证据、06 文档、03 台账 仅本机 | 建私有 Bootstrap 仓 `enterprise-skill-lab-bootstrap`（Manifest/Handoff/Restore/critical-assets） |

## 二、问题分层

- **Core**：RC-9/10/11（复杂度推导/交付计划/交互边界）——新增 `delivery_planning_core.py`，不动既有可靠性不变量。
- **Adapter**：RC-13（薄适配器指本地）——换装自包含；adapter 语义层本轮无新缺陷。
- **Installer/Release**：RC-12（单一源/stale/or True/Release 缺失）——已修并机械验证。
- **Workspace**：RC-14（非 Git 资产无便携源）——Bootstrap 仓已建并推送。

## 三、关键词模板泄漏

`KEYWORD_TEMPLATE_ROUTING = ELIMINATED`：决策表（复杂度权重/能力推导）零关键词键名；`keyword_signals_are_context_only()` 机械断言（词边界匹配，CJK 包含匹配）每改必测（DYN-001）。同关键词不同复杂度 → 不同计划（DYN-004）；同结构不同标签 → 相同计划。

## 四、动态交付规划

- 复杂度：`LOW/MEDIUM/HIGH/CRITICAL` 均具名 rationale（DYN-002/003 + `test_every_level_has_rationale`）。
- 计划：Stage 七要素 + Final Acceptance Matrix（DYN-005/006）；无价值标记降级为 Task（颗粒度）。
- 展示后默认继续（NO_STAGE_WAIT 不变）；真实 Human Gate 仅限业务歧义/不可逆/授权/审批/专属验收/外部动作/架构方向。
- Replan：`assumption_change_model` 部分失效 + 重算（DYN-007）。

## 五、交互边界

`USER_INTERACTION_BOUNDARY = PASS`：USER 模式不泄漏 UNDERSTANDING_BLOCKED/CORE_RELEASE_IDENTITY_BLOCKED/NOT_APPLICABLE/Gate 图/Core Hash/Adapter 元数据（DYN-008）；内部码全部翻译为人类语言；DIAGNOSTIC 模式全量（DYN-009）；非法模式拒绝。

## 六、Evolution 防钙化

`EVOLUTION_TEMPLATE_CALCIFICATION_GUARD = PASS`：五路经验路由 + `FREQUENCY != GENERALIZABILITY` + Core 准入十项（上一轮已建，本轮 DYN-011/012 复测通过）。

## 七、安装与更新

- `URL_ONLY_SKILL_INSTALLATION = PASS`：AGENT_INSTALL.md URL-only 合同；用户只需给 Repo URL + 「帮我安装这个 Skill」。
- `REMOTE_FORMAL_UPDATE = PASS`：正式更新只走 Canonical Remote Release Metadata → 远端 Release → Download → Verify → Update；Installer 零本机路径（INST-009 机械断言）。
- `INSTALLED_MODE / DEVELOPMENT_MODE = PASS`：安装 = 自包含拷贝（`INSTALL_INFO.json`，无 D:\ 依赖）；开发 = 本机 checkout + 可选 dev 绑定（`04_Harness接入适配`）。
- `RELEASE_IDENTITY_SINGLE_SOURCE = PASS`：`RELEASE_METADATA.json` 唯一源；Installer/Adapter/Validator 均读它（INST-005/006）。
- `恒真验证已修`：`or True` 已消除（AST 剥离 docstring 后代码体零匹配，INST-008）；无效身份真 FAIL（INST-007 负测试）。

## 八、工作区迁移

- **Git 仓**：10 个（9 上游参考 + 1 产品仓）。全部有远端；产品仓 `enterprise-ai-project-delivery` tags v1.0.0–v1.6.0 全在远端。
- **Non-Git 关键资产**：`企业业务流程数据沉淀Skill`（设计）、`03_成品`（发布 zips/台账）、`05_验收证据`、`06_说明文档` —— 已复制进 Bootstrap 仓 `critical-assets/`。
- **曾经只存在本地**：上述 4 类；已建便携 Source of Truth（Bootstrap 仓）。
- **unpushed/untracked/local-only**：产品仓已全推；microsoft-skillopt 仅 `.mimosa/` 钩子态（非资产）；无 local-only 分支/未推 commit/stash。
- **Bootstrap 远端入口**：`https://github.com/tl3981390-blip/enterprise-skill-lab-bootstrap`（私库，与产品仓同账号）。
- **新电脑 Harness 取得方式**：clone 该 Bootstrap 仓 → 读 `NEW_MACHINE_RESTORE_INSTRUCTION.md` → 跑 `restore_workspace.py`。

## 九、Clean Machine Replay

- **真实输入**：Harness + GitHub 认证 + Skill Repo URL + Workspace Bootstrap URL。
- **本地沙箱 Replay（网络可用时）**：`workspace-bootstrap/clean_replay.py` 在 `mktemp -d` 隔离根执行 clone → restore → install → invoke，全程不读旧工作区；本轮因 GitHub 连接瞬断（curl 000）未能完成 live 版，**PENDING_EXTERNAL_VALIDATION**，已在恢复脚本 + MIG 测试中机械证明幂等/续跑/无本地依赖/安全（无 shell=True，AST 校验）。
- **恢复脚本实测**：`--plan-only` 检测 git/python/gh/认证全过；`--root <新路径>` 恢复全部仓 + 非 Git 资产 + 校验 READY（本机已实测一次完整恢复，网络可用时通过）。

## 十、真实 Harness 回归

- **ZCode（本会话，真实）**：`~/.zcode/skills/enterprise-ai-project-delivery` 已换装 v1.6.0 自包含核心；`validate-skill.py` 0 错误 0 警告；RELEASE_METADATA 1.6.0/55207d2 自洽。真实调用 = 本会话全程执行本 Skill（理解 → 合同 → 门禁 → 施工 → 回归 → 发布），即 Skill 的真实运行证据。
- **WorkBuddy**：`PENDING_EXTERNAL_VALIDATION`（本机无 CLI，绝不伪造）。复测合同：同一「家庭点菜单」显式调用应到达业务澄清而非 Skill 拒绝。

## 十一、Release / Tag / Hash

```text
v1.5.0 → 491f6c9f76c6c384fd18a21303aba56812eeadb1（历史不变）
v1.5.1 → ba7ca9e71d90c2a20eb994053a6d2bee21c36f2c（本轮补建 GitHub Release，远端 SHA == 本地 733c89b8…）
v1.6.0 → 55207d242aac741d82959de6fd778416c6d304d4（tag 指向 metadata 所在 commit；metadata 记 tag 目标）
zip    → enterprise-ai-project-delivery-v1.6.0.zip
SHA-256= 24c81e69f69354a31a32bb6b7f73149a9d66f7641649f8203b9ec17d1cff7715（远端回验 == 本地）
GitHub Release v1.6.0 = 已建（asset 上传 + 远端 SHA 回验一致）
```

## 十二、版本决策

本轮新增 Core 机制（复杂度推导/交付计划/交互边界）→ **MINOR = v1.6.0**（语义化版本；非 patch，因引入新能力而非仅缺陷修复）。历史 tag 未移动，v1.5.x 链完整。

## 十三、Core Freeze

本轮新增属合法重开（真实 Harness 症状 + 机制缺失 + 可泛化 + 可复现 + 证据）。完成后：

```text
CORE_FEATURE_FREEZE = ACTIVE
PRODUCT_CORE = v1.6.0 COMPLETE（通用动态交付 + 可靠性不变量）
```

## 十四、剩余外部人工动作（如实）

1. **WorkBuddy 真实复验**：在有 WorkBuddy 的机器上复测「家庭点菜单」。
2. **Clean Machine Replay（live）**：在一台真实新电脑/无旧工作区环境执行 `workspace-bootstrap/clean_replay.py`（需网络可达 GitHub）。
3. **TRAE 外部验证**：历史遗留，与本轮无关。
4. **FULL_SECURITY_AUDIT**：静态扫描 ≠ 完整 AST 审计环境，状态保持 `NOT_AVAILABLE`。

## 十五、停止规则

本轮到此收口。下一阶段由真实失效驱动（WorkBuddy 复验 / 真实新机器恢复 / 真实企业流程），非作者想象。

# 04｜企业AI项目交付 Skill 模块树

> Architecture C 正式模块树：独立 Skill + 选择性上游复用。内部保留主入口+阶段模块；上游只以带来源的 references 适配进入。

共享 references 的正式上游吸收层包含：上游吸收索引、SDD流程与规格模板、Plan模板、Tasks与分级仪式、需求表达与最少提问、Signoff与生产检查清单、Traceability与收敛。禁止引入 Spec Kit Runtime 或第二状态机。
> 说明：这是 **1 个公开 Skill**。节点模块数量为 20（含 S0 总控）；核心交付模块 19 个，均使用不会进入 `/` 发现菜单的 `MODULE.md` +（按需）references/scripts/tests。施工期可细拆/合并，但需在 `10` 中说明理由，禁止「看情况」式抹平。

---

## 物理目录（最终施工目标形态，设计草案）

```text
02_Skill二次开发区\企业AI项目交付Skill\
│
├── SKILL.md                        # 主 SKILL（触发 + S0 理解门禁 + 编排 + 总描述）
├── LICENSE / NOTICE                # 本 Skill 自身许可证与来源声明（施工期签发）
├── CHANGELOG.md / README.md        # 版本变更与使用说明（施工期签发）
│
├── 00_总控/                         # S0：施工前理解门禁 / 状态机 / 任务理解合同 / 计划-合同对账 / DRIFT_CHECK / 权限阶段控制 / 门禁 / 输出合同
│   ├── MODULE.md
│   └── references/
│       ├── 任务理解合同模板.md        # Task Understanding Contract 全文模板
│       ├── 施工前理解门禁.md          # UNDERSTANDING 门禁判定规则
│       ├── 目标漂移检查清单.md        # DRIFT_CHECK 清单
│       └── 状态与权限矩阵.md          # 12 状态状态机 + 各状态权限矩阵
│
├── 01_项目理解/
│   ├── MODULE.md                    # 强化：用户真正目标 / 最终结果 / 业务价值
│   └── references/目标声明模板.md
│
├── 02_当前状态审计/
│   ├── MODULE.md                    # 强化：已有什么/完成到哪/哪些真哪些假/哪些不可改
│   ├── references/存量审计清单.md
│   └── scripts/audit_scan.py        # 只读扫描辅助（施工期）
│
├── 03_需求与范围/
│   ├── MODULE.md                    # 强化：范围/非目标/禁止项/成功标准/关键约束
│   ├── references/禁用词检查.md
│   └── scripts/check_requirements.py
│
├── 04_SDD规格/
│   ├── MODULE.md
│   └── references/SDD规格模板.md
│
├── 05_TDD与测试策略/
│   ├── MODULE.md
│   └── references/TDD适用性判断.md
│
├── 06_架构设计/
│   ├── MODULE.md
│   └── references/架构评审清单.md
│
├── 07_RAG设计/
│   ├── MODULE.md
│   ├── references/RAG四防检查.md
│   └── scripts/verify_citation.py    # 防假引用（施工期）
│
├── 08_Agent设计/
│   ├── MODULE.md
│   └── references/多角色职责分离.md
│
├── 09_MCP与工具权限网关/
│   ├── MODULE.md
│   ├── references/权限矩阵模板.md
│   └── scripts/check_permission.py
│
├── 10_企业治理与合规/
│   ├── MODULE.md
│   └── references/治理检查清单.md
│
├── 11_施工管理与增量实现/
│   ├── MODULE.md
│   └── references/Definition-of-Done.md
│
├── 12_失败处理与恢复/
│   ├── MODULE.md
│   ├── references/失败处理流程.md
│   └── scripts/stop_condition.py
│
├── 13_浏览器真实验收/
│   ├── MODULE.md
│   └── references/浏览器验收检查.md
│
├── 14_多角色验收/
│   ├── MODULE.md
│   └── references/四角色验收模板.md
│
├── 15_Evidence与防假验收/
│   ├── MODULE.md
│   ├── references/证据schema.md
│   └── scripts/collect_evidence.py
│
├── 16_部署/
│   ├── MODULE.md
│   └── references/部署检查清单.md
│
├── 17_License与合规/
│   ├── MODULE.md
│   └── scripts/scan_license.py
│
├── 18_升级与回滚/
│   ├── MODULE.md
│   ├── references/回滚演练.md
│   └── scripts/semver_check.py
│
├── 19_最终交付与经验沉淀/
│   ├── MODULE.md
│   └── references/最终报告模板.md
│
├── 共享/
│   ├── references/                 # DoD、公共检查清单
│   │   ├── Definition-of-Done.md
│   │   └── 公共检查清单.md
│   ├── scripts/                    # validate-skill、check_understanding_gate、check_plan_alignment、collect-evidence 等通用工具
│   │   ├── validate-skill.py
│   │   ├── check_understanding_gate.py
│   │   ├── check_plan_alignment.py
│   │   ├── collect_evidence.py
│   │   └── ...
│   └── schema/                     # JSON Schema：任务理解合同 / 输出 / Evidence / input
│       ├── task_understanding_contract.schema.json
│       ├── output_schema.json
│       ├── evidence_schema.json
│       └── input_schema.json
│
└── tests/
    └── evals/                      # Skill 自身结构与行为测试数据
        ├── structural/             # 结构/版本/license/schema 校验
        ├── trigger/                # 触发测试
        ├── state_machine/          # 状态机合法跳转测试
        └── understanding/          # 专项 Eval A-E（见 07）
```

---

## 模块职责总览（含输入/输出/门禁）

| 模块 | 职责 | 主要输入 | 产出物 | 通过门禁（下放的条件） |
| ---- | ---- | -------- | ------ | ---------------------- |
| S0 总控 | 编排各阶段、**施工前理解门禁（UNDERSTANDING→任务理解合同→Gate→READY_TO_PLAN）**、状态机推进、**计划-合同对账**、**DRIFT_CHECK**、**权限阶段控制**、发布门禁、执行停止条件、汇总输出合同 | 用户目标/上下文 | 阶段状态机、任务理解合同、最终交付包 | —（发起者） |
| 01 项目理解 | **用户真正目标/最终结果/业务价值**、为什么做/给谁用/价值 | 业务诉求 | 目标声明 | 目标声明可评审 |
| 02 状态审计 | 判存量真实情况（已有什么/完成到哪/**哪些真哪些假**/**哪些不可改**），禁默认从零 | 现有系统路径 | 存量审计清单+证据 | 存量结论有证据 |
| 03 需求与边界 | **范围/非目标/禁止项/成功标准/关键约束**，清不确定词 | 目标声明 | 需求规格 | 无禁用词+验收标准可判 |
| 04 SDD | 先规格后编码，全维度规格 | 需求规格 | SDD 规格 | 规格机械可检查项通过 |
| 05 TDD | 判断式测试策略 | 规格/架构 | 测试策略+关键测试 | 核心逻辑测试真实通过 |
| 06 架构设计 | 架构/组件/接口/部署形态 | 规格 | 架构设计 | 架构评审通过 |
| 07 RAG 设计 | 知识源/索引/权限/引用/拒答，四防 | 数据情况 | RAG 方案 | 防幻觉/越权/旧版/假引用用例过 |
| 08 Agent 设计 | 角色分离（逻辑角色），多 Agent 适度 | 架构 | Agent 设计 | 职责分离清单过 |
| 09 权限网关 | READ/WRITE/DELETE/EXECUTE/ADMIN/EXTERNAL 矩阵 | 工具/MCP 清单 | 权限矩阵 | 拒绝用例过 |
| 10 企业治理 | 审计/SSO/数据不出域/合规/变更管理 | 企业政策 | 治理清单 | 治理项外链到企规 |
| 11 施工管理 | 增量实现+DoD，防一次性大段 | 任务拆解 | 可交付增量 | 每增量测试+提交过 |
| 12 失败处理 | 根因定位+证据保留+自动/人工修复边界 | 失败现场 | 失败证据+修复记录 | 阻塞消失才 PASS |
| 13 浏览器验收 | 真实浏览器操作验证 Web 产品 | 运行中系统 | 浏览器证据 | 无 console/网络异常 |
| 14 多角色验收 | 需求/工程/安全/用户 四视角 | 交付物 | 四角色验收表 | 四角色均 PASS |
| 15 Evidence | 统一证据合同，防假验收 | 全阶段证据 | Evidence 包 | schema 校验过 |
| 16 部署 | Build→Deploy→回滚，非「本地能跑」 | 验收产物 | 部署记录 | 部署清单过 |
| 17 License | 代码/依赖/模型/数据许可合规 | 代码/依赖 | 许可报告 | 无红色许可 |
| 18 升级回滚 | Version/Migration/BackCompat/Rollback | 已发布版 | 发布+回滚方案 | 回滚演练过 |
| 19 收尾沉淀 | 最终报告+经验入库 | 全流程 | 最终交付包 | 目标完成有证据 |

---

## 模块生命周期依赖（门禁顺序，主 SKILL 执行）

```text
[UNDERSTANDING] → [任务理解合同] → [施工前理解门禁] → [READY_TO_PLAN]   ← S0 最高门禁，任何施工之前
                                                                  （阻断点：UNDERSTANDING_BLOCKED / BLOCKED）
S0 → 01 → 02 → 03 → 04 → 05 → 06 → [07 | 08 | 09 | 10] → 11 ⇄ 12 → 13 → 14 → 15 → 16 → 17 → 18 → 19 → 复盘
```

- 第一行是 S0 施工前理解门禁，位于所有阶段模块之前；其状态机见 `00_总控\references\状态与权限矩阵.md`（12 状态，不能从 UNDERSTANDING 直接跳 EXECUTING）。
- 每个阶段模块执行前，须经 `PLAN_CONTRACT_ALIGNMENT_CHECK` 与执行期 `DRIFT_CHECK` 与任务理解合同对账（见 `00_总控\references\目标漂移检查清单.md`）。
- `[07|08|09|10]`：治理设计 4 模块可在架构定稿后并行/依序，但各自有独立门禁。
- `11 ⇄ 12`：施工与失败处理循环，须受最大循环/停止条件约束。
- 每个箭头上的门禁未过 → 主 SKILL 暂停并请求人工介入（见 `12` 停止条件）。

---

## 设计取舍说明（为什么是这个模块数/分法）

1. **分组贴合生命周期**：阶段 A-G 即 理解→设计→治理→施工→验收→发布→沉淀，映射 addyosmani 的 Define/Plan/Build/Verify/Review/Ship，但增加了企业治理与 Evidence 两大企业特有面（来自我的方法论，见 `03`）。
2. **单模块职责 coherent**：每模块对应一个可独立验证的工作单元，避免过宽/过窄（依据 agentskills best-practices「范围像函数」）。
3. **共享 references/scripts 去重**：DoD、权限矩阵、evidence schema 等公共件放共享区，多个模块引用（依据 addyosmani references/ 模式）。
4. **未照抄 addyosmani 26 个**：去掉了 code-simplification/performance-optimization 等偏通用工程项（它们更像是企业内部其他 Skill 的职责），保留企业 AI 交付必需的 19 项。此项判断为工程推断，施工期可回检。

> 模块树的最终可执行化（每个模块写什么内部章节、放哪些脚本）在 `10_正式施工计划.md` 分阶段落地。

# 06｜输入输出与 Evidence 合同

> 目的：定义 Skill 的输入输出结构化契约（项目级，非 Harness 级调用），以及统一的 Evidence 证据链设计。回答「Skill 是否应使用 JSON Schema」。

---

## 1. 为什么需要结构化输入输出

Skill 不能只输出自然语言。理由：

1. **可验收**：结构化字段让「过/不过」可判、可自动核对。
2. **可追踪**：阶段结论与真实证据挂钩，避免「AI 说完成」。
3. **可驱动 Harness**：门禁/人工介入/审计都依赖结构化结果。
4. **可回滚/可续跑**：保存状态用于 suspend/resume（依据 `05` 生命周期）。

---

## 2. 项目级输入合同（ProjectInput，每次用本 Skill 交付一个项目时填写）

```jsonc
{
  "skill_version":   "string",     // 用哪个 Skill 版本
  "goal":            "string",     // 业务目标（一句话）
  "business_value":  "string",     // 商业/业务价值
  "users":           ["string"],   // 谁用
  "system_context":  "string",     // 在哪套系统里用
  "data_sources":    ["string"],   // 数据从哪里来
  "ai_responsible":  ["string"],   // AI 负责什么
  "human_responsible":["string"],  // 人工负责什么
  "org_policy_ref":  "string",     // 企业政策引用（合规/数据不出域/审批）
  "user_identity":   "object"      // 角色、权限域、审计 id
}
```

> 这一份先于任何编码完成（模块 01）。缺「谁用/数据从哪/价值」视为目标未定义，禁止进入编码。

### 2.1 任务理解合同（Task Understanding Contract，S0 施工前理解门禁产物）

UNDERSTANDING 阶段结束时必须产出，纳入每个项目交付的起点（`schemas/task_understanding_contract.schema.json` 可机器校验）：

```jsonc
{
  "task_id":            "string",
  "user_real_goal":     "string",   // 用户真正要解决的问题
  "business_goal":      "string",   // 为什么做（业务价值）
  "final_deliverable":  "string",   // 最终交付物
  "current_state":      "string",   // 当前项目已有什么
  "completed_scope":    "string",   // 已经完成到什么程度
  "work_scope":         "array",    // 本轮工作范围
  "explicit_non_goals": "array",    // 明确非目标
  "allowed_modify":     "array",    // 允许修改范围
  "forbidden_modify":   "array",    // 禁止修改范围
  "allowed_tools":      "array",
  "forbidden_tools":    "array",
  "key_constraints":    "array",    // 关键约束
  "success_criteria":   "array",    // 成功标准
  "acceptance_criteria":"array",    // 验收标准
  "evidence_requirements":"array",  // Evidence 要求
  "known_risks":        "array",
  "blocking_unknowns":  "array",    // 阻塞性未知项
  "non_blocking_unknowns": "array", // 非阻塞性未知项
  "provenance":         "object",   // 每个结论来源，见第 2.2 节
  "understanding_status":"enum"     // UNDERSTANDING_COMPLETE / BLOCKED / UNDERSTANDING_BLOCKED
}
```

### 2.2 结论来源分级（来源可追踪）

每个重要结论标记来源，`AI_INFERRED` 禁止冒充用户要求：

| 来源码 | 含义 |
| ---- | ---- |
| `USER_EXPLICIT` | 用户当前明确提出 |
| `USER_PREVIOUSLY_CONFIRMED` | 此前已明确确认且仍有效 |
| `PROJECT_EVIDENCE` | 真实项目/文件/Git/代码/配置支持 |
| `SYSTEM_OBSERVED` | 运行环境真实观察 |
| `AI_INFERRED` | AI 推断（重大范围/权限/**不**能仅凭它升级为合同事实） |

> 施工前八问与来源规则详 `00_总控\references\施工前理解门禁.md`。

### 2.3 状态机（S0 权限阶段控制依据）

`UNDERSTANDING → UNDERSTANDING_BLOCKED/UNDERSTANDING_COMPLETE → READY_TO_PLAN → PLANNING → PLAN_BLOCKED/PLAN_COMPLETE → READY_TO_EXECUTE → EXECUTING → EXECUTION_BLOCKED/VERIFYING → COMPLETED`。UNDERSTANDING 阶段仅允许 `READ/SEARCH/INSPECT/ANALYZE/COMPARE/SUMMARIZE/VALIDATE_EXISTING_STATE`；写改权限在 `READY_TO_EXECUTE` 后按模块开放（`05` 第 10 节）。禁止从 UNDERSTANDING 直接跳 EXECUTING。

---

## 3. 项目级阶段输出 + 最终交付输出（ProjectStatus）

```jsonc
{
  "goal":            "string",
  "stage":           "string",     // 当前阶段
  "phase_status":    { "01_项目理解": "passed", "03_需求与范围": "blocked", "…": "…" },
  "completed":       ["string"],
  "blocked":         ["string"],
  "risks":           ["string"],
  "evidence_ids":    ["string"],   // 关联的证据包
  "human_signoffs":  ["string"],   // 四角色验收结论
  "can_enter_next":  "boolean",    // 是否允许进入下一阶段
  "rollback_info":   "string|nil", // 若有发布，回滚方案引用
  "lessons":         ["string"]    // 19 沉淀
}
```

---

## 4. 统一 Evidence 契约（复用 `05` 的 evidence_schema，项目管理层）

### 4.1 证据类型白名单

| type | 捕获方式 | 是否可被信任 |
| ---- | -------- | ------------ |
| `git_head` | `git rev-parse HEAD` 输出 | ✅ |
| `build_id` | CI/build 产物 id | ✅ |
| `api_response` | 真实 HTTP 响应体/状态码 | ✅ |
| `browser_capture` | 浏览器截图/console/network 快照 | ✅ |
| `test_result` | 测试运行器的真实输出（退出码+记录） | ✅ |
| `log` | 运行日志片段 + 文件路径 | ✅ |
| `db_record` | 数据库读出的记录行（脱敏后） | ✅ |
| `screenshot` | 截图文件路径 + 哈希 | ✅ |
| `hash` | 文件/产物哈希 | ✅ |
| `file_path` | 存在的文件绝对路径 + 内容摘要 | `⚠️ 仅辅助` |
| `runtime_id` | 运行时/进程 id + 时间窗 | ✅ |
| `task_understanding_contract` | 任务理解合同（schema 校验通过） | ✅ |
| `understanding_gate_result` | 施工前理解门禁判定结果 | ✅ |
| `plan_alignment_result` | 计划-合同对账结果 | ✅ |
| `drift_check_log` | DRIFT_CHECK 过程日志（含约束冲突记录） | ✅ |
| `constraint_conflicts` | 识别到的约束冲突明细 | ✅ |
| `model_text` | 模型生成的总结文字 | ❌ **禁止当证据** |

### 4.2 证据包（Evidence Bundle）

每个阶段汇成一个文件夹 + 索引：

```text
evidence/
└── <stage>/
    ├── index.json              # 证据清单（可被 JSON Schema 校验）
    ├── *.jsonl                 # append-only 事件流（seq/ts/stage/event）
    ├── *.png | *.log | *.json   # 原始证据文件
    └── manifest.sha256         # 全部文件哈希清单
```

- **append-only**：只追加，不覆盖；便于审计（依据 recorder/skillopt 事件流）。
- **redact_secrets**：入库前清洗密钥/敏感 PII（依据 skillopt evidence.py + recorder 隐私）。
- **checksum**：防篡改（依据我能力 `16`）。

---

## 5. 防假验收映射（什么能当证据，什么不能）

| “证据候选” | 判定 | 说明 |
| ---- | ---- | ---- |
| 代码看起来没问题 | ❌ | 无真实运行证据 |
| 测试文件存在 | ❌ | 未运行不算数（rule: 测试文件存在≠测试通过） |
| `pytest`/`npm test` 真实退出码 0 + 记录 | ✅ | 真实执行 |
| 页面能打开 | ❌ | 仅打开不够；需浏览器检查 console/network/交互 |
| 浏览器真实操作 + console0错误 + 交互通过 | ✅ | 浏览器证据 |
| AI 说已完成 | ❌ | 无外部佐证 |
| 模型总结文字 | ❌ | 明令禁止 |
| 接口代码存在 | ❌ | 未调用不成立 |
| 真实 API 调用返回预期状态码+body | ✅ | api_response |
| README 说支持 | ❌ | 文档≠功能 |
| 回滚演练真实执行并成功恢复 | ✅ | 部署回滚证据 |

---

## 6. 是否应使用 JSON Schema —— 推荐

**推荐：JSON Schema（必须）+ 人类可读摘要（附加）。**

理由：
1. **可机器校验**：`validate-skill` / Harness / CI 都能直接校验输出是否符合合同（依据 agentskills validator 的思路）。
2. **可自动化门禁**：`can_advance`、`evidence_ids` 缺一即可机检。
3. **跨模型/跨 Harness 兼容**：JSON Schema 与具体模型无关（企业目标：不绑单一模型）。
4. **自然语言仅作摘要**：给人类阅读，但不作为验收依据。

建议的 schema 版本与校验脚本在施工期 `10` 阶段落地（共享 `scripts/schema/`），本阶段仅定契约本文。

---

## 7. 契约完整性自检

- [x] 项目输入（目标五问）强制
- [x] **任务理解合同（2.1）+ 来源分级（2.2）+ 状态机（2.3）**（本次补强新增）
- [x] 阶段输出 + 最终交付结构化
- [x] Evidence 类型白名单 + 「模型文字禁止」+ **理解类证据（2.3 引入）**
- [x] 证据包结构与防篡改
- [x] JSON Schema 推荐
- [ ] schema JSON 文件与校验器 → 施工期
- [ ] 与 `05` evidence_schema 对齐：本项目证据类型集 = `05` 类型集的子集扩容，保持一致
# 05｜Skill 与 Harness 接口合同（草案）

> 目的：定义企业AI项目交付 Skill 与未来 Agent Harness 之间的接口契约。本阶段**仅定义合同，不修改 Harness 主工程**。Harness 侧落地在 `04_Harness接入适配`（后续阶段，本阶段禁止动 Harness）。

---

## 1. 设计原则

1. **Skill 声明所需，Harness 注入能力**：Skill 不写死工具/MCP 连接，只声明需要什么、允许什么。
2. **一个 skill_id、一个入口、一个版本**：Harness 只注册一次，内部模块由主 Skill 编排。
3. **合同的每个字段可被静态校验**：防止 Skill 漂移（依据 agentskills validator + addyosmani evals 的 structural 检查）。
4. **权限最小化**：默认无管理员/生产/root 权限（依据我的能力 `24`）。
5. **Evidence 与失败语义内建**：Skill 每次调用都要能返回结构化结果与失败原因。

---

## 2. Skill 注册/元数据字段

| 字段 | 类型 | 必填 | 作用 | 示例 |
| ---- | ---- | ---- | ---- | ---- |
| `skill_id` | string | ✅ | 全局唯一标识，命名 kebab-case | `enterprise-ai-project-delivery` |
| `name` | string | ✅ | 人类可读名 | `企业AI项目交付Skill` |
| `version` | semver | ✅ | Skill 自身版本，见 `07/08` | `1.0.0` |
| `description` | string≤1024 | ✅ | 触发描述（祈使式），标准 frontmatter | “交付一个企业 AI 内部产品… Use when …” |
| `compatibility` | string≤500 | 可选 | 环境要求 | 无特定模型绑定 |
| `license` | string | ✅ | 本 Skill 自身许可 | `MIT`（施工期签发，见 `09`） |
| `entrypoint` | path | ✅ | 主 SKILL 入口 | `SKILL.md` |
| `modules` | list | ✅ | 可用阶段模块 | `[01_项目理解, 02_当前状态审计, …]` |
| `entrypoint_args` | string | 可选 | 入口附带参数 | 预填企业/项目上下文 |

---

## 3. 运行/依赖契约

| 字段 | 类型 | 说明 |
| ---- | ---- | ---- |
| `required_context` | object | Skill 运行前必须注入的上下文：`project_dir`、`org_policy_ref`、`user_identity`、`goal` |
| `required_tools` | list<string> | 必须可用否则 Skill 拒绝执行（如 git、浏览器） |
| `allowed_tools` | list<string> | 可调用白名单（最小化） |
| `blocked_tools` | list<string> | 显式禁止（如生产写库、root） |
| `required_mcp` | list`<mcp_id>` | 需要的 MCP server（若项目涉及） |
| `allowed_mcp` | list | MCP 白名单 |
| `permissions` | object | 权限矩阵，见下 |
| `runtime_context` | object | 执行期变量：`session_id`、`workspace`、`evidence_dir`、`token_budget`、`max_loop` |

### permissions 结构（READ/WRITE/DELETE/EXECUTE/ADMIN/EXTERNAL 分级）

```jsonc
{
  "permissions": {
    "filesystem":     { "project": ["READ","WRITE"], "elsewhere": ["READ"], "production_secrets": [] },
    "database":       { "dev": ["READ"], "prod": [], "migrate_prod": [] },
    "network":        { "external": ["READ"], "webhook_post": [] },
    "browser":        { "local_dev": ["EXECUTE"], "production": [] },
    "deploy":         { "execute": [], "rollback": [] },
    "admin":          []  // 默认空
  }
}
```

> 说明：权限按「默认拒绝、显式允许」最小化。高风险操作（EXECUTE/ADMIN/写生产/外发）不能因模型要求自动执行，必须显式配置 + 人工确认（依据我的能力 `10/24`；anthropic `~~category` 抽象思想）。

---

## 4. 调用输入契约（input_schema）

主 Skill 入口接受的最小输入（建议 JSON）：

```jsonc
{
  "goal":              "string",   // 业务目标
  "project_dir":       "string",   // 工作目录绝对路径
  "phase":             "enum",     // 可选：从指定阶段开始；默认从 UNDERSTANDING（S0 理解门禁）
  "org_policy_ref":    "string",   // 企业制度/政策引用（数据不出域、审批等）
  "user_identity":     "object",   // 角色、权限域、审计 id
  "constraints":       "object[]", // 企业侧硬约束（合规/范围/期限/禁止项）
  "evidence_base":     "string"    // 证据目录（默认由 Harness 分配）
}
```

> 默认入口即**理解门禁入口**：`phase` 未显式指定时，Skill 先进入 `UNDERSTANDING`，任何 WRITE/EDIT/EXECUTE 在理解门禁 PASS 前被拒绝（见第 10 节）。

---

## 5. 输出契约（output_schema）

Skill 每次阶段/设备完成必须输出规范化结果：

```jsonc
{
  "phase":            "string",      // 当前阶段 id（含 "UNDERSTANDING" / "PLANNING" / "EXECUTING" …）
  "status":           "enum",        // 状态机状态，见第 10 节："UNDERSTANDING" | "UNDERSTANDING_BLOCKED" | "BLOCKED" | "UNDERSTANDING_COMPLETE" | "READY_TO_PLAN" | "PLANNING" | "PLAN_BLOCKED" | "PLAN_COMPLETE" | "READY_TO_EXECUTE" | "EXECUTING" | "EXECUTION_BLOCKED" | "VERIFYING" | "COMPLETED"
  "goal":             "string",
  "understanding_contract": "object|nil",  // 任务理解合同（UNDERSTANDING 阶段产物），见 `06` 第 6.1 节
  "gate_results":     { "understanding_gate": "PASS|FAIL", "plan_alignment": "PASS|FAIL", "drift_check": "PASS|DRIFT_DETECTED" },
  "completed":        ["string"],    // 本阶段完成项
  "blocked":          ["string"],    // 阻塞项
  "risks":            ["string"],
  "evidence":         [Evidence],    // 真实验证引用，见 `06`
  "suggested_next":   ["string"],
  "can_advance":      "boolean",     // 是否允许进入下一阶段（门禁结果）
  "requires_human":   "boolean",     // 是否需人工介入
  "human_action":     "string|nil"   // 需要人工做的具体事
}
```

---

## 6. 失败契约（failure_schema）

| 字段 | 说明 |
| ---- | ---- |
| `failure_type` | 分类：`tool_denied` / `permission_denied` / `test_failed` / `evidence_missing` / `loop_exhausted` / `human_required` / `external` |
| `failure_reason` | 根因描述 |
| `evidence_captured` | 失败现场证据引用（必填，防改报告 PASS） |
| `auto_repair_attempted` | 是否已尝试自动修复 |
| `retry_count` / `max_retry` | 重试进度 |
| `recommendation` | 推荐修复路径或人工动作（源自 addyosmani debugging / skillopt RolloutResult.fail_reason 思想） |

---

## 7. Evidence 输出契约（evidence_schema）

```jsonc
{
  "evidence_id":   "string",
  "stage":         "string",            // 产生阶段
  "type":          "enum",              // git_head | build_id | api_response | browser_capture | test_result | log | db_record | screenshot | hash | file_path | runtime_id
  "payload":       "object|path",       // 结构化数据或文件引用
  "ts":            "int",               // epoch ms
  "seq":           "int",               // 单调序列
  "checksum":      "string",            // hash，防篡改
  "source":        "string"             // 生成主体（agent/mcp/tool/人为）
}
```

依据：microsoft-skill-recorder 事件契约（type→payload、seq、ts）+ microsoft-skillopt evidence.jsonl（stage/event、redact）+ 我的能力 `16`。

---

## 8. 生命周期契约

| 操作 | 入参 | 出参 |
| ---- | ---- | ---- |
| `discover` | — | 注册元数据（第 2 节） |
| `invoke` | input_schema | output_schema + evidence |
| `advance`（门禁） | 当前 phase + output | 是否放行下一 phase |
| `suspend`（人工介入） | reason | 挂起凭证，等待人工 |
| `resume` | 人工决策 | 恢复上下文并续跑 |
| `collect_evidence` | phase | 该阶段 evidence 包 |
| `version` | — | 当前版本 + changelog + 兼容性 |

---

## 9. 权限路由意图（Harness/Adapter 侧未来实现）

```text
Skill 声明 required/allowed_tools+mcp+permissions
   ↓
Adapter 把声明映射到 Harness 的 Tool/MCP 白名单
   ↓
Permission Gateway 运行时拦截：READ 放行 / WRITE 需检 / EXECUTE|ADMIN|外发 需人工
   ↓
审计日志记录每次调用与授权
```

> 本阶段只定义本合同；Adapter/Permission Gateway/Harness 修改一律在 `04_Harness接入适配` 后续阶段执行，本阶段 **不触碰 Harness**。

---

## 10. 理解门禁与状态机在 Harness 侧落地

- 状态机共 12 个状态：`UNDERSTANDING → UNDERSTANDING_BLOCKED / UNDERSTANDING_COMPLETE → READY_TO_PLAN → PLANNING → PLAN_BLOCKED / PLAN_COMPLETE → READY_TO_EXECUTE → EXECUTING → EXECUTION_BLOCKED / VERIFYING → COMPLETED`。**禁止从 UNDERSTANDING 直接跳 EXECUTING**（详见 `00_总控\references\状态与权限矩阵.md`）。
- **权限阶段控制**：Harness/Adapter 依据当前状态放行权限 —— UNDERSTANDING 阶段仅开放 `READ/SEARCH/INSPECT/ANALYZE/COMPARE/SUMMARIZE/VALIDATE_EXISTING_STATE`；`WRITE/EDIT/EXECUTE/DEPLOY/MIGRATE/INSTALL/ALTER` 在 `READY_TO_EXECUTE` 后才按模块开放。
- 若在非授权状态下出现写改请求，Gateway 返回 `permission_denied`（`failure_schema.failure_type`），并写入 `drift_check_log`（`CONSTRAINT_CONFLICT`）。
- 理解门禁在 Harness 侧仅做**结构/权限**强制；**业务含义是否理解**由 Skill 的 UNDERSTANDING 模块判定（脚本不能替代 AI 对业务含义的判断）。

## 11. 合同自检（本次设计是否完整）

- [x] skill_id/name/version/description/entrypoint
- [x] required_context / required_tools / allowed_tools / required_mcp / permissions
- [x] input_schema / output_schema / evidence_schema / failure_schema / status
- [x] 生命周期操作（discover/invoke/advance/suspend/resume）
- [x] **施工前理解门禁 + 12 状态状态机 + 权限阶段控制（UNDERSTANDING 只读，READY_TO_EXECUTE 后放开）**（本次补强新增）
- [x] **任务理解合同入输出契约（`understanding_contract` / `gate_results`）**
- [ ] 静态校验器（把合同变成可机器检查的 JSON Schema）→ 施工期 `10` 阶段落地
- [ ] 与具体 Harness 的解耦适配层 → `04_Harness接入适配` 阶段

> 对输出是否使用 JSON Schema 的推荐：见 `06` 第 6 节（推荐 JSON Schema + 附自然语言摘要）。
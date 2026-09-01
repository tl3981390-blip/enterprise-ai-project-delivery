# 09｜License 与来源边界

> 目的：定义本 Skill 可合法使用/复用的来源边界，明确「哪些能拿、拿了怎么保留声明、哪些绝对禁止」。承接 `06_项目说明文档\开源许可证检查表.md` 的结论。

---

## 1. 来源边界地图（谁能给本 Skill 供什么）

| 来源仓库 | 本 Skill 与它的关系 | 许可 | 能否向商业产物借用代码/结构 | 保留声明要求 |
| -------- | ------------------- | ---- | ---------------------------- | ------------ |
| addyosmani-agent-skills | 工程组织方式参考（how/Who/when、模块章节、DoD、eval） | **MIT** | ✅ 可引用代码/文档，须保留 MIT 版权与许可声明 | 复制/实质部分须含原版权与许可 |
| agentskills-standard | 开放标准遵循（frontmatter、目录、validator 规则） | **Apache-2.0** | ✅ 可遵循规范；若直接使用其参考实现/文档片段，须按 Apache 保留声明/NOTICE | 分发须附 Apache 声明、保留属性 |
| anthropic-knowledge-work-plugins | 企业岗位组织 + `~~category` 工具抽象（思想迁移） | **Apache-2.0** | ✅ 迁移思想/目录结构；直接抄 SKILL 内容按 Apache | 若含其文本须保留声明 |
| microsoft-skill-recorder | Evidence/事件流数据结构（思想采纳，非代码） | **MIT** | ✅ 可参考其 types 设计；复制代码须 MIT 声明 | 复制须保留 MIT |
| microsoft-skillopt | Gate/Staging/evidence 机制（思想采纳） | **MIT** | ✅ 可参考机制；复制代码须 MIT 声明 | 复制须保留 MIT |
| github/spec-kit @ `51e52be6…` | Specification/Clarification/Planning 思想与上游能力组合 | **MIT** | ✅ 可调用或依法适配；复制代码须保留声明 | 保留 MIT 版权与许可 |
| mariano-aguero/spec-driven-development-skill @ `939b1e74…` | SDD、EARS、Traceability 思想 | **MIT** | ✅ 可调用或依法适配；复制代码须保留声明 | 保留 MIT 版权与许可 |
| unboundinnov/specdd @ `a75bd6aa…` | 最少提问、变更回写、生产检查思想 | **MIT** | ✅ 可调用或依法适配；复制代码须保留声明 | 保留 MIT 版权与许可 |
| openai-skills-reference | **只读架构参考，禁止复制** | 根无许可；.system 无许可；.curated=Apache-2.0 | ❌ OpenAI 自有 `.system` **禁止**借用进商业产品；`.curated` 第三方若引用须逐个核 Apache 作者 | `.curated` 引用须保留各自 Apache 声明 |

---

## 2. 本项目（企业AI项目交付 Skill）自身的 License 策略

- 本公开 Skill Core 已正式采用 **MIT License**，仓库根目录 `LICENSE` 与 `NOTICE` 已签发并随 Stable Release 分发。
- MIT 允许商业使用、修改和再分发，但必须保留许可证与版权声明，并且软件按“无担保”条件提供。
- 已公开的 MIT 版本不能通过后续改许可证收回既有接收者已经获得的权利。
- 收费产品应把私有企业策略、连接器、集中 Evidence、认证发行、实施和 SLA 放在独立私有扩展或服务层；不得把私有 Workspace/Bootstrap 混入公开 Release。
- 正式销售前仍需由知识产权律师复核实际复制边界、商标、合同和责任条款；本文件不是法律意见。

无论选择公开 Core 还是私有商业扩展，只要实际复制或改写上游内容，都必须按对应许可保留版权和许可声明。

---

## 3. 必须保留来源与 NOTICE 的文件（建议结构）

```text
企业AI项目交付Skill\
├── LICENSE                 # 本 Skill 自身许可
├── NOTICE                 # 声明采用了哪些上游项目、各自许可
├── 00_引用来源清单.md       # 每个设计决策 → 来源 → 许可 → 保留声明
└── 03_我的项目能力提炼表.md #（已在 `03` 记录能力来源）
```

每个实际复制/改写自上游的脚本或文档都要增加来源和许可声明；仅有思想借鉴时在来源映射与 NOTICE 中说明，不伪称代码复制。

---

## 4. 使用合规动作清单（施工与后续每个阶段必须执行）

| 动作 | 触发点 |
| ---- | ------ |
| 复制上游代码 → 头部来源+许可注释，并登记来源清单 | 每次借用 |
| 借鉴思想/结构 → 在 `03`/来源清单标注"思想采纳，非代码复制" | 设计引用 |
| 扫描依赖 License | 模块 17 / 每版本 |
| 检查模型使用条款/数据许可/字体/图片/三方组件 | 模块 17 |
| OpenAI `.system` 内容 → 仅只读，任何阶段禁止复制进本仓库 | 全程 |
| 商业化前证明可合法使用（依赖/数据/模型） | Release 前（模块 17） |

---

## 5. 与 `02` 对照表的关系
- `02` 回答「能力怎么拿」（an evolution of capabilities），本文件回答「能不能合法拿 + 怎么保留声明」（legal boundary）。两者配套使用。
- 本文件的「禁止」优先：即使某项能力在 `02` 被勾选采纳，若源于 OpenAI `.system`，也**一律禁止**（只读）。

---

## 6. 合规状态自检
- [x] 已列明当前上游来源、版本/commit 与许可边界
- [x] 「思想迁移 vs 代码复制」区分
- [x] NOTICE/来源清单结构设计
- [x] 依赖/模型/数据许可检查纳入模块 17
- [x] OpenAI `.system` 全程禁止
- [x] 本 Skill 自身 MIT LICENSE 与 NOTICE 已签发
- [x] Stable Release 分发包含 LICENSE 与 NOTICE
- [ ] 商业签约前律师复核、商标与合同责任边界 → `PENDING_EXTERNAL_VALIDATION`
- [ ] 未来新增实际复制内容时逐文件复核来源声明（持续义务）

# Development History（内部实验编号 → 公开结论对照）

公开 README 只保留影响使用的结论；以下为内部编号的公开摘要（详细实验资产未纳入本仓库，内部留存）。

| 内部编号 | 公开含义 |
| --- | --- |
| Round 1 (v1.1.0 era) | 首个受控复杂项目实验：发现"仅说继续即停"与"本地遥测冒充核心"两类核心缺陷 → v1.2 修复并回归 |
| v1.2 Reliability Hardening | 五不变量（含资源守卫与跨模型交接）+ 核心遥测绑定 |
| v1.3 Coverage Hardening | 合同范围完整性 / 声明运行时适配器 / 角色工作流 E2E 覆盖三门禁（均源自真实失效） |
| Phase B / Phase C | 同口径 With-Skill vs No-Skill 观察性对照：双臂 14/14；Skill 的可测价值=过程可证明性与旅程广度，成本约 2.6×（范围混杂） |
| v1.4 Efficiency | 六效率协议；同口径回放 token -2.6%、时间 -30%（观察性） |
| v1.5 Productization | 中途接入 / 遥测闭环 / 企业定制 / 多 Harness 架构；冻结例外 EXP-018（同键政策覆盖缺陷）经机械证明修复 |

Benchmark 数字与限制：见 README "Reliability efficiency"（ENGINEERING_OBSERVATIONAL_BENCHMARK，禁平均/因果表述）。
Internal validation evidence retained privately（项目实验室与基准工作区不入本仓库）。

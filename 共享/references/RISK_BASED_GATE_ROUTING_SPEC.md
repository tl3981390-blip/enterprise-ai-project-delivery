# RISK_BASED_GATE_ROUTING_SPEC（风险分级门禁路由）

机械核心：`efficiency_core.py::classify_risk/route_gates`（含 GATE_DEPENDENCY_GRAPH 与 ALWAYS_GATES）；回归：EFF-004/005 + 未知面 fail-closed。

1. 先判 Change Surface → 风险级：LOW（文案/非业务 UI 文本/隔离样式/无状态展示层）｜MEDIUM（模块逻辑/API 处理）｜HIGH（Workflow/RAG/RBAC/Persistence/Database/Runtime adapter）｜CRITICAL（Production/不可逆迁移/安全边界/跨环境）。未知 Surface → fail-closed 报错，不猜。
2. LOW：仅相关轻量 Gate（affected_module_tests[+targeted browser]）。禁止无意义跑 PostgreSQL/RAG/RBAC/Migration/Handoff/Full Browser。
3. MEDIUM：affected module tests + contract_check + relevant integration + targeted browser journey。
4. HIGH：按依赖图跑完整相关链（database→persistence→restart→api；workflow→workflow+role_e2e；rag→rag+citation…）。
5. CRITICAL：完整治理链，不路由不减。
6. 无关 Gate 记 `NOT_APPLICABLE`，不要求模型读其全文自证不适用。
7. contract_check 属 ALWAYS（便宜且常相关）。最终验收/Release 不在路由范围（永不降级）。

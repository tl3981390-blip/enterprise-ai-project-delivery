# EVIDENCE_REFERENCE_PROTOCOL（证据引用紧凑化）

机械核心：`efficiency_core.py::EvidenceRegistry`；回归：EFF-006。

1. 一份 Evidence 只存一次正文；此后一律以 `evidence_id + hash + source + result`（REF: EV-xxxx）引用。
2. 禁止同一 Event Log/Stage Report/Handoff/Final Report/Evolution Pack 相互复制全文；需要详情时按需读取（cold read）。
3. 重复注册同 id → 返回 deduplicated=True + 原 hash，不存第二份。
4. 完整性不降级：hash 仍是完整性锚（引用携带 hash，篡改可检）。
5. 路径约定（LL-011 采纳，零治理成本）：遥测 log 与 anchor 同目录；证据引用写绝对路径或自仓根相对路径——消除跨目录审计摩擦（v1.4 轮观察者曾因锚点异目录多花一次全局搜索）。

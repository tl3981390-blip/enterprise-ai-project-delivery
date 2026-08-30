# VERIFIED_STATE_CACHE_SPEC（已验证状态缓存）

机械核心：`efficiency_core.py::VerifiedStateCache`；回归：EFF-002/003。

1. 缓存条目 = gate_id + 精确输入哈希（contract_hash/runtime/evidence_anchor 等）→ PASS|FAIL。只缓存机械验证结论。
2. 严格失效：相关输入任一变化 → 新键 → MISS → 强制重验（`CACHE_INVALIDATED` 语义）。禁止为省 Token 使用 stale verification；无 MAYBE 等模糊缓存值。
3. 计数进效率指标：gate_cache_hit / gate_cache_miss（§42-44 记账）。
4. 不缓存的内容：最终验收、Release Gate、Candidate Integrity——这些层永远实跑（分层验证见 §25-26，本缓存只服务中间层）。

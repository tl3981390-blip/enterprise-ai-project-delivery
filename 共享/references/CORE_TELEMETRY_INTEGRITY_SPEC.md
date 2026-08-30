# CORE_TELEMETRY_INTEGRITY_SPEC（核心遥测完整性规格）

来源：Round 1 FINDING-003 TELEMETRY_INTEGRITY_FAIL——项目自建"差不多"的遥测自测 PASS，但正式核心验证拒绝其日志（事件类型不符、correlation 非法/重复、hash-chain 非法、anchor 非法）。

## 1. 单一真源

所有正式交付遥测只能经核心 Recorder 写入：

```bash
python 共享/scripts/record_delivery_event.py --event <event.json> --log <events.jsonl> --anchor <events.anchor.json>
```

Recorder 负责：schema 校验、event_type/event_id 合法性、correlation 规则与去重、task/stage 身份、SYSTEM_CLOCK/PROVIDER 时间戳、append-only、hash chain、anchor。

## 2. 验收（机械）

最终验收必须执行核心完整性验证，项目内部测试 PASS 不能替代：

```bash
python 共享/scripts/check_telemetry_binding.py --manifest <manifest.json> --core-root <skill root>
python 共享/scripts/calculate_delivery_metrics.py --log <events.jsonl> --anchor <events.anchor.json> --output metrics.json --report report.md
```

`check_telemetry_binding.py` 校验 manifest 中 Recorder/Verifier 的规范 SHA-256 与核心目录实际文件一致（防伪入口），随后验证 hash chain 与 anchor 完整性。

## 3. 禁止

- 项目创建"兼容 Skill Telemetry 的私有版本"冒充正式 Event Log（Round 1 实证：此类日志在核心验证下必然失败）。
- 绕过 Recorder 手写 events.jsonl；伪造 prev_hash/event_hash/anchor。
- Token 无 Provider 证据时输出数值（必须 `NOT_AVAILABLE`，禁止估算与零值冒充）。
- 用历史或跨候选 Evidence 证明新候选。

## 4. 事件与指标合同

事件 schema：`共享/schema/project_reliability_event.schema.json`；指标 schema：`共享/schema/project_delivery_metrics.schema.json`。新增事件/指标走最小必要原则（§50/§51），逐项有负向测试。

## 5. 回归

`TELEMETRY-001/002/003`（correlation 非法 / hash chain 非法 / anchor 非法 → 核心拒绝）与 v1.1 遥测 14 项回归。

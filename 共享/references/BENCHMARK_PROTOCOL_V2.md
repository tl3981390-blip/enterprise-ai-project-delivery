# BENCHMARK_PROTOCOL_V2（基准协议 v2 规格）

来源：Round 1 FINDING-005 BENCHMARK_CONTROLLER_CONTAMINATION——Controller 提示过细把测试意图泄漏给施工 Agent，污染行为实验。结论：测试框架本身也需要治理。

## 1. 分离原则

```text
PRIVATE_BENCHMARK_SPEC   # 主控私有：测试目标、期望事件名（如 USER_SCOPE_CHANGE）、门禁 id、判定规则
PUBLIC_BUSINESS_EVENT    # 施工 Agent 只能看到：正常业务事件叙述
```

禁止向施工 Agent 暴露：正在测试什么、期望什么事件、期望什么判定。业务注入只能以真实业务口吻表达，例如"业务方提出以下真实需求变化……"，禁止"现在测试 USER_SCOPE_CHANGE"。

## 2. 污染检测（机械）

`共享/scripts/check_benchmark_contamination.py`：输入基准 spec 的 `private_markers` 与 Agent 可见文本；任一私有标记出现在可见文本 → `CONTROLLER_CONTAMINATED`。

```bash
python 共享/scripts/check_benchmark_contamination.py --benchmark spec.json --text agent_visible.txt
```

## 3. 污染结果的用途限制

标记为 `CONTROLLER_CONTAMINATED` 的基准结果：

- ✅ 只能用于工程验证（链路是否可运行）
- ❌ 不得用于行为效果证明（Skill 是否改变了 Agent 行为）

## 4. 与运行时 Skill 的边界

基准卫生是测试框架协议，不是核心 Skill 的运行时门禁（CANDIDATE_REVIEW 对 FINDING-005 的处置为 REJECT_FROM_CORE）；本协议约束的是基准 Controller 与用例设计者。

## 5. 回归

`BENCH-001`：Controller 暴露完整测试目的 → 检测器必须输出 `CONTROLLER_CONTAMINATED`（负向测试）。

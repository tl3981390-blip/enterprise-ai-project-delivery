---
name: enterprise-ai-project-delivery.19-handover
description: 模块19·最终交付与经验沉淀。最终报告+经验入库。Use when 交付完成需收尾。
version: 1.7.0
license: MIT
compatibility: open
metadata:
  skill_id: enterprise-ai-project-delivery
  module: 19_最终交付与经验沉淀
  language: zh-CN
  gate: 需 COMPLETED 前置证据齐备
---

# 19 最终交付与经验沉淀

最终交付必须运行确定性指标脚本并生成《AI 项目可靠性与交付效率报告》。报告数字只能来自验证通过的事件日志与 metrics.json；Token 无真实 Provider/Harness 用量时必须显示 NOT_AVAILABLE，禁止估算或写 0。

## Overview
生成最终交付包与经验沉淀，目标完成须有真实证据，并与任务理解合同核对。

## When to Use
所有阶段通过后收尾。

## Core Process
1. 汇总各阶段输出与证据（`references/Release检查清单.md`）。
2. 逐项核对是否满足合同 success / acceptance 标准。
3. 沉淀经验入库（lessons）；可泛化经验按 [`SKILL_EVOLUTION_ENGINE_SPEC`](../共享/references/SKILL_EVOLUTION_ENGINE_SPEC.md) 走 Experience → Learning → Bounded Patch → Negative/Held-out/Regression 流水线（仅 AUTO_PROPOSE，正式发版仍走 Release Gate）。
4. 缺证据 / 目飘标移 → 禁止宣称完成。
5. 报告必须包含 `unnecessary_human_wait_count`；非零时需列出每个 `ILLEGAL_PASSIVE_STOP` 和修复/处置，不能把它藏在模型总结中。

## 反合理化 / Red Flags
- 未证明目标完成就说"做完" → 假交付
- 少证据仍发布 → 违规
- 教训不沉淀 → 价值流失

## Verification
- 合同成功/验收标准逐项有真实证据；最终交付包完整；达到 COMPLETED

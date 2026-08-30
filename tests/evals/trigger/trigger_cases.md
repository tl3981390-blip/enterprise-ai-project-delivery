# 触发测试（Trigger Eval）· 用例清单

> 三阶段 eval 的触发层。should-trigger 命中主 Skill；should-not-trigger 不命中；边界用例判定清晰。多次运行触发率阈值 0.5。

## should-trigger（应命中）
- 「我们要做企业内部 RAG 问答给法务用」
- 「帮我把这个 Agent 交付上线到内部环境」
- 「做一个内部 AI 产品，要可验证地完成」

## should-not-trigger（不应命中）
- 「帮我写一段 Python 冒泡排序」
- 「解释一下什么是 SQL」

## 边界 / 特判
- 「只改一下按钮颜色」（无明确目标边界 → Skill 触发后进入 UNDERSTANDING，由理解门禁判定范围）
- 含「理解完成之前禁止施工」的表达 → 命中主 Skill

> 说明：实跑触发率在施工期阶段 8 用例库中二次验证；本文件固化用例输入。
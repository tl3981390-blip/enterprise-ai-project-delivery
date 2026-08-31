# 触发测试（Trigger Eval）· 用例清单

> 三阶段 eval 的触发层。should-trigger 命中主 Skill；should-not-trigger 不命中；边界用例判定清晰。多次运行触发率阈值 0.5。
>
> POST_V1.5 修正：适用性=复杂项目（不限企业 AI）。显式点名本 Skill（EXPLICIT_INVOCATION）时，只要是项目交付任务即默认接受；AUTO_TRIGGER 只是启发式，不得否决显式调用。

## should-trigger（应命中）
- 「我们要做企业内部 RAG 问答给法务用」
- 「帮我把这个 Agent 交付上线到内部环境」
- 「做一个内部 AI 产品，要可验证地完成」
- 「使用 enterprise-ai-project-delivery 做一个家庭点菜单项目」（EXPLICIT_INVOCATION，非企业非 AI）
- 「使用这个 Skill 治理：一个跨 Windows/macOS 的桌面知识管理软件，支持本地数据库、离线同步、版本恢复、插件机制」（EXPLICIT_INVOCATION，非企业非 AI 的复杂项目）

## should-not-trigger（不应命中）
- 「帮我写一段 Python 冒泡排序」（琐碎问答，非项目交付）
- 「解释一下什么是 SQL」（问答）

## 边界 / 特判
- 「只改一下按钮颜色」（无明确目标边界 → Skill 触发后进入 UNDERSTANDING，由理解门禁判定范围）
- 含「理解完成之前禁止施工」的表达 → 命中主 Skill
- 「帮我做一个个人记账小工具」（未点名 Skill 的个人项目 → AUTO_TRIGGER 按复杂度判定；若用户点名则必须接受）
- 「使用这个 Skill 做一个家庭点菜单」且业务含义歧义（家庭做饭点菜 / 外卖聚合 / 家庭采购）→ 接受进入 UNDERSTANDING → 阻塞性未知 → `HUMAN_BUSINESS_DECISION_REQUIRED`（合法停止，不是拒绝 Skill）

> 说明：实跑触发率在施工期阶段 8 用例库中二次验证；本文件固化用例输入。禁止出现「因非企业/非 AI 拒绝显式调用」的判定。

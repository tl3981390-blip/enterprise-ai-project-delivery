<!-- Source: github/spec-kit@51e52be6c3b26fed3ff5424c671f4a559519a759 and unboundinnov/specdd@a75bd6aa457123cab22d6ce7edd220faafbc043c; License: MIT; Adaptation: Chinese enterprise workflow, no runtime code copied. -->
# SDD 流程与规格模板

依次执行 Specify → Clarify → Plan → Tasks → Analyze → Implement → Converge。Clarify 只问影响目标、边界、权限或验收的最少问题；能从证据安全推断的内容标为假设。Analyze 必须检查合同、规格、计划、任务之间的遗漏、冲突和不可验证项；Converge 只在关键 gap 为零、证据齐全时通过。

规格至少包含：目标与用户；范围与非目标；MoSCoW 需求；EARS/Given-When-Then 验收标准；数据与权限；错误、空数据、重复操作与恢复；性能、安全、部署与回滚；未知项；sign-off。需求状态只允许 proposed、clarified、approved、implemented、verified；状态变化必须有证据。

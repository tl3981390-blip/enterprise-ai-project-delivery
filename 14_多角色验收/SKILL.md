---
name: enterprise-ai-project-delivery.14-multi-role-acceptance
description: 模块14·多角色验收。需求/工程/安全/用户四视角独立验收。Use when 交付需多角色验收通过。
version: 1.0.0
license: MIT
compatibility: open
metadata:
  skill_id: enterprise-ai-project-delivery
  module: 14_多角色验收
  language: zh-CN
  gate: 需施工后、四角色独立证据
---

# 14 多角色验收（四视角）

## Overview
从需求方/工程方/安全治理方/真实用户四视角独立验收，禁止自己开发+自己宣布通过。

## When to Use
交付物完成后，需四角色验收。

## Core Process
1. 需求方：是否解决真实业务问题。
2. 工程方：架构/代码/依赖/数据/接口/错误处理。
3. 安全治理方：权限/泄露/日志/密钥/越权/外部工具。
4. 真实用户：能否真完成工作。
5. 每角色独立证据（`references/四角色验收模板.md`），缺签不能进下阶段。

## 反合理化 / Red Flags
- 同一 Model 结论互相背书 → 无效
- 缺某角色签核仍前进 → 违规
- 把个人总结当多方证据 → 假验收

## Verification
- 四角色均独立 PASS + 独立证据；缺签 blocked
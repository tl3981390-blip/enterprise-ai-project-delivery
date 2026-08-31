---
name: enterprise-ai-project-delivery.14-multi-perspective-acceptance
description: 模块14·多视角独立验收。恒活生命周期模块：以「独立验证」为不变量，验收视角随真实干系人缩放（企业默认需求/工程/安全/用户四视角；单人项目坍缩为 owner/user 视角）。Use when 交付物完成、进入最终验收。
version: 1.7.0
license: MIT
compatibility: open
metadata:
  skill_id: enterprise-ai-project-delivery
  module: 14_多角色验收
  language: zh-CN
  gate: 需施工后、各必需视角独立证据
---

# 14 验收（多视角独立验收）

## Overview
最终验收的不变量是**独立验证**：每个必需视角需独立 PASS + 独立证据，禁止「自己开发 + 自己宣布通过」。视角集合不是固定四角色法律，而是随项目真实干系人缩放：

- 企业项目（Enterprise Profile 声明 roles）：默认四视角 = 需求方 / 工程方 / 安全治理方 / 真实用户。
- 单人/个人项目（干系人坍缩）：owner_user 视角（+ 交付物成功标准的真实 Evidence）；工程自检可作为证据之一但不能替代验收判定。
- 其他干系人结构：以 `acceptance_perspectives` 声明，机械校验（`共享/scripts/check_acceptance.py::required_perspectives`）。

## When to Use
交付物完成后，进入最终验收（恒活；视角按上述规则确定）。

## Core Process
1. 确定必需视角集合（`required_acceptance_perspectives`：声明 > 企业默认 > 干系人坍缩）。
2. 逐视角验收：需求/owner 视角是否解决真实问题；工程视角架构/代码/依赖/接口/错误处理；安全治理视角仅在项目涉及相应风险面时必答（个人项目无边界面则记 N/A 及理由）；用户视角能否真完成工作。
3. 每视角独立证据（`references/四角色签核模板.md` 作为企业四视角实例模板），缺签不能进下阶段。

## 反合理化 / Red Flags
- 同一 Model 结论互相背书 → 无效
- 缺某必需视角签核仍前进 → 违规
- 把个人总结当多方证据 → 假验收
- 以「项目是个人的」为由跳过独立验收证据 → 违反 INDEPENDENT_VERIFICATION 不变量

## Verification
- 全部必需视角独立 PASS + 独立证据；缺签 blocked；`check_acceptance.py` 机械执行

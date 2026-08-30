---
name: enterprise-ai-project-delivery.13-browser-acceptance
description: 模块13·浏览器真实验收。真实浏览器操作验证 Web 产品（console/network/交互）。Use when 交付含 Web UI 需真实验收。
version: 1.1.0
license: MIT
compatibility: open
metadata:
  skill_id: enterprise-ai-project-delivery
  module: 13_浏览器真实验收
  language: zh-CN
  gate: 需施工产物可运行后
---

# 13 浏览器真实验收

## Overview
对 Web 产物做真实浏览器操作验收，仅打开不够，须检查 console/网络/交互。

## When to Use
交付物含 Web UI，进入验收阶段。

## Core Process
1. 真实打开页面，操作关键交互。
2. 检查 console 0 错误、网络异常、交互通过。
3. 产出 browser_capture 证据（截图/console/network）。
4. 单测/接口证据不能替代浏览器交互证据。

## 反合理化 / Red Flags
- "页面能打开"当验收 → 不足
- 未真实点击交互 → 假验收
- 截图无 console/网络佐证 → 证据不足

## Verification
- 真实操作 + console0 + 交互通过；有 browser_capture 证据

# 可信交付现场演示清单

本演示的目标不是让模型现场“表现得很聪明”，而是展示：失败时系统不允许正式完成，授权修复和重新验证后才放行。

## 演示前一天

```powershell
python -m pytest -q
python demo/run_trusted_delivery_demo.py --run-dir C:\temp\trusted-delivery-demo
```

两个命令必须全部成功；第二个命令输出中必须同时包含：

```text
FAILED_ARTIFACT_BLOCKED_COMPLETION = true
OWNER_AUTHORIZED_RECOVERY_REVALIDATED = RECOVERED_REVALIDATED
FINAL_COMPLETION_ALLOWED = true
DEMO_STATUS = PASS
```

## 现场讲法（两分钟）

1. “AI 可以执行，但它不能单方面决定企业结果已经完成。”
2. 运行演示。第一个文件通过、第二个文件故意不合格；系统记录失败并拒绝完成。
3. “此时即使模型说完成，系统也不会放行。”
4. 展示模拟的可信 Owner 授权、修复文件、重新验证。
5. 展示最终只有在所有验收项通过后才出现 `FINAL_COMPLETION_ALLOWED = true`。

## 现场风险控制

- 主演示完全本地、确定性运行；不依赖网络、远端模型额度或临场模型表现。
- 真实 Codex 对话演示只能作为加分项；必须先完成一次同机彩排。
- `demo_result.json` 和 `delivery-session.json` 是现场可打开的审计证据。
- 该演示中的 Owner 授权是受控 Harness 模拟。接入企业生产环境时，必须由企业 Harness 绑定真实 Owner 身份；不能把演示标识当作生产授权。

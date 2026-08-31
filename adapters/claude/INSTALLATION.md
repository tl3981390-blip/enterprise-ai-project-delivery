# Claude Code 安装映射
技能目录：`~/.claude/skills/enterprise-ai-project-delivery/`（SKILL.md+ADAPTER_MANIFEST，指向 canonical core）。
调用：`claude -p "<任务，要求使用 enterprise-ai-project-delivery>"`（需有效模型端点；本机实测 401 invalid key → L2 BLOCKED_RUNTIME_AUTH，见矩阵）。
修复路径：更新 settings.json 的 ANTHROPIC_AUTH_TOKEN/BASE_URL 后重跑 conformance。

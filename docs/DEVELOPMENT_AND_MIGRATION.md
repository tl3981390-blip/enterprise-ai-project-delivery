# Development & Migration Guide

## 只维护本公开 Skill

GitHub 是公开 Skill 版本与历史的中央真源。新电脑 clone 仓库、获取 tags、验证 origin 后从开发分支继续：

```bash
git clone https://github.com/tl3981390-blip/enterprise-ai-project-delivery.git
cd enterprise-ai-project-delivery
git fetch --tags
git remote get-url origin
git tag --sort=-version:refname
git switch -c <work>-dev
```

不要在文档中长期写死“当前版本”；以 GitHub Latest Stable 和 `共享/schema/RELEASE_METADATA.json` 为准。历史 tag 和 Release 资产不可移动、重建或覆盖。

## 继续开发整个企业 Skill 实验室

单独 clone 本仓库不等于恢复整个实验室。完整 Workspace 还包括多个上游 Git 仓、非 Git 文档、证据、Harness 接入、历史区以及未提交/未跟踪内容。

正确迁移方式：

```text
旧电脑 Honey
→ 读取私有 Bootstrap 的 OLD_COMPUTER_MIGRATION_INSTRUCTION.md
→ 预检、生成 Workspace Bundle、逐文件校验
→ 用户只携带 ZIP + 同名 .sha256
→ 新电脑 Honey 读取 NEW_MACHINE_RESTORE_INSTRUCTION.md
→ 校验、恢复、重建依赖、运行验收
```

完整 Workspace Bundle 属于私有资产，不进入本公开 Skill Release。`.venv`、`node_modules`、缓存、凭据、Harness 用户目录和 Docker 运行态不直接迁移；数据库唯一数据按具体数据库单独备份。

## 身份规则

- Git commit hash 跨电脑保持不变；只有新提交才产生新 hash。
- Git tag 标识历史源码身份；Release 资产 SHA-256 标识已发布 ZIP，二者不是一回事。
- 重新压缩同样文件通常会得到不同 ZIP SHA-256，因此正式安装只验证原始 GitHub Release 资产。
- AI/Honey 可以代为运行 clone、验证和恢复，但不能绕过 GitHub、文件系统或企业权限边界。

## Release 之后

main 可以包含正式 tag 之后的文档、测试、适配器或候选改动；这不改变历史 Release。涉及 Core 的新行为必须满足真实失效、可泛化、可复现、有证据，并重新经过 Candidate 验收与新版本发布。

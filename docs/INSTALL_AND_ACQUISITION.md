# Installation & Acquisition Guide

> v3 Stable 路径分离：普通用户 = Stable Release Asset；可选策略 = Harness 自己同步（没有也能用）；发布者开发空间 = Workspace Bundle。三者不得互相冒充或成为彼此依赖。

正式使用、维护公开源码和迁移作者完整实验室是三条不同路径。

## 使用正式 Skill（推荐）

把仓库 URL 交给支持 Agent/Skill 安装的 Harness：

```text
请从 https://github.com/tl3981390-blip/enterprise-ai-project-delivery 安装
enterprise-ai-project-delivery 的最新 Stable Release，并遵循 docs/AGENT_INSTALL.md。
下载正式 Release 资产，不使用 Code → Download ZIP 或 main 快照；验证资产身份，
安装自包含副本并运行自检。若当前 Harness 不支持 Skill、没有网络/文件权限或需要授权，
请报告真实限制，不得假装安装成功。
```

上面的“最新 Stable Release”只适用于个人使用或探索。企业试用、测试、预生产和生产必须在指令中提供批准的精确 tag，验证该 tag 的 Release asset SHA-256，且禁止自动升级或回退到 Latest Stable。见 [企业版本治理](ENTERPRISE_VERSION_GOVERNANCE.md)。仓库当前为公开仓库；GitHub 或 Harness 的限流、网络或组织策略仍可能要求合法认证。不要把密码、PAT、2FA、OAuth secret 或私钥发送给模型。

正式 Release ZIP 与绿色 **Code → Download ZIP** 不同：前者具有发布身份与 GitHub 资产 SHA-256，后者只是分支快照，不能用于正式身份验收。

## 维护公开 Skill 源码

```bash
git clone https://github.com/tl3981390-blip/enterprise-ai-project-delivery.git
cd enterprise-ai-project-delivery
git fetch --tags
git remote get-url origin
git tag --sort=-version:refname
git switch -c <your-development-branch>
```

开发者应从分支施工；历史正式 tag 永不移动。不要用 Release ZIP 代替带历史的开发 clone。

## 迁移完整企业 Skill 实验室

本公开仓库不包含作者的上游研究仓、未提交工作、私有 Bootstrap、内部证据和整个 Workspace。要在另一台电脑继续开发完整实验室，使用私有 `enterprise-skill-lab-bootstrap` 的 `OLD_COMPUTER_MIGRATION_INSTRUCTION.md` 和 `NEW_MACHINE_RESTORE_INSTRUCTION.md`，由两端 Honey 生成、验证并恢复 Workspace Bundle。

完整 Workspace Bundle 绝不能上传到本公开仓库或公开 Release。

## Harness 边界

URL-only 是统一用户入口，不是对所有 Harness 的兼容承诺。Harness 必须能够加载 Skill、访问 GitHub 并写入其 Skill 目录。真实支持状态见 [HARNESS_GUIDE.md](HARNESS_GUIDE.md)；未知 Harness 第一次安装后必须执行自检和真实小项目验证。

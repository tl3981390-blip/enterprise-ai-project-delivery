# 企业版本治理

> v3 Stable：Runtime Adaptive Strategy 不属于版本治理，不得产生代码或 Release；Publisher Core Maintenance 才进入 SemVer、独立验证、人类批准和回滚治理。正式安装只认不可移动 Stable Tag 对应的 Release Asset 与 SHA。

`v3.0.0` 保持不可移动的失败历史，禁止批准使用。企业环境只安装明确批准、完成发布后回下载与 installed exact identity 验证的版本；不得把 prerelease、FAILED POST-RELEASE VALIDATION 或 main 当作 Stable。

当前公开 Valid Stable 是 `v3.0.8`。企业 Harness 必须显式批准该 exact tag，从 GitHub Release digest 核验 Asset SHA-256，并从 `INSTALL_INFO.json` 核验 exact `tag v3.0.8 -> commit <40-char-sha>`；不得从 Latest 静默升级。`v3.0.5` 已被替代；`v3.0.0`–`v3.0.4` 是失败历史或被拒候选，不得批准使用。

Skill 的版本选择是交付控制的一部分，不是一个隐藏的安装细节。历史 tag 和已发布资产不可移动、不可覆盖、不可删除。

## 两条安装路径

| 使用场景 | 版本选择 | 自动升级 |
| --- | --- | --- |
| 个人使用、探索或非受控演示 | 可以解析最新 Stable Release | 仅在用户再次明确要求安装/升级时 |
| 企业试用、测试、预生产、生产 | 必须使用企业批准的精确 tag，并验证该 Release asset 的 SHA-256 | 禁止 |

“最新正式版”只是一种方便的默认选择，**不是企业环境的更新策略**。一次安装完成后，已安装版本保持不变；新版本要经过企业自己的候选验证、批准和变更窗口，才可以升级。

## 给 Harness / Honey 的企业安装指令

将下列 `<approved-tag>` 替换为公司批准的版本：

```text
从 https://github.com/tl3981390-blip/enterprise-ai-project-delivery 安装
enterprise-ai-project-delivery 的正式版本 <approved-tag>。
这是企业受控环境：不得解析 Latest Stable、不得回退到其他 tag、不得自动升级。
只下载该 tag 对应的 GitHub Release asset；先核对 tag、Release asset SHA-256
与资产元数据，再安装自包含副本并运行 docs/AGENT_INSTALL.md 规定的自检。
最后报告 skill id、版本、tag、commit/asset SHA-256、安装路径和自检结果。
如当前已安装其他版本，保留它并等待明确的升级授权。
```

Harness 不能访问 GitHub、不能写入 Skill 目录、不能读取已安装身份，或无法完成校验时，必须报告限制；不得安装 main 快照、作者电脑目录或未验证副本来冒充成功。

## 受控升级流程

```text
批准的当前版本
  → 指定候选 tag 安装到测试环境
  → 身份校验 + 自检 + 本企业验收
  → 人类/变更流程批准
  → 在变更窗口升级生产环境
  → 记录新旧版本与验收证据
```

升级前应保留当前安装目录或可重装的当前 tag；回退时安装先前批准的精确 tag，而不是“回到最新”。本 Skill 的 `INSTALL_INFO.json` 和 `共享/schema/RELEASE_METADATA.json` 是安装身份证据；企业仍应把它们纳入自身 CMDB、变更单或审计系统。

## 开发 Workspace 与正式运行环境

开发者迁移整个 Workspace 时，可以迁移 Git 仓库、私有 Bootstrap、工具配置和恢复包；这不等于把开发目录当作企业正式 Skill 来源。正式环境始终从批准 tag 的 GitHub Release asset 安装。详见 [开发与迁移](DEVELOPMENT_AND_MIGRATION.md)。

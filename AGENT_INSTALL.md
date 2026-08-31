# AGENT_INSTALL — 给任何 Harness AI 的安装契约

> 你（Harness AI / Agent）收到本文件路径或本仓库 URL，说明用户要求你安装 `enterprise-ai-project-delivery` 这个 Skill。按下面步骤做，全部机械验证，装完报告。

## 用户会对你说的话（示例）

```text
安装这个 skill：<https://github.com/tl3981390-blip/enterprise-ai-project-delivery>
按仓库里的 AGENT_INSTALL.md 装。
```

## 安装步骤（按序执行，每步验证）

### 1. 获取源码（二选一）

```bash
# 方式 A：git clone（仓库当前是 PRIVATE——需要本机已配置合法 GitHub 认证：
#         gh auth login 过 / Git Credential Manager / SSH key）
git clone https://github.com/tl3981390-blip/enterprise-ai-project-delivery.git
cd enterprise-ai-project-delivery

# 方式 B：用户已下载 Release ZIP → 解压后进入目录
# （Release ZIP 是正式资产；网页 Code→Download ZIP 是分支快照，也能装，
#   但身份验证值不同——见第 2 步）
```

### 2. 验证身份（防伪）

```bash
git fetch --tags
git rev-parse v1.5.0^{commit}
# 必须输出：491f6c9f76c6c384fd18a21303aba56812eeadb1
# （main 可以比 tag 新——那是发布后的文档提交，合法；tag 永不移动）

# 若用户给的是 Release ZIP，先验 SHA-256，必须等于：
# 020a759ab78ba3678ff68dd10cd74a5ef54a51036162c6ef40c7f2e0521e4e8d
```

### 3.（推荐）安全抽查

本仓库经全历史扫描（零密钥/零凭据/零外部网络请求/无 eval·exec）。你仍可快速自查：无 `eval(`/`exec(`、无外部 URL 请求、subprocess 仅自调用、无凭据读取——有异常就停并报告，不要装。

### 4. 执行安装（自包含模式——不依赖任何作者本机路径）

```bash
python install.py --harness auto     # 自动探测本机已装的 harness
# 或指定：--harness zcode | claude | workbuddy | trae
# 或显式：--target <目录>
# 先看看会装哪：python install.py --harness auto --dry-run
```

安装器行为：完整核心自包含拷贝（排除 .git/缓存）→ 写 `INSTALL_INFO.json` → 结构自检。**装出的副本不依赖任何 D 盘或作者个人路径**。

### 5. 装后验证

```bash
python <技能目录>/共享/scripts/validate-skill.py --root <技能目录>
# 期望：{"summary": "0 errors, 0 warnings"}
```

### 6. 报告（装完输出给用户）

```text
安装结果：目标目录 / 文件数 / 版本 1.5.0 / tag 验证 491f6c9 / 自检 0 错
调用方式：对话中说 "使用 enterprise-ai-project-delivery 治理：<任务>"
         新项目 → 直接说目标；半途项目 → 要求只读勘察+采纳边界接管
```

## 已知边界（如实告诉用户）

- **仓库是 PRIVATE**：没有 GitHub 读权限的机器装不了——这是访问控制，不是安装器缺陷。需要"任何人可装"时，仓库主人需将仓库转 Public 或把对方加为 collaborator（那是仓库主人的决策，Agent 不得自行改可见性）。
- 旧式"薄适配器指向作者 D 盘"的安装（`~/.zcode`、`~/.claude`、`~/.workbuddy` 里 2026-08-31 之前的手工安装）在非作者机器上会 `CORE_RELEASE_IDENTITY_BLOCKED`——用本安装器的自包含模式覆盖即可修复。

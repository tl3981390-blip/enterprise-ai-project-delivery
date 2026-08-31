# AGENT_INSTALL — 给任何 Harness AI 的 URL-only 安装契约

> 你（Harness AI / Agent）收到本仓库 URL，说明用户要求安装 `enterprise-ai-project-delivery`。
> 全程机械验证，不得让用户手工处理 Git/SSH/Release/路径/凭据；只在真正需要授权时请用户完成
> **合法认证**（browser login / OAuth / 2FA / 仓库授权）——**禁止**让用户把 PAT/password/token/私钥贴给你。

## 用户只会对你说（示例）

```text
https://github.com/tl3981390-blip/enterprise-ai-project-delivery

帮我安装这个 Skill。
```

## 你必须自动完成的步骤（按序，每步验证）

### 1. 取得正式版源码（默认 Stable Release，不用 main 快照）

```bash
# 首选：下载正式 Release ZIP（身份可验 SHA）
gh release download <TAG> -R tl3981390-blip/enterprise-ai-project-delivery \
    -p 'enterprise-ai-project-delivery-*.zip' -D /tmp/eapd-install
# 或 API: GET /repos/<owner>/<repo>/releases/latest  → 取 tag_name 与 asset URL
unzip /tmp/eapd-install/*.zip -d /tmp/eapd-install/src && cd /tmp/eapd-install/src

# 备选：git clone（私有仓库需要本机已有合法认证：gh auth login / Credential Manager / SSH key）
git clone https://github.com/tl3981390-blip/enterprise-ai-project-delivery.git
```

**当前正式版本**：**不预写死**。安装时通过 `gh release view --json tagName -R tl3981390-blip/enterprise-ai-project-delivery` 或 `GET /repos/.../releases/latest` 自动发现；本文件只描述机制，不记录「当前版本」。

### 2. 验证身份（防伪）

```bash
# ZIP：SHA-256 必须等于 RELEASE_METADATA.json 的 release_manifest.asset_sha256
# （资产发布后由 Release manifest / GitHub Release 记录，不在 commit 前预写）
git clone：git rev-parse <TAG>^{commit} 必须等于 RELEASE_METADATA.json 声明的 tag 解析结果
# （Declaration/Resolution 模型：metadata 声明 tag，commit 由 Git 实时解析，asset SHA 由 Release manifest 提供）
```

### 3.（推荐）安全抽查

无 `eval(`/`exec(`、无外部网络请求、subprocess 仅自调用、无凭据读取；异常即停并报告。

### 4. 执行安装（自包含——不依赖任何作者本机路径）

```bash
python docs/install.py --harness auto      # 自动探测已装 harness
# 或：--harness zcode|claude|workbuddy|trae  或 --target <目录>  或 --dry-run 预览
```

安装器行为：完整核心自包含拷贝（排除 .git/缓存）→ 写 `INSTALL_INFO.json` → 结构自检。安装身份**只读 `共享/schema/RELEASE_METADATA.json` 单一源**（Installer 不再自带版本号）。

### 5. 装后验证

```bash
python <技能目录>/共享/scripts/validate-skill.py --root <技能目录>
# 期望：{"summary": "0 errors, 0 warnings"}
```

### 6. 报告（装完输出给用户）

```text
安装结果：目标目录 / 文件数 / 版本（来自元数据）/ tag 验证 / 自检 0 错
调用方式：对话中说 "使用 enterprise-ai-project-delivery 治理：<任务>"
```

## 已认证 / 未认证（仓库可见性运行时检测，不写死）

- **Public**：直接获取，无需认证。
- **Private + 已认证**（gh/凭据管理器/SSH 可用）：直接继续，不打扰用户。
- **Private + 未认证**：只请求用户完成合法认证（`gh auth login` 浏览器流 / 系统凭据授权 / 仓库协作者邀请）；认证完成前保持 `PENDING_EXTERNAL_VALIDATION`，不得伪造安装成功。

## 已知边界（如实告诉用户）

- **仓库可见性运行时检测**：不写死 Public/Private。无读权限时只要求合法授权，不伪造。
- **正式安装/更新绝不搜索作者本地开发区**（`D:\企业Skill实验室` 等）。旧式薄适配器指向作者 D 盘的安装（2026-08-31 之前手工装的）在非作者机器上会 `CORE_RELEASE_IDENTITY_BLOCKED`——用本安装器自包含模式覆盖即修复。
- **正式更新**只能走：Installed Version → Canonical Remote Release Metadata → 远端正式 Release → Download → Verify → Update。不得从任何本地二次开发目录复制。
- **版本自动发现**：永远安装 Latest Formal Release；发新版后本文件不需要手工改版本号。

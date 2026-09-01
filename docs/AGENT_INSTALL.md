# AGENT_INSTALL — 给任何 Harness AI 的 URL-only 安装契约

> v3 Stable：只获取 GitHub Stable Release Asset，校验 SHA 后安装到 Harness 的 Skill 目录。不得要求作者开发空间、`.git`、缓存、bootstrap 或自适应状态。安装后必须在原开发目录不可用的独立目录运行 validator 与全量回归；adaptive strategy 缺失时使用默认值。
> 验收顺序是硬合同：先运行 `docs/validate_installed_copy.py`；额外定向 pytest 必须设置 `PYTHONDONTWRITEBYTECODE=1` 并禁用 pytest cache provider。不得先用普通 pytest 污染被验资产。

> 你（Harness AI / Agent）收到本仓库 URL，说明用户要求安装 `enterprise-ai-project-delivery`。
> 全程机械验证，不得让用户手工处理 Git/SSH/Release/路径/凭据；只在真正需要授权时请用户完成
> **合法认证**（browser login / OAuth / 2FA / 仓库授权）——**禁止**让用户把 PAT/password/token/私钥贴给你。

## 用户只会对你说（示例）

```text
https://github.com/tl3981390-blip/enterprise-ai-project-delivery

帮我安装这个 Skill。
```

## 你必须自动完成的步骤（按序，每步验证）

### 1. 先确认安装模式，再取得正式版源码（不用 main 快照）

先从用户指令判断模式：

- **个人/探索模式**：用户没有指定版本时，才可解析 GitHub Latest Stable Release。
- **企业受控模式**：用户、企业变更单或环境策略指定了 tag 时，必须只使用该精确 tag；不得解析 Latest Stable、不得回退到其他版本、不得自动升级。若 tag 缺失或不合法，停止并要求人类提供批准版本。

```bash
# 个人/探索模式：先解析 Latest Stable 的 tag
gh release view -R tl3981390-blip/enterprise-ai-project-delivery --json tagName

# 企业受控模式：<APPROVED_TAG> 由人类/企业明确提供；不要替换为“最新”
gh release view <APPROVED_TAG> -R tl3981390-blip/enterprise-ai-project-delivery --json tagName,assets

# 两种模式均只下载已选定 tag 对应的正式 Release ZIP（身份可验 SHA）
gh release download <TAG> -R tl3981390-blip/enterprise-ai-project-delivery \
    -p 'enterprise-ai-project-delivery-*.zip' -D /tmp/eapd-install
unzip /tmp/eapd-install/*.zip -d /tmp/eapd-install/src && cd /tmp/eapd-install/src

# 备选：git clone（私有仓库需要本机已有合法认证：gh auth login / Credential Manager / SSH key）
git clone https://github.com/tl3981390-blip/enterprise-ai-project-delivery.git
```

个人/探索模式可通过 `gh release view --json tagName -R tl3981390-blip/enterprise-ai-project-delivery` 或 `GET /repos/.../releases/latest` 自动发现版本。企业受控模式只查询并下载 `<APPROVED_TAG>`。本文件不把“当前版本”写死，但企业安装记录必须写明实际 tag。

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
安装结果：目标目录 / 文件数 / skill id / 版本（来自元数据）/ 精确 tag / Release asset SHA-256 / 自检结果
调用方式：对话中说 "使用 enterprise-ai-project-delivery 治理：<任务>"
```

## 已认证 / 未认证（仓库可见性运行时检测，不写死）

- **Public**：直接获取，无需认证。
- **Private + 已认证**（gh/凭据管理器/SSH 可用）：直接继续，不打扰用户。
- **Private + 未认证**：只请求用户完成合法认证（`gh auth login` 浏览器流 / 系统凭据授权 / 仓库协作者邀请）；认证完成前保持 `PENDING_EXTERNAL_VALIDATION`，不得伪造安装成功。

## 已知边界（如实告诉用户）

- **仓库可见性运行时检测**：不写死 Public/Private。无读权限时只要求合法授权，不伪造。
- **正式安装/更新绝不搜索作者本地开发区**（例如任意维护者工作区）。旧式薄适配器指向作者机器的安装在其他电脑上会 `CORE_RELEASE_IDENTITY_BLOCKED`——用本安装器自包含模式覆盖即修复。
- **正式更新**只能走：Installed Version → Canonical Remote Release Metadata → 远端正式 Release → Download → Verify → Update。不得从任何本地二次开发目录复制。
- **版本选择与更新**：个人/探索安装可在用户明确要求时解析 Latest Formal Release；企业试用、测试、预生产和生产必须固定人类批准的精确 tag，验证 asset SHA-256，且不得自动更新。企业升级流程是“候选环境验证 → 人类批准 → 生产变更窗口 → 重新自检与记录”，不是“发现新版本就覆盖”。完整规则见 [企业版本治理](ENTERPRISE_VERSION_GOVERNANCE.md)。

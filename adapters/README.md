# Thin Harness Adapters（薄适配层——Core 冻结，平台细节只进此处）

结构：`adapters/<platform>/{INSTALLATION.md, INVOCATION.md, LIFECYCLE.md, PERMISSIONS.md, CAPABILITIES.json}`。每包只含映射与能力声明，**零 Core 复制**。Core 唯一源是正式 Release；当前版本始终从 `共享/schema/RELEASE_METADATA.json` 与 GitHub Latest Stable 动态解析，不在适配器文档写死。

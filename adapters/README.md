# Thin Harness Adapters（薄适配层——Core 冻结，平台细节只进此处）

结构：`adapters/<platform>/{INSTALLATION.md, INVOCATION.md, LIFECYCLE.md, PERMISSIONS.md, CAPABILITIES.json}`。每包只含映射与能力声明，**零 Core 复制**。Core 唯一源是正式 Release；个人安装可从 `共享/schema/RELEASE_METADATA.json` 与 GitHub Latest Stable 解析版本，企业受控安装必须使用批准的精确 tag，不在适配器文档写死。

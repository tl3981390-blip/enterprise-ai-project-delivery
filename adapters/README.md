# Thin Harness Adapters（薄适配层——Core 冻结，平台细节只进此处）

结构：`adapters/<platform>/{INSTALLATION.md, INVOCATION.md, LIFECYCLE.md, PERMISSIONS.md, CAPABILITIES.json}`。每包只含映射与能力声明，**零 Core 复制**（Core 唯一源=canonical repo，当前 tag v1.4.0 / 开发线 v1.5.0-dev）。

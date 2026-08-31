# Release 检查清单

确认全部 ACTIVE 模块通过（未激活能力模块已记 `NOT_APPLICABLE` 及理由，不要求执行）、正向/负向/回归、至少一个真实域内哑案例（域=本次交付项目所在领域，不强制企业 AI）、Evidence 清单与哈希、全部必需验收视角、License/NOTICE（能力激活时）、版本一致性、隔离回滚、Harness 未改、生产未触碰、无 P0/P1、Git 提交/标签/工作树干净。任何一项失败则版本回退开发态并 BLOCKED。

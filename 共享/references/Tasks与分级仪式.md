<!-- Source: unboundinnov/specdd@a75bd6aa457123cab22d6ce7edd220faafbc043c and mariano-aguero/spec-driven-development-skill@939b1e74a8b27f963153df5f420170571d0e28e6; License: MIT; Adaptation: enterprise evidence and permission gates added. -->
# Tasks 与分级仪式

- Quick：低风险、局部、可快速回滚；仍需合同、权限、测试和证据。
- Feature：跨组件或有用户可见行为；需完整 spec/plan/tasks。
- Project：多阶段、数据迁移、部署或治理影响；逐阶段 Gate 和独立签核。

任务格式：ID、合同/需求映射、前置条件、允许改动、禁止改动、单次可完成动作、先失败测试、完成信号、Evidence、回滚。一个任务一次提交；失败不能用改报告代替修复。

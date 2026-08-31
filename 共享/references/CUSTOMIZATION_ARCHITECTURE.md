# CUSTOMIZATION_ARCHITECTURE（企业定制架构）

机械核心：`product_completion_core.py`（双 schema 字段集 / NON_OVERRIDABLE_CORE_INVARIANTS / merge_profiles / classify_learning）；测试：CUS-001..008。

## 四层（§29，禁止公司 Fork）

```text
CORE（不可变安全不变量）
  + HARNESS ADAPTER（平台专属）
  + ENTERPRISE PROFILE（组织级 13 字段）
  + PROJECT PROFILE（项目级 12 字段）
```

## 合并优先级与冲突

CORE_INVARIANTS > Enterprise > Project > Task；低层违反高层 → `PROFILE_CONSTRAINT_CONFLICT`（merge_profiles 机械检出）。不可覆盖核心不变量：evidence_integrity / candidate_identity_verification / human_authorization_boundary / anti_fake_pass / recovery_evidence / scope_authority / telemetry_integrity（`allow_fake_pass=true` 等尝试被 validate_profile 直接拒绝）。

## 双学习线（§34）

`GLOBAL_FAILURE_PATTERN → Core Skill Evolution`；`COMPANY_SPECIFIC_PATTERN → Enterprise Profile Evolution`。公司规则永不学成全球 Core（classify_learning 机械分流）。合成示例：Biopharma Private AI（external_model_for_sensitive_data=DENY；production 需 IT+BUSINESS_OWNER；regulated evidence=STRICT；internal model preferred）——仅用于 Profile 测试，无任何真实企业秘密。

## POST_v1.5.0 泛化修订单（2026-08-31）

`product_completion_core.py` 新增 Part E（项目编排与泛化）：`CAPABILITY_REGISTRY`（Layer 2 条件能力）、`derive_active_plan`（Layer 4 Active Delivery Plan）、`compile_enterprise_workflow`（企业流程=输入）、`classify_experience_route`（五路经验路由 + FREQUENCY≠GENERALIZABILITY）、`validate_core_evolution_admission`（Core 准入十项）、`assumption_change_model`（假设变化部分失效）。Project Profile 分类字段必填、能力声明选填。规格：`PROJECT_ORCHESTRATION_SPEC.md`。

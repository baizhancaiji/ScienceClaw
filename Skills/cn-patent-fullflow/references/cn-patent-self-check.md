# Chinese Patent Self-Check

Use this as the high-level self-check before delivery. Load rule files under `references/cn-review-rules/` only when a specific problem needs detailed guidance.

## Core Checks

1. The draft is written for Chinese patent filing conventions rather than a generic global template.
2. The technical problem, technical solution, and technical effect are all explicit.
3. The core inventive point is distinguishable from the closest known prior art discussed in the draft.
4. The claims direction matches the disclosed embodiments and does not outrun the description.
5. Key terms are used consistently across title, abstract, claims, description, and drawings.
6. The embodiments provide enough implementation detail for support and enablement.
7. Drawings, drawing references, and component names are consistent with the text.
8. The draft avoids vague, absolute, promotional, or non-technical language.
9. If a range, parameter, formula, or acronym is used, it is explained where needed.
10. The final files are timestamped and do not overwrite earlier versions by default.

## Rule Mapping

Use these files when the issue is specific:

- Claims formatting or vague wording:
  `31-权利要求书-简单审查1-格式检查1.md`
  `31-权利要求书-简单审查2-格式检查2.md`
- Claim dependency or claim theme problems:
  `31-权利要求书-简单审查3-所述的引用基础.md`
  `31-权利要求书-简单审查4-引用与主题.md`
- Unity or deeper claim issues:
  `32-权利要求书-复杂审查1.md`
  `32-权利要求书-复杂审查2-单一性.md`
- Specification sufficiency or support:
  `41-说明书-简单审查1.md`
  `42-说明书-复杂审查1-说明书公开是否充分.md`
  `62-全文-复杂审查1.md`
- Global consistency and wording:
  `61-全文-简单审查1.md`
- Drawings:
  `51-附图-简单检查1.md`
  `52-附图-图片检查1.md`

## Delivery Gate

Do not call the draft filing-ready if any of these remain unresolved:

- core inventive point still unclear
- claims unsupported by the specification
- obvious terminology inconsistency
- missing or mismatched drawing references
- retrieval evidence directly undercuts the claimed core point without revision


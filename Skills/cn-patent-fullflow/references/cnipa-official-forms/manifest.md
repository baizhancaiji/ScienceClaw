# CNIPA Official Forms Manifest

This folder contains official CNIPA-related reference texts absorbed from `E:\zhuanli\专利相关要求文档`.

The original downloaded files are left untouched. Only reference copies with English or stable filenames are stored here for skill use.

For forms that may need machine-side prefilling, later manual completion, or direct printing, the skill must preserve original binaries under `assets/cnipa-official-originals/` rather than forcing Markdown conversion.

## Absorbed Into Skill References

### Core drafting references

- `specification_requirements.md`
  Source: `100002说明书.docx`
  Why kept: directly useful for drafting the main specification body.

- `drawing_requirements.md`
  Source: `100003说明书附图.docx`
  Why kept: directly useful for drawing and figure-section requirements.

- `abstract_requirements.md`
  Source: `100004说明书摘要.docx`
  Why kept: directly useful for abstract drafting constraints.

### Revision / post-draft references

- `office_action_response_form.md`
  Source: `100012意见陈述书.docx`
  Why kept: useful for later-stage revision or response workflow, but not part of the first-draft core template.

- `publication_correction_form.md`
  Source: `1f0a71bbb6704b14a22053d21b6672ef.docx`
  Why kept: identified by content as a publication/certificate correction form.

## Not Yet Absorbed

These files appear relevant by filename, but their actual content has not been safely extracted in the current environment because they are legacy `.doc` files and Microsoft Word COM conversion is not currently available:

- `100001权利要求书.doc`
- `100006补正书.doc`
- `100009延长期限请求书.doc`
- `100010恢复权利请求书.doc`
- `100013chzlsqsm.doc`
- `100014fy.doc`
- `100017中止程序请求书.doc`
- `100601fqzlqsm.doc`
- `110401实质审查请求书.doc`
- `120701实用新型专利检索报告请求书.doc`
- `130001外观设计图片或照片.doc`
- `5842a6cb114a427cba1a228d860453b9.doc`
- `c7e44c391f7e4fbfae394af0abd2f169.doc`

## Out Of Current Core Scope

These are official materials but do not belong to the current core skill focus of Chinese invention / utility-model drafting:

- `130002外观设计简要说明.docx`
  Reason: design patent specific, not part of the current main drafting workflow.

## Current Environment Limitation

Legacy `.doc` extraction is blocked right now because `pywin32` is present but Microsoft Word COM automation is not available in the current machine state. The attempted conversion failed with COM class registration error.

Even when conversion becomes available later, not every official form should be normalized to Markdown. Some are better treated as original templates/assets.

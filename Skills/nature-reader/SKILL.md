---
name: nature-reader
description: >-
  Build full-paper Chinese-English side-by-side, figure/table-aware, source-grounded
  Markdown readers for journal or conference papers from PDF, DOI, arXiv, publisher HTML,
  or pasted text. Use whenever the user asks to translate or read a paper, make
  中英文对照/原文对照/全文翻译解读, or keep exact source anchors for every block.
  Triggers: "全文翻译", "中英文对照", "nature-reader", "论文解读", "原文对照", "全篇翻译".
---

## 执行架构（ScienceClaw 适配版）

**输入源处理**：
- **PDF**：使用 `pdf` 技能（`/builtin-skills/pdf/SKILL.md`）提取文本
- **DOI/arXiv 链接**：使用 `web_crawl` 抓取摘要/全文
- **网页 HTML**：使用 `web_crawl` 抓取
- **粘贴文本**：直接处理

本技能不依赖 MCP Server。所有步骤由当前 Agent 直接完成。

# Full-Paper Markdown Reader

Use this skill to turn a research paper into a complete Markdown reading artifact.

The default output should read like a bilingual paper companion, not a summary dump:

- keep the extractable prose, paragraph structure, and section flow
- show original text and Chinese translation together at block level
- extract figures and tables as assets and place them at the first substantive mention or interpretation point
- keep captions attached to figures/tables with English caption text and Chinese caption translation
- preserve stable page and block anchors for traceability
- write a complete `paper.md` by default, plus `source_map.json`, `translation_notes.md`, and `assets/`

This skill is for papers, preprints, and conference proceedings across disciplines. It is not limited to Nature-family journals.

## When to use

Use this skill when the user wants any of the following:

- translate an entire paper into a complete Markdown document
- make a paper easier to read without losing the original wording
- generate a full-paper reading file with original/translation alignment
- keep figures or tables visually close to the claims they support
- preserve exact source locations for every substantive block
- build a source-grounded markdown artifact that can be shared or published
- read a paper in Chinese while keeping the original English structure visible
- keep figure/table captions bilingual and close to the visual assets

## Input requirements

Accept any of these as input:

- a local PDF file path
- a DOI string
- an arXiv URL or arXiv ID
- a publisher HTML URL
- pasted paper text
- a previously generated `paper.md` that needs refresh or audit

If the user provides multiple inputs, prefer the most authoritative source.
For example, DOI + PDF together should use DOI for metadata and PDF for body extraction.

## Default output contract

By default, produce a directory-shaped artifact under the workspace with at least:

- `paper.md`: the main bilingual reading file
- `source_map.json`: mapping from each block in `paper.md` back to source location
- `translation_notes.md`: notes on ambiguity, terminology choices, and unresolved extraction issues
- `assets/`: extracted figures, tables, and image files

### `paper.md` structure

The default structure should be:

1. Paper metadata header
2. Bilingual abstract
3. Bilingual sections in original order
4. Figure/table blocks inserted at first meaningful mention point
5. Captions in bilingual form
6. Optional reference section if the source provides it

### Translation block rule

For each substantial block, use this shape:

- original text
- Chinese translation
- optional source anchor note

Do not flatten the paper into summary bullets unless the user asks for summary mode.

## Source grounding rules

This skill must be source-grounded, not hallucination-friendly.

1. Do not invent content that is not present in the source.
2. If a paragraph is unclear, partially extracted, or corrupted by PDF extraction, say so in Chinese in `translation_notes.md`.
3. If a figure is missing or unrecoverable, keep a placeholder and explain the issue.
4. If page numbers are available, preserve them as anchors.
5. If block-level anchors are not possible, use paragraph numbering or section anchors instead.

## PDF extraction guidance

When the source is PDF:

- prefer structural extraction over raw text dump
- preserve section headings, lists, and paragraph breaks
- keep figure references near their first mention
- extract table content if possible, otherwise keep a textual description and note the limitation
- if OCR is needed, say so explicitly in the notes artifact

## Translation guidance

When translating:

- keep technical terms faithful to the field
- avoid ornamental rewriting
- preserve author claims without strengthening or softening them
- keep abbreviations and symbols intact where appropriate
- if a term has multiple plausible Chinese translations, add a short note in `translation_notes.md`

## Figure and table handling

When figures or tables appear:

- extract the asset if possible
- place the asset near the first substantive reference, not necessarily at the end
- keep the original caption
- add a Chinese caption translation below the original
- if the source only gives "Figure 1" with no nearby context, keep a note and avoid inventing interpretation

## Review checklist

Before returning the artifact, check:

- all major sections are present
- no invented claims were added
- figures/tables are placed near relevant discussion
- source anchors exist for key blocks
- Chinese translation is readable and accurate
- missing content is explicitly flagged
- the output can be reopened later without losing structure

## Output style

The output should feel like a careful bilingual reading companion, not a marketing summary.

Prefer clarity, structure, and traceability over brevity.

## Failure handling

If the source cannot be read:

- do not guess the paper contents
- explain the failure clearly in Chinese
- suggest the next best action, such as providing a different PDF, DOI, or pasted text

## Interaction mode

Default language:

- respond in the user's language when asking clarification questions
- keep final artifacts bilingual unless the user asks for Chinese-only or English-only output

If the user asks for changes, revise the existing artifact instead of rebuilding from scratch unless a rebuild is clearly better.
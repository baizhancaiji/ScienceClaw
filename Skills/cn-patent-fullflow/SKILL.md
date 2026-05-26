---
name: cn-patent-fullflow
description: >-
  中文专利撰写全流程技能。覆盖创意挖掘、交底书录入、现有技术检索（国知局/ToolUniverse/WebSearch）、
  中文专利说明书撰写、权利要求强化、反馈修订、Markdown/Word 终稿交付。适用于从零写中文专利、
  改进现有专利交底书、将 Word/PPT 材料转为撰写输入、根据审查人或代理机构意见修订专利文件。
  Trigger: 写专利、专利交底书、专利申请、专利撰写、改进专利、专利检索查新、
  "patent draft"、CNIPA、国知局、权利要求。
---

# 中文专利撰写全流程

端到端中文专利撰写工作流，面向中国专利撰写与提交准备。

## 适用范围

1. 从想法或零散材料到可提交的中文专利交底书。
2. 从已有交底书、技术文档、`.docx`/`.pptx` 到改进版中文专利文档。
3. 从审查人、发明人、代理机构反馈到针对性修订与重新交付。
4. 从定稿 Markdown 到 `.docx` 交付（含内嵌图表）。

## 硬性边界

- 默认语言为简体中文，除非用户明确要求其他语言。
- 以中国专利撰写惯例为先。
- **检索优先路径**：CNIPA（国知局公布公告）→ ToolUniverse（PubMed/OpenAlex/Semantic Scholar/Crossref）→ Web 搜索。
- 不依赖 Google Search / Google Scholar / Google Patents 作为默认路径。
- **不要**覆盖先前版本草稿，除非用户明确要求替换。
- 禁止编造 DOI/公开号/URL/期刊/卷期/页码。

---

## 工作流选择

选择最轻量的匹配通道：

### Lane A：从零撰写新专利

当用户有想法、技术笔记、设计文档、实验笔记或混合素材时使用。

按序执行：

1. 读取 `prompts/intake.md` → 收敛案件边界（可跳过，但须注明假设）
2. 读取 `prompts/project_scan.md` → 材料摸底与信息补全
3. 读取 `prompts/patent_points_analyzer.md` → 挖掘 3-5 个候选专利点
4. 读取 `prompts/prior_art_search.md` → 现有技术检索查新
5. 读取 `prompts/disclosure_preview.md` → 交底书撰写预览（用户可跳过）
6. 读取 `prompts/disclosure_builder.md` → 按模板生成全文
7. 读取 `prompts/disclosure_self_check.md` → 生成后自检修订

**交付物**：
- Markdown 格式技术交底书
- 提交用 `.docx` 文件
- 查新笔记与关键区别点

### Lane B：改进现有交底书

当用户已有中文交底书、技术文档、`.docx`/`.pptx` 或混合素材时使用。

按序执行：

1. 读取 `prompts/intake.md`
2. 读取 `prompts/project_scan.md`
3. 读取 `prompts/patent_points_analyzer.md`（仅用于找缺口和重组，非盲目重写）
4. 读取 `prompts/prior_art_search.md`（针对性对比）
5. 读取 `prompts/disclosure_builder.md`
6. 读取 `prompts/disclosure_self_check.md`

若用户明显是继续之前的交底书，额外读取：
- `prompts/iteration_context.md`

**交付物**：
- 改进版 Markdown 交底书（带时间戳新文件名）
- 改进版 `.docx`
- 简版修订说明

### Lane C：反馈后修订

当用户提供发明人、内部审阅人、或专利代理机构的反馈时使用。

按序执行：

1. 读取 `prompts/iteration_context.md`
2. 读取 `prompts/merger.md`（当输入是补充性材料时）
3. 读取 `prompts/correction_handler.md`（当输入是纠正性反馈时）
4. 读取 `prompts/prior_art_search.md`（若反馈改变了新颖性或创造性假设）
5. 读取 `prompts/disclosure_self_check.md`

**交付物**：
- 修订版 Markdown 交底书（带时间戳新文件名）
- 修订版 `.docx`
- 简版纠正或合并摘要

---

## Office 材料录入

当素材包含 Office 文件时：

| 文件格式 | 处理方式 |
|---------|---------|
| `.docx` | 运行 `python3 tools/docx_to_md.py --input <文件> --output <输出.md>` |
| `.doc` | 先用 LibreOffice 转 `.docx`：`soffice --headless --convert-to docx <文件>` 再同上 |
| `.pptx` / `.ppsx` | 运行 `python3 tools/pptx_to_md.py --input <文件> --output <输出.md>` |

将转换后的 Markdown 作为主要分析输入。

---

## 检索策略

先读取 `prompts/prior_art_search.md` 再开始检索。

### 检索优先级

1. **CNIPA 国知局** → 通过 `tools/cnipa_epub_search.py`（需要 Playwright + Chromium）
2. **ToolUniverse 学术工具** → `PubMed_search_articles`、`SemanticScholar_search_papers`、`openalex_literature_search`、`Crossref_search_works`
3. **Web 搜索** → `web_search`（中文源优先，如 cnki.net、万方、百度学术）

### CNIPA 国知局检索（优先尝试）

**前提**：Playwright 已安装且 Chromium 已就绪。执行：

```bash
pip install -r tools/requirements-cnipa.txt
python -m playwright install chromium
```

对每个检索单位**分次独立调用**（一次一词块，每次独立 Bash）：

```bash
python3 ${SKILL_DIR}/tools/cnipa_epub_search.py <单个中文词块>
```

- **拆分原则**：2-8 个有检索意义的语义块（专业术语、名词短语、名动组合），**不要**拆成单字或泛词
- **合并去重**：解析每次 stdout 中 `EPUB_HITS_JSON:` 那一行 JSON 数组，按 `pub_number` 去重
- **`abstract` 必须使用**：若命中条目含非空 `abstract`，交底书 1.1 对该专利的概括必须基于摘要理解后撰写
- **降级编辑**：若 Playwright 不可用、超时、无结果，**进入下一步**

### ToolUniverse 学术检索（降级/补充）

在 CNIPA 不可用或结果不足时启用：

- `SemanticScholar_search_papers` — 通用学术论文 + 引用图
- `PubMed_search_articles` — 生物医药领域专利相关文献
- `openalex_literature_search` — 跨学科学术索引（含 OA 链接）
- `Crossref_search_works` — DOI 精确元数据查询

### Web 搜索（降级/补充）

用 `web_search`，中文关键词优先，选择可访问的公开中文源：
- CNIPA 相关页面、国内知识产权资讯、专利公开转载页面
- 期刊官网、DOI 着陆页、机构知识库
- 外国专利或论文仅在确有帮助时补充

---

## 交底书结构与交付

使用 `prompts/disclosure_builder.md` 获取完整模板。

### 标准章节结构

```
1. 注意事项
2. 一、介绍相关技术背景，描述与本发明技术最相近的现有技术，并说明该现有技术存在的缺点
   - 1.1 现有技术（按技术方向分类，含专利检索结果）
   - 1.2 现有技术存在的缺点
3. 二、针对上述缺点，说明本发明所要解决的技术问题
4. 三、本发明技术方案的详细阐述
   - 3.1 背景
   - 3.2 系统框图（Mermaid）
   - 3.3 模块功能说明
   - 3.4 系统流程说明（Mermaid 流程图）
   - 3.5 关键技术参数
5. 四、与现有技术相比，本发明具有哪些优点？
6. 五、本发明的技术关键点和欲保护点是什么？
7. 六、其它（实施例、技术效果、参数示例）
```

**硬性要求**：
- 1.1 每条现有技术必须附经核验的公开源 URL
- 系统框图与流程图必须使用 Mermaid fenced code block，定稿前经 `tools/mermaid_render.py` 转为 PNG
- **禁止**在正文中出现自检清单、技能仓库脚注、"教学示例"等元信息

### 最终交付流程

1. 写出 Markdown 交底书（带时间戳文件名：`{案件名}_{YYYYMMDDHHmmss}.md`）
2. 运行 `python3 ${SKILL_DIR}/tools/mermaid_render.py -i <草稿.md> -o <终稿.md>`
   - 环境变量设置：`MERMAID_CFG_SCALE=3`（防 DOCX 清晰度不足）
   - npx fallback 可用但速度慢
3. 运行 `python3 ${SKILL_DIR}/tools/md_to_docx.py --input <终稿.md> --output <文件名.docx>`
4. 对用户交付 Markdown 路径 + `.docx` 路径 + 简版变更说明 + 当前新颖性/区别视角

### 权利要求侧面引导（仅对话回复，不入正文）

**凡定稿交付**的对话回复中附加『可选下一步』类交互：
- 「侧重方法步骤保护 → 建议独立方法权利要求 + 对应系统权要」
- 「侧重系统/装置保护 → 建议系统权利要求为主 + 存储介质从权」
- 「侧重应用/用途保护 → 建议用途权利要求 + 对应方法限定的产品权要」

---

## 自检

交底书生成后，**内部执行**自检（不将自检清单写入正文）：

| 检查维度 | 关键项 |
|---------|--------|
| 逻辑闭环 | 方案是否完整？模块关联清晰？分支有处理路径？ |
| 参数一致性 | 公式/阈值/参数命名全文统一 |
| 格式与引用 | 迭代路径留档、文件名时间戳、Mermaid 已转 PNG、1.1 每条有 URL |
| 查新摘要 | CNIPA 条目 abstract 是否已被充分理解并改写入 1.1 |
| 文末清洁 | 无技能仓库名/教学示例/免责脚注 |

发现问题则直接修订正文后再交付。

> 读取 `prompts/disclosure_self_check.md` 和 `references/cn-patent-self-check.md` 获取完整自检清单。

---

## 环境变量参考

| 变量 | 用途 | 默认值 |
|------|------|--------|
| `MERMAID_CFG_SCALE` | Mermaid PNG 渲染缩放 | `2` |
| `OUTPUT_DIR` | 交付文件输出目录 | `./outputs/` |
| `SKILL_DIR` | 本技能安装目录 | (自动检测) |

---

## 工具清单

| 工具 | 作用 |
|------|------|
| `tools/docx_to_md.py` | `.docx`/`.doc` → Markdown（`.doc` 需先 LibreOffice 转 `.docx`） |
| `tools/pptx_to_md.py` | `.pptx`/`.ppsx` → Markdown |
| `tools/md_to_docx.py` | Markdown → `.docx`（Mermaid 先转 PNG） |
| `tools/mermaid_render.py` | Mermaid 围栏块 → PNG 并替换 Markdown 引用 |
| `tools/cnipa_epub_search.py` | CNIPA 公布公告站检索（需 Playwright + Chromium） |
| `tools/doc_converter.py` | `.doc` → `.docx` 转换辅助（需 LibreOffice） |
| `tools/iteration_dialog_log.py` | 迭代对话记录与摘要追加 |

### .doc 文件处理（Linux 环境）

由于沙箱为 Linux 环境，无 Microsoft Word COM。`.doc` 文件通过以下方式处理：

```bash
soffice --headless --convert-to docx <输入.doc> --outdir <输出目录>
```

转换后再用 `tools/docx_to_md.py` 提取为 Markdown。

---

## 依赖

### Python（须预装）
- `python-docx` — Markdown → Word
- `mammoth` — Word → Markdown
- `python-pptx` — PPTX → Markdown
- `requests` — HTTP 请求
- `playwright` — CNIPA 站点浏览器自动化（可选，仅 CNIPA 检索需要）

### Node（Mermaid 渲染，可选）
- `npx` 已预装，Mermaid 渲染可通过 npx 临时拉取 `@mermaid-js/mermaid-cli`
- 也可预先安装：`npm install -g @mermaid-js/mermaid-cli`

### 系统工具
- `soffice` (LibreOffice) — `.doc` 文件预处理

---

## 输出规范

每次最终交付提供：
- 最新的 Markdown 交底书路径
- 最新的 `.docx` 路径
- 本轮变更摘要
- 当前新颖性/与现有技术区别的简述（若执行了检索）

# Tools 中文分类、国际化与三段式工具发现执行计划

更新时间：2026-05-31

本文档是 ScienceClaw 工具目录治理的当前权威计划。当前阶段只处理 **中文 UI、工具分类、Agent 工具暴露面、非 embedding 工具检索策略**。当前阶段不做工具平台重构，不引入 embedding，不引入向量数据库，不把全量工具目录注入 Agent 上下文。

## 目标与边界

### 当前阶段必须完成

1. Tools / MCP / ToolUniverse 相关页面必须完成中文国际化治理，页面普通文本、按钮、空状态、状态标签、工具分类名不得中英文混杂。
2. 工具分类必须在中文语境下重新整理。普通类别名使用中文，专有名词保留原文，例如 `arXiv`、`OpenAlex`、`PubMed`、`ToolUniverse`、`MCP`。
3. Agent 侧必须控制工具暴露面。基础常用工具可以直接暴露，大规模或可扩展工具源必须通过“检索 -> 获取信息 -> 运行”的三段式流程使用。
4. 工具快速定位必须采用非 embedding 混合检索：结构化过滤 + SQLite FTS5 全文检索 + 中文别名/同义词扩展 + 规则重排。
5. 文档、代码和 Agent 提示必须明确区分：
   - Agent 直接暴露工具
   - 可浏览目录项
   - 可检索工具索引项
   - skill 内辅助脚本

### 当前阶段明确不做

1. 不引入 embedding 模型、本地 embedding 服务、embedding API 或向量数据库。
2. 不把 ToolUniverse 1,900+ 工具元数据注入 Agent 上下文。
3. 不把任意 MCP server 暴露的工具全量默认注入 Agent。
4. 不把 `Skills/*/tools` 或 `builtin_skills/*/scripts` 当成 Agent runtime tools 扫描。
5. 不重写 DeepAgents / sandbox 基础工具体系。
6. 不删除现有 `tooluniverse_search`、`tooluniverse_info`、`tooluniverse_run` 兼容入口。

## 当前事实

### 外置 `Tools/` 是热加载 Python 工具入口

- 根目录 `Tools/__init__.py` 使用 AST 扫描同目录 `.py` 文件，只提取第一个 `@tool` 函数元数据。
- 后端不直接 import 用户工具；外置工具被包装成 `StructuredTool` 后，通过 sandbox 容器执行。
- `reload_external_tools()` 使用目录变更检测和缓存，返回外置工具代理列表。

### Agent 当前工具注入链路

- `_STATIC_TOOLS` 当前包含 `web_search`、`web_crawl`、`propose_skill_save`、`propose_tool_save`、`eval_skill`、`grade_eval`、`tooluniverse_search`、`tooluniverse_info`、`tooluniverse_run`。
- `_collect_tools()` 合并 `_STATIC_TOOLS` 和根目录 `Tools/` 代理工具，并按用户级 `blocked_tools` 过滤。
- `_append_user_mcp_tools()` 在 `_collect_tools()` 之后追加当前用户启用的 HTTPS MCP 工具。

### ToolUniverse 当前定位方式

- Agent 侧只暴露三个 ToolUniverse adapter：`tooluniverse_search`、`tooluniverse_info`、`tooluniverse_run`。
- `tooluniverse_search()` 当前调用 ToolUniverse 内部 `Tool_Finder_Keyword`，按 query 和 limit 返回少量候选工具。
- `/api/v1/tooluniverse/tools` 当前服务前端目录浏览：构建 `tu.all_tools` 的轻量列表，缓存 600 秒，再按名称/描述做字符串过滤。
- ToolUniverse catalog 是可浏览、可检索目录，不是 Agent tool list。

### 前端当前工具入口

- `ToolsPage.vue` 当前有 `Science`、`External`、`MCP` 三个 tab。
- `Science` 展示 ToolUniverse catalog。
- `External` 展示根目录外置 `Tools/`。
- `MCP` 展示已启用 HTTPS MCP 工具。
- 运行时工具事件展示依赖 `tool_meta`、`constants/tool.ts` 和 `useTool.ts`。

### Skills 内脚本不是 Agent 直接工具

- `ScienceClaw/backend/builtin_skills/*/scripts/`、`Skills/*/tools/` 是技能工作流资源。
- 这些脚本只有在 skill 指令中被 Agent 通过文件/命令工具间接使用。
- 它们不得进入 Agent runtime tool registry，除非通过 `tool-creator` 和 `propose_tool_save` 显式保存到根目录 `Tools/`。

## Agent 工具暴露规则

### 直接暴露的基础工具

基础工作能力继续直接暴露给 Agent，因为它们高频、低数量、语义稳定：

| 能力 | 示例 |
| --- | --- |
| 文件读写 | `read_file`、`write_file`、`edit_file`、`ls`、`grep` |
| 命令执行 | `execute` / sandbox 执行类工具 |
| 网页搜索与抓取 | `web_search`、`web_crawl` |
| skill/tool 生命周期控制 | `propose_skill_save`、`propose_tool_save` |

### 三段式使用的扩展工具源

以下工具源不得全量直接暴露给 Agent，必须通过三段式流程使用：

| 工具源 | 当前/目标暴露方式 |
| --- | --- |
| ToolUniverse 1,900+ catalog | 当前只暴露 `tooluniverse_search/info/run`，后续接入通用 `tool_search/info/run` provider |
| HTTPS MCP tools | 当前按用户启用工具追加；后续进入统一检索索引并由 `tool_run` 分发 |
| 外置 Python `Tools/*.py` | 当前直接注入；后续当数量增长时进入统一检索索引，默认通过 `tool_search/info/run` 调用 |
| 其他可扩展工具源 | 必须先进入工具索引，不得直接批量注入 Agent |

### 三段式流程

所有扩展工具源统一采用：

```text
tool_search -> tool_info -> tool_run
```

1. `tool_search(query, source_type?, category_zh?, limit?, debug?)`
   - 只返回 top 5-10 个短候选。
   - 不返回完整参数 schema。
   - 不返回全量目录。
   - 默认只返回 `tool_ref`、`name`、`cat_zh`、`why`。
   - 只有 `debug = true` 时才返回 score、source、命中字段等诊断信息。
   - `debug` 是 `tool_search` 的可选入参，默认值固定为 `false`。
   - `debug` 不设置全局开关，不做普通 UI 开关，不由 Tools 页面默认传入。
2. `tool_info(tool_ref)`
   - 只返回单个工具的参数 schema、说明、限制、示例。
   - Agent 必须在运行未知扩展工具前调用它。
3. `tool_run(tool_ref, arguments)`
   - 按 `tool_ref` 分发到具体 provider。
   - Agent 不得臆测工具参数。

现有 `tooluniverse_search`、`tooluniverse_info`、`tooluniverse_run` 必须保留兼容。通用三段式入口落地后，ToolUniverse provider 复用现有三个 adapter 的能力。

## 非 embedding 混合检索策略

### 检索原则

工具快速定位不使用 embedding。检索系统必须可解释、低成本、可离线运行、可测试。

### 工具索引字段

统一工具索引项必须包含以下轻量字段：

| 字段 | 用途 |
| --- | --- |
| `tool_ref` | 稳定工具引用，例如 `tooluniverse:PubMed_search_articles` |
| `source_type` | `tooluniverse`、`https_mcp`、`external_python_tool` 等 |
| `name` | 原始工具名 |
| `display_name` | 展示名 |
| `name_zh` | 中文名，没有则为空 |
| `description` | 原始描述 |
| `description_zh` | 中文描述 |
| `category_zh` | 中文分类 |
| `aliases` | 中文别名、英文别名、常见说法 |
| `keywords` | 检索关键词 |
| `provider` | ToolUniverse、MCP server 名称、Tools 目录等 |
| `enabled` | 是否启用 |
| `blocked` | 当前用户是否屏蔽 |
| `schema_status` | `available`、`missing`、`complex` |
| `has_examples` | 是否有示例 |
| `last_success_at` | 最近成功调用时间，可为空 |

### 查询流程

`tool_search` 必须按以下顺序执行：

1. **结构化过滤**
   - 过滤 `enabled = true`。
   - 过滤 `blocked = false`。
   - 按用户权限过滤。
   - 如果提供 `source_type` 或 `category_zh`，先缩小候选范围。
2. **查询归一化**
   - 中英文大小写归一。
   - 中文全角/半角归一。
   - 保留专有名词原文。
   - 扩展中文同义词和别名，例如 `论文 -> 文献 paper article`，`医学论文 -> PubMed EuropePMC OpenAlex`。
3. **SQLite FTS5 全文检索**
   - 对 `name`、`display_name`、`name_zh`、`description`、`description_zh`、`category_zh`、`aliases`、`keywords`、`provider` 建 FTS 索引。
   - 第一轮取 top 30 候选。
4. **规则重排**
   - 排序优先级固定为：精确工具名命中 > 中文别名命中 > 分类命中 > 描述命中 > provider 命中。
   - 加分项固定为：已启用、有示例、schema 简单、最近成功调用过、当前语言匹配。
5. **短结果返回**
   - 默认返回 top 5。
   - 最大返回 top 10。
   - 默认只返回最小候选字段。
   - `debug = True` 时才返回诊断字段，说明命中来源、分数和排序细节。

### `tool_search` 返回形状

`tool_search` 入参固定为：

```python
tool_search(
    query: str,
    source_type: str | None = None,
    category_zh: str | None = None,
    limit: int = 5,
    debug: bool = False,
)
```

默认返回：

```json
{
  "results": [
    {
      "tool_ref": "tooluniverse:PubMed_search_articles",
      "name": "PubMed 文献检索",
      "cat_zh": "学术文献",
      "why": "医学论文, PubMed"
    }
  ]
}
```

默认结果不得返回完整描述、参数 schema、示例、provider 详情、原始 description、score 或命中字段列表。

`debug = True` 时允许追加诊断信息：

```json
{
  "results": [
    {
      "tool_ref": "tooluniverse:PubMed_search_articles",
      "name": "PubMed 文献检索",
      "cat_zh": "学术文献",
      "why": "医学论文, PubMed",
      "debug": {
        "source_type": "tooluniverse",
        "score": 18.4,
        "matched_fields": ["aliases", "provider"],
        "rank_reason": "alias + provider match"
      }
    }
  ]
}
```

`debug` 信息只用于开发、测试和诊断，不进入 Agent 默认上下文。

### `tool_search` debug 触发边界

`debug` 只能通过 `tool_search(..., debug=True)` 触发。触发来源限定为：

1. 用户明确要求排查工具检索问题，例如“为什么没搜到这个工具”“调试工具搜索排序”“看看 tool_search 为什么选了这个结果”。
2. 后端单元测试、集成测试或开发调试代码显式传入 `debug=True`。

普通对话、普通 Tools 页面浏览、Agent 常规工具发现流程都必须使用默认 `debug=False`。实现时不得增加全局 debug 开关，不得在前端普通页面默认传 `debug=True`，不得把 debug 诊断字段写入 Agent 常规上下文。

### `tool_info` 返回形状

```json
{
  "tool_ref": "tooluniverse:PubMed_search_articles",
  "name": "PubMed_search_articles",
  "display_name": "PubMed 文献检索",
  "description": "...",
  "cat_zh": "学术文献",
  "input_schema": {},
  "examples": [],
  "limitations": []
}
```

### `tool_run` 分发规则

```text
tooluniverse:* -> ToolUniverseProvider.run
https_mcp:*    -> McpProvider.run
external:*     -> ExternalPythonToolProvider.run
```

`tool_run` 不接受未解析的自然语言任务。Agent 必须先通过 `tool_search` 得到 `tool_ref`，再通过 `tool_info` 获取参数结构，最后传入结构化 `arguments`。

## 中文工具分类表

当前阶段工具类别使用以下中文分类。实现时不得直接展示英文普通类别名。

| 中文分类 | 覆盖范围 | 保留原文示例 |
| --- | --- | --- |
| 学术文献 | 论文、预印本、引用、摘要、全文检索 | arXiv、OpenAlex、PubMed、Crossref |
| 生命科学 | 蛋白、基因、通路、组学、生物数据库 | UniProt、PDB、AlphaFold |
| 药物与化合物 | 靶点、ADMET、毒性、药物安全、化合物属性 | ChEMBL、FAERS |
| 临床医学 | 临床试验、疾病、指南、患者数据 | ClinicalTrials |
| 材料与化学 | 材料性质、晶体、分子、反应、谱图 | COD、SMILES |
| 地球与环境 | 地震、水文、气候、空气质量、土壤、海洋 | USGS、OpenMeteo |
| 天文与空间 | 天体、星历、空间天气、巡天数据 | SIMBAD、SDSS、NASA |
| 数据处理 | 表格、统计、数据转换、可视化、机器学习 | OpenML |
| 文档处理 | PDF、DOCX、PPTX、XLSX、Markdown 转换 | PDF、DOCX、PPTX、XLSX |
| 网页与外部服务 | 网页搜索、网页抓取、第三方 API、MCP 服务 | MCP |
| 文件与执行 | 文件读写、命令执行、sandbox 操作 | sandbox |
| 技能与工具管理 | skill 创建、tool 创建、保存、评估、屏蔽 | Skill、Tool |
| 其他 | 未归类或用户自定义工具 | 用户自定义名 |

## 分阶段执行路线

### 阶段 1：文案与分类盘点

目标：形成当前 UI 文案和分类问题清单，不改运行逻辑。

步骤：

1. 扫描 `ToolsPage.vue`、`McpToolsTab.vue`、`McpToolCard.vue`、`McpSettings.vue`、`ScienceToolDetail.vue`、`ToolDetailPage.vue` 中所有硬编码英文。
2. 扫描 `constants/tool.ts`、`useTool.ts` 中所有工具名、动作名、类别名映射。
3. 扫描 `locales/zh.ts`、`locales/en.ts`，找出已有 key、缺失 key、中文翻译不一致 key。
4. 输出三张清单：
   - 页面可见英文文案清单
   - 工具类别名清单
   - 需要保留原文的专有名词清单

验收：

- 每个 Tools/MCP/ToolUniverse 可见英文都有归属：翻译、保留原文、删除。
- 分类清单只使用中文普通类别名。

### 阶段 2：中文分类与别名词典落定

目标：把工具中文分类、别名、关键词做成检索和 UI 共用的静态合同。

步骤：

1. 将本文档的中文工具分类表落到前端可消费常量或后端共享配置中。
2. 为 ToolUniverse 常见类别建立中文映射。
3. 为高频工具源建立别名和关键词：
   - 学术文献：论文、文献、paper、article、PubMed、arXiv、OpenAlex
   - 药物与化合物：药物、化合物、毒性、ADMET、靶点
   - 生命科学：蛋白、基因、通路、组学
   - 文档处理：PDF、Word、PPT、Excel、表格、转换
4. 规定 UI 展示中文类别，检索索引同时保留中英文关键词。

验收：

- Tools 页展示类别不再出现普通英文类别名。
- 搜索“论文”“医学论文”“药物毒性”“PDF 转换”等中文词能映射到正确类别和候选关键词。

### 阶段 3：前端 i18n 最小改造

目标：先把用户可见界面变成中文一致体验。

步骤：

1. 将 Tools 页 tab、header subtitle、搜索 placeholder、空状态、按钮、状态 badge 接入 i18n。
2. 将 MCP 工具页、MCP 卡片、schema drawer 中的普通英文文案接入 i18n。
3. 将工具事件展示中的普通工具动作名接入 i18n。
4. 保留专有名词原文，不翻译 `ToolUniverse`、`MCP`、`arXiv`、`OpenAlex`、`PubMed` 等。

验收：

```powershell
npm --prefix .\ScienceClaw\frontend run type-check
npm --prefix .\ScienceClaw\frontend run build
```

浏览器验收：

- 中文 locale 下 Tools 页面普通 UI 文案为中文。
- 普通分类名为中文。
- 专有名词保持原文。
- 页面中不出现 `All Tools`、`Search tools...`、`No description available`、`Enabled`、`Disabled` 等未翻译普通英文,而应该是"所有工具","搜索工具...","无描述文本","启用","禁用"等中文释义。

### 阶段 4：非 embedding 工具发现索引设计落地

目标：建立统一工具发现索引合同和后端只读索引，不改变 Agent 暴露面。

步骤：

1. 定义 `ToolIndexItem` schema，字段按本文档“工具索引字段”执行。
2. 为 ToolUniverse catalog 构建索引项，source_type 固定为 `tooluniverse`。
3. 为 HTTPS MCP tools 构建索引项，source_type 固定为 `https_mcp`。
4. 为外置 Python Tools 构建索引项，source_type 固定为 `external_python_tool`。
5. 建立 SQLite FTS5 索引，索引文件放在后端可重建缓存位置，不作为权威数据源。
6. 索引重建必须可重复执行，不能依赖 embedding。

验收：

- 能从索引查询到 ToolUniverse、MCP、外置 Tools 的轻量候选。
- 索引缺失时可以从原始目录/数据库重建。
- 不新增 embedding 依赖。

### 阶段 5：通用三段式 adapter 落地

目标：新增统一工具发现入口，并保留现有 ToolUniverse 三工具兼容。

步骤：

1. 新增 `tool_search`：
   - 调用非 embedding 混合检索。
   - 返回 top 5-10 个短候选。
   - 不返回完整 schema。
2. 新增 `tool_info`：
   - 根据 `tool_ref` 调用 provider 的 info 方法。
   - ToolUniverse provider 复用 `tu.tool_specification()`。
   - MCP provider 读取 MCP tool schema。
   - External Python provider 读取 AST 解析出的参数和 docstring。
3. 新增 `tool_run`：
   - 根据 `tool_ref` 分发到 provider。
   - ToolUniverse provider 复用 `tu.run()`。
   - MCP provider 复用 HTTPS MCP call 链路。
   - External Python provider 复用 sandbox proxy 执行链路。
4. 现有 `tooluniverse_search/info/run` 保留不删。
5. Agent 提示更新为：扩展工具必须先 search，再 info，再 run。

验收：

```powershell
$env:PYTHONNOUSERSITE='1'
conda run -p D:\conda\envs\scienceclaw python -m pytest ScienceClaw/backend/tests -k "tool_search or tool_info or tool_run or tooluniverse or mcp"
```

Agent 暴露面验收：

- ToolUniverse 1,900+ catalog item 不进入 `_collect_tools()`。
- 新增通用入口后，Agent 只增加 `tool_search`、`tool_info`、`tool_run` 三个稳定工具。
- 大规模工具源只通过索引和 provider 按需调用。

### 阶段 6：文档与提示词对齐

目标：让 README、内置 skill、Agent 提示和 UI 行为一致。

步骤：

1. 更新 README 工具体系说明：
   - 基础常用工具直接暴露。
   - 扩展工具源走三段式发现流程。
   - ToolUniverse catalog 不等于 Agent tools。
2. 更新 `tool-creator` 文案：
   - 只有根目录 `Tools/*.py` 是外置 Python tools。
   - skill 内脚本不是 Agent runtime tools。
3. 更新 `tooluniverse` skill 文案：
   - ToolUniverse 使用 `search -> info -> run`。
   - 不列出全量工具目录。
4. 更新 Agent system prompt：
   - 说明已有能力类别。
   - 要求扩展工具必须走三段式流程。
   - 禁止请求全量工具列表和臆测参数。

验收：

- 文档、UI 和 Agent 提示对工具使用路径的描述一致。
- 新用户可以判断：何时直接用基础工具，何时用 `tool_search/info/run`。

## 风险与处理

| 风险 | 处理 |
| --- | --- |
| 上下文膨胀 | ToolUniverse catalog 永不进入 Agent tool list；MCP 和外置 Tools 后续按索引发现 |
| 中文检索召回不足 | 用中文别名、关键词、同义词扩展和分类加权补足，不用 embedding |
| 工具重名 | 所有扩展工具使用 `tool_ref`，不用裸工具名作为唯一标识 |
| UI 与 Agent 语义不一致 | UI catalog item 标记为可浏览；Agent 只拿稳定入口工具 |
| 旧流程兼容 | 保留 `tooluniverse_search/info/run` 和现有 Tools/MCP 接口，新增通用入口不破坏旧入口 |
| 误扫 skill scripts | 扫描规则固定为根目录 `Tools/*.py`，不递归扫描 `Skills/**/tools` |

## 当前执行顺序

执行顺序固定为：

1. 先做阶段 1-3，完成中文 UI 与中文分类治理。
2. 再做阶段 4，建立非 embedding 工具发现索引。
3. 再做阶段 5，新增通用三段式 adapter。
4. 最后做阶段 6，统一 README、skill 文案和 Agent 提示。

任何代码实现都必须保持以下不变量：

1. 不引入 embedding。
2. 不扩大 Agent 工具暴露面到全量 catalog。
3. 不破坏现有 ToolUniverse 三工具兼容入口。
4. 不把 skill resource scripts 当成 runtime tools。
5. 中文 UI 普通文本和普通类别名必须一致中文化。

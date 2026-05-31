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

## 仓库现状对齐结论

本计划以当前仓库实际文件为准，不以旧设计文档的“建议新增模块”为准。`docs/archive/plans/mcp-https-integration-design-zh.md` 只作为结构和粒度参考；其中 MCP 模块已落地到当前仓库，本计划不得再把已存在的 MCP 模块描述为待新增组件。

### 当前已存在组件

| 工作面 | 当前文件 | 当前职责 | 本计划调整方向 |
| --- | --- | --- | --- |
| Agent 工具汇总 | `ScienceClaw/backend/deepagent/agent.py` | `_STATIC_TOOLS`、`_collect_tools()`、`_append_user_mcp_tools()` 汇总内置、ToolUniverse、外置 Tools、用户启用 MCP 工具 | 阶段 5 只新增 `tool_search`、`tool_info`、`tool_run` 三个稳定入口；不得把全量 catalog 或全量 schema 注入 `_STATIC_TOOLS` |
| ToolUniverse Agent adapter | `ScienceClaw/backend/deepagent/tooluniverse_tools.py` | 暴露 `tooluniverse_search`、`tooluniverse_info`、`tooluniverse_run`，其中 search 调用 `Tool_Finder_Keyword` | 保留兼容入口；阶段 4-5 的 ToolUniverse provider 复用该能力，不重写为新体系 |
| DeepAgent 基础工具 | `ScienceClaw/backend/deepagent/tools.py` | `web_search`、`web_crawl`、`propose_tool_save` 等基础工具 | 继续作为基础常用工具直接暴露；不进入扩展 catalog 的批量治理 |
| 外置 Python Tools | `Tools/__init__.py` | AST 扫描根目录 `Tools/*.py`，生成 sandbox 代理工具，提供 `reload_external_tools()` | 阶段 4 只读取其现有元数据生成索引项；不得递归扫描 `Skills/**/tools` 或 `builtin_skills/**/scripts` |
| ToolUniverse 前端目录 API | `ScienceClaw/backend/route/tooluniverse.py` | `/api/v1/tooluniverse/tools`、详情、运行；缓存 `tu.all_tools` 轻量列表 | 保持目录浏览接口；阶段 4 provider 可从这里复用目录加载和 ToolUniverse 单例 |
| 外置 Tools API | `ScienceClaw/backend/route/sessions.py` | `/api/v1/sessions/tools`、外置工具保存/读取/删除/屏蔽 | 阶段 4 provider 复用其数据事实；不把 sessions 路由改成统一 discovery 路由 |
| HTTPS MCP API | `ScienceClaw/backend/route/mcp.py` | `/api/v1/mcp/*`，MCP server 和 tool 管理 | 阶段 4 provider 只读取已验证、已启用、未移除工具；不改 MCP 管理主流程 |
| HTTPS MCP 内部层 | `ScienceClaw/backend/mcp/schemas.py`、`repository.py`、`service.py`、`tool_factory.py` | MCP schema、数据库读写、服务层、Agent 工具物化 | 阶段 4-5 复用 repository/service/tool_factory；不新增第二套 MCP client |
| FastAPI 路由注册 | `ScienceClaw/backend/main.py` | 统一以 `/api/v1` include 各 route router | 阶段 5 新增 `tools_router` 后在这里注册，形成 `/api/v1/tools/*` |
| Tools 页面 | `ScienceClaw/frontend/src/pages/ToolsPage.vue` | Science / External / MCP 三 tab；调用 ToolUniverse、External Tools、MCP API | 阶段 1-3 做中文 i18n 和中文分类展示；阶段 5 后如接入统一搜索，只调用 `/api/v1/tools/search`，默认不传 `debug` |
| ToolUniverse 前端 API | `ScienceClaw/frontend/src/api/tooluniverse.ts` | `listTUTools()` 等目录 API | 继续服务 Science tab 目录浏览；不被 `tool_search` 直接替代 |
| MCP 前端 API | `ScienceClaw/frontend/src/api/mcp.ts` | MCP server/tool 管理 API | 阶段 1-3 补 i18n 类型和展示；阶段 4-5 不改变管理 API 语义 |
| MCP Tools UI | `ScienceClaw/frontend/src/components/tools/McpToolsTab.vue`、`McpToolCard.vue` | MCP 工具列表、搜索、schema drawer 入口 | 阶段 1-3 替换硬编码普通英文；保持 MCP 专有名词原文 |
| MCP Settings UI | `ScienceClaw/frontend/src/components/settings/McpSettings.vue`、`McpToolList.vue`、`McpToolSchemaDrawer.vue` | MCP server 管理、工具启停、schema 查看 | 阶段 1-3 替换普通英文、状态和空态；不改变管理流程 |
| 工具事件展示 | `ScienceClaw/frontend/src/constants/tool.ts`、`ScienceClaw/frontend/src/composables/useTool.ts`、`ScienceClaw/frontend/src/types/event.ts` | 工具名、颜色、图标、事件 meta 映射 | 阶段 1-3 统一中文显示名；阶段 5 后识别 `tool_ref`/`cat_zh` 时仍优先 `tool_meta` |
| i18n 字典 | `ScienceClaw/frontend/src/locales/zh.ts`、`en.ts`、`index.ts` | 前端中英文翻译资源 | 阶段 1-3 新增 Tools/MCP/ToolUniverse 所有普通 UI 文案 key |

### 预计新增组件确切位置

以下新增位置固定，不再使用泛称：

```text
ScienceClaw/backend/tool_discovery/
  __init__.py
  schemas.py
  aliases.py
  providers.py
  index_store.py
  service.py

ScienceClaw/backend/deepagent/discovery_tools.py
ScienceClaw/backend/route/tools.py
ScienceClaw/backend/tests/test_tool_discovery_index.py
ScienceClaw/backend/tests/test_tool_discovery_service.py
ScienceClaw/backend/tests/test_deepagent_discovery_tools.py

ScienceClaw/frontend/src/constants/toolCategories.ts
ScienceClaw/frontend/src/api/tools.ts
```

新增后端 API 路径固定为：

```text
POST /api/v1/tools/search
GET  /api/v1/tools/info/{tool_ref}
POST /api/v1/tools/run
```

其中 `ScienceClaw/backend/route/tools.py` 的 router prefix 固定为 `/tools`，并由 `ScienceClaw/backend/main.py` 继续统一加 `/api/v1` 前缀。

### 新增组件职责

| 新增组件 | 职责 | 不得承担的职责 |
| --- | --- | --- |
| `backend/tool_discovery/schemas.py` | 定义 `ToolIndexItem`、`ToolSearchRequest`、`ToolSearchResult`、`ToolInfoResult`、`ToolRunRequest` 等 Pydantic schema | 不保存业务状态 |
| `backend/tool_discovery/aliases.py` | 保存中文分类、别名、同义词、专有名词保留表 | 不调用数据库，不调用外部服务 |
| `backend/tool_discovery/providers.py` | 定义 provider 协议，并实现 ToolUniverse、HTTPS MCP、External Python Tools 三类 provider | 不做 FTS 排序，不直接处理 HTTP request |
| `backend/tool_discovery/index_store.py` | 管理 SQLite FTS5 可重建索引、查询、重排输入候选 | 不作为权威数据源，不保存密钥 |
| `backend/tool_discovery/service.py` | 编排 provider、索引重建、`search/info/run` 分发、权限过滤、debug 字段裁剪 | 不直接注入 Agent |
| `backend/deepagent/discovery_tools.py` | 暴露给 Agent 的 `tool_search`、`tool_info`、`tool_run` 三个 adapter | 不返回全量 catalog，不暴露 debug 默认信息 |
| `backend/route/tools.py` | 暴露前端和调试用 `/api/v1/tools/*` API | 不替代 `/tooluniverse`、`/mcp`、`/sessions/tools` 管理接口 |
| `frontend/src/constants/toolCategories.ts` | 前端中文分类、显示顺序、专有名词保留表 | 不保存工具运行参数 schema |
| `frontend/src/api/tools.ts` | 调用统一 `tools/search/info/run` API | 不让普通 Tools 页面默认传 `debug=true` |

### 调整方向不变量

1. `tool_search` 的 API 输出字段使用 `cat_zh`；内部索引字段可使用 `category_zh`。两者边界固定：`category_zh` 是内部字段，`cat_zh` 是对 Agent 和前端返回字段。
2. `tool_search` 的搜索源可以覆盖 ToolUniverse、HTTPS MCP、外置 Python Tools；`tooluniverse_search` 的搜索源只覆盖 ToolUniverse。二者搜索源存在交集，但职责不重叠：前者是统一入口，后者是兼容入口。
3. `tool_search` 不直接搜索 skill scripts。skill scripts 只有被显式保存到根目录 `Tools/*.py` 后，才可能作为 `external_python_tool` 进入索引。
4. `tool_search` 默认返回最小字段；`debug=True` 只能由显式调用触发，不设置全局开关，不在普通 UI 中开启。
5. `tool_run` 只接收 `tool_ref` 和结构化 `arguments`，不接收自然语言任务。
6. MCP 管理面继续使用 `/api/v1/mcp/*`；统一 discovery 面只负责检索、信息和运行，不负责新增/编辑/删除 MCP server。

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
| 外置 Python `Tools/*.py` | 当前直接注入；阶段 4 固定进入统一检索索引，阶段 5 固定支持 `external:*` 通过 `tool_search/info/run` 调用；是否取消当前直接注入不在本计划内隐式改变 |
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

执行顺序固定为阶段 1 到阶段 6。阶段 1-3 先完成用户可见中文一致性和中文分类；阶段 4-5 才进入统一检索与三段式 adapter；阶段 6 做文档、skill 和 Agent 提示收口。

### 阶段 1：现状盘点与问题清单

目标：形成当前 Tools/MCP/ToolUniverse UI 文案、分类和工具来源边界清单，不改运行逻辑。

涉及工作面：

| 工作面 | 文件 |
| --- | --- |
| Tools 主页面 | `ScienceClaw/frontend/src/pages/ToolsPage.vue` |
| ToolUniverse 详情页 | `ScienceClaw/frontend/src/pages/ScienceToolDetail.vue` |
| 外置 Tool 详情页 | `ScienceClaw/frontend/src/pages/ToolDetailPage.vue` |
| MCP 工具浏览 | `ScienceClaw/frontend/src/components/tools/McpToolsTab.vue`、`McpToolCard.vue` |
| MCP 设置页 | `ScienceClaw/frontend/src/components/settings/McpSettings.vue`、`McpToolList.vue`、`McpToolSchemaDrawer.vue`、`McpServerDrawer.vue`、`McpHeaderEditor.vue` |
| 工具展示映射 | `ScienceClaw/frontend/src/constants/tool.ts`、`ScienceClaw/frontend/src/composables/useTool.ts` |
| 类型和 API | `ScienceClaw/frontend/src/api/tooluniverse.ts`、`api/mcp.ts`、`api/agent.ts`、`types/event.ts`、`types/response.ts` |
| i18n 字典 | `ScienceClaw/frontend/src/locales/zh.ts`、`en.ts`、`index.ts` |

详细步骤：

1. 扫描以上 Vue 文件中的 template、script、computed、toast、错误提示、空状态、按钮、placeholder、tab label、状态 badge。
2. 扫描 `constants/tool.ts` 和 `useTool.ts`，列出工具显示名、工具分组名、动作名、MCP fallback 名称中的英文普通词。
3. 扫描 `zh.ts` 和 `en.ts`，列出已有 key、重复 key、缺失 key、中文含义不一致 key。
4. 扫描 `api/tooluniverse.ts` 的 `TUCategory`、`api/mcp.ts` 的 MCP tool 类型、`types/event.ts` 的 `ToolMetaData`，确认当前前端能拿到的分类字段和来源字段。
5. 输出并保留三张盘点清单到本计划后续实施记录中：可翻译普通英文、必须保留原文的专有名词、分类来源字段。

测试口径与方法：

```bash
git diff -- ScienceClaw/frontend/src/pages/ToolsPage.vue ScienceClaw/frontend/src/components/tools ScienceClaw/frontend/src/components/settings ScienceClaw/frontend/src/constants/tool.ts ScienceClaw/frontend/src/composables/useTool.ts ScienceClaw/frontend/src/locales
```

阶段退出标准：

1. 每个 Tools/MCP/ToolUniverse 可见英文都有明确归属：翻译、保留原文、删除。
2. 每个分类来源都有明确处理方式：直接映射、后端补字段、前端 fallback。
3. 阶段 1 不产生运行逻辑改动。

### 阶段 2：中文分类与别名合同落地

目标：把中文分类、别名、关键词落成前后端共用的静态合同，先服务 UI，再服务阶段 4 的索引。

涉及工作面：

| 工作面 | 文件 |
| --- | --- |
| 前端分类常量 | 新增 `ScienceClaw/frontend/src/constants/toolCategories.ts` |
| 前端现有工具映射 | 调整 `ScienceClaw/frontend/src/constants/tool.ts` |
| 前端 i18n | 调整 `ScienceClaw/frontend/src/locales/zh.ts`、`en.ts` |
| 后端检索词典 | 阶段 4 新增 `ScienceClaw/backend/tool_discovery/aliases.py`，本阶段先按本文档合同实现前端侧 |

详细步骤：

1. 新增 `toolCategories.ts`，固定导出中文分类枚举、显示顺序、专有名词保留表和常见别名表。
2. 中文分类键固定使用本文档“中文工具分类表”，不得再新增普通英文分类名。
3. `ToolUniverse`、`MCP`、`arXiv`、`OpenAlex`、`PubMed`、`Crossref`、`UniProt`、`PDB`、`AlphaFold`、`ChEMBL` 等专有名词在显示层保留原文。
4. 将 ToolUniverse 原始 category 映射到中文分类；无法确定时固定落入“其他”，不得展示原始英文普通类别。
5. 将 `constants/tool.ts` 中的工具分组显示名调整为中文显示；图标、颜色和 legacy key 保持兼容。
6. 为阶段 4 的后端 `aliases.py` 保持同一套分类名和别名内容，后端实现时必须以本阶段合同为准。

测试口径与方法：

```bash
npm --prefix ScienceClaw/frontend run type-check
rg -n "All Tools|Search tools|No description available|Enabled|Disabled|External|Science" ScienceClaw/frontend/src/pages/ToolsPage.vue ScienceClaw/frontend/src/components/tools ScienceClaw/frontend/src/components/settings ScienceClaw/frontend/src/constants ScienceClaw/frontend/src/locales
```

阶段退出标准：

1. Tools 页面展示分类只出现中文普通类别名。
2. 专有名词原文保留，不被翻译成生硬中文。
3. “论文”“医学论文”“药物毒性”“PDF 转换”等中文词在前端本地过滤和分类映射中有明确落点。

### 阶段 3：前端 i18n 最小改造

目标：把用户可见 Tools/MCP/ToolUniverse 界面改成中文一致体验，不改变后端数据结构和 Agent 工具暴露面。

涉及工作面：

| 工作面 | 调整方向 |
| --- | --- |
| `ToolsPage.vue` | tab label、标题、副标题、搜索 placeholder、加载态、空态、按钮、删除确认、剩余数量、状态 badge 全部接入 i18n 和中文分类 |
| `McpToolsTab.vue` | 错误态、空态、搜索结果提示、刷新按钮、schema 查看入口接入 i18n |
| `McpToolCard.vue` | schema 字段数、server/source 展示、打开按钮等普通文本接入 i18n |
| `McpSettings.vue`、`McpToolList.vue`、`McpToolSchemaDrawer.vue`、`McpServerDrawer.vue`、`McpHeaderEditor.vue` | server 管理、验证、刷新、启停、认证、headers、schema 文案接入 i18n |
| `ScienceToolDetail.vue`、`ToolDetailPage.vue` | 标题、描述 fallback、参数、运行、错误、返回结果普通文案接入 i18n |
| `constants/tool.ts`、`useTool.ts` | 工具事件显示名中文化；HTTPS MCP 仍优先 `tool_meta` |
| `locales/zh.ts`、`en.ts` | 补齐所有新增 key，中文默认语义必须完整 |

详细步骤：

1. `ToolsPage.vue` 的 tab 显示固定改为“科学工具”“外置工具”“MCP”，内部 tab id 继续保持 `science`、`external`、`mcp`。
2. Science tab 中 ToolUniverse 工具分类通过 `toolCategories.ts` 映射为中文；搜索框支持中文关键词和保留原始专有名词。
3. External tab 中根目录 `Tools/*.py` 工具保留原始函数名作为技术标识，但普通状态文案中文化。
4. MCP tab 和 MCP 设置页保留 `MCP` 原文；`enabled/disabled/healthy/error/unknown` 等普通状态固定翻译。
5. `useTool.ts` 对 HTTPS MCP 工具继续优先读取 `tool_meta.mcp`、`server_name`、`source_type`；缺失时才使用 legacy `mcp_` 前缀 fallback。
6. 所有新增中文 key 必须同时补 `en.ts`，避免英文 locale 运行时报 key。

测试口径与方法：

```bash
npm --prefix ScienceClaw/frontend run type-check
npm --prefix ScienceClaw/frontend run build
rg -n "All Tools|Search tools|No description available|Enabled|Disabled|remaining|Unknown MCP tools error|MCP Tool" ScienceClaw/frontend/src/pages/ToolsPage.vue ScienceClaw/frontend/src/components/tools ScienceClaw/frontend/src/components/settings ScienceClaw/frontend/src/constants/tool.ts ScienceClaw/frontend/src/composables/useTool.ts
```

浏览器验收：

1. 中文 locale 下 Tools 页面普通 UI 文案为中文。
2. 普通分类名为中文。
3. `ToolUniverse`、`MCP`、`arXiv`、`OpenAlex`、`PubMed` 等专有名词保持原文。
4. 页面不出现 `All Tools`、`Search tools...`、`No description available`、`Enabled`、`Disabled` 等未翻译普通英文。

### 阶段 4：非 embedding 工具发现索引落地

目标：建立统一工具发现索引合同和后端可重建索引，不改变 Agent 暴露面。

涉及工作面：

| 工作面 | 文件 |
| --- | --- |
| 新 discovery 包 | `ScienceClaw/backend/tool_discovery/__init__.py`、`schemas.py`、`aliases.py`、`providers.py`、`index_store.py`、`service.py` |
| ToolUniverse provider 来源 | 复用 `ScienceClaw/backend/route/tooluniverse.py` 的 ToolUniverse 单例和 catalog 加载逻辑 |
| HTTPS MCP provider 来源 | 复用 `ScienceClaw/backend/mcp/repository.py`、`service.py`、`tool_factory.py` |
| External Tools provider 来源 | 复用根目录 `Tools/__init__.py` 的 AST 元数据和 `reload_external_tools()` |
| 测试 | 新增 `ScienceClaw/backend/tests/test_tool_discovery_index.py`、`test_tool_discovery_service.py` |

详细步骤：

1. 在 `schemas.py` 定义 `ToolIndexItem`。内部字段使用 `category_zh`，API 输出转换为 `cat_zh`。
2. 在 `aliases.py` 固定中文分类、同义词、专有名词保留表；内容必须和 `frontend/src/constants/toolCategories.ts` 对齐。
3. 在 `providers.py` 定义 provider 协议：`list_index_items(user_id)`、`get_info(tool_ref, user_id)`、`run(tool_ref, arguments, user_id)`。
4. ToolUniverse provider 的 `tool_ref` 固定为 `tooluniverse:{tool_name}`，`source_type` 固定为 `tooluniverse`。
5. HTTPS MCP provider 的 `tool_ref` 固定为 `https_mcp:{tool_id}`，只索引已验证、已启用、未移除且当前用户可见的工具。
6. External Python Tools provider 的 `tool_ref` 固定为 `external:{tool_name}`，只索引根目录 `Tools/*.py` 经现有 AST 解析得到的工具。
7. 在 `index_store.py` 使用 SQLite FTS5 建可重建索引，索引文件固定放在后端运行时缓存目录，不能成为权威数据源。
8. `service.py` 固定执行结构化过滤、查询归一化、FTS5 召回、规则重排、短结果裁剪。
9. 索引重建必须幂等；索引缺失或损坏时从 provider 原始来源重建。
10. 阶段 4 不改 `ScienceClaw/backend/deepagent/agent.py` 的 `_STATIC_TOOLS`。

测试口径与方法：

```bash
PYTHONNOUSERSITE=1 conda run -p D:/conda/envs/scienceclaw python -m pytest ScienceClaw/backend/tests/test_tool_discovery_index.py ScienceClaw/backend/tests/test_tool_discovery_service.py
PYTHONNOUSERSITE=1 conda run -p D:/conda/envs/scienceclaw python - <<'PY'
import sqlite3
conn = sqlite3.connect(':memory:')
conn.execute('CREATE VIRTUAL TABLE x USING fts5(name)')
print('fts5_ok')
PY
```

阶段退出标准：

1. `tool_discovery` 能返回 ToolUniverse、HTTPS MCP、External Python Tools 三类轻量索引项。
2. 搜索“论文”“医学论文”“药物毒性”“PDF 转换”能得到可解释候选。
3. `pip`/依赖文件不新增 embedding、向量数据库或 embedding SDK。
4. Agent 工具列表没有新增全量目录项。

### 阶段 5：通用三段式 adapter 与 API 落地

目标：新增统一 `tool_search`、`tool_info`、`tool_run` 入口；保留现有 ToolUniverse 三工具兼容；让扩展工具源统一走“检索 -> 获取信息 -> 运行”。

涉及工作面：

| 工作面 | 文件 |
| --- | --- |
| Agent adapter | 新增 `ScienceClaw/backend/deepagent/discovery_tools.py` |
| Agent 注入点 | 调整 `ScienceClaw/backend/deepagent/agent.py` 的 import、`_STATIC_TOOLS` 和 system prompt |
| 后端 API | 新增 `ScienceClaw/backend/route/tools.py`，调整 `ScienceClaw/backend/main.py` 注册 router |
| discovery service | 调整 `ScienceClaw/backend/tool_discovery/service.py` |
| 前端 API | 新增 `ScienceClaw/frontend/src/api/tools.ts` |
| 测试 | 新增 `ScienceClaw/backend/tests/test_deepagent_discovery_tools.py`，扩展 discovery service 测试 |

详细步骤：

1. 在 `deepagent/discovery_tools.py` 新增 LangChain/DeepAgents 可用工具函数 `tool_search`、`tool_info`、`tool_run`。
2. `tool_search` 签名固定为 `query, source_type=None, category_zh=None, limit=5, debug=False`；默认返回 `tool_ref`、`name`、`cat_zh`、`why`。
3. `tool_search(..., debug=True)` 只在显式传参时返回诊断字段；普通 Agent 流程和普通 Tools 页面不得传 `debug=True`。
4. `tool_info(tool_ref)` 只返回单个工具 schema、说明、限制、示例，不返回其他工具。
5. `tool_run(tool_ref, arguments)` 只接受结构化参数，根据 `tool_ref` prefix 分发到 provider。
6. `agent.py` 的 `_STATIC_TOOLS` 只新增三个通用 adapter；现有 `tooluniverse_search/info/run` 保留。
7. `agent.py` 的提示词必须写明：扩展工具先 `tool_search`，再 `tool_info`，最后 `tool_run`；不得请求全量工具目录，不得猜参数。
8. 新增 `route/tools.py` 暴露 `/tools/search`、`/tools/info/{tool_ref}`、`/tools/run`，并在 `main.py` 注册为 `/api/v1/tools/*`。
9. 前端 `api/tools.ts` 只封装统一 API；普通 Tools 页面默认不使用 debug 参数。
10. MCP 管理仍走 `/api/v1/mcp/*`；ToolUniverse 目录浏览仍走 `/api/v1/tooluniverse/*`；外置 Tools 管理仍走 `/api/v1/sessions/tools`。

测试口径与方法：

```bash
PYTHONNOUSERSITE=1 conda run -p D:/conda/envs/scienceclaw python -m pytest ScienceClaw/backend/tests -k "tool_discovery or discovery_tools or tooluniverse or mcp"
npm --prefix ScienceClaw/frontend run type-check
```

Agent 暴露面验收：

1. `_collect_tools()` 中 ToolUniverse 1,900+ catalog item 不出现。
2. 通用入口落地后，Agent 只增加 `tool_search`、`tool_info`、`tool_run` 三个稳定工具。
3. `tooluniverse_search/info/run` 仍可用。
4. 大规模工具源只通过索引和 provider 按需调用。

API 验收：

```bash
curl -s -X POST http://localhost:12001/api/v1/tools/search \
  -H 'Content-Type: application/json' \
  -d '{"query":"医学论文","limit":5}'
```

默认响应必须只包含短字段；带 `debug=true` 的请求才允许出现诊断字段。

### 阶段 6：文档、skill 与提示词对齐

目标：让 README、内置 skill、Agent 提示和 UI 行为对工具体系的描述一致。

涉及工作面：

| 工作面 | 文件 |
| --- | --- |
| 项目说明 | `README_zh.md`、必要时同步 `README.md` |
| 当前计划索引 | `docs/current-active-execution-plans-zh.md` |
| ToolUniverse skill | `ScienceClaw/backend/builtin_skills/tooluniverse/SKILL.md` 或当前实际 ToolUniverse skill 文件 |
| tool-creator skill | `ScienceClaw/backend/builtin_skills/tool-creator/SKILL.md` 或当前实际 tool 创建 skill 文件 |
| Agent 提示 | `ScienceClaw/backend/deepagent/agent.py` |

详细步骤：

1. README 工具体系说明固定写成：基础常用工具直接暴露；扩展工具源走三段式发现流程；ToolUniverse catalog 不等于 Agent tools。
2. `tool-creator` 文案固定写成：只有根目录 `Tools/*.py` 是外置 Python runtime tools；skill 内脚本不是 Agent runtime tools。
3. ToolUniverse skill 文案固定写成：使用 `tool_search/info/run` 或兼容 `tooluniverse_search/info/run`，不列出全量工具目录。
4. Agent system prompt 固定写明已有能力类别、三段式流程、禁止请求全量工具列表、禁止臆测参数。
5. `docs/current-active-execution-plans-zh.md` 指向本计划的当前阶段，并记录下一步只能从阶段 1 开始执行。

测试口径与方法：

```bash
rg -n "embedding|vector|全量工具|ToolUniverse|tool_search|tool_info|tool_run|Skills/.*/tools|builtin_skills/.*/scripts|Tools/\\*.py" README_zh.md README.md docs ScienceClaw/backend/builtin_skills ScienceClaw/backend/deepagent/agent.py
PYTHONNOUSERSITE=1 conda run -p D:/conda/envs/scienceclaw python -m pytest ScienceClaw/backend/tests -k "tool_discovery or discovery_tools"
npm --prefix ScienceClaw/frontend run build
```

阶段退出标准：

1. 文档、UI 和 Agent 提示对工具使用路径的描述一致。
2. 新用户能判断何时直接用基础工具、何时用 `tool_search/info/run`。
3. 文档中不存在“把 1,900+ ToolUniverse 工具直接暴露给 Agent”的表述。
4. 文档中不存在把 embedding 纳入默认方案或备选方案的表述。

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

## 阶段 1 实施记录

完成时间：2026-05-31

本阶段只做现状盘点，不改运行逻辑。扫描范围按阶段 1 指定文件执行：`ToolsPage.vue`、`ScienceToolDetail.vue`、`ToolDetailPage.vue`、`components/tools/*`、`components/settings/Mcp*`、`constants/tool.ts`、`useTool.ts`、`api/tooluniverse.ts`、`api/mcp.ts`、`types/event.ts`、`types/response.ts`、`locales/zh.ts`、`locales/en.ts`。

### 清单一：可翻译普通英文

以下普通英文属于 UI 文案、状态、动作或 fallback，阶段 2-3 必须通过 i18n 或中文分类合同治理，不得继续在中文界面直接展示：

| 工作面 | 当前发现 | 处理方式 |
| --- | --- | --- |
| Tools 主页面标题与搜索 | `Tools Library`、`Search tools...`、`All Tools` | 接入 i18n；中文分别落为工具库、搜索工具、全部工具 |
| Science tab 卡片 | `No description available`、`params`、`Has examples`、`Open`、`Show more`、`remaining`、`No tools match` | 接入 i18n；参数数量和剩余数量使用带 `{count}` 的 key |
| External tab 空态与卡片 | `Install tools via Skills or the sandbox CLI`、`No description`、`Blocked`、`Custom tool`、`Open` | 接入 i18n；`Skills` 保留原文，普通说明中文化 |
| 删除弹窗与详情 fallback | `Cancel`、`Error loading file` 等 | 已有部分 i18n key；缺失处补齐并统一调用 `t()` |
| ToolUniverse 详情页 | `ToolUniverse Scientific Tool`、`Description`、`Examples`、`Parameters`、`Running...`、`Run Tool`、`Copied!`、`Copy JSON`、`Fill in parameters and click "Run Tool"`、`Return Schema`、`Execution failed` | 接入 i18n；`ToolUniverse`、`JSON` 保留原文 |
| MCP 管理页统计与操作 | `Servers`、`Enabled`、`Healthy`、`Errors`、`Verify`、`Refresh tools`、`Edit`、`Add Server` | 已有部分 key；统计 label 目前仍在 script 中硬编码，阶段 3 改为 i18n |
| MCP server 表单 | `Endpoint URL`、`Auth Mode`、`Bearer Token`、`Token`、`Verify after save`、`Refresh tools after save`、`Save`、`Create` | 已有部分 key；缺失 key 补齐 |
| MCP schema 展示 | `This schema uses complex JSON Schema features. Pass arguments as a JSON object in payload.`、字段类型 fallback | 普通说明中文化；`JSON Schema`、`JSON` 保留原文 |
| 工具事件映射 | `Editing file`、`MCP Tool`、`File Edit` 等 | `constants/tool.ts` 中显示名阶段 3 中文化，legacy key 和图标映射保持兼容 |

### 清单二：必须保留原文的专有名词

以下名称是产品名、协议名、数据源名、文件格式或技术标识，显示层保留原文，只翻译周边普通文本：

| 类型 | 名称 |
| --- | --- |
| 项目与能力名 | `ScienceClaw`、`ToolUniverse`、`MCP`、`HTTPS MCP`、`DeepAgents`、`sandbox` |
| 学术与科学数据源 | `arXiv`、`OpenAlex`、`PubMed`、`Crossref`、`UniProt`、`PDB`、`AlphaFold`、`ChEMBL`、`FAERS`、`ClinicalTrials`、`COD`、`USGS`、`OpenMeteo`、`SIMBAD`、`SDSS`、`NASA`、`OpenML` |
| 格式与 schema | `PDF`、`DOCX`、`PPTX`、`XLSX`、`Markdown`、`SMILES`、`JSON`、`JSON Schema` |
| 技术标识 | 根目录 `Tools/*.py` 的函数名、MCP server 名、MCP tool 名、`tool_meta` 内的 `source_type`、`server_name`、`server_slug` |

### 清单三：分类来源字段

当前前端可用字段和阶段 2-3 处理方式如下：

| 来源 | 当前字段 | 处理方式 |
| --- | --- | --- |
| ToolUniverse 目录列表 | `TUTool.category`、`TUTool.category_zh`、`TUCategory.name`、`TUCategory.name_zh` | 优先展示 `category_zh`/`name_zh`；缺失时用阶段 2 `toolCategories.ts` 映射；仍无法确定时显示“其他”，不得直接展示普通英文 category |
| ToolUniverse 详情 | `TUToolSpec.category`、`TUToolSpec.category_zh` | 详情页 badge 同样走中文映射；专有名词保持原文 |
| External Python Tools | `ExternalToolItem.name`、`description`、`file`、`blocked` | 当前无分类字段；阶段 2-3 暂归“其他”或“文件与执行/技能与工具管理”的 UI 合同，不改变后端结构 |
| HTTPS MCP tools | `MCPTool.server_name`、`name`、`description`、`enabled`、`input_schema_raw`、`schema_summary` | 当前无中文分类字段；MCP 浏览与设置页只做普通文案中文化，阶段 4 再由 provider 生成 `category_zh` |
| 工具事件 | `ToolMetaData.name`、`category`、`description`、`mcp`、`source_type`、`server_name`、`server_slug`、`tool_id` | `useTool.ts` 继续优先 `tool_meta`；缺失时保留 legacy `mcp_` fallback；显示名阶段 3 中文化 |

阶段 1 退出结论：

1. Tools/MCP/ToolUniverse 可见英文已按“翻译、保留原文、删除/替换 fallback”归属。
2. 分类来源已明确为 ToolUniverse 字段优先、前端中文映射兜底、无字段来源暂不新增后端字段。
3. 本阶段未产生运行逻辑改动，后续只能从阶段 2 的 `toolCategories.ts` 静态合同开始推进。

## 阶段 2 实施记录

完成时间：2026-05-31

本阶段落地前端静态分类合同，仍不改变后端数据结构、不改变 Agent 工具暴露面。

已完成：

1. 新增 `ScienceClaw/frontend/src/constants/toolCategories.ts`，固定导出 13 个中文分类、显示顺序、专有名词保留表、中文/英文别名表。
2. `ToolsPage.vue` 的 Science tab 已使用中文分类合同展示 ToolUniverse 分类 badge 和侧栏分类；原始 `category` 只作为映射输入，不直接展示普通英文类别。
3. Science tab 本地过滤已纳入中文分类名和别名，可通过“论文”“医学论文”“药物毒性”“PDF 转换”等中文词命中对应分类。
4. `constants/tool.ts` 中部分工具事件显示名已中文化，并在 `zh.ts` / `en.ts` 补齐反向翻译，保证英文 locale 不直接显示中文 key。
5. 当前合同已参考 `ScienceClaw/backend/translations/tu_zh.json` 中真实 ToolUniverse category slug，增加 exact alias 和规则词根映射；无法确定时固定落入“其他”。

验证：

```bash
npm --prefix ScienceClaw/frontend run type-check
rg -n "医学论文|药物毒性|PDF|论文|pubmed|clinical_trials|cod_crystal|open_meteo|nasa_exoplanet" ScienceClaw/frontend/src/constants/toolCategories.ts
```

结果：type-check 通过；计划要求的中文检索词和代表性 ToolUniverse category slug 均有明确落点。

阶段 2 退出结论：

1. Tools 页面普通分类展示已收敛到中文分类合同。
2. 专有名词保留表已落地到前端常量，后续阶段不得生硬翻译这些名词。
3. 阶段 4 后端 `aliases.py` 必须与 `toolCategories.ts` 的分类名、别名和保留词保持一致。

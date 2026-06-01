# ScienceClaw 前端技术债复核报告 v2

**复核日期**：2026-06-01
**复核范围**：`ScienceClaw/frontend/src/`，以及与前端合同直接相关的 `ScienceClaw/backend/`、`ScienceClaw/task-service/`、Compose 配置和现有计划文档
**文档用途**：技术债事实清单和后续计划登记依据。本文不代表各批次已经进入执行态。

---

## 结论摘要

原报告识别出的组件体量、样式治理、前端测试基座和部分类型问题基本存在，但优先级和方案需要调整。

最重要的修正有四项：

1. `src/api/tooluniverse.ts` 当前直接返回 `resp.data` 是正确实现。后端 ToolUniverse 路由直接返回业务对象，没有 `ApiResponse.data` 包装。原报告建议改成 `resp.data.data`，会制造回归。
2. `tasks.ts` 和 `webhooks.ts` 确实重复创建 Axios 客户端，但“补 401 自动刷新”不是完整方案。`task-service` 当前路由没有用户认证依赖，也没有按当前用户过滤任务和 webhook。前端客户端整理只能作为清理项；跨服务认证和数据隔离需要单独审计。
3. `ChatPage.vue` 和 `ChatMessage.vue` 的大文件问题属实，但“渲染性能差”“加载性能差”尚未经过 profiling 证实。当前可以确认的是维护成本和测试难度偏高。
4. 前端缺少自动化测试基座属实，但全项目并非“没有任何测试”。后端已有测试集；前端当前仍以 `type-check + build + browser smoke` 作为主要闸门。

当前仓库还有一项已登记的活跃计划：VNC signed URL 接口闭环。执行新的技术债批次前，应先按 `docs/current-active-execution-plans-zh.md` 完成或重新排序该事项。

---

## 当前验证基线

### 已执行命令

```bash
cd ScienceClaw/frontend
npm run type-check
npm run build
npm outdated --json
```

### 结果

| 检查项 | 当前结果 |
| --- | --- |
| TypeScript | `npm run type-check` 通过 |
| Production build | `npm run build` 通过 |
| 构建提示 | Browserslist / `caniuse-lite` 数据约 14 个月未更新 |
| 前端自动化测试 | 未发现 Vitest、Jest 或 Playwright 测试文件和配置 |
| `any` 粗略计数 | `src/**/*.{ts,vue}` 中约 150 处文本命中，需要按边界分批治理 |
| GitNexus | 已运行 `npx gitnexus analyze --force --index-only --name ScienceClaw`；CLI 完成重建，但本次 MCP 查询仍提示 FTS 缺失，因此本文不使用 GitNexus 查询结果作为事实证据 |

---

## 优先级调整

| 顺序 | 主题 | 修订后等级 | 原因 |
| --- | --- | --- | --- |
| 0 | VNC signed URL 接口闭环 | 既有活跃计划 | 已在台账登记，先完成或明确延后 |
| 1 | Task Service 跨服务认证和用户隔离审计 | P0 | 当前前端会携带 token，但 task-service 路由未验证 token，也未按用户过滤数据 |
| 2 | 前端自动化测试基座 | P1 | 后续客户端整理和组件拆分都需要回归闸门 |
| 3 | HTTP 客户端边界整理 | P1 | 重复实现属实；方案必须服从跨服务认证结论 |
| 4 | 核心类型边界收紧 | P1 | 类型检查已通过，但共享合同仍存在宽泛 `any` |
| 5 | `ChatPage.vue` 渐进拆分 | P2 | 维护性问题属实；先抽纯函数和低耦合逻辑 |
| 6 | `ChatMessage.vue` 渐进拆分 | P2 | 优先拆 Markdown、数学公式、Mermaid 和代码块交互 |
| 7 | 颜色 token 分层治理 | P2 | 先定义 token 语义，再迁移硬编码颜色 |
| 8 | ESLint 和 Prettier 基线 | P2 | 有价值，但不应压过合同、隔离和测试基座 |
| 9 | Pinia 适用性评估 | P3 | 模块级 composable 单例可工作；只有在状态边界继续扩张时再迁移 |
| 10 | 依赖升级 | P3 | 单独立项，先处理 patch/minor，再评估 major migration |

---

## 1. Task Service 跨服务认证和用户隔离

### 判定：已证实，原报告遗漏了更重要的问题

前端 `src/api/tasks.ts` 和 `src/api/webhooks.ts` 分别创建 Axios 实例，并在请求拦截器中注入 bearer token：

- `ScienceClaw/frontend/src/api/tasks.ts:5-23`
- `ScienceClaw/frontend/src/api/webhooks.ts:4-22`

但 task-service 路由没有认证依赖：

- `ScienceClaw/task-service/app/main.py:34-35` 直接挂载 tasks 和 webhooks 路由
- `ScienceClaw/task-service/app/api/tasks.py:144-171` 列出全部任务
- `ScienceClaw/task-service/app/api/webhooks.py:46-49` 列出全部 webhook

任务 schema 虽然包含可选 `user_id`，但列表、读取、更新和删除接口没有使用它做访问控制：

- `ScienceClaw/task-service/app/models/task.py:10-33`
- `ScienceClaw/task-service/app/api/tasks.py:144-254`

### 原方案评估

原报告建议新建共享 `taskClient.ts` 并复用主站 token 刷新逻辑。这个方向只能减少前端重复代码，不能解决跨服务认证和用户数据隔离。主后端的 refresh endpoint 位于 `/api/v1/auth/refresh`，而 task-service 使用 `/task-service` 代理前缀；直接复制主客户端逻辑还需要明确 refresh 请求应该发往哪个服务。

### 修订方案

先登记独立后端审计计划，再整理前端客户端：

1. 明确 task-service 的信任模型：浏览器直连、主后端反向代理，或内部服务专用。
2. 若浏览器继续直连 task-service，增加 token 校验依赖，并让任务和 webhook 查询按当前用户过滤。
3. 明确管理员是否可以查看全量任务和 webhook。
4. 在认证合同确定后，新建 `src/api/taskClient.ts`，统一 task-service 的 base URL、超时、错误映射和认证策略。
5. 增加跨用户访问回归测试。

---

## 2. HTTP 客户端边界整理

### 判定：部分证实

项目确实有多个 Axios 实例：

| 客户端 | 位置 | 当前职责 |
| --- | --- | --- |
| 主 API 客户端 | `ScienceClaw/frontend/src/api/client.ts:37-43` | `/api/v1`，包含业务错误映射、401 refresh、SSE 支撑 |
| Tasks 客户端 | `ScienceClaw/frontend/src/api/tasks.ts:11-23` | `/task-service`，只注入 token |
| Webhooks 客户端 | `ScienceClaw/frontend/src/api/webhooks.ts:10-22` | `/task-service`，只注入 token |

Tasks 和 Webhooks 属于同一个 task-service，应共享客户端。主 API 与 task-service 是否共享 refresh 行为，要等第 1 节的跨服务认证结论。

### 需要删除的原结论

原报告要求把 `listTUTools()` 从 `return resp.data` 改成 `return resp.data.data`。该修改错误。

后端 `ScienceClaw/backend/route/tooluniverse.py:198-234` 直接返回：

```json
{
  "tools": [],
  "total": 0,
  "categories": []
}
```

因此 `ScienceClaw/frontend/src/api/tooluniverse.ts:53-54` 的 `return resp.data` 应保持不变。

### 修订方案

1. 只合并 `tasks.ts` 和 `webhooks.ts` 的 task-service 客户端。
2. 不改 ToolUniverse 解包逻辑。
3. 用测试覆盖 base URL、token header、错误映射和认证失效行为。

---

## 3. 前端自动化测试基座

### 判定：已证实，但原范围过宽

`ScienceClaw/frontend/package.json:6-10` 只有 `dev`、`build`、`type-check`、`preview` 脚本。前端目录中未发现 Vitest、Jest 或 Playwright 测试配置和测试文件。

原报告写成“项目中没有任何测试文件、测试配置或测试依赖”不准确。后端已有 `ScienceClaw/backend/tests/`，现有 MCP 完成审计也记录过后端测试和前端 smoke 闸门：

- `ScienceClaw/backend/tests/`
- `docs/archive/plans/mcp-https-integration-completion-audit-zh.md:34-47`

### 原方案评估

引入 Vitest 和 `@vue/test-utils` 的方向合理。原方案同时引入 `jsdom` 和 `happy-dom`，但只配置 `happy-dom`，没有必要一次安装两套 DOM 环境。示例测试还依赖尚未存在的 Pinia store，不能作为第一批测试。

### 修订方案

第一批只建立可运行的前端测试基线：

1. 安装 `vitest`、`@vue/test-utils`、`happy-dom` 和覆盖率 provider。
2. 增加 `test`、`test:run`、`test:coverage` 脚本。
3. 先覆盖纯函数和边界稳定的模块：
   - `src/utils/content.ts`
   - `src/utils/fileType.ts`
   - `src/composables/useSessionSearch.ts`
   - task-service 客户端错误映射
4. 保留 `npm run type-check`、`npm run build` 和浏览器 smoke。
5. CI 集成另行核验；本文不假设仓库已有前端 CI workflow。

---

## 4. 核心类型边界收紧

### 判定：已证实，但不是“TypeScript 形同虚设”

当前 `npm run type-check` 已通过，说明类型检查仍在发挥作用。共享类型中确实存在宽泛 `any`：

- `ScienceClaw/frontend/src/types/message.ts:27-28`
- `ScienceClaw/frontend/src/types/event.ts:44-45`
- `ScienceClaw/frontend/src/api/client.ts:60-62`
- `ScienceClaw/frontend/src/composables/useSessionNotifications.ts:8-19`

`src/**/*.{ts,vue}` 中约有 150 处 `any` 文本命中。这个数字只能作为治理规模参考，不能直接等价成 150 个缺陷。

### 原方案评估

原报告建议为工具参数定义只包含 `string | number | boolean | string[] | number[] | undefined` 的 `ToolArgs`。该类型过窄。工具参数可能包含嵌套对象、数组和 `null`；强行收窄会把合法 ToolUniverse、MCP 或 sandbox 参数排除。

### 修订方案

1. 先定义可递归 JSON 类型：

```ts
export type JsonPrimitive = string | number | boolean | null;
export type JsonValue = JsonPrimitive | JsonValue[] | { [key: string]: JsonValue };
```

2. 用 `Record<string, JsonValue>` 收紧工具参数。
3. 工具结果先用 `unknown`，在具体视图或 adapter 处做 narrowing。
4. 为 Axios refresh queue 定义明确的 queue item 类型。
5. 按协议边界、工具渲染、页面局部变量三批处理，不做全仓机械替换。

---

## 5. 错误可观测性和用户反馈

### 判定：部分证实

`ScienceClaw/frontend/src/main.ts:115-119` 没有配置 `app.config.errorHandler`。`ScienceClaw/frontend/src/composables/useSessionNotifications.ts:39-51` 会自动重连，但不会记录连接错误。`ScienceClaw/frontend/src/pages/ChatPage.vue:1166-1200` 已记录聊天 SSE 错误。

### 需要删除的原结论

以下表述缺少证据：

- “没有全局错误捕获机制，未捕获异常会导致白屏”
- “未捕获 Promise rejection 会导致内存泄漏”
- “SSE 连接中断后错误静默吞没”

代码只能证明部分错误缺少统一记录或用户提示。不能从当前源码推导出必然白屏或内存泄漏。

### 修订方案

1. 先定义错误分类：可恢复请求错误、认证失效、SSE 重连、渲染异常、不可恢复启动错误。
2. 给 `useSessionNotifications` 增加结构化日志，并避免重复重连计时器。
3. 在 Vue 全局 handler 中记录渲染异常；只有用户可以采取行动时才显示 toast。
4. `unhandledrejection` 监听器只做记录和上报，不默认调用 `preventDefault()`。
5. 用故障注入验证：后端离线、401、畸形 SSE event、组件渲染异常。

---

## 6. `ChatPage.vue` 渐进拆分

### 判定：已证实的维护性问题

`ScienceClaw/frontend/src/pages/ChatPage.vue` 当前有 1819 行，承担页面布局、会话内搜索、Activity、Plan、SSE、消息发送、恢复、分享和保存提示。

关键区域：

| 职责 | 位置 |
| --- | --- |
| 页面状态 | `ScienceClaw/frontend/src/pages/ChatPage.vue:379-510` |
| 会话内搜索接线 | `ScienceClaw/frontend/src/pages/ChatPage.vue:439-619` |
| SSE 和消息合并 | `ScienceClaw/frontend/src/pages/ChatPage.vue:640-1053` |
| `chat()` | `ScienceClaw/frontend/src/pages/ChatPage.vue:1063-1204` |
| `restoreSession()` | `ScienceClaw/frontend/src/pages/ChatPage.vue:1206-1320` |
| 分享逻辑 | `ScienceClaw/frontend/src/pages/ChatPage.vue:1474-1566` |

### 需要删除的原结论

“组件渲染性能差”没有 profiling 证据。当前可以确认的是改动半径大、测试困难、协议逻辑和视图状态耦合。

### 修订方案

不要一次把 `chat()`、恢复和全部 SSE 状态迁移到多个 composable。先提取低风险边界：

1. 提取事件归一化和消息合并纯函数，并加单元测试。
2. 提取分享逻辑。
3. 保留现有 `useSessionSearch.ts`，只清理页面接线。
4. 提取 Activity snapshot 和 Plan 合并 helper。
5. 最后再评估 `useChatSession` 和 `useSSEEventHandler`。这一步需要以自动化测试和浏览器长会话 smoke 为前置条件。

不把“页面必须少于 600 行”作为验收条件。验收应关注职责边界、行为保持和测试覆盖。

---

## 7. `ChatMessage.vue` 渐进拆分

### 判定：已证实的维护性问题

`ScienceClaw/frontend/src/components/ChatMessage.vue` 当前有 1801 行。文件中同时包含：

- 消息模板和 footer
- Markdown renderer
- DOMPurify 配置和 hook
- KaTeX 预处理
- Mermaid 动态加载和渲染
- 代码块复制交互
- 约 880 行样式

关键位置：

- `ScienceClaw/frontend/src/components/ChatMessage.vue:150-216`
- `ScienceClaw/frontend/src/components/ChatMessage.vue:217-559`
- `ScienceClaw/frontend/src/components/ChatMessage.vue:656-710`
- `ScienceClaw/frontend/src/components/ChatMessage.vue:918-1801`

### 需要删除的原结论

“即使只看纯文本也会加载全部渲染逻辑”需要改成风险描述。`ChatPage.vue:361` 已异步加载 `ChatMessage`，Mermaid 也采用动态 import。当前 build 输出显示 `ChatMessage` chunk 约 40 kB，CSS 约 25 kB；是否影响真实体验仍需 profiling。

### 修订方案

优先提取高复杂度 renderer，不先拆出空壳消息组件：

1. `useMarkdownRenderer.ts`
2. `useMathRenderer.ts`
3. `useMermaidRenderer.ts`
4. `MessageFooter.vue`
5. 独立样式文件或可维护的样式分区

当前 `tool` 和 `step` 分支在 `ChatMessage.vue:141-143` 中隐藏，真正渲染由其他组件承担。原报告建议新增 `ToolMessage.vue`、`StepMessage.vue`，收益有限。

---

## 8. 颜色 token 分层治理

### 判定：已证实

`ScienceClaw/frontend/src/assets/theme.css:1-177` 已定义 light/dark 语义变量，但组件中仍存在硬编码颜色和 Tailwind 任意值。

粗略统计：

| 文件 | 颜色文本命中 |
| --- | ---: |
| `ScienceClaw/frontend/src/components/ChatMessage.vue` | 128 |
| `ScienceClaw/frontend/src/components/MarkdownEnhancements.vue` | 31 |
| `ScienceClaw/frontend/src/pages/ChatPage.vue` | 38 |
| `ScienceClaw/frontend/src/components/FilePanel.vue` | 1 |

这些命中包含有意保留的语义色、渐变和透明度值，不能全部机械替换。

### 原方案评估

“统一到 CSS 变量”的方向合理，但需要先定义 token 层级。否则只会把硬编码从组件移动到 `theme.css`。

### 修订方案

1. 定义 `brand`、`surface`、`border`、`text`、`semantic-state`、`code`、`diagram` token。
2. 先迁移 `ChatMessage.vue` 和 `MarkdownEnhancements.vue`。
3. Tailwind 配置只映射稳定 token；实验性渐变保留局部命名。
4. 用 light/dark 浏览器 smoke 和截图回归验证。

---

## 9. ESLint 和 Prettier 基线

### 判定：已证实，但优先级应下调

`ScienceClaw/frontend/package.json:31` 已安装 `prettier`，但它位于 runtime dependencies。前端根目录未发现项目级 ESLint、Prettier 或 EditorConfig 配置。

### 原方案评估

引入 lint 和 format 脚本合理。原报告建议直接使用 `.eslintrc.js` 和 ESLint 8 版本段，容易把旧配置格式固化进新项目。应在执行时按所选 ESLint 主版本决定 flat config 或 legacy config。

Husky 和 lint-staged 不应与基础 lint 配置同批落地。先让现有代码在 CI 或本地命令下达到可接受基线，再决定是否添加提交钩子。

### 修订方案

1. 把 `prettier` 和 `@types/dompurify` 从 runtime dependencies 移到 devDependencies。
2. 选择 ESLint 主版本后创建对应配置。
3. 先增加只检查不改写的 `lint` 和 `format:check`。
4. 单独评估 `lint:fix`、Husky 和 lint-staged。
5. 不要求第一批清零全部 warning；先锁定新增代码不继续扩大问题。

---

## 10. Pinia 适用性评估

### 判定：存在评估价值，不应直接立项迁移

项目没有使用 Pinia 或 Vuex。多个 composable 使用模块级 `ref` 提供共享状态：

- `ScienceClaw/frontend/src/composables/useTheme.ts:3-40`
- `ScienceClaw/frontend/src/composables/useLeftPanel.ts:18-62`
- `ScienceClaw/frontend/src/composables/useFilePanel.ts:7-70`
- `ScienceClaw/frontend/src/composables/useRightPanel.ts:5-38`
- `ScienceClaw/frontend/src/composables/useSessionFileList.ts:3-21`
- `ScienceClaw/frontend/src/composables/useSettingsDialog.ts:3-34`

这种模式不是缺陷本身。它适合小型共享 UI 状态。需要治理的是状态归属、生命周期和可观察性。

### 需要删除的原结论

“模块级 ref 在 HMR 时有内存泄漏风险”只能作为待验证风险。`useSessionNotifications.ts:91-100` 已在无订阅者时清理连接，当前源码不能证明发生泄漏。

### 修订方案

1. 先列出跨组件共享状态和所有者。
2. 为事件订阅、timer、连接和 localStorage side effect 增加清理测试。
3. 只有当状态需要 DevTools、SSR 隔离、复杂派生状态或跨页面一致性时，再迁移到 Pinia。
4. 若迁移，先做 Auth 或 Panel 单一 store，不一次替换全部 composable。

---

## 11. 依赖升级

### 判定：需要单独立项，原版本口径过时

`ScienceClaw/frontend/package.json` 的声明范围和 `package-lock.json` 的已安装版本不同。执行升级前必须同时核对两者。

2026-06-01 运行 `npm outdated --json` 得到的主要结果：

| 依赖 | package.json 声明 | 当前安装 | npm registry latest | 建议 |
| --- | --- | --- | --- | --- |
| `vue` | `^3.3.4` | `3.5.13` | `3.5.35` | 先更新声明和 patch/minor |
| `vite` | `^4.3.9` | `4.5.13` | `8.0.14` | 单独评估 major migration |
| `tailwindcss` | `^3.3.2` | `3.4.17` | `4.3.0` | Tailwind 4 单独立项 |
| `@vitejs/plugin-vue` | `^4.2.3` | `4.6.2` | `6.0.7` | 随 Vite migration 评估 |
| `axios` | `^1.8.4` | `1.8.4` | `1.16.1` | 先评估 patch/minor |
| `vue-i18n` | `^9.14.4` | `9.14.4` | `11.4.4` | 单独阅读迁移说明 |

### 原方案评估

原报告把“升级到 Vite 5”写成低影响步骤，还建议为 `defineModel` 增加 plugin 配置。当前代码没有证明需要该配置。`vite.config.ts` 还包含 Monaco CSS workaround、manualChunks 和代理设置，升级不能只改版本号。

### 修订方案

1. 先更新 Browserslist 数据。
2. 单独处理安全修复和 patch/minor 更新。
3. 为 Vite、Tailwind、Vue Router、Vue I18n 的 major migration 分别建评估单。
4. 每次升级都执行：

```bash
npm run type-check
npm run build
```

并补充浏览器 smoke。涉及 Tailwind 或组件库时增加 light/dark 截图对比。

---

## 后续执行拆分

后续如果进入实现阶段，每个计划都应登记到 `docs/current-active-execution-plans-zh.md`，并按最小可验证增量推进。

建议拆成以下独立计划：

| 计划 | 第一批最小增量 | 核心验收 |
| --- | --- | --- |
| Task Service 认证和隔离审计 | 明确信任模型，增加跨用户合同测试 | 未授权请求失败；用户只能看到自己的任务和 webhook |
| 前端测试基座 | Vitest + 一个纯函数测试 + 一个 composable 测试 | `npm run test:run` 通过 |
| Task Service 客户端整理 | 合并 tasks/webhooks 客户端 | type-check、build、认证失效测试 |
| 类型边界治理 | JSON 类型 + refresh queue 类型 | type-check、相关单测 |
| ChatPage 渐进拆分 | 提取纯函数 | 长会话 smoke、消息/Plan 行为不变 |
| ChatMessage 渐进拆分 | 提取 renderer | Markdown、KaTeX、Mermaid、复制代码 smoke |
| 样式 token 治理 | token 分类和首批迁移 | light/dark 截图对比 |
| 前端工程基线 | lint + format:check | 新增代码不扩大 lint 问题 |
| 依赖升级 | Browserslist 和 patch/minor 更新 | type-check、build、浏览器 smoke |

---

## 边界说明

本文复核前端技术债时发现了 task-service 的跨服务认证和隔离问题。它涉及后端，但会直接决定前端 HTTP 客户端方案，因此必须列入审计结论。

本文没有修改业务代码，也没有把以上事项登记成活跃执行计划。进入实现阶段前，需要先核对现有 VNC signed URL 活跃计划的排序。

---

**复核状态**：已完成
**下一步**：从台账中选择一个最小批次进入执行

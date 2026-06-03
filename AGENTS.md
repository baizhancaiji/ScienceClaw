# ScienceClaw AI Agent Instructions

Welcome to the ScienceClaw project! This guide provides context and conventions to help AI agents be immediately productive in this repository.

## 🏗️ Project Architecture
ScienceClaw is a personal scientific research assistant based on [LangChain DeepAgents] and an AIO Sandbox.
- **Frontend** (`./ScienceClaw/frontend/`): Vue 3 + TypeScript + Vite. TailwindCSS for styling.
- **Backend** (`./ScienceClaw/backend/`): Python + FastAPI + Motor (MongoDB Async). Includes WebSocket/SSE logic and LangChain integrations.
- **Sandbox** (`./ScienceClaw/sandbox/`): Isolate code execution environment (Python).
- **WebSearch** (`./ScienceClaw/websearch/`): Crawler and search service.
- **Task Service** (`./ScienceClaw/task-service/`): Scheduler API.
- **Infrastructure**: MongoDB (Main DB), Redis, SearXNG.

## 🛠️ Build and Test Commands
The project heavily relies on Docker Compose for local environments. Never run components locally on the host unless debugging specific scripts.
- **Domestic users (China)**: `docker compose -f docker-compose-china.yml up -d --build` (See [Deployment Guide](docs/deployment-guide-zh.md)).
- **Standard release**: `docker compose -f docker-compose-release.yml up -d --pull always`.
- Generated files and local executions are safely contained inside the `./workspace` directory.
- **Local Python environment**: When a host-side Python command is needed for tests, import probes, or lightweight debugging, use the project Conda environment at `D:\conda\envs\scienceclaw`. Prefer `conda run -p D:\conda\envs\scienceclaw ...` and set `PYTHONNOUSERSITE=1` so commands do not fall back to user-level packages from `C:\Users\keepoux\AppData\Roaming\Python`. Do not use the old `C:\ProgramData\miniconda3\envs\py312` environment for this repository.

## 📝 Conventions
- **DO NOT** edit code directly inside the Docker containers. Edit local files and allow volume mounts or rebuilds to sync changes.
- **Link, don't embed**: For detailed project initialization, always refer to [README_zh.md](README_zh.md) and [Deployment Guide](docs/deployment-guide-zh.md).
- **Codex App in-app browser**: When a task explicitly requires the internal/in-app browser, follow [CODEX_IN_APP_BROWSER.md](CODEX_IN_APP_BROWSER.md); do not substitute `mcp__playwright__` evidence for in-app browser verification.
- **Active plans ledger**: Current execution plans are tracked in [docs/current-active-execution-plans-zh.md](docs/current-active-execution-plans-zh.md). Completed plans are archived under `docs/archive/plans/`; do not execute directly from archived plans without re-registering a new active plan.
- **Internationalization is mandatory for new functionality/components**: Any new user-facing feature, component, route, dialog, button, tooltip/title/aria-label, toast, empty state, validation message, error message, status label, or backend-originated user-visible message must use the existing i18n/locales mechanism. Do not hardcode display text in components or return raw backend/sandbox exception text to users; add/update locale keys in both `ScienceClaw/frontend/src/locales/zh.ts` and `ScienceClaw/frontend/src/locales/en.ts` when adding new UI text.
- **GitNexus workflow**: This repository uses GitNexus for code-intelligence gates. Before non-trivial code changes, use GitNexus query/context/impact when symbol ownership or blast radius is unclear. Before each local commit that changes code, run `gitnexus detect-changes` and treat the result as required review input. After initializing GitNexus or after broad structural changes, refresh the index with `gitnexus analyze --force --index-only --name ScienceClaw`.
- **Agents/Skills/Tools**:
  - Python-based tools belong in the `Tools/` directory.
  - LLM Skills (e.g., prompt definitions, workflows) belong in the `Skills/` directory.

## 💡 Potential Pitfalls
- **Port Conflicts**: Ensure ports `5173` (Frontend), `12001` (Backend), `18080`, `8068`, `27014`, `26080` are free before running Docker.
- **Sandbox Build Time**: Initializing the sandbox container takes a long time (20-40 mins) as it includes Playwright browsers. Be mindful of full rebuilds.

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **ScienceClaw** (15680 symbols, 26118 relationships, 300 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` in terminal first.

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `gitnexus_impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `gitnexus_detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `gitnexus_context({name: "symbolName"})`.

## Never Do

- NEVER edit a function, class, or method without first running `gitnexus_impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands the call graph.
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope.

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/ScienceClaw/context` | Codebase overview, check index freshness |
| `gitnexus://repo/ScienceClaw/clusters` | All functional areas |
| `gitnexus://repo/ScienceClaw/processes` | All execution flows |
| `gitnexus://repo/ScienceClaw/process/{name}` | Step-by-step execution trace |

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->

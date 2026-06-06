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
- **Agents/Skills/Tools**:
  - Python-based tools belong in the `Tools/` directory.
  - LLM Skills (e.g., prompt definitions, workflows) belong in the `Skills/` directory.

## 💡 Potential Pitfalls
- **Port Conflicts**: Ensure ports `5173` (Frontend), `12001` (Backend), `18080`, `8068`, `27014`, `26080` are free before running Docker.
- **Sandbox Build Time**: Initializing the sandbox container takes a long time (20-40 mins) as it includes Playwright browsers. Be mindful of full rebuilds.

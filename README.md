Nova Writer AI

[English](#english) | [中文](#中文)

# English

Nova Writer AI is a multi-agent novel writing system with streaming output, resumable workflows, and persistent chat history. It includes a web frontend, backend API, and an AI microservice.

Key Features
- Multi-agent workflow: Director, Writer, Critic, Archivist
- Streaming output with pause/cancel and resume
- Auto-save generated chapters with summaries
- Chat history and workflow steps stored in the database
- Docker-first deployment

Quick Start (Docker)
1. Create `.env` at repo root and set required values.
2. Refer to `backend/.env.example` and `nova-ai-service/.env.example`.
3. Run:
   - `docker compose up -d --build`

Required Environment Variables
- `GEMINI_API_KEY` (required)
- `GEMINI_PROXY` (optional)
- `SECRET_KEY` (required in production)
- `NEO4J_PASSWORD` (if Neo4j is enabled)

Project Layout
- `backend/` API server
- `nova-ai-service/` AI microservice
- `novawrite-ai---professional-novel-assistant/` frontend
- `docs/` root documentation
- `scripts/` shared scripts

Documentation Index
Root docs (`docs/`)
- `docs/START_HERE.md`
- `docs/本地启动说明.md`
- `docs/AI_MICROSERVICE_SETUP.md`
- `docs/WARP_SETUP_INSTRUCTIONS.md`
- `docs/PROJECT_STRUCTURE.md`
- `docs/AUDIT_SYSTEM_DESIGN.md`
- `docs/SECURITY_AUDIT_REPORT.md`
- `docs/CHAPTER_COHERENCE_ISSUE_ANALYSIS.md`
- `docs/FIX_CHAPTER_COHERENCE_SUMMARY.md`

Backend docs (`backend/`)
- `backend/docs/README.md`
- `backend/docs/API_AUTHENTICATION.md`
- `backend/GEMINI_PROXY_SETUP.md`
- `backend/MIGRATION_GUIDE.md`
- `backend/BACKEND_STRUCTURE.md`
- `backend/FILE_ORGANIZATION.md`
- `backend/FINAL_ORGANIZATION.md`
- `backend/ORGANIZATION_SUMMARY.md`
- `backend/FILES_TO_DELETE.md`
- `backend/STRUCTURE_TEST_SUMMARY.md`
- `backend/TEST_RESULTS.md`
- `backend/VECTOR_DATABASE_USAGE.md`
- `backend/VECTOR_CONTEXT_IN_PROMPT.md`

AI service docs (`nova-ai-service/`)
- `nova-ai-service/README.md`
- `nova-ai-service/QUICK_START.md`
- `nova-ai-service/IMPLEMENTATION_SUMMARY.md`

Frontend docs (`novawrite-ai---professional-novel-assistant/`)
- `novawrite-ai---professional-novel-assistant/docs/README.md`
- `novawrite-ai---professional-novel-assistant/docs/DEPLOY.md`
- `novawrite-ai---professional-novel-assistant/docs/TROUBLESHOOTING.md`
- `novawrite-ai---professional-novel-assistant/docs/API_DIAGNOSTIC.md`
- `novawrite-ai---professional-novel-assistant/docs/QUICK_FIX.md`

Scripts
- `scripts/root/deploy-full.ps1`
- `scripts/root/view-logs.ps1`
- `scripts/start_local.bat`
- `scripts/start_local.sh`
- `scripts/stop_local.sh`
- `backend/scripts/`
- `novawrite-ai---professional-novel-assistant/scripts/`

License
CC BY-NC 4.0. See `LICENSE`.

# 中文

Nova Writer AI 是面向长篇小说创作的多 Agent 写作系统，支持流式输出、流程可中断/可恢复，并将对话与流程步骤持久化到数据库。项目由前端、后端 API 与 AI 微服务组成。

主要特性
- 多 Agent 协作：导演/作家/评论/存档
- 流式输出，支持停止与恢复
- 写作结果自动入库并生成摘要
- 对话记录与流程步骤持久化
- Docker 优先部署

快速开始（Docker）
1. 在仓库根目录创建 `.env` 并填写必要参数。
2. 参考 `backend/.env.example` 与 `nova-ai-service/.env.example`。
3. 启动：
   - `docker compose up -d --build`

关键环境变量
- `GEMINI_API_KEY`（必填）
- `GEMINI_PROXY`（可选）
- `SECRET_KEY`（生产环境必填）
- `NEO4J_PASSWORD`（启用 Neo4j 时需要）

目录结构
- `backend/` 后端 API
- `nova-ai-service/` AI 微服务
- `novawrite-ai---professional-novel-assistant/` 前端
- `docs/` 根目录文档汇总
- `scripts/` 通用脚本

文档索引
根目录文档（`docs/`）
- `docs/START_HERE.md`
- `docs/本地启动说明.md`
- `docs/AI_MICROSERVICE_SETUP.md`
- `docs/WARP_SETUP_INSTRUCTIONS.md`
- `docs/PROJECT_STRUCTURE.md`
- `docs/AUDIT_SYSTEM_DESIGN.md`
- `docs/SECURITY_AUDIT_REPORT.md`
- `docs/CHAPTER_COHERENCE_ISSUE_ANALYSIS.md`
- `docs/FIX_CHAPTER_COHERENCE_SUMMARY.md`

后端文档（`backend/`）
- `backend/docs/README.md`
- `backend/docs/API_AUTHENTICATION.md`
- `backend/GEMINI_PROXY_SETUP.md`
- `backend/MIGRATION_GUIDE.md`
- `backend/BACKEND_STRUCTURE.md`
- `backend/FILE_ORGANIZATION.md`
- `backend/FINAL_ORGANIZATION.md`
- `backend/ORGANIZATION_SUMMARY.md`
- `backend/FILES_TO_DELETE.md`
- `backend/STRUCTURE_TEST_SUMMARY.md`
- `backend/TEST_RESULTS.md`
- `backend/VECTOR_DATABASE_USAGE.md`
- `backend/VECTOR_CONTEXT_IN_PROMPT.md`

AI 微服务文档（`nova-ai-service/`）
- `nova-ai-service/README.md`
- `nova-ai-service/QUICK_START.md`
- `nova-ai-service/IMPLEMENTATION_SUMMARY.md`

前端文档（`novawrite-ai---professional-novel-assistant/`）
- `novawrite-ai---professional-novel-assistant/docs/README.md`
- `novawrite-ai---professional-novel-assistant/docs/DEPLOY.md`
- `novawrite-ai---professional-novel-assistant/docs/TROUBLESHOOTING.md`
- `novawrite-ai---professional-novel-assistant/docs/API_DIAGNOSTIC.md`
- `novawrite-ai---professional-novel-assistant/docs/QUICK_FIX.md`

脚本
- `scripts/root/deploy-full.ps1`
- `scripts/root/view-logs.ps1`
- `scripts/start_local.bat`
- `scripts/start_local.sh`
- `scripts/stop_local.sh`
- `backend/scripts/`
- `novawrite-ai---professional-novel-assistant/scripts/`

许可证
本项目使用 CC BY-NC 4.0 许可协议，详见 `LICENSE`。

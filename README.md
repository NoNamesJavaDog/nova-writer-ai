Nova Writer AI

一套面向长篇小说创作的多 Agent 工作流系统，包含写作端前端、后端服务与 AI 服务，支持流式输出、流程可中断/可恢复、章节自动入库与对话历史持久化。

特性
- 多 Agent 流程：导演/作家/评论/存档协作
- 流式输出与可中断/可恢复
- 写作结果自动写入章节并生成摘要
- 对话记录与流程步骤写入数据库
- Docker 统一部署

快速开始（Docker）
1. 复制环境变量模板并填写关键参数：
   - `.env`（仓库根目录）
   - `backend/.env.example` 和 `nova-ai-service/.env.example` 作为参考
2. 启动：
   - `docker compose up -d --build`

重要环境变量
- `GEMINI_API_KEY`：必填
- `GEMINI_PROXY`：可选（代理）
- `SECRET_KEY`：生产环境必须修改
- `NEO4J_PASSWORD`：如启用图数据库需设置

目录结构
- `backend/` 后端 API
- `nova-ai-service/` AI 微服务
- `novawrite-ai---professional-novel-assistant/` 前端
- `docs/` 根目录文档汇总
- `scripts/` 通用脚本

文档索引
根目录文档（docs/）
- `docs/START_HERE.md` 快速上手
- `docs/本地启动说明.md` 本地启动说明
- `docs/AI_MICROSERVICE_SETUP.md` AI 服务配置
- `docs/WARP_SETUP_INSTRUCTIONS.md` 代理配置
- `docs/PROJECT_STRUCTURE.md` 项目结构
- `docs/AUDIT_SYSTEM_DESIGN.md` 系统设计审计
- `docs/SECURITY_AUDIT_REPORT.md` 安全审计报告
- `docs/CHAPTER_COHERENCE_ISSUE_ANALYSIS.md` 一致性问题分析
- `docs/FIX_CHAPTER_COHERENCE_SUMMARY.md` 修复总结

后端文档（backend/）
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

AI 微服务文档（nova-ai-service/）
- `nova-ai-service/README.md`
- `nova-ai-service/QUICK_START.md`
- `nova-ai-service/IMPLEMENTATION_SUMMARY.md`

前端文档（novawrite-ai---professional-novel-assistant/）
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
- `backend/scripts/` 后端运维脚本
- `novawrite-ai---professional-novel-assistant/scripts/` 前端部署脚本

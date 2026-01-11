# AI 微服务架构 - 启动指南

## 架构概述

项目已成功重构为微服务架构：

```
┌─────────────────────────────────────────────────────────────┐
│                      用户请求                                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│            主应用（FastAPI Backend）:8000                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  业务逻辑层                                             │  │
│  │  - 用户认证                                             │  │
│  │  - 小说管理                                             │  │
│  │  - 向量检索（ConsistencyChecker）                       │  │
│  │  - 数据库操作                                           │  │
│  └──────────────────────────────────────────────────────┘  │
│                       │                                      │
│                       │ HTTP 调用                             │
│                       ▼                                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  AIServiceClient（适配器）                             │  │
│  │  - 微服务客户端                                         │  │
│  │  - 保持原有函数签名                                     │  │
│  │  - 保留向量检索逻辑                                     │  │
│  └──────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            │ REST API
                            ▼
┌─────────────────────────────────────────────────────────────┐
│            AI 微服务（nova-ai-service）:8001                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  纯 AI 调用，无业务逻辑                                │  │
│  │  - GeminiProvider                                    │  │
│  │  - ClaudeProvider（预留）                            │  │
│  │  - OpenAIProvider（预留）                            │  │
│  │  - 16 个 API 端点                                     │  │
│  │  - 支持流式响应（SSE）                                │  │
│  └──────────────────────────────────────────────────────┘  │
│                       │                                      │
│                       │ 调用                                  │
│                       ▼                                      │
│              Gemini API / Claude API / OpenAI API           │
└─────────────────────────────────────────────────────────────┘
```

## 快速启动

### 方式 1：Docker Compose（推荐）

**前提条件**：
- Docker 和 Docker Compose 已安装
- 已获取 Gemini API Key

**步骤**：

1. **配置环境变量**
```bash
# 在项目根目录创建 .env 文件
cat > .env << EOF
GEMINI_API_KEY=your-gemini-api-key-here
GEMINI_PROXY=http://127.0.0.1:40000
SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
EOF
```

2. **启动所有服务**
```bash
docker-compose up --build
```

3. **验证服务**
```bash
# 检查 AI 微服务健康状态
curl http://localhost:8001/health

# 检查主应用健康状态
curl http://localhost:8000/health
```

**服务访问地址**：
- **AI 微服务**: http://localhost:8001
  - Swagger UI: http://localhost:8001/docs
  - ReDoc: http://localhost:8001/redoc
- **主应用**: http://localhost:8000
  - API 文档: http://localhost:8000/docs
- **数据库**: localhost:5432

---

### 方式 2：本地开发模式

**步骤**：

#### 1. 启动 AI 微服务

```bash
# 进入微服务目录
cd nova-ai-service

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，添加你的 GEMINI_API_KEY

# 启动服务
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

#### 2. 启动主应用

```bash
# 在新终端窗口，进入主应用目录
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，确保以下配置：
# AI_SERVICE_URL=http://localhost:8001
# GEMINI_API_KEY=your-key-here

# 启动服务
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

---

## API 测试

### 1. 测试 AI 微服务（直接调用）

```bash
# 生成完整大纲
curl -X POST http://localhost:8001/api/v1/outline/generate-full \
  -H "Content-Type: application/json" \
  -H "X-Provider: gemini" \
  -d '{
    "title": "星际探险记",
    "genre": "科幻",
    "synopsis": "一个关于太空探险的故事"
  }'

# 流式生成章节内容
curl -X POST http://localhost:8001/api/v1/chapter/write-content-stream \
  -H "Content-Type: application/json" \
  -H "X-Provider: gemini" \
  -d '{
    "novel_title": "星际探险记",
    "genre": "科幻",
    "synopsis": "一个关于太空探险的故事",
    "chapter_title": "第一章 启程",
    "chapter_summary": "主角登上飞船，开始太空之旅",
    "chapter_prompt_hints": "",
    "characters": [],
    "world_settings": []
  }'
```

### 2. 测试主应用（通过适配器）

```bash
# 生成小说大纲（会自动调用微服务）
curl -X POST http://localhost:8000/api/ai/generate-outline \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-jwt-token" \
  -d '{
    "title": "星际探险记",
    "genre": "科幻",
    "synopsis": "一个关于太空探险的故事",
    "novel_id": "some-uuid"
  }'
```

---

## 架构优势

### ✅ 已实现的特性

1. **业务逻辑分离**
   - AI 微服务：纯 AI API 调用，无业务逻辑
   - 主应用：保留向量检索、数据库操作等业务逻辑

2. **统一抽象接口**
   - `AIServiceProvider` 抽象基类
   - 已实现：GeminiProvider
   - 预留：ClaudeProvider, OpenAIProvider

3. **适配器模式**
   - `gemini_service.py` 改为适配器，保持原有函数签名
   - 主应用代码无需大量修改
   - 向量检索逻辑保留在主应用

4. **流式响应支持**
   - 2 个流式端点（大纲生成、章节生成）
   - SSE 格式：`data: {json}\n\n`

5. **完整错误处理**
   - 地理位置限制检测
   - 友好错误提示
   - 详细日志记录

6. **Docker 化**
   - 微服务 Dockerfile
   - Docker Compose 一键启动
   - 健康检查

---

## 文件结构

### AI 微服务（nova-ai-service/）

```
nova-ai-service/
├── app/
│   ├── main.py                      # FastAPI 入口
│   ├── config.py                    # 配置管理
│   ├── core/
│   │   └── providers/
│   │       ├── base.py              # AIServiceProvider 抽象基类
│   │       ├── gemini.py            # Gemini 实现（1479 行）
│   │       └── __init__.py          # 提供商工厂
│   ├── schemas/
│   │   ├── requests.py              # 请求模型
│   │   └── responses.py             # 响应模型
│   └── api/
│       ├── dependencies.py          # 依赖注入
│       └── v1/
│           ├── health.py            # 健康检查
│           ├── outline.py           # 大纲生成（4 个端点）
│           ├── chapter.py           # 章节生成（4 个端点）
│           └── analysis.py          # 元数据分析（6 个端点）
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

### 主应用改造（backend/）

```
backend/
├── services/ai/
│   ├── ai_service_client.py         # 微服务客户端（新建，817 行）
│   ├── gemini_service.py            # 适配器（改造）
│   └── gemini_service_direct.py     # 原实现备份
├── core/
│   └── config.py                    # 添加 AI_SERVICE_* 配置
└── .env.example                     # 添加 AI 微服务配置
```

### 根目录

```
nova-ai/
├── docker-compose.yml               # 完整编排（主应用 + 微服务 + 数据库）
└── AI_MICROSERVICE_SETUP.md         # 本文档
```

---

## 配置说明

### AI 微服务配置（nova-ai-service/.env）

```env
# 必填
GEMINI_API_KEY=your-api-key-here

# 可选
GEMINI_PROXY=http://127.0.0.1:40000
GEMINI_MODEL=gemini-3-pro-preview
LOG_LEVEL=INFO
PORT=8001
```

### 主应用配置（backend/.env）

```env
# AI 微服务配置（新增）
AI_SERVICE_URL=http://localhost:8001       # Docker: http://ai-service:8001
AI_SERVICE_TIMEOUT=300
AI_SERVICE_PROVIDER=gemini

# 原有配置保持不变
DATABASE_URL=postgresql://...
GEMINI_API_KEY=...（保留，用于备份）
```

---

## 监控和日志

### 查看日志

```bash
# Docker Compose 模式
docker-compose logs -f ai-service    # AI 微服务日志
docker-compose logs -f backend       # 主应用日志

# 本地开发模式
# 日志会输出到控制台
```

### 健康检查

```bash
# AI 微服务
curl http://localhost:8001/health
# 响应: {"status": "ok", "service": "nova-ai-service", "version": "1.0.0"}

# 主应用
curl http://localhost:8000/health
```

---

## 故障排查

### 问题 1：AI 微服务无法启动

**症状**：`ERROR: GEMINI_API_KEY 未配置`

**解决**：
```bash
# 检查 .env 文件
cat nova-ai-service/.env

# 确保 GEMINI_API_KEY 已设置
echo "GEMINI_API_KEY=your-key" >> nova-ai-service/.env
```

### 问题 2：主应用无法连接微服务

**症状**：`AI 服务调用失败: Connection refused`

**解决**：
1. 确认 AI 微服务正在运行：`curl http://localhost:8001/health`
2. 检查 `backend/.env` 中的 `AI_SERVICE_URL` 配置
3. Docker 模式：使用 `http://ai-service:8001`
4. 本地模式：使用 `http://localhost:8001`

### 问题 3：地理位置限制

**症状**：`location is not supported`

**解决**：
1. 配置 WARP 代理：`GEMINI_PROXY=http://127.0.0.1:40000`
2. 或使用其他 HTTP/SOCKS5 代理
3. 重启服务

---

## 性能优化建议

1. **连接池优化**
   - AIServiceClient 使用连接池
   - 超时设置：300 秒（可调整）

2. **缓存策略**
   - 考虑为常用请求添加缓存
   - 使用 Redis 缓存 AI 响应

3. **负载均衡**
   - 部署多个 AI 微服务实例
   - 使用 Nginx 进行负载均衡

4. **监控**
   - 添加 Prometheus metrics
   - 使用 Grafana 可视化

---

## 扩展指南

### 添加 Claude 支持

1. 实现 `ClaudeProvider` 类（继承 `AIServiceProvider`）
2. 在 `PROVIDERS` 字典中注册
3. 添加 Claude API 配置
4. 重启服务

### 添加新的 AI 功能

1. 在 `AIServiceProvider` 中添加抽象方法
2. 在 `GeminiProvider` 中实现
3. 在微服务 API 中添加端点
4. 在 `AIServiceClient` 中添加客户端方法
5. 在主应用适配器中添加对应函数

---

## 总结

✅ **已完成**：
- AI 微服务完整实现（16 个 API 端点）
- 主应用适配器改造
- Docker Compose 一键启动
- 完整的错误处理和日志
- 流式响应支持
- 多 AI 提供商抽象

🎯 **下一步**：
- 添加单元测试
- 添加集成测试
- 性能测试和优化
- 添加 Claude/OpenAI 支持
- 添加监控和告警

---

## 支持

如有问题，请查看：
- AI 微服务文档：`nova-ai-service/README.md`
- 主应用计划文档：`.claude/plans/flickering-churning-eich.md`
- API 文档：
  - http://localhost:8001/docs（AI 微服务）
  - http://localhost:8000/docs（主应用）

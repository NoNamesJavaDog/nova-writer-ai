# NovaWrite AI - 快速启动指南

## 🚀 本地启动（推荐新手）

### Windows 用户

1. **前置要求**：
   - ✅ Python 3.11+ 已安装
   - ✅ PostgreSQL 数据库正在运行（本地 Docker）
   - ✅ 已获取 Gemini API Key

2. **一键启动**：
```cmd
cd C:\Users\LILAN\IdeaProjects\nova-ai
scripts\start_local.bat
```

脚本会自动：
- ✅ 检查环境配置
- ✅ 初始化数据库（创建表、pgvector 扩展）
- ✅ 启动 AI 微服务（端口 8001）
- ✅ 启动主应用后端（端口 8000）
- ✅ 验证服务状态

### Mac/Linux 用户

1. **赋予执行权限**：
```bash
chmod +x scripts/start_local.sh scripts/stop_local.sh
```

2. **启动服务**：
```bash
cd /path/to/nova-ai
./scripts/start_local.sh
```

3. **停止服务**：
```bash
./scripts/stop_local.sh
```

---

## 📝 首次运行配置

### 1. 配置后端环境变量

脚本会自动复制 `.env.example` 为 `.env`，请编辑以下关键配置：

**backend/.env**：
```env
# 必填 - Gemini API Key
GEMINI_API_KEY=你的-gemini-api-key

# 数据库连接（根据你的 Docker PostgreSQL 配置）
DATABASE_URL=postgresql://postgres:你的密码@localhost:5432/novawrite_ai

# 如果需要代理访问 Gemini API
GEMINI_PROXY=http://127.0.0.1:40000
```

### 2. 配置 AI 微服务环境变量

**nova-ai-service/.env**：
```env
# 必填 - Gemini API Key
GEMINI_API_KEY=你的-gemini-api-key

# 可选 - 代理配置
GEMINI_PROXY=http://127.0.0.1:40000
```

---

## 🔍 验证服务

### 访问 API 文档

启动成功后，打开浏览器访问：

1. **AI 微服务文档**：http://localhost:8001/docs
   - 16 个 AI API 端点
   - 支持在线测试

2. **主应用文档**：http://localhost:8000/docs
   - 完整业务 API
   - 包含认证、小说管理等

### 快速测试

```bash
# 测试 AI 微服务健康状态
curl http://localhost:8001/health

# 测试主应用健康状态
curl http://localhost:8000/health
```

---

## 🐳 Docker Compose 启动（可选）

如果你更喜欢使用 Docker Compose：

```bash
# 1. 配置环境变量
echo "GEMINI_API_KEY=your-key" > .env

# 2. 启动所有服务（包括数据库）
docker-compose up --build

# 3. 停止服务
docker-compose down
```

Docker Compose 会启动：
- PostgreSQL 数据库（端口 5432）
- AI 微服务（端口 8001）
- 主应用后端（端口 8000）

---

## 📂 项目结构

```
nova-ai/
├── backend/                    # 主应用后端
│   ├── .env                   # 后端配置（需创建）
│   ├── main.py                # FastAPI 入口
│   └── services/ai/
│       ├── ai_service_client.py    # 微服务客户端
│       └── gemini_service.py       # AI 适配器
│
├── nova-ai-service/           # AI 微服务
│   ├── .env                   # 微服务配置（需创建）
│   ├── app/
│   │   ├── main.py            # 微服务入口
│   │   └── core/providers/
│   │       └── gemini.py      # Gemini 实现
│   └── requirements.txt
│
├── scripts/                   # 启动脚本
│   ├── start_local.bat        # Windows 启动脚本
│   ├── start_local.sh         # Linux/Mac 启动脚本
│   ├── stop_local.sh          # 停止脚本
│   └── init_local_db.py       # 数据库初始化
│
├── docker-compose.yml         # Docker 编排文件
└── START_HERE.md             # 本文件
```

---

## 🛠️ 常见问题

### 1. 数据库连接失败

**症状**：`数据库连接失败` 或 `could not connect to server`

**解决**：
```bash
# 检查 PostgreSQL 是否运行
docker ps | grep postgres

# 如果没有运行，启动 PostgreSQL
docker start <postgres-container-name>

# 或创建新的 PostgreSQL 容器
docker run -d \
  --name nova-ai-db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=novawrite_db_2024 \
  -e POSTGRES_DB=novawrite_ai \
  -p 5432:5432 \
  pgvector/pgvector:pg16
```

### 2. 端口被占用

**症状**：`Address already in use`

**解决**：
```bash
# Windows - 查找占用端口的进程
netstat -ano | findstr :8000
netstat -ano | findstr :8001

# 结束进程（替换 <PID> 为实际进程 ID）
taskkill /F /PID <PID>

# Linux/Mac
lsof -ti:8000 | xargs kill -9
lsof -ti:8001 | xargs kill -9
```

### 3. Gemini API 地理限制

**症状**：`location is not supported`

**解决**：
1. 配置 WARP 代理或其他 HTTP 代理
2. 在 `.env` 文件中设置：
```env
GEMINI_PROXY=http://127.0.0.1:40000
```

### 4. 模块导入错误

**症状**：`ModuleNotFoundError`

**解决**：
```bash
# 进入对应目录并安装依赖
cd backend
pip install -r requirements.txt

cd ../nova-ai-service
pip install -r requirements.txt
```

---

## 📚 更多文档

- **AI 微服务架构说明**：[AI_MICROSERVICE_SETUP.md](AI_MICROSERVICE_SETUP.md)
- **AI 微服务详细文档**：[nova-ai-service/README.md](nova-ai-service/README.md)
- **实施计划**：[.claude/plans/flickering-churning-eich.md](.claude/plans/flickering-churning-eich.md)

---

## 🎯 下一步

1. ✅ 启动服务
2. 访问 API 文档并测试
3. 查看 [API 使用示例](nova-ai-service/QUICK_START.md)
4. 开始开发前端或调用 API

---

## 💬 获取帮助

如有问题：
1. 查看日志文件（Windows：终端窗口 / Linux：logs/*.log）
2. 检查上述常见问题
3. 查看详细文档

🎉 祝使用愉快！

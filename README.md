# NovaWrite AI - 专业小说写作助手

AI 驱动的专业小说写作助手，帮助您创作下一部杰作。

## 功能特性

- 📝 AI 生成完整小说大纲和卷结构
- ✍️ 智能章节内容生成
- 👥 角色管理
- 🌍 世界观构建
- 📅 时间线管理
- 💡 伏笔管理和追踪
- 📱 移动端支持（响应式设计）
- 🔐 完整的用户认证系统
- 🔒 安全特性（速率限制、安全响应头、刷新令牌等）

## 技术栈

### 后端
- FastAPI (Python)
- SQLAlchemy (ORM)
- PostgreSQL
- JWT 认证
- Gemini API (gemini-3-pro-preview)

### 前端
- React 19
- TypeScript
- Tailwind CSS
- Vite

## 项目结构

```
terol/
├── backend/              # 后端代码
│   ├── main.py          # FastAPI 主应用
│   ├── models.py        # 数据库模型
│   ├── schemas.py       # Pydantic 数据模型
│   ├── auth.py          # 认证相关
│   ├── gemini_service.py # Gemini API 服务
│   └── requirements.txt # Python 依赖
│
├── novawrite-ai---professional-novel-assistant/  # 前端代码
│   ├── components/      # React 组件
│   ├── services/        # API 服务
│   ├── types.ts         # TypeScript 类型定义
│   └── package.json     # Node.js 依赖
│
└── deploy-from-repo.sh  # 自动部署脚本
```

## 部署流程

### 自动部署（推荐）

1. 本地开发完成后，提交代码：
   ```bash
   git add .
   git commit -m "your commit message"
   git push origin main
   ```

2. 在远程服务器上运行部署脚本：
   ```bash
   cd /opt/novawrite-ai
   git pull origin main
   ./deploy-from-repo.sh
   ```

### 手动部署

详见 `DEPLOY.md` 文件。

## 环境配置

### 后端环境变量

复制 `backend/config.example.env` 为 `backend/.env` 并配置：

```env
# 数据库配置
DATABASE_URL=postgresql://user:password@localhost/novawrite_db

# JWT 配置
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# Gemini API
GEMINI_API_KEY=your_gemini_api_key

# CORS
CORS_ORIGINS=http://localhost:3000,http://your-domain.com

# 环境
ENVIRONMENT=production
DEBUG=false
```

### 前端环境变量

前端通过 Nginx 代理访问后端 API，无需额外配置。

## 开发

### 后端开发

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### 前端开发

```bash
cd novawrite-ai---professional-novel-assistant
npm install
npm run dev
```

## 安全特性

- ✅ JWT 认证
- ✅ 刷新令牌机制
- ✅ 请求速率限制
- ✅ 密码强度验证
- ✅ 安全响应头（HSTS, CSP等）
- ✅ 全局异常处理（防止敏感信息泄露）

## 移动端支持

应用完全支持移动端浏览器访问：
- 响应式布局
- 移动端底部导航栏
- 抽屉式侧边栏
- 触摸友好的交互
- PWA 支持

## 伏笔管理

- 大纲生成时自动生成伏笔
- 章节生成后自动提取伏笔
- 查看伏笔产生的章节
- 标记伏笔闭环状态
- 关联闭环章节

## 许可证

私有项目



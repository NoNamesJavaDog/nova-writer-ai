# 前后端分离集成完成说明

## 完成的工作

### 后端 (FastAPI)
1. ✅ 创建了完整的 REST API (`backend/main.py`)
   - 用户认证（注册、登录、获取当前用户）
   - 小说 CRUD 操作
   - 卷、章节、角色、世界观、时间线的完整 API
   - 当前小说ID管理

2. ✅ 数据库初始化脚本 (`backend/init_db.py`)

3. ✅ CORS 中间件配置（允许前端跨域请求）

4. ✅ 启动脚本 (`backend/run.py`)

### 前端 (React + TypeScript)
1. ✅ 创建了 API 服务层 (`services/apiService.ts`)
   - 封装所有后端 API 调用
   - 数据格式转换（前端格式 ↔ 后端格式）
   - 错误处理

2. ✅ 更新了认证服务 (`services/authService.ts`)
   - 使用后端 API 进行登录/注册
   - JWT token 管理

3. ✅ 更新了主应用 (`App.tsx`)
   - 从 API 加载数据而不是 localStorage
   - 异步保存到后端
   - 加载状态处理

## 使用方法

### 1. 后端设置

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 配置环境变量（复制 .env.example 为 .env 并修改）
# DATABASE_URL=postgresql://postgres:password@localhost:5432/novawrite_ai
# SECRET_KEY=your-secret-key-here

# 初始化数据库
python init_db.py

# 启动服务器
python run.py
# 或
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

后端将在 `http://localhost:8000` 运行
API 文档：`http://localhost:8000/docs`

### 2. 前端设置

```bash
cd novawrite-ai---professional-novel-assistant

# 安装依赖（如果还没有）
npm install

# 配置环境变量（复制 .env.example 为 .env.local）
# VITE_API_BASE_URL=http://localhost:8000
# GEMINI_API_KEY=your_gemini_api_key

# 启动开发服务器
npm run dev
```

前端将在 `http://localhost:3000` 运行

## 数据流

### 登录流程
1. 用户在登录页面输入用户名/密码
2. 前端调用 `authApi.login()`
3. 后端验证并返回 JWT token
4. 前端保存 token 到 localStorage
5. 后续请求自动在请求头中包含 token

### 数据加载流程
1. 用户登录后，`App.tsx` 调用 `novelApi.getAll()`
2. 后端返回用户的所有小说
3. 前端更新状态并显示

### 数据保存流程
1. 用户修改小说内容
2. `updateNovel()` 先更新本地状态（乐观更新）
3. 异步调用 `novelApi.syncFull()` 保存到后端
4. 成功后使用服务器返回的最新数据更新本地状态

## API 端点

### 认证
- `POST /api/auth/register` - 注册
- `POST /api/auth/login` - 登录
- `GET /api/auth/me` - 获取当前用户

### 小说管理
- `GET /api/novels` - 获取所有小说
- `GET /api/novels/{id}` - 获取单个小说
- `POST /api/novels` - 创建小说
- `PUT /api/novels/{id}` - 更新小说
- `DELETE /api/novels/{id}` - 删除小说

详细 API 文档请查看 `backend/README.md`

## 注意事项

1. **数据库配置**：确保 PostgreSQL 数据库已创建并运行
2. **环境变量**：前后端都需要正确配置环境变量
3. **CORS**：后端已配置允许 `localhost:3000` 的跨域请求
4. **Token 管理**：JWT token 存储在 localStorage，生产环境建议考虑使用 httpOnly cookie
5. **数据同步**：`syncFull()` 函数会执行大量 API 调用，建议只在必要时使用

## 故障排除

### 前端无法连接到后端
- 检查后端是否在 `http://localhost:8000` 运行
- 检查 `VITE_API_BASE_URL` 环境变量配置
- 检查浏览器控制台的错误信息

### 401 Unauthorized 错误
- 检查 token 是否有效
- 尝试重新登录
- 检查后端 `SECRET_KEY` 是否配置正确

### 数据库连接错误
- 检查 PostgreSQL 是否运行
- 检查 `DATABASE_URL` 配置是否正确
- 确保数据库已创建

## 下一步优化建议

1. **性能优化**
   - 实现增量更新而不是完整同步
   - 添加请求去抖/节流
   - 实现数据缓存

2. **错误处理**
   - 添加全局错误处理
   - 实现错误重试机制
   - 添加用户友好的错误提示

3. **安全性**
   - 在生产环境使用 HTTPS
   - 实现 token 刷新机制
   - 添加请求限流

4. **用户体验**
   - 添加保存状态指示器
   - 实现离线支持
   - 添加数据冲突解决机制



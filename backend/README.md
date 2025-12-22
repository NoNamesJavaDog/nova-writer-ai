# NovaWrite AI 后端 API

## 环境要求

- Python 3.8+
- PostgreSQL 12+

## 安装

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 配置环境变量：
```bash
# 复制配置文件示例
cp config.example.env .env

# 编辑 .env 文件，配置数据库连接和其他参数
# 重要：生产环境必须修改 SECRET_KEY！
```

3. 初始化数据库：
```bash
python init_db.py
```

## 运行

启动开发服务器：
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

或者使用启动脚本：
```bash
python run.py
```

启动脚本会自动从配置文件读取 HOST 和 PORT 设置。

API 文档可在 http://localhost:8000/docs 查看（Swagger UI）

## API 端点

### 认证
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录
- `GET /api/auth/me` - 获取当前用户信息

### 小说
- `GET /api/novels` - 获取用户的所有小说
- `GET /api/novels/{novel_id}` - 获取单个小说详情
- `POST /api/novels` - 创建新小说
- `PUT /api/novels/{novel_id}` - 更新小说信息
- `DELETE /api/novels/{novel_id}` - 删除小说

### 卷
- `GET /api/novels/{novel_id}/volumes` - 获取小说的所有卷
- `POST /api/novels/{novel_id}/volumes` - 创建新卷
- `PUT /api/novels/{novel_id}/volumes/{volume_id}` - 更新卷信息
- `DELETE /api/novels/{novel_id}/volumes/{volume_id}` - 删除卷

### 章节
- `GET /api/volumes/{volume_id}/chapters` - 获取卷的所有章节
- `POST /api/volumes/{volume_id}/chapters` - 批量创建章节
- `PUT /api/volumes/{volume_id}/chapters/{chapter_id}` - 更新章节信息
- `DELETE /api/volumes/{volume_id}/chapters/{chapter_id}` - 删除章节

### 角色
- `GET /api/novels/{novel_id}/characters` - 获取小说的所有角色
- `POST /api/novels/{novel_id}/characters` - 批量创建角色
- `PUT /api/novels/{novel_id}/characters/{character_id}` - 更新角色信息
- `DELETE /api/novels/{novel_id}/characters/{character_id}` - 删除角色

### 世界观设定
- `GET /api/novels/{novel_id}/world-settings` - 获取小说的所有世界观设定
- `POST /api/novels/{novel_id}/world-settings` - 批量创建世界观设定
- `PUT /api/novels/{novel_id}/world-settings/{world_setting_id}` - 更新世界观设定
- `DELETE /api/novels/{novel_id}/world-settings/{world_setting_id}` - 删除世界观设定

### 时间线
- `GET /api/novels/{novel_id}/timeline` - 获取小说的所有时间线事件
- `POST /api/novels/{novel_id}/timeline` - 批量创建时间线事件
- `PUT /api/novels/{novel_id}/timeline/{timeline_event_id}` - 更新时间线事件
- `DELETE /api/novels/{novel_id}/timeline/{timeline_event_id}` - 删除时间线事件

### 当前小说
- `GET /api/current-novel` - 获取用户当前选择的小说ID
- `PUT /api/current-novel` - 设置用户当前选择的小说ID

## 数据库模型

- User: 用户
- Novel: 小说
- Volume: 卷
- Chapter: 章节
- Character: 角色
- WorldSetting: 世界观设定
- TimelineEvent: 时间线事件
- UserCurrentNovel: 用户当前小说（偏好）

## 认证

API 使用 JWT (JSON Web Token) 进行认证。登录成功后，客户端需要在请求头中包含：
```
Authorization: Bearer <access_token>
```

## 配置文件说明

配置文件使用 `.env` 文件存储环境变量。项目提供了 `config.example.env` 作为示例。

### 配置步骤

1. 复制配置示例文件：
```bash
cp config.example.env .env
```

2. 编辑 `.env` 文件，修改以下配置：
   - `DATABASE_URL`: PostgreSQL 数据库连接字符串
   - `SECRET_KEY`: JWT 密钥（**生产环境必须修改！**）
   - `CORS_ORIGINS`: 允许的前端地址（多个用逗号分隔）

3. 生成安全的 SECRET_KEY：
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 配置项说明

- `DATABASE_URL`: 数据库连接字符串
- `SECRET_KEY`: JWT 认证密钥（生产环境必须使用强随机字符串）
- `ALGORITHM`: JWT 算法（默认 HS256）
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token 过期时间（分钟，默认 1440）
- `HOST`: 服务器监听地址（默认 0.0.0.0）
- `PORT`: 服务器端口（默认 8000）
- `CORS_ORIGINS`: 允许的前端地址（逗号分隔）
- `ENVIRONMENT`: 环境类型（development/production）
- `DEBUG`: 调试模式（true/false）

## 注意事项

1. ⚠️ **生产环境必须修改 `SECRET_KEY` 为强随机字符串**
2. 确保数据库连接安全，不要在生产环境使用默认密码
3. CORS 配置在生产环境需要限制允许的源
4. `.env` 文件包含敏感信息，已添加到 `.gitignore`，不会提交到版本控制


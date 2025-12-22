# API 认证说明

## 需要认证的接口

以下接口**需要**用户登录认证（需要在请求头中携带 JWT Token）：

```
Authorization: Bearer <access_token>
```

### 认证相关
- ❌ `POST /api/auth/register` - **不需要认证**（公开接口）
- ❌ `POST /api/auth/login` - **不需要认证**（公开接口）
- ✅ `GET /api/auth/me` - **需要认证**

### 小说相关
- ✅ `GET /api/novels` - **需要认证**（获取用户的所有小说）
- ✅ `GET /api/novels/{novel_id}` - **需要认证**
- ✅ `POST /api/novels` - **需要认证**
- ✅ `PUT /api/novels/{novel_id}` - **需要认证**
- ✅ `DELETE /api/novels/{novel_id}` - **需要认证**

### 卷相关
- ✅ `GET /api/novels/{novel_id}/volumes` - **需要认证**
- ✅ `POST /api/novels/{novel_id}/volumes` - **需要认证**
- ✅ `PUT /api/novels/{novel_id}/volumes/{volume_id}` - **需要认证**
- ✅ `DELETE /api/novels/{novel_id}/volumes/{volume_id}` - **需要认证**

### 章节相关
- ✅ `GET /api/volumes/{volume_id}/chapters` - **需要认证**
- ✅ `POST /api/volumes/{volume_id}/chapters` - **需要认证**
- ✅ `PUT /api/volumes/{volume_id}/chapters/{chapter_id}` - **需要认证**
- ✅ `DELETE /api/volumes/{volume_id}/chapters/{chapter_id}` - **需要认证**

### 角色相关
- ✅ `GET /api/novels/{novel_id}/characters` - **需要认证**
- ✅ `POST /api/novels/{novel_id}/characters` - **需要认证**
- ✅ `PUT /api/novels/{novel_id}/characters/{character_id}` - **需要认证**
- ✅ `DELETE /api/novels/{novel_id}/characters/{character_id}` - **需要认证**

### 世界观设定相关
- ✅ `GET /api/novels/{novel_id}/world-settings` - **需要认证**
- ✅ `POST /api/novels/{novel_id}/world-settings` - **需要认证**
- ✅ `PUT /api/novels/{novel_id}/world-settings/{world_setting_id}` - **需要认证**
- ✅ `DELETE /api/novels/{novel_id}/world-settings/{world_setting_id}` - **需要认证**

### 时间线相关
- ✅ `GET /api/novels/{novel_id}/timeline` - **需要认证**
- ✅ `POST /api/novels/{novel_id}/timeline` - **需要认证**
- ✅ `PUT /api/novels/{novel_id}/timeline/{timeline_event_id}` - **需要认证**
- ✅ `DELETE /api/novels/{novel_id}/timeline/{timeline_event_id}` - **需要认证**

### 当前小说相关
- ✅ `GET /api/current-novel` - **需要认证**
- ✅ `PUT /api/current-novel` - **需要认证**

### AI 相关
- ✅ `POST /api/ai/generate-outline` - **需要认证**
- ✅ `POST /api/ai/generate-volume-outline` - **需要认证**
- ✅ `POST /api/ai/generate-chapter-outline` - **需要认证**
- ✅ `POST /api/ai/write-chapter` - **需要认证**
- ✅ `POST /api/ai/generate-characters` - **需要认证**
- ✅ `POST /api/ai/generate-world-settings` - **需要认证**
- ✅ `POST /api/ai/generate-timeline-events` - **需要认证**

### 其他
- ❌ `GET /` - **不需要认证**（根路径，返回 API 信息）
- ❌ `GET /docs` - **不需要认证**（Swagger 文档，开发环境）
- ❌ `GET /openapi.json` - **不需要认证**（OpenAPI 规范）

## 总结

**不需要认证的接口（公开接口）**：
1. `POST /api/auth/register` - 用户注册
2. `POST /api/auth/login` - 用户登录
3. `GET /` - API 信息
4. `GET /docs` - API 文档
5. `GET /openapi.json` - OpenAPI 规范

**所有其他接口都需要认证**。

## 认证方式

使用 JWT (JSON Web Token) 进行认证：

1. **获取 Token**：通过 `/api/auth/login` 或 `/api/auth/register` 获取 `access_token`
2. **使用 Token**：在后续请求的请求头中添加：
   ```
   Authorization: Bearer <access_token>
   ```
3. **Token 过期**：Token 默认 24 小时过期，过期后需要重新登录

## 安全说明

- ✅ 所有数据操作接口都需要认证，确保用户只能访问自己的数据
- ✅ AI 功能需要认证，防止滥用和未授权访问
- ✅ 认证接口（注册/登录）是公开的，但注册后需要登录才能使用其他功能
- ⚠️ 建议在生产环境中限制 `/docs` 和 `/openapi.json` 的访问



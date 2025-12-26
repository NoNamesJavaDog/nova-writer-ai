# 前端到后端迁移检查报告

## 检查时间
2025-12-26

## 前端调用的 API 端点清单

### 1. 认证相关 (`/api/auth/*`)
- ✅ `POST /api/auth/register` - 用户注册
- ✅ `POST /api/auth/login` - 用户登录
- ✅ `POST /api/auth/refresh` - 刷新令牌
- ✅ `GET /api/auth/captcha` - 获取验证码
- ✅ `GET /api/auth/login-status` - 检查登录状态
- ✅ `GET /api/auth/me` - 获取当前用户信息

### 2. 小说相关 (`/api/novels/*`)
- ✅ `GET /api/novels` - 获取所有小说
- ✅ `GET /api/novels/{novel_id}` - 获取单个小说
- ✅ `POST /api/novels` - 创建小说
- ✅ `PUT /api/novels/{novel_id}` - 更新小说
- ✅ `DELETE /api/novels/{novel_id}` - 删除小说

### 3. 卷相关 (`/api/novels/{novel_id}/volumes/*`)
- ✅ `GET /api/novels/{novel_id}/volumes` - 获取所有卷
- ✅ `POST /api/novels/{novel_id}/volumes` - 创建卷
- ✅ `PUT /api/novels/{novel_id}/volumes/{volume_id}` - 更新卷
- ✅ `DELETE /api/novels/{novel_id}/volumes/{volume_id}` - 删除卷

### 4. 章节相关 (`/api/volumes/{volume_id}/chapters/*`)
- ✅ `GET /api/volumes/{volume_id}/chapters` - 获取所有章节
- ✅ `POST /api/volumes/{volume_id}/chapters` - 批量创建章节
- ✅ `PUT /api/volumes/{volume_id}/chapters/{chapter_id}` - 更新章节
- ✅ `DELETE /api/volumes/{volume_id}/chapters/{chapter_id}` - 删除章节

### 5. 角色相关 (`/api/novels/{novel_id}/characters/*`)
- ✅ `GET /api/novels/{novel_id}/characters` - 获取所有角色
- ✅ `POST /api/novels/{novel_id}/characters` - 批量创建角色
- ✅ `PUT /api/novels/{novel_id}/characters/{character_id}` - 更新角色
- ✅ `DELETE /api/novels/{novel_id}/characters/{character_id}` - 删除角色

### 6. 世界观设定相关 (`/api/novels/{novel_id}/world-settings/*`)
- ✅ `GET /api/novels/{novel_id}/world-settings` - 获取所有世界观设定
- ✅ `POST /api/novels/{novel_id}/world-settings` - 批量创建世界观设定
- ✅ `PUT /api/novels/{novel_id}/world-settings/{world_setting_id}` - 更新世界观设定
- ✅ `DELETE /api/novels/{novel_id}/world-settings/{world_setting_id}` - 删除世界观设定

### 7. 时间线相关 (`/api/novels/{novel_id}/timeline/*`)
- ✅ `GET /api/novels/{novel_id}/timeline` - 获取所有时间线事件
- ✅ `POST /api/novels/{novel_id}/timeline` - 批量创建时间线事件
- ✅ `PUT /api/novels/{novel_id}/timeline/{timeline_event_id}` - 更新时间线事件
- ✅ `DELETE /api/novels/{novel_id}/timeline/{timeline_event_id}` - 删除时间线事件

### 8. 伏笔相关 (`/api/novels/{novel_id}/foreshadowings/*`)
- ✅ `GET /api/novels/{novel_id}/foreshadowings` - 获取所有伏笔
- ✅ `POST /api/novels/{novel_id}/foreshadowings` - 批量创建伏笔
- ✅ `PUT /api/novels/{novel_id}/foreshadowings/{foreshadowing_id}` - 更新伏笔
- ✅ `DELETE /api/novels/{novel_id}/foreshadowings/{foreshadowing_id}` - 删除伏笔

### 9. 当前小说相关 (`/api/current-novel`)
- ✅ `GET /api/current-novel` - 获取当前小说ID
- ✅ `PUT /api/current-novel` - 设置当前小说ID

### 10. AI 生成相关 (`/api/ai/*`)
- ❓ `POST /api/ai/generate-outline` - 生成完整大纲（任务模式）
- ❓ `POST /api/ai/generate-volume-outline` - 生成卷详细大纲（流式）
- ❓ `POST /api/ai/generate-chapter-outline` - 生成章节列表
- ❓ `POST /api/ai/write-chapter` - 生成章节内容（流式）
- ❓ `POST /api/ai/generate-characters` - 生成角色列表（任务模式）
- ❓ `POST /api/ai/generate-world-settings` - 生成世界观设定（任务模式）
- ❓ `POST /api/ai/generate-timeline-events` - 生成时间线事件（任务模式）
- ❓ `POST /api/ai/generate-foreshadowings` - 生成伏笔（任务模式）
- ❓ `POST /api/ai/extract-foreshadowings-from-chapter` - 从章节提取伏笔
- ❓ `POST /api/ai/modify-outline-by-dialogue` - 通过对话修改大纲（任务模式）

### 11. 任务相关 (`/api/tasks/*`)
- ❓ `GET /api/tasks/{task_id}` - 获取任务状态
- ❓ `GET /api/tasks/active` - 获取活跃任务列表
- ❓ `GET /api/tasks/novel/{novel_id}` - 获取小说的所有任务

### 12. 前端业务逻辑（未迁移到后端）

#### 12.1 数据转换逻辑
- ⚠️ **`apiToNovel()`** - 将后端 API 响应转换为前端 Novel 对象
  - 位置: `services/apiService.ts:317`
  - 说明: 前端负责数据格式转换，包括：
    - 字段名映射（snake_case → camelCase）
    - 嵌套对象转换（volumes, chapters, characters 等）
    - 数组过滤和映射

- ⚠️ **`novelToApi()`** - 将前端 Novel 对象转换为后端 API 格式
  - 位置: `services/apiService.ts:372`
  - 说明: 前端负责数据格式转换

#### 12.2 同步逻辑
- ⚠️ **`novelApi.sync()`** - 完整同步小说数据
  - 位置: `services/apiService.ts:427`
  - 说明: 前端负责复杂的同步逻辑：
    - 比较新旧数据差异
    - 批量创建/更新/删除操作
    - 处理卷、章节、角色、世界观、时间线、伏笔的同步
    - 这个逻辑应该移到后端，前端只调用一个同步接口

#### 12.3 上下文生成逻辑
- ⚠️ **`getPreviousChaptersContext()`** - 获取前文章节上下文
  - 位置: `services/geminiService.ts:209`
  - 说明: 前端负责生成前文上下文，用于避免重复内容
  - 建议: 应该由后端根据 novel_id 和 chapter_id 自动生成

#### 12.4 流式响应处理
- ⚠️ **`processStreamResponse()`** - 处理 Server-Sent Events 流式响应
  - 位置: `services/geminiService.ts:9`
  - 说明: 前端负责解析流式响应
  - 状态: 这个逻辑可以保留在前端，但后端需要确保正确发送流式响应

#### 12.5 任务轮询逻辑
- ⚠️ **`startPolling()`** - 轮询任务状态
  - 位置: `services/taskService.ts:33`
  - 说明: 前端负责轮询任务状态
  - 状态: 这个逻辑可以保留在前端，但后端需要提供任务状态 API

#### 12.6 未实现的 AI 功能
- ❌ **`expandText()`** - 扩展文本
  - 位置: `services/geminiService.ts:322`
  - 状态: 前端已定义但未实现，后端也未实现

- ❌ **`polishText()`** - 润色文本
  - 位置: `services/geminiService.ts:328`
  - 状态: 前端已定义但未实现，后端也未实现

## 需要迁移到后端的逻辑

### 高优先级

1. **完整同步逻辑 (`novelApi.sync`)**
   - 当前: 前端负责比较差异并执行批量操作
   - 建议: 后端提供 `POST /api/novels/{novel_id}/sync` 接口
   - 好处: 
     - 减少网络请求次数
     - 保证数据一致性
     - 支持事务处理

2. **前文上下文生成 (`getPreviousChaptersContext`)**
   - 当前: 前端手动提取前3章内容
   - 建议: 后端在生成章节时自动获取上下文
   - 好处:
     - 更智能的上下文选择（可以使用向量相似度）
     - 减少前端数据传输量

3. **数据格式转换**
   - 当前: 前端负责 snake_case ↔ camelCase 转换
   - 建议: 后端统一使用 camelCase 或提供转换中间件
   - 好处:
     - 减少前端代码复杂度
     - 统一数据格式

### 中优先级

4. **AI 端点实现**
   - 需要确认后端是否已实现所有 `/api/ai/*` 端点
   - 需要确认任务系统是否正常工作

5. **任务 API**
   - 需要确认 `/api/tasks/*` 端点是否已实现

### 低优先级

6. **扩展文本和润色功能**
   - 可以后续实现

## 检查结果

### ✅ 已迁移的功能
- 所有 CRUD 操作（创建、读取、更新、删除）
- 认证和授权
- 基本的数据管理

### ⚠️ 部分迁移的功能
- AI 生成功能（后端有服务函数，但需要确认路由是否实现）
- 任务系统（后端有服务，但需要确认 API 是否实现）

### ❌ 未迁移的功能
- 完整同步逻辑（前端实现）
- 前文上下文生成（前端实现）
- 数据格式转换（前端实现）
- 扩展文本功能（未实现）
- 润色文本功能（未实现）

## 建议

1. **立即迁移**: 完整同步逻辑应该尽快移到后端
2. **优化**: 前文上下文生成应该由后端智能处理
3. **统一**: 数据格式应该统一，减少前端转换逻辑
4. **完善**: 确认所有 AI 端点和任务 API 都已实现并正常工作


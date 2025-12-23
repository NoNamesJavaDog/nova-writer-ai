# 后台任务系统测试指南

## 准备工作

### 1. 运行数据库迁移

首先需要在数据库中创建 `tasks` 表：

```bash
cd terol/backend
python migrate_add_tasks_table.py
```

或者如果数据库权限不足，可以手动执行 SQL：

```sql
CREATE TABLE tasks (
    id VARCHAR(36) PRIMARY KEY,
    novel_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    task_type VARCHAR(50) NOT NULL,
    task_data TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    progress INTEGER NOT NULL DEFAULT 0,
    progress_message TEXT,
    result TEXT,
    error_message TEXT,
    created_at BIGINT NOT NULL,
    updated_at BIGINT NOT NULL,
    started_at BIGINT,
    completed_at BIGINT,
    FOREIGN KEY (novel_id) REFERENCES novels(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_tasks_novel_id ON tasks(novel_id);
CREATE INDEX idx_tasks_user_id ON tasks(user_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_created_at ON tasks(created_at DESC);
```

### 2. 确保后端服务运行

```bash
cd terol/backend
python run.py
```

### 3. 确保前端构建并运行

```bash
cd terol/novawrite-ai---professional-novel-assistant
npm install
npm run build
# 或者开发模式
npm run dev
```

## 测试步骤

### 测试 1: 创建生成大纲任务

1. 登录系统
2. 进入 Dashboard 页面
3. 填写小说标题、类型、简介
4. 点击"生成大纲"按钮
5. 应该看到：
   - 任务创建成功的消息
   - 任务ID显示在控制台
   - 进度条开始更新
   - 进度消息不断更新（10% -> 50% -> 90% -> 100%）

### 测试 2: 任务后台执行

1. 在任务执行过程中（进度 < 100%）
2. 切换到其他页面（例如 Outline 页面）
3. 任务应该继续在后台执行
4. 检查浏览器控制台，应该看到任务状态仍在更新

### 测试 3: 返回页面恢复任务

1. 在任务执行过程中离开 Dashboard
2. 等待几秒钟（确保任务仍在运行）
3. 返回 Dashboard 页面
4. 系统应该检测到活跃任务（控制台会有日志）
5. 可以手动查询任务状态验证

### 测试 4: 查询任务状态 API

使用 curl 或 Postman 测试 API：

```bash
# 获取任务状态（替换 YOUR_TOKEN 和 TASK_ID）
curl -X GET "http://localhost:8000/api/tasks/TASK_ID" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 获取小说的所有任务
curl -X GET "http://localhost:8000/api/novels/NOVEL_ID/tasks" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 获取活跃任务
curl -X GET "http://localhost:8000/api/tasks/active" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 测试 5: 任务完成后的结果应用

1. 等待任务完成（进度 100%）
2. 检查任务结果是否正确应用到大纲和卷结构
3. 验证小说数据是否正确更新

### 测试 6: 任务失败处理

1. 模拟任务失败（例如：断开网络或使用无效的 API Key）
2. 检查任务状态是否变为 "failed"
3. 检查错误消息是否正确显示

## 预期行为

### 正常流程

1. **任务创建**：
   - API 返回 `task_id`
   - 任务状态为 "pending"
   - 立即开始执行

2. **任务执行**：
   - 状态变为 "running"
   - 进度从 0% 逐步增加到 100%
   - 进度消息定期更新

3. **任务完成**：
   - 状态变为 "completed"
   - 结果存储在 `result` 字段中
   - 前端接收到结果并应用到小说数据

### 错误处理

1. **任务失败**：
   - 状态变为 "failed"
   - 错误消息存储在 `error_message` 字段
   - 前端显示错误提示

2. **网络中断**：
   - 任务继续在后台执行
   - 前端轮询失败时会记录错误
   - 重新连接后可以继续查询任务状态

## 调试技巧

### 查看任务数据

```sql
-- 查看所有任务
SELECT id, novel_id, task_type, status, progress, progress_message, created_at, updated_at 
FROM tasks 
ORDER BY created_at DESC;

-- 查看运行中的任务
SELECT * FROM tasks WHERE status = 'running';

-- 查看失败的任务
SELECT * FROM tasks WHERE status = 'failed';
```

### 查看后端日志

```bash
# 查看 systemd 服务日志
journalctl -u novawrite-ai-backend -f

# 或者如果直接运行
cd terol/backend
python run.py
```

### 前端调试

1. 打开浏览器开发者工具
2. 查看 Console 标签页中的日志
3. 查看 Network 标签页中的 API 请求
4. 检查任务轮询是否正常

## 已知问题

1. **进度更新频率**：当前进度更新可能不够频繁，需要优化
2. **任务结果解析**：需要确保 JSON 解析正确
3. **错误消息**：需要确保错误消息对用户友好

## 下一步改进

1. 添加任务取消功能
2. 添加任务重试功能
3. 添加任务历史记录查看
4. 优化进度更新机制
5. 添加任务通知（浏览器通知）


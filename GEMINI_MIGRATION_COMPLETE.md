# ✅ Gemini API 已迁移到后端

## 完成的工作

### 1. 后端实现

- ✅ **创建 `backend/gemini_service.py`**
  - 封装所有 Gemini API 调用
  - 支持流式和非流式响应
  - 统一的错误处理

- ✅ **添加后端 API 路由** (`backend/main.py`)
  - `/api/ai/generate-outline` - 生成完整大纲
  - `/api/ai/generate-volume-outline` - 生成卷大纲（流式）
  - `/api/ai/generate-chapter-outline` - 生成章节列表
  - `/api/ai/write-chapter` - 生成章节内容（流式）
  - `/api/ai/generate-characters` - 生成角色列表
  - `/api/ai/generate-world-settings` - 生成世界观设定
  - `/api/ai/generate-timeline-events` - 生成时间线事件

- ✅ **更新配置**
  - `backend/config.py` - 添加 `GEMINI_API_KEY` 配置
  - `backend/config.example.env` - 添加配置示例
  - `backend/requirements.txt` - 添加 `google-genai>=0.2.0`

- ✅ **添加数据模型** (`backend/schemas.py`)
  - 所有 AI 相关的请求和响应模型

### 2. 前端修改

- ✅ **重写 `services/geminiService.ts`**
  - 移除直接调用 Gemini API 的代码
  - 改为调用后端 API
  - 支持 Server-Sent Events 流式响应
  - 保持相同的函数接口（向后兼容）

### 3. 优势

- ✅ **安全性提升**
  - API Key 存储在服务器端，不会暴露
  - 不需要浏览器代理配置

- ✅ **性能提升**
  - 服务器网络更稳定
  - 可以添加缓存和限流

- ✅ **更好的错误处理**
  - 统一的错误处理机制
  - 更好的日志记录

## 部署步骤

### 1. 更新后端依赖

```bash
cd /opt/novawrite-ai/backend
source ../venv/bin/activate
pip install google-genai>=0.2.0
```

### 2. 配置 API Key

在 `/opt/novawrite-ai/backend/.env` 文件中添加：

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. 重启后端服务

```bash
systemctl restart novawrite-backend
```

### 4. 重新部署前端

前端代码已更新，需要重新构建并部署：

```powershell
.\deploy.ps1
```

## 测试

部署后测试以下功能：

1. **生成大纲** - 在 Dashboard 页面生成完整大纲
2. **生成卷大纲** - 在 Outline 页面生成卷详细大纲
3. **生成章节列表** - 生成章节列表
4. **生成章节内容** - 在 Editor 页面生成章节内容
5. **生成角色/世界观/时间线** - 测试其他 AI 功能

## 注意事项

- 确保后端 `.env` 文件中配置了正确的 `GEMINI_API_KEY`
- 如果 API Key 无效，所有 AI 功能将无法使用
- 流式响应使用 Server-Sent Events (SSE)，确保浏览器支持

---

**迁移完成时间**: 2025-12-22
**状态**: ✅ 代码已完成，等待部署和测试



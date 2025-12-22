# Gemini API 调用位置分析

## 当前状态

**Gemini API 目前是在前端调用的**

### 证据

1. **服务文件位置**: `novawrite-ai---professional-novel-assistant/services/geminiService.ts`
   - 位于前端目录中
   - 使用 `@google/genai` 库直接调用 Gemini API

2. **API Key 管理**:
   ```typescript
   const getApiKey = () => {
     const key = process.env.API_KEY || process.env.GEMINI_API_KEY || '';
     // ...
   };
   ```
   - API Key 从前端环境变量读取
   - 会暴露在浏览器中（安全风险）

3. **调用方式**:
   ```typescript
   const ai = new GoogleGenAI({ apiKey });
   // 直接在前端调用
   ai.models.generateContentStream({ ... })
   ```

4. **使用位置**:
   - `Dashboard.tsx` - 生成大纲
   - `OutlineView.tsx` - 生成卷大纲、章节列表
   - `EditorView.tsx` - 生成章节内容
   - 其他组件中也可能使用

## 问题

### 1. 安全风险
- ❌ API Key 暴露在前端代码中
- ❌ 任何人都可以在浏览器中查看 API Key
- ❌ 可能导致 API Key 被滥用

### 2. 网络问题
- ❌ 需要浏览器配置代理才能访问 Gemini API
- ❌ 可能遇到 CORS 问题
- ❌ 网络错误处理复杂

### 3. 性能问题
- ❌ 大请求可能导致浏览器超时
- ❌ 流式传输在浏览器中可能不稳定

## 建议

### 应该改为后端调用

**优势**:
- ✅ API Key 安全存储在服务器端
- ✅ 不需要浏览器代理
- ✅ 更好的错误处理和重试机制
- ✅ 可以添加缓存和限流
- ✅ 更好的性能（服务器网络通常更稳定）

### 实现方案

1. **在后端添加 Gemini API 路由**:
   ```python
   # backend/main.py
   @app.post("/api/ai/generate-outline")
   async def generate_outline(...):
       # 调用 Gemini API
       pass
   ```

2. **前端调用后端 API**:
   ```typescript
   // services/apiService.ts
   export const aiApi = {
     generateOutline: async (data) => {
       return apiRequest('/api/ai/generate-outline', {
         method: 'POST',
         body: JSON.stringify(data)
       });
     }
   };
   ```

3. **后端配置 API Key**:
   ```python
   # backend/config.py
   GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
   ```

## 当前架构

```
前端 (浏览器)
  ↓ 直接调用
Gemini API
  ↑
需要代理配置
```

## 推荐架构

```
前端 (浏览器)
  ↓ HTTP 请求
后端 API (FastAPI)
  ↓ 服务器调用
Gemini API
  ↑
API Key 安全存储
```

---

**结论**: 目前是前端调用，建议改为后端调用以提高安全性和稳定性。



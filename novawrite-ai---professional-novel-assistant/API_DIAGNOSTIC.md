# API 连接诊断指南

## 问题：无法连接到 Gemini API

### 步骤 1：检查 API Key 配置

1. **创建 `.env.local` 文件**（如果不存在）
   - 位置：项目根目录 `novawrite-ai---professional-novel-assistant/`
   - 内容：
     ```
     GEMINI_API_KEY=your_api_key_here
     ```
   - 获取 API Key：https://aistudio.google.com/apikey

2. **验证文件存在**
   ```bash
   # 在项目根目录执行
   ls .env.local
   # 或 Windows
   dir .env.local
   ```

3. **重启开发服务器**
   ```bash
   # 停止当前服务器（Ctrl+C）
   # 然后重新启动
   npm run dev
   ```

### 步骤 2：检查代理设置

由于应用在浏览器中运行，代理设置需要：

1. **确保代理软件运行**
   - 检查代理软件（如 Clash、V2Ray）是否在运行
   - 确认代理端口：`127.0.0.1:7899`

2. **配置浏览器代理**（如果系统代理未生效）
   - Chrome/Edge：设置 → 系统 → 打开计算机的代理设置
   - 或使用浏览器扩展（如 SwitchyOmega）

3. **测试代理连接**
   ```bash
   # 测试代理是否工作
   curl -x http://127.0.0.1:7899 https://generativelanguage.googleapis.com
   ```

### 步骤 3：检查浏览器控制台

1. 打开浏览器开发者工具（F12）
2. 切换到 "Console" 标签
3. 查看错误信息：
   - 如果看到 "未找到 Gemini API Key" → API Key 未配置
   - 如果看到网络错误 → 检查代理或网络连接
   - 如果看到 401/403 错误 → API Key 无效

### 步骤 4：常见错误及解决方案

#### 错误：未配置 Gemini API Key
- **解决**：创建 `.env.local` 文件并添加 `GEMINI_API_KEY=your_key`
- **注意**：必须重启开发服务器才能生效

#### 错误：网络连接失败 / CORS 错误
- **解决**：配置浏览器使用代理 `127.0.0.1:7899`
- **或**：确保系统代理已正确配置

#### 错误：401 Unauthorized
- **解决**：检查 API Key 是否正确
- **检查**：API Key 是否已启用 Gemini API 访问权限

#### 错误：请求超时
- **解决**：检查网络连接
- **检查**：代理服务器是否正常工作

### 步骤 5：手动测试 API 连接

在浏览器控制台执行：

```javascript
// 测试 API Key 是否可用
fetch('https://generativelanguage.googleapis.com/v1beta/models?key=YOUR_API_KEY')
  .then(r => r.json())
  .then(console.log)
  .catch(console.error);
```

替换 `YOUR_API_KEY` 为您的实际 API Key。

### 调试信息

应用会在浏览器控制台输出详细的调试信息：
- ✅ API Key 检查状态
- 🚀 API 调用开始
- ✅ API 调用成功
- ❌ 错误详情

请查看控制台获取更多信息。



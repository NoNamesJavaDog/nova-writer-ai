# 快速修复：API 连接问题

## ✅ 已确认：API Key 已配置

您的 `.env.local` 文件已存在且包含 API Key。

## ⚠️ 问题：浏览器代理配置

**重要**：由于 `@google/genai` 库在浏览器中运行，Node.js 的环境变量代理（`HTTP_PROXY`）对浏览器端的请求**不起作用**。

### 解决方案

#### 方法 1：配置系统代理（推荐）

1. **Windows 系统代理设置**
   - 打开"设置" → "网络和 Internet" → "代理"
   - 开启"使用代理服务器"
   - 地址：`127.0.0.1`
   - 端口：`7899`
   - 保存设置

2. **重启浏览器**
   - 完全关闭浏览器（所有窗口）
   - 重新打开浏览器
   - 访问应用

#### 方法 2：使用浏览器代理扩展

1. **安装代理扩展**（如 SwitchyOmega）
   - Chrome: https://chrome.google.com/webstore
   - Edge: https://microsoftedge.microsoft.com/addons

2. **配置扩展**
   - 代理协议：HTTP
   - 代理服务器：`127.0.0.1`
   - 端口：`7899`
   - 应用到所有网站

#### 方法 3：检查代理软件

1. **确认代理软件运行**
   ```bash
   # 测试代理是否响应
   curl -x http://127.0.0.1:7899 http://www.google.com
   ```

2. **检查代理日志**
   - 查看代理软件是否有请求记录
   - 确认代理规则允许访问 `generativelanguage.googleapis.com`

### 调试步骤

1. **打开浏览器控制台**（F12）
2. **查看 Network 标签**
   - 尝试生成大纲
   - 查看是否有对 `generativelanguage.googleapis.com` 的请求
   - 检查请求状态（失败/超时/被阻止）

3. **查看 Console 标签**
   - 查找错误信息
   - 查看 API Key 检查状态

### 测试连接

在浏览器控制台执行：

```javascript
// 测试是否能访问 Google API（需要配置代理）
fetch('https://generativelanguage.googleapis.com/v1beta/models?key=YOUR_API_KEY')
  .then(r => {
    console.log('状态:', r.status);
    return r.json();
  })
  .then(data => console.log('成功:', data))
  .catch(err => console.error('失败:', err));
```

### 如果仍然无法连接

1. **检查防火墙**
   - 确保浏览器未被防火墙阻止
   - 允许浏览器访问网络

2. **检查代理软件配置**
   - 确认代理支持 HTTPS
   - 检查是否需要配置证书

3. **尝试直接连接**（不使用代理）
   - 如果您的网络可以直接访问 Google API，可以暂时关闭代理测试

4. **查看详细错误**
   - 浏览器控制台会显示详细的错误信息
   - 根据错误信息进一步排查



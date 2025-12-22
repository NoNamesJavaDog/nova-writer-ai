# 前端刷新令牌机制更新

## 更新时间
2025-12-22

## 更新内容

### 1. 更新 `apiService.ts`

#### 新增功能：
- **刷新令牌存储和管理**
  - `getRefreshToken()`: 获取刷新令牌
  - `setRefreshToken()`: 设置刷新令牌
  - `clearRefreshToken()`: 清除刷新令牌
  - `clearAllTokens()`: 清除所有令牌

- **自动刷新机制**
  - `refreshAccessToken()`: 刷新访问令牌的函数
  - 防止并发刷新请求（使用 `isRefreshing` 标志）
  - 401 错误时自动尝试刷新令牌并重试请求

- **更新 `LoginResponse` 接口**
  ```typescript
  export interface LoginResponse {
    access_token: string;
    refresh_token: string;  // 新增
    token_type: string;
    user: User;
  }
  ```

- **更新 `apiRequest` 函数**
  - 添加 `retryOn401` 参数控制是否在 401 时重试
  - 401 错误时自动调用 `refreshAccessToken()` 刷新令牌
  - 刷新成功后自动重试原请求
  - 刷新失败则清除所有令牌并抛出错误

- **更新 `authApi`**
  - `register()`: 保存 `refresh_token`
  - `login()`: 保存 `refresh_token`
  - `refresh()`: 新增刷新令牌接口
  - `logout()`: 清除所有令牌（包括刷新令牌）

### 2. 更新 `authService.ts`

- `logout()`: 确保清除所有令牌

## 工作流程

### 登录流程
1. 用户登录成功
2. 后端返回 `access_token` 和 `refresh_token`
3. 前端存储两个令牌到 localStorage

### API 请求流程
1. 使用 `access_token` 发送请求
2. 如果收到 401 错误：
   - 使用 `refresh_token` 调用 `/api/auth/refresh` 接口
   - 获取新的 `access_token` 和 `refresh_token`
   - 更新 localStorage
   - 使用新的 `access_token` 重试原请求
3. 如果刷新失败：
   - 清除所有令牌
   - 提示用户重新登录

### 令牌过期
- **访问令牌**: 1小时过期（自动刷新）
- **刷新令牌**: 7天过期（需要重新登录）

## 安全性

1. **防止令牌泄露**: 刷新令牌不会在请求中自动使用，只在需要刷新时使用
2. **并发控制**: 多个请求同时收到 401 时，只发起一次刷新请求
3. **错误处理**: 刷新失败时立即清除所有令牌，防止使用无效令牌

## 部署状态

✅ 前端代码已更新
✅ 已部署到生产环境
✅ 与后端刷新令牌机制完全兼容

## 测试建议

1. **测试自动刷新**:
   - 登录后等待 1 小时（或修改后端 token 过期时间为更短时间测试）
   - 发起 API 请求，应该自动刷新令牌

2. **测试刷新失败**:
   - 手动删除或修改刷新令牌
   - 发起 API 请求，应该提示重新登录

3. **测试并发请求**:
   - 在令牌过期时同时发起多个请求
   - 应该只发起一次刷新请求

---

**状态**: ✅ 已完成并部署



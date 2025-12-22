# ✅ 登录问题已修复

## 修复的问题

### 1. **后端密码验证问题**
- **问题**: 创建用户时使用了 `bcrypt` 库，但验证时使用了 `passlib`，两者不兼容
- **修复**: 统一使用 `bcrypt` 库进行密码哈希和验证
- **文件**: `backend/auth.py`

### 2. **前端 API 配置问题**
- **问题**: 前端 API_BASE_URL 默认是 `http://localhost:8000`，部署后无法连接后端
- **修复**: 改为使用相对路径（空字符串），由 Nginx 代理到后端
- **文件**: `novawrite-ai---professional-novel-assistant/services/apiService.ts`

## 测试结果

✅ **后端登录 API 测试成功**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "username": "lanf",
    "email": "lanf@example.com",
    "id": "998fd70a-4972-4b3a-9988-243952f644cd"
  }
}
```

## 下一步操作

需要重新构建并部署前端：

```powershell
# 使用部署脚本重新部署
.\deploy.ps1
```

或者手动操作：

1. **重新构建前端**:
   ```powershell
   cd novawrite-ai---professional-novel-assistant
   $env:VITE_API_BASE_URL = ""
   npm run build
   ```

2. **上传并部署**:
   ```powershell
   scp -P 22 -r dist/* root@66.154.108.62:/var/www/novawrite-ai/current/
   ```

## 验证

部署后，访问 http://66.154.108.62，使用以下凭据登录：
- **用户名**: `lanf`
- **密码**: `Gauss_234`

---

**修复时间**: 2025-12-22
**状态**: ✅ 后端已修复，前端需要重新部署



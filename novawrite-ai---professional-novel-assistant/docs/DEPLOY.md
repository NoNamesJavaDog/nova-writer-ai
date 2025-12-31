# 部署指南

## 快速部署

### 方法一：使用部署脚本（推荐）

1. **首次部署 - 设置服务器环境**
   ```bash
   # 在本地执行，会在服务器上设置环境
   ssh root@66.154.108.62 'bash -s' < deploy-setup.sh
   ```

2. **部署应用**
   ```bash
   # 在项目根目录执行
   ./deploy.sh
   ```

### 方法二：手动部署

1. **构建项目**
   ```bash
   npm run build
   ```

2. **上传到服务器**
   ```bash
   # 创建部署目录
   ssh root@66.154.108.62 "mkdir -p /var/www/novawrite-ai/current"
   
   # 上传文件
   scp -r dist/* root@66.154.108.62:/var/www/novawrite-ai/current/
   ```

3. **配置nginx**
   ```bash
   # 复制nginx配置
   scp nginx.conf.example root@66.154.108.62:/etc/nginx/sites-available/novawrite-ai
   
   # 在服务器上执行
   ssh root@66.154.108.62
   ln -s /etc/nginx/sites-available/novawrite-ai /etc/nginx/sites-enabled/
   nginx -t
   systemctl restart nginx
   ```

## 服务器要求

- Ubuntu/Debian Linux
- Nginx（脚本会自动安装）
- 至少 500MB 可用空间

## 部署目录结构

```
/var/www/novawrite-ai/
├── current/          # 当前版本
└── backup-*/         # 备份版本
```

## 访问地址

部署完成后，访问：`http://66.154.108.62:6547`

## 注意事项

1. **环境变量**：生产环境需要在服务器上配置环境变量，或者修改代码使用不同的配置方式
2. **HTTPS**：建议使用 Let's Encrypt 配置 HTTPS
3. **防火墙**：确保服务器开放了 80 和 443 端口
4. **API Key**：确保在服务器环境中配置了 GEMINI_API_KEY

## 故障排查

1. **检查nginx状态**：`systemctl status nginx`
2. **查看nginx日志**：`tail -f /var/log/nginx/novawrite-ai-error.log`
3. **检查文件权限**：确保 `/var/www/novawrite-ai/current` 目录权限正确


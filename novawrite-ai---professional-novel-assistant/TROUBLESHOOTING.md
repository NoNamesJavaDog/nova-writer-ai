# 部署故障排查指南

## 服务器端检查

### 1. 检查nginx状态
```bash
ssh root@66.154.108.62 "systemctl status nginx"
```

### 2. 检查端口监听
```bash
ssh root@66.154.108.62 "ss -tlnp | grep :80"
```

### 3. 检查应用文件
```bash
ssh root@66.154.108.62 "ls -la /var/www/novawrite-ai/current/"
```

### 4. 检查nginx配置
```bash
ssh root@66.154.108.62 "nginx -t"
```

### 5. 查看访问日志
```bash
ssh root@66.154.108.62 "tail -f /var/log/nginx/novawrite-ai-access.log"
```

## 外部访问问题排查

### 1. 云服务商安全组/防火墙
- **检查云服务商控制台**（如阿里云、腾讯云、AWS等）
- 确保**入站规则**中开放了 **80端口**
- 确保允许来自 `0.0.0.0/0` 的HTTP流量

### 2. 服务器防火墙
```bash
# 如果使用firewalld
ssh root@66.154.108.62 "firewall-cmd --permanent --add-service=http"
ssh root@66.154.108.62 "firewall-cmd --reload"

# 如果使用iptables
ssh root@66.154.108.62 "iptables -I INPUT -p tcp --dport 80 -j ACCEPT"
ssh root@66.154.108.62 "iptables-save"
```

### 3. 网络连通性测试
```bash
# 从本地测试
curl -I http://66.154.108.62
telnet 66.154.108.62 80

# 使用在线工具
# https://www.yougetsignal.com/tools/open-ports/
# 检查端口80是否开放
```

### 4. DNS解析（如果有域名）
```bash
nslookup your-domain.com
dig your-domain.com
```

## 常见问题

### 问题1: 能ping通但无法访问网站
**原因**: 防火墙或安全组未开放80端口
**解决**: 检查云服务商安全组和服务器防火墙

### 问题2: 返回502 Bad Gateway
**原因**: nginx配置错误或应用未运行
**解决**: 检查nginx配置和日志

### 问题3: 返回403 Forbidden
**原因**: 文件权限问题
**解决**: 
```bash
ssh root@66.154.108.62 "chown -R nginx:nginx /var/www/novawrite-ai"
ssh root@66.154.108.62 "chmod -R 755 /var/www/novawrite-ai"
```

### 问题4: 返回默认nginx页面
**原因**: nginx配置优先级问题
**解决**: 已通过创建default.conf解决

## 当前状态

✅ nginx服务运行正常
✅ 应用文件已部署
✅ 服务器本地访问正常
✅ 配置文件正确

⚠️ **如果外部无法访问，请检查：**
1. 云服务商安全组规则（最重要！）
2. 服务器防火墙设置
3. 网络路由和ISP限制

## 快速修复命令

```bash
# 1. 确保nginx运行
ssh root@66.154.108.62 "systemctl restart nginx"

# 2. 开放防火墙（如果使用firewalld）
ssh root@66.154.108.62 "firewall-cmd --permanent --add-service=http && firewall-cmd --reload"

# 3. 检查配置
ssh root@66.154.108.62 "nginx -t && systemctl reload nginx"

# 4. 测试访问
curl -I http://66.154.108.62
```


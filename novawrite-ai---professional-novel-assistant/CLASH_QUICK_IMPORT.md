# Clash 一键导入链接

## 🚀 一键导入链接（推荐）

### clash:// 协议链接

复制下面的链接，在浏览器中打开即可自动导入到 Clash：

```
clash://install-config?url=data:text/plain;base64,cG9ydDogNzg5MApzb2Nrcy1wb3J0OiA3ODkxCmFsbG93LWxhbjogZmFsc2UKbW9kZTogcnVsZQpsb2ctbGV2ZWw6IGluZm8KZXh0ZXJuYWwtY29udHJvbGxlcjogMTI3LjAuMC4xOjkwOTAKCnByb3hpZXM6CiAgLSBuYW1lOiAiVjJSYXktU2VydmVyIgogICAgdHlwZTogdm1lc3MKICAgIHNlcnZlcjogNjYuMTU0LjEwOC42MgogICAgcG9ydDogMTAwODYKICAgIHV1aWQ6IDJlNGEwNzQ1LWE3ZmEtNDljYS04OWJiLTYyYWEyMTM5Yzk1YgogICAgYWx0ZXJJZDogMAogICAgY2lwaGVyOiBhdXRvCiAgICBuZXR3b3JrOiB3cwogICAgd3Mtb3B0czoKICAgICAgcGF0aDogL3JheQogICAgdGxzOiBmYWxzZQoKcHJveHktZ3JvdXBzOgogIC0gbmFtZTogIlBST1hZIgogICAgdHlwZTogc2VsZWN0CiAgICBwcm94aWVzOgogICAgICAtICJWMlJheS1TZXJ2ZXIiCiAgICAgIC0gRElSRUNUCgpydWxlczoKICAtIE1BVENILFBST1hZCgo=
```

**直接点击或复制到浏览器打开即可！**

## 📋 使用方法

### Clash for Windows

1. **方法一（推荐）**：
   - 复制上面的 `clash://` 链接
   - 在浏览器中打开，会自动调用 Clash 导入

2. **方法二**：
   - 打开 Clash for Windows
   - 点击 **Profiles**（配置）
   - 点击 **Download**（下载）
   - 粘贴上面的链接
   - 点击 **Download** 导入

### ClashX (macOS)

1. 复制 `clash://` 链接
2. 在浏览器中打开（Safari 或 Chrome）
3. 系统会自动调用 ClashX 导入配置

### Clash for Android

1. 打开 Clash for Android
2. 点击 **配置**
3. 点击 **新建配置**
4. 选择 **从URL导入**
5. 粘贴上面的 `clash://` 链接
6. 点击 **确定**

## 🔧 手动配置（如果链接无法使用）

如果一键导入链接无法使用，可以手动添加以下配置：

```yaml
proxies:
  - name: "V2Ray-Server"
    type: vmess
    server: 66.154.108.62
    port: 10086
    uuid: 2e4a0745-a7fa-49ca-89bb-62aa2139c95b
    alterId: 0
    cipher: auto
    network: ws
    ws-opts:
      path: /ray
    tls: false
```

## 📝 服务器信息

- **服务器地址**: 66.154.108.62
- **端口**: 10086
- **UUID**: 2e4a0745-a7fa-49ca-89bb-62aa2139c95b
- **传输协议**: WebSocket (ws)
- **路径**: /ray
- **alterId**: 0

## ✅ 验证连接

导入配置后：

1. 在 Clash 中选择 "V2Ray-Server" 代理
2. 检查连接状态（应显示为已连接/绿色）
3. 访问测试网站验证

## 🔍 故障排查

如果无法连接：

1. 检查 Clash 是否正在运行
2. 确认代理已选择 "V2Ray-Server"
3. 检查服务器状态：`ssh root@66.154.108.62 "systemctl status v2ray"`
4. 查看日志：`ssh root@66.154.108.62 "tail -20 /var/log/v2ray/error.log"`


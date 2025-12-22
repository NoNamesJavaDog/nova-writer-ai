# Clash 一键导入链接

## 方法一：使用 clash:// 协议链接（推荐）

### 完整配置链接

```
clash://install-config?url=data:text/plain;base64,cG9ydDogNzg5MApzb2Nrcy1wb3J0OiA3ODkxCmFsbG93LWxhbi: falseKbW9kZTogcnVsZQpsb2ctbGV2ZWw6IGluZm8KZXh0ZXJuYWwtY29udHJvbGxlcjogMTI3LjAuMC4xOjkwOTAKCnByb3hpZXM6CiAgLSBuYW1lOiAiVjJSYXktU2VydmVyIgogICAgdHlwZTogdm1lc3MKICAgIHNlcnZlcjogNjYuMTU0LjEwOC42MgogICAgcG9ydDogMTAwODYKICAgIHV1aWQ6IDJlNGEwNzQ1LWE3ZmEtNDljYS04OWJiLTYyYWEyMTM5Yzk1YgogICAgYWx0ZXJJZDogMAogICAgY2lwaGVyOiBhdXRvCiAgICBuZXR3b3JrOiB3cwogICAgd3Mtb3B0czoKICAgICAgcGF0aDogL3JheQogICAgdGxzOiBmYWxzZQoKcHJveHktZ3JvdXBzOgogIC0gbmFtZ: "PROXY"CiAgICB0eXBlOiBzZWxlY3QKICAgIHByb3hpZXM6CiAgICAgIC0gIlYyUmF5LVNlcnZlciIKICAgICAgLSBESVJFQ1QKCnJ1bGVzOgogIC0gTUFUQ0gsUFJPWFk=
```

### 使用方法

1. **Clash for Windows**:
   - 复制上面的链接
   - 在浏览器中打开，会自动调用 Clash 导入
   - 或者在 Clash 中点击 **Profiles** → **Download** → 粘贴链接

2. **ClashX (macOS)**:
   - 复制链接
   - 在浏览器中打开，会自动导入到 ClashX

3. **Clash for Android**:
   - 复制链接
   - 在 Clash for Android 中点击 **配置** → **新建配置** → **从URL导入**
   - 粘贴链接

## 方法二：使用订阅链接

如果你有服务器可以托管配置文件，可以创建一个订阅链接：

```
http://your-server.com/clash-config.yaml
```

## 方法三：手动导入配置文件

1. 下载 `clash-subscription.yaml` 文件
2. 在 Clash 客户端中：
   - **Clash for Windows**: Profiles → 点击配置 → Edit → 粘贴内容
   - **ClashX**: 配置 → 打开配置文件夹 → 编辑 config.yaml
   - **Clash for Android**: 配置 → 新建配置 → 从文件导入

## 配置信息

- **服务器**: 66.154.108.62
- **端口**: 10086
- **UUID**: 2e4a0745-a7fa-49ca-89bb-62aa2139c95b
- **传输协议**: ws
- **路径**: /ray

## 注意事项

1. 确保 Clash 客户端已安装并运行
2. 某些浏览器可能需要手动确认打开 Clash 应用
3. 如果链接无法直接打开，可以手动复制配置内容


# Clash 客户端配置指南

## V2Ray 服务器信息

- **服务器地址**: `66.154.108.62`
- **端口**: `10086`
- **UUID**: `2e4a0745-a7fa-49ca-89bb-62aa2139c95b`
- **传输协议**: WebSocket (ws)
- **路径**: `/ray`
- **alterId**: `0`

## Clash 配置方法

### 方法一：在现有配置中添加代理

在你的 Clash 配置文件的 `proxies` 部分添加：

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

然后在 `proxy-groups` 中添加这个代理：

```yaml
proxy-groups:
  - name: "PROXY"
    type: select
    proxies:
      - "V2Ray-Server"
      - DIRECT
```

### 方法二：使用完整配置

完整的 Clash 配置示例（`CLASH_CONFIG.yaml`）：

```yaml
port: 7890
socks-port: 7891
allow-lan: false
mode: rule
log-level: info
external-controller: 127.0.0.1:9090

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

proxy-groups:
  - name: "PROXY"
    type: select
    proxies:
      - "V2Ray-Server"
      - DIRECT

rules:
  - MATCH,PROXY
```

## Clash 客户端使用步骤

### Clash for Windows

1. 打开 Clash for Windows
2. 点击 **Profiles**（配置）
3. 点击 **Edit**（编辑）或 **New**（新建）
4. 将上述配置添加到配置文件中
5. 保存并重新加载配置
6. 在 **Proxies**（代理）中选择 "V2Ray-Server"

### ClashX (macOS)

1. 打开 ClashX
2. 点击菜单栏图标 → **配置** → **打开配置文件夹**
3. 编辑 `config.yaml` 文件
4. 添加上述代理配置
5. 点击菜单栏图标 → **配置** → **重新加载配置**
6. 选择 "V2Ray-Server" 代理

### Clash for Android

1. 打开 Clash for Android
2. 点击 **配置**
3. 点击 **新建配置** 或编辑现有配置
4. 添加上述代理配置
5. 保存并应用配置
6. 在代理列表中选择 "V2Ray-Server"

## 配置参数说明

- **name**: 代理名称（可自定义）
- **type**: 代理类型，使用 `vmess`
- **server**: V2Ray 服务器地址
- **port**: V2Ray 服务器端口
- **uuid**: 用户ID（从v2ray配置中获取）
- **alterId**: 额外ID，设置为 `0`
- **cipher**: 加密方式，使用 `auto`
- **network**: 传输协议，使用 `ws` (WebSocket)
- **ws-opts**: WebSocket 选项
  - **path**: WebSocket 路径
- **tls**: 是否启用TLS，当前为 `false`

## 测试连接

配置完成后：

1. 在 Clash 中选择 "V2Ray-Server" 代理
2. 检查连接状态（应该显示为绿色/已连接）
3. 访问 https://www.google.com 测试是否成功

## 故障排查

如果无法连接：

1. **检查服务器状态**
   ```bash
   ssh root@66.154.108.62 "systemctl status v2ray"
   ```

2. **检查端口监听**
   ```bash
   ssh root@66.154.108.62 "ss -tlnp | grep 10086"
   ```

3. **检查防火墙**
   ```bash
   ssh root@66.154.108.62 "firewall-cmd --list-ports | grep 10086"
   ```

4. **查看 V2Ray 日志**
   ```bash
   ssh root@66.154.108.62 "tail -20 /var/log/v2ray/error.log"
   ```

5. **检查云服务商安全组**
   - 确保在云服务商控制台开放 10086 端口

## 更新配置

如果服务器配置更改（如UUID、端口等），只需更新 Clash 配置文件中的相应参数即可。


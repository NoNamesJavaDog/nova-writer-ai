# V2Ray VPN 服务端配置信息

## 服务器信息

- **服务器地址**: `66.154.108.62`
- **端口**: `10086`
- **UUID**: `2e4a0745-a7fa-49ca-89bb-62aa2139c95b`
- **传输协议**: WebSocket (ws)
- **路径**: `/ray`
- **alterId**: `0`

## 客户端配置

### V2RayN / V2RayNG 配置

```
地址(Address): 66.154.108.62
端口(Port): 10086
用户ID(UUID): 2e4a0745-a7fa-49ca-89bb-62aa2139c95b
额外ID(AlterId): 0
加密方式(Security): auto
传输协议(Network): ws
伪装类型(Header Type): none
路径(Path): /ray
```

### JSON 配置格式

```json
{
  "v": "2",
  "ps": "V2Ray Server",
  "add": "66.154.108.62",
  "port": "10086",
  "id": "2e4a0745-a7fa-49ca-89bb-62aa2139c95b",
  "aid": "0",
  "scy": "auto",
  "net": "ws",
  "type": "none",
  "host": "",
  "path": "/ray",
  "tls": "none"
}
```

### VMESS 链接

```
vmess://eyJ2IjoiMiIsInBzIjoiVjJSYXkgU2VydmVyIiwiYWRkIjoiNjYuMTU0LjEwOC42MiIsInBvcnQiOiIxMDA4NiIsImlkIjoiMmU0YTA3NDUtYTdmYS00OWNhLTg5YmItNjJhYTIxMzljOTViIiwiYWlkIjoiMCIsInNjeSI6ImF1dG8iLCJuZXQiOiJ3cyIsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIvcmF5IiwidGxzIjoibm9uZSJ9
```

## 服务管理命令

```bash
# 查看服务状态
systemctl status v2ray

# 启动服务
systemctl start v2ray

# 停止服务
systemctl stop v2ray

# 重启服务
systemctl restart v2ray

# 查看日志
tail -f /var/log/v2ray/access.log
tail -f /var/log/v2ray/error.log

# 测试配置
/usr/local/bin/v2ray test -config /usr/local/etc/v2ray/config.json
```

## 防火墙状态

- **端口 10086**: 已开放（firewalld + iptables）
- **服务状态**: 运行中
- **监听地址**: 0.0.0.0:10086

## 注意事项

1. **云服务商安全组**: 确保在云服务商控制台开放 10086 端口的入站规则
2. **客户端配置**: 使用上述配置信息在客户端中配置连接
3. **测试连接**: 配置完成后测试连接是否正常
4. **日志查看**: 如有问题，查看 `/var/log/v2ray/error.log`

## 更新配置

如需修改配置（如更改端口、UUID等），编辑 `/usr/local/etc/v2ray/config.json` 后重启服务：

```bash
systemctl restart v2ray
```


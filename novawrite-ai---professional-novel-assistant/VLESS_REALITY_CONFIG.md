# VLESS Reality 配置信息

## 服务器信息

- **协议类型**: VLESS Reality
- **服务器地址**: `66.154.108.62`
- **端口**: `10011`
- **用户ID (UUID)**: `65488062-2ae6-4a68-a703-e10b0774e4dc`
- **传输方式**: TCP
- **账户名**: `65488062-vless_reality_vision`

## Reality 配置

- **Public Key**: `GIQGinCWuISE73QK90EVQtcz0Mu7iBsZHRZA0DzS-zE`
- **Short ID**: `6ba85179e30d4fc2`
- **Server Name**: `images-na.ssl-images-amazon.com`
- **Dest**: `images-na.ssl-images-amazon.com:443`

## 客户端配置

### V2RayN / V2RayNG 配置

```
协议: VLESS
地址: 66.154.108.62
端口: 10011
用户ID: 65488062-2ae6-4a68-a703-e10b0774e4dc
流控: 空（不填）
加密: none
传输协议: tcp
伪装类型: none
TLS: reality
SNI: images-na.ssl-images-amazon.com
Public Key: GIQGinCWuISE73QK90EVQtcz0Mu7iBsZHRZA0DzS-zE
Short ID: 6ba85179e30d4fc2
```

### JSON 配置格式

```json
{
  "v": "2",
  "ps": "VLESS-Reality-Server",
  "add": "66.154.108.62",
  "port": "10011",
  "id": "65488062-2ae6-4a68-a703-e10b0774e4dc",
  "aid": "0",
  "scy": "none",
  "net": "tcp",
  "type": "none",
  "host": "",
  "path": "",
  "tls": "reality",
  "sni": "images-na.ssl-images-amazon.com",
  "alpn": "",
  "fp": "",
  "pbk": "GIQGinCWuISE73QK90EVQtcz0Mu7iBsZHRZA0DzS-zE",
  "sid": "6ba85179e30d4fc2"
}
```

### VLESS 链接

```
vless://65488062-2ae6-4a68-a703-e10b0774e4dc@66.154.108.62:10011?type=tcp&security=reality&sni=images-na.ssl-images-amazon.com&pbk=GIQGinCWuISE73QK90EVQtcz0Mu7iBsZHRZA0DzS-zE&sid=6ba85179e30d4fc2&fp=chrome#VLESS-Reality-Server
```

## Clash 配置

**注意**: Clash 可能不完全支持 VLESS Reality。建议使用 V2RayN、V2RayNG 或其他支持 Reality 的客户端。

如果使用 Clash，可以尝试以下配置（可能不工作）：

```yaml
proxies:
  - name: "VLESS-Reality"
    type: vless
    server: 66.154.108.62
    port: 10011
    uuid: 65488062-2ae6-4a68-a703-e10b0774e4dc
    network: tcp
    tls: true
    reality-opts:
      public-key: GIQGinCWuISE73QK90EVQtcz0Mu7iBsZHRZA0DzS-zE
      short-id: 6ba85179e30d4fc2
      server-name: images-na.ssl-images-amazon.com
```

## 推荐客户端

1. **V2RayN** (Windows) - 完全支持 VLESS Reality
2. **V2RayNG** (Android) - 完全支持 VLESS Reality
3. **v2ray-core** (命令行) - 完全支持
4. **Clash Meta** - 部分支持，可能需要特定版本

## 服务管理

```bash
# 查看服务状态
ssh root@66.154.108.62 "systemctl status v2ray"

# 重启服务
ssh root@66.154.108.62 "systemctl restart v2ray"

# 查看日志
ssh root@66.154.108.62 "tail -f /var/log/v2ray/error.log"
```

## 防火墙状态

- **端口 10011**: 已开放（firewalld + iptables）
- **服务状态**: 运行中

## 注意事项

1. **云服务商安全组**: 确保在云服务商控制台开放 10011 端口的入站规则
2. **客户端兼容性**: 确保使用支持 VLESS Reality 的客户端
3. **Reality 特性**: Reality 是 V2Ray 的伪装技术，可以更好地绕过检测


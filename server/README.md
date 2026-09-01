# 轻盈工作台 · 后端部署指南（阿里云学生机 · 账号版）

## 0. 前置（只能本人操作）
1. 注册阿里云账号（手机号 + 实名认证）
2. **学生认证**：搜索「阿里云学生机」/「高校学生认证」，用**学信网**验证学籍
3. 购买**轻量应用服务器（学生机）**：2 核 2G，系统镜像选 **Ubuntu 22.04**
4. 买完在控制台记下：**公网 IP**、**root 密码**
5. 控制台「安全组」放行 **22**（SSH）、**80**（HTTP）端口

## 1. 连接服务器
```bash
ssh root@你的服务器IP
# 输入 root 密码
```

## 2. 安装 Node.js 20
```bash
cd /root
wget https://mirrors.aliyun.com/nodejs-release/v20.18.0/node-v20.18.0-linux-x64.tar.xz
tar -xf node-v20.18.0-linux-x64.tar.xz
mv node-v20.18.0-linux-x64 /usr/local/node
ln -sf /usr/local/node/bin/node /usr/local/bin/node
ln -sf /usr/local/node/bin/npm /usr/local/bin/npm
node -v   # 应显示 v20.18.0
```

## 3. 部署本后端
```bash
# 在本机把 server 文件夹传到服务器（也可以用 SFTP/宝塔上传）
scp -r server root@你的服务器IP:/root/jianzhi-server

# 上服务器装依赖
cd /root/jianzhi-server
npm install
```

## 4. 用 systemd 常驻运行（开机自启）
写 `/etc/systemd/system/jianzhi-server.service`：
```ini
[Unit]
Description=Jianzhi Sync Server (账号版)
After=network.target

[Service]
WorkingDirectory=/root/jianzhi-server
Environment=NODE_ENV=production
Environment=PORT=80
ExecStart=/usr/local/bin/node server.js
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```
```bash
systemctl daemon-reload
systemctl enable jianzhi-server
systemctl restart jianzhi-server
systemctl status jianzhi-server   # active (running) 即成功
```

## 5. 测试接口
```bash
curl http://你的服务器IP/health
# {"ok":true}

# 注册一个账号（会返回 token）
curl -X POST http://你的服务器IP/api/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"abc12345"}'

# 登录
curl -X POST http://你的服务器IP/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"abc12345"}'
```

## 6. 回到应用
在 App「目标页 → 云端同步」填：
- **服务器地址**：`http://你的服务器IP`
- **用户名 + 密码**：注册的账号

登录后自动同步。**每个人注册自己的账号，数据互相独立。**

## 接口一览
| 接口 | 说明 |
|---|---|
| `POST /api/register` | 注册，body `{username,password}`，返回 token |
| `POST /api/login` | 登录，返回 token |
| `POST /api/logout` | 登出，请求头 `x-token` |
| `GET /api/data` | 取当前账号数据，请求头 `x-token` |
| `PUT /api/data` | 存当前账号数据，请求头 `x-token`，body 为完整数据对象 |

数据文件：
- `users.json` — 账号（scrypt 哈希，不存明文密码）
- `sessions.json` — 登录 token → 用户名（持久化，重启不掉线）
- `data/<用户名>.json` — 每个用户独立的数据

## 常见问题
- **80 端口打不开**：阿里云控制台 → 安全组 → 入方向放行 TCP 80（来源 0.0.0.0/0）
- **接口 401**：`x-token` 是登录/注册返回的 token，不是密码；token 丢了重新登录即可
- **改了 server.js**：重新上传后 `systemctl restart jianzhi-server`
- **备份服务器数据**：备份 `/root/jianzhi-server/` 下的 `users.json`、`sessions.json`、`data/` 即可

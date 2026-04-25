---
categories:
- 运维
date: 2026-04-23
description: 详细介绍购买云服务器、安装Ubuntu系统、部署1Panel面板，并配置CoPaw（龙虾）AI个人助理套件的完整教程
image: /images/cover-devops.svg
lastmod: 2026-04-23
tags:
- 云服务器
- 1Panel
- CoPaw
- AI助手
- Ubuntu
title: 从零搭建AI个人助理环境：云服务器 + 1Panel + CoPaw
---

# 从零搭建 AI 个人助理环境：云服务器 + 1Panel + CoPaw

> 本文详细介绍如何购买云服务器，安装 Ubuntu 系统，部署 1Panel 面板，并配置 CoPaw（龙虾）AI 个人助理套件。适合技术爱好者搭建自己的 AI 工作流环境。

## 前言

你是否想过拥有一个 **24 小时在线的 AI 助手**？帮你处理信息、追踪资讯、提醒待办、甚至陪你聊天？

本文将手把手教你搭建一套完整的 AI 个人助理环境，基于 **CoPaw（龙虾）** —— 一个多智能体协作框架，让 AI 不再只是问答机器，而是真正能帮你干活的助手。

## 一、购买云服务器

### 1.1 选择云服务商

国内主流云服务商：

| 云厂商 | 特点 | 推荐配置 | 优惠入口 |
|:---|:---|:---|:---|
| 腾讯云 | 性价比高，生态完善 | 2核4G 50GB SSD | [限时优惠](https://curl.qcloud.com/mFofiULO) |
| 阿里云 | 稳定性强，活动多 | 2核2G 40GB | [ECS特惠](https://www.aliyun.com/daily-act/ecs/activity_selection?userCode=rwjv3frv) |
| UCloud | 价格优惠 | 2核2G 40GB | [云服务器](https://www.ucloud.cn/site/active/openclaw?cps_code=4ekQdaU0wlSDjuTbopBkOp) |

> 💡 需要购买云服务器的朋友，可通过上方链接前往各大平台选购。

### 1.2 推荐配置

**最低配置（体验用）：**
- CPU: 2 核
- 内存: 4 GB
- 硬盘: 50 GB SSD
- 带宽: 3 Mbps
- 系统: Ubuntu 22.04 LTS

**推荐配置（生产用）：**
- CPU: 2 核
- 内存: 4-8 GB
- 硬盘: 100 GB SSD
- 带宽: 5 Mbps
- 系统: Ubuntu 22.04 LTS

### 1.3 购买注意事项

1. **地域选择**：选择离你最近的地域，延迟更低
2. **系统盘**：建议 SSD，性能更好
3. **安全组**：放行 22（SSH）、80（HTTP）、443（HTTPS）端口
4. **账号密钥**：创建后立即下载私钥文件，丢失无法找回

## 二、安装 Ubuntu 系统

> 如果你在购买时已选择 Ubuntu 系统，可跳过此步骤。

### 2.1 重装系统（以腾讯云为例）

1. 登录云服务器控制台
2. 选择目标服务器 → 更多 → 资源调整 → 重装系统
3. 选择 **Ubuntu 22.04 LTS 64位**
4. 设置 root 密码或导入密钥
5. 等待重装完成（约 5-10 分钟）

### 2.2 连接服务器

**Mac/Linux 终端连接：**

```bash
ssh root@你的服务器IP
```

**Windows 使用 PowerShell 连接：**

```powershell
ssh root@你的服务器IP
```

### 2.3 初始化配置

```bash
# 更新系统软件包
apt update && apt upgrade -y

# 创建新用户（不建议直接用 root）
adduser yison
usermod -aG sudo yison

# 切换到新用户
su - yison

# 配置 SSH 免密登录（可选）
mkdir ~/.ssh
chmod 700 ~/.ssh
touch ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

## 三、安装 1Panel 面板

### 3.1 什么是 1Panel

[1Panel](https://1panel.cn/) 是一个现代化的 Linux 服务器管理面板，提供：
- Web 界面管理服务器
- 应用商店一键安装软件
- 容器管理
- 防火墙配置
- 定时任务
- 备份恢复

### 3.2 一键安装

```bash
# 以 root 用户执行
curl -sSL https://resource.fit2cloud.com/1panel/package/quick_start.sh -o quick_start.sh && bash quick_start.sh
```

安装过程会提示选择版本（选稳定版），确认后自动安装。

### 3.3 安装完成

安装成功后，记录以下信息：
- **访问地址**：`http://你的服务器IP:20659`
- **查看密码**：`cat /opt/1panel/initial passwords.txt`

### 3.4 安全加固

1. 修改默认端口（在 1Panel 面板 → 主机 → 端口规则 中修改）
2. 配置防火墙：
   ```bash
   ufw allow 20659/tcp
   ufw allow 22/tcp
   ufw enable
   ```
3. 设置 SSL 证书（在 1Panel 面板 → 网站 → SSL 证书 → Let's Encrypt）

## 四、安装 CoPaw 龙虾套件

### 4.1 什么是 CoPaw

CoPaw（谐音「龙虾」）是一个基于 AI 大语言模型的个人助理框架，支持：
- **多 Agent 协作**：多个 AI 角色分工合作
- **定时任务**：晨晚报告、周期性提醒
- **技能扩展**：可定制的技能插件
- **多渠道接入**：支持 QQ、Telegram、微信等

### 4.2 通过 1Panel 应用商店安装（推荐）

1. 登录 1Panel 面板
2. 进入 **应用商店**
3. 搜索 **CoPaw** 或 **龙框架**
4. 点击安装，配置参数

### 4.3 手动安装

```bash
# 创建安装目录
sudo mkdir -p /opt/copaw
cd /opt/copaw

# 下载最新版本
wget https://github.com/your-repo/copaw/releases/latest/copaw-linux-amd64.tar.gz

# 解压
tar -xzf copaw-linux-amd64.tar.gz

# 赋予执行权限
chmod +x copaw

# 验证安装
./copaw --version
```

### 4.4 配置系统服务

```bash
# 创建 systemd 服务文件
sudo tee /etc/systemd/system/copaw.service << 'EOF'
[Unit]
Description=CoPaw AI Assistant
After=network.target

[Service]
Type=simple
User=yison
WorkingDirectory=/opt/copaw
ExecStart=/opt/copaw/copaw serve
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 启用并启动服务
sudo systemctl daemon-reload
sudo systemctl enable copaw
sudo systemctl start copaw

# 查看状态
sudo systemctl status copaw
```

## 五、配置 MiniMax API Key

### 5.1 获取 API Key

> 💡 新用户可通过 [此链接](https://platform.minimaxi.com/subscribe/token-plan?code=JnGYGFFOVU&source=link) 注册获得免费 tokens 额度。

1. 访问 MiniMax 开放平台并注册账号
2. 注册/登录账号
3. 进入控制台 → API Keys
4. 创建新密钥，保存好（只显示一次）

### 5.2 配置环境变量

```bash
# 编辑环境变量文件
sudo tee /opt/copaw/.env << 'EOF'
# MiniMax API 配置
MINIMAX_API_KEY=your_api_key_here
MINIMAX_MODEL=abab6.5s-chat

# 服务配置
COPAW_PORT=8080
COPAW_SECRET=your_secret_key

# 日志配置
LOG_LEVEL=info
EOF

# 复制到用户目录
mkdir -p ~/.copaw
cp /opt/copaw/.env ~/.copaw/.env
chmod 600 ~/.copaw/.env
```

### 5.3 在 1Panel 中配置

1. 登录 1Panel → 应用商店 → 找到 CoPaw
2. 点击 **设置** → **环境变量**
3. 添加：`MINIMAX_API_KEY = 你的API密钥`
4. 保存并重启应用

### 5.4 验证配置

```bash
# 测试 API 连接
curl -X POST http://localhost:8080/api/health \
  -H "Content-Type: application/json" \
  -d '{"test": true}'

# 查看日志
sudo journalctl -u copaw -f
```

## 六、配置 QQ 机器人（可选）

### 6.1 创建 QQ 机器人

1. 登录 [QQ 开放平台](https://q.qq.com/)
2. 创建应用 → 选择「机器人」类型
3. 获取 AppID 和 Token

### 6.2 配置 QQ 频道

在 `.env` 中添加：

```bash
QQ_APP_ID=your_app_id
QQ_TOKEN=your_token
QQ_SECRET=your_secret

# 重启服务
sudo systemctl restart copaw
```

## 七、配置定时任务

### 7.1 晨晚报任务

CoPaw 支持配置定时任务，自动执行：

| 任务 | 时间 | 内容 |
|:---|:---|:---|
| 🌅 晨报 | 每天 09:10 | 技术前沿 + 财经重点 + 热点速览 |
| 🌙 晚安 | 每天 22:30 | 今日总结 + 待办顺延 |
| 📈 周报 | 每周日 23:00 | 本周工作复盘 + 技能迭代 |

### 7.2 配置方法

1. 登录 1Panel → 定时任务
2. 创建新任务，选择 **CoPaw** 模板
3. 配置执行时间和 Prompt 模板
4. 保存并启用

## 八、验证与使用

### 8.1 访问 CoPaw

```bash
# 查看服务状态
sudo systemctl status copaw

# 查看服务日志
sudo journalctl -u copaw -f

# 访问 Web 界面
http://你的服务器IP:8080
```

### 8.2 基本使用

配置完成后，你的 AI 助手将自动：
- 📰 每天 09:10 推送晨报（技术 + 财经 + 热点）
- 🌙 每天 22:30 发送晚安总结
- 📈 每周日自动复盘

你也可以随时通过 QQ 频道与助手对话，获取帮助。

## 九、常见问题

### Q1: 1Panel 安装失败？

**原因**：系统要求不满足或网络问题。

**解决**：
1. 确认系统为 Ubuntu 20.04+ 或 Debian 11+
2. 检查网络连接：`ping -c 3 8.8.8.8`
3. 查看安装日志获取详细错误信息

### Q2: CoPaw 无法启动？

**排查步骤**：
1. 检查 MiniMax API Key 是否正确
2. 检查端口是否被占用：`netstat -tlnp | grep 8080`
3. 查看日志定位问题：`journalctl -u copaw -n 100`

### Q3: 定时任务没有执行？

**排查步骤**：
1. 检查系统时间是否正确：`timedatectl`
2. 确认定时任务已启用
3. 检查 CoPaw 服务是否正常运行：`systemctl status copaw`

### Q4: QQ 机器人无法接收消息？

**排查步骤**：
1. 确认 QQ 机器人已添加至频道
2. 检查 AppID、Token、Secret 是否正确
3. 查看 CoPaw 日志确认连接状态

## 十、进阶玩法

### 10.1 自定义 Agent 角色

CoPaw 支持自定义 Agent 角色，你可以：
- 创建专属的 AI 助手形象
- 定制技能和工作流程
- 调整输出风格和语气

### 10.2 扩展技能插件

通过编写技能插件，可以实现：
- 自动抓取特定网站内容
- 接入第三方 API
- 实现自动化工作流

### 10.3 多渠道接入

除了 QQ，CoPaw 还支持：
- Telegram
- 微信（通过企业微信）
- Slack
- 自定义 Web 界面

## 结语

通过本文，你已经拥有了一套完整的 AI 个人助理环境。这只是开始 —— CoPaw 支持丰富的扩展能力，你可以根据需要定制技能、调整 Agent 角色，打造专属的 AI 助手。

祝你玩得开心！

---

*有问题？欢迎在评论区留言交流。*
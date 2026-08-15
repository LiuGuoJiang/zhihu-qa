# 腾讯云服务器部署手册

## 知乎内容工作室 - Paperclip 智能体系统

本文档提供在腾讯云服务器上完整部署知乎内容工作室系统的详细步骤。

---

## 目录

1. [服务器要求](#服务器要求)
2. [基础环境安装](#基础环境安装)
3. [项目部署](#项目部署)
4. [浏览器环境配置](#浏览器环境配置)
5. [Paperclip 安装](#paperclip-安装)
6. [服务启动](#服务启动)
7. [验证部署](#验证部署)
8. [故障排查](#故障排查)

---

## 服务器要求

### 推荐配置

| 资源 | 最低配置 | 推荐配置 |
|------|----------|----------|
| CPU | 2核 | 4核+ |
| 内存 | 4GB | 8GB+ |
| 硬盘 | 40GB | 100GB+ |
| 系统 | Ubuntu 20.04+ | Ubuntu 22.04 LTS |
| 网络 | 5Mbps | 10Mbps+ |

### 操作系统

```bash
# 查看系统版本
cat /etc/os-release

# 推荐：Ubuntu 22.04 LTS
```

---

## 基础环境安装

### 1. 更新系统

```bash
# 连接到腾讯云服务器
ssh root@your_server_ip

# 更新系统包
sudo apt update && sudo apt upgrade -y
```

### 2. 安装基础工具

```bash
# 安装基础工具
sudo apt install -y curl wget git vim unzip build-essential

# 安装 Python 和 pip
sudo apt install -y python3.12 python3.12-venv python3-pip

# 验证安装
python3 --version
pip3 --version
```

### 3. 安装 Node.js (Claude Code 需要)

```bash
# 安装 Node.js 20.x
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# 验证安装
node --version
npm --version
```

### 4. 安装 Playwright 浏览器依赖

```bash
# 安装 Playwright 系统依赖
sudo apt install -y \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpangocairo-1.0-0 \
    libpango-1.0-0 \
    libatspi2.0-0 \
    libxshmfence1

# 安装 Chrome 浏览器
sudo apt install -y chromium-browser
```

### 5. 安装 Selenium/浏览器驱动（可选，有头模式需要）

```bash
# 如果需要使用有头浏览器（登录等操作）
sudo apt install -y xvfb

# 设置显示环境
export DISPLAY=:99
Xvfb :99 -screen 0 1920x1080x24 > /dev/null 2>&1 &
```

---

## 项目部署

### 1. 克隆项目

```bash
# 创建项目目录
sudo mkdir -p /opt/zhihu-qa
sudo chown $USER:$USER /opt/zhihu-qa

# 克隆项目
cd /opt/zhihu-qa
git clone git@github.com:LiuGuoJiang/zhihu-qa.git .
# 或者使用 HTTPS:
# git clone https://github.com/LiuGuoJiang/zhihu-qa.git .

# 查看项目结构
ls -la
```

### 2. 创建 Python 虚拟环境

```bash
cd /opt/zhihu-qa

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 升级 pip
pip install --upgrade pip
```

### 3. 安装 Python 依赖

```bash
# 安装依赖
pip install -r requirements.txt

# 安装 Playwright 浏览器
playwright install chromium
playwright install-deps chromium
```

### 4. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量（根据需要修改）
vim .env
```

`.env` 文件内容示例：

```bash
# 知乎登录配置
ZHIHU_USERNAME=your_email_or_phone
ZHIHU_PASSWORD=your_password

# 浏览器配置
HEADLESS=true
BROWSER_TIMEOUT=30000

# 数据存储路径
DATA_PATH=/opt/zhihu-qa/data

# MCP 服务配置
MCP_SERVER_PORT=3000
```

### 5. 创建必要的目录

```bash
# 创建数据目录
mkdir -p data/questions
mkdir -p data/materials
mkdir -p data/drafts
mkdir -p data/sessions

# 设置权限
chmod -R 755 data
```

---

## 浏览器环境配置

### 1. 首次登录（有头模式）

在服务器上首次运行时，需要使用有头模式完成知乎登录：

```bash
cd /opt/zhihu-qa
source venv/bin/activate

# 运行登录脚本（有头模式）
python scripts/zhihu_rpa.py --login
```

如果使用 Xvfb，可以先设置显示：

```bash
export DISPLAY=:99
python scripts/zhihu_rpa.py --login
```

### 2. 验证登录

登录成功后，会话文件会保存在 `data/sessions/` 目录。

### 3. 测试 RPA 功能

```bash
# 测试获取推荐问题
python scripts/zhihu_rpa.py --test get_recommended

# 测试搜索问题
python scripts/zhihu_rpa.py --test search --keyword "人工智能"
```

---

## Paperclip 安装

### 1. 安装 Claude Code CLI

```bash
# 使用 npm 安装 Claude Code
npm install -g @anthropic-ai/claude-code

# 验证安装
claude --version
```

### 2. 配置 Claude API 密钥

```bash
# 设置 API 密钥
claude config set api_key your_anthropic_api_key

# 验证配置
claude config get
```

### 3. 初始化 Paperclip 项目

```bash
cd /opt/zhihu-qa

# Paperclip 配置已包含在项目中
# 查看 Paperclip 配置
cat .paperclip/company.yaml
```

### 4. 测试 Paperclip

```bash
# 测试单个智能体
cd /opt/zhihu-qa
claude agent run question_scout

# 查看智能体日志
tail -f .paperclip/logs/question_scout.log
```

---

## 服务启动

### 方案一：使用 systemd 服务

#### 1. 创建 Paperclip 服务

```bash
sudo vim /etc/systemd/system/paperclip.service
```

添加以下内容：

```ini
[Unit]
Description=Paperclip Intelligent Agents System
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/opt/zhihu-qa
Environment="PATH=/opt/zhihu-qa/venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="DISPLAY=:99"
ExecStart=/usr/local/bin/claude agent run --all
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### 2. 启动服务

```bash
# 重载 systemd 配置
sudo systemctl daemon-reload

# 启动 Paperclip 服务
sudo systemctl start paperclip

# 设置开机自启
sudo systemctl enable paperclip

# 查看服务状态
sudo systemctl status paperclip

# 查看服务日志
sudo journalctl -u paperclip -f
```

### 方案二：使用 Screen/Tmux

```bash
# 使用 Screen
screen -S paperclip
cd /opt/zhihu-qa
source venv/bin/activate
claude agent run --all

# 按 Ctrl+A 然后按 D 分离会话

# 重新连接
screen -r paperclip
```

```bash
# 使用 Tmux
tmux new -s paperclip
cd /opt/zhihu-qa
source venv/bin/activate
claude agent run --all

# 按 Ctrl+B 然后按 D 分离会话

# 重新连接
tmux attach -t paperclip
```

### 方案三：使用 Supervisor

```bash
# 安装 Supervisor
sudo apt install -y supervisor

# 创建配置文件
sudo vim /etc/supervisor/conf.d/paperclip.conf
```

添加以下内容：

```ini
[program:paperclip]
command=/usr/local/bin/claude agent run --all
directory=/opt/zhihu-qa
user=your_username
autostart=true
autorestart=true
stderr_logfile=/var/log/paperclip.err.log
stdout_logfile=/var/log/paperclip.out.log
environment=DISPLAY=":99"
```

启动服务：

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start paperclip
```

---

## 验证部署

### 1. 检查服务状态

```bash
# 检查 Paperclip 服务
sudo systemctl status paperclip

# 检查进程
ps aux | grep claude
ps aux | grep playwright
```

### 2. 测试 MCP 服务器

```bash
cd /opt/zhihu-qa
source venv/bin/activate

# 测试知识库 MCP
python -m mcp_servers.knowledge_base

# 测试知乎 RPA MCP
python -m mcp_servers.zhihu_rpa
```

### 3. 检查数据输出

```bash
# 查看生成的问题
cat data/questions.json

# 查看收集的素材
ls -la data/materials/

# 查看生成的草稿
ls -la data/drafts/
```

### 4. 测试智能体

```bash
cd /opt/zhihu-qa

# 手动触发问题探索
claude agent run question_scout --once

# 手动触发素材收集
claude agent run material_collector --once
```

---

## 故障排查

### 问题1：浏览器无法启动

```bash
# 检查浏览器依赖
which chromium-browser

# 手动启动测试
chromium-browser --headless --no-sandbox --disable-gpu

# 检查显示环境
echo $DISPLAY
```

**解决方案：**

```bash
# 安装缺失依赖
sudo apt install -y chromium-browser

# 或使用 Playwright 安装
playwright install-deps chromium
```

### 问题2：登录失败

```bash
# 检查会话目录
ls -la data/sessions/

# 清除旧会话重新登录
rm -rf data/sessions/*
python scripts/zhihu_rpa.py --login
```

### 问题3：Paperclip 服务无法启动

```bash
# 检查日志
sudo journalctl -u paperclip -n 50

# 手动运行测试
cd /opt/zhihu-qa
claude agent run question_scout
```

### 问题4：内存不足

```bash
# 检查内存使用
free -h

# 创建 Swap 空间
sudo dd if=/dev/zero of=/swapfile bs=1M count=2048
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 永久生效
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### 问题5：网络问题

```bash
# 测试网络连接
ping -c 4 www.zhihu.com

# 检查防火墙
sudo ufw status

# 允许必要端口
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

---

## 定期维护

### 1. 更新代码

```bash
cd /opt/zhihu-qa
git pull origin main

# 重启服务
sudo systemctl restart paperclip
```

### 2. 清理旧数据

```bash
# 清理90天前的数据
find data/ -name "*.json" -mtime +90 -delete

# 清理浏览器缓存
rm -rf /tmp/playwright-*
```

### 3. 监控日志

```bash
# 设置日志轮转
sudo vim /etc/logrotate.d/paperclip
```

添加：

```
/opt/zhihu-qa/.paperclip/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 your_username your_username
}
```

---

## 安全建议

1. **限制 SSH 访问**
```bash
# 禁用密码登录，只允许密钥
sudo vim /etc/ssh/sshd_config
# 设置: PasswordAuthentication no
sudo systemctl restart sshd
```

2. **配置防火墙**
```bash
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow from your_ip to any port 22
```

3. **定期备份**
```bash
# 备份脚本
cat > /opt/backup-zhihu-qa.sh << 'EOF'
#!/bin/bash
rsync -avz /opt/zhihu-qa /backup/zhihu-qa-$(date +%Y%m%d)
EOF
chmod +x /opt/backup-zhihu-qa.sh
```

---

## 联系支持

如遇到部署问题，请检查：
1. 项目 Issues: https://github.com/LiuGuoJiang/zhihu-qa/issues
2. 系统日志: `/var/log/paperclip.err.log`
3. Paperclip 文档: [官方文档链接]

---

**部署完成后，您的知乎内容工作室系统将自动运行，智能体会定期发现高质量问题并生成内容！**

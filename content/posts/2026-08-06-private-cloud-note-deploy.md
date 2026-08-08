---
categories:
- 运维
date: 2026-08-06
description: 30分钟搞定，两个热门开源方案对比，从0到1搭建私有云笔记，含完整迁移攻略。
image: /images/cover-devops.svg
lastmod: 2026-08-06
tags:
- 私有云
- 笔记
- Docker
- self-hosted
title: 30分钟搞定：从0到1搭建私有云笔记（双方案对比 + 迁移全攻略）
---

> 写在前面：印象笔记越涨越贵，Notion国内访问慢如蜗牛，OneDrive同步经常卡，还有数据隐私问题？不如自己搭一个——全程Docker，30分钟搞定，全平台同步，数据全在你自己手里。

## 为什么自己搭？

核心就四点：
1. **数据主权**：笔记是个人最核心资产，自己服务器说了算
2. **隐私安全**：端到端加密，没人能动你的笔记
3. **成本可控**：小VPS一年几十块，比订阅省太多
4. **功能不缺**：开源方案该有的都有，不比商业笔记差

## 怎么选？两个热门方案对比

| 维度 | 📝 **Joplin Server** | 📚 **Trilium Notes** |
|:---|:---|:---|
| 开源协议 | MIT 免费 | AGPL v3 免费 |
| 架构 | 客户端+Server 原生同步 | 网页端+本地存储，自行同步 |
| 编辑 | Markdown为主 | 分层块编辑，树形大纲 |
| UI | 传统云笔记风格简洁 | 现代化，高度可定制 |
| 同步 | 开箱即用 | 需要自己配WebDAV |
| 部署难度 | ⭐⭐⭐ 5分钟 | ⭐⭐ 3分钟，更轻 |
| 移动端 | 原生APP，稳定 | Web端，体验一般 |
| 内存占用 | ~500MB | ~200MB |
| 适合 | 替代印象笔记，手机用得多 | 大型知识库，分层管理 |

一句话：**日常记笔记选Joplin，做知识库选Trilium**。本文两个完整教程，你挑着来。

---

## 方案一：Joplin Server 部署

### 1. 前置准备

- VPS（2核2G足够）+ Docker + Docker Compose
- 可选：域名 + Nginx + SSL证书

![Joplin官网首页](/images/joplin-home.png)
*Joplin官网首页示意*

### 2. 编写 `docker-compose.yml`

```yaml
version: '3'

services:
  db:
    image: postgres:15-alpine
    container_name: joplin-db
    restart: unless-stopped
    volumes:
      - ./data/postgres:/var/lib/postgresql/data
    environment:
      - POSTGRES_PASSWORD=joplin123456  # 改密码！
      - POSTGRES_USER=joplin
      - POSTGRES_DB=joplin

  app:
    image: joplin/server:latest
    container_name: joplin-app
    restart: unless-stopped
    depends_on:
      - db
    ports:
      - "22300:22300"
    environment:
      - APP_PORT=22300
      - APP_BASE_URL=https://your-domain.com  # 改你的域名，**末尾不要斜杠**
      - DB_CLIENT=pg
      - POSTGRES_CONNECTION_STRING=postgres://joplin:joplin123456@db:5432/joplin
      - MAX_FILE_SIZE=100000000  # 附件大小限制100MB
```

### 3. 启动

```bash
docker compose up -d
docker compose logs -f app  # 查看日志，看到 "Joplin Server is ready" 就成了
```

### 4. Nginx反向代理（可选推荐）

```nginx
server {
    listen 80;
    server_name notes.your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name notes.your-domain.com;

    ssl_certificate /path/to/fullchain.pem;
    ssl_certificate_key /path/to/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:22300;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
nginx -t && systemctl reload nginx
```

### 5. 客户端配置

1. [官网下载客户端](https://joplinapp.org/) → 全平台都有
2. 打开 → 设置 → 同步 → 选 `Joplin Server`
3. 填你的地址+邮箱+密码 → 检查通过就同步完成了

---

## 方案二：Trilium Notes 部署

### 1. 前置准备

和Joplin一样，要求更低，1G内存就能跑。

![Trilium官网首页](/images/trilium-home.png)
*Trilium官网首页示意*

### 2. 编写 `docker-compose.yml`

```yaml
version: '3'

services:
  trilium:
    image: zadam/trilium:latest
    container_name: trilium
    restart: unless-stopped
    ports:
      - "8080:8080"
    volumes:
      - ./data:/home/node/trilium-data
```

默认SQLite够用，想折腾PostgreSQL看官方文档。

### 3. 启动

```bash
mkdir -p ./data
docker compose up -d
docker compose logs -f trilium  # 看到 "Trilium has started" 就成了
```

### 4. Nginx反向代理（可选）

```nginx
server {
    listen 80;
    server_name notes.your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name notes.your-domain.com;

    ssl_certificate /path/to/fullchain.pem;
    ssl_certificate_key /path/to/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Trilium需要支持Websocket
        proxy_set_header Connection "upgrade";
        proxy_set_header Upgrade $http_upgrade;
    }
}
```

### 5. 同步配置

Trilium需要自己配WebDAV同步：
- 已有Nextcloud/Cloudreve直接开WebDAV
- 没有就用rclone + 对象存储（OSS/COS）
- Trilium → 设置 → 同步 → 填信息启用

移动端直接浏览器访问网址就能用。

---

## ⚠️ 通用避坑指南

1. **域名末尾不要斜杠**
   - 错：`https://notes.domain.com/`
   - 对：`https://notes.domain.com`
   加斜杠会导致API拼错，各种奇怪问题。

2. **数据持久化一定要做**
   两个docker-compose都配好了volume，直接用就行，别删。

3. **上传大小限制**
   除了改环境变量，Nginx也要改：
   ```nginx
   http { client_max_body_size 100m; }
   ```

4. **证书问题**
   用Let's Encrypt免费证书，一句话搞定：
   ```bash
   certbot --nginx -d notes.your-domain.com
   ```

5. **内存不够加Swap**
   ```bash
   fallocate -l 1G /swapfile
   chmod 600 /swapfile
   mkswap /swapfile
   swapon /swapfile
   echo '/swapfile none swap sw 0 0' >> /etc/fstab
   ```

---

## 迁移攻略：从其他笔记导入

两个方案导入方法大同小异：

| 来源 | Joplin | Trilium |
|:---|:---|:---|
| **印象笔记** | 直接导入 `.enex` → Joplin文件→导入 | 先用 `enex2trilium` 转换再导入 |
| **有道云笔记** | `yinxiangtransfer` 转Markdown → 导入目录 | 同左，直接导入 |
| **Notion** | 导出Markdown → 导入目录 | 同左 |

工具链接都在延伸阅读里。

---

## 数据备份

一定要备份！推荐定时脚本：

### Joplin (PostgreSQL)
```bash
#!/bin/bash
# backup-joplin.sh
DATE=$(date +%Y%m%d)
BACKUP_DIR=/opt/backup/joplin
mkdir -p $BACKUP_DIR
docker exec joplin-db pg_dump -U joplin joplin | gzip > $BACKUP_DIR/joplin-$DATE.sql.gz
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete
```

### Trilium (SQLite)
```bash
#!/bin/bash
# backup-trilium.sh
DATE=$(date +%Y%m%d)
BACKUP_DIR=/opt/backup/trilium
mkdir -p $BACKUP_DIR
cd ./data
tar czf $BACKUP_DIR/trilium-backup-$DATE.tar.gz .
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
```

加到crontab每天凌晨跑，再把备份同步到对象存储做异地备份就完美了。

---

## 总结

| 需求 | 选 |
|:---|:---|
| 替代印象笔记，手机日常用 | ✅ Joplin |
| 做大型个人知识库，分层管理 | ✅ Trilium |
| 资源少想最轻量 | ✅ Trilium |
| 要原生移动端 | ✅ Joplin |

两个都是多年维护的成熟开源项目，选哪个都不亏。30分钟搞定，一劳永逸，从此你的笔记你做主。

---

**延伸阅读：**
- [Joplin GitHub](https://github.com/laurent22/joplin)
- [Trilium GitHub](https://github.com/zadam/trilium)
- [yinxiangtransfer（有道导出工具）](https://github.com/siyuan-note/yinxiangtransfer)
- [enex2trilium（印象转Trilium）](https://github.com/zadam/trilium/tree/master/tools/enex2trilium)

---
title: Alpine系统下的apk指令
date: '2019-06-09T00:00:00'
draft: false
categories:
- 操作系统
tags:
- Linux
- Alpine
- Docker
- apk
description: Alpine Linux 包管理工具 apk 的完整使用指南
lastmod: 2019-06-09
image: /images/cover-os.svg
---
> Alpine Linux 是一个面向安全应用的轻量级 Linux 发行版。它采用了 musl libc 和 busybox 以减小系统的体积和运行时资源消耗，同时还提供了自己的包管理工具 apk。

## apk 常用命令速查

| 命令 | 说明 |
|:---|:---|
| `apk update` | 更新本地镜像源索引 |
| `apk add <pkg>` | 安装软件包 |
| `apk del <pkg>` | 卸载软件包 |
| `apk upgrade` | 升级所有已安装包 |
| `apk search <pkg>` | 搜索软件包 |
| `apk info <pkg>` | 查看软件包信息 |
| `apk list` | 列出已安装包 |
| `apk fix` | 修复或升级包 |

## 基础命令

### 更新镜像源

```bash
# 更新本地镜像源索引
apk update
```

`update` 命令会从各个镜像源列表下载 `APKINDEX.tar.gz` 并存储到本地缓存，一般在 `/var/cache/apk/`、`/var/lib/apk/`、`/etc/apk/cache/` 目录下。

### 安装软件包

```bash
# 基本安装
apk add openssh openntp vim

# 不缓存安装（减小镜像体积）
apk add --no-cache mysql-client

# 从指定仓库安装
apk add docker --update-cache \
    --repository http://mirrors.ustc.edu.cn/alpine/v3.4/main/ \
    --allow-untrusted
```

#### 安装指定版本

```bash
# 安装精确版本
apk add asterisk=1.6.0.21-r0

# 版本约束
apk add 'asterisk<1.6.1'      # 小于
apk add 'asterisk>1.6.1'      # 大于
apk add 'asterisk>=1.6.1'     # 大于等于
apk add 'asterisk~=1.6.1'     # 约等于
```

### 卸载软件包

```bash
# 卸载并删除相关文件
apk del openssh openntp vim
```

### 升级软件包

```bash
# 更新镜像源
apk update

# 升级所有已安装包
apk upgrade

# 升级指定软件包
apk add --upgrade busybox
```

### 搜索软件包

```bash
# 搜索所有可用包
apk search

# 显示详细信息
apk search -v

# 通过名称查找
apk search -v 'acf*'

# 通过描述查找
apk search -v -d 'docker'
```

### 查看软件包信息

```bash
# 列出所有已安装包
apk info

# 查看指定包详细信息
apk info -a zlib

# 查看文件属于哪个包
apk info --who-owns /sbin/lbu
```

## 常用场景

### Docker 容器中安装工具

```bash
# 更新并安装基础工具
apk update && apk add --no-cache \
    curl \
    wget \
    git \
    vim \
    htop \
    bash \
    bash-completion
```

### PHP 运行环境

```bash
apk add --no-cache \
    php \
    php-fpm \
    php-mysql \
    php-mbstring \
    php-xml \
    php-curl \
    php-json
```

### Nginx 运行环境

```bash
apk add --no-cache \
    nginx \
    openssl \
    pcre \
    zlib
```

### 数据库客户端

```bash
# MySQL 客户端
apk add --no-cache mysql-client

# PostgreSQL 客户端
apk add --no-cache postgresql-client

# Redis 客户端
apk add --no-cache redis
```

## Alpine 中文支持

如果需要在 Alpine 中使用中文，需要安装 glibc：

```bash
# 安装 glibc（解决 locale 问题）
apk --no-cache add ca-certificates wget

wget -q -O /etc/apk/keys/sgerrand.rsa.pub \
    https://alpine-pkgs.sgerrand.com/sgerrand.rsa.pub

wget https://github.com/sgerrand/alpine-pkg-glibc/releases/download/2.29-r0/glibc-2.29-r0.apk
apk add glibc-2.29-r0.apk

wget https://github.com/sgerrand/alpine-pkg-glibc/releases/download/2.29-r0/glibc-bin-2.29-r0.apk
wget https://github.com/sgerrand/alpine-pkg-glibc/releases/download/2.29-r0/glibc-i18n-2.29-r0.apk
apk add glibc-bin-2.29-r0.apk glibc-i18n-2.29-r0.apk

# 生成 locale
/usr/glibc-compat/bin/localedef -i en_US -f UTF-8 en_US.UTF-8
```

## 镜像源配置

### 官方源

```bash
# /etc/apk/repositories
https://dl-cdn.alpinelinux.org/alpine/v3.19/main
https://dl-cdn.alpinelinux.org/alpine/v3.19/community
```

### 国内镜像

```bash
# 阿里云镜像
echo "https://mirrors.aliyun.com/alpine/v3.19/main" > /etc/apk/repositories
echo "https://mirrors.aliyun.com/alpine/v3.19/community" >> /etc/apk/repositories

# 中科大镜像
echo "https://mirrors.ustc.edu.cn/alpine/v3.19/main" > /etc/apk/repositories
echo "https://mirrors.ustc.edu.cn/alpine/v3.19/community" >> /etc/apk/repositories

# 腾讯云镜像
echo "https://mirrors.cloud.tencent.com/alpine/v3.19/main" > /etc/apk/repositories
echo "https://mirrors.cloud.tencent.com/alpine/v3.19/community" >> /etc/apk/repositories
```

## 进阶命令

### 查看依赖关系

```bash
# 查看包依赖
apk info -r php

# 查看反向依赖（哪些包依赖它）
apk info -R nginx
```

### 缓存管理

```bash
# 下载包到缓存
apk cache download

# 清理缓存
apk cache clean

# 修复缓存
apk cache fix
```

### 版本比较

```bash
# 比较版本
apk version abc 1.2.3-r0

# 测试版本表达式
apk version --test 'bash>3.1'
```

## 常见问题

### Q: apk add 报错 signature is invalid

A: 更新镜像源或添加 `--allow-untrusted` 参数

### Q: 找不到包

A: 确认仓库配置正确后执行 `apk update`

### Q: 依赖冲突

A: 使用 `apk add --force-overwrite` 或查看冲突详情

## Docker 最佳实践

```dockerfile
# 使用国内镜像源
RUN echo "https://mirrors.aliyun.com/alpine/v3.19/main" > /etc/apk/repositories \
    && apk add --no-cache \
        nginx \
        php-fpm \
        php-mysqli \
    && rm -rf /var/cache/apk/*

# 多阶段构建
FROM alpine:3.19 AS builder
RUN apk add --no-cache go

FROM alpine:3.19
COPY --from=builder /usr/local/bin/ /usr/local/bin/
```

## 参考链接

- [Alpine Linux 官网](https://alpinelinux.org/)
- [Alpine 包仓库](https://pkgs.alpinelinux.org/)
- [Alpine Wiki](https://wiki.alpinelinux.org/)
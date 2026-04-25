---
title: Docker从零构建php-nginx-alpine镜像
date: '2018-11-09T00:00:00'
draft: false
categories:
- 编程
tags:
- Docker
- PHP
- Nginx
- Alpine
description: 从零开始构建 PHP + Nginx + Alpine 精简镜像的完整教程
lastmod: 2018-11-09
image: /images/cover-programming.svg
---
> 虽然之前用 Docker 环境运行了一些项目，但对于镜像这块还不是很理解，且网上现成的镜像都包含太多用不到的库，所以决定从零开始构建一个自己的镜像。

## 选择 Alpine Linux 作为基础镜像

```bash
# 拉取 Alpine 镜像
docker pull alpine:latest

# 查看镜像
docker images alpine
```

Alpine Linux 是一个面向安全的轻量级 Linux 发行版，镜像只有 **5MB** 左右。

## 运行并进入容器

```bash
# 交互式运行
docker run -it alpine /bin/sh

# 或后台运行
docker run -d --name my-alpine alpine:latest
docker exec -it my-alpine /bin/sh
```

## 安装 PHP 和 Nginx

```bash
# 更新包索引
apk update

# 安装 PHP 和 Nginx
apk add php7 php7-fpm php7-cli nginx

# 如果使用 PHP 8.x
apk add php81 php81-fpm php81-cli nginx
```

> ⚠️ **提示**：Alpine 3.18+ 使用 `php81`、`php82` 等命名

## 安装 PHP 扩展

```bash
# 安装常用扩展
apk add php7-mysqli \
    php7-pdo_mysql \
    php7-mbstring \
    php7-json \
    php7-zlib \
    php7-gd \
    php7-intl \
    php7-session \
    php7-curl \
    php7-posix \
    php7-fileinfo \
    php7-simplexml \
    php7-xml \
    php7-openssl \
    php7-dom \
    php7-phar

# PHP 8.x 扩展
apk add php81-mysqli php81-pdo_mysql php81-mbstring php81-xml php81-curl
```

## 目录结构

| 软件 | 路径 |
|:---|:---|
| PHP 配置 | `/etc/php7` |
| Nginx 配置 | `/etc/nginx` |
| 网站目录 | `/var/www/localhost/htdocs` |
| 日志目录 | `/var/log/nginx` |

## 配置 PHP-FPM

### 修改 www.conf

```bash
vi /etc/php7/php-fpm.d/www.conf
```

```ini
[www]
user = nobody
group = nobody
listen = 127.0.0.1:9000
```

## 配置 Nginx

### nginx.conf

```bash
vi /etc/nginx/nginx.conf
```

```nginx
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';
    
    access_log /var/log/nginx/access.log main;
    
    sendfile on;
    keepalive_timeout 65;
    
    include /etc/nginx/conf.d/*.conf;
}
```

### default.conf

```bash
vi /etc/nginx/conf.d/default.conf
```

```nginx
server {
    listen 80 default_server;
    root /var/www/localhost/htdocs;
    index index.php index.html;
    
    server_name localhost;
    
    location / {
        try_files $uri $uri/ =404;
    }
    
    location ~ \.php$ {
        fastcgi_pass 127.0.0.1:9000;
        fastcgi_index index.php;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        include fastcgi_params;
    }
    
    location ~ /\.ht {
        deny all;
    }
}
```

## 启动服务

```bash
# 创建必要的目录
mkdir -p /run/nginx

# 启动 PHP-FPM
/usr/sbin/php-fpm7

# 启动 Nginx
/usr/sbin/nginx

# 测试
curl http://localhost
```

## 创建 Dockerfile

### 基础版本

```dockerfile
# Dockerfile
FROM alpine:latest

LABEL maintainer="yisonli <email@example.com>"
LABEL version="1.0"
LABEL description="PHP7 + Nginx on Alpine Linux"

# 安装系统工具
RUN apk add --no-cache \
    openssl \
    curl \
    ca-certificates \
    bash

# 安装 PHP 和扩展
RUN apk add --no-cache \
    php7 \
    php7-fpm \
    php7-mysqli \
    php7-pdo_mysql \
    php7-mbstring \
    php7-json \
    php7-gd \
    php7-curl

# 安装 Nginx
RUN apk add --no-cache nginx

# 配置 PHP-FPM
RUN mkdir -p /run/nginx \
    && chown -R nobody:nobody /var/www/localhost

# 复制配置文件
COPY nginx.conf /etc/nginx/nginx.conf
COPY default.conf /etc/nginx/conf.d/
COPY php.ini /etc/php7/php.ini
COPY php-fpm.conf /etc/php7/php-fpm.conf

# 复制应用代码
COPY ./app /var/www/localhost/htdocs

# 暴露端口
EXPOSE 80 443

# 启动脚本
COPY start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]
```

### 启动脚本

```bash
#!/bin/sh
# start.sh

# 创建必要目录
mkdir -p /run/nginx /var/log/nginx /var/tmp/php-fpm

# 设置权限
chown -R nobody:nobody /var/www/localhost

# 启动 PHP-FPM
/usr/sbin/php-fpm7 &

# 启动 Nginx
/usr/sbin/nginx -g 'daemon off;'
```

### PHP 配置文件

```ini
; php.ini
upload_max_filesize = 50M
post_max_size = 50M
memory_limit = 128M
max_execution_time = 300
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8080:80"
    volumes:
      - ./app:/var/www/localhost/htdocs
    environment:
      - PHP_MEMORY_LIMIT=256M
    restart: unless-stopped

  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: secret
      MYSQL_DATABASE: app
    volumes:
      - mysql_data:/var/lib/mysql

volumes:
  mysql_data:
```

## 构建并运行

```bash
# 构建镜像
docker build -t my-php-app:1.0 .

# 运行容器
docker run -d -p 8080:80 --name my-app my-php-app:1.0

# 使用 docker-compose
docker-compose up -d

# 查看日志
docker logs -f my-app

# 进入容器
docker exec -it my-app /bin/sh
```

## 常用 Docker 命令

```bash
# 查看运行中的容器
docker ps

# 查看所有容器
docker ps -a

# 删除未运行的容器
docker rm $(docker ps -a -q)

# 提交镜像
docker commit -a "yisonli" -m "my php7-nginx" CONTAINER_ID my-php-app:0.1

# 添加标签
docker tag IMAGE_ID my-repo/my-image:tag

# 推送镜像
docker push my-repo/my-image:tag
```

## 共享文件夹

```bash
# 挂载本地目录
docker run -v $(pwd)/www:/var/www/localhost/htdocs \
    -p 8080:80 \
    my-php-app:1.0
```

## 优化建议

1. **使用多阶段构建**减小镜像体积
2. **合并 RUN 指令**减少层数
3. **使用 .dockerignore**排除不需要的文件
4. **使用国内镜像源**加速构建

### 多阶段构建示例

```dockerfile
# 构建阶段
FROM composer:2 as builder
WORKDIR /app
COPY composer.* ./
RUN composer install --no-dev
COPY . .
RUN composer dump-autoload --optimize

# 运行阶段
FROM alpine:latest
COPY --from=builder /app /var/www/localhost/htdocs
# ...
```

## 参考链接

- [Alpine Linux 官网](https://alpinelinux.org/)
- [Docker Hub - Alpine](https://hub.docker.com/_/alpine)
- [Docker 官方文档](https://docs.docker.com/)
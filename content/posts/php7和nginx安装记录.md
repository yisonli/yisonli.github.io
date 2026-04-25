---
categories:
- 编程
date: 2016-06-02
description: Linux 环境下 PHP7 + Nginx 的编译安装与环境配置完整记录
image: /images/cover-programming.svg
lastmod: 2016-06-02
tags:
- PHP
- Nginx
- Linux
title: PHP7和Nginx安装记录
---

> 本文主要记录 PHP7 + Nginx 的编译安装以及环境搭建的操作步骤

## 1. 获取 PHP 源码

```bash
# 下载 PHP 7.0.7（注意：PHP 7.0 已停止维护，建议使用更高版本）
sudo wget http://cn2.php.net/distributions/php-7.0.7.tar.xz

# 解压
tar -xvf php-7.0.7.tar.xz
cd php-7.0.7
```

> ⚠️ **提示**：PHP 7.0 已停止维护，建议使用 PHP 7.4 或 PHP 8.x

## 2. 安装依赖

```bash
sudo apt-get update

sudo apt-get install -y \
    nginx \
    mysql-client \
    git \
    build-essential \
    libxml2-dev \
    libssl-dev \
    libcurl4-openssl-dev \
    libjpeg-dev \
    libpng-dev \
    libmcrypt-dev \
    libreadline-dev \
    libgmp-dev \
    libzip-dev \
    libonig-dev \
    libicu-dev
```

> **现代推荐**：如果安装 PHP 8.x，mcrypt 已被移除，gd 扩展改为 libgd-dev

## 3. 编译 PHP

```bash
cd php-7.0.7

sudo ./configure \
    --prefix=/usr/local/php7 \
    --enable-fpm \
    --enable-inline-optimization \
    --disable-debug \
    --disable-rpath \
    --enable-shared \
    --enable-opcache \
    --with-mysqli \
    --with-mysql-sock \
    --enable-pdo \
    --with-pdo-mysql \
    --with-gettext \
    --enable-mbstring \
    --with-iconv \
    --enable-bcmath \
    --enable-soap \
    --with-libxml-dir \
    --enable-pcntl \
    --enable-shmop \
    --enable-sysvmsg \
    --enable-sysvsem \
    --enable-sysvshm \
    --enable-sockets \
    --with-curl \
    --with-zlib \
    --enable-zip \
    --with-readline \
    --with-pear \
    --with-gd \
    --with-jpeg-dir=/usr/lib \
    --enable-gd-native-ttf \
    --enable-xml
```

```bash
# 编译安装
sudo make -j$(nproc)
sudo make install

# 创建软链接
sudo ln -s /usr/local/php7 /usr/local/php

# 复制配置文件
sudo cp php.ini-production /usr/local/php/lib/php.ini
```

> ⚠️ **警告**：`--with-mysql` 在 PHP 7.0 中已被移除，请使用 `--with-mysqli`

## 4. 配置 PHP-FPM

```bash
cd /usr/local/php/etc

# 复制默认配置
sudo cp php-fpm.conf.default php-fpm.conf
cd /usr/local/php/etc/php-fpm.d
sudo cp www.conf.default www.conf

# 编辑 www.conf
sudo vim www.conf
```

修改用户和组：

```ini
[www]
user = www-data
group = www-data

; 如果使用 socket 连接
listen = /run/php/php-fpm.sock
listen.owner = www-data
listen.group = www-data
listen.mode = 0660
```

如果 www-data 用户不存在，需要先创建：

```bash
sudo groupadd -g 33 www-data
sudo useradd -g www-data -u 33 -s /usr/sbin/nologin www-data
```

## 5. 启动 PHP-FPM

```bash
# 启动 php-fpm
sudo /usr/local/php/sbin/php-fpm

# 添加到系统 PATH
sudo tee -a /etc/profile << 'EOF'
export PATH=$PATH:/usr/local/php/bin:/usr/local/php/sbin
EOF
source /etc/profile

# 验证安装
php -v
php-fpm -v
```

## 6. Nginx 配置

```bash
cd /etc/nginx/sites-enabled
sudo vim default
```

修改 PHP 配置文件块：

```nginx
server {
    listen 80 default_server;
    root /var/www/html;
    
    index index.php index.html index.htm;

    server_name _;

    location / {
        try_files $uri $uri/ =404;
    }

    # PHP 配置
    location ~ \.php$ {
        fastcgi_split_path_info ^(.+\.php)(/.+)$;
        fastcgi_pass unix:/run/php/php-fpm.sock;
        # 或者使用 IP:9000
        # fastcgi_pass 127.0.0.1:9000;
        fastcgi_index index.php;
        include fastcgi_params;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
    }

    # 禁止访问隐藏文件
    location ~ /\. {
        deny all;
    }
}
```

```bash
# 重载 Nginx 配置
sudo nginx -t
sudo service nginx reload
```

## 7. 测试

创建测试文件：

```php
<?php
// /var/www/html/info.php
phpinfo();
```

访问 `http://your_server_ip/info.php`

> ⚠️ **安全提醒**：测试完成后记得删除 `info.php`

## 8. 腾讯云/阿里云安全组

> **重要**：记得在云控制台开放 80 端口的安全组规则！

## 现代安装方式推荐

### 使用 Ondrej PPA（Ubuntu/Debian）

```bash
sudo apt install software-properties-common
sudo add-apt-repository ppa:ondrej/php
sudo apt update
sudo apt install php8.1-fpm php8.1-mysql php8.1-curl php8.1-gd php8.1-mbstring php8.1-xml php8.1-zip
```

### 使用 Remi（CentOS/RHEL）

```bash
sudo dnf install epel-release
sudo dnf install dnf-utils
sudo dnf module reset php
sudo dnf module enable php:8.1
sudo dnf install php php-fpm php-mysqlnd
```

## 常见问题

| 问题 | 解决方案 |
|:---|:---|
| make 报错 | 检查依赖是否安装完整 |
| php-fpm 无法启动 | 检查用户权限和 socket 路径 |
| 502 Bad Gateway | 检查 php-fpm 是否运行，socket 权限 |
| 访问不到 PHP | 检查 Nginx fastcgi_pass 配置 |

## 参考链接

- [PHP 官方下载](https://www.php.net/downloads.php)
- [Nginx + PHP-FPM 配置](https://www.nginx.com/resources/wiki/start/topics/examples/phpfcgi/)
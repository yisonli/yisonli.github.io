---
title: 使用Composer安装Laravel/Lumen
date: '2017-12-08T00:00:00'
draft: false
categories:
- 编程
tags:
- Laravel
- Lumen
- Composer
- PHP
description: PHP Composer 安装与 Laravel/Lumen 框架环境搭建完整指南
lastmod: 2017-12-08
image: /images/cover-programming.svg
---
> 本文介绍如何搭建 PHP 的 Laravel 和 Lumen 环境

## 安装 Composer

### 方法一：官方安装脚本

```bash
php -r "copy('https://install.phpcomposer.com/installer', 'composer-setup.php');"
php composer-setup.php
php -r "unlink('composer-setup.php');"

# 移动到系统 PATH
sudo mv composer.phar /usr/local/bin/composer
```

### 方法二：直接下载（推荐）

```bash
# Linux/macOS
curl -sS https://getcomposer.org/installer | php
sudo mv composer.phar /usr/local/bin/composer

# Windows
# 下载 https://getcomposer.org/Composer-Setup.exe
```

### 设置权限

```bash
# 添加执行权限
sudo chmod +x /usr/local/bin/composer
```

## 修改 Composer 镜像

由于国内网络原因，建议使用国内镜像加速：

```bash
# 阿里云镜像（推荐）
composer config -g repo.packagist composer https://mirrors.aliyun.com/composer/

# Laravel China 镜像
composer config -g repo.packagist composer https://packagist.laravel-china.org

# 恢复官方源
composer config -g --unset repos.packagist
```

## 安装 Laravel/Lumen

### 全局安装 Laravel

```bash
composer global require "laravel/installer"
```

### 全局安装 Lumen

```bash
composer global require "laravel/lumen-installer"
```

### 添加到系统 PATH

```bash
# 编辑 ~/.bashrc 或 ~/.zshrc
echo 'export PATH="$PATH:$HOME/.composer/vendor/bin"' >> ~/.bashrc
source ~/.bashrc

# 确认目录（可能因 Composer 版本而异）
echo 'export PATH="$PATH:/home/yison/.config/composer/vendor/bin"' >> ~/.bashrc
source ~/.bashrc
```

验证安装：

```bash
composer --version
laravel --version
lumen --version
```

## 创建项目

### 使用 Laravel 创建项目

```bash
# 方式一：使用 laravel 命令
laravel new blog

# 方式二：使用 Composer
composer create-project --prefer-dist laravel/laravel blog

# 指定版本
composer create-project --prefer-dist laravel/laravel blog "10.*"
```

### 使用 Lumen 创建项目

```bash
# 方式一：使用 lumen 命令
lumen new lumen

# 方式二：使用 Composer（推荐）
composer create-project --prefer-dist laravel/lumen lumen

# 指定版本
composer create-project --prefer-dist laravel/lumen lumen "10.*"
```

## 启动 Laravel 项目

```bash
cd blog

# 安装依赖
composer install

# 复制环境配置
cp .env.example .env

# 生成应用密钥
php artisan key:generate

# 启动开发服务器
php artisan serve
# 访问 http://localhost:8000
```

## 启动 Lumen 项目

```bash
cd lumen

# 安装依赖
composer install

# 复制环境配置
cp .env.example .env

# 生成应用密钥
php artisan key:generate

# 启动开发服务器
php -S localhost:8000 -t public
# 访问 http://localhost:8000
```

## Laravel/Lumen 常用命令

### Artisan 命令

```bash
# 查看所有命令
php artisan list

# 创建控制器
php artisan make:controller UserController

# 创建模型
php artisan make:model User

# 创建中间件
php artisan make:middleware AuthMiddleware

# 创建数据库迁移
php artisan make:migration create_users_table

# 执行数据库迁移
php artisan migrate

# 路由列表
php artisan route:list

# 清除缓存
php artisan config:clear
php artisan cache:clear
php artisan view:clear
```

### Composer 常用命令

```bash
# 更新依赖
composer update

# 添加依赖
composer require package/name

# 添加开发依赖
composer require --dev phpunit/phpunit

# 移除依赖
composer remove package/name

# 优化自动加载
composer dump-autoload -o

# 查看可用更新
composer outdated
```

## Lumen vs Laravel

| 特性 | Lumen | Laravel |
|:---|:---:|:---:|
| 定位 | 微服务/API | 全栈应用 |
| 体积 | ~1MB | ~10MB |
| 视图 | ❌ 不支持 | ✅ 支持 |
| Session | ❌ | ✅ |
| 路由 | FastRoute | Symfony Router |
| 开箱即用 | 较少 | 丰富 |
| 性能 | 更快 | 较慢 |

## Docker 部署 Laravel

```bash
# 使用 Laravel Sail 快速搭建开发环境
composer require laravel/sail --dev
php artisan sail:install
php artisan db:seed
docker-compose up -d
```

## 常见问题

### Q: composer 命令找不到

A: 确保 Composer 在 PATH 中：
```bash
export PATH="$PATH:$HOME/.composer/vendor/bin"
source ~/.bashrc
```

### Q: 依赖安装失败

A: 尝试清除缓存或更换镜像：
```bash
composer clear-cache
composer config -g repo.packagist composer https://mirrors.aliyun.com/composer/
composer install
```

### Q: 权限不足

A: Linux 系统设置目录权限：
```bash
sudo chown -R $USER:$USER /path/to/project
chmod -R 755 /path/to/project
chmod -R 775 /path/to/project/storage
```

## 参考链接

- [Composer 官网](https://getcomposer.org/)
- [Laravel 官网](https://laravel.com/)
- [Lumen 官网](https://lumen.laravel.com/)
- [Packagist](https://packagist.org/)
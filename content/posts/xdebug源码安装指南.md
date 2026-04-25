---
categories:
- 编程
date: 2018-05-04
description: PHP 在 Linux/macOS 上源码编译安装 Xdebug 调试器的完整教程
image: /images/cover-programming.svg
lastmod: 2018-05-04
tags:
- PHP
- Xdebug
- 调试工具
title: Xdebug源码安装指南
---

> PHP 在 Linux/macOS 上安装 Xdebug 的方法

## 方法一：PECL 安装（推荐）

```bash
# 安装 Xdebug（会自动编译）
pecl install xdebug

# 或者指定版本
pecl install xdebug-3.2.2
```

安装后会在输出中显示需要添加到 `php.ini` 的配置。

## 方法二：源码编译安装

### 1. 下载源码

到 [Xdebug 官网](https://xdebug.org/download.php) 下载源码：

```bash
# 下载稳定版本（推荐）
wget https://xdebug.org/files/xdebug-3.2.2.tgz

# 或者下载最新版本
wget https://xdebug.org/files/xdebug-3.3.1.tgz
```

### 2. 解压并编译

```bash
# 解压
tar -xvf xdebug-3.3.1.tgz
cd xdebug-3.3.1

# 生成编译配置
phpize

# 编译
./configure --enable-xdebug
make
```

### 3. 安装

```bash
# 查看编译产物
ls modules/
# 输出：xdebug.so

# 拷贝到 PHP 扩展目录
cp modules/xdebug.so /usr/lib/php/extensions/xdebug.so
```

> 💡 使用 `php -i | grep extension_dir` 查看扩展目录路径

### 4. 配置 php.ini

在 `php.ini` 中添加：

```ini
[xdebug]
; Xdebug 3.x 配置
zend_extension=xdebug.so

; 开启性能分析
xdebug.mode=profile

; 开启调试模式
; xdebug.mode=debug

; IDE IP 地址
xdebug.client_host=127.0.0.1

; IDE 端口
xdebug.client_port=9003

; 启动调试的方式
; xdebug.start_with_request=yes
```

### 5. 重启服务

```bash
# Nginx + PHP-FPM
sudo service php-fpm restart
# 或
sudo systemctl restart php-fpm

# Apache
sudo service apache2 restart
```

## Xdebug 3.x 配置详解

> ⚠️ **重要**：Xdebug 3.x 相比 2.x 有重大变化！

### 配置项对照表

| Xdebug 2.x | Xdebug 3.x | 说明 |
|:---|:---|:---|
| `xdebug.remote_enable` | `xdebug.mode` | 调试模式开关 |
| `xdebug.remote_host` | `xdebug.client_host` | IDE 主机地址 |
| `xdebug.remote_port` | `xdebug.client_port` | IDE 端口 |
| `xdebug.remote_autostart` | `xdebug.start_with_request` | 自动启动调试 |
| `xdebug.remote_handler` | - | 已移除 |
| `xdebug.idekey` | `xdebug.idekey` | IDE Key |

### 常用配置示例

```ini
[xdebug]
; 加载扩展
zend_extension=xdebug.so

; 调试模式：debug/profile/coverage/off
xdebug.mode=debug

; IDE 主机地址（IDE 所在机器的 IP）
xdebug.client_host=127.0.0.1

; IDE 端口
xdebug.client_port=9003

; 自动启动调试
xdebug.start_with_request=trigger

; 记录调试日志
xdebug.log=/var/log/xdebug.log
xdebug.log_level=3
```

### 不同模式说明

```ini
# 关闭所有功能
xdebug.mode=off

# 调试模式（断点调试）
xdebug.mode=debug

# 性能分析（生成 cachegrind 文件）
xdebug.mode=profile

# 代码覆盖率分析
xdebug.mode=coverage

# 触发调试（浏览器安装 Xdebug Helper 插件）
xdebug.mode=debug
xdebug.start_with_request=trigger
```

## 验证安装

```bash
# 检查 Xdebug 是否加载
php -m | grep xdebug

# 查看详细配置
php -i | grep xdebug
```

输出示例：

```
xdebug
xdebug Support => enabled
Version => 3.3.1
IDE Key => yison
```

## IDE 配置

### VS Code

安装 PHP Debug 扩展，配置 `launch.json`：

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Listen for Xdebug",
            "type": "php",
            "request": "launch",
            "port": 9003,
            "pathMappings": {
                "/var/www/html": "${workspaceFolder}"
            }
        }
    ]
}
```

### PhpStorm

1. `Settings` → `PHP` → `Debug`
2. 确认 `Xdebug` 端口为 `9003`
3. 点击电话图标开始监听

## 常见问题

### Q: phpize 报错：autoconf not found

```bash
# Ubuntu/Debian
sudo apt-get install autoconf

# CentOS/RHEL
sudo yum install autoconf

# macOS
brew install autoconf
```

### Q: Xdebug 无法连接

1. 检查防火墙
   ```bash
   sudo firewall-cmd --add-port=9003/tcp
   ```

2. 检查 SELinux
   ```bash
   sudo setsebool -P httpd_can_network_connect 1
   ```

### Q: Xdebug 3.x 配置不生效

检查 PHP 版本和 Xdebug 版本兼容性：

```bash
php -v
php -m | grep xdebug
```

## Docker 中使用 Xdebug

```dockerfile
# Dockerfile
RUN pecl install xdebug \
    && docker-php-ext-enable xdebug

# php.ini 追加配置
RUN echo "xdebug.mode=debug" >> /usr/local/etc/php/conf.d/xdebug.ini \
    && echo "xdebug.client_host=host.docker.internal" >> /usr/local/etc/php/conf.d/xdebug.ini
```

## macOS 特殊路径

| 类型 | 路径 |
|:---|:---|
| Apache 配置 | `/etc/apache2/httpd.conf` |
| Apache 根目录 | `/Library/WebServer/Documents` |
| Hosts 文件 | `/etc/hosts` |
| PHP 配置 | `/etc/php.ini` |
| PHP 扩展目录 | `/usr/lib/php/extensions/` |

## 参考链接

- [Xdebug 官方文档](https://xdebug.org/docs/)
- [Xdebug 安装向导](https://xdebug.org/wizard)
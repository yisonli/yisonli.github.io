---
title: Linux新建用户与sudo权限
date: '2017-04-10T00:00:00'
draft: false
categories:
- 操作系统
tags:
- Linux
- 用户管理
- sudo
description: Linux 系统下创建用户、用户组以及配置 sudo 权限的完整指南
lastmod: 2017-04-10
image: /images/cover-os.svg
---
> 如何用命令行新建一个带超管权限的账号

## 用户管理基础

### 1. 创建用户组并指定 GID

```bash
# 创建用户组，指定 GID 为 1002
sudo groupadd -g 1002 www

# 不指定 GID（系统自动分配）
sudo groupadd www
```

### 2. 添加用户并指定 UID

```bash
# 创建用户并加入 www 组
sudo useradd -g www -u 1003 -m -s /bin/bash www

# 参数说明：
# -g : 指定主用户组
# -u : 指定用户 ID
# -m : 创建用户主目录
# -s : 指定登录 shell
```

### 3. 修改用户密码

```bash
sudo passwd www
```

### 4. 删除用户

```bash
# 删除用户（保留主目录）
sudo userdel www

# 删除用户及其主目录
sudo userdel -r www
```

## Sudo 权限配置

### 添加用户到 sudo 组

```bash
# Debian/Ubuntu 系统
sudo usermod -a -G sudo www

# CentOS/RHEL 系统
sudo usermod -a -G wheel www
```

### 查看用户所属组

```bash
groups www
# 输出: www : www sudo
```

### Ubuntu 系统默认管理员组

Ubuntu 第一个默认账号加入的组：

```bash
adm cdrom sudo dip plugdev lpadmin sambashare
```

## 完整示例：创建 Web 服务用户

```bash
# 1. 创建用户组
sudo groupadd -g 1002 webapps

# 2. 创建用户
sudo useradd -g webapps -u 1003 -m -s /bin/bash webapp

# 3. 设置密码
sudo passwd webapp

# 4. 添加 sudo 权限
sudo usermod -a -G sudo webapp

# 5. 验证
su - webapp
sudo ls /root
```

## Sudoers 文件配置

### 编辑 sudoers 文件

```bash
# 安全的编辑方式（会检查语法）
sudo visudo

# 直接编辑（不推荐）
sudo nano /etc/sudoers
```

### 常用配置示例

```bash
# 允许用户执行所有命令（无需密码）
username ALL=(ALL) NOPASSWD: ALL

# 允许用户执行所有命令（需要密码）
username ALL=(ALL) ALL

# 允许用户执行特定命令
username ALL=(ALL) /usr/bin/systemctl restart nginx, /usr/bin/systemctl stop nginx

# 限制只有特定 IP 可以使用 sudo
username 192.168.1.100=(ALL) ALL
```

### 用户组权限配置

```bash
# 允许 sudo 组所有成员执行命令
%sudo ALL=(ALL:ALL) ALL

# 允许 wheel 组无密码 sudo（CentOS）
%wheel ALL=(ALL) NOPASSWD: ALL
```

## 查看和管理

### 查看所有用户

```bash
cat /etc/passwd | grep -v nologin | grep -v false
```

### 查看所有用户组

```bash
cat /etc/group
```

### 锁定/解锁用户

```bash
# 锁定用户（禁止登录）
sudo passwd -l username

# 解锁用户
sudo passwd -u username
```

### 设置用户过期时间

```bash
# 设置账户过期日期
sudo usermod -e 2025-12-31 username

# 查看账户过期信息
sudo chage -l username
```

## 常见问题

### Q: 为什么新用户无法使用 sudo？

A: 检查用户是否在正确的管理员组中：
```bash
# Ubuntu
groups username  # 应该包含 sudo

# CentOS
groups username  # 应该包含 wheel
```

### Q: 如何免密使用 sudo？

A: 编辑 sudoers 添加 NOPASSWD：
```bash
sudo visudo
# 添加：username ALL=(ALL) NOPASSWD: ALL
```

## 最佳实践

1. **不要给普通用户 root 权限** - 只授予必要的最小权限
2. **使用用户组管理权限** - 便于批量管理
3. **禁用 root 远程登录** - 提高服务器安全性
4. **记录 sudo 操作日志** - 审计用户行为

```bash
# 启用 sudo 日志（Debian/Ubuntu）
sudo visudo
# 添加：Defaults logfile="/var/log/sudo.log"
```
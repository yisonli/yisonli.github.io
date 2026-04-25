---
title: MySQL新建数据库和用户账号
date: '2017-05-03T00:00:00'
draft: false
categories:
- 数据库
tags:
- MySQL
- 数据库管理
description: MySQL 数据库和用户管理的基本操作指南
lastmod: 2017-05-03
image: /images/cover-database.svg
---
> MySQL 数据库账号的基本用法，适合初学者快速上手。

## 登陆数据库

```bash
mysql -h数据库HOST -P端口 -u管理员账户 -p
```

按提示输入密码即可登录。如果在本地操作且使用默认端口，可以简化为：

```bash
mysql -u root -p
```

## 基本操作命令

### 显示数据库

```sql
SHOW DATABASES;
```

### 创建数据库

```sql
CREATE DATABASE 新数据库名;
```

如果需要指定字符集：

```sql
CREATE DATABASE 新数据库名 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 进入某个数据库

```sql
USE 新数据库名;
```

### 显示数据库中的表

```sql
SHOW TABLES;
```

## 用户管理

### 插入新用户

```sql
INSERT INTO mysql.user(Host, User, Password) 
VALUES("使用者IP", "新用户名", PASSWORD("密码"));
FLUSH PRIVILEGES;
```

> **注意：** MySQL 5.7+ 版本中 `Password` 字段已改为 `authentication_string`。

### 推荐方式：使用 CREATE USER

```sql
-- 创建用户
CREATE USER '用户名'@'localhost' IDENTIFIED BY '密码';

-- 或者允许远程连接
CREATE USER '用户名'@'%' IDENTIFIED BY '密码';
```

### 给用户分配数据库权限

```sql
GRANT ALL PRIVILEGES ON 数据库名.* TO '用户名'@'使用者IP' IDENTIFIED BY '密码';
FLUSH PRIVILEGES;
```

**常见权限说明：**

| 权限 | 说明 |
|:---|:---|
| ALL PRIVILEGES | 所有权限 |
| SELECT | 只读 |
| INSERT | 插入数据 |
| UPDATE | 更新数据 |
| DELETE | 删除数据 |
| CREATE | 创建表/数据库 |
| DROP | 删除表/数据库 |

### 示例：创建只读用户

```sql
-- 创建只读用户
CREATE USER 'readonly_user'@'%' IDENTIFIED BY 'password123';

-- 授予 SELECT 权限
GRANT SELECT ON mydb.* TO 'readonly_user'@'%';

-- 刷新权限
FLUSH PRIVILEGES;
```

### 示例：创建管理员用户

```sql
-- 创建管理员用户
CREATE USER 'admin_user'@'%' IDENTIFIED BY 'strong_password';

-- 授予所有权限
GRANT ALL PRIVILEGES ON *.* TO 'admin_user'@'%' WITH GRANT OPTION;

-- 刷新权限
FLUSH PRIVILEGES;
```

## 查看和撤销权限

### 查看用户权限

```sql
SHOW GRANTS FOR '用户名'@'localhost';
```

### 撤销权限

```sql
REVOKE ALL PRIVILEGES ON 数据库名.* FROM '用户名'@'localhost';
FLUSH PRIVILEGES;
```

## 删除用户

```sql
DROP USER '用户名'@'localhost';
```

## 常用配置检查

### 查看字符集设置

```sql
SHOW VARIABLES LIKE 'character%';
```

### 修改 root 密码

```sql
SET PASSWORD FOR 'root'@'localhost' = PASSWORD('新密码');
-- 或者
ALTER USER 'root'@'localhost' IDENTIFIED BY '新密码';
```

## 安全建议

1. **不要使用 `%` 作为生产环境用户的 Host**
2. **为每个应用创建单独的用户和数据库**
3. **遵循最小权限原则**，只授予必要的权限
4. **定期更换密码**
5. **生产环境禁用 root 远程登录**

## 总结

| 操作 | 命令 |
|:---|:---|
| 登录 | `mysql -u root -p` |
| 创建数据库 | `CREATE DATABASE dbname;` |
| 创建用户 | `CREATE USER 'user'@'host' IDENTIFIED BY 'pwd';` |
| 授权 | `GRANT privileges ON db.table TO 'user'@'host';` |
| 撤销权限 | `REVOKE privileges ON db.table FROM 'user'@'host';` |
| 删除用户 | `DROP USER 'user'@'host';` |
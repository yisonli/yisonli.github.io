---
title: 同时使用多个GitHub的SSH Key配置
date: '2016-05-29T00:00:00'
draft: false
categories:
- 版本控制
tags:
- Git
- GitHub
- SSH
description: 一台机器配置多个 GitHub 账号的 SSH Key，实现多仓库管理
lastmod: 2016-05-29
image: /images/cover-vcs.svg
---
> GitHub 中一个 deploy key 只能用在一个仓库内，如果一台机器要管理多个仓库，就需要配置多个 SSH Key。

## 问题背景

在一台机器上可能需要：
- 管理多个 GitHub 账号
- 同时操作多个 GitHub 仓库
- 区分个人仓库和工作仓库

## 配置步骤

### 一、生成第一个 SSH Key

```bash
# 生成第一个 SSH Key（用于个人仓库）
ssh-keygen -t rsa -C "your_email@example.com"
```

一路回车，会在 `~/.ssh/` 目录下生成：
- `id_rsa` - 私钥
- `id_rsa.pub` - 公钥

```bash
# 查看公钥内容
cat ~/.ssh/id_rsa.pub
```

复制公钥内容，到 GitHub 添加 SSH Keys（仓库1）

### 二、生成第二个 SSH Key

```bash
# 生成第二个 SSH Key（用于另一个仓库）
ssh-keygen -t rsa -C "another_email@example.com"
```

**注意：给这个文件起一个专属名字**，例如 `id_rsa_work`

```bash
# 查看第二个公钥内容
cat ~/.ssh/id_rsa_work.pub
```

复制公钥内容，到 GitHub 添加 SSH Keys（仓库2）

### 三、创建 SSH 配置文件

在 `~/.ssh/` 目录下创建 `config` 文件：

```bash
# 编辑 config 文件
nano ~/.ssh/config
```

填入以下内容：

```bash
# 个人仓库（默认）
Host github.com
    HostName github.com
    PreferredAuthentications publickey
    IdentityFile ~/.ssh/id_rsa

# 工作仓库（自定义别名）
Host github-work
    HostName github.com
    PreferredAuthentications publickey
    IdentityFile ~/.ssh/id_rsa_work

# 也可以用域名区分
# Host github.com-company
#     HostName github.com
#     IdentityFile ~/.ssh/id_rsa_company
```

### 四、修改本地仓库配置

#### 方法一：直接修改 .git/config

打开仓库的 `.git/config` 文件：

```ini
# 仓库1（个人）
[remote "origin"]
    url = git@github.com:username/personal-repo.git

# 仓库2（工作）
[remote "origin"]
    url = git@github-work:company/work-repo.git
```

#### 方法二：使用 git remote 命令

```bash
# 克隆时指定 host
git clone git@github-work:company/work-repo.git

# 或者修改已存在的仓库
git remote set-url origin git@github-work:company/work-repo.git
```

## 验证配置

```bash
# 测试连接
ssh -T git@github.com
# 期望输出：Hi username! You've successfully authenticated...

ssh -T git@github-work
# 期望输出：Hi company! You've successfully authenticated...
```

## 多账号管理最佳实践

### 1. 清晰的命名规范

```bash
~/.ssh/
├── id_rsa              # 个人主账号
├── id_rsa.pub
├── id_rsa_work         # 工作账号
├── id_rsa_work.pub
├── id_rsa_client1      # 客户项目A
├── id_rsa_client1.pub
└── config              # SSH 配置文件
```

### 2. Windows 用户注意

Windows 系统 SSH 配置文件位置：`C:\Users\用户名\.ssh\config`

确保文件格式为 **UTF-8 without BOM**

### 3. GitHub 多账号使用

```bash
# 克隆不同仓库
git clone git@github.com:username/repo1.git      # 使用 id_rsa
git clone git@github-work:company/repo2.git     # 使用 id_rsa_work
```

## 常见问题

### Q: Permission denied (publickey)

A: 检查 SSH Key 是否正确添加：
```bash
# 调试连接
ssh -vT git@github.com

# 查看加载了哪些 Key
ssh-add -l
```

### Q: 仍然提示需要密码

A: 确认 config 文件格式正确：
```
Host github.com
    HostName github.com
    IdentityFile ~/.ssh/id_rsa
```

### Q: Windows Git Bash 无法识别 config

A: 使用记事本或 VS Code 创建 config 文件，避免格式问题

## 简化版 config 示例

```bash
# 默认
Host github.com
    HostName github.com
    IdentityFile ~/.ssh/id_rsa

# 别名1
Host gh-work
    HostName github.com
    IdentityFile ~/.ssh/id_rsa_work
```

## 总结

| 步骤 | 操作 |
|:---|:---|
| 1 | 生成多个 SSH Key（不同文件名） |
| 2 | 添加到对应的 GitHub 账户 |
| 3 | 创建 `~/.ssh/config` 配置 |
| 4 | 修改仓库 remote URL 或克隆时指定 |

通过以上配置，就可以在一台机器上同时使用多个 GitHub 账号管理不同的仓库了。
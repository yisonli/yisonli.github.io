---
title: 《PHP7内核剖析》之PHP基础架构
date: '2018-04-27T00:00:00'
draft: false
categories:
- 编程
tags:
- PHP
- 内核
- 底层原理
description: 深入理解 PHP 的基本构成、生命周期以及各阶段的工作流程
lastmod: 2018-04-27
image: /images/cover-programming.svg
---
> 有幸在读秦朋的《PHP 内核剖析》一书，收获良多。为了加深理解，依照书中内容整理了 PHP 的基本架构和生命周期。

## PHP 的构成

PHP 的源代码主要由以下几个核心模块组成：

```
┌─────────────────────────────────────────────────────┐
│                    PHP 架构图                        │
├─────────────────────────────────────────────────────┤
│  ┌─────────┐                                        │
│  │  SAPI   │  ← 应用接口层（Apache2Handler/FastCGI）│
│  └────┬────┘                                        │
│  ┌────▼────┐                                        │
│  │  main   │  ← 输入/输出、Web通信、框架初始化        │
│  └────┬────┘                                        │
│  ┌────▼────┐                                        │
│  │  Zend   │  ← PHP 解析器核心（Zend Engine）        │
│  └────┬────┘                                        │
│  ┌────▼────┐                                        │
│  │   ext   │  ← PHP 扩展目录                         │
│  └─────────┘                                        │
│  ┌─────────┐                                        │
│  │  TSRM   │  ← 线程安全资源管理                     │
│  └─────────┘                                        │
└─────────────────────────────────────────────────────┘
```

### 核心模块说明

| 模块 | 说明 |
|:---|:---|
| **SAPI** | Server Application Programming Interface，PHP 的应用接口层，负责与 Web 服务器交互 |
| **main** | PHP 的核心代码，处理输入/输出、Web 通信、扩展加载、配置解析等工作 |
| **Zend** | PHP 解析器的主要实现，即 Zend Engine，是 PHP 语言的核心 |
| **ext** | PHP 的扩展目录，提供了各种功能的扩展（GD、MySQL、JSON 等） |
| **TSRM** | Thread Safe Resource Manager，线程安全相关的实现 |

### 各模块协作关系

```
Web Server (Apache/Nginx)
        │
        ▼
    SAPI Layer
        │
        ▼
    main (请求初始化、配置解析)
        │
        ▼
    Zend Engine (词法分析 → 语法分析 → 编译 → 执行)
        │
        ▼
    PHP Extensions (提供各种内置函数)
```

## PHP 的生命周期

```
┌─────────────────────────────────────────────────────────────┐
│                    PHP 生命周期                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌───────────────────┐                                     │
│  │  模块初始化阶段    │  MINIT (Module Initialization)    │
│  │  (PHP-FPM 启动时) │  - 加载扩展                        │
│  └─────────┬─────────┘  - 初始化扩展                      │
│            │            - 注册常量/函数                     │
│            ▼                                              │
│  ┌───────────────────┐                                     │
│  │  请求初始化阶段    │  RINIT (Request Initialization)   │
│  │  (每个请求开始时)  │  - 重置全局变量                    │
│  └─────────┬─────────┘  - 初始化静态变量                   │
│            │            - 启动 session                      │
│            ▼                                              │
│  ┌───────────────────┐                                     │
│  │  执行脚本阶段      │  Execute Script                     │
│  │  (核心执行期)      │  - 编译 PHP 代码为 OpCodes        │
│  └─────────┬─────────┘  - 执行 OpCodes                     │
│            │            - 输出响应                          │
│            ▼                                              │
│  ┌───────────────────┐                                     │
│  │  请求关闭阶段      │  RSHUTDOWN (Request Shutdown)      │
│  │  (每个请求结束时)  │  - 刷新输出缓冲区                  │
│  └─────────┬─────────┘  - 发送 HTTP 响应                   │
│            │            - 清理全局变量                      │
│            ▼                                              │
│  ┌───────────────────┐                                     │
│  │  模块关闭阶段      │  MSHUTDOWN (Module Shutdown)       │
│  │  (PHP-FPM 关闭时)  │  - 关闭扩展                       │
│  └───────────────────┘  - 释放资源                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 1. 模块初始化阶段 (MINIT)

```c
// PHP 扩展中的模块初始化函数
PHP_MINIT_FUNCTION(my_extension)
{
    // 注册常量
    REGISTER_STRING_CONSTANT("MY_EXT_VERSION", "1.0.0", CONST_PERSISTENT);
    
    // 注册函数
    REGISTER_FUNCTION(MyNamespace, my_function);
    
    // 初始化类
    zend_class_entry ce;
    INIT_CLASS_ENTRY(ce, "MyClass", my_class_methods);
    // ...
    
    return SUCCESS;
}
```

**主要任务：**
- 加载并初始化 PHP 扩展
- 注册常量和函数
- 注册类接口
- 初始化线程安全

### 2. 请求初始化阶段 (RINIT)

```c
// 请求开始时调用
PHP_RINIT_FUNCTION(my_extension)
{
    // 重置全局变量
    MyG(enabled) = 0;
    
    // 启动 session（如果配置了 auto_start）
    php_session_start();
    
    return SUCCESS;
}
```

**主要任务：**
- 重置全局变量
- 初始化静态变量
- 启动 session
- 初始化用户级别的计数器

### 3. 执行脚本阶段

```
PHP 代码
    │
    ▼
┌─────────────────┐
│  Lexer (词法)   │  将代码转换为 Token
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Parser (语法)  │  将 Token 转换为 AST
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Compiler (编译) │  将 AST 转换为 OpArray
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Executor (执行) │  逐条执行 OpCode
└─────────────────┘
```

**主要任务：**
- 词法分析 → 语法分析 → 编译
- 生成 OpCode（操作码）
- 执行 OpCode
- 输出响应内容

### 4. 请求关闭阶段 (RSHUTDOWN)

```c
// 请求结束时调用
PHP_RSHUTDOWN_FUNCTION(my_extension)
{
    // 刷新输出
    while (OG(ob_nesting_level) > 0) {
        og_level--;
    }
    
    // 清理用户空间对象
    // ...
    
    return SUCCESS;
}
```

**主要任务：**
- 刷新输出缓冲区
- 发送 HTTP 响应
- 清理全局变量
- 关闭 session

### 5. 模块关闭阶段 (MSHUTDOWN)

```c
// PHP-FPM 关闭时调用
PHP_MSHUTDOWN_FUNCTION(my_extension)
{
    // 注销常量和类
    // 释放持久化资源
    
    return SUCCESS;
}
```

**主要任务：**
- 关闭所有扩展
- 释放持久化资源
- 清理线程安全数据

## 不同的 SAPI 模式

PHP 在不同运行环境下，工作模式有所差异：

| SAPI | 启动次数 | 生命周期 |
|:---|:---:|:---|
| **CLI/CGI** | 每次请求 | 完整生命周期 |
| **PHP-FPM** | 一次启动 | MINIT 一次，请求周期重复 |
| **mod_php (Apache)** | 一次启动 | MINIT 一次，请求周期重复 |

### PHP-FPM 生命周期

```
┌─────────────────────────────────────────────────────┐
│              PHP-FPM Master Process                  │
│  - 监听端口                                         │
│  - 管理 Worker 进程                                  │
│  - MINIT 只执行一次                                  │
└───────────────────────┬─────────────────────────────┘
                        │ fork
                        ▼
┌─────────────────────────────────────────────────────┐
│              PHP-FPM Worker Process                 │
│  - 处理请求                                         │
│  - 重复执行 RINIT → 执行 → RSHUTDOWN               │
└─────────────────────────────────────────────────────┘
```

## 总结

1. PHP 架构由 SAPI、main、Zend、ext、TSRM 五大模块组成
2. PHP 生命周期分为 5 个阶段：模块初始化、请求初始化、脚本执行、请求关闭、模块关闭
3. 不同 SAPI 模式下，生命周期有所差异（CLI 每次都完整执行，PHP-FPM 只在启动时执行 MINIT）
4. 理解 PHP 生命周期对于编写高效扩展和排查问题非常重要

## 参考资料

- 《PHP 内核剖析》- 秦朋
- [PHP 官方文档](https://www.php.net/manual/zh/internals2.php)
---
categories:
- 编程
date: 2018-11-05
description: PHP7 内存管理机制详解，深入理解 Zend 引擎的内存分配与释放
image: /images/cover-programming.svg
lastmod: 2018-11-05
tags:
- PHP
- 内存管理
- PHP7
title: PHP7内存管理 - 谁动了我的内存
---

> 来源：Laruence

> Zend 引擎提供了一种特殊的内存管理器，用于处理请求相关数据。请求相关数据是指只需要服务于单个请求，最迟会在请求结束时释放的数据。

## 内存管理基础

### 问题引入

```php
<?php

var_dump(memory_get_usage());
// 输出：int(61800) 初始内存

$a = "laruence";
var_dump(memory_get_usage());
// 输出：int(61864) 字符串占用

unset($a);
var_dump(memory_get_usage());
// 输出：int(61864) 为什么没有释放？
```

### 内存管理机制

```
┌─────────────────────────────────────────────────────────────┐
│                   PHP 内存管理机制                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   分配请求数据                                               │
│        │                                                    │
│        ▼                                                    │
│   ┌─────────┐                                               │
│   │ Zend MM │  ← 特殊内存管理器                            │
│   └────┬────┘                                               │
│        │                                                    │
│        ▼                                                    │
│   ┌─────────────────────────────────────────┐              │
│   │          堆（Heap）                      │              │
│   │  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐      │              │
│   │  │chunk│ │chunk│ │chunk│ │chunk│      │              │
│   │  └─────┘ └─────┘ └─────┘ └─────┘      │              │
│   └─────────────────────────────────────────┘              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 内存分配策略

### Zend MM 内存池

```php
<?php

// 预分配内存（减少系统调用）
var_dump(memory_get_usage(true));
// 输出：int(262144) 256KB 预分配

// 查看峰值
var_dump(memory_get_peak_usage());
// 输出：最大内存使用量

// 峰值（真实分配）
var_dump(memory_get_peak_usage(true));
```

### 内存分配函数

| 函数 | 说明 |
|:---|:---|
| `emalloc()` | 分配请求内存 |
| `efree()` | 释放请求内存 |
| `estrdup()` | 复制字符串 |
| `ecalloc()` | 分配并初始化为零 |
| `erealloc()` | 重新分配内存 |

## PHP 7 内存改进

### 与 PHP 5 的区别

```
┌─────────────────────────────────────────────────────────────┐
│                  PHP 5 vs PHP 7 内存对比                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   PHP 5:                                                     │
│   ┌────────────────────┐                                    │
│   │ zval (16 bytes)   │                                    │
│   │ ├─ refcount (4B)   │                                    │
│   │ ├─ is_ref (4B)     │                                    │
│   │ └─ value (8B)      │                                    │
│   └────────────────────┘                                    │
│                                                             │
│   PHP 7:                                                     │
│   ┌────────────────────┐                                    │
│   │ zval (16/32 bytes) │                                    │
│   │ ├─ type (1B)       │                                    │
│   │ ├─ flags (1B)      │                                    │
│   │ └─ value/unioned   │                                    │
│   └────────────────────┘                                    │
│                                                             │
│   字符串： zend_string (40 bytes) → (x)ptr + len + hash    │
│   对象：   zend_object → Object handlers                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 优化效果

```php
<?php
// PHP 5 vs PHP 7 性能对比

// 创建 100000 个简单对象
$start = memory_get_usage();

// PHP 5: ~50MB
// PHP 7: ~5MB

for ($i = 0; $i < 100000; $i++) {
    $objects[] = new stdClass();
}

$end = memory_get_usage();
echo "内存增长: " . ($end - $start) . " bytes\n";
```

## 引用计数与循环引用

### 引用计数机制

```php
<?php

// 变量 a 引用计数为 1
$a = "hello";
debug_zval_dump($a);
// 输出：string(5) "hello" refcount(1)

// 变量 b 也引用同一个值，引用计数为 2
$b = $a;
debug_zval_dump($a);
// 输出：string(5) "hello" refcount(2)

// 删除 b，引用计数回到 1
unset($b);
debug_zval_dump($a);
// 输出：string(5) "hello" refcount(1)
```

### 循环引用问题

```php
<?php

// PHP 5 中的循环引用
$a = new stdClass();
$b = new stdClass();

$a->b = $b;  // a 引用 b
$b->a = $a;  // b 引用 a

// 此时：refcount(a) = 2, refcount(b) = 2
// unset(a): refcount(a) = 1, refcount(b) = 2
// 内存泄漏！

// PHP 7 使用标记清除（GC）解决
unset($a);
unset($b);
// GC 周期会清除循环引用
```

### 手动垃圾回收

```php
<?php

// 查看待回收数量
gc_enabled();                    // 垃圾回收是否启用
gc_collect_cycles();              // 强制回收循环引用

// 记录垃圾回收状态
$start = gc_collect_cycles();
echo "回收前待处理: $start\n";

// 产生循环引用
$a = new stdClass();
$b = new stdClass();
$a->b = $b;
$b->a = $a;

unset($a);
unset($b);

$after = gc_collect_cycles();
echo "回收后待处理: $after\n";
```

## 内存泄漏检测

### 开启内存泄漏检测

```bash
# 编译时启用
./configure --enable-debug --with-valgrind

# 运行测试
php -d memory_limit=128M -d zend.enable_gc=1 script.php
```

### Xdebug 内存跟踪

```ini
; php.ini
[xdebug]
xdebug.mode=memory
```

```php
<?php

// 查看函数调用栈
xdebug_debug_zval('a');

// 查看文件调用
xdebug_stop_trace();
```

## 优化建议

### 1. 及时 unset 大变量

```php
<?php

// 不推荐：大数组保留在内存中
$bigArray = loadLargeData();  // 10MB
process($bigArray);
// $bigArray 仍然占用内存

// 推荐：及时释放
$bigArray = loadLargeData();
process($bigArray);
unset($bigArray);  // 释放内存
```

### 2. 使用引用减少复制

```php
<?php

// 不推荐：复制整个数组
function processArray(array $arr) {
    // 副本，额外内存
}
$data = range(1, 100000);
processArray($data);

// 推荐：引用传递
function processArray(array &$arr) {
    // 同一数组，无复制
}
processArray($data);
```

### 3. 生成器处理大数据

```php
<?php

// 不推荐：一次性加载
function getAllUsers() {
    $users = [];
    foreach ($db->query('SELECT * FROM users') as $row) {
        $users[] = $row;  // 全部加载到内存
    }
    return $users;
}

// 推荐：生成器
function getUsersGenerator() {
    foreach ($db->query('SELECT * FROM users') as $row) {
        yield $row;  // 逐个返回
    }
}

foreach (getUsersGenerator() as $user) {
    process($user);
}
```

### 4. 静态变量陷阱

```php
<?php

class HeavyClass {
    private static $cache = [];

    public static function getInstance() {
        if (!isset(self::$cache['instance'])) {
            self::$cache['instance'] = new HeavyClass();
        }
        return self::$cache['instance'];
    }
    
    // 清理静态缓存
    public static function clearCache() {
        self::$cache = [];
    }
}
```

## 性能监控

```php
<?php

class MemoryProfiler {
    private static $marks = [];

    public static function mark(string $name) {
        self::$marks[$name] = memory_get_usage(true);
    }

    public static function report(): array {
        $report = [];
        $last = null;
        foreach (self::$marks as $name => $usage) {
            $delta = ($last !== null) ? ($usage - $last) : 0;
            $report[$name] = [
                'memory' => $usage,
                'delta'  => $delta,
            ];
            $last = $usage;
        }

        return $report;
    }
}

// 使用示例
MemoryProfiler::mark('bootstrap');
// ... 业务 ...
MemoryProfiler::mark('after_query');
print_r(MemoryProfiler::report());
```
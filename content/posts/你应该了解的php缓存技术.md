---
title: 你应该了解的PHP缓存技术
date: '2019-01-09T00:00:00'
draft: false
categories:
- 编程
tags:
- PHP
- 缓存
- Memcached
- Redis
description: PHP 缓存技术全面解析：编译缓存、数据缓存、内存缓存、分布式缓存
lastmod: 2019-01-09
image: /images/cover-programming.svg
---
> 缓存是现代系统中必不可少的模块，已经成为高并发高性能架构的关键组件。

## 缓存概念

### 什么是缓存

缓存是将程序或系统经常要调用的对象存在内存中，以便快速调用，不必重复创建实例。这样可以减少系统开销，提高系统效率。

### 缓存分类

| 类型 | 说明 | 示例 |
|:---|:---|:---|
| **文件缓存** | 数据存储在磁盘上 | XML、JSON、序列化文件 |
| **内存缓存** | 存储在静态内存区域 | Application、静态 Map |
| **分布式缓存** | 跨进程、跨域访问 | Redis、Memcached |

## PHP 缓存类型

### PHP 编译缓存

PHP 是解释型语言，执行过程包括：
1. **编译过程**：读取文件，编译成中间码
2. **执行过程**：直接执行中间码

**问题**：
- 即使代码文件未改变，也会被重新编译
- 引用文件也需要重新编译

**解决方案**：PHP 编译缓存工具

| 工具 | 说明 |
|:---|:---|
| APC | Alternative PHP Cache |
| OPcache | PHP 内置（PHP 5.5+） |
| XCache | 国产高性能编译器 |

### 启用 OPcache

```ini
; php.ini
zend_extension=opcache.so

; 基本配置
opcache.enable=1
opcache.memory_consumption=128
opcache.max_accelerated_files=10000
opcache.revalidate_freq=2
```

### PHP 数据缓存

| 类型 | 缓存内容 | 工具 |
|:---|:---|:---|
| 数据库缓存 | 查询结果 | Memcached、Redis |
| 模板缓存 | 页面模板 | Smarty、Twig |

## 缓存优势

### 1. 提升性能

- 减少数据库查询
- 加速远程调用
- 降低响应时间

### 2. 缓解数据库压力

```
┌─────────┐    请求    ┌─────────┐
│   用户   │ ───────▶ │  Nginx  │
└─────────┘          └────┬────┘
                         │
                   ┌─────▼─────┐
                   │   缓存层   │ ◀──────┐ 命中
                   └─────┬─────┘        │
                         │ 未命中      │
                   ┌─────▼─────┐        │
                   │  数据库   │ ──────┘ 写入
                   └───────────┘
```

## 常用缓存方案

### 1. 文件缓存

```php
<?php

/**
 * 简单文件缓存类
 */
class FileCache
{
    private $cacheDir;
    private $expire = 3600;

    public function __construct(string $cacheDir = './cache', int $expire = 3600)
    {
        $this->cacheDir = rtrim($cacheDir, '/');
        $this->expire = $expire;
        
        if (!is_dir($this->cacheDir)) {
            mkdir($this->cacheDir, 0755, true);
        }
    }

    /**
     * 设置缓存
     */
    public function set(string $key, $value, ?int $expire = null): bool
    {
        $file = $this->getFilePath($key);
        $data = [
            'value' => $value,
            'expire' => time() + ($expire ?? $this->expire),
        ];
        
        return file_put_contents(
            $file,
            serialize($data),
            LOCK_EX
        ) !== false;
    }

    /**
     * 获取缓存
     */
    public function get(string $key, $default = null)
    {
        $file = $this->getFilePath($key);
        
        if (!file_exists($file)) {
            return $default;
        }
        
        $content = file_get_contents($file);
        $data = unserialize($content);
        
        if ($data['expire'] < time()) {
            unlink($file);
            return $default;
        }
        
        return $data['value'];
    }

    /**
     * 删除缓存
     */
    public function delete(string $key): bool
    {
        $file = $this->getFilePath($key);
        return file_exists($file) ? unlink($file) : true;
    }

    /**
     * 清除所有缓存
     */
    public function clear(): bool
    {
        $files = glob($this->cacheDir . '/*');
        foreach ($files as $file) {
            if (is_file($file)) {
                unlink($file);
            }
        }
        return true;
    }

    private function getFilePath(string $key): string
    {
        return $this->cacheDir . '/' . md5($key) . '.cache';
    }
}

// 使用示例
$cache = new FileCache('./cache', 3600);

// 设置缓存
$cache->set('user_1', ['name' => 'John', 'email' => 'john@example.com']);

// 获取缓存
$user = $cache->get('user_1');
if ($user) {
    echo "缓存命中: " . json_encode($user);
} else {
    // 从数据库获取
    $user = fetchUserFromDB(1);
    $cache->set('user_1', $user);
}
```

### 2. Memcached

```php
<?php

/**
 * Memcached 缓存封装
 */
class MemcachedCache
{
    private $memcached;

    public function __construct(array $servers = [])
    {
        $this->memcached = new Memcached();
        
        if (empty($servers)) {
            $servers = [
                ['127.0.0.1', 11211, 100],
            ];
        }
        
        $this->memcached->addServers($servers);
    }

    /**
     * 设置缓存
     */
    public function set(string $key, $value, int $ttl = 0): bool
    {
        return $this->memcached->set($key, $value, $ttl);
    }

    /**
     * 获取缓存
     */
    public function get(string $key)
    {
        return $this->memcached->get($key);
    }

    /**
     * 删除缓存
     */
    public function delete(string $key): bool
    {
        return $this->memcached->delete($key);
    }

    /**
     * 增加数值
     */
    public function increment(string $key, int $offset = 1)
    {
        return $this->memcached->increment($key, $offset);
    }

    /**
     * 清除所有缓存
     */
    public function flush(): bool
    {
        return $this->memcached->flush();
    }

    /**
     * 获取多条缓存
     */
    public function getMulti(array $keys): array
    {
        return $this->memcached->getMulti($keys);
    }

    /**
     * 批量设置
     */
    public function setMulti(array $items, int $ttl = 0): bool
    {
        return $this->memcached->setMulti($items, $ttl);
    }
}

// 使用示例
$cache = new MemcachedCache([
    ['127.0.0.1', 11211],
]);

// 设置缓存
$cache->set('user_1', ['name' => 'John'], 3600);

// 获取缓存
$user = $cache->get('user_1');

// 计数器
$cache->set('page_views', 0);
$cache->increment('page_views');
```

### 3. Redis

```php
<?php

/**
 * Redis 缓存封装
 */
class RedisCache
{
    private $redis;

    public function __construct(string $host = '127.0.0.1', int $port = 6379)
    {
        $this->redis = new Redis();
        $this->redis->connect($host, $port);
    }

    /**
     * 设置缓存
     */
    public function set(string $key, $value, ?int $ttl = null): bool
    {
        $value = is_array($value) ? json_encode($value) : $value;
        
        if ($ttl === null) {
            return $this->redis->set($key, $value);
        }
        
        return $this->redis->setex($key, $ttl, $value);
    }

    /**
     * 获取缓存
     */
    public function get(string $key)
    {
        $value = $this->redis->get($key);
        
        if ($value === null) {
            return null;
        }
        
        // 尝试 JSON 解码
        $decoded = json_decode($value, true);
        return json_last_error() === JSON_ERROR_NONE ? $decoded : $value;
    }

    /**
     * 删除缓存
     */
    public function delete(string $key): int
    {
        return (int) $this->redis->del($key);
    }

    /**
     * 判断键是否存在
     */
    public function exists(string $key): bool
    {
        return $this->redis->exists($key) > 0;
    }

    /**
     * 设置过期时间（秒）
     */
    public function expire(string $key, int $seconds): bool
    {
        return $this->redis->expire($key, $seconds);
    }
}

// 使用示例
$redis = new RedisCache();
$redis->set('foo', 'bar', 60);
var_dump($redis->get('foo'));
$redis->delete('foo');
```

> 提示：生产环境建议加连接池、统一 Key 前缀、超时与熔断，并结合业务决定哪些数据适合落在 Redis。

## 选型小结

| 场景 | 建议 |
|:---|:---|
| 单机小规模、持久化不重要 | 文件缓存 / APCu |
| 多节点共享会话、计数 | Memcached |
| 丰富数据结构 + 持久化 | Redis |

结合 OPcache 减少 PHP 脚本重复编译，再配合数据缓存，通常能在成本可控的前提下显著提升站点响应速度。
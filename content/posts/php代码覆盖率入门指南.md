---
categories:
- 编程
date: 2018-05-04
description: PHPUnit 单元测试与代码覆盖率配置的完整入门教程
image: /images/cover-programming.svg
lastmod: 2018-05-04
tags:
- PHP
- 单元测试
- PHPUnit
- 代码覆盖率
title: PHP代码覆盖率入门指南
---

> 最近在玩 PHP 的单元测试，以及代码覆盖率这块，遇到一些问题，记录下来作为简单入门参考。

## 安装 PHPUnit

### Composer 安装（推荐）

```bash
# 进入项目目录
cd your-project

# 安装 PHPUnit
composer require --dev phpunit/phpunit:^10.0

# 安装代码覆盖率扩展
composer require --dev phpunit/php-code-coverage
```

### PHP Archive (PHAR)

```bash
# 下载 PHPUnit
wget https://phar.phpunit.de/phpunit-10.phar

# 添加执行权限
chmod +x phpunit-10.phar

# 全局安装
sudo mv phpunit-10.phar /usr/local/bin/phpunit

# 验证
phpunit --version
```

## 基础单元测试示例

### 编写测试

```php
<?php
// tests/StackTest.php

namespace tests;

use PHPUnit\Framework\TestCase;

class StackTest extends TestCase
{
    /**
     * 测试空栈
     */
    public function testEmpty(): void
    {
        $stack = [];
        $this->assertEmpty($stack);

        return $stack;
    }

    /**
     * 测试压栈
     * @depends testEmpty
     */
    public function testPush(array $stack): array
    {
        array_push($stack, 'foo');
        $this->assertEquals('foo', $stack[count($stack) - 1]);
        $this->assertNotEmpty($stack);

        return $stack;
    }

    /**
     * 测试弹栈
     * @depends testPush
     */
    public function testPop(array $stack): void
    {
        $this->assertEquals('foo', array_pop($stack));
        $this->assertEmpty($stack);
    }
}
```

### 运行测试

```bash
# 运行所有测试
phpunit --verbose tests/

# 运行指定测试文件
phpunit --verbose tests/StackTest.php

# 运行指定测试方法
phpunit --verbose tests/StackTest.php --filter testPush
```

### 输出示例

```
PHPUnit 10.0 by Sebastian Bergmann and contributors.

Runtime:       PHP 8.2.0 with Xdebug 3.2.0

...                                                                 3 / 3 (100%)

Time: 149 ms, Memory: 10.00MB

OK (3 tests, 5 assertions)
```

## 代码覆盖率配置

### phpunit.xml 配置

```xml
<?xml version="1.0" encoding="UTF-8"?>
<phpunit xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:noNamespaceSchemaLocation="vendor/phpunit/phpunit/phpunit.xsd"
         bootstrap="vendor/autoload.php"
         colors="true"
         executionOrder="depends,defects"
         beStrictAboutOutputDuringTests="true"
         cacheResultFile=".phpunit.cache/test-results">
    
    <testsuites>
        <testsuite name="Unit Tests">
            <directory suffix="Test.php">./tests</directory>
        </testsuite>
    </testsuites>

    <coverage>
        <include>
            <directory suffix=".php">./src</directory>
        </include>
        <exclude>
            <directory suffix=".php">./src/Exceptions</directory>
            <file>./src/bootstrap.php</file>
        </exclude>
        
        <!-- HTML 报告 -->
        <report>
            <html outputDirectory="coverage"/>
        </report>
        
        <!-- Clover XML 报告（CI 集成） -->
        <report>
            <clover outputFile="coverage/clover.xml"/>
        </report>
    </coverage>
</phpunit>
```

### 运行覆盖率测试

```bash
# 生成覆盖率报告
phpunit --coverage-html coverage/

# 指定覆盖率输出目录
phpunit --coverage-html ./report/coverage/

# 生成 Clover XML 格式
phpunit --coverage-clover coverage/clover.xml
```

## 常用断言方法

| 断言 | 说明 |
|:---|:---|
| `assertEquals($expected, $actual)` | 值相等 |
| `assertSame($expected, $actual)` | 同一对象/值 |
| `assertTrue($condition)` | 条件为真 |
| `assertFalse($condition)` | 条件为假 |
| `assertNull($value)` | 值为空 |
| `assertContains($needle, $haystack)` | 数组/字符串包含 |
| `assertCount($expected, $actual)` | 元素数量 |
| `assertEmpty($actual)` | 值为空 |
| `assertThrows($exception, $callable)` | 抛出异常 |
| `assertMatchesRegularExpression($pattern, $string)` | 正则匹配 |

## 测试依赖

### @depends 依赖

```php
public function testCreate(): array
{
    $entity = new Entity();
    $entity->create(['name' => 'test']);
    $this->assertNotNull($entity->getId());
    
    return ['id' => $entity->getId()];
}

/**
 * @depends testCreate
 */
public function testFind(array $data): void
{
    $entity = new Entity();
    $found = $entity->find($data['id']);
    
    $this->assertNotNull($found);
    $this->assertEquals('test', $found->name);
}
```

## 数据供给器

### @dataProvider

```php
/**
 * @dataProvider additionProvider
 */
public function testAddition(int $a, int $b, int $expected): void
{
    $this->assertEquals($expected, $a + $b);
}

public function additionProvider(): array
{
    return [
        'zero plus zero' => [0, 0, 0],
        'positive numbers' => [1, 2, 3],
        'negative numbers' => [-1, -1, -2],
    ];
}
```

## Mock 对象

### 创建 Mock

```php
use PHPUnit\Framework\TestCase;
use App\Services\UserService;
use App\Repositories\UserRepository;

class UserServiceTest extends TestCase
{
    public function testGetUserName(): void
    {
        // 创建 Mock 对象
        $repository = $this->createMock(UserRepository::class);
        
        // 配置 Mock 行为
        $repository->method('find')
            ->with(1)
            ->willReturn(['id' => 1, 'name' => 'John']);
        
        // 使用 Mock
        $service = new UserService($repository);
        $name = $service->getUserName(1);
        
        $this->assertEquals('John', $name);
    }
}
```

### Mock 方法链

```php
$mock = $this->getMockBuilder(stdClass::class)
    ->addMethods(['getName', 'setName'])
    ->getMock();

$mock->method('getName')->willReturn('Test');
```

## 数据集测试

```php
use PHPUnit\Framework\TestCase;

class DataProviderTest extends TestCase
{
    /**
     * @dataProvider additionProvider
     */
    public function testAdditions(int $a, int $b, int $expected): void
    {
        $this->assertEquals($expected, $a + $b);
    }

    public static function additionProvider(): array
    {
        return [
            'integers' => [1, 2, 3],
            'floats' => [0.1, 0.2, 0.3],
        ];
    }
}
```

## CI 集成

### GitHub Actions

```yaml
# .github/workflows/phpunit.yml
name: PHPUnit Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup PHP
        uses: shivammathur/setup-php@v2
        with:
          php-version: '8.2'
          extensions: xdebug
          coverage: xdebug
        
      - name: Install Dependencies
        run: composer install --prefer-dist
        
      - name: Run Tests with Coverage
        run: |
          ./vendor/bin/phpunit \n            --coverage-text \n            --coverage-clover coverage/clover.xml
        env:
          XDEBUG_MODE: coverage
```

## 常见问题

### Q: Xdebug 版本不兼容

```bash
# PHPUnit 10 需要 Xdebug 3.x
composer require --dev phpunit/phpunit:^10.0
pecl install xdebug

# Xdebug 2.x 适配 PHPUnit 9
composer require --dev phpunit/phpunit:^9.0
pecl install xdebug-2.9.8
```

### Q: 覆盖率不准确

检查 phpunit.xml 中的 include/exclude 配置是否正确：

```xml
<coverage>
    <include>
        <directory suffix=".php">./src</directory>
    </include>
</coverage>
```

## 最佳实践

1. **每个发布单元（类/模块）至少覆盖一条主路径与一条异常路径**，优先保证核心业务与错误分支可被测试执行到。

2. **单元测试避免直连真实数据库、MQ、第三方 HTTP**，可用接口抽象 + 内存实现或 Mock，使覆盖率反映的是「你的代码」而非外部环境。

3. **在 CI 中固定 PHPUnit、Xdebug 主版本**，并通过环境变量注入 `XDEBUG_MODE=coverage`，避免本地与流水线结果不一致。

4. **覆盖率是手段不是目的**：不必盲目追求 100%；对复杂条件分支优先补测试用例或重构降低圈复杂度。

5. **结合静态分析与 CR**：将 Clover/XML 输出接入 SonarQube、Codecov 等工具，对新增未覆盖代码做团队约定（例如 Diff Coverage 阈值）。

## 延伸阅读

- [PHPUnit 覆盖率文档](https://docs.phpunit.de/en/10.5/code-coverage.html)
- [Xdebug 覆盖率模式说明](https://xdebug.org/docs/code_coverage)
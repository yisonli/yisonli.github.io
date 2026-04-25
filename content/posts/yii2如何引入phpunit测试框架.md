---
title: 在Yii2框架上使用PHPUnit做单元测试与代码覆盖率
date: '2018-05-11T00:00:00'
draft: false
categories:
- 编程
tags:
- PHP
- Yii2
- PHPUnit
- 单元测试
- 代码覆盖率
description: Yii2 框架集成 PHPUnit 实现单元测试和代码覆盖率检测的完整指南
lastmod: 2018-05-11
image: /images/cover-programming.svg
---
> PHPUnit 是一个很不错的测试框架，既能做自动化单元测试，也能同时检测代码覆盖率。自己在 Yii 框架上经过一番尝试，总结了这篇配置指南。

## 目录结构约定

在 Yii2 项目下，需要创建 `phpunit` 目录：

```
yii2-project/
├── phpunit/
│   ├── README.md           # 说明文档
│   ├── _bootstrap.php     # 框架初始化文件
│   ├── phpunit.xml        # 配置文件
│   └── tests/
│       ├── UserAuthTest.php
│       └── ...
├── frontend/
├── backend/
└── common/
```

## _bootstrap.php 引导文件

参考 `frontend/web/index.php`，创建引导文件：

```php
<?php
// phpunit/_bootstrap.php

// 定义测试环境常量
defined('YII_DEBUG') or define('YII_DEBUG', true);
defined('YII_ENV') or define('YII_ENV', 'test');

// 引入 Composer 自动加载
require_once dirname(__DIR__) . '/vendor/autoload.php';

// 引入 Yii 入口文件
require_once dirname(__DIR__) . '/frontend/web/index.php';

// 返回应用实例（而不是运行）
return Yii::$app;
```

## phpunit.xml 配置

```xml
<?xml version="1.0" encoding="UTF-8"?>
<phpunit xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:noNamespaceSchemaLocation="vendor/phpunit/phpunit/phpunit.xsd"
         bootstrap="_bootstrap.php"
         backupGlobals="false"
         backupStaticAttributes="false"
         beStrictAboutCoversAnnotation="true"
         beStrictAboutOutputDuringTests="true"
         beStrictAboutTestsThatDoNotTestAnything="true"
         beStrictAboutTodoAnnotatedTests="true"
         forceCoversAnnotation="true"
         verbose="true"
         colors="true">
    
    <!-- 测试套件配置 -->
    <testsuites>
        <testsuite name="Application Test Suite">
            <directory suffix="Test.php">./tests</directory>
        </testsuite>
    </testsuites>

    <!-- 代码覆盖率配置 -->
    <coverage>
        <include>
            <directory suffix=".php">../frontend/controllers</directory>
            <directory suffix=".php">../backend/controllers</directory>
            <directory suffix=".php">../common</directory>
            <directory suffix=".php">../console</directory>
        </include>
        <exclude>
            <directory suffix=".php">../common/mail</directory>
            <directory suffix=".php">../common/config</directory>
        </exclude>
    </coverage>

    <!-- 日志配置 -->
    <logging>
        <log type="coverage-html" target="coverage"/>
        <log type="coverage-clover" target="logs/clover.xml"/>
        <log type="coverage-crap4j" target="logs/crap4j.xml"/>
        <log type="junit" target="logs/junit.xml"/>
        <log type="testdox-html" target="testdox/index.html"/>
    </logging>
</phpunit>
```

## 安装 PHPUnit

### 使用 Composer 安装

```bash
# 进入项目目录
cd your-yii2-project

# 安装 PHPUnit（建议作为开发依赖）
composer require --dev phpunit/phpunit:^9.0

# 或者安装带 PHP 版本支持的版本
composer require --dev phpunit/phpunit:"^9.0" --ignore-platform-reqs

# 安装代码覆盖率扩展
composer require --dev phpunit/php-code-coverage
```

### 验证安装

```bash
# 检查 PHPUnit 版本
./vendor/bin/phpunit --version

# PHPUnit 9.x 输出
# PHPUnit 9.6.x by Sebastian Bergmann and contributors.
```

## 测试命令

### 运行测试

```bash
# 进入测试目录
cd phpunit/

# 运行所有测试
../vendor/bin/phpunit --configuration phpunit.xml

# 指定测试文件
../vendor/bin/phpunit --configuration phpunit.xml tests/UserAuthTest.php

# 运行测试套件
../vendor/bin/phpunit --configuration phpunit.xml --testsuite "Application Test Suite"
```

### 生成覆盖率报告

```bash
# 生成 HTML 覆盖率报告
../vendor/bin/phpunit --configuration phpunit.xml --coverage-html coverage

# 生成 Clover XML 格式报告（可导入 CI 系统）
../vendor/bin/phpunit --configuration phpunit.xml --coverage-clover logs/clover.xml
```

## 编写单元测试

### 基本测试示例

```php
<?php
// tests/UserAuthTest.php

namespace tests;

use PHPUnit\Framework\TestCase;
use common\models\User;

class UserAuthTest extends TestCase
{
    /**
     * @covers \common\models\User
     */
    public function testUserCanBeCreated()
    {
        $user = new User();
        $user->username = 'testuser';
        $user->email = 'test@example.com';
        
        $this->assertInstanceOf(User::class, $user);
        $this->assertEquals('testuser', $user->username);
    }

    /**
     * @covers \common\models\User::validatePassword()
     */
    public function testPasswordValidation()
    {
        $user = new User();
        $user->password_hash = password_hash('secret', PASSWORD_DEFAULT);
        
        $this->assertTrue($user->validatePassword('secret'));
        $this->assertFalse($user->validatePassword('wrong'));
    }

    /**
     * @covers \common\models\User::getId()
     */
    public function testUserIdReturnsInteger()
    {
        $user = new User();
        $user->id = 123;
        
        $this->assertIsInt($user->getId());
        $this->assertEquals(123, $user->getId());
    }
}
```

### Yii2 ActiveRecord 测试

```php
<?php
// tests/UserModelTest.php

namespace tests;

use Yii;
use Codeception\Specify;
use common\fixtures\UserFixture;
use common\models\User;

class UserModelTest extends \yii\codeception\TestCase
{
    // 加载测试数据
    public $fixtures = [
        'user' => [
            'class' => UserFixture::class,
            'dataFile' => '@tests/fixtures/data/user.php',
        ],
    ];

    public function testUserLogin()
    {
        $user = User::findByUsername('erau');
        
        $this->assertNotNull($user);
        $this->assertTrue($user->validatePassword('password_0'));
    }

    public function testUserNotFound()
    {
        $user = User::findByUsername('nonexistent');
        
        $this->assertNull($user);
    }
}
```

### Fixture 数据文件

```php
<?php
// tests/fixtures/data/user.php

return [
    'user1' => [
        'id' => 1,
        'username' => 'erau',
        'auth_key' => 'testAuthKey_0',
        'password_hash' => '$2y$13$qFS7HXXkJb9V5KjZ8xX7EOYKvW7YQZ1xX7EOYKvW7YQZ1xX7EO',
        'email' => 'erau@example.com',
        'status' => 10,
        'created_at' => 1500000000,
        'updated_at' => 1500000000,
    ],
];
```

## 常用注解

| 注解 | 说明 |
|:---|:---|
| `@covers ClassName` | 指定测试覆盖的类 |
| `@covers ClassName::method` | 指定测试覆盖的方法 |
| `@coversNothing` | 该测试不计入覆盖率 |
| `@depends` | 依赖另一个测试 |
| `@dataProvider` | 数据供给器 |

```php
/**
 * @covers \common\models\User::findByUsername()
 * @covers \common\models\User::validatePassword()
 */
public function testLoginWithValidCredentials()
{
    // ...
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
          php-version: '8.1'
          extensions: pdo_mysql, intl
          coverage: xdebug
        
      - name: Install Dependencies
        run: composer install --prefer-dist
        
      - name: Run PHPUnit
        run: ./vendor/bin/phpunit --configuration phpunit.xml --colors=never
```

## 最佳实践

1. **遵循 AAA 模式**（Arrange-Act-Assert）
2. **测试单一职责** - 每个测试只验证一个行为
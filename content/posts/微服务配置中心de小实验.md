---
title: 微服务配置中心小实验
date: '2021-07-25T00:00:00'
draft: false
categories:
- 编程
tags:
- Go
- 微服务
- 配置中心
- Spring Cloud Config
description: 微服务配置中心实战：Spring Cloud Config + Go 客户端实现配置集中管理
lastmod: 2021-07-25
image: /images/cover-programming.svg
---
> 本文是个人在学习书籍《Go 语言高并发与微服务实战》第8章内容过程中，动手做的小实验，涉及 Spring Cloud Config 和 YAML 相关知识。

## 配置中心概念

```
┌─────────────────────────────────────────────────────────────┐
│                    配置中心架构                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌──────────────┐                                         │
│   │ 配置中心     │                                         │
│   │ Config Server│◀──── Git/SVN/Nacos                     │
│   └──────┬───────┘                                         │
│          │                                                  │
│          │ 拉取/推送                                        │
│          ▼                                                  │
│   ┌─────────────────────────────────────────┐              │
│   │           微服务集群                     │              │
│   │  ┌─────────┐  ┌─────────┐  ┌─────────┐│              │
│   │  │Service A│  │Service B│  │Service C││              │
│   │  └─────────┘  └─────────┘  └─────────┘│              │
│   └─────────────────────────────────────────┘              │
│                                                             │
│   特性：                                                    │
│   • 配置集中管理                                            │
│   • 配置热更新                                              │
│   • 环境隔离（dev/staging/prod）                          │
│   • 版本控制                                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Spring Cloud Config 简介

Spring Cloud Config 为分布式系统的外部配置提供了服务端和客户端支持。

### 核心特性

| 特性 | 说明 |
|:---|:---|
| 配置集中管理 | 所有配置存储在 Git 仓库 |
| 环境隔离 | dev、test、prod 环境分离 |
| 配置加密 | 支持敏感配置加密存储 |
| 动态刷新 | 无需重启即可更新配置 |
| 高可用 | 支持集群部署 |

## 准备 Spring Boot 环境

### macOS 安装

```bash
# 使用 Homebrew 安装
brew tap spring-io/tap
brew install spring-boot

# 或安装 Spring CLI
brew install springboot
```

### 快速开始

创建 `app.groovy`：

```groovy
@RestController
class ThisWillActuallyRun {
    @RequestMapping("/")
    String home() {
        "Hello World!"
    }
}
```

运行：

```bash
spring run app.groovy
```

## 创建配置中心服务端

### 项目结构

```
config-server/
├── pom.xml
├── src/main/java/com/example/configserver/
│   └── ConfigServerApplication.java
└── config/
    └── application.yml
```

### Maven 依赖 (pom.xml)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    
    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>2.5.2</version>
    </parent>
    
    <dependencies>
        <!-- Spring Cloud Config Server -->
        <dependency>
            <groupId>org.springframework.cloud</groupId>
            <artifactId>spring-cloud-config-server</artifactId>
        </dependency>
        
        <!-- Eureka 服务发现（可选）-->
        <dependency>
            <groupId>org.springframework.cloud</groupId>
            <artifactId>spring-cloud-starter-netflix-eureka-client</artifactId>
        </dependency>
    </dependencies>
    
    <dependencyManagement>
        <dependencies>
            <dependency>
                <groupId>org.springframework.cloud</groupId>
                <artifactId>spring-cloud-dependencies</artifactId>
                <version>2020.0.2</version>
                <type>pom</type>
                <scope>import</scope>
            </dependency>
        </dependencies>
    </dependencyManagement>
</project>
```

### 启动类

```java
@SpringBootApplication
@EnableConfigServer
public class ConfigServerApplication {
    public static void main(String[] args) {
        SpringApplication.run(ConfigServerApplication.class, args);
    }
}
```

### 配置文件

```yaml
# application.yml
server:
  port: 8888

spring:
  application:
    name: config-server
  cloud:
    config:
      server:
        git:
          uri: https://github.com/your-org/config-repo
          search-paths: config/{application}
          username: your-github-username
          default-label: main
```

## 配置仓库结构

```
config-repo/
├── config/
│   ├── user-service/
│   │   ├── application.yml      # 默认配置
│   │   ├── application-dev.yml  # 开发环境
│   │   ├── application-test.yml # 测试环境
│   │   └── application-prod.yml # 生产环境
│   └── order-service/
│       └── application.yml
└── README.md
```

### 示例配置

```yaml
# user-service/application.yml
server:
  port: ${PORT:8080}

spring:
  application:
    name: user-service
  datasource:
    url: jdbc:mysql://localhost:3306/user_db
    username: root
    password: ${DB_PASSWORD}
  redis:
    host: ${REDIS_HOST:localhost}
    port: ${REDIS_PORT:6379}

# 用户服务配置
user:
  cache:
    ttl: 3600
    max-size: 1000
  rate-limit:
    qps: 100
```

```yaml
# user-service/application-dev.yml
spring:
  datasource:
    url: jdbc:mysql://localhost:3306/user_db_dev
    password: dev_password
  redis:
    host: localhost

user:
  rate-limit:
    qps: 10  # 开发环境限流放宽
```

## Go 客户端接入

### 安装依赖

```bash
go get github.com/spf13/viper
go get github.com/go-laoji/go-config
```

### Viper 配置

```go
// config/config.go
package config

import (
    "fmt"
    "github.com/spf13/viper"
)

type Config struct {
    App      AppConfig      `mapstructure:"app"`
    Database DatabaseConfig `mapstructure:"database"`
    Redis    RedisConfig    `mapstructure:"redis"`
    User     UserConfig     `mapstructure:"user"`
}

type AppConfig struct {
    Name string `mapstructure:"name"`
    Port int    `mapstructure:"port"`
}

type DatabaseConfig struct {
    Host     string `mapstructure:"host"`
    Port     int    `mapstructure:"port"`
    Username string `mapstructure:"username"`
    Password string `mapstructure:"password"`
    Name     string `mapstructure:"name"`
}

type RedisConfig struct {
    Host     string `mapstructure:"host"`
    Port     int    `mapstructure:"port"`
    Password string `mapstructure:"password"`
    DB       int    `mapstructure:"db"`
}

type UserConfig struct {
    Cache     CacheConfig     `mapstructure:"cache"`
    RateLimit RateLimitConfig `mapstructure:"rate-limit"`
}

type CacheConfig struct {
    TTL      int `mapstructure:"ttl"`
    MaxSize  int `mapstructure:"max-size"`
}

type RateLimitConfig struct {
    QPS int `mapstructure:"qps"`
}

var GlobalConfig *Config

func LoadConfig(configServer, appName, profile string) (*Config, error) {
    v := viper.New()
    
    // 设置配置中心地址
    configURL := fmt.Sprintf("http://%s/%s/%s", configServer, appName, profile)
    v.SetConfigType("yaml")
    
    // 从配置中心获取配置
    if err := v.SafeGetConfigFile(configURL); err != nil {
        // 尝试直接读取
        v.SetConfigFile(fmt.Sprintf("config/%s.yml", profile))
        if err := v.ReadInConfig(); err != nil {
            return nil, err
        }
    }
    
    var cfg Config
    if err := v.Unmarshal(&cfg); err != nil {
        return nil, err
    }
    
    GlobalConfig = &cfg
    return &cfg, nil
}

// 本地配置（备用）
func LoadLocalConfig() (*Config, error) {
    v := viper.New()
    
    v.SetConfigName("config")
    v.SetConfigType("yaml")
    v.AddConfigPath("./config")
    
    if err := v.ReadInConfig(); err != nil {
        return nil, err
    }
    
    var cfg Config
    if err := v.Unmarshal(&cfg); err != nil {
        return nil, err
    }
    
    GlobalConfig = &cfg
    return &cfg, nil
}
```

若配置中心不可用，`LoadLocalConfig()` 可作为本地开发与灾备兜底；关键是保证 **profile**、**密钥**与 **环境变量注入** 在流水线与运行时一致。
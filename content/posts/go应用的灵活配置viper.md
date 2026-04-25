---
categories:
- 编程
date: 2019-10-10
description: Go 语言 Viper 配置管理库详解，支持多格式配置、环境变量、远程配置
image: /images/cover-programming.svg
lastmod: 2019-10-10
tags:
- Go
- 配置管理
- Viper
title: Go应用的灵活配置Viper
---

> Viper 是一个完整的 Go 应用程序配置解决方案，它可以处理所有类型的配置需求和格式。

## Viper 功能特性

| 功能 | 说明 |
|:---|:---|
| **多格式支持** | Yaml、Json、TOML、HCL、ENV、Java Properties |
| **多来源读取** | 文件、环境变量、命令行参数、远程配置 |
| **热加载** | 支持监听配置文件变化自动重载 |
| **类型转换** | 自动转换配置值为 Go 类型 |
| **远程配置** | 支持从 etcd、Consul、NATS 等读取配置 |
| **默认值** | 支持设置默认值 |

## 安装

```bash
go get -u github.com/spf13/viper
```

## 基础用法

### config.yaml 配置文件

```yaml
app:
  name: "my-app"
  version: "1.0.0"
  port: 8080

database:
  host: "localhost"
  port: 3306
  username: "root"
  password: "secret"
  name: "test_db"

redis:
  host: "127.0.0.1"
  port: 6379
  password: ""
  db: 0

information:
  list:
    - "One"
    - "Two"
    - "Three"
  lucky_number: 7

timestamp: "2019-10-10 14:15:16"
author: "Yisonli"
```

### 初始化配置

```go
package main

import (
    "fmt"
    "github.com/spf13/viper"
)

func main() {
    // 创建 Viper 实例
    v := viper.New()

    // 设置配置文件名（不含扩展名）
    v.SetConfigName("config")

    // 添加配置文件搜索路径
    v.AddConfigPath("./config/")
    v.AddConfigPath("$HOME/.app/")
    v.AddConfigPath("/etc/app/")

    // 设置配置文件类型
    v.SetConfigType("yaml")

    // 读取配置
    if err := v.ReadInConfig(); err != nil {
        panic(fmt.Errorf("配置读取失败: %w", err))
    }

    // 获取配置值
    fmt.Printf("应用名称: %s\n", v.GetString("app.name"))
    fmt.Printf("数据库主机: %s\n", v.GetString("database.host"))
    fmt.Printf("列表: %v\n", v.GetStringSlice("information.list"))
}
```

### 全局 Viper 实例

```go
var VP *viper.Viper

func AutoLoadConfig() error {
    VP = viper.New()

    // 设置配置文件名
    VP.SetConfigName("config")

    // 添加配置文件路径
    VP.AddConfigPath("./config/")

    // 设置配置文件类型
    VP.SetConfigType("yaml")

    if err := VP.ReadInConfig(); err != nil {
        return fmt.Errorf("配置读取失败: %w", err)
    }

    // 绑定环境变量
    VP.BindEnv("GOPATH")

    fmt.Printf("list: %+v, gopath: %s\n", VP.Get("information.list"), VP.Get("GOPATH"))
    return nil
}
```

## 高级用法

### 读取环境变量

```go
// 自动绑定环境变量
v.AutomaticEnv()
v.SetEnvPrefix("APP")           // 环境变量前缀：APP_DATABASE_HOST
v.SetEnvKeyReplacer(strings.NewReplacer(".", "_"))

// 手动绑定
v.BindEnv("database.host", "DB_HOST")  // 绑定到 DB_HOST 环境变量
```

### 读取命令行参数

```go
v.SetConfigFile("./config.yaml")  // 指定配置文件路径
v.SetConfigType("yaml")           // 明确配置文件类型

// 绑定 Pflags
v.BindPFlag("database.host", flag.Lookup("db-host"))
```

### 设置默认值

```go
v := viper.New()

v.SetDefault("app.port", 8080)
v.SetDefault("database.host", "localhost")
v.SetDefault("database.port", 3306)
v.SetDefault("cache.enabled", true)
```

### 类型安全获取

```go
// 字符串
name := v.GetString("app.name")

// 整数
port := v.GetInt("app.port")

// 布尔
enabled := v.GetBool("cache.enabled")

// 浮点数
rate := v.GetFloat64("api.rate_limit")

// 切片
list := v.GetStringSlice("information.list")

// Map
dbConfig := v.GetStringMap("database")
// dbConfig["host"], dbConfig["port"], etc.

// 嵌套获取
host := v.GetString("database.host")
listItem := v.GetString("information.list.0")  // "One"
```

### Unmarshal 到结构体

```go
type Config struct {
    App      AppConfig      `mapstructure:"app"`
    Database DatabaseConfig `mapstructure:"database"`
    Redis    RedisConfig    `mapstructure:"redis"`
}

type AppConfig struct {
    Name    string `mapstructure:"name"`
    Version string `mapstructure:"version"`
    Port    int    `mapstructure:"port"`
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

func main() {
    v := viper.New()
    v.SetConfigFile("config.yaml")
    v.SetConfigType("yaml")
    v.ReadInConfig()

    var config Config
    if err := v.Unmarshal(&config); err != nil {
        panic(err)
    }

    fmt.Printf("App: %s:%d\n", config.App.Name, config.App.Port)
    fmt.Printf("DB: %s:%d\n", config.Database.Host, config.Database.Port)
}
```

## 监听配置文件变化

```go
v := viper.New()
v.SetConfigName("config")
v.SetConfigType("yaml")
v.ReadInConfig()

// 监听配置变化
v.WatchConfig()
v.OnConfigChange(func(e fsnotify.Event) {
    fmt.Printf("配置文件已更新: %s\n", e.Name)
    // 重新读取配置
    v.ReadInConfig()
})
```

## 远程配置

### etcd 配置

```go
import (
    "github.com/spf13/viper/remote"
    "github.com/hashicorp/vault/api"
)

func initRemoteConfig() error {
    v := viper.New()

    // 设置远程源
    err := remote.AddProvider("etcd", "http://127.0.0.1:4001", "/config.yaml")
    if err != nil {
        return err
    }

    // 或者使用 Consul
    err = remote.AddProvider("consul", "http://127.0.0.1:8500", "/config.yaml", "my-consul-token")

    // 启用远程配置
    err = v.AddRemoteProvider("etcd", "http://127.0.0.1:4001", "/config.yaml")
    v.SetConfigType("yaml")
    
    return v.ReadRemoteConfig()
}
```

## 多环境配置

```go
// 根据环境加载不同配置
func loadConfig(env string) (*viper.Viper, error) {
    v := viper.New()

    // 基础配置
    v.SetConfigName("config")
    v.SetConfigType("yaml")
    v.AddConfigPath("./config/")

    // 环境特定配置
    if env != "" {
        v.SetConfigName("config." + env)  // config.dev.yaml, config.prod.yaml
    }

    if err := v.ReadInConfig(); err != nil {
        return nil, err
    }

    return v, nil
}

// 使用
v, err := loadConfig("dev")  // 加载 config.dev.yaml
```

## 最佳实践

### 项目结构

```
project/
├── config/
│   ├── config.yaml         # 默认配置
│   ├── config.dev.yaml     # 开发环境
│   ├── config.prod.yaml    # 生产环境
│   └── config.test.yaml    # 测试环境
├── config.yaml
└── main.go
```

### 环境变量配置

```bash
# .env 文件
APP_NAME=my-app
APP_ENV=production
DATABASE_HOST=localhost
DATABASE_PORT=3306
```

```go
// 加载 .env 文件
go get github.com/joho/godotenv

func main() {
    // 加载 .env 文件
    godotenv.Load()

    v := viper.New()
    v.AutomaticEnv()
    
    // 或者手动映射（键名建议使用点分层级，对应 yaml 嵌套字段）
    v.BindEnv("database.host", "DATABASE_HOST")
    v.BindEnv("database.port", "DATABASE_PORT")

    // 读取：优先配置文件，再以环境变量覆盖 AutomaticEnv / BindEnv 的值
    host := v.GetString("database.host")
    _ = host
}
```

> `.env` 只适合开发机本地密钥；线上请使用容器/编排注入的环境变量或密钥管理服务，`BindEnv` 只是把环境变量桥接到同一套键名。
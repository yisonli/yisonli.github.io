---
categories:
- 编程
date: 2021-07-17
description: gRPC 快速入门教程：定义服务、生成代码、构建 gRPC 服务和 HTTP 网关
image: /images/cover-programming.svg
lastmod: 2021-07-17
tags:
- Go
- gRPC
- 微服务
- Protobuf
title: GRPC一点通
---

> gRPC 是一个高性能、开源和通用的 RPC 框架，面向移动和 HTTP/2 设计。带来双向流、流控、头部压缩、单 TCP 连接上的多复用请求等特性。

## 什么是 gRPC

```
┌─────────────────────────────────────────────────────────────┐
│                      gRPC 架构                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   Client                          Server                    │
│     │                               │                       │
│     │  ─────── HTTP/2 ───────────▶ │                       │
│     │  Protobuf 序列化              │                       │
│     │                               │                       │
│     │◀─────── Protobuf ───────────│                       │
│     │                               │                       │
│                                                             │
│   特性：                                                    │
│   • HTTP/2 传输                                            │
│   • Protobuf 序列化                                         │
│   • 多语言支持                                              │
│   • 双向流                                                  │
│   • 强类型定义                                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 环境准备

### 安装 Protobuf 编译器

```bash
# macOS
brew install protobuf

# Linux
apt install protobuf-compiler

# Windows
# 下载 https://github.com/protocolbuffers/protobuf/releases
```

### 安装 Go 工具

```bash
# gRPC 核心库
go get -u google.golang.org/grpc

# Protobuf 插件
go install google.golang.org/protobuf/cmd/protoc-gen-go@latest
go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest

# gRPC Gateway（HTTP 转 gRPC）
go install github.com/grpc-ecosystem/grpc-gateway/v2/cmd/protoc-gen-grpc-gateway@latest

# 添加到 PATH
export PATH="$PATH:$(go env GOPATH)/bin"
```

## 定义服务

### 创建项目

```bash
mkdir grpc-demo && cd grpc-demo
go mod init grpc-demo
mkdir helloworld
```

### 编写 Proto 文件

```protobuf
// helloworld/simple.proto
syntax = "proto3";

option go_package = "grpc-demo/helloworld";

package helloworld;

// Greeting 服务定义
service Greeter {
  // 简单 RPC
  rpc SayHello (HelloRequest) returns (HelloReply) {}
  
  // 服务端流式 RPC
  rpc SayHelloServerStream (HelloRequest) returns (stream HelloReply) {}
  
  // 客户端流式 RPC
  rpc SayHelloClientStream (stream HelloRequest) returns (HelloReply) {}
  
  // 双向流式 RPC
  rpc SayHelloBidirectionalStream (stream HelloRequest) returns (stream HelloReply) {}
}

// 请求消息
message HelloRequest {
  string name = 1;
  int32 age = 2;
}

// 响应消息
message HelloReply {
  string message = 1;
  string timestamp = 2;
}
```

### 生成 Go 代码

```bash
# 生成 gRPC 代码
protoc --go_out=. --go_opt=paths=source_relative \n       --go-grpc_out=. --go-grpc_opt=paths=source_relative \n       helloworld/simple.proto

# 查看生成的文件
ls -la helloworld/
# simple.pb.go  - Protobuf 消息定义
# simple_grpc.pb.go - gRPC 服务定义
```

## 实现 gRPC 服务

```go
// helloworld/server.go
package main

import (
    "context"
    "fmt"
    "log"
    "net"
    
    "google.golang.org/grpc"
    pb "grpc-demo/helloworld"
)

type server struct {
    pb.UnimplementedGreeterServer
}

// 简单 RPC 实现
func (s *server) SayHello(ctx context.Context, req *pb.HelloRequest) (*pb.HelloReply, error) {
    return &pb.HelloReply{
        Message:   fmt.Sprintf("Hello, %s! You are %d years old.", req.Name, req.Age),
        Timestamp: fmt.Sprintf("%d", time.Now().Unix()),
    }, nil
}

// 服务端流式 RPC 实现
func (s *server) SayHelloServerStream(req *pb.HelloRequest, stream pb.Greeter_SayHelloServerStreamServer) error {
    for i := 0; i < 5; i++ {
        msg := fmt.Sprintf("Hello %s (stream %d)", req.Name, i+1)
        if err := stream.Send(&pb.HelloReply{Message: msg}); err != nil {
            return err
        }
        time.Sleep(500 * time.Millisecond)
    }
    return nil
}

// 客户端流式 RPC 实现
func (s *server) SayHelloClientStream(stream pb.Greeter_SayHelloClientStreamServer) error {
    var names []string
    for {
        req, err := stream.Recv()
        if err == io.EOF {
            return stream.SendAndClose(&pb.HelloReply{
                Message: fmt.Sprintf("Hello %v!", names),
            })
        }
        if err != nil {
            return err
        }
        names = append(names, req.Name)
    }
}

// 双向流式 RPC 实现
func (s *server) SayHelloBidirectionalStream(stream pb.Greeter_SayHelloBidirectionalStreamServer) error {
    for {
        req, err := stream.Recv()
        if err == io.EOF {
            return nil
        }
        if err != nil {
            return err
        }
        
        msg := fmt.Sprintf("Hello %s!", req.Name)
        if err := stream.Send(&pb.HelloReply{Message: msg}); err != nil {
            return err
        }
    }
}

func main() {
    lis, err := net.Listen("tcp", ":50051")
    if err != nil {
        log.Fatalf("failed to listen: %v", err)
    }
    
    s := grpc.NewServer()
    pb.RegisterGreeterServer(s, &server{})
    
    log.Println("gRPC server started on :50051")
    if err := s.Serve(lis); err != nil {
        log.Fatalf("failed to serve: %v", err)
    }
}
```

## 实现 gRPC 客户端

```go
// helloworld/client.go
package main

import (
    "context"
    "fmt"
    "log"
    "time"
    
    "google.golang.org/grpc"
    "google.golang.org/grpc/credentials/insecure"
    pb "grpc-demo/helloworld"
)

func main() {
    // 连接 gRPC 服务器
    conn, err := grpc.Dial(":50051", grpc.WithTransportCredentials(insecure.NewCredentials()))
    if err != nil {
        log.Fatalf("did not connect: %v", err)
    }
    defer conn.Close()
    
    client := pb.NewGreeterClient(conn)
    
    // 调用简单 RPC
    ctx, cancel := context.WithTimeout(context.Background(), time.Second)
    defer cancel()
    
    r, err := client.SayHello(ctx, &pb.HelloRequest{Name: "World", Age: 25})
    if err != nil {
        log.Fatalf("could not greet: %v", err)
    }
    log.Printf("Greeting: %s", r.GetMessage())
}
```

## 添加 HTTP Gateway

### 安装依赖

```bash
go get google.golang.org/grpc/proto
```

### Gateway 服务

```go
// gateway/main.go
package main

import (
    "context"
    "fmt"
    "net/http"
    
    "github.com/grpc-ecosystem/grpc-gateway/v2/runtime"
    "google.golang.org/grpc"
    "google.golang.org/grpc/credentials/insecure"
    pb "grpc-demo/helloworld"
)

func main() {
    ctx := context.Background()
    ctx, cancel := context.WithCancel(ctx)
    defer cancel()
    
    mux := runtime.NewServeMux()
    opts := []grpc.DialOption{
        grpc.WithTransportCredentials(insecure.NewCredentials()),
    }
    
    err := pb.RegisterGreeterHandlerFromEndpoint(ctx, mux, ":50051", opts)
    if err != nil {
        log.Fatalf("failed to register gateway: %v", err)
    }
    
    http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
        mux.ServeHTTP(w, r)
    })
    
    log.Println("HTTP Gateway started on :8080")
    http.ListenAndServe(":8080", nil)
}
```

### 启动服务

```bash
# 终端 1: 启动 gRPC 服务
go run helloworld/server.go

# 终端 2: 启动 HTTP Gateway
go run gateway/main.go

# 测试 HTTP 接口
curl -X POST http://localhost:8080/helloworld.Greeter/SayHello \n  -H "Content-Type: application/json" \n  -d '{"name": "World", "age": 25}'
```

## 四种 RPC 模式

| 模式 | 说明 |
|:---|:---|
| Unary（一元） | 客户端发起一次请求，服务端返回一次响应；最常见，类似普通 HTTP JSON。 |
| Server streaming（服务端流） | 客户端一次请求，服务端以流多次推送数据；适合大列表、订阅通知。 |
| Client streaming（客户端流） | 客户端多次写入流，服务端最终一次汇总响应；适合批量上传、日志汇总。 |
| Bidirectional streaming（双向流） | 两端可同时读写流；适合聊天、协作编辑、实时推送等对「管道」建模的场景。 |

选型上：能用 Unary 就不用流式；若业务本身是「按需拉取一块块数据」，优先考虑 Server streaming；必须在单连接上交织多条请求/响应时（如 HTTP/2 多路复用语义），再结合双向流评估。

### 小结

掌握四种模式后，阅读 `.proto` 里的 `rpc` 定义会更直观：`stream` 关键字出现在请求侧、响应侧或两侧，分别对应上述三种流式形态。
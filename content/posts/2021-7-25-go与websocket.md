---
title: GO与Websocket
date: '2026-04-25T02:46:02.596028'
draft: false
categories:
- 编程
tags:
- Go
- WebSocket
- 网络编程
description: 深入理解 WebSocket 协议原理，并通过 Go 语言实现实时通信应用
lastmod: 2021-07-25
image: /images/cover-programming.svg
---
> 本文介绍 WebSocket 协议的原理，以及如何使用 Go 语言实现 WebSocket 实时通信功能。

## 解决什么问题

WebSocket 是 HTML5 下一种新的协议。它实现了浏览器与服务器全双工通信，能更好的节省服务器资源和带宽并达到实时通讯的目的。

WebSocket 使得客户端和服务器之间的数据交换变得更加简单，允许服务端主动向客户端推送数据。在 WebSocket API 中，浏览器和服务器只需要完成一次握手，两者之间就直接可以创建持久性的连接，并进行双向数据传输。

现在，很多网站为了实现推送技术，所用的技术都是 Ajax 轮询。轮询是在特定的的时间间隔（如每1秒），由浏览器对服务器发出 HTTP 请求，然后由服务器返回最新的数据给客户端的浏览器。这种传统的模式带来很明显的缺点，即浏览器需要不断的向服务器发出请求，然而 HTTP 请求可能包含较长的头部，其中真正有效的数据可能只是很小的一部分，显然这样会浪费很多的带宽等资源。

HTML5 定义的 WebSocket 协议，能更好的节省服务器资源和带宽，并且能够更实时地进行通讯。

### WebSocket 与 TCP、HTTP 的关系

WebSocket 与 HTTP 协议一样都是基于 TCP 的，所以他们都是可靠的协议。WebSocket 和 HTTP 协议一样都属于应用层的协议，WebSocket 在建立握手连接时，数据是通过 HTTP 协议传输的，但是在建立连接之后，真正的数据传输阶段是不需要 HTTP 协议参与的。

```
┌─────────────────────────────────────────────────────────┐
│                      应用层                               │
│  ┌─────────────┐              ┌─────────────┐            │
│  │   HTTP      │              │  WebSocket  │            │
│  └──────┬──────┘              └──────┬──────┘            │
│         │                            │                   │
│  ┌──────▼──────┐              ┌──────▼──────┐           │
│  │  TLS/SSL   │              │     TLS     │            │
│  └──────┬──────┘              └──────┬──────┘           │
│         │                            │                   │
│  ┌──────▼────────────────────────────▼──────┐            │
│  │              TCP                         │            │
│  └─────────────────────────────────────────┘            │
└─────────────────────────────────────────────────────────┘
```

## 分层架构

```
┌────────────────────────────────────────┐
│           WebSocket 协议                │
│  ├── 握手层（HTTP Upgrade）            │
│  ├── 帧解析层（Frame Parsing）         │
│  └── 数据传输层（Message Handling）    │
├────────────────────────────────────────┤
│           Go 标准库 / Gorilla          │
│  ├── gorilla/websocket                 │
│  └── golang.org/x/net/websocket       │
└────────────────────────────────────────┘
```

## 了解 Socket 原理

### WebSocket 握手过程

1. **客户端发送握手请求**
```http
GET /ws HTTP/1.1
Host: localhost:8080
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==
Sec-WebSocket-Version: 13
```

2. **服务器响应握手**
```http
HTTP/1.1 101 Switching Protocols
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=
```

3. **握手完成后开始双向通信**

### Go 中使用 gorilla/websocket

```go
package main

import (
    "fmt"
    "log"
    "net/http"
    "github.com/gorilla/websocket"
)

var upgrader = websocket.Upgrader{
    ReadBufferSize:  1024,
    WriteBufferSize: 1024,
    CheckOrigin: func(r *http.Request) bool {
        return true // 生产环境应做 origin 检查
    },
}

func wsHandler(w http.ResponseWriter, r *http.Request) {
    // 升级 HTTP 连接为 WebSocket
    conn, err := upgrader.Upgrade(w, r, nil)
    if err != nil {
        log.Println("upgrade failed:", err)
        return
    }
    defer conn.Close()

    // 读取消息
    for {
        messageType, msg, err := conn.ReadMessage()
        if err != nil {
            log.Println("read failed:", err)
            break
        }
        log.Printf("received: %s", msg)

        // 发送消息
        err = conn.WriteMessage(messageType, msg)
        if err != nil {
            log.Println("write failed:", err)
            break
        }
    }
}

func main() {
    http.HandleFunc("/ws", wsHandler)
    fmt.Println("WebSocket server started at :8080")
    log.Fatal(http.ListenAndServe(":8080", nil))
}
```

## 最基本的 Demo

### 前端代码

```html
<!DOCTYPE html>
<html>
<head>
    <title>WebSocket Demo</title>
</head>
<body>
    <h2>WebSocket Client</h2>
    <input type="text" id="message" placeholder="输入消息">
    <button onclick="sendMessage()">发送</button>
    <div id="output"></div>

    <script>
        const ws = new WebSocket("ws://localhost:8080/ws");

        ws.onopen = () => {
            console.log("Connected to WebSocket");
            addMessage("已连接服务器");
        };

        ws.onmessage = (event) => {
            addMessage("收到: " + event.data);
        };

        ws.onclose = () => {
            addMessage("连接已关闭");
        };

        function sendMessage() {
            const msg = document.getElementById("message").value;
            ws.send(msg);
            addMessage("发送: " + msg);
        }

        function addMessage(msg) {
            document.getElementById("output").innerHTML += 
                "<p>" + msg + "</p>";
        }
    </script>
</body>
</html>
```

### 运行步骤

```bash
# 1. 安装依赖
go get github.com/gorilla/websocket

# 2. 运行服务器
go run server.go

# 3. 浏览器打开 index.html
```

## 功能升级你需要了解的

### 1. 心跳机制

保持连接活跃，防止被中间设备断开：

```go
// 心跳 Ping-Pong
type Hub struct {
    clients    map[*websocket.Conn]bool
    broadcast  chan []byte
    register   chan *websocket.Conn
    unregister chan *websocket.Conn
}

func (h *Hub) readPump(conn *websocket.Conn) {
    defer func() {
        h.unregister <- conn
        conn.Close()
    }()
    
    conn.SetReadDeadline(time.Now().Add(60 * time.Second))
    conn.SetPongHandler(func(string) error {
        conn.SetReadDeadline(time.Now().Add(60 * time.Second))
        return nil
    })
    
    for {
        _, msg, err := conn.ReadMessage()
        if err != nil {
            break
        }
        h.broadcast <- msg
    }
}

func (h *Hub) writePump(conn *websocket.Conn) {
    ticker := time.NewTicker(30 * time.Second)
    defer func() {
        ticker.Stop()
        conn.Close()
    }()
    
    for {
        select {
        case <-ticker.C:
            conn.SetWriteDeadline(time.Now().Add(10 * time.Second))
            if err := conn.WriteMessage(websocket.PingMessage, nil); err != nil {
                return
            }
        }
    }
}
```

### 2. 断线重连

```javascript
function connect() {
    ws = new WebSocket("ws://localhost:8080/ws");
    
    ws.onclose = () => {
        console.log("Connection closed, reconnecting...");
        setTimeout(connect, 3000); // 3秒后重连
    };
}
```

### 3. 消息类型

```go
// 文本消息
websocket.TextMessage

// 二进制消息
websocket.BinaryMessage

// Ping 消息
websocket.PingMessage

// Pong 消息
websocket.PongMessage

// 关闭消息
websocket.CloseMessage
```

## 总结

- WebSocket 实现了真正的全双工通信
- 基于 HTTP 握手协议建立连接
- Go 语言通过 `gorilla/websocket` 库可以轻松实现 WebSocket 服务
- 生产环境需要考虑：心跳机制、断线重连、安全认证等

## 参考资料

- [RFC 6455 - The WebSocket Protocol](https://tools.ietf.org/html/rfc6455)
- [gorilla/websocket](https://github.com/gorilla/websocket)
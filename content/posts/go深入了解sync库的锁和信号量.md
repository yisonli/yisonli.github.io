---
categories:
- 编程
date: 2019-10-15
description: Go sync 包完全指南：Mutex、RWMutex、Cond、WaitGroup、Once、Pool、Map
image: /images/cover-programming.svg
lastmod: 2019-10-15
tags:
- Go
- 并发
- sync
- 锁
- 信号量
title: Go深入了解sync库的锁和信号量
---

> sync 包提供了 Go 语言的基本同步基元，如互斥锁。除了 Once 和 WaitGroup 类型，大部分都适用于低水平程序线程，高水平的同步使用 channel 通信更好。

## 并发与同步

### Go 并发基础

```go
package main

import (
    "fmt"
    "time"
)

func main() {
    // 创建 goroutine
    go sayHello()
    
    // 主 goroutine 继续执行
    for i := 0; i < 5; i++ {
        fmt.Println("Main:", i)
        time.Sleep(time.Millisecond * 100)
    }
}

func sayHello() {
    for i := 0; i < 5; i++ {
        fmt.Println("Hello:", i)
        time.Sleep(time.Millisecond * 100)
    }
}
```

### 同步问题

```go
// 竞态条件示例
var counter int

func increment() {
    counter++  // 非原子操作
}

func main() {
    // 1000 个 goroutine 同时修改 counter
    for i := 0; i < 1000; i++ {
        go increment()
    }
    time.Sleep(time.Second)
    // 预期: 1000，实际可能: 900-1000 之间
    fmt.Println(counter)  // 存在竞态条件！
}
```

## sync.Mutex 互斥锁

### 基本用法

```go
package main

import (
    "fmt"
    "sync"
    "time"
)

type Counter struct {
    mu    sync.Mutex
    count int
}

func (c *Counter) Incr() {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.count++
}

func (c *Counter) Value() int {
    c.mu.Lock()
    defer c.mu.Unlock()
    return c.count
}

func main() {
    var counter Counter
    
    // 1000 个 goroutine 安全递增
    for i := 0; i < 1000; i++ {
        go counter.Incr()
    }
    
    time.Sleep(time.Second)
    fmt.Println(counter.Value())  // 输出: 1000
}
```

### 注意事项

- ✅ 使用 `defer` 确保锁一定会释放
- ✅ 锁的粒度要尽可能小
- ❌ 不要在持有锁时调用用户代码
- ❌ 不要忘记解锁

## sync.RWMutex 读写锁

### 适用场景

| 场景 | 锁类型 | 说明 |
|:---|:---|:---|
| 读多写少 | RWMutex | 多个读锁可并存 |
| 写操作 | Mutex | 独占访问 |

### 基本用法

```go
package main

import (
    "fmt"
    "sync"
    "time"
)

type SafeMap struct {
    mu sync.RWMutex
    m  map[string]int
}

func (sm *SafeMap) Set(key string, value int) {
    sm.mu.Lock()
    defer sm.mu.Unlock()
    sm.m[key] = value
}

func (sm *SafeMap) Get(key string) (int, bool) {
    sm.mu.RLock()  // 读锁
    defer sm.mu.RUnlock()
    val, ok := sm.m[key]
    return val, ok
}

func main() {
    sm := SafeMap{m: make(map[string]int)}
    
    // 多个读 goroutine
    for i := 0; i < 10; i++ {
        go func(id int) {
            for j := 0; j < 100; j++ {
                sm.Set(fmt.Sprintf("key-%d", j%5), j)
            }
        }(i)
    }
    
    // 一个写 goroutine
    go func() {
        for i := 0; i < 100; i++ {
            sm.Set("write", i)
        }
    }()
    
    time.Sleep(time.Second)
    
    // 读取结果
    for i := 0; i < 5; i++ {
        fmt.Printf("key-%d: %d\n", i, sm.Get(fmt.Sprintf("key-%d", i)))
    }
}
```

## sync.Cond 条件变量

### 适用场景

- 等待某个条件成立
- 线程等待/唤醒模式
- 生产者-消费者模型

### 基本用法

```go
package main

import (
    "fmt"
    "sync"
    "time"
)

type Queue struct {
    mu    sync.Mutex
    cond  *sync.Cond
    items []int
    max   int
}

func NewQueue(max int) *Queue {
    q := &Queue{
        items: make([]int, 0, max),
        max:   max,
    }
    q.cond = sync.NewCond(&q.mu)
    return q
}

func (q *Queue) Put(item int) {
    q.mu.Lock()
    defer q.mu.Unlock()
    
    // 队列满，等待
    for len(q.items) >= q.max {
        q.cond.Wait()  // 解锁并等待
    }
    
    q.items = append(q.items, item)
    fmt.Printf("Put: %d, Queue: %v\n", item, q.items)
    
    // 唤醒一个等待的消费者
    q.cond.Signal()
}

func (q *Queue) Get() int {
    q.mu.Lock()
    defer q.mu.Unlock()
    
    // 队列空，等待
    for len(q.items) == 0 {
        q.cond.Wait()
    }
    
    item := q.items[0]
    q.items = q.items[1:]
    fmt.Printf("Get: %d, Queue: %v\n", item, q.items)
    
    // 唤醒一个等待的生产者
    q.cond.Signal()
    
    return item
}

func main() {
    q := NewQueue(3)
    
    // 生产者
    go func() {
        for i := 0; i < 10; i++ {
            q.Put(i)
            time.Sleep(100 * time.Millisecond)
        }
    }()
    
    // 消费者
    go func() {
        for i := 0; i < 10; i++ {
            q.Get()
            time.Sleep(150 * time.Millisecond)
        }
    }()
    
    time.Sleep(3 * time.Second)
}
```

### Broadcast vs Signal

| 方法 | 说明 |
|:---|:---|
| `Signal()` | 唤醒一个等待的 goroutine |
| `Broadcast()` | 唤醒所有等待的 goroutine |

## sync.WaitGroup 等待组

### 基本用法

```go
package main

import (
    "fmt"
    "sync"
    "time"
)

func main() {
    var wg sync.WaitGroup
    
    // 添加 3 个任务
    wg.Add(3)
    
    for i := 0; i < 3; i++ {
        go func(id int) {
            defer wg.Done()  // 完成后计数减 1
            fmt.Printf("Task %d started\n", id)
            time.Sleep(time.Second)
            fmt.Printf("Task %d completed\n", id)
        }(i)
    }
    
    // 等待所有任务完成
    wg.Wait()
    fmt.Println("All tasks completed!")
}
```

### 常见模式

```go
// 1. 并行爬虫
func crawlUrls(urls []string) []string {
    var wg sync.WaitGroup
    results := make(chan string, len(urls))
    
    for _, url := range urls {
        wg.Add(1)
        go func(u string) {
            defer wg.Done()
            if body, err := fetch(u); err == nil {
                results <- body
            }
        }(url)
    }
    
    // 等待完成并关闭通道
    go func() {
        wg.Wait()
        close(results)
    }()
    
    var bodies []string
    for body := range results {
        bodies = append(bodies, body)
    }
    return bodies
}

// 2. 错误处理
type Task struct {
    ID   int
    URL  string
    Err  error
}

func processTasks(tasks []Task) []Task {
    var wg sync.WaitGroup
    for i := range tasks {
        wg.Add(1)
        go func(idx int) {
            defer wg.Done()
            tasks[idx].Err = process(tasks[idx].URL)
        }(i)
    }
    wg.Wait()
    return tasks
}
```

## sync.Once 一次性执行

### 基本用法

```go
package main

import (
    "fmt"
    "sync"
)

type Config struct {
    Data string
}

var (
    config *Config
    once   sync.Once
)

func getConfig() *Config {
    once.Do(func() {
        fmt.Println("Loading config...")
        config = &Config{
            Data: "loaded-once",
        }
    })
    return config
}

func main() {
    c1 := getConfig()
    c2 := getConfig()
    fmt.Println(c1 == c2, c1.Data) // true, 同一实例
}
```

### 注意事项

- `once.Do` 内的函数若 panic，仍视为「已执行」，再次调用不会重试；需要在内部自行 recover 或保证可恢复。
- 不要在 `once.Do` 里再嵌套依赖同一 `Once` 的死锁路径。
---
categories:
- 编程
date: 2026-05-04
description: AI 编码工具的 token 消耗大头不在 prompt，而在命令输出。RTK 是一个 Rust 写的 CLI 代理，在命令输出到达 AI 上下文之前做智能过滤，能省 60-90%。本文拆解它的核心原理和架构设计。
image: /images/article/2026-05-04/rtk-cover.svg
lastmod: 2026-05-04
tags:
- RTK
- AI编码
- Token优化
- 开发者工具
- Rust
title: RTK：让 AI 编码工具的 Token 账单打一折
---

# RTK：让 AI 编码工具的 Token 账单打一折

> 用 Cursor 写代码，一次深度交互能烧掉四五百万 tokens，平时也动辄几十万。直到我发现 token 消耗的大头不在 prompt，而在那些被 AI 吞进去的命令输出。

---

## 一、你的 token 到底花在了哪？

用 AI 编码工具（Claude Code / Cursor / Copilot）写代码，AI 会频繁执行 shell 命令：读文件、搜代码、跑测试、看 diff、查 git 状态。**每条命令的完整输出都会作为 token 塞进上下文窗口。**

一个典型的中等复杂度编码会话，token 消耗分布大概是这样：

| 操作 | 频率 | 典型 token 消耗 |
|------|------|----------------|
| `cat` / `read` 读文件 | 20+ 次 | 40,000+ |
| `grep` / `rg` 搜索代码 | 8+ 次 | 16,000+ |
| `git status` / `git diff` | 15+ 次 | 13,000+ |
| `go test` / `pytest` 跑测试 | 8+ 次 | 31,000+ |
| `ls` / `tree` 看目录 | 10+ 次 | 2,000+ |
| **单次会话粗估** | | **~100,000+** |

如果是深度调试或大项目，一次会话轻松突破**百万级**，最高可达**四五百万 tokens**。

问题在于：这些输出里，**80% 是对 AI 毫无价值的噪音**——通过的测试输出、git 的提示信息、空行、ANSI 颜色码、样板注释。你在为噪音买单。

---

## 二、RTK 是什么？

**RTK（Rust Token Killer）** 是一个高性能 CLI 代理，在命令输出到达 AI 上下文**之前**进行智能过滤压缩。

![RTK 架构总览](/images/article/2026-05-04/rtk-architecture.svg)

| 项目 | 信息 |
|------|------|
| GitHub | [rtk-ai/rtk](https://github.com/rtk-ai/rtk)（40k+ ⭐） |
| 语言 | Rust，单二进制文件，零依赖 |
| 代理开销 | < 10ms |
| 支持工具 | Claude Code、Copilot、Cursor、Gemini CLI、OpenClaw 等 12 种 |
| 官网 | https://www.rtk-ai.app |

官方宣称的效果：**60-90% 的 token 节省**。

---

## 三、核心原理：三层架构

作为工程师，我最关心的不是"能省多少"，而是"怎么做到的"。

RTK 的架构分三层，每一层解决一个独立问题：

```
┌──────────────────────────────────────────────────────────────┐
│  Layer 1: Hook 拦截层 — "让 AI 不知不觉用上 RTK"               │
│  ────────────────────────────────────────────                │
│  AI 执行 "git status"                                        │
│       ↓ PreToolUse Hook 自动重写                             │
│  实际执行 "rtk git status"                                    │
│  AI 完全无感知，只是收到更精简的输出                            │
├──────────────────────────────────────────────────────────────┤
│  Layer 2: 命令路由层 — "不同命令用不同策略"                     │
│  ────────────────────────────────────────────                │
│  main.rs → Clap 解析器 → 路由到对应处理器                      │
│  ├─ git/*  → Git 模块（结构化解析 porcelain 格式）             │
│  ├─ go/*   → Go 模块（解析 NDJSON 格式）                      │
│  ├─ rust/* → Cargo 模块                                       │
│  └─ 其他   → TOML 声明式过滤引擎（回退）                       │
├──────────────────────────────────────────────────────────────┤
│  Layer 3: 过滤引擎层 — "两套系统，各司其职"                     │
│  ────────────────────────────────────────────                │
│  System A: Rust 原生过滤器（复杂命令）                         │
│    → git diff, go test, cargo test 等需要结构化解析的命令      │
│  System B: TOML 声明式过滤器（简单命令）                       │
│    → du, ping, systemctl 等只需正则+截断的命令                 │
└──────────────────────────────────────────────────────────────┘
```

---

## 四、过滤引擎深度拆解

### 4.1 System A：Rust 原生过滤器（复杂命令）

用于 git、go test、cargo test 等**需要语义理解**的命令。核心思路：**用结构化解析代替文本处理**。

#### `go test` 的压缩（-90%）

RTK 强制给 `go test` 加上 `-json` 参数，输出 NDJSON 格式。然后逐行解析 JSON：

```rust
// 解析每一行 JSON 事件
match event.action.as_str() {
    "pass" => pkg_result.pass += 1,   // 通过 → 只计数，丢弃输出
    "fail" => {
        pkg_result.fail += 1;
        pkg_result.failed_tests.push((test, outputs));  // 失败 → 保留
    }
    "skip" => pkg_result.skip += 1,   // 跳过 → 只计数
    _ => {}
}
```

**压缩前**（6000 tokens）：
```
=== RUN   TestAdd
--- PASS: TestAdd (0.00s)
=== RUN   TestSubtract
--- PASS: TestSubtract (0.00s)
=== RUN   TestMultiply
--- FAIL: TestMultiply (0.00s)
    multiply_test.go:15: expected 6, got 5
=== RUN   TestDivide
--- PASS: TestDivide (0.00s)
... (重复 100+ 个测试)
```

**压缩后**（600 tokens）：
```
FAIL  github.com/user/project
  ✗ TestMultiply (0.00s)
    multiply_test.go:15: expected 6, got 5

3 passed, 1 failed, 0 skipped
```

关键洞察：**AI 不需要看通过的测试输出，它只需要知道"谁失败了"和"为什么失败"。**

#### `git diff` 的压缩（-75%）

核心函数 `compact_diff()` 做了四件事：

1. **按文件分组** — 只保留文件名，不保留 diff 头部的 `index`、`---`/`+++` 行
2. **统计 +/- 数量** — 每个文件末尾显示 `+5 -2`
3. **Hunk 截断** — 每个 hunk 最多显示 100 行变更
4. **上下文行裁剪** — 只在变更附近保留上下文，中间的跳过

```rust
// 核心循环
for line in diff.lines() {
    if line.starts_with("diff --git") {
        // 新文件：输出文件名，重置计数器
    } else if line.starts_with("@@") {
        // Hunk 头：保留（含函数名信息）
    } else if in_hunk {
        if line.starts_with('+') { added += 1; /* 保留 */ }
        else if line.starts_with('-') { removed += 1; /* 保留 */ }
        else if hunk_shown > 0 { /* 上下文行：只在有变更时保留 */ }
    }
}
```

#### `git status` 的压缩（-80%）

解析 `git status --porcelain` 输出，按状态码分类汇总：

```
* main...origin/main
+ Staged: 2 files
   src/main.rs
   src/utils.rs
~ Modified: 1 files
   src/lib.rs
? Untracked: 2 files
   docs/README.md
```

所有 git 提示信息（`use "git restore"...` 等）全部丢弃。

#### `git add` / `commit` / `push` 的暴力压缩（-92%）

```rust
// git add → 直接输出 "ok"
// git commit → 输出 "ok abc1234"
// git push → 输出 "ok main"
```

AI 不需要看 git 的 verbose 输出，只需要知道"成功了没"和关键标识。

### 4.2 System B：TOML 声明式过滤器（简单命令）

用于 du、ping、systemctl 等**只需正则+截断**的命令。零代码，纯配置。

```toml
# ping.toml — 只保留统计摘要，删除逐行响应
[filters.ping]
match_command = "^ping\\b"
strip_ansi = true
strip_lines_matching = [
  "^PING ",
  "^\\d+ bytes from ",     # 删除每行 ping 响应
  "^\\s*$",                # 删除空行
]
tail_lines = 4             # 只保留最后 4 行（统计摘要）
```

TOML 过滤器有 **8 阶段管道**，按顺序执行：

```
① strip_ansi        去除 ANSI 转义码（颜色等）
② replace           正则替换（逐行，可链式）
③ match_output      短路匹配：整个输出匹配某模式 → 直接返回固定消息
④ strip/keep_lines  按正则过滤行（二选一）
⑤ truncate_lines_at 每行截断到 N 字符
⑥ head/tail_lines   只保留前 N / 后 N 行
⑦ max_lines         绝对行数上限
⑧ on_empty          结果为空时的默认消息
```

添加新命令？只需要写一个 TOML 文件，不需要写一行 Rust。仓库里已经有 60+ 个内置过滤器。

### 4.3 故障安全：宁可多输出，不能丢信息

```rust
// 核心原则：如果过滤失败，回退到原始输出
if exit_code != 0 {
    // 保存完整原始输出到 ~/.local/share/rtk/tee/
    // 输出提示："[full output: /path/to/tee.log]"
}
```

这个设计很工程师——**fail-safe，不是 fail-open**。AI 永远不会因为 RTK 自身的 bug 而丢失关键信息。

---

## 五、安装与使用

### 5.1 安装

```bash
# macOS / Linux（推荐 Homebrew）
brew install rtk

# 或快速安装
curl -fsSL https://raw.githubusercontent.com/rtk-ai/rtk/refs/heads/master/install.sh | sh

# 验证
rtk --version
rtk gain     # 查看 token 节省统计
```

Windows 用户从 [GitHub Releases](https://github.com/rtk-ai/rtk/releases) 下载 `rtk-x86_64-pc-windows-msvc.zip`，解压后加入 PATH。

### 5.2 集成到 AI 工具

**Claude Code / Copilot**（最无缝）：
```bash
rtk init -g     # 安装 Hook，重启 Claude Code 即可
```

**Cursor**：
```bash
rtk init -g --agent cursor
# 修改 ~/.cursor/hooks.json，添加 preToolUse 钩子
# Cursor 自动加载
```

**OpenClaw**（插件方式）：
```bash
git clone https://github.com/rtk-ai/rtk.git && cd rtk
openclaw plugins install ./openclaw
openclaw gateway restart
```

**Gemini CLI**：
```bash
rtk init -g --gemini
```

**其他工具**（手动使用）：直接在命令前加 `rtk` 前缀即可。

### 5.3 常用命令速查

```bash
# 文件
rtk ls .                        # Token 优化的目录树
rtk read file.go                # 智能文件读取（-70%）
rtk grep "pattern" .            # 按文件分组的搜索结果
rtk find "*.go" .               # 紧凑的查找结果

# Git
rtk git status                  # 紧凑状态（-80%）
rtk git log -n 10               # 单行提交（-80%）
rtk git diff                    # 精简 diff（-75%）
rtk git push                    # → "ok main"（-92%）

# 测试
rtk go test                     # Go 测试（-90%，只显示失败）
rtk pytest                      # Python 测试（-90%）
rtk cargo test                  # Rust 测试（-90%）
rtk test <任意命令>              # 通用测试包装器

# 构建 & Lint
rtk cargo build                 # Cargo 构建（-80%）
rtk golangci-lint run           # Go lint（-85%）
rtk ruff check                  # Python lint（-80%）

# 容器 & 云
rtk docker ps                   # 紧凑容器列表（-80%）
rtk kubectl pods                # 紧凑 Pod 列表
```

### 5.4 配置

配置文件：`~/.config/rtk/config.toml`

```toml
[hooks]
exclude_commands = ["curl", "playwright"]  # 排除某些命令不重写

[tee]
enabled = true          # 失败时保存完整原始输出
mode = "failures"       # "failures" / "always" / "never"
```

还支持**项目级自定义过滤器**：在项目根目录创建 `.rtk/filters.toml`，可以覆盖或扩展内置规则。

---

## 六、为什么能省这么多？总结

| 策略 | 节省比例 | 原理 |
|------|---------|------|
| **删除噪音** | 30-40% | git 提示、空行、ANSI 颜色、样板文本 |
| **结构化解析** | 20-30% | JSON/NDJSON 解析，只提取关键字段 |
| **汇总代替明细** | 15-20% | "3 passed, 1 failed" 代替每个测试的完整输出 |
| **截断策略** | 10-20% | hunk 100 行上限、文件列表 20 个上限 |
| **短路匹配** | 5-10% | match_output：整个输出匹配"成功"→ 返回 "ok" |
| **上下文裁剪** | 10-15% | diff 中的上下文行只在变更附近保留 |

核心理念就一句话：**语义理解 + 选择性丢弃**。

它知道 AI 编码场景下哪些信息是噪音（通过的测试、git 提示、上下文行），哪些是关键（失败信息、文件名、行号），然后只保留关键部分。

---

## 七、Go 工程师的视角

RTK 是 Rust 写的。作为 Go 工程师，我第一反应是"为什么不用 Go？"

答案很直接：**性能**。每次命令执行都要过一遍代理，< 10ms 的开销要求极致的零成本抽象。Rust 的 `lazy_static!` 正则预编译、`include_str!` 编译时嵌入、无 GC 停顿，在这种场景下确实更合适。

但 RTK 的**架构设计**——Hook 拦截 → 命令路由 → 策略过滤 → 输出压缩——完全是语言无关的。它的 TOML 声明式过滤器设计特别优雅，添加新命令只需要写配置，不需要写代码。这套思路用 Go 完全可以复刻。

另外，RTK 的源码值得一读。作为一个 40k+ star 的 Rust 项目，它的代码组织、错误处理、测试策略都是很好的学习材料。

---

**参考链接：**
- RTK GitHub: https://github.com/rtk-ai/rtk
- RTK 官网: https://www.rtk-ai.app
- RTK 架构文档: https://github.com/rtk-ai/rtk/blob/master/ARCHITECTURE.md

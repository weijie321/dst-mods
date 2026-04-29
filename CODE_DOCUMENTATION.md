# DST Mod Crash Tracer — 代码文档

## 项目概述

本项目是一个 **Don't Starve Together (饥荒联机版) Mod 异常诊断工具**，用于捕获并归因 Lua 层 mod 异常。当玩家的 mod 出错时，它能告诉你：

- 最可疑的是哪个 mod
- 异常是在什么动作下触发的
- 目标对象和事件上下文是什么
- 应该先检查哪个文件

项目采用 **两部分交付模型**：

| 组件 | 语言 | 运行环境 | 职责 |
|------|------|----------|------|
| `dst-mod-crash-tracer` | Lua | DST 游戏内 | 运行时捕获异常，输出结构化日志 |
| `CrashTraceViewer.exe` / `view_crashtrace_report.py` | Python | Windows 桌面 | 读取日志，生成易读的诊断报告 |

---

## 目录结构

```
dst-mods/
├── dst-mod-crash-tracer/          # 核心诊断 mod（创意工坊发布物）
│   ├── modinfo.lua                # mod 元数据与配置项
│   ├── modmain.lua                # mod 入口，加载 bootstrap
│   └── scripts/crashtrace/
│       ├── bootstrap.lua          # 启动引导，初始化所有子模块
│       ├── config.lua             # 配置管理（语言、版本号）
│       ├── logger.lua             # 日志输出（格式化 CrashTrace 日志块）
│       ├── context.lua            # 调用上下文栈（追踪嵌套调用链）
│       ├── safe_call.lua          # 安全调用包装器（xpcall + 错误报告）
│       ├── wrappers.lua           # 环境 API 钩子（劫持 mod 注册函数）
│       ├── runtime_hooks.lua      # 运行时钩子（ListenForEvent/DoTaskInTime/DoPeriodicTask）
│       ├── report_builder.lua     # 报告构建器（结构化摘要行）
│       ├── i18n.lua               # 国际化（中英文术语翻译 + 触发摘要生成）
│       └── mod_identity.lua       # Mod 身份识别（从调用栈推断 mod_id）
│
├── dst-mod-crash-tracer-test/         # 测试 mod：玩家初始化异常
├── dst-mod-crash-tracer-event-test/   # 测试 mod：事件监听异常
├── dst-mod-crash-tracer-task-test/    # 测试 mod：延时任务异常
├── dst-mod-crash-tracer-periodic-test/# 测试 mod：周期任务异常
├── dst-mod-crash-tracer-grass-test/   # 测试 mod：采集动作异常
│
├── dst-inspect/                       # DST 原生脚本提取（开发参考）
│   ├── extract_dst_scripts.py         # 从 scripts.zip 提取指定脚本
│   └── scripts/                       # 提取出的 DST 原生脚本
│       ├── modutil.lua                # mod 工具函数（AddPlayerPostInit 等 API 定义）
│       ├── mods.lua                   # ModWrangler（mod 加载管理器）
│       ├── strict.lua                 # 全局变量严格模式
│       └── util.lua                   # 通用工具函数
│
├── view_crashtrace_report.py      # CrashTrace 报告查看器（Python 源码）
├── CrashTraceViewer.spec          # PyInstaller 打包配置
├── build_crashtrace_viewer.bat    # 打包脚本（生成 CrashTraceViewer.exe）
├── sync_dst_mods.bat              # 开发同步脚本（复制 mod 到游戏目录）
├── view_latest_crashtrace_report.bat   # 一键运行查看器（英文入口）
├── 查看最新CrashTrace报告.bat          # 一键运行查看器（中文入口）
├── 使用说明.txt                        # 面向普通用户的使用说明
├── CrashTrace_workshop_description.md  # 创意工坊发布文案
└── latest_crashtrace_report.txt        # 最近一次生成的报告
```

---

## 核心 Mod：`dst-mod-crash-tracer`

### 启动流程

```
modmain.lua
  └─ modimport("scripts/crashtrace/bootstrap.lua")
       ├─ Config.SetLanguage(...)        # 从 modinfo 读取语言配置
       ├─ Wrappers.Install()             # 劫持已加载 mod 的环境 API
       └─ RuntimeHooks.Install(...)      # 注册 AddPrefabPostInitAny 钩子
```

### 模块详解

#### 1. `config.lua` — 配置管理

存储版本号和语言设置，提供中英文文本查找。

- `Config.SetLanguage(value)` — 设置语言（`"zh"` / `"en"`）
- `Config.GetText(key)` — 获取当前语言下的文本
- `Config.GetVersion()` — 返回 `"0.2.0"`

#### 2. `context.lua` — 调用上下文栈

维护一个栈结构，用于追踪嵌套的异常捕获链路。当 `prefab_post_init_any` 在 `player_post_init` 内部触发时，可通过 `Context.HasParentAction()` 判断并跳过重复报告。

- `Context.Push(entry)` — 压入上下文
- `Context.Pop()` — 弹出上下文
- `Context.Peek()` — 查看栈顶
- `Context.Snapshot()` — 获取栈快照
- `Context.HasParentAction(action)` — 检查父级是否包含指定动作

#### 3. `safe_call.lua` — 安全调用包装器

核心的异常捕获机制。使用 `xpcall` 包装函数调用，捕获异常后构建报告并交给 Logger 输出。

```lua
SafeCall.Run(meta, fn, ...)
```

- 使用 `Context.Push/Pop` 管理调用栈
- 异常时通过 `debug.traceback` 获取完整调用栈
- 通过 `should_skip_nested_report` 避免重复报告（如 `prefab_post_init_any` 在 `player_post_init` 内部时）

#### 4. `wrappers.lua` — 环境 API 钩子

**Phase 1 钩子**：劫持每个 mod 环境中的注册 API，将用户回调包装为带异常捕获的版本。

被劫持的 API：

| API | hook_type | action |
|-----|-----------|--------|
| `AddPrefabPostInit` | `AddPrefabPostInit` | `prefab_post_init` |
| `AddPrefabPostInitAny` | `AddPrefabPostInitAny` | `prefab_post_init_any` |
| `AddPlayerPostInit` | `AddPlayerPostInit` | `player_post_init` |
| `AddComponentPostInit` | `AddComponentPostInit` | `component_post_init` |
| `AddGamePostInit` | `AddGamePostInit` | `game_post_init` |
| `AddSimPostInit` | `AddSimPostInit` | `sim_post_init` |

工作原理：

1. 遍历 `ModManager.mods` 中所有已加载的 mod 环境
2. 跳过自身（`dst-mod-crash-tracer`）
3. 对每个环境，使用 `rawget/rawset` 替换上述 API
4. 替换后的 API 会识别回调函数，用 `wrap_callback` 包装
5. 包装后的回调在执行时通过 `SafeCall.Run` 运行，异常时自动报告

`build_env_identity(env)` 函数从 mod 环境中提取 `mod_id`、`mod_name`、`source` 等身份信息。

#### 5. `runtime_hooks.lua` — 运行时钩子

**Phase 2 钩子**：通过 `AddPrefabPostInitAny` 注册回调，在每个实体实例上安装运行时方法钩子。

被钩住的实例方法：

| 方法 | hook_type | action |
|------|-----------|--------|
| `inst:ListenForEvent(event, fn)` | `ListenForEvent` | `event_listener` |
| `inst:DoTaskInTime(delay, fn)` | `DoTaskInTime` | `task_in_time` |
| `inst:DoPeriodicTask(interval, fn)` | `DoPeriodicTask` | `periodic_task` |

关键设计：

- 使用 `ModIdentity.CaptureCallerIdentity()` 从调用栈推断是哪个 mod 注册的回调
- 通过 `debug.getinfo(level, "S")` 遍历调用栈（level 3~10），匹配 `/mods/<mod_id>/` 路径
- 只对非自身 mod 的回调进行包装（`should_instrument` 检查）
- 使用 `_crashtrace_listen_wrapped` 等标志避免重复包装

#### 6. `mod_identity.lua` — Mod 身份识别

通过分析调用栈中的文件路径来推断调用者属于哪个 mod：

```lua
ModIdentity.CaptureCallerIdentity()
-- 遍历 debug.getinfo(level, "S")，匹配 ../mods/<mod_id>/ 模式
-- 返回 { mod_id, mod_name, source }
```

#### 7. `logger.lua` — 日志输出

将结构化报告输出为 DST 日志中的格式化文本块：

```
[CrashTrace][ERROR] report_begin
[CrashTrace][ERROR] 捕获到 Lua mod 异常
[CrashTrace][ERROR] title=检测到 mod 异常
[CrashTrace][ERROR] mod_id=some_mod
[CrashTrace][ERROR] hook_type=ListenForEvent
...
[CrashTrace][ERROR] traceback_begin
[CrashTrace][TRACE] ../mods/some_mod/modmain.lua(10,1) in function ...
[CrashTrace][ERROR] traceback_end
[CrashTrace][ERROR] report_end
```

#### 8. `report_builder.lua` — 报告构建器

将报告表转换为 `key=value` 格式的摘要行数组。包含：

- 标题、语言、版本
- mod_id、mod_name
- hook_type、action、event
- target、prefab、guid
- 触发摘要（trigger_summary）
- 错误原因、来源文件

#### 9. `i18n.lua` — 国际化

提供中英文术语映射，覆盖：

- **hook 类型**：`AddPlayerPostInit` → "玩家初始化回调" / "player post init hook"
- **动作类型**：`event_listener` → "事件监听触发" / "event listener fired"
- **事件名称**：`picked` → "采集" / "picked"
- **Prefab 名称**：`grass` → "草" / "grass"
- **触发摘要模板**：`"玩家%s采集%s时触发"` / `"player %s triggered this by picking %s"`

`BuildTriggerSummary(report)` 根据 action/event/target/actor 生成人类可读的触发描述。

---

## Python 查看器：`view_crashtrace_report.py`

### 功能

读取 DST 本机日志目录下的 `client_log.txt`、`backup/client_log/*.txt`、`server_log.txt`，提取 CrashTrace 报告块，生成结构化的诊断报告。

### 工作流程

```
1. 解析命令行参数（--root, --output, --open-output）
2. 收集日志文件（按修改时间倒序）
3. 对每个日志文件：
   a. extract_reports()      — 提取 CrashTrace 结构化报告
   b. extract_native_reports() — 提取 DST 原生日志中的 mod 异常
4. 取最新一条报告，生成格式化文本
5. 写入输出文件，可选自动打开
```

### 报告解析

**结构化报告解析**（`extract_reports`）：
- 识别 `report_begin` / `report_end` 标记
- 提取 `key=value` 格式的摘要行
- 提取 `traceback_begin` / `traceback_end` 之间的调用栈

**原生日志解析**（`extract_native_reports`）：
- 识别 `"error calling ... in mod ..."` 模式
- 识别 `"../mods/"` 路径中的 `attempt to` 错误
- 从上下文中提取 event、target、picker 等信息
- 根据 traceback 中出现的组件文件推断动作类型（如 `pickable.lua` → 采集动作）

### 报告输出格式

```
=== CrashTrace 最近一次诊断 ===

结论:
最可疑 mod: <mod_name>
触发位置: 客户端 / 前端/客户端
捕获方式: CrashTrace 结构化捕获
触发动作: 事件监听触发
优先检查: ../mods/<mod>/modmain.lua:10
核心原因: attempt to index a nil value

摘要:
标题: 检测到 mod 异常
Mod ID: <mod_id>
Hook 类型: 事件监听
触发动作: 事件监听触发
触发摘要: 玩家 威尔逊 采集 草 时触发
错误原因: ...

修复建议:
先打开并检查: ../mods/<mod>/modmain.lua:10
...

调用栈:
...
```

### 本地化映射

查看器内含完整的中文术语映射表：

| 类别 | 示例 |
|------|------|
| Hook 类型 | `ListenForEvent` → "事件监听" |
| 动作类型 | `pick_action` → "采集动作" |
| 事件名称 | `picked` → "采集" |
| Prefab 名称 | `grass` → "草", `wilson` → "威尔逊" |

---

## 测试 Mod

五个测试 mod 分别验证不同场景的异常捕获能力：

| Mod | 场景 | 触发方式 |
|-----|------|----------|
| `dst-mod-crash-tracer-test` | 玩家初始化回调 | `AddPlayerPostInit` + `DoTaskInTime(0.9s)` 访问不存在的字段 |
| `dst-mod-crash-tracer-event-test` | 事件监听 | `ListenForEvent("crashtrace_test_event")` + 1.3s 后 `PushEvent` |
| `dst-mod-crash-tracer-task-test` | 延时任务 | `DoTaskInTime(0.2s)` 访问不存在的字段 |
| `dst-mod-crash-tracer-periodic-test` | 周期任务 | `DoPeriodicTask(0.3s)` 访问不存在的字段 |
| `dst-mod-crash-tracer-grass-test` | 采集动作 | `ListenForEvent("picked")` 在草/树枝苗/芦苇/浆果丛上触发 |

所有测试 mod 的模式相同：访问一个不存在的字段（如 `player.not_exists.prefab`）来触发 `attempt to index a nil value` 错误。

---

## 工具脚本

### `sync_dst_mods.bat`

将开发目录中的所有 mod 同步到 DST 游戏的 `mods` 目录。使用 `robocopy` 进行增量复制。

```
源: E:\work\code\ai-generated\dst-mods\<mod-name>
目标: S:\game\steam\steamapps\common\Don't Starve Together\mods\<mod-name>
```

### `build_crashtrace_viewer.bat`

使用 PyInstaller 将 `view_crashtrace_report.py` 打包为独立的 `CrashTraceViewer.exe`。自动检测并安装 PyInstaller。

### `view_latest_crashtrace_report.bat` / `查看最新CrashTrace报告.bat`

一键运行 Python 查看器，生成并打开 `latest_crashtrace_report.txt`。优先使用 `py -3`，回退到 `python`。

### `dst-inspect/extract_dst_scripts.py`

从 DST 安装目录的 `scripts.zip` 中提取指定的原生脚本文件，用于开发时参考 DST 的 mod 加载机制。

---

## 技术细节

### 异常捕获链路

```
1. mod 调用 AddPlayerPostInit(fn)
   └─ Wrappers 劫持 → 包装 fn 为 wrapped_fn
       └─ wrapped_fn 内部调用 SafeCall.Run(meta, fn, inst)
           └─ xpcall(fn, error_handler)
               ├─ 成功: 正常返回
               └─ 失败: 构建 report → Logger.Report(report)

2. mod 调用 inst:ListenForEvent(event, fn)
   └─ RuntimeHooks 劫持 → 包装 fn 为 wrapped_fn
       └─ wrapped_fn 内部调用 SafeCall.Run(meta, fn, inst, data)
           └─ 同上
```

### Mod 身份推断

```lua
-- 从调用栈中提取 mod_id
debug.getinfo(level, "S").source
-- 例如: "../mods/my_mod/scripts/main.lua"
-- 正则匹配: /mods/([^/]+)/ → "my_mod"
```

### 防重复报告

当 `player_post_init`（通过 `AddPrefabPostInitAny` 实现）内部触发 `prefab_post_init_any` 时，`should_skip_nested_report` 会检查上下文栈中是否已有 `player_post_init`，避免同一异常被报告两次。

### 优先级

`dst-mod-crash-tracer` 的 `priority = 1000000`（极高），确保它在所有其他 mod 之前加载，从而能劫持后续 mod 的 API 注册。

---

## 已验证的捕获能力

| 链路 | 状态 |
|------|------|
| `AddPlayerPostInit` | 已验证 |
| `ListenForEvent` | 已验证 |
| `DoTaskInTime` | 已验证 |
| `DoPeriodicTask` | 已验证 |
| `AddPrefabPostInit` | 已实现 |
| `AddComponentPostInit` | 已实现 |
| `AddGamePostInit` | 已实现 |
| `AddSimPostInit` | 已实现 |
| DST 原生日志回退解析 | 已实现 |

## 已知边界

- 主要覆盖 Lua 层 mod 异常，不保证捕获引擎层或进程级闪退
- 某些 very early frontend 阶段可能回退到 DST 原生日志
- 查看器默认只展示最近一条报告
- 创意工坊不适合直接分发 exe，查看器需通过外部下载提供

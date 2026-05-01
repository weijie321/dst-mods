# DST Mods Workspace

这个目录用于存放本地开发和发布 `Don't Starve Together` mod 及其配套工具。

当前包含：

- `dst-mod-crash-tracer/`：Lua 层 mod 异常诊断 mod
- `dst-mod-crash-tracer-test/`：用于验证诊断能力的故意抛错测试 mod
- `dst-mod-crash-tracer-event-test/`：事件监听异常测试 mod
- `dst-mod-crash-tracer-task-test/`：延时任务异常测试 mod
- `dst-mod-crash-tracer-periodic-test/`：周期任务异常测试 mod
- `dst-mod-crash-tracer-grass-test/`：采集动作异常测试 mod（草、树枝苗、芦苇、浆果丛）
- `tools/`：开发工具（同步脚本、查看器源码和打包产物）
  - `sync_dst_mods.bat`：同步开发 mod 到游戏 `mods` 目录
  - `crashtrace-viewer/`：查看器源码、打包配置、启动脚本、exe 产物
- `latest_crashtrace_report.txt`：查看器最近一次生成的报告
- `使用说明.txt`：给普通用户的使用说明
- `CrashTrace_workshop_description.md`：创意工坊发布文案草稿

## 交付模型

CrashTrace 现在按两部分交付：

- `dst-mod-crash-tracer`：放在创意工坊，负责运行时捕获和输出结构化日志
- `CrashTraceViewer.exe`：独立 Windows 工具，负责读取本机 DST 日志并生成易读报告

职责边界：

- 诊断 mod 不负责提供 Python 运行环境，也不负责启动桌面工具
- 查看器不参与游戏运行时逻辑，只消费已经写入本机日志的内容

## 本地开发使用方式

1. 双击或执行 `tools/sync_dst_mods.bat`
2. 打开游戏并启用：
   - `DST Mod Crash Tracer`
   - `DST Mod Crash Tracer Test`
   - `DST Mod Crash Tracer Event Test`
   - `DST Mod Crash Tracer Task Test`
   - `DST Mod Crash Tracer Periodic Test`
   - `Crash Tracer Pick Test / 采集动作异常测试`
3. 确保诊断 mod 先于测试 mod 加载
4. 进入世界，等待或主动触发测试异常
5. 运行 `tools/crashtrace-viewer/查看最新CrashTrace报告.bat`
6. 查看器会自动生成并打开 `latest_crashtrace_report.txt`

## 面向创意工坊用户的使用方式

1. 订阅并启用 `dst-mod-crash-tracer`
2. 正常进入游戏并触发一次 mod 异常
3. 退出游戏或切回桌面
4. 双击 `CrashTraceViewer.exe`
5. 查看自动生成的 `latest_crashtrace_report.txt`

说明：

- 查看器当前只支持 Windows
- 查看器不需要 Python
- 默认读取 `Documents\\Klei\\DoNotStarveTogether`
- 如果没有结构化报告，会自动回退解析 DST 原生日志
- 创意工坊页面应提供查看器的外部下载地址

## 当前验证目标

验证日志中是否至少包含：

- 触发的 mod
- hook 类型
- action
- target
- traceback

## 当前已验证能力

当前已经验证成功的结构化捕获链路：

- `AddPlayerPostInit`
- `ListenForEvent`
- `DoTaskInTime`
- `DoPeriodicTask`

当前报告已能输出：

- 具体 mod
- hook 类型
- 触发动作
- 目标对象或 prefab
- 疑似出错文件
- traceback

## 已知边界

当前版本仍然有这些边界：

- 主要覆盖 Lua 层 mod 异常，不保证捕获引擎层或进程级闪退
- 某些 very early frontend 阶段或特殊加载阶段，可能还会回退到 DST 原生日志
- 若多个测试 mod 同时启用，较早触发的异常可能会打断后续测试链路
- 查看器默认展示最近一条可用报告；若没有结构化报告，则回退解析 DST 原生日志
- 创意工坊本身不适合直接分发 exe，查看器需要通过外部下载地址提供

## 打包查看器

如果你要重新生成 Windows 查看器：

1. 确认当前机器可用 `pyinstaller`
2. 运行 `tools/crashtrace-viewer/build_crashtrace_viewer.bat`
3. 产物位于 `tools/crashtrace-viewer/dist/CrashTraceViewer.exe`

## 小白查看方式

优先使用：

- `tools/crashtrace-viewer/dist/CrashTraceViewer.exe`
- `tools/crashtrace-viewer/查看最新CrashTrace报告.bat`

它会自动读取 `Documents\\Klei\\DoNotStarveTogether` 下的日志，并提取最近一次 `CrashTrace` 报告块。
如果当前日志已被 DST 轮转，它也会自动扫描 `backup/client_log` 里的最近一次客户端报错。
报告会尽量直接给出最可疑 mod、疑似出错文件以及修复建议。

## 建议发布物

如果你要对外发布，建议至少准备：

- 创意工坊 mod：`dst-mod-crash-tracer`
- 独立查看器：`tools/crashtrace-viewer/dist/CrashTraceViewer.exe`
- 玩家说明：`使用说明.txt`
- 创意工坊介绍文案：`CrashTrace_workshop_description.md`

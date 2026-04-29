# DST Mod Crash Tracer

用于捕获并归因 Lua 层 mod 异常的诊断工具。

它会尽量告诉你：

- 最可疑的是哪个 mod
- 异常是在什么动作下触发的
- 目标对象和事件上下文是什么
- 应该先检查哪个文件

适合玩家、服主和 mod 作者快速缩小排查范围。

## 能力说明

- 捕获常见 Lua 层 mod 异常
- 尽量归因到具体 mod
- 输出结构化 CrashTrace 日志
- 支持事件监听、延时任务、周期任务、初始化回调等常见场景

## 查看报告

本创意工坊 mod 负责记录日志。
如果想看更容易理解的诊断结果，请配合独立 Windows 查看器使用：

- `CrashTraceViewer.exe`

查看器特点：

- 一键运行
- 不需要 Python
- 自动读取 `Documents\\Klei\\DoNotStarveTogether` 下的日志
- 自动生成 `latest_crashtrace_report.txt`

推荐流程：

1. 订阅并启用 `DST Mod Crash Tracer`
2. 在游戏中触发一次 mod 异常
3. 退出游戏或切回桌面
4. 运行 `CrashTraceViewer.exe`
5. 查看自动生成的诊断报告

## 边界说明

- 不保证捕获引擎层或 C 层崩溃
- 不保证覆盖所有 very early frontend 场景
- 非常早期的闪退可能只能回退解析 DST 原生日志

反馈问题时，建议附带：

- `latest_crashtrace_report.txt`
- 复现步骤
- 当前启用的 mod 列表

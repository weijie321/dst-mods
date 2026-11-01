# DST Mods Workspace

这个目录用于存放本地开发和发布 `Don't Starve Together` mod 及其配套工具。

当前包含：

- `wanda-skilltree/`：旺达技能树、怀表机制与时光贮匣，状态见其 `DEVELOPMENT_STATUS.md`
- `dst-mod-crash-tracer/`：Lua 层 mod 异常诊断 mod
- `dst-mod-crash-tracer-test/`：用于验证诊断能力的故意抛错测试 mod
- `dst-mod-crash-tracer-event-test/`：事件监听异常测试 mod
- `dst-mod-crash-tracer-task-test/`：延时任务异常测试 mod
- `dst-mod-crash-tracer-periodic-test/`：周期任务异常测试 mod
- `dst-mod-crash-tracer-grass-test/`：采集动作异常测试 mod（草、树枝苗、芦苇、浆果丛）
- `tools/`：开发工具（验收、部署、查看器源码和打包产物）
  - `dst.ps1`：统一的 `doctor/check/test/verify/deploy` 入口
  - `sync_dst_mods.bat`：兼容部署入口，无参数只预览旺达模组
  - `crashtrace-viewer/`：查看器源码、打包配置、启动脚本、exe 产物
- `latest_crashtrace_report.txt`：查看器生成的当前报告文件
- `使用说明.txt`：给普通用户的使用说明
- `CrashTrace_workshop_description.md`：创意工坊发布文案草稿

相关分析工作区：

- `..\dst-original-analysis\` 和 `dst-inspect/`：历史原版解压副本、索引报告和模组可读性记录，可用于查找线索。当前 Hook、Prefab、组件、状态机和资源契约必须回到配置安装目录的 `data/databundles/scripts.zip` 核对。

## 模组开发与验收

在仓库根目录运行下列入口；环境恢复、计划格式、场景协议和部署回滚详见 [tools/DST_TESTING.md](tools/DST_TESTING.md)。

```powershell
& ./tools/dst.ps1 doctor
& ./tools/dst.ps1 check --mod wanda-skilltree
& ./tools/dst.ps1 test --mod wanda-skilltree
& ./tools/dst.ps1 verify --mod wanda-skilltree
& ./tools/dst.ps1 deploy --mod wanda-skilltree
& ./tools/dst.ps1 deploy --mod wanda-skilltree --apply --verified '<成功verify的result.json完整路径>'
```

每个新需求先写对应的验收要求和具名断言，再循环实现、测试、修复。`verify` 默认使用 `tools/acceptance/<模组名>.json`；既有基线只覆盖计划声明的范围，不能证明新功能完成。报告和日志写入本机配置的项目外 `evidence_root`，实际部署只接受输入版本仍匹配的成功 `verify` 报告。

本轮旺达 `verify` 已通过：静态检查 83 个直接调用、0 个待查调用，服务端 34 条断言及真实客户端 7 条基础断言全部通过，清理通过。这只覆盖核心服务端与客户端 HUD/Replica 基线，未覆盖技能点击、重连重生、像素/声音等，也不代表全部技能完成。报告及详细边界见 [旺达开发状态](wanda-skilltree/DEVELOPMENT_STATUS.md)。

## 交付模型

CrashTrace 现在按两部分交付：

- `dst-mod-crash-tracer`：放在创意工坊，负责运行时捕获和输出结构化日志
- `CrashTraceViewer.exe`：独立 Windows 工具，负责读取本机 DST 日志并生成易读报告

职责边界：

- 诊断 mod 不负责提供 Python 运行环境，也不负责启动桌面工具
- 查看器不参与游戏运行时逻辑，只消费已经写入本机日志的内容

## CrashTrace 专项诊断手工回归

1. 按上述统一入口为待测模组准备相应验收计划、验证并部署；旺达计划不覆盖 CrashTrace。
2. 打开游戏，启用 `DST Mod Crash Tracer`，每次只选择一个故意抛错测试 mod：`DST Mod Crash Tracer Test`、`DST Mod Crash Tracer Event Test`、`DST Mod Crash Tracer Task Test`、`DST Mod Crash Tracer Periodic Test` 或 `Crash Tracer Pick Test / 采集动作异常测试`。
3. 确保诊断 mod 先于测试 mod 加载；不要让前一个异常中断其它测试链路。
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
- 查看器按日志修改时间选择第一条可用报告；若没有结构化报告，则回退解析 DST 原生日志
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

它会自动读取 `Documents\\Klei\\DoNotStarveTogether` 下的日志，并提取按日志修改时间排序后的第一条 `CrashTrace` 报告块。
如果当前日志已被 DST 轮转，它也会自动扫描 `backup/client_log` 中按修改时间排序的客户端报错。
报告会尽量直接给出最可疑 mod、疑似出错文件以及修复建议。

## 建议发布物

如果你要对外发布，建议至少准备：

- 创意工坊 mod：`dst-mod-crash-tracer`
- 独立查看器：`tools/crashtrace-viewer/dist/CrashTraceViewer.exe`
- 玩家说明：`使用说明.txt`
- 创意工坊介绍文案：`CrashTrace_workshop_description.md`

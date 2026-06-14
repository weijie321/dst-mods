# DST Mod Crash Tracer

DST (Don't Starve Together) Lua 层 mod 异常诊断工具项目。

## 项目结构

- `dst-mod-crash-tracer/` — 核心诊断 mod（Lua，创意工坊发布物）
- `dst-mod-crash-tracer-test/` — 测试 mod（玩家初始化异常）
- `dst-mod-crash-tracer-event-test/` — 测试 mod（事件监听异常）
- `dst-mod-crash-tracer-task-test/` — 测试 mod（延时任务异常）
- `dst-mod-crash-tracer-periodic-test/` — 测试 mod（周期任务异常）
- `dst-mod-crash-tracer-grass-test/` — 测试 mod（采集动作异常）
- `tools/crashtrace-viewer/` — 查看器相关（源码、打包配置、启动脚本）
- `tools/sync_dst_mods.bat` — 同步 mod 到 DST 游戏目录
- `dst-inspect/` — DST 原生脚本提取（开发参考）
- `wanda-skilltree/` — 旺达技能树扩展 mod（五栏技能树 + 怀表 Hook + 时光贮匣）

## 相关工作区

- `E:\work\code\dst-original-analysis\` — DST 原版代码和创意工坊模组分析工作区。这里存放从 `scripts.zip` 解压出的完整只读副本、`reports/*.csv` 索引、模组 ID 映射和混淆/可读性记录。
- `dst-inspect/` 只保留少量关键原版脚本提取结果；需要完整原版源码索引时不要继续扩展它，优先使用 `dst-original-analysis`。

## 关键技术点

- Mod 入口: `dst-mod-crash-tracer/modmain.lua` → `scripts/crashtrace/bootstrap.lua`
- 核心模块: `runtime_hooks.lua`（实例方法钩子）、`safe_call.lua`（xpcall 包装）
- 捕获范围: ListenForEvent、DoTaskInTime、DoPeriodicTask（通过 AddPrefabPostInitAny 注册）
- 语言配置: `modinfo.lua` 中 `language` 选项，`config.lua` 管理中英文文本

## 开发工作流

1. `tools/sync_dst_mods.bat` — 同步 mod 到 DST 游戏目录（robocopy）
2. `tools/crashtrace-viewer/build_crashtrace_viewer.bat` — 打包 Python 查看器为 exe
3. `tools/crashtrace-viewer/查看最新CrashTrace报告.bat` — 运行查看器

## 日志路径

- 客户端: `Documents\Klei\DoNotStarveTogether\client_log.txt`
- 客户端备份: `Documents\Klei\DoNotStarveTogether\backup\client_log\client_log_*.txt`
- 独立服务器: `Documents\Klei\DoNotStarveTogether\MyDediServer\{Master,Caves}\server_log.txt`

## 打包规范

- Python 查看器用 PyInstaller 打包，spec 文件: `tools/crashtrace-viewer/CrashTraceViewer.spec`
- 产物: `tools/crashtrace-viewer/dist/CrashTraceViewer.exe`
- 依赖: 无第三方 Python 依赖，仅标准库

## Git 配置

- 远程仓库: `git@github.com:weijie321/dst-mods.git`（SSH 认证）
- 主分支: `main`（2026-04-29 从 master 重命名）

## 注意事项

- `dst-inspect/scripts/` 下的 Lua 文件是从 DST 的 `scripts.zip` 提取的原生脚本，仅作开发参考，不要修改
- 测试 mod 的命名以 `dst-mod-crash-tracer-*-test` 为模式
- 查看器的本地化映射（HOOK_LABELS、PREFAB_LABELS 等）在 Python 和 Lua 两侧都有维护，修改时需同步

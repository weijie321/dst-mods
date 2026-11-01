# DST 模组工作区

DST (Don't Starve Together) 本地模组与配套工具项目。先读取根 [AGENTS.md](AGENTS.md) 和目标模组的专用指令；开发验收详见 [tools/DST_TESTING.md](tools/DST_TESTING.md)。

## 项目结构

- `dst-mod-crash-tracer/` — 核心诊断 mod（Lua，创意工坊发布物）
- `dst-mod-crash-tracer-test/` — 测试 mod（玩家初始化异常）
- `dst-mod-crash-tracer-event-test/` — 测试 mod（事件监听异常）
- `dst-mod-crash-tracer-task-test/` — 测试 mod（延时任务异常）
- `dst-mod-crash-tracer-periodic-test/` — 测试 mod（周期任务异常）
- `dst-mod-crash-tracer-grass-test/` — 测试 mod（采集动作异常）
- `tools/crashtrace-viewer/` — 查看器相关（源码、打包配置、启动脚本）
- `tools/dst.ps1` — 环境检查、静态检查、隔离专服测试、完整验收和部署
- `tools/sync_dst_mods.bat` — 兼容部署入口，无参数只预览旺达模组
- `dst-inspect/` — DST 原生脚本历史提取（只读线索）
- `wanda-skilltree/` — 旺达技能树扩展 mod（五栏技能树 + 怀表 Hook + 时光贮匣）

## 相关工作区

- `../dst-original-analysis/` — 历史原版代码和创意工坊模组分析工作区，保留解压副本、`reports/*.csv` 索引、模组 ID 映射和混淆/可读性记录。
- `dst-inspect/` 保留少量历史原版脚本。两者可用于查找线索，不作为当前 API 的优先事实源；当前定义与资源以本机配置安装目录内的 `data/databundles/scripts.zip` 为准。

## 关键技术点

- Mod 入口: `dst-mod-crash-tracer/modmain.lua` → `scripts/crashtrace/bootstrap.lua`
- 核心模块: `runtime_hooks.lua`（实例方法钩子）、`safe_call.lua`（xpcall 包装）
- 捕获范围: ListenForEvent、DoTaskInTime、DoPeriodicTask（通过 AddPrefabPostInitAny 注册）
- 语言配置: `modinfo.lua` 中 `language` 选项，`config.lua` 管理中英文文本

## 开发工作流

1. `tools/dst.ps1 doctor` — 检查本机配置与已审查工具版本。
2. 为本次需求确定验收项，按 `check → test → verify` 循环实现、测试和修复；基线通过不代表新增功能完成。
3. `tools/dst.ps1 deploy --mod <模组名>` 预览；实际部署须增加 `--apply --verified <成功verify的result.json>`，输入发生变化后重新验收。
4. `tools/crashtrace-viewer/build_crashtrace_viewer.bat` — 打包 Python 查看器为 exe。
5. `tools/crashtrace-viewer/查看最新CrashTrace报告.bat` — 运行查看器。

本机路径来自 `~/.ai/local/config/dst-mod-development/config.json`；测试报告写入项目外 `evidence_root`。客户端 HUD、交互与网络同步需要真实客户端证据，不能用专服通过代替。旧入口参数映射和清理规则统一见 `tools/DST_TESTING.md`。

旺达核心服务端与真实客户端 HUD/Replica 基线已通过 `verify`；当前证据和未覆盖项见 `wanda-skilltree/DEVELOPMENT_STATUS.md` 第 6 节，不能据此宣称全部技能或完整客户端玩法通过。

## 日志路径

- 客户端: `Documents\Klei\DoNotStarveTogether\client_log.txt`
- 客户端备份: `Documents\Klei\DoNotStarveTogether\backup\client_log\client_log_*.txt`
- 独立服务器: `Documents\Klei\DoNotStarveTogether\MyDediServer\{Master,Caves}\server_log.txt`

## 打包规范

- Python 查看器用 PyInstaller 打包，spec 文件: `tools/crashtrace-viewer/CrashTraceViewer.spec`
- 产物: `tools/crashtrace-viewer/dist/CrashTraceViewer.exe`
- 依赖: 无第三方 Python 依赖，仅标准库

## Git 配置

- 远程仓库: `https://github.com/weijie321/dst-mods.git`（HTTPS；本机使用 GitHub CLI 凭据）
- 主分支: `main`（2026-04-29 从 master 重命名）

## 注意事项

- `dst-inspect/scripts/` 下的 Lua 文件是从 DST 的 `scripts.zip` 提取的原生脚本，仅作开发参考，不要修改
- 根目录原 Agent 历史上下文保存在 `docs/history/agent-context-20260601.md`，按需追溯，不作为当前验证结论。
- 测试 mod 的命名以 `dst-mod-crash-tracer-*-test` 为模式
- 查看器的本地化映射（HOOK_LABELS、PREFAB_LABELS 等）在 Python 和 Lua 两侧都有维护，修改时需同步

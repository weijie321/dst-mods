# DST 模组开发与验收

从需求出发，先确定可观察结果与断言，再循环实现、测试和修复。每次新需求都必须有对应验收项；已有核心基线通过不能证明新增功能完成。本文是项目测试、证据与本地部署的统一说明。

## 入口与环境

在仓库根目录运行 `tools/dst.ps1`。它读取 `~/.ai/local/config/dst-mod-development/config.json`，使用其中指定的 Python；也可通过 `--config <文件>` 指定本机配置。配置字段为 `workspace`、`dst_root`、`upstream_root`、`python`、`evidence_root`、`expected_upstream_commit`，真实机器路径不放进共享代码。

```powershell
& ./tools/dst.ps1 doctor
```

`doctor` 检查 Python、固定版本的 `luaparser`、当前游戏 `scripts.zip`、专服、客户端和模组目录；同时校验已审查的上游提交及工作区状态。环境缺失时按 `~/.ai/tools/docs/notes/dst-mod-workflow.md` 恢复，安装脚本是 `~/.ai/tools/scripts/setup-dst-mod-workflow.ps1`，可先传 `-CheckOnly`。核心依赖见 `tools/requirements-dst-test.txt`；可选图像/UI 工具依赖单列在 `tools/ui-tests/requirements.txt`，不作为普通服务端测试的前提。

API、组件、状态机和资源以配置中当前游戏安装目录的 `data/databundles/scripts.zip` 为准。`../dst-original-analysis/` 和 `dst-inspect/` 的历史解压副本只提供查找线索；不要依赖旧快照判断当前 API，也不要修改原版或第三方上游镜像。

## 命令与结果

| 命令 | 用途与边界 |
| --- | --- |
| `doctor` | 检查环境与工具版本，不证明模组行为正确 |
| `check --mod wanda-skilltree` | Lua 语法、直接组件声明和静态资源检查；必要时用 `--plan <文件>` 加载已查证的 API 说明 |
| `test --mod wanda-skilltree` | 隔离专服执行具名断言；默认取 `tools/acceptance/<模组名>.json` 的 `server_script`，可用 `--script <文件>` 指定场景 |
| `verify --mod wanda-skilltree` | 默认读取 `tools/acceptance/<模组名>.json`，执行静态检查和计划要求的服务端/客户端阶段，核对每条需求的断言 ID |
| `verify --mod wanda-skilltree --plan <文件>` | 使用本次需求的专属验收计划 |
| `deploy --mod wanda-skilltree` | 预览运行文件的新增、更新、删除和不变项，不写目标目录 |
| `deploy --mod wanda-skilltree --apply --verified <result.json>` | 凭明确指定且仍有效的成功 `verify` 报告实际部署 |

`test`、`verify` 支持 `--timeout <秒>`，默认 240 秒。独立 `test` 只证明本次执行的断言；需求覆盖完整性由 `verify` 根据计划核对。`verify` 只在计划要求客户端验收时执行客户端阶段，名称本身不代表所有玩法均已测试。

验收状态必须如实保留：

- `passed`：计划限定范围内的检查及断言通过。
- `failed`：断言、运行、清理失败，或执行期间输入发生变化。
- `review_required`：静态声明或资源等仍需查证，不能按通过处理。
- `blocked`：环境、证据或运行条件不足，不能按跳过成功处理。

`passed` 和部署的 `preview/applied/unchanged` 返回 0；`failed` 返回 1；其它状态返回 2。部署预览成功不等于验收通过。

## 把需求写成验收计划

先记录触发动作、预期状态、执行端，以及本次变更涉及的失败/恢复路径。需求 ID 和断言 ID 只使用字母、数字、下划线、点、短横线；需求 ID 唯一。`requirements` 非空，每项必须有 `description`、`stage`（`server` 或 `client`）及非空 `assertions`。

以下是协议示例，不能替代具体新功能的验收：

```json
{
  "schema_version": 1,
  "mod": "example-mod",
  "scope": "示例：生成物品与延迟有效性",
  "server_script": "tools/scenarios/example-server.lua",
  "requirements": [
    {
      "id": "spawn-item",
      "description": "木头生成成功，延迟检查时实体仍然有效",
      "stage": "server",
      "assertions": ["log_spawned", "log_still_valid"]
    }
  ],
  "uncovered": ["真实客户端图标与交互"]
}
```

场景路径相对配置中的 `workspace` 解析。需要客户端时增加 `client_script` 及对应的 `stage: "client"` 要求；需要专服先准备客户端测试状态时可设置 `client_server_script`。真实示例见 [旺达验收计划](acceptance/wanda-skilltree.json)。

`scope` 描述本次覆盖范围；`uncovered` 是范围外的未验证说明，非空不自动导致失败。本次需求不能放入 `uncovered` 后宣称完成，也不能删除失败断言来取得绿色结果。修改需求、API 或实现后重跑受影响检查，最后运行 `verify`。

## 服务端场景协议

场景在隔离专服内直接执行，使用以下接口：

- `TEST.Assert(id, ok, details)`：记录具名断言，`ok` 必须为 `true` 才通过；同名断言出现过失败，之后通过也不能覆盖失败。
- `TEST.After(seconds, callback)`：登记异步回调，捕获回调异常；完成信号会等待已登记回调结束。
- `TEST.Done(details)`：显式请求结束；零断言、计划要求的断言缺失或失败均不能通过。

对应上面的示例场景：

```lua
local item = SpawnPrefab("log")
TEST.Assert("log_spawned", item ~= nil)
TEST.After(0.2, function()
    TEST.Assert("log_still_valid", item ~= nil and item:IsValid())
    if item ~= nil and item:IsValid() then item:Remove() end
    TEST.Done("生成与延迟检查完成")
end)
```

异步断言必须使用 `TEST.After`；不能直接 `DoTaskInTime` 后立刻 `TEST.Done`，否则完成信号无法追踪该回调。场景仅 `return function(api)` 不会被隐式执行，工具会明确失败。旧同步 `dst_selftest.lua` 需要明确的包装场景加载并调用 `TEST.Legacy`，再显式结束；当前例子见 [wanda-server.lua](scenarios/wanda-server.lua)。不要把同步包装直接用于包含未登记异步任务的旧脚本。

## 真实客户端证据

涉及 HUD、图标、技能按钮、网络预测、客户端 Replica 或主客机同步时，要在独立真实客户端运行对应场景。客户端脚本可返回 `function(t)`，使用 `t.Assert`、`t.After`、`t.Done`；其加载协议与上面的服务端直接执行协议不同。示例见 [wanda-client.lua](scenarios/wanda-client.lua)。客户端异步断言同样要登记并显式完成。

客户端报告要求本轮运行 token、`side=client` 的 `ready/player/hud/replica/done` 事件，以及全部规定断言。服务端 DONE、客户端进程启动或进入菜单都不能代替这些证据。HUD/Replica 对象验证也不证明像素外观、声音、技能点击和实际激活正常，这些必须各有对应场景或明确记录为尚未验收。

遇到 Steam、连接、选角、模组提示等外部阻塞，记录具体阶段和证据；不能把无法进入世界改成“客户端通过”。同一阻塞没有新证据时停止重复试跑。

## 证据绑定与失效

除 `doctor` 外，命令在配置校验与模组定位成功后，于项目外 `evidence_root` 创建独立目录，保存 `result.json` 及相关阶段报告、日志。`doctor` 只输出检查结果；配置或初始化提前失败时也可能尚未创建报告目录。正常执行的统一报告记录命令、模组、生成时间和以下版本信息：

- `source_sha256`：运行文件集合及模组旧 `dst_selftest.lua`（如存在）。
- `scripts_zip_sha256`：本次实际使用的游戏脚本包。
- `upstream_commit`：已审查且通过版本检查的上游提交。
- `tool_sha256`：本地测试工具及客户端 harness。
- `plan_sha256`、`scenario_sha256`：`verify` 使用的验收计划与场景。

任一输入改变后旧报告失效，执行期间输入改变也不能归属为当前版本通过。部署必须显式传入位于本机 `evidence_root` 内、名为 `result.json`、`command=verify`、`status=passed` 且模组匹配的报告；单项 `test` 报告不具备部署资格。

静态检查只识别扫描范围内的直接调用，不证明参数语义、执行端、动态 Hook 或完整运行链路。需要人工查证的调用可在计划 `api_reviews` 中记录 `file/line/side/component/method`、`reason`、`evidence`，并绑定 `mod_file_sha256` 和 `scripts_zip_sha256`。必须先读当前原版定义及调用者；这不是跳过告警的白名单，文件或游戏版本变化后应重新查证。

## 隔离与清理

测试会创建本轮唯一的临时模组副本、runner、临时存档与端口，不覆盖正式模组或用户存档。结束时仅停止本轮创建的专服/客户端，清除本轮临时目录并核对端口释放；报告和日志保留供追溯。用户原有进程不属于清理范围。

客户端测试发现 Steam 未运行时，会尝试以 `-silent` 启动已安装的 Steam，并在结束后清理本轮启动的实例；不安装或自动登录。测试前已运行的 Steam 保留。

离线连接仅原样复制当前 Steam 活动账号的 `inventory_cache_prod` 与 `inventory_cache_prod_sig` 到隔离账号的 `client_save/`，由同账号 `customcommands.lua` 在握手前调用官方 `TheInventory:ForceLoadOfflineCache()` 校验加载；不复制 token、凭据或完整玩家存档。结束时删除本轮临时缓存与脚本。路径及排查细节见 `~/.ai/tools/docs/notes/dst-mod-workflow.md` 的客户端准备章节。

隔离账号的启动命令同时调用原版 `Profile:SetWarnModsEnabled(false)`，并核对 `ShouldWarnModsEnabled()` 为 false，自动跳过联机时的“Mods Enabled”确认。每轮临时配置都会重新设置并记录日志；只写隔离测试目录，不修改玩家日常配置。

查看报告中的 cleanup 结果，任何清理失败都不能交付为通过。不要为了省去清理使用旧 `-KeepTemp`，也不要手动结束所有同名 DST 进程。

## 部署、备份与回滚

先预览目标和差异，再通过统一入口应用：

```powershell
& ./tools/dst.ps1 deploy --mod wanda-skilltree
& ./tools/dst.ps1 deploy --mod wanda-skilltree --apply --verified '<成功verify的result.json完整路径>'
```

仅支持工作区直属的本地模组，拒绝 `workshop-*`、符号链接/目录联接及目标 Git 工作副本。部署仅包含运行文件，排除文档、测试脚本、日志、源美术等开发文件，并清除目标内不属于运行集合的残留；预览时要核对 `delete` 项。

发生文件变更的实际应用在 `evidence_root/deploy/<时间与唯一标识>/` 保存 `manifest.json`；原更新/删除文件备份在 `before/`，新文件先准备在 `staged/`。准备阶段核对源、目标是否变化，应用后验证完整目标文件集合及 SHA256。失败时自动恢复原文件、移除本轮新增文件，并核对恢复后的哈希。备份清单中 `prepare_failed` 表示准备阶段失败、目标未改；`rolled_back` 表示已恢复；`rollback_failed` 表示恢复未完成，需依据保留的清单处理。没有文件差异时返回 `unchanged`，不创建备份。

当前没有独立 `rollback` 子命令。需要恢复某次成功部署时，先依据对应 `manifest.json` 核对目标边界和 `add/update/delete`，从 `before/` 恢复原文件，并仅移除该次新增项，最后校验清单中的原哈希；不要盲目整目录覆盖或递归删除。不要直接调用低层 `dst_deploy.py --apply` 绕开统一入口的验收门禁。

部署后重启相应世界/服务器加载新 Lua，并核对实际运行副本。创意工坊发布不属于本地部署，需要该任务的明确授权。

## 旧入口兼容

| 旧入口 | 当前行为 |
| --- | --- |
| `run_dst_mod_tests.ps1 -Mode static` | 转发 `check` |
| `run_dst_mod_tests.ps1 -Mode server` | 转发 `test` |
| `run_dst_mod_tests.ps1 -Mode full` | 转发 `verify`，不再只是尽力启动客户端 |
| `-RuntimeTimeout` / `-Config` | 对应 `--timeout` / `--config` |
| `-Plan` | 用于 static/full；独立服务端场景改用 `test --script` |
| `-Strict` | 严格检查始终生效 |
| `-KeepTemp/-DstRoot/-KleiRoot/-ServerPort/-ClientTimeout` | 已停用，传入会报错；环境用配置，临时目录和端口由工具管理 |
| `sync_dst_mods.bat` 无参数 | 仅预览旺达模组部署 |
| `sync_dst_mods.bat --mod <模组名> --apply --verified <result.json>` | 转发统一部署入口，仍要求有效验收报告 |

不要继续使用历史 `dst-original-analysis/tools/dst_mod_selftest.py` 作为日常入口，也不要把旧 `test-reports` 或模组目录内的报告当作当前验收证据。

## 当前已验证边界

2026-11-01 最终 `verify` 已通过旧 `-Mode full` 兼容入口运行，退出码 0：静态检查 83 个直接调用、0 个待查调用，服务端 34 条具名断言、真实客户端 7 条基础断言全部 `passed`；两阶段 cleanup 全部通过。最终报告为本机配置的 `evidence_root/20261101-150840-c286c2a7/result.json`。客户端基础验收覆盖远端旺达、HUD、health Replica 与专服数值一致、年龄徽章对象，不代表全部技能或完整客户端玩法通过。

故意失败与延迟失败场景均正确返回失败且清理通过；最终工具回归 46 项全部通过，日志为 `evidence_root/final-workflow-tests.log`。

旺达计划尚未覆盖技能树点击与实际激活、重连/重生/保存重启、洞穴切换、第三方状态栏兼容、像素/声音及未完成技能设计；这些边界仍保留在计划和 [开发状态](../wanda-skilltree/DEVELOPMENT_STATUS.md) 中。

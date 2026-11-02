# DST 模组工作区指令

本仓库包含旺达技能树、地皮合集、CrashTrace 诊断模组及开发工具。与用户沟通、维护文档使用中文，修改前保留已有未提交变更。

## 开始开发

- 先读目标模组内的 `AGENTS.md`、状态和交接文档；旺达入口是 `wanda-skilltree/DEVELOPMENT_STATUS.md` 和 `wanda-skilltree/AI_CONVERSATION_SUMMARY.md`。
- 开发及验收的唯一说明入口是 [tools/DST_TESTING.md](tools/DST_TESTING.md)。本机路径从 `~/.ai/local/config/dst-mod-development/config.json` 读取，先执行 `tools/dst.ps1 doctor`。
- 当前游戏 API、组件和资源以配置安装目录中的 `data/databundles/scripts.zip` 为准。`../dst-original-analysis/`、`dst-inspect/` 是历史线索，不代表当前版本；不要修改原版或第三方镜像。

## 实现与验收

- 每个新需求先确定可观察结果，并为它增加或选择对应的具名断言；既有核心基线通过不能替代新功能验收。
- 按 `check → test → verify` 迭代修复。默认计划位于 `tools/acceptance/<模组名>.json`；服务端场景使用 `TEST.Assert`、`TEST.After` 和显式 `TEST.Done`。
- 真实客户端的 HUD、交互、图标、预测及 Replica 需要对应客户端证据。静态或专服通过不能表述为完整客户端通过；缺证据如实标记 `blocked`。
- 验收只覆盖计划声明的范围，保留 `uncovered`；不能删掉失败要求、缩小本次需求或把零断言当作通过。
- 部署先执行 `tools/dst.ps1 deploy --mod <模组名>` 预览；实际写入必须通过统一入口的 `--apply --verified <成功verify的result.json>`。源码、游戏、工具、计划或场景变更后重新验收。
- 工坊更新后必须核对源码、上传副本、工坊唯一 `version:...` 标签和实际下载副本的版本一致，并比对下载运行文件哈希；不能仅凭上传 `Success` 或封面生效宣布发布完成。版本标签不一致会让客户端持续提示过期；发布检查见 [地皮合集发布说明](turf-collection/README.md#创意工坊发布与更新)。
- 测试结束清理本轮创建的进程、临时模组和存档，并确认端口释放；保留用户原有进程。报告留在配置的项目外 `evidence_root`。
- 修改玩法或验证状态时，同步目标模组要求维护的状态和交接文档。已授权的实现、测试与修复持续完成；评审请求本身保持只读。
- 旺达当前验收证据与未覆盖项统一维护在 `wanda-skilltree/DEVELOPMENT_STATUS.md` 第 6 节；不要把局部基线的 `passed` 扩大为全部技能完成。

## 历史

原 `AGENTS.md` 的完整历史上下文已逐字节保存在 [2026-06-01 历史索引](docs/history/agent-context-20260601.md)。其中旧推测、旧路径和旧验证状态仅用于追溯，以当前源码、状态文档和本次报告为准。

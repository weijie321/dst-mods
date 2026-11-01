# Agent Notes

本仓库是 Don't Starve Together 的旺达技能树模组。与用户沟通使用中文。

改代码前先读 `DEVELOPMENT_STATUS.md` 和 `AI_CONVERSATION_SUMMARY.md`，它们是当前交接事实源。凡是改到技能、配方、UI、动作或验证状态，都要同步更新这两份文档。

关键代码：

- `modmain.lua`：注册、配方、Prefab 导入。
- `scripts/wanda_skill_hooks.lua`：主要玩法和 UI Hook。
- `scripts/prefabs/skilltree_wanda.lua`：技能节点和连线。
- `scripts/wanda_skill_util.lua`：共享技能工具。

重要约束：

- `scripts/prefabs/skilltree_wanda.lua` 通过 `Asset("SCRIPT", ...)` 加载，不要加入 `PrefabFiles`。
- 优先复用原版 DST 机制和现有 UI/模组 Hook，避免自造 UI 层。旺达年龄徽章应提供正确数值，并复用已有状态栏显示逻辑。
- 不要重新引入 `scripts/prefabs/wanda_time_shard.lua`；时光贮匣配方使用原版 `pocketwatch_parts`。
- 客户端代码不要假设 `components.health` 这类服务端组件存在。

验证命令见 `README.md`。复制到实际 DST `mods` 目录后，需要重启世界/服务器让 Lua 重新加载。

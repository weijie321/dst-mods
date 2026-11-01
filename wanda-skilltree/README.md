# wanda-skilltree

`wanda-skilltree` 是一个 Don't Starve Together 模组，为旺达添加官方风格技能树，并扩展多条怀表相关机制。

## 项目入口

- `modmain.lua`：模组入口、技能树注册、Prefab 列表、配方和模块导入。
- `scripts/prefabs/skilltree_wanda.lua`：旺达技能节点与面板分组。
- `scripts/wanda_skill_hooks.lua`：旺达、怀表、动作、状态机、徽章和装备栏等主体 Hook。
- `scripts/wanda_skill_util.lua`：技能判断和共享工具函数。
- `scripts/containers_wanda_timebox.lua`：时光贮匣容器布局。
- `scripts/prefabs/wanda_timebox.lua`：时光贮匣 prefab。
- `DEVELOPMENT_STATUS.md`：详细实现状态和剩余验证缺口。
- `AI_CONVERSATION_SUMMARY.md`：给下一轮 AI 接手的一页摘要。

## 当前状态

已实现的主要范围包括年龄上限技能、怀表治疗加成、老年工作效率、溯源表/裂缝表改名、时光贮匣配方与装备槽、恒稳裂隙，以及部分战斗、团队和亲和 Hook。

高风险剩余项是 DST 真实客户端回归、命运回拨复活优先级、位面防御语义，以及非 `rechargeable` 怀表消耗路径。

## 验证

在仓库根目录使用统一入口；配置、验收计划格式、证据和部署回滚见 [开发与验收说明](../tools/DST_TESTING.md)。

```powershell
& ./tools/dst.ps1 doctor
& ./tools/dst.ps1 check --mod wanda-skilltree
& ./tools/dst.ps1 test --mod wanda-skilltree
& ./tools/dst.ps1 verify --mod wanda-skilltree
```

默认计划是 `tools/acceptance/wanda-skilltree.json`。每个新需求先增加或选择对应的验收断言；核心基线通过不能直接证明新功能完成。本轮 `verify` 已通过：静态 83 个直接调用、0 个待查调用，服务端 34 条断言、真实客户端 7 条基础断言及两阶段清理全部通过。客户端结论仅覆盖远端旺达、HUD、health Replica 与年龄徽章基线；技能点击、重连重生、像素/声音及未完成技能仍未验收，证据与完整边界见 `DEVELOPMENT_STATUS.md` 第 6 节。

完整验收通过后，先预览，再凭输入仍匹配的报告部署：

```powershell
& ./tools/dst.ps1 deploy --mod wanda-skilltree
& ./tools/dst.ps1 deploy --mod wanda-skilltree --apply --verified '<成功verify的result.json完整路径>'
```

报告与日志保存在本机配置的项目外 `evidence_root`，源码、游戏、工具、计划或场景变化后重新验收。部署后重启世界/服务器让 Lua 重新加载，并核对实际运行副本。

# 旺达技能树扩展（wanda-skilltree）开发状态交接

> 路径：`dst-mods/wanda-skilltree/`  
> 用途：后续从零或断点继续开发时，快速了解「已实现 / 半成品 / 未实现 / 已知风险」。  
> 说明：本文档依据仓库内当前 Lua 与计划对照整理，**未在真实 DST 客户端内完整跑通验证**。

---

## 1. 目录与入口

| 文件 | 作用 |
|------|------|
| `modinfo.lua` | 模组元信息；当前未配置 `icon` / `icon_atlas`（可选补全）。 |
| `modmain.lua` | `GLOBAL` 代理、`TUNING.WANDA_SKILLTREE_MOD`、注册旺达技能树、`PrefabFiles`、`AddRecipe2`、加载 `containers` / `hooks`。 |
| `scripts/prefabs/skilltree_wanda.lua` | 技能树节点定义与 `ORDERS`（面板分组）。 |
| `scripts/wanda_skill_strings.lua` | 中文 `STRINGS`（技能名、描述、部分物品）。 |
| `scripts/wanda_skill_util.lua` | `HasSkill`、队友查找、绑定表查找等工具。 |
| `scripts/wanda_skill_hooks.lua` | 旺达 PostInit、怀表 Hook、状态机、动作、UI 装备栏等。 |
| `scripts/containers_wanda_timebox.lua` | `wanda_timebox_1/2/3` 容器布局。 |
| `scripts/prefabs/wanda_timebox.lua` | 时光贮匣三阶 prefab。 |
| `scripts/prefabs/wanda_time_shard.lua` | 时间碎片材料。 |
| `scripts/prefabs/wanda_time_decoy.lua` | 倒走表「残影」占位实现。 |
| `scripts/prefabs/desperate_pocketwatch_weapon.lua` | 绝望警钟武器。 |

---

## 2. 设计对照：已实现（或部分实现）

### 2.1 技能树框架

- [x] 通过 `require("prefabs/skilltree_defs")` + `CreateSkillTreeFor("wanda", ...)` 注册旺达树（若官方已有 `wanda` 定义则跳过并打印日志）。
- [x] 五类分组 `ORDERS`：`age` / `watch` / `warp` / `team` / `allegiance`。
- [x] 亲和锁：暗影侧织影者、月亮侧天体英雄 + 互斥锁写法参考原版 Wilson 树。

### 2.2 分支一：岁月掌控

| 设计点 | 代码状态 | 备注 |
|--------|----------|------|
| 岁月感知 100/120/150 | 部分 | `ApplyAgeMax` 通过事件驱动（`onactivateskill_server`/`ms_skilltreeinitialized`）调用。服务端 `SetMaxHealth` 成功，但客户端 age badge 仍显示 Max:80，疑似 `player_classified` 同步问题。**待查：客户端 `classified.maxhealth:value()` 实际值。** |
| 逆龄余波 +2/+5/+10 | 基本 | 通过 `oldager:OnTakeDamage(bonus, false, "wanda_heal_bonus")` 实现年龄回退；在 PostInit 中注册 `AddValidHealingCause("wanda_heal_bonus")`。 |
| 迟暮从容 | 部分 | 仅在 `age_state == "old"` 时去掉 `slowbuilder`、`noheavylifting`、锤击倍率；未覆盖设计里「搬运等全部惩罚」。 |
| 岁月主宰 50% 位面减伤 | 存疑 | 使用 `planardefense:SetBaseDefense(0.5)`；**需查原版 `planardefense` 语义**是否等价「受位面伤害减半」，否则应改用 `damagetyperesist` 或其它官方用法。 |
| 亲和后解锁 | 部分 | `wanda_planar_defense_lock` 用 `CountTags(..., "allegiance")` 判断；需确认与暗影/月亮 tag 是否一致。 |

### 2.3 分支二：钟表匠造诣

| 设计点 | 代码状态 | 备注 |
|--------|----------|------|
| 时光贮匣 2×2 / 3×3 / 4×4 | 基本 | `containers_wanda_timebox.lua` + `wanda_timebox.lua`；仅允许 `pocketwatch` tag。 |
| 不占物品栏 + 专属装备栏 | 基本 | `EQUIPSLOTS.WANDA_TIMEBOX` + `inventorybar:AddEquipSlot`；`CanEquipTimeBox` 校验技能后才允许装备；无技能时槽位为空。 |
| 配方材料「时间碎片」 | 变通 | 实现为独立 prefab `wanda_time_shard`，另加 `AddRecipe2` 用 `pocketwatch_parts`+燃料合成（与设计「单一时间碎片」来源可能不一致，需产品定稿）。 |
| 钟表调校 −25% 冷却/消耗 | 部分 | 仅 Hook `rechargeable:Discharge` 乘系数；**未**统一处理 `finiteuses`、`fueled` 等其它消耗。 |
| 绝望警钟 +20% 伤害 | 基本 | `desperate_pocketwatch_weapon` 基础伤害 `POCKETWATCH_SHADOW_DAMAGE * 1.2`；配方与设计「绝望石+纯粹恐惧+警钟」已用 `dreadstone`+`horrorfuel`（需与游戏内物品名一致）。 |

### 2.4 分支三：时空行者

| 设计点 | 代码状态 | 备注 |
|--------|----------|------|
| 轻盈跃迁 | 基本 | `onwarpback` + `locomotor:SetExternalSpeedMultiplier`。 |
| 回溯记忆（羽毛笔改名） | 未完成 | 给溯源表挂了 `writeable` 与存档字段；**未**接羽毛笔交互、未限制「仅已标记且学会技能后」才可写。 |
| 时空残影 + 爆炸 50 | 占位 | `wanda_time_decoy` 用假人模型、`FindEntities`+`GetAttacked`；**无**可靠嘲讽/索敌干扰；爆炸用 `explode_small` 需确认 prefab 存在。 |
| 恒稳裂隙 | 基本 | 重写 `pocketwatch_portal` 施法分支；已对齐原版 walkable offset 寻路、`SpawnExit`、音效、冷却；保留裂缝表（不消耗/替换为溯源表），标记可复用。 |
| 虚时庇护（第 1 帧无敌） | 部分 | `AddStategraphPostInit` 在 `pocketwatch_warpback` timeline **头部**插入 1 帧事件；与原版第 4 帧逻辑**叠加**后的总无敌区间需游戏内验证。 |

### 2.5 分支四：时间支援

| 设计点 | 代码状态 | 备注 |
|--------|----------|------|
| 同频修复 30 血 | 基本 | 不老表成功施法后对半径内队友 `DoDelta(30)`；缺「仅治疗自己时」等边界（若原版可对他人施法需对齐）。 |
| 短暂庇护 3 帧 | 部分 | 仅在「同频治疗」循环里触发；**未**覆盖「旺达复活队友」等其它治疗/复活路径。 |
| 羁绊刻印 | 部分 | 自定义 `WANDA_BOND_MARK` + `recallmark:MarkPosition`；需确认 `ACTIONS` 在客户端注册、`STRINGS.ACTIONS` 全语言、以及存档同步 `userid` 跨下线。 |
| 命运回拨（最低优先级复活） | **未完成** | 监听 `ms_becameghost` + 延迟 `respawnfromghost`；**未**实现与其它复活源的优先级排序；`source = watch` 是否被原版接受需验证；`FindBondedRecallWatch` 仅扫一名旺达背包，未处理表在地面/他人身上等。 |

### 2.6 分支五：亲和

| 设计点 | 代码状态 | 备注 |
|--------|----------|------|
| 暗影/月亮亲和节点 | 树内有 | `onactivate` 仅调 `ApplyWandaSkill`；**未**给玩家加原版 `player_shadow_aligned` / `damagetyperesist` 等与 Wilson 一致的完整效果（若需要需复制 Wilson 的 `onactivate` 逻辑）。 |
| 暗钟共鸣 / 明钟共鸣 | 部分 | Hook `weapon:SetOnAttack`；暗影叠层改 `weapon:SetDamage` 为**全局**伤害倍率，易副作用；月亮 AOE 用 `GetAttacked` 与「总伤害 30%」表述是否一致需验。**技能节点 `wanda_shadow_clock` / `wanda_lunar_clock` 在 `skilltree_wanda.lua` 中无 `locks`/`connects`/`root`，可能被 `CreateSkillTreeFor` 判为 FLOATING，需在树里补父节点或 `locks`。** |

---

## 3. 明确未做 / 待验证清单

1. **游戏内加载**：整 Mod 未在 DST 主菜单启用后完整跑一局；技能树 UI、图标资源、`GetSkilltreeIconAtlas` 是否缺图需进游戏看 log。  
2. ~~**技能树校验**~~：已确认 `wanda_shadow_clock`、`wanda_lunar_clock` 通过父节点 `connects` 连接，不会 FLOATING。  
3. ~~**逆龄余波**~~：已改为 `oldager:OnTakeDamage(bonus, false, "wanda_heal_bonus")`，并注册 valid healing cause。  
4. **岁月感知与生命上限**：与 `WANDA_OLDAGER`、`oldager` 更新顺序、换人物、重生后是否一致。  
5. ~~**恒稳裂隙**~~：已对齐原版 walkable offset、SpawnExit、音效、冷却；保留裂缝表不消耗。  
6. **命运回拨**：事件选型（`death` / `ms_playerdied` / 幽灵状态）、与其它复活 Mod 优先级、`activateresurrection` 流程。  
7. ~~**inventorybar**~~：`AddEquipSlot` 对旺达总是生效，`CanEquipTimeBox` 校验技能后才允许装备。  
8. **本地化**：`modinfo` 英文描述、`STRINGS.SKILLTREE.WANDA` 英文版、`ACTIONS` 等。  
9. **modinfo 图标**：可选 `modicon.tex/xml`。  

---

## 4. 建议的续开发顺序

1. ~~修正技能树数据~~：已确认 FLOATING 为误报，connects 已从父节点连通。  
2. ~~修正逆龄余波~~：已改用 `oldager:OnTakeDamage`。  
3. ~~恒稳裂隙~~：已对齐原版 walkable offset + SpawnExit + 冷却。  
4. ~~技能激活与 bonus 应用架构~~：已从类表方法 Hook 重构为事件驱动（2026-05-03）。  
5. **岁月感知 MaxHealth 客户端同步**：服务端 `SetMaxHealth` 生效，客户端显示仍不正确。需定位 `player_classified` 同步链断点。  
6. 回溯记忆：羽毛笔 `ACTION` + `writeable` 仅在 `recallmark:IsMarked()` 且学会技能后可用。  
7. 命运回拨：统一复活管线与优先级；绑定表全容器扫描 + 落点安全校验。  
8. 钟表调校：枚举所有怀表消耗路径（`finiteuses`、`fueled`、自定义消耗）。  
9. 时空残影：专用 `combat` 诱饵 prefab 或 `target` 组件、仇恨列表、爆炸伤害类型（是否位面）。  
10. 全量联机测试 + CrashTrace / 客户端 log。  

---

## 5. 关键代码锚点（便于搜索）

- 技能树注册：`modmain.lua` 中 `RegisterWandaSkillTree`。  
- 旺达数值应用：`wanda_skill_hooks.lua` 中 `ApplyWandaSkillTreeBonuses` / `OnWandaPostInit`。  
- 不老表：`WrapPocketWatchHeal`。  
- 溯源 / 裂缝：`WrapRecallWatch`、`WrapPortalWatch`。  
- 倒走表无敌与残影：`AddStategraphPostInit("wilson", ...)` + `onwarpback`。  
- 容器：`containers_wanda_timebox.lua`。  

---

*文档生成日期以仓库为准；后续改代码后请同步更新本文件「第 2、3 节」。*

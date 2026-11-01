# 旺达技能树扩展（wanda-skilltree）开发状态交接

> 路径：`dst-mods/wanda-skilltree/`  
> 用途：后续从零或断点继续开发时，快速了解「已实现 / 半成品 / 未实现 / 已知风险」。  
> 说明：本文档依据仓库内当前 Lua 与计划对照整理，**核心服务端与真实客户端 HUD/Replica 基线已验收，全部技能和客户端玩法仍未完整验证**。
> 流程验证：本轮 `verify` 的静态检查、服务端 34 条断言、真实客户端 7 条基础断言及两阶段清理全部通过；只代表计划限定范围。开发入口、报告与未覆盖项见第 6 节。

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
| `scripts/prefabs/wanda_timebox.lua` | 时光贮匣三阶 prefab（复用原版时间碎片图标/材料，不再新增独立时间碎片材料）。 |
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
| 岁月感知 100/120/150 | 基本 | `ApplyAgeMax` 通过事件驱动（`onactivateskill_server`/`ms_skilltreeinitialized`）调用，按显示年龄上限换算 `health.maxhealth = display_max - WANDA_MIN_YEARS_OLD` 并保持当前显示年龄。客户端 `wandaagebadge` 已按传入 max 计算当前年龄/最大年龄；若启用 Combined Status 类状态栏 UI，则复用其 `CombinedStatusUpdateNumbers(max)` 更新最大值显示，不新增自定义 `Max:` UI。仍建议进真实客户端验证换人、重生、重连后的显示。 |
| 逆龄余波 +2/+5/+10 | 已修复 | 通过 `oldager:OnTakeDamage(bonus / TUNING.OLDAGE_HEALTH_SCALE, false, "wanda_heal_bonus")` 实现年龄回退；在 PostInit 中注册 `AddValidHealingCause("wanda_heal_bonus")`，避免只回复 1 点年龄。 |
| 迟暮从容 | 已修复 | 老年状态且学会技能时去掉 `slowbuilder` 与 `noheavylifting`，锤击/砍伐/开采复用满力量大力士工作倍率，并补 `efficientuser`、`expertsailor`、装备减速下限等满力量相关效率。失去技能或离开老年状态会移除这些加成并恢复原版老年惩罚。 |
| 岁月主宰 50% 位面减伤 | 存疑 | 使用 `planardefense:SetBaseDefense(0.5)`；**需查原版 `planardefense` 语义**是否等价「受位面伤害减半」，否则应改用 `damagetyperesist` 或其它官方用法。 |
| 亲和后解锁 | 部分 | `wanda_planar_defense_lock` 用 `CountTags(..., "allegiance")` 判断；需确认与暗影/月亮 tag 是否一致。 |

### 2.3 分支二：钟表匠造诣

| 设计点 | 代码状态 | 备注 |
|--------|----------|------|
| 时光贮匣 2×2 / 3×3 / 4×4 | 基本 | `containers_wanda_timebox.lua` + `wanda_timebox.lua`；仅允许 `pocketwatch` tag。 |
| 不占物品栏 + 专属装备栏 | 基本 | `EQUIPSLOTS.WANDA_TIMEBOX` + `inventorybar:AddEquipSlot(..., 3.5)`；`CanEquipTimeBox` 校验技能后才允许装备；无技能时槽位为空。 |
| 配方材料「时间碎片」 | 已修正 | 不再定义 `wanda_time_shard`；配方使用原版 `pocketwatch_parts`（游戏内时间碎片）并复用原版图标。时光贮匣不需要蓝图，一阶靠近科学机器解锁，二/三阶按技能继续升级。 |
| 钟表调校 −25% 冷却/消耗 | 部分 | 仅 Hook `rechargeable:Discharge` 乘系数；**未**统一处理 `finiteuses`、`fueled` 等其它消耗。 |
| 绝望警钟 +20% 伤害 | 基本 | `desperate_pocketwatch_weapon` 基础伤害 `POCKETWATCH_SHADOW_DAMAGE * 1.2`；配方与设计「绝望石+纯粹恐惧+警钟」已用 `dreadstone`+`horrorfuel`（需与游戏内物品名一致）。 |

### 2.4 分支三：时空行者

| 设计点 | 代码状态 | 备注 |
|--------|----------|------|
| 轻盈跃迁 | 基本 | `onwarpback` + `locomotor:SetExternalSpeedMultiplier`。 |
| 回溯记忆（羽毛笔改名） | 基本 | 给溯源表/裂缝表挂 `writeable` 与存档字段；学会 `wanda_recall_rename` 后，拿羽毛笔右键溯源表或裂缝表会触发 `WANDA_RENAME_WATCH` 并弹出原版书写框。当前限制为技能 + 表 prefab，未强制要求 `recallmark:IsMarked()`。 |
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

1. **客户端玩法与画面**：已验证独立客户端进入旺达角色、HUD、health Replica 与年龄徽章基础对象；尚未验证完整技能操作与画面。技能树 UI、图标资源、`GetSkilltreeIconAtlas` 是否缺图仍需对应的真实客户端证据。
2. ~~**技能树校验**~~：已确认 `wanda_shadow_clock`、`wanda_lunar_clock` 通过父节点 `connects` 连接，不会 FLOATING。
3. ~~**逆龄余波**~~：已改为 `oldager:OnTakeDamage(bonus / TUNING.OLDAGE_HEALTH_SCALE, false, "wanda_heal_bonus")`，并注册 valid healing cause。
4. **岁月感知与生命上限回归验证**：基础同步链路已修；仍需真实客户端验证与 `WANDA_OLDAGER`、`oldager` 更新顺序、换人物、重生后是否一致。
5. ~~**恒稳裂隙**~~：已对齐原版 walkable offset、SpawnExit、音效、冷却；保留裂缝表不消耗。
6. **命运回拨**：事件选型（`death` / `ms_playerdied` / 幽灵状态）、与其它复活 Mod 优先级、`activateresurrection` 流程。
7. ~~**inventorybar**~~：`AddEquipSlot` 对旺达总是生效，`CanEquipTimeBox` 校验技能后才允许装备。
8. ~~**时光贮匣配方/解锁/材料**~~：已改为原版 `pocketwatch_parts`，靠近科学机器解锁，一阶无需技能/蓝图，二三阶按技能升级。
9. ~~**羽毛笔改名交互**~~：已添加羽毛笔右键溯源表/裂缝表的 `WANDA_RENAME_WATCH` 动作与书写框。
10. **本地化**：`modinfo` 英文描述、`STRINGS.SKILLTREE.WANDA` 英文版、`ACTIONS` 等。
11. **modinfo 图标**：可选 `modicon.tex/xml`。

---

## 4. 建议的续开发顺序

1. ~~修正技能树数据~~：已确认 FLOATING 为误报，connects 已从父节点连通。
2. ~~修正逆龄余波~~：已改用 `oldager:OnTakeDamage`。
3. ~~恒稳裂隙~~：已对齐原版 walkable offset + SpawnExit + 冷却。
4. ~~技能激活与 bonus 应用架构~~：已从类表方法 Hook 重构为事件驱动（2026-05-03）。
5. ~~岁月感知 MaxHealth / age badge 同步~~：已按显示年龄上限换算生命上限，并修正 `wandaagebadge` 对 max 的计算；Combined Status 类 UI 通过既有 `CombinedStatusUpdateNumbers(max)` 显示最大值。继续做真实客户端回归即可。
6. ~~回溯记忆改名交互~~：已接羽毛笔 `ACTION` + `writeable`，学会技能后可右键溯源表/裂缝表改名；若后续设计要求「仅已标记表可改名」，再补 `recallmark:IsMarked()` 限制。
7. 命运回拨：统一复活管线与优先级；绑定表全容器扫描 + 落点安全校验。
8. 钟表调校：枚举所有怀表消耗路径（`finiteuses`、`fueled`、自定义消耗）。
9. 时空残影：专用 `combat` 诱饵 prefab 或 `target` 组件、仇恨列表、爆炸伤害类型（是否位面）。
10. 按 [统一验收入口](../tools/DST_TESTING.md) 补齐本次需求的联机/客户端断言，结合 CrashTrace 与客户端 log；不把进程启动当作客户端通过。

---

## 5. 关键代码锚点（便于搜索）

- 技能树注册：`modmain.lua` 中 `RegisterWandaSkillTree`。  
- 旺达数值应用：`wanda_skill_hooks.lua` 中 `ApplyWandaSkillTreeBonuses` / `OnWandaPostInit`。  
- 不老表：`WrapPocketWatchHeal`。  
- 溯源 / 裂缝：`WrapRecallWatch`、`WrapPortalWatch`。  
- 倒走表无敌与残影：`AddStategraphPostInit("wilson", ...)` + `onwarpback`。  
- 容器：`containers_wanda_timebox.lua`。  

---

## 6. 开发验证入口与证据边界

在仓库根目录使用 `tools/dst.ps1 doctor/check/test/verify/deploy`；完整命令、计划 schema、异步场景和回滚说明见 [tools/DST_TESTING.md](../tools/DST_TESTING.md)。默认验收计划是 `tools/acceptance/wanda-skilltree.json`，默认服务端场景是 `tools/scenarios/wanda-server.lua`。

每次新需求先定义对应的可观察结果和具名断言，再实现、运行、修复，最后 `verify`。现有 34 条服务端基线只覆盖核心配方/装备槽、改名注册、年龄同步、老年效率和治疗等行为；不能沿用该基线宣称新增功能完成。

2026-11-01 最终 `verify` 通过旧 `-Mode full` 兼容入口运行，退出码 0：静态检查 83 个直接调用、0 个待查调用；服务端 34 条具名断言、真实客户端 7 条基础断言全部 `passed`，两阶段 cleanup 全部通过。客户端覆盖远端旺达、HUD、health Replica 与专服数值一致、年龄徽章基础对象。报告位于本机配置的 `evidence_root/20261101-150840-c286c2a7/result.json`。

故意失败和延迟失败场景均正确返回失败且清理通过；工具回归 46 项全部通过，日志位于 `evidence_root/final-workflow-tests.log`。这些结果不扩张计划范围：技能点击与实际激活、重连、死亡重生、保存重启、洞穴切换、第三方状态栏、像素/声音及未完成技能设计仍在 `uncovered`，需要后续需求的专属断言和证据。

报告存入本机配置的项目外 `evidence_root`，绑定源码、游戏 `scripts.zip`、测试工具、计划与场景版本。实际部署必须先预览，再使用 `deploy --mod wanda-skilltree --apply --verified <成功verify的result.json>`；版本变化后重新验收，单项服务端报告不能代替完整验收。当前原版查证直接读取配置安装目录的 `scripts.zip`，历史 `dst-original-analysis`/`dst-inspect` 仅供线索。

*文档生成日期以仓库为准；后续改代码后请同步更新本文件「第 2、3 节」，验证状态变化时同步第 6 节与交接摘要。*

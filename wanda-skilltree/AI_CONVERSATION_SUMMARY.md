# 给后续 AI 的一页摘要（旺达技能树 Mod）

**项目**：`Don't Starve Together` 模组 **wanda-skilltree**，为旺达扩展官方式技能树（五栏：岁月 / 怀表 / 时空 / 团队 / 亲和），并 Hook 怀表、倒走、溯源、裂缝、警钟、时光贮匣等。

**根路径**：`dst-mods/wanda-skilltree/`。详细设计对照、文件表、续开发顺序见同目录 **`DEVELOPMENT_STATUS.md`**（以该文件为事实源，本摘要仅加速上下文加载）。

**必读入口**：`modmain.lua`（注册树、Prefab、配方、`modimport`）；`scripts/wanda_skill_hooks.lua`（主体逻辑）；`scripts/prefabs/skilltree_wanda.lua`（节点与连线）。`skilltree_wanda` 仅作 `Asset("SCRIPT", ...)` 加载，**不要**放进 `PrefabFiles`。

**已大致落地**：技能树注册与安全跳过（若官方已有 `wanda` 树）；旺达 PostInit（年龄上限、迟暮从容、位面相关 `planardefense`、配方 tag）；不老表团队治疗与短庇护；倒走加速、warp 首帧无敌、残影占位；溯源表绑定/存档/传送分支与 `WANDA_BOND_MARK`；裂缝表在「恒稳裂隙」下的自定义分支；怀表 `rechargeable:Discharge` 调校；警钟/绝望钟叠层与月亮 AOE（简化）；幽灵侧「命运回拨」雏形；时光贮匣三阶 + `EQUIPSLOTS.WANDA_TIMEBOX` + `inventorybar` 加槽；原版时间碎片 `pocketwatch_parts` 配方与相关 `AddRecipe2`。

**已修复项**：① 逆龄余波按 `OLDAGE_HEALTH_SCALE` 换算后调用 `oldager:OnTakeDamage(..., "wanda_heal_bonus")`，注册 valid healing cause，避免实际只回复 1 点年龄。② 迟暮从容在老年状态下补齐满力量大力士式工作/搬运/划船/装备减速处理，并在离开老年或失去技能时恢复原版老年惩罚。③ 岁月感知按显示年龄上限换算 `health.maxhealth`，并修正 `wandaagebadge` 使用传入 max；Combined Status 类状态栏 UI 通过既有 `CombinedStatusUpdateNumbers(max)` 显示最大值，不新增自定义 UI。④ 时光贮匣使用原版 `pocketwatch_parts`，一阶靠近科学机器解锁且不需要蓝图，二三阶按技能升级；不再有 `wanda_time_shard` prefab。⑤ 羽毛笔右键溯源表/裂缝表会触发 `WANDA_RENAME_WATCH` 并打开原版书写框。⑥ 恒稳裂隙已对齐原版 walkable offset + SpawnExit + 音效 + 冷却，保留裂缝表不消耗。⑦ 技能树 FLOATING 已确认为误报（connects 从父节点连通）。⑧ 贮匣栏 `CanEquipTimeBox` 校验技能后才允许装备。⑨ 技能激活通过 `skilltreeupdater` 事件驱动 bonus 应用，避免类表级 ActivateSkill hook 破坏其它角色技能激活。

**剩余高优先级缺口**：① **真实客户端回归**：岁月感知换人/重生/重连后的 age badge 与状态栏 UI 显示仍需进游戏验证。② **岁月主宰** 的 `planardefense:SetBaseDefense(0.5)` 是否等于「位面伤害减半」需查原版组件语义。③ **命运回拨**：复活优先级、`ms_becameghost` / `respawnfromghost` 是否合适、绑定表扫描范围。④ **钟表调校**：仅 Hook `rechargeable:Discharge`，未覆盖 `finiteuses`、`fueled` 等其它消耗路径。

**环境与验证**：2026-11-01 最终 `verify` 通过（旧 `-Mode full` 兼容入口、退出码 0）：静态 83 个直接调用、0 个待查调用，服务端 34 条及真实客户端 7 条基础断言全部 `passed`，两阶段清理通过。报告为本机 `evidence_root/20261101-150840-c286c2a7/result.json`；工具回归 46 项通过，日志为 `evidence_root/final-workflow-tests.log`。客户端结论限于远端旺达、HUD、health Replica 与年龄徽章；技能点击、重连重生、洞穴、第三方状态栏、像素/声音及未完成技能仍未验收。故意失败和延迟失败场景已确认正确失败且清理通过。改代码后同步 `DEVELOPMENT_STATUS.md` 第 2–3 节，验证状态变化同时维护其第 6 节。

**统一入口**：在仓库根目录执行 `tools/dst.ps1 doctor`，再按 `check → test → verify` 循环；计划默认 `tools/acceptance/wanda-skilltree.json`。每个新需求先写对应断言，已有核心基线只作回归。详细协议、清理和回滚见 `../tools/DST_TESTING.md`。部署先预览，应用必须使用 `--apply --verified <成功verify的result.json>`，输入版本变化后重新验收。报告保存在本机配置的项目外 `evidence_root`。

**原版查证**：从本机配置指定的安装目录读取当前 `data/databundles/scripts.zip`。兄弟 `dst-original-analysis` 和 `dst-inspect` 只提供历史线索；不要优先用旧解压副本判断当前 API。

**用户偏好**：中文沟通；小改动可直接改仓库；大架构或大规模改动可先 plan 或与用户确认。UTF-8 保存 Lua/MD。

当前已授权范围内的开发、测试与修复持续完成，不反复请求同一授权；评审请求本身不自动授权修改玩法。
